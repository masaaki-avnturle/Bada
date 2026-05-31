/*
 * gui_x11.c — X11 グラフィカルGUI フロントエンド
 *
 * 真のウィンドウ(Xlib)で動作するデスクトップ版。
 *   - プリセット一覧(クリック/↑↓ で選択)
 *   - 赤外線(IR)センサー + 温度計 のライブ表示(バーゲージ)
 *   - 選択プリセットの波形描画
 *   - ボタン: Play / Save / BioFB / Quit
 *       BioFB(バイオフィードバック)ON 時は温度計の値で beat を変調
 *
 * 重要: 音響トーン発生器です。プリセット名はラベルであり、薬剤や治療効果を
 *       再現・代替しません(医学的主張なし)。
 *
 * ビルド:
 *   gcc -std=c99 -O2 -Wall -o bfa_gui gui_x11.c audio_core.c sensors.c -lX11 -lm
 * 実行:
 *   DISPLAY=:0 ./bfa_gui      (Xディスプレイのあるデスクトップで)
 *   ./bfa_gui --selftest      (ディスプレイを開かず検証して終了)
 *
 * 注意: このリモートコンテナはディスプレイ非接続のため、実ウィンドウ表示は
 *       Xサーバのある環境で確認してください。--selftest はどこでも動きます。
 */
#define _POSIX_C_SOURCE 200809L
#include "audio_core.h"
#include "sensors.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <sys/select.h>

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/keysym.h>

#define WIN_W 780
#define WIN_H 540

static double feedback_beat(double base_beat, double ambient_c) {
    double b = base_beat + (ambient_c - 24.0) * 0.5;
    if (b < 0.5) b = 0.5;
    if (b > 30.0) b = 30.0;
    return b;
}

/* ---- ディスプレイを開かない自己診断 ---- */
static int selftest(void) {
    SensorCtx sc; sensor_init(&sc);
    printf("[selftest] sensor backend = %s\n", sensor_backend_name(&sc));
    SensorReading r;
    for (int i = 0; i < 3; i++) {
        sensor_read(&sc, &r);
        printf("[selftest] amb=%.2fC ir_obj=%.2fC ir_raw=%.2f present=%d\n",
               r.ambient_c, r.ir_object_c, r.ir_raw, r.present);
    }
    const Preset *p = &BFA_PRESETS[0];
    printf("[selftest] preset[0]=%s carrier=%.1f beat=%.1f fb_beat=%.2f\n",
           p->jp, p->carrier, p->beat, feedback_beat(p->beat, r.ambient_c));
    if (bfa_write_wav("/tmp/bfa_x11_selftest.wav", p->carrier, p->beat, 0.5) != 0) {
        printf("[selftest] WAV write FAILED\n"); return 1;
    }
    printf("[selftest] WAV write OK\n[selftest] OK\n");
    return 0;
}

/* ---- 色確保ヘルパ ---- */
static unsigned long alloc_rgb(Display *d, Colormap cm, int r, int g, int b) {
    XColor c;
    c.red = r * 257; c.green = g * 257; c.blue = b * 257;
    c.flags = DoRed | DoGreen | DoBlue;
    if (!XAllocColor(d, cm, &c)) return BlackPixel(d, DefaultScreen(d));
    return c.pixel;
}

/* ボタン矩形 */
typedef struct { int x, y, w, h; const char *label; } Button;

static int in_rect(int px, int py, int x, int y, int w, int h) {
    return px >= x && px < x + w && py >= y && py < y + h;
}

