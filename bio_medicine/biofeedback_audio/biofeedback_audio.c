/*
 * biofeedback_audio.c — CLI フロントエンド
 *
 * バイオフィードバック用 音(サイン波)ジェネレータのコマンドライン版。
 * 音合成は audio_core に分離(GUI 版と共有)。
 *
 * 重要: 本プログラムは音響トーン発生器です。プリセット名はラベルであり、
 *       薬剤や治療効果を再現・代替するものではありません(医学的主張なし)。
 *
 * ビルド:
 *   gcc -std=c99 -O2 -Wall -o biofeedback_audio biofeedback_audio.c audio_core.c -lm
 * 使い方:
 *   ./biofeedback_audio list
 *   ./biofeedback_audio gen <preset|all> [seconds] [outdir]
 *   ./biofeedback_audio play <preset> [seconds]
 *   ./biofeedback_audio custom <carrier_hz> <beat_hz> <seconds> <out.wav>
 */
#define _POSIX_C_SOURCE 200809L
#include "audio_core.h"
#include "sensors.h"
#include "biosignal.h"
#include "oracle.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <time.h>
#include <sys/stat.h>

/* 短い待機(ミリ秒)。usleep は POSIX.2008 で廃止のため nanosleep を使う */
static void sleep_ms(long ms) {
    struct timespec ts = { ms / 1000, (ms % 1000) * 1000000L };
    nanosleep(&ts, NULL);
}

static void cmd_list(void) {
    printf("利用可能なプリセット (%zu 件):\n", BFA_PRESET_COUNT);
    printf("  %-12s %-16s %8s %6s  %s\n", "KEY", "ラベル", "carrier", "beat", "帯域");
    printf("  ------------ ---------------- -------- ------  ------\n");
    for (size_t i = 0; i < BFA_PRESET_COUNT; i++)
        printf("  %-12s %-16s %6.1fHz %4.1fHz  %s\n",
               BFA_PRESETS[i].key, BFA_PRESETS[i].jp,
               BFA_PRESETS[i].carrier, BFA_PRESETS[i].beat,
               bfa_band_name(BFA_PRESETS[i].beat));
    printf("\n生成: ./biofeedback_audio gen <KEY|all> [秒] [出力先]\n");
}

static int ensure_dir(const char *dir) {
    if (!dir || dir[0] == '\0') return 0;
    if (mkdir(dir, 0755) != 0 && errno != EEXIST) {
        fprintf(stderr, "ディレクトリを作成できません '%s': %s\n", dir, strerror(errno));
        return 1;
    }
    return 0;
}

static int gen_one(const Preset *p, double seconds, const char *outdir) {
    char path[1024];
    if (outdir && outdir[0])
        snprintf(path, sizeof(path), "%s/%s.wav", outdir, p->key);
    else
        snprintf(path, sizeof(path), "%s.wav", p->key);
    if (bfa_write_wav(path, p->carrier, p->beat, seconds) != 0) return 1;
    printf("生成: %-16s -> %-24s carrier=%.1fHz beat=%.1fHz(%s) %.1fs\n",
           p->jp, path, p->carrier, p->beat, bfa_band_name(p->beat), seconds);
    return 0;
}

static int cmd_gen(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "Usage: %s gen <preset|all> [seconds] [outdir]\n", argv[0]); return 1; }
    const char *target = argv[2];
    double seconds = (argc >= 4) ? atof(argv[3]) : 30.0;
    const char *outdir = (argc >= 5) ? argv[4] : "";
    if (seconds <= 0.0) { fprintf(stderr, "秒数は正の値で。\n"); return 1; }
    if (ensure_dir(outdir) != 0) return 1;

    if (strcmp(target, "all") == 0) {
        int rc = 0;
        for (size_t i = 0; i < BFA_PRESET_COUNT; i++) rc |= gen_one(&BFA_PRESETS[i], seconds, outdir);
        printf("\n完了: %zu ファイルを生成しました。\n", BFA_PRESET_COUNT);
        return rc;
    }
    const Preset *p = bfa_find_preset(target);
    if (!p) { fprintf(stderr, "未知のプリセット '%s'。'list' を参照。\n", target); return 1; }
    return gen_one(p, seconds, outdir);
}

static int cmd_play(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "Usage: %s play <preset> [seconds]\n", argv[0]); return 1; }
    const Preset *p = bfa_find_preset(argv[2]);
    if (!p) { fprintf(stderr, "未知のプリセット '%s'。\n", argv[2]); return 1; }
    double seconds = (argc >= 4) ? atof(argv[3]) : 15.0;
    char path[256];
    snprintf(path, sizeof(path), "/tmp/bfa_%s.wav", p->key);
    if (bfa_play_wav(path, p->carrier, p->beat, seconds) != 0) return 1;
    printf("再生(試行): %s carrier=%.1fHz beat=%.1fHz(%s) %.1fs -> %s\n",
           p->jp, p->carrier, p->beat, bfa_band_name(p->beat), seconds, path);
    return 0;
}

static int cmd_custom(int argc, char **argv) {
    if (argc < 6) { fprintf(stderr, "Usage: %s custom <carrier_hz> <beat_hz> <seconds> <out.wav>\n", argv[0]); return 1; }
    double carrier = atof(argv[2]), beat = atof(argv[3]), seconds = atof(argv[4]);
    const char *out = argv[5];
    if (carrier <= 0.0 || seconds <= 0.0) { fprintf(stderr, "carrier と seconds は正の値で。\n"); return 1; }
    if (bfa_write_wav(out, carrier, beat, seconds) != 0) return 1;
    printf("生成: %s carrier=%.1fHz beat=%.1fHz(%s) %.1fs\n",
           out, carrier, beat, bfa_band_name(beat), seconds);
    return 0;
}

