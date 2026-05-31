/*
 * gui_ncurses.c — 端末GUI(ncurses) フロントエンド
 *
 * 機能:
 *   - プリセット一覧の選択(↑↓ / j k)
 *   - 赤外線(IR)センサー + 温度計 のライブ表示(バーゲージ)
 *   - 選択プリセットの波形(ASCII)表示
 *   - 再生(p/Enter) / WAV保存(s) / バイオフィードバックモード(b)
 *       バイオフィードバックモード: 温度計の値で beat 周波数を変調
 *
 * 重要: 音響トーン発生器です。プリセット名はラベルであり、薬剤や治療効果を
 *       再現・代替しません(医学的主張なし)。
 *
 * ビルド:
 *   gcc -std=c99 -O2 -Wall -o bfa_tui gui_ncurses.c audio_core.c sensors.c -lncurses -lm
 * 実行:
 *   ./bfa_tui            (端末GUI)
 *   ./bfa_tui --selftest (画面を開かず内部ロジックを検証して終了)
 */
#define _POSIX_C_SOURCE 200809L
#include "audio_core.h"
#include "sensors.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <ncurses.h>

/* 温度を beat 変調量(Hz)に写像(バイオフィードバック) */
static double feedback_beat(double base_beat, double ambient_c) {
    double mod = (ambient_c - 24.0) * 0.5; /* 24C を基準に ±変調 */
    double b = base_beat + mod;
    if (b < 0.5) b = 0.5;
    if (b > 30.0) b = 30.0;
    return b;
}

/* ---- 画面を開かない自己診断(コンテナ等での検証用) ---- */
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
    printf("[selftest] preset[0] = %s carrier=%.1f beat=%.1f fb_beat=%.2f\n",
           p->jp, p->carrier, p->beat, feedback_beat(p->beat, r.ambient_c));
    if (bfa_write_wav("/tmp/bfa_selftest.wav", p->carrier, p->beat, 0.5) != 0) {
        printf("[selftest] WAV write FAILED\n");
        return 1;
    }
    printf("[selftest] WAV write OK (/tmp/bfa_selftest.wav)\n");
    printf("[selftest] OK\n");
    return 0;
}

/* 水平バーゲージを描画 */
static void draw_gauge(int y, int x, int width, double frac, const char *label, double value, const char *unit) {
    if (frac < 0) frac = 0;
    if (frac > 1) frac = 1;
    int fill = (int)(frac * width + 0.5);
    mvprintw(y, x, "%-10s [", label);
    int bx = x + 12;
    for (int i = 0; i < width; i++)
        mvaddch(y, bx + i, i < fill ? ACS_CKBOARD : '.');
    mvprintw(y, bx + width, "] %6.2f%s", value, unit);
}

