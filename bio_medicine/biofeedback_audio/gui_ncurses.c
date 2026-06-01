/*
 * gui_ncurses.c — 端末GUI(ncurses) フロントエンド
 *
 * 機能:
 *   - プリセット一覧の選択(↑↓ / j k)
 *   - 赤外線(IR)センサー + 温度計 のライブ表示(バーゲージ)
 *   - 選択プリセットの波形(ASCII)表示
 *   - 再生(p/Enter: WAV生成+外部プレイヤー) / WAV保存(s)
 *   - r: リアルタイム連続再生(ALSA)の ON/OFF
 *   - b: バイオフィードバックモード ON/OFF
 *       温度計 -> beat 周波数、IR対象温度 -> carrier 周波数 を変調
 *       (リアルタイム再生中はセンサー値に追従して音が変化)
 *
 * 重要: 音響トーン発生器です。プリセット名はラベルであり、薬剤や治療効果を
 *       再現・代替しません(医学的主張なし)。
 *
 * ビルド: Makefile 参照(ALSA があれば -DBFA_HAVE_ALSA で実時間再生有効)
 * 実行:
 *   ./bfa_tui            (端末GUI)
 *   ./bfa_tui --selftest (画面を開かず内部ロジックを検証して終了)
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
#include <ncurses.h>

/* ---- 画面を開かない自己診断(コンテナ等での検証用) ---- */
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
    /* EEG/ECG */
    BioCtx bc; bio_init(&bc);
    BioReading br;
    for (int i = 0; i < 40; i++) bio_read(&bc, &br);
    printf("[selftest] biosignal backend = %s\n", bio_backend_name(&bc));
    printf("[selftest] EEG dominant=%s -> beat=%.1fHz   ECG bpm=%.1f -> carrier=%.1fHz\n",
           bio_band_name(br.eeg_dominant), bfa_eeg_beat(br.eeg_dominant),
           br.bpm, bfa_ecg_carrier(p->carrier, br.bpm));
    if (bfa_write_wav("/tmp/bfa_selftest.wav", p->carrier, p->beat, 0.5) != 0) {
        printf("[selftest] WAV write FAILED\n");
        return 1;
    }
    printf("[selftest] WAV write OK (/tmp/bfa_selftest.wav)\n[selftest] OK\n");
    return 0;
}

