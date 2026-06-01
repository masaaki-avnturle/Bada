/*
 * gui_x11.c — X11 グラフィカルGUI フロントエンド
 *
 * 真のウィンドウ(Xlib)で動作するデスクトップ版。
 *   - プリセット一覧(クリック/↑↓ で選択)
 *   - 赤外線(IR)センサー + 温度計 のライブ表示(バーゲージ)
 *   - 選択プリセットの波形描画
 *   - ボタン: Play / Save / Realtime / BioFB / Quit
 *       BioFB ON 時: 温度計 -> beat、IR対象温度 -> carrier を変調
 *       Realtime ON 時: ALSA で連続再生し、センサー値に追従して音が変化
 *
 * 重要: 音響トーン発生器です。プリセット名はラベルであり、薬剤や治療効果を
 *       再現・代替しません(医学的主張なし)。
 *
 * ビルド: Makefile 参照(ALSA があれば実時間再生有効)
 * 実行:
 *   DISPLAY=:0 ./bfa_gui      (Xディスプレイのあるデスクトップで)
 *   ./bfa_gui --selftest      (ディスプレイを開かず検証して終了)
 */
#define _POSIX_C_SOURCE 200809L
#include "audio_core.h"
#include "sensors.h"
#include "rt_audio.h"
#include "biosignal.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <locale.h>
#include <sys/select.h>

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/keysym.h>
#include <X11/Xft/Xft.h>   /* fontconfig 経由で日本語(TrueType)を描画 */

#define WIN_W 820
#define WIN_H 760

/* ---- ディスプレイを開かない自己診断 ---- */
static int selftest(void) {
    SensorCtx sc; sensor_init(&sc);
    printf("[selftest] sensor backend = %s\n", sensor_backend_name(&sc));
    printf("[selftest] realtime audio (ALSA) = %s\n",
           rt_audio_available() ? "compiled-in" : "not available");
    SensorReading r;
    for (int i = 0; i < 3; i++) {
        sensor_read(&sc, &r);
        printf("[selftest] amb=%.2fC ir_obj=%.2fC ir_raw=%.2f present=%d\n",
               r.ambient_c, r.ir_object_c, r.ir_raw, r.present);
    }
    const Preset *p = &BFA_PRESETS[0];
    printf("[selftest] preset[0]=%s carrier=%.1f beat=%.1f -> fb_carrier=%.2f fb_beat=%.2f\n",
           p->jp, p->carrier, p->beat,
           bfa_feedback_carrier(p->carrier, r.ir_object_c),
           bfa_feedback_beat(p->beat, r.ambient_c));
    BioCtx bc; bio_init(&bc);
    BioReading br;
    for (int i = 0; i < 40; i++) bio_read(&bc, &br);
    printf("[selftest] biosignal backend = %s\n", bio_backend_name(&bc));
    printf("[selftest] EEG dominant=%s -> beat=%.1fHz   ECG bpm=%.1f -> carrier=%.1fHz\n",
           bio_band_name(br.eeg_dominant), bfa_eeg_beat(br.eeg_dominant),
           br.bpm, bfa_ecg_carrier(p->carrier, br.bpm));
    if (bfa_write_wav("/tmp/bfa_x11_selftest.wav", p->carrier, p->beat, 0.5) != 0) {
        printf("[selftest] WAV write FAILED\n"); return 1;
    }
    printf("[selftest] WAV write OK\n[selftest] OK\n");
    return 0;
}

static unsigned long alloc_rgb(Display *d, Colormap cm, int r, int g, int b) {
    XColor c;
    c.red = r * 257; c.green = g * 257; c.blue = b * 257;
    c.flags = DoRed | DoGreen | DoBlue;
    if (!XAllocColor(d, cm, &c)) return BlackPixel(d, DefaultScreen(d));
    return c.pixel;
}

typedef struct { int x, y, w, h; const char *label; } Button;

static int in_rect(int px, int py, int x, int y, int w, int h) {
    return px >= x && px < x + w && py >= y && py < y + h;
}

/* UTF-8(日本語含む)を描画するための Xft フォント。
 * Xlib の XDrawString/XFontSet は 8bit ないし旧式 X コアフォント前提で、
 * fontconfig の TrueType(IPAGothic 等)を使えず日本語が化ける。
 * Xft は fontconfig 経由で TrueType を扱えるため確実に表示できる。 */