int main(int argc, char **argv) {
    if (argc >= 2 && strcmp(argv[1], "--selftest") == 0)
        return selftest();

    SensorCtx sc; sensor_init(&sc);
    SensorReading rd; memset(&rd, 0, sizeof(rd));

    Display *dpy = XOpenDisplay(NULL);
    if (!dpy) {
        fprintf(stderr,
            "Xディスプレイを開けません(DISPLAY未設定/未接続)。\n"
            "Xサーバのある環境で実行してください。検証だけなら: %s --selftest\n",
            argv[0]);
        return 1;
    }
    int scr = DefaultScreen(dpy);
    Window root = RootWindow(dpy, scr);
    Colormap cm = DefaultColormap(dpy, scr);

    unsigned long c_bg    = alloc_rgb(dpy, cm, 24, 26, 32);
    unsigned long c_fg    = alloc_rgb(dpy, cm, 220, 224, 230);
    unsigned long c_sel   = alloc_rgb(dpy, cm, 50, 90, 140);
    unsigned long c_temp  = alloc_rgb(dpy, cm, 90, 200, 120);
    unsigned long c_ir    = alloc_rgb(dpy, cm, 240, 200, 80);
    unsigned long c_warn  = alloc_rgb(dpy, cm, 230, 90, 90);
    unsigned long c_panel = alloc_rgb(dpy, cm, 38, 42, 52);
    unsigned long c_wave  = alloc_rgb(dpy, cm, 120, 200, 240);
    unsigned long c_btn   = alloc_rgb(dpy, cm, 60, 66, 80);

    Window win = XCreateSimpleWindow(dpy, root, 0, 0, WIN_W, WIN_H, 0,
                                     c_fg, c_bg);
    XStoreName(dpy, win, "Biofeedback Audio (X11) - IR sensor & thermometer");
    XSelectInput(dpy, win, ExposureMask | KeyPressMask | ButtonPressMask | StructureNotifyMask);

    Atom wm_delete = XInternAtom(dpy, "WM_DELETE_WINDOW", False);
    XSetWMProtocols(dpy, win, &wm_delete, 1);
    XMapWindow(dpy, win);

    GC gc = XCreateGC(dpy, win, 0, NULL);
    XFontStruct *font = XLoadQueryFont(dpy, "fixed");
    if (font) XSetFont(dpy, gc, font->fid);

    /* 描画はバッキング Pixmap 経由(ちらつき防止) */
    Pixmap buf = XCreatePixmap(dpy, win, WIN_W, WIN_H, DefaultDepth(dpy, scr));

    int sel = 0, feedback = 0;
    char status[256];
    snprintf(status, sizeof(status), "↑↓:選択  P:再生  S:保存  B:バイオFB  Q:終了");

    Button btns[4] = {
        { 300, 470, 90, 30, "Play" },
        { 400, 470, 90, 30, "Save" },
        { 500, 470, 110, 30, "BioFB" },
        { 620, 470, 90, 30, "Quit" },
    };

    int fd = ConnectionNumber(dpy);
    double phase = 0.0;
    int running = 1;

    while (running) {
        /* --- イベント処理 --- */
        while (XPending(dpy)) {
            XEvent ev;
            XNextEvent(dpy, &ev);
            if (ev.type == ClientMessage) {
                if ((Atom)ev.xclient.data.l[0] == wm_delete) running = 0;
            } else if (ev.type == KeyPress) {
                KeySym ks = XLookupKeysym(&ev.xkey, 0);
                if (ks == XK_q || ks == XK_Q) running = 0;
                else if (ks == XK_Up   && sel > 0) sel--;
                else if (ks == XK_Down && sel < (int)BFA_PRESET_COUNT - 1) sel++;
                else if (ks == XK_b || ks == XK_B) {
                    feedback = !feedback;
                    snprintf(status, sizeof(status), "バイオフィードバック %s", feedback ? "ON" : "OFF");
                } else if (ks == XK_p || ks == XK_P || ks == XK_Return) {
                    const Preset *p = &BFA_PRESETS[sel];
                    double eb = feedback ? feedback_beat(p->beat, rd.ambient_c) : p->beat;
                    char path[256]; snprintf(path, sizeof(path), "/tmp/bfa_%s.wav", p->key);
                    bfa_play_wav(path, p->carrier, eb, 15.0);
                    snprintf(status, sizeof(status), "再生(試行): %s eff_beat=%.2fHz", p->jp, eb);
                } else if (ks == XK_s || ks == XK_S) {
                    const Preset *p = &BFA_PRESETS[sel];
                    double eb = feedback ? feedback_beat(p->beat, rd.ambient_c) : p->beat;
                    char path[256]; snprintf(path, sizeof(path), "%s.wav", p->key);
                    if (bfa_write_wav(path, p->carrier, eb, 30.0) == 0)
                        snprintf(status, sizeof(status), "保存: %s (30s)", path);
                }
            } else if (ev.type == ButtonPress) {
                int mx = ev.xbutton.x, my = ev.xbutton.y;
                /* プリセット行クリック */
                int row_top = 60, row_h = 22;
                if (mx >= 10 && mx < 280 && my >= row_top) {
                    int idx = (my - row_top) / row_h;
                    if (idx >= 0 && idx < (int)BFA_PRESET_COUNT) sel = idx;
                }
                /* ボタン */
                for (int i = 0; i < 4; i++) {
                    if (in_rect(mx, my, btns[i].x, btns[i].y, btns[i].w, btns[i].h)) {
                        const Preset *p = &BFA_PRESETS[sel];
                        double eb = feedback ? feedback_beat(p->beat, rd.ambient_c) : p->beat;
                        if (i == 0) { char pa[256]; snprintf(pa,sizeof(pa),"/tmp/bfa_%s.wav",p->key);
                                      bfa_play_wav(pa, p->carrier, eb, 15.0);
                                      snprintf(status,sizeof(status),"再生(試行): %s eff_beat=%.2fHz",p->jp,eb); }
                        else if (i == 1) { char pa[256]; snprintf(pa,sizeof(pa),"%s.wav",p->key);
                                      if (bfa_write_wav(pa,p->carrier,eb,30.0)==0)
                                        snprintf(status,sizeof(status),"保存: %s (30s)",pa); }
                        else if (i == 2) { feedback = !feedback;
                                      snprintf(status,sizeof(status),"バイオフィードバック %s",feedback?"ON":"OFF"); }
                        else if (i == 3) running = 0;
                    }
                }
            }
        }
        if (!running) break;

        /* --- センサー更新(タイマ: 150ms) --- */
        fd_set fds; FD_ZERO(&fds); FD_SET(fd, &fds);
        struct timeval tv = { 0, 150000 };
        select(fd + 1, &fds, NULL, NULL, &tv);
        sensor_read(&sc, &rd);

        const Preset *p = &BFA_PRESETS[sel];
        double eff_beat = feedback ? feedback_beat(p->beat, rd.ambient_c) : p->beat;

        /* --- 描画(バッキング Pixmap) --- */
        XSetForeground(dpy, gc, c_bg);
        XFillRectangle(dpy, buf, gc, 0, 0, WIN_W, WIN_H);

        XSetForeground(dpy, gc, c_fg);
        XDrawString(dpy, buf, gc, 10, 20,
                    "Biofeedback Audio (X11)  IR sensor & thermometer", 48);
        char hdr[128];
        snprintf(hdr, sizeof(hdr), "sensor backend: %s", sensor_backend_name(&sc));
        XDrawString(dpy, buf, gc, 10, 36, hdr, (int)strlen(hdr));
        XDrawString(dpy, buf, gc, 10, 50,
                    "* tone generator only - not a medical/therapeutic device", 56);

        /* プリセット一覧 */
        int row_top = 60, row_h = 22;
        for (int i = 0; i < (int)BFA_PRESET_COUNT; i++) {
            int y = row_top + i * row_h;
            if (i == sel) {
                XSetForeground(dpy, gc, c_sel);
                XFillRectangle(dpy, buf, gc, 10, y, 270, row_h);
            }
            XSetForeground(dpy, gc, c_fg);
            char line[128];
            snprintf(line, sizeof(line), "%-12s %6.1fHz %4.1fHz %s",
                     BFA_PRESETS[i].key, BFA_PRESETS[i].carrier,
                     BFA_PRESETS[i].beat, bfa_band_name(BFA_PRESETS[i].beat));
            XDrawString(dpy, buf, gc, 16, y + 15, line, (int)strlen(line));
        }

        /* センサーパネル */
        int px = 300, py = 70, pw = 460, ph = 150;
        XSetForeground(dpy, gc, c_panel);
        XFillRectangle(dpy, buf, gc, px, py, pw, ph);
        XSetForeground(dpy, gc, c_fg);
        XDrawString(dpy, buf, gc, px + 8, py + 16, "Sensors (live)", 14);

        /* 温度計バー */
        int bx = px + 110, bw = 240, bh = 14;
        double f_temp = (rd.ambient_c - 10.0) / 30.0; if (f_temp<0)f_temp=0; if(f_temp>1)f_temp=1;
        XDrawString(dpy, buf, gc, px + 8, py + 40, "Thermometer", 11);
        XSetForeground(dpy, gc, c_btn); XFillRectangle(dpy, buf, gc, bx, py + 30, bw, bh);
        XSetForeground(dpy, gc, c_temp); XFillRectangle(dpy, buf, gc, bx, py + 30, (int)(bw*f_temp), bh);
        char t1[64]; snprintf(t1,sizeof(t1),"%.2f C", rd.ambient_c);
        XSetForeground(dpy, gc, c_fg); XDrawString(dpy, buf, gc, bx + bw + 8, py + 42, t1, (int)strlen(t1));

        /* IR 対象温度バー */
        double f_iro = (rd.ir_object_c - 20.0) / 20.0; if(f_iro<0)f_iro=0; if(f_iro>1)f_iro=1;
        XDrawString(dpy, buf, gc, px + 8, py + 70, "IR object", 9);
        XSetForeground(dpy, gc, c_btn); XFillRectangle(dpy, buf, gc, bx, py + 60, bw, bh);
        XSetForeground(dpy, gc, c_ir); XFillRectangle(dpy, buf, gc, bx, py + 60, (int)(bw*f_iro), bh);
        char t2[64]; snprintf(t2,sizeof(t2),"%.2f C", rd.ir_object_c);
        XSetForeground(dpy, gc, c_fg); XDrawString(dpy, buf, gc, bx + bw + 8, py + 72, t2, (int)strlen(t2));

        /* IR 生値バー */
        XDrawString(dpy, buf, gc, px + 8, py + 100, "IR raw", 6);
        XSetForeground(dpy, gc, c_btn); XFillRectangle(dpy, buf, gc, bx, py + 90, bw, bh);
        XSetForeground(dpy, gc, c_ir); XFillRectangle(dpy, buf, gc, bx, py + 90, (int)(bw*rd.ir_raw), bh);
        char t3[64]; snprintf(t3,sizeof(t3),"%.2f", rd.ir_raw);
        XSetForeground(dpy, gc, c_fg); XDrawString(dpy, buf, gc, bx + bw + 8, py + 102, t3, (int)strlen(t3));

        /* 近接 */
        XSetForeground(dpy, gc, rd.present ? c_temp : c_warn);
        XDrawString(dpy, buf, gc, px + 8, py + 130,
                    rd.present ? "IR proximity: DETECTED" : "IR proximity: none", 22);

        /* 選択情報 */
        XSetForeground(dpy, gc, c_fg);
        char info[160];
        snprintf(info, sizeof(info), "Selected: %s  carrier=%.1fHz  beat=%.1f -> eff=%.2fHz(%s) %s",
                 p->key, p->carrier, p->beat, eff_beat, bfa_band_name(eff_beat),
                 feedback ? "[FB:ON]" : "[FB:OFF]");
        XDrawString(dpy, buf, gc, px, py + ph + 20, info, (int)strlen(info));

        /* 波形 */
        int wx = px, wy = py + ph + 35, ww = pw, wh = 90;
        XSetForeground(dpy, gc, c_panel); XFillRectangle(dpy, buf, gc, wx, wy, ww, wh);
        XSetForeground(dpy, gc, c_wave);
        int prev_y = wy + wh/2;
        for (int xx = 0; xx < ww; xx++) {
            double t = phase + (double)xx / ww * (3.0 / p->carrier);
            double l, r; bfa_sample_at(t, p->carrier, eff_beat, &l, &r);
            int yy = wy + (int)((1.0 - l) * 0.5 * (wh - 4)) + 2;
            if (xx > 0) XDrawLine(dpy, buf, gc, wx + xx - 1, prev_y, wx + xx, yy);
            prev_y = yy;
        }

        /* ボタン */
        for (int i = 0; i < 4; i++) {
            XSetForeground(dpy, gc, (i == 2 && feedback) ? c_sel : c_btn);
            XFillRectangle(dpy, buf, gc, btns[i].x, btns[i].y, btns[i].w, btns[i].h);
            XSetForeground(dpy, gc, c_fg);
            XDrawRectangle(dpy, buf, gc, btns[i].x, btns[i].y, btns[i].w, btns[i].h);
            XDrawString(dpy, buf, gc, btns[i].x + 12, btns[i].y + 20,
                        btns[i].label, (int)strlen(btns[i].label));
        }

        /* ステータス */
        XDrawString(dpy, buf, gc, 10, WIN_H - 8, status, (int)strlen(status));

        /* バッファをウィンドウへ転送 */
        XCopyArea(dpy, buf, win, gc, 0, 0, WIN_W, WIN_H, 0, 0);
        XFlush(dpy);
        phase += 0.02;
    }

    XFreePixmap(dpy, buf);
    if (font) XFreeFont(dpy, font);
    XFreeGC(dpy, gc);
    XDestroyWindow(dpy, win);
    XCloseDisplay(dpy);
    printf("終了しました。\n");
    return 0;
}