/* 水平バーゲージを描画 */
static void draw_gauge(int y, int x, int width, double frac, const char *label,
                       double value, const char *unit) {
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
    BioCtx bc; bio_init(&bc);
    BioReading br; memset(&br, 0, sizeof(br));

    RtAudio *rt = rt_audio_create();   /* ALSA 非対応ビルドでは NULL */

    int sel = 0;
    int feedback = 0;   /* 温度/IR -> beat/carrier */
    int neuro = 0;      /* EEG/ECG -> beat/carrier */
    int realtime = 0;
    char status[512] = "↑↓:選択 p:再生 s:保存 r:実時間 b:温度FB e:脳波/心電FB q:終了";

    initscr();
    if (!stdscr) { fprintf(stderr, "端末を初期化できません(TTYで実行してください)\n"); return 1; }
    cbreak(); noecho(); keypad(stdscr, TRUE); curs_set(0);
    timeout(150);
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
        bio_read(&bc, &br);
        const Preset *p = &BFA_PRESETS[sel];
        /* 周波数決定の優先順位: 脳波/心電FB > 温度/IR FB > プリセット既定 */
        double eff_carrier = p->carrier, eff_beat = p->beat;
        if (feedback) {
            eff_carrier = bfa_feedback_carrier(p->carrier, rd.ir_object_c);
            eff_beat    = bfa_feedback_beat(p->beat, rd.ambient_c);
        }
        if (neuro) {
            eff_carrier = bfa_ecg_carrier(p->carrier, br.bpm);   /* 心拍 -> carrier */
            eff_beat    = bfa_eeg_beat(br.eeg_dominant);         /* 脳波支配帯域 -> beat */
        }

        /* リアルタイム再生中は周波数をライブ更新 */
        if (realtime && rt && rt_audio_is_running(rt))
            rt_audio_set_freq(rt, eff_carrier, eff_beat);

        erase();
        int H = LINES, W = COLS;

        attron(A_BOLD | COLOR_PAIR(1));
        mvprintw(0, 1, "バイオフィードバック 音アプリ (ncurses)  センサー:%s  実時間:%s",
                 sensor_backend_name(&sc),
                 (realtime && rt_audio_is_running(rt)) ? "ON" :
                 (rt_audio_available() ? "OFF" : "N/A"));
        attroff(A_BOLD | COLOR_PAIR(1));
        mvprintw(1, 1, "※音響トーン発生器です。薬剤/治療効果を再現・代替しません。");

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

        mvprintw(list_top + 5, panel_x, "選択: %s %s%s", p->jp,
                 feedback ? "[温度FB]" : "", neuro ? "[脳波/心電FB]" : "");
        mvprintw(list_top + 6, panel_x, "carrier=%.1fHz -> 実効=%.1fHz", p->carrier, eff_carrier);
        mvprintw(list_top + 7, panel_x, "beat=%.1fHz -> 実効=%.2fHz(%s)",
                 p->beat, eff_beat, bfa_band_name(eff_beat));

        /* --- 脳波計(EEG) + 心電図(ECG) パネル --- */
        int bio_y = list_top + 9;
        attron(A_BOLD); mvprintw(bio_y - 1, panel_x, "[ 脳波計/心電図 %s ]", bio_backend_name(&bc)); attroff(A_BOLD);
        attron(COLOR_PAIR(1));
        for (int b = 0; b < BIO_BAND_COUNT; b++)
            draw_gauge(bio_y + b, panel_x, 16, br.eeg_band[b],
                       bio_band_name(b), br.eeg_band[b] * 100.0, "%");
        attroff(COLOR_PAIR(1));
        mvprintw(bio_y + BIO_BAND_COUNT, panel_x, "EEG支配帯域: %-6s (-> beat %.1fHz)",
                 bio_band_name(br.eeg_dominant), bfa_eeg_beat(br.eeg_dominant));
        if (br.beat) attron(COLOR_PAIR(4) | A_BOLD);
        mvprintw(bio_y + BIO_BAND_COUNT + 1, panel_x, "ECG 心拍: %5.1f bpm %s",
                 br.bpm, br.beat ? "♥ R" : "  ");
        if (br.beat) attroff(COLOR_PAIR(4) | A_BOLD);

        /* ECG 波形(1行ミニ表示) */
        int ecg_y = bio_y + BIO_BAND_COUNT + 2;
        if (ecg_y < H - 3 && br.ecg_count > 0) {
            int ecg_w = (W - panel_x - 2);
            if (ecg_w > 40) ecg_w = 40;
            mvprintw(ecg_y, panel_x, "ECG:");
            for (int xx = 0; xx < ecg_w; xx++) {
                int idx = (int)((double)xx / ecg_w * (ECG_WIN - 1));
                float v = br.ecg_wave[idx];
                char ch2 = (v > 0.5) ? '^' : (v > 0.1) ? '\'' : (v < -0.1) ? '.' : '-';
                mvaddch(ecg_y, panel_x + 5 + xx, ch2);
            }
        }

        int wf_top = list_top + (max_rows > 9 ? max_rows : 9) + 1;
        if (wf_top > H - 5) wf_top = H - 5;
        mvprintw(wf_top - 1, 1, "[ 波形(L=carrier) ]");
        int wf_w = W - 2, wf_h = 3;
        for (int xx = 0; xx < wf_w; xx++) {
            double t = phase + (double)xx / wf_w * (3.0 / eff_carrier);
            double l, r;
            bfa_sample_at(t, eff_carrier, eff_beat, &l, &r);
            int yy = wf_top + (int)((1.0 - l) * 0.5 * (wf_h - 1) + 0.5);
            mvaddch(yy, 1 + xx, '*');
        }

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
            case 'b': case 'B':
                feedback = !feedback;
                if (feedback) neuro = 0;
                snprintf(status, sizeof(status),
                         "温度FB %s (温度->beat, IR->carrier)", feedback ? "ON" : "OFF");
                break;
            case 'e': case 'E':
                neuro = !neuro;
                if (neuro) feedback = 0;
                snprintf(status, sizeof(status),
                         "脳波/心電FB %s (脳波支配帯域->beat, 心拍->carrier)", neuro ? "ON" : "OFF");
                break;
            case 'r': case 'R':
                if (!rt_audio_available()) {
                    snprintf(status, sizeof(status), "実時間再生はこのビルドで無効(ALSA無し)");
                } else if (realtime && rt_audio_is_running(rt)) {
                    rt_audio_stop(rt); realtime = 0;
                    snprintf(status, sizeof(status), "実時間再生 停止");
                } else {
                    rt_audio_set_freq(rt, eff_carrier, eff_beat);
                    if (rt_audio_start(rt) == 0) {
                        realtime = 1;
                        snprintf(status, sizeof(status), "実時間再生 開始(ALSA)");
                    } else {
                        snprintf(status, sizeof(status), "実時間再生 失敗(出力デバイス無し?)");
                    }
                }
                break;
            case 'p': case 'P': case '\n': case KEY_ENTER: {
                char path[256];
                snprintf(path, sizeof(path), "/tmp/bfa_%s.wav", p->key);
                bfa_play_wav(path, eff_carrier, eff_beat, 15.0);
                snprintf(status, sizeof(status), "再生(試行): %s c=%.0f b=%.2f",
                         p->jp, eff_carrier, eff_beat);
                break;
            }
            case 's': case 'S': {
                char path[256];
                snprintf(path, sizeof(path), "%s.wav", p->key);
                if (bfa_write_wav(path, eff_carrier, eff_beat, 30.0) == 0)
                    snprintf(status, sizeof(status), "保存: %s (30s)", path);
                else
                    snprintf(status, sizeof(status), "保存失敗");
                break;
            }
            default: break;
        }
    }

    if (rt) rt_audio_destroy(rt);
    endwin();
    printf("終了しました。\n");
    return 0;
}