static XftFont   *g_font = NULL;
static XftDraw   *g_xft  = NULL;
static Display   *g_dpy  = NULL;
static Visual    *g_vis  = NULL;
static Colormap   g_cmap;

/* GC の現在の前景ピクセルを RGB に戻して XftColor を作り、UTF-8 を描画。
 * 既存の各描画箇所は直前に XSetForeground しているので色が一致する。
 * シグネチャは XDrawString と同一(末尾の len も受け取る)。 */
static void draw_u8(Display *dpy, Drawable d, GC gc, int x, int y,
                    const char *s, int len) {
    if (!g_font || !g_xft) {                 /* フォールバック */
        XDrawString(dpy, d, gc, x, y, s, len);
        return;
    }
    XGCValues gv;
    XGetGCValues(dpy, gc, GCForeground, &gv);
    XColor xc; xc.pixel = gv.foreground;
    XQueryColor(dpy, g_cmap, &xc);
    XRenderColor rc = { xc.red, xc.green, xc.blue, 0xffff };
    XftColor col;
    if (!XftColorAllocValue(dpy, g_vis, g_cmap, &rc, &col)) {
        XDrawString(dpy, d, gc, x, y, s, len);
        return;
    }
    XftDrawStringUtf8(g_xft, &col, g_font, x, y, (const FcChar8 *)s, len);
    XftColorFree(dpy, g_vis, g_cmap, &col);
}

/* 有効周波数を一元計算: neuro(脳波/心電) > feedback(温度/IR) > 既定 */
static void eff_freq(const Preset *p, int feedback, int neuro,
                     const SensorReading *rd, const BioReading *br,
                     double *carrier, double *beat) {
    double c = p->carrier, b = p->beat;
    if (feedback) {
        c = bfa_feedback_carrier(p->carrier, rd->ir_object_c);
        b = bfa_feedback_beat(p->beat, rd->ambient_c);
    }
    if (neuro) {
        c = bfa_ecg_carrier(p->carrier, br->bpm);
        b = bfa_eeg_beat(br->eeg_dominant);
    }
    *carrier = c; *beat = b;
}