int main(int argc, char **argv) {
    if (argc >= 2 && strcmp(argv[1], "--selftest") == 0)
        return selftest();

    SensorCtx sc; sensor_init(&sc);
    SensorReading rd; memset(&rd, 0, sizeof(rd));

    int sel = 0;
    int feedback = 0;
    char status[512] = "↑↓/jk:選択  p/Enter:再生  s:保存  b:バイオFB  q:終了";

    initscr();
    if (!stdscr) { fprintf(stderr, "端末を初期化できません(TTYで実行してください)\n"); return 1; }
    cbreak();
    noecho();
    keypad(stdscr, TRUE);
    curs_set(0);
    timeout(150);              /* 非ブロッキング getch (150ms) */
    if (has_colors()) {
        start_color();
        init_pair(1, COLOR_CYAN, COLOR_BLACK);
        init_pair(2, COLOR_GREEN, COLOR_BLACK);
        init_pair(3, COLOR_YELLOW, COLOR_BLACK);
        init_pair(4, COLOR_RED, COLOR_BLACK);
    }

    double phase = 0.0;
    int running = 1;
    while (running) {
        sensor_read(&sc, &rd);
        const Preset *p = &BFA_PRESETS[sel];
        double eff_beat = feedback ? feedback_beat(p->beat, rd.ambient_c) : p->beat;

        erase();
        int H = LINES, W = COLS;

        /* ヘッダ */
        attron(A_BOLD | COLOR_PAIR(1));
        mvprintw(0, 1, "バイオフィードバック 音アプリ (ncurses GUI)  センサー: %s",
                 sensor_backend_name(&sc));
        attroff(A_BOLD | COLOR_PAIR(1));
        mvprintw(1, 1, "※音響トーン発生器です。薬剤/治療効果を再現・代替しません。");

        /* 左: プリセット一覧 */
        int list_top = 3, list_x = 1;
        mvprintw(list_top - 1, list_x, "[ プリセット ]");
        int max_rows = H - list_top - 9;
        if (max_rows < 4) max_rows = 4;
        int first = 0;
        if (sel >= max_rows) first = sel - max_rows + 1;
        for (int i = 0; i < max_rows && (first + i) < (int)BFA_PRESET_COUNT; i++) {
            int idx = first + i;
            if (idx == sel) attron(A_REVERSE);
            mvprintw(list_top + i, list_x, " %-14s %6.1fHz %4.1fHz %-5s ",
                     BFA_PRESETS[idx].jp, BFA_PRESETS[idx].carrier,
                     BFA_PRESETS[idx].beat, bfa_band_name(BFA_PRESETS[idx].beat));
            if (idx == sel) attroff(A_REVERSE);
        }

        /* 右: センサーパネル */
        int panel_x = 40;
        if (panel_x > W - 30) panel_x = (W > 30) ? W - 30 : 1;
        mvprintw(list_top - 1, panel_x, "[ センサー(ライブ) ]");
        attron(COLOR_PAIR(2));
        draw_gauge(list_top + 0, panel_x, 16, (rd.ambient_c - 10.0) / 30.0,
                   "温度計", rd.ambient_c, "C");
        attroff(COLOR_PAIR(2));
        attron(COLOR_PAIR(3));
        draw_gauge(list_top + 1, panel_x, 16, (rd.ir_object_c - 20.0) / 20.0,
                   "IR対象温", rd.ir_object_c, "C");
        draw_gauge(list_top + 2, panel_x, 16, rd.ir_raw, "IR生値", rd.ir_raw, "");
        attroff(COLOR_PAIR(3));
        if (rd.present) { attron(COLOR_PAIR(2)); mvprintw(list_top + 3, panel_x, "IR近接: ●検知"); attroff(COLOR_PAIR(2)); }
        else            { attron(COLOR_PAIR(4)); mvprintw(list_top + 3, panel_x, "IR近接: ○なし"); attroff(COLOR_PAIR(4)); }

        /* 選択プリセット情報 */
        mvprintw(list_top + 5, panel_x, "選択: %s", p->jp);
        mvprintw(list_top + 6, panel_x, "carrier=%.1fHz", p->carrier);
        mvprintw(list_top + 7, panel_x, "beat=%.1fHz -> 実効=%.2fHz(%s) %s",
                 p->beat, eff_beat, bfa_band_name(eff_beat),
                 feedback ? "[FB:ON]" : "[FB:OFF]");

        /* 下部: 波形 */
        int wf_top = list_top + (max_rows > 9 ? max_rows : 9) + 1;
        if (wf_top > H - 5) wf_top = H - 5;
        mvprintw(wf_top - 1, 1, "[ 波形(L=carrier) ]");
        int wf_w = W - 2;
        int wf_h = 3;
        for (int xx = 0; xx < wf_w; xx++) {
            double t = phase + (double)xx / wf_w * (3.0 / p->carrier); /* 約3周期 */
            double l, r;
            bfa_sample_at(t, p->carrier, eff_beat, &l, &r);
            int yy = wf_top + (int)((1.0 - l) * 0.5 * (wf_h - 1) + 0.5);
            mvaddch(yy, 1 + xx, '*');
        }

        /* ステータス行 */
        attron(A_REVERSE);
        mvprintw(H - 1, 0, " %-*s", W - 1, status);
        attroff(A_REVERSE);

        refresh();
        phase += 0.02;

        int ch = getch();
        switch (ch) {
            case 'q': case 'Q': running = 0; break;
            case KEY_UP: case 'k': if (sel > 0) sel--; break;
            case KEY_DOWN: case 'j': if (sel < (int)BFA_PRESET_COUNT - 1) sel++; break;
            case 'b': case 'B': feedback = !feedback;
                snprintf(status, sizeof(status), "バイオフィードバック %s (温度で beat 変調)",
                         feedback ? "ON" : "OFF"); break;
            case 'p': case 'P': case '\n': case KEY_ENTER: {
                char path[256];
                snprintf(path, sizeof(path), "/tmp/bfa_%s.wav", p->key);
                bfa_play_wav(path, p->carrier, eff_beat, 15.0);
                snprintf(status, sizeof(status), "再生(試行): %s eff_beat=%.2fHz -> %s",
                         p->jp, eff_beat, path);
                break;
            }
            case 's': case 'S': {
                char path[256];
                snprintf(path, sizeof(path), "%s.wav", p->key);
                if (bfa_write_wav(path, p->carrier, eff_beat, 30.0) == 0)
                    snprintf(status, sizeof(status), "保存: %s (30s)", path);
                else
                    snprintf(status, sizeof(status), "保存失敗: %s", path);
                break;
            }
            default: break; /* timeout -> 再描画してライブ更新 */
        }
    }

    endwin();
    printf("終了しました。\n");
    return 0;
}