/* 脳波計(EEG) + 心電図(ECG) のライブモニタ(テキスト) */
static int cmd_bio(int argc, char **argv) {
    int frames = (argc >= 3) ? atoi(argv[2]) : 40;
    if (frames <= 0) frames = 40;

    BioCtx ctx; bio_init(&ctx);
    printf("脳波計(EEG) + 心電図(ECG) モニタ  バックエンド:%s\n", bio_backend_name(&ctx));
    printf("EEG=%dHz/%dch相当(1ch) ECG=%dHz  (Ctrl-C で中断)\n\n", EEG_FS, 1, ECG_FS);

    BioReading r;
    for (int k = 0; k < frames; k++) {
        bio_read(&ctx, &r);
        /* EEG 帯域パワーを百分率で */
        printf("\rEEG ");
        for (int b = 0; b < BIO_BAND_COUNT; b++)
            printf("%s:%-3.0f%% ", bio_band_name(b), r.eeg_band[b] * 100);
        printf("| 支配=%-5s  ECG bpm=%5.1f %s     ",
               bio_band_name(r.eeg_dominant), r.bpm, r.beat ? "♥" : " ");
        fflush(stdout);
        sleep_ms(120);
    }
    printf("\n\nEEG -> 推奨 beat = %.1fHz (%s)\n",
           bfa_eeg_beat(r.eeg_dominant), bio_band_name(r.eeg_dominant));
    printf("ECG -> 推奨 carrier(base200) = %.1fHz (bpm=%.1f)\n",
           bfa_ecg_carrier(200.0, r.bpm), r.bpm);
    printf("\n注意: 医療機器ではありません。教育・可視化・バイオフィードバック用途。\n");
    return 0;
}

/* 娯楽オラクル(お告げ)。乱数で定型メッセージを選び、連動プリセットを表示。 */
static int cmd_oracle(int argc, char **argv) {
    int draws = (argc >= 3) ? atoi(argv[2]) : 1;
    if (draws <= 0) draws = 1;

    /* 種はセンサー/生体値 + 時刻で合成(娯楽演出) */
    SensorCtx sc; sensor_init(&sc); SensorReading sr;
    BioCtx bc; bio_init(&bc); BioReading brd;
    for (int i = 0; i < 20; i++) { sensor_read(&sc, &sr); bio_read(&bc, &brd); }

    printf("🔮 オラクル(お告げ)  %s\n\n", oracle_disclaimer_jp());
    for (int d = 0; d < draws; d++) {
        unsigned long seed = (unsigned long)time(NULL)
            ^ ((unsigned long)d << 3)
            ^ (unsigned long)(sr.ir_object_c * 1000)
            ^ ((unsigned long)brd.bpm << 8);
        const OracleCard *c = oracle_draw(seed, BFA_PRESET_COUNT);
        int pr = c->preset;
        if (pr < 0 || pr >= (int)BFA_PRESET_COUNT) pr = 0;
        printf("  [%s] %s\n", oracle_mood_jp(c->mood), c->jp);
        printf("     連動音: %s (carrier=%.1fHz beat=%.1fHz)\n\n",
               BFA_PRESETS[pr].jp, BFA_PRESETS[pr].carrier, BFA_PRESETS[pr].beat);
        sensor_read(&sc, &sr); bio_read(&bc, &brd);
    }
    return 0;
}

static void usage(const char *prog) {
    printf("バイオフィードバック 音(サイン波)ジェネレータ — CLI\n\n");
    printf("Usage:\n");
    printf("  %s list\n", prog);
    printf("  %s gen <preset|all> [seconds] [outdir]\n", prog);
    printf("  %s play <preset> [seconds]\n", prog);
    printf("  %s custom <carrier_hz> <beat_hz> <seconds> <out.wav>\n", prog);
    printf("  %s bio [frames]     (脳波計EEG + 心電図ECG ライブモニタ)\n", prog);
    printf("  %s oracle [draws]   (娯楽オラクル/お告げ。予知ではありません)\n\n", prog);
    printf("注意: 音響トーン発生器です。プリセット名はラベルであり、薬剤や\n");
    printf("      治療効果を再現・代替するものではありません。\n");
    printf("GUI 版: ./bfa_tui (ncurses) / ./bfa_gui (X11) / ./bfa_gtk (GTK)\n");
}

int main(int argc, char **argv) {
    if (argc < 2) { usage(argv[0]); return 1; }
    if (!strcmp(argv[1], "list"))   { cmd_list(); return 0; }
    if (!strcmp(argv[1], "gen"))    return cmd_gen(argc, argv);
    if (!strcmp(argv[1], "play"))   return cmd_play(argc, argv);
    if (!strcmp(argv[1], "custom")) return cmd_custom(argc, argv);
    if (!strcmp(argv[1], "bio"))    return cmd_bio(argc, argv);
    if (!strcmp(argv[1], "oracle")) return cmd_oracle(argc, argv);
    if (!strcmp(argv[1], "-h") || !strcmp(argv[1], "--help")) { usage(argv[0]); return 0; }
    fprintf(stderr, "未知のコマンド '%s'\n\n", argv[1]);
    usage(argv[0]);
    return 1;
}