int main(int argc, char **argv) {
    if (argc >= 2 && strcmp(argv[1], "--selftest") == 0)
        return selftest();

    /* UTF-8 の日本語を描画するためロケールを有効化(XFontSet が利用)。
     * 環境が POSIX/C でも C.UTF-8 等へ自動フォールバックする。 */
    bfa_enable_utf8_locale();
    if (!XSupportsLocale()) XSetLocaleModifiers("");

    SensorCtx sc; sensor_init(&sc);
    SensorReading rd; memset(&rd, 0, sizeof(rd));
    BioCtx bc; bio_init(&bc);
    BioReading br; memset(&br, 0, sizeof(br));
    RtAudio *rt = rt_audio_create();

    Display *dpy = XOpenDisplay(NULL);
    if (!dpy) {
        fprintf(stderr,
            "Xディスプレイを開けません(DISPLAY未設定/未接続)。\n"
            "Xサーバのある環境で実行してください。検証だけなら: %s --selftest\n",
            argv[0]);
        if (rt) rt_audio_destroy(rt);
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

    Window win = XCreateSimpleWindow(dpy, root, 0, 0, WIN_W, WIN_H, 0, c_fg, c_bg);
    XStoreName(dpy, win, "Biofeedback Audio (X11) - IR sensor & thermometer");
    XSelectInput(dpy, win, ExposureMask | KeyPressMask | ButtonPressMask | StructureNotifyMask);

    Atom wm_delete = XInternAtom(dpy, "WM_DELETE_WINDOW", False);
    XSetWMProtocols(dpy, win, &wm_delete, 1);
    XMapWindow(dpy, win);

    GC gc = XCreateGC(dpy, win, 0, NULL);
    Pixmap buf = XCreatePixmap(dpy, win, WIN_W, WIN_H, DefaultDepth(dpy, scr));

    /* Xft フォント(fontconfig)で日本語表示。
     * ":lang=ja" を付けて「日本語を含むフォント」を fontconfig に選ばせる
     * (この環境では IPAGothic 等が選ばれ、Latin も日本語も同一フェイスで描ける)。
     * 単一の XftFont は自動グリフ補完をしないため、最初から CJK 対応フェイスを要求するのが要点。 */
    g_dpy  = dpy;
    g_vis  = DefaultVisual(dpy, scr);
    g_cmap = cm;
    g_font = XftFontOpenName(dpy, scr, "sans-12:lang=ja");
    if (!g_font) g_font = XftFontOpenName(dpy, scr, "IPAGothic-12");
    if (!g_font) g_font = XftFontOpenName(dpy, scr, "sans-12");
    /* 描画先はバッキング Pixmap(buf) */
    g_xft  = XftDrawCreate(dpy, buf, g_vis, g_cmap);

    int sel = 0, feedback = 0, neuro = 0, realtime = 0;
    char status[512];
    snprintf(status, sizeof(status), "↑↓:選択 P:再生 S:保存 R:実時間 B:温度FB E:脳波/心電FB Q:終了");

    Button btns[6] = {
        {  10, 720, 70, 30, "Play" },
        {  86, 720, 70, 30, "Save" },
        { 162, 720, 90, 30, "Realtime" },
        { 258, 720, 80, 30, "TempFB" },
        { 344, 720, 100, 30, "Neuro" },
        { 450, 720, 70, 30, "Quit" },
    };
    const int NBTN = 6;

    int fd = ConnectionNumber(dpy);
    double phase = 0.0;
    int running = 1;

    while (running) {
        while (XPending(dpy)) {
            XEvent ev;
            XNextEvent(dpy, &ev);
            const Preset *p = &BFA_PRESETS[sel];
            double ec, eb;
            eff_freq(p, feedback, neuro, &rd, &br, &ec, &eb);

            if (ev.type == ClientMessage) {
                if ((Atom)ev.xclient.data.l[0] == wm_delete) running = 0;
            } else if (ev.type == KeyPress) {
                KeySym ks = XLookupKeysym(&ev.xkey, 0);
                if (ks == XK_q || ks == XK_Q) running = 0;
                else if (ks == XK_Up   && sel > 0) sel--;
                else if (ks == XK_Down && sel < (int)BFA_PRESET_COUNT - 1) sel++;
                else if (ks == XK_b || ks == XK_B) {
                    feedback = !feedback; if (feedback) neuro = 0;
                    snprintf(status, sizeof(status), "温度FB %s", feedback ? "ON" : "OFF");
                } else if (ks == XK_e || ks == XK_E) {
                    neuro = !neuro; if (neuro) feedback = 0;
                    snprintf(status, sizeof(status), "脳波/心電FB %s", neuro ? "ON" : "OFF");
                } else if (ks == XK_r || ks == XK_R) {
                    if (!rt_audio_available())
                        snprintf(status, sizeof(status), "実時間再生は無効(ALSA無し)");
                    else if (realtime && rt_audio_is_running(rt)) {
                        rt_audio_stop(rt); realtime = 0;
                        snprintf(status, sizeof(status), "実時間再生 停止");
                    } else {
                        rt_audio_set_freq(rt, ec, eb);
                        if (rt_audio_start(rt) == 0) { realtime = 1;
                            snprintf(status, sizeof(status), "実時間再生 開始(ALSA)"); }
                        else snprintf(status, sizeof(status), "実時間再生 失敗(デバイス無し?)");
                    }
                } else if (ks == XK_p || ks == XK_P || ks == XK_Return) {
                    char path[256]; snprintf(path, sizeof(path), "/tmp/bfa_%s.wav", p->key);
                    bfa_play_wav(path, ec, eb, 15.0);
                    snprintf(status, sizeof(status), "再生(試行): %s c=%.0f b=%.2f", p->jp, ec, eb);
                } else if (ks == XK_s || ks == XK_S) {
                    char path[256]; snprintf(path, sizeof(path), "%s.wav", p->key);
                    if (bfa_write_wav(path, ec, eb, 30.0) == 0)
                        snprintf(status, sizeof(status), "保存(30s)");
                }
            } else if (ev.type == ButtonPress) {
                int mx = ev.xbutton.x, my = ev.xbutton.y;
                int row_top = 60, row_h = 22;
                if (mx >= 10 && mx < 280 && my >= row_top) {
                    int idx = (my - row_top) / row_h;
                    if (idx >= 0 && idx < (int)BFA_PRESET_COUNT) sel = idx;
                }
                for (int i = 0; i < NBTN; i++) {
                    if (in_rect(mx, my, btns[i].x, btns[i].y, btns[i].w, btns[i].h)) {
                        if (i == 0) { char pa[256]; snprintf(pa,sizeof(pa),"/tmp/bfa_%s.wav",p->key);
                                      bfa_play_wav(pa, ec, eb, 15.0);
                                      snprintf(status,sizeof(status),"再生(試行): %s",p->jp); }
                        else if (i == 1) { char pa[256]; snprintf(pa,sizeof(pa),"%s.wav",p->key);
                                      if (bfa_write_wav(pa,ec,eb,30.0)==0)
                                        snprintf(status,sizeof(status),"保存(30s)"); }
                        else if (i == 2) {
                            if (!rt_audio_available())
                                snprintf(status,sizeof(status),"実時間再生は無効(ALSA無し)");
                            else if (realtime && rt_audio_is_running(rt)) {
                                rt_audio_stop(rt); realtime = 0;
                                snprintf(status,sizeof(status),"実時間再生 停止"); }
                            else { rt_audio_set_freq(rt, ec, eb);
                                if (rt_audio_start(rt)==0){ realtime=1;
                                    snprintf(status,sizeof(status),"実時間再生 開始(ALSA)"); }
                                else snprintf(status,sizeof(status),"実時間再生 失敗"); }
                        }
                        else if (i == 3) { feedback = !feedback; if (feedback) neuro = 0;
                                      snprintf(status,sizeof(status),"温度FB %s",feedback?"ON":"OFF"); }
                        else if (i == 4) { neuro = !neuro; if (neuro) feedback = 0;
                                      snprintf(status,sizeof(status),"脳波/心電FB %s",neuro?"ON":"OFF"); }
                        else if (i == 5) running = 0;
                    }
                }
            }
        }
        if (!running) break;

        fd_set fds; FD_ZERO(&fds); FD_SET(fd, &fds);
        struct timeval tv = { 0, 150000 };
        select(fd + 1, &fds, NULL, NULL, &tv);
        sensor_read(&sc, &rd);
        bio_read(&bc, &br);

        const Preset *p = &BFA_PRESETS[sel];
        double eff_carrier, eff_beat;
        eff_freq(p, feedback, neuro, &rd, &br, &eff_carrier, &eff_beat);

        if (realtime && rt && rt_audio_is_running(rt))
            rt_audio_set_freq(rt, eff_carrier, eff_beat);

        /* --- 描画 --- */
        XSetForeground(dpy, gc, c_bg);
        XFillRectangle(dpy, buf, gc, 0, 0, WIN_W, WIN_H);

        XSetForeground(dpy, gc, c_fg);
        draw_u8(dpy, buf, gc, 10, 20,
                    "Biofeedback Audio (X11)  IR sensor & thermometer", 48);
        char hdr[160];
        snprintf(hdr, sizeof(hdr), "sensor: %s   realtime(ALSA): %s",
                 sensor_backend_name(&sc),
                 (realtime && rt_audio_is_running(rt)) ? "ON" :
                 (rt_audio_available() ? "OFF" : "N/A"));
        draw_u8(dpy, buf, gc, 10, 36, hdr, (int)strlen(hdr));
        draw_u8(dpy, buf, gc, 10, 50,
                    "* tone generator only - not a medical/therapeutic device", 56);

        int row_top = 60, row_h = 22;
        for (int i = 0; i < (int)BFA_PRESET_COUNT; i++) {
            int y = row_top + i * row_h;
            if (i == sel) { XSetForeground(dpy, gc, c_sel);
                            XFillRectangle(dpy, buf, gc, 10, y, 270, row_h); }
            XSetForeground(dpy, gc, c_fg);
            char line[128];
            snprintf(line, sizeof(line), "%-12s %6.1fHz %4.1fHz %s",
                     BFA_PRESETS[i].key, BFA_PRESETS[i].carrier,
                     BFA_PRESETS[i].beat, bfa_band_name(BFA_PRESETS[i].beat));
            draw_u8(dpy, buf, gc, 16, y + 15, line, (int)strlen(line));
        }

        int px = 300, py = 70, pw = 480, ph = 150;
        XSetForeground(dpy, gc, c_panel);
        XFillRectangle(dpy, buf, gc, px, py, pw, ph);
        XSetForeground(dpy, gc, c_fg);
        draw_u8(dpy, buf, gc, px + 8, py + 16, "Sensors (live)", 14);

        int bx = px + 110, bw = 250, bh = 14;
        double f_temp = (rd.ambient_c - 10.0) / 30.0; if (f_temp<0)f_temp=0; if(f_temp>1)f_temp=1;
        draw_u8(dpy, buf, gc, px + 8, py + 40, "Thermometer", 11);
        XSetForeground(dpy, gc, c_btn); XFillRectangle(dpy, buf, gc, bx, py + 30, bw, bh);
        XSetForeground(dpy, gc, c_temp); XFillRectangle(dpy, buf, gc, bx, py + 30, (int)(bw*f_temp), bh);
        char t1[64]; snprintf(t1,sizeof(t1),"%.2f C", rd.ambient_c);
        XSetForeground(dpy, gc, c_fg); draw_u8(dpy, buf, gc, bx + bw + 8, py + 42, t1, (int)strlen(t1));

        double f_iro = (rd.ir_object_c - 20.0) / 20.0; if(f_iro<0)f_iro=0; if(f_iro>1)f_iro=1;
        draw_u8(dpy, buf, gc, px + 8, py + 70, "IR object", 9);
        XSetForeground(dpy, gc, c_btn); XFillRectangle(dpy, buf, gc, bx, py + 60, bw, bh);
        XSetForeground(dpy, gc, c_ir); XFillRectangle(dpy, buf, gc, bx, py + 60, (int)(bw*f_iro), bh);
        char t2[64]; snprintf(t2,sizeof(t2),"%.2f C", rd.ir_object_c);
        XSetForeground(dpy, gc, c_fg); draw_u8(dpy, buf, gc, bx + bw + 8, py + 72, t2, (int)strlen(t2));

        draw_u8(dpy, buf, gc, px + 8, py + 100, "IR raw", 6);
        XSetForeground(dpy, gc, c_btn); XFillRectangle(dpy, buf, gc, bx, py + 90, bw, bh);
        XSetForeground(dpy, gc, c_ir); XFillRectangle(dpy, buf, gc, bx, py + 90, (int)(bw*rd.ir_raw), bh);
        char t3[64]; snprintf(t3,sizeof(t3),"%.2f", rd.ir_raw);
        XSetForeground(dpy, gc, c_fg); draw_u8(dpy, buf, gc, bx + bw + 8, py + 102, t3, (int)strlen(t3));

        XSetForeground(dpy, gc, rd.present ? c_temp : c_warn);
        draw_u8(dpy, buf, gc, px + 8, py + 130,
                    rd.present ? "IR proximity: DETECTED" : "IR proximity: none", 22);

        XSetForeground(dpy, gc, c_fg);
        char info[256];
        const char *mode = neuro ? "[NEURO]" : (feedback ? "[TEMP-FB]" : "[OFF]");
        snprintf(info, sizeof(info),
                 "%s  carrier %.0f→%.0fHz  beat %.1f→%.1fHz(%s) %s",
                 p->key, p->carrier, eff_carrier, p->beat, eff_beat,
                 bfa_band_name(eff_beat), mode);
        draw_u8(dpy, buf, gc, px, py + ph + 20, info, (int)strlen(info));

        int wx = px, wy = py + ph + 35, ww = pw, wh = 80;
        XSetForeground(dpy, gc, c_panel); XFillRectangle(dpy, buf, gc, wx, wy, ww, wh);
        XSetForeground(dpy, gc, c_wave);
        int prev_y = wy + wh/2;
        for (int xx = 0; xx < ww; xx++) {
            double t = phase + (double)xx / ww * (3.0 / eff_carrier);
            double l, r; bfa_sample_at(t, eff_carrier, eff_beat, &l, &r);
            int yy = wy + (int)((1.0 - l) * 0.5 * (wh - 4)) + 2;
            if (xx > 0) XDrawLine(dpy, buf, gc, wx + xx - 1, prev_y, wx + xx, yy);
            prev_y = yy;
        }

        /* --- 脳波計(EEG) + 心電図(ECG) パネル --- */
        int gx = 10, gy = 540, gw = WIN_W - 20, gh = 165;
        XSetForeground(dpy, gc, c_panel); XFillRectangle(dpy, buf, gc, gx, gy, gw, gh);
        XSetForeground(dpy, gc, c_fg);
        char bh1[128];
        snprintf(bh1, sizeof(bh1), "EEG(脳波計) %s", bio_band_name(br.eeg_dominant));
        draw_u8(dpy, buf, gc, gx + 8, gy + 16, bh1, (int)strlen(bh1));

        /* EEG 帯域パワーバー(縦棒5本) */
        int eb_x = gx + 8, eb_w = 36, eb_gap = 8, eb_top = gy + 26, eb_h = 50;
        for (int b = 0; b < BIO_BAND_COUNT; b++) {
            int x = eb_x + b * (eb_w + eb_gap);
            int hh = (int)(br.eeg_band[b] * eb_h);
            XSetForeground(dpy, gc, c_btn);
            XFillRectangle(dpy, buf, gc, x, eb_top, eb_w, eb_h);
            XSetForeground(dpy, gc, (b == br.eeg_dominant) ? c_temp : c_ir);
            XFillRectangle(dpy, buf, gc, x, eb_top + (eb_h - hh), eb_w, hh);
            XSetForeground(dpy, gc, c_fg);
            draw_u8(dpy, buf, gc, x, eb_top + eb_h + 14,
                        bio_band_name(b), (int)strlen(bio_band_name(b)));
        }

        /* ECG 波形 + 心拍 */
        int ex = eb_x + BIO_BAND_COUNT * (eb_w + eb_gap) + 20;
        int ew = gx + gw - ex - 10, eh = 70, ey = gy + 26;
        XSetForeground(dpy, gc, c_fg);
        char bh2[96];
        snprintf(bh2, sizeof(bh2), "ECG(心電図)  %.1f bpm %s",
                 br.bpm, br.beat ? "<HEART R>" : "");
        draw_u8(dpy, buf, gc, ex, gy + 16, bh2, (int)strlen(bh2));
        XSetForeground(dpy, gc, c_btn); XFillRectangle(dpy, buf, gc, ex, ey, ew, eh);
        if (br.ecg_count > 0 && ew > 1) {
            XSetForeground(dpy, gc, br.beat ? c_warn : c_wave);
            int pe = ey + eh/2;
            for (int xx = 0; xx < ew; xx++) {
                int idx = (int)((double)xx / ew * (ECG_WIN - 1));
                float v = br.ecg_wave[idx];
                int yy = ey + (int)((1.0 - v) * 0.5 * (eh - 4)) + 2;
                if (yy < ey) yy = ey;
                if (yy > ey + eh) yy = ey + eh;
                if (xx > 0) XDrawLine(dpy, buf, gc, ex + xx - 1, pe, ex + xx, yy);
                pe = yy;
            }
        }

        for (int i = 0; i < NBTN; i++) {
            int hot = (i == 2 && realtime) || (i == 3 && feedback) || (i == 4 && neuro);
            XSetForeground(dpy, gc, hot ? c_sel : c_btn);
            XFillRectangle(dpy, buf, gc, btns[i].x, btns[i].y, btns[i].w, btns[i].h);
            XSetForeground(dpy, gc, c_fg);
            XDrawRectangle(dpy, buf, gc, btns[i].x, btns[i].y, btns[i].w, btns[i].h);
            draw_u8(dpy, buf, gc, btns[i].x + 8, btns[i].y + 20,
                        btns[i].label, (int)strlen(btns[i].label));
        }

        draw_u8(dpy, buf, gc, 10, WIN_H - 8, status, (int)strlen(status));

        XCopyArea(dpy, buf, win, gc, 0, 0, WIN_W, WIN_H, 0, 0);
        XFlush(dpy);
        phase += 0.02;
    }

    if (rt) rt_audio_destroy(rt);
    if (g_xft)  XftDrawDestroy(g_xft);
    if (g_font) XftFontClose(dpy, g_font);
    XFreePixmap(dpy, buf);
    XFreeGC(dpy, gc);
    XDestroyWindow(dpy, win);
    XCloseDisplay(dpy);
    printf("終了しました。\n");
    return 0;
}
