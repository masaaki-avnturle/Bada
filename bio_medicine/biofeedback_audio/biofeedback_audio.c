/*
 * biofeedback_audio.c
 *
 * バイオフィードバック用 音（サイン波）ジェネレータ
 * Biofeedback sound (sine-wave) generator.
 *
 * 概要 / Overview
 * ---------------
 * 名前付きプリセット（リスパダール, ジプレキサ, ... など）それぞれに
 * 「キャリア周波数」と「バイノーラルビート周波数」を割り当て、
 * 16bit / 44.1kHz / ステレオ の WAV ファイルとして音を生成します。
 *
 * - 左チャンネル : sin(2*pi*carrier*t)
 * - 右チャンネル : sin(2*pi*(carrier+beat)*t)
 *   左右の周波数差(beat)が「うなり(binaural beat)」として知覚され、
 *   リラクゼーション/集中などのバイオフィードバック用途で使われる手法です。
 * - フェードイン/アウトのエンベロープでクリックノイズを抑制します。
 *
 * 重要な注意 / IMPORTANT
 * ----------------------
 * 本プログラムは「音響トーン発生器」です。プリセット名は単なるラベルであり、
 * 薬剤そのものや、その薬効・治療効果を再現・代替するものではありません。
 * 特定の周波数に医学的・治療的効果があるという主張は一切しません。
 * 体調・治療に関する判断は必ず医師・薬剤師に相談してください。
 * 大音量での長時間使用は避け、不快を感じたら直ちに中止してください。
 *
 * This program is purely a tone generator. Preset names are labels only and do
 * not reproduce or substitute any medication or its clinical effect. No medical
 * or therapeutic claim is made about any frequency.
 *
 * ビルド / Build
 * --------------
 *   gcc -std=c99 -O2 -Wall -o biofeedback_audio biofeedback_audio.c -lm
 *
 * 使い方 / Usage
 * --------------
 *   ./biofeedback_audio list
 *   ./biofeedback_audio gen <preset|all> [seconds] [outdir]
 *   ./biofeedback_audio custom <carrier_hz> <beat_hz> <seconds> <out.wav>
 *
 * 例 / Examples
 * -------------
 *   ./biofeedback_audio list
 *   ./biofeedback_audio gen risperdal 30
 *   ./biofeedback_audio gen all 20 ./out
 *   ./biofeedback_audio custom 200 8 60 alpha.wav
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdint.h>
#include <ctype.h>
#include <errno.h>
#include <sys/stat.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define SAMPLE_RATE   44100
#define CHANNELS      2
#define BITS_PER_SAMP 16
#define AMPLITUDE     0.45      /* 0.0 .. 1.0  ピーク振幅(クリッピング回避のため余裕を持たせる) */
#define FADE_SECONDS  0.05      /* フェードイン/アウト時間(秒) */

/*
 * プリセット表
 * key    : コマンドラインで指定する英字キー
 * jp     : 日本語ラベル(表示用)
 * carrier: キャリア周波数(Hz) ... 心地よい可聴域に分散配置
 * beat   : バイノーラルビート周波数(Hz) ... EEG帯域(delta/theta/alpha/beta)を意識
 *
 * beat の目安:
 *   ~0.5-4 Hz : delta (深い休息)
 *   ~4-8  Hz : theta (深いリラックス)
 *   ~8-13 Hz : alpha (リラックス/集中の橋渡し)
 *   ~13-30 Hz: beta  (覚醒/集中)
 */
typedef struct {
    const char *key;
    const char *jp;
    double      carrier;
    double      beat;
} Preset;

static const Preset PRESETS[] = {
    /* key            jp(日本語)          carrier  beat */
    { "risperdal",   "リスパダール",      174.0,   3.0 },
    { "zyprexa",     "ジプレキサ",        185.0,   3.5 },
    { "silece",      "サイレース",        110.0,   1.5 },
    { "depas",       "デパス",            210.0,   6.0 },
    { "etizolam",    "エチゾラム",        216.0,   6.5 },
    { "brotizolam",  "ブロチゾラム",      128.0,   2.0 },
    { "rohypnol",    "ロヒプノール",      120.0,   1.0 },
    { "sancoba",     "サンコバ",          396.0,  10.0 },
    { "hyaluronic",  "ヒアルロン酸",      417.0,  10.5 },
    { "lendormin",   "レンドルミン",      132.0,   2.5 },
    { "luran",       "ルーラン",          198.0,   4.5 },
    { "saphris",     "シクレスト",        222.0,   5.0 },  /* asenapine / Sycrest */
    { "sennoside",   "センノサイド",      288.0,   9.0 },
    { "akineton",    "アキネトン",        256.0,   8.0 },
    { "biperiden",   "ビペリデン",        264.0,   8.5 },
    { "amel",        "アメル",            333.0,   9.5 },
    { "benzalin",    "ベンザリン",        144.0,   2.0 },
    { "levotomin",   "レボトミン",        160.0,   4.0 },
};
static const size_t PRESET_COUNT = sizeof(PRESETS) / sizeof(PRESETS[0]);

/* ---- 小さなユーティリティ ---------------------------------------------- */

static void write_u32_le(FILE *f, uint32_t v) {
    uint8_t b[4] = { (uint8_t)(v), (uint8_t)(v >> 8),
                     (uint8_t)(v >> 16), (uint8_t)(v >> 24) };
    fwrite(b, 1, 4, f);
}

static void write_u16_le(FILE *f, uint16_t v) {
    uint8_t b[2] = { (uint8_t)(v), (uint8_t)(v >> 8) };
    fwrite(b, 1, 2, f);
}

/* EEG帯域名(beat周波数から判定) */
static const char *band_name(double beat) {
    if (beat < 4.0)   return "delta(深い休息)";
    if (beat < 8.0)   return "theta(深いリラックス)";
    if (beat < 13.0)  return "alpha(リラックス)";
    return "beta(覚醒/集中)";
}

/* ---- WAV 書き出し ------------------------------------------------------ */

/*
 * carrier   : 左チャンネルの基準周波数(Hz)
 * beat      : 右チャンネルに加える差分(Hz) -> バイノーラルビート
 * seconds   : 長さ(秒)
 * path      : 出力 WAV パス
 * 戻り値: 0=成功, 非0=失敗
 */
static int write_wav(const char *path, double carrier, double beat, double seconds) {
    if (seconds <= 0.0) seconds = 1.0;

    uint32_t total_frames = (uint32_t)(seconds * SAMPLE_RATE + 0.5);
    uint32_t bytes_per_frame = CHANNELS * (BITS_PER_SAMP / 8);
    uint32_t data_bytes = total_frames * bytes_per_frame;

    FILE *f = fopen(path, "wb");
    if (!f) {
        fprintf(stderr, "出力を開けません '%s': %s\n", path, strerror(errno));
        return 1;
    }

    /* ---- RIFF / WAVE ヘッダ ---- */
    fwrite("RIFF", 1, 4, f);
    write_u32_le(f, 36 + data_bytes);          /* ChunkSize */
    fwrite("WAVE", 1, 4, f);

    /* ---- fmt サブチャンク ---- */
    fwrite("fmt ", 1, 4, f);
    write_u32_le(f, 16);                        /* Subchunk1Size (PCM=16) */
    write_u16_le(f, 1);                         /* AudioFormat (PCM=1) */
    write_u16_le(f, CHANNELS);
    write_u32_le(f, SAMPLE_RATE);
    write_u32_le(f, SAMPLE_RATE * bytes_per_frame); /* ByteRate */
    write_u16_le(f, (uint16_t)bytes_per_frame);     /* BlockAlign */
    write_u16_le(f, BITS_PER_SAMP);

    /* ---- data サブチャンク ---- */
    fwrite("data", 1, 4, f);
    write_u32_le(f, data_bytes);

    double left_hz  = carrier;
    double right_hz = carrier + beat;
    uint32_t fade = (uint32_t)(FADE_SECONDS * SAMPLE_RATE);
    if (fade * 2 > total_frames) fade = total_frames / 2;

    for (uint32_t i = 0; i < total_frames; i++) {
        double t = (double)i / SAMPLE_RATE;

        /* フェードイン/アウトのエンベロープ(0..1) */
        double env = 1.0;
        if (fade > 0) {
            if (i < fade)
                env = (double)i / fade;
            else if (i >= total_frames - fade)
                env = (double)(total_frames - 1 - i) / fade;
        }

        double lv = sin(2.0 * M_PI * left_hz  * t) * AMPLITUDE * env;
        double rv = sin(2.0 * M_PI * right_hz * t) * AMPLITUDE * env;

        int16_t ls = (int16_t)(lv * 32767.0);
        int16_t rs = (int16_t)(rv * 32767.0);
        write_u16_le(f, (uint16_t)ls);
        write_u16_le(f, (uint16_t)rs);
    }

    if (ferror(f)) {
        fprintf(stderr, "書き込みエラー '%s'\n", path);
        fclose(f);
        return 1;
    }
    fclose(f);
    return 0;
}

/* ---- コマンド ---------------------------------------------------------- */

static const Preset *find_preset(const char *key) {
    for (size_t i = 0; i < PRESET_COUNT; i++)
        if (strcmp(PRESETS[i].key, key) == 0)
            return &PRESETS[i];
    return NULL;
}

static void cmd_list(void) {
    printf("利用可能なプリセット (%zu 件):\n", PRESET_COUNT);
    printf("  %-12s %-16s %8s %6s  %s\n",
           "KEY", "ラベル", "carrier", "beat", "帯域");
    printf("  ------------ ---------------- -------- ------  --------------------\n");
    for (size_t i = 0; i < PRESET_COUNT; i++) {
        printf("  %-12s %-16s %6.1fHz %4.1fHz  %s\n",
               PRESETS[i].key, PRESETS[i].jp,
               PRESETS[i].carrier, PRESETS[i].beat,
               band_name(PRESETS[i].beat));
    }
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
    if (outdir && outdir[0] != '\0')
        snprintf(path, sizeof(path), "%s/%s.wav", outdir, p->key);
    else
        snprintf(path, sizeof(path), "%s.wav", p->key);

    if (write_wav(path, p->carrier, p->beat, seconds) != 0)
        return 1;

    printf("生成: %-16s -> %-24s  carrier=%.1fHz beat=%.1fHz(%s) %.1fs\n",
           p->jp, path, p->carrier, p->beat, band_name(p->beat), seconds);
    return 0;
}

static int cmd_gen(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s gen <preset|all> [seconds] [outdir]\n", argv[0]);
        return 1;
    }
    const char *target = argv[2];
    double seconds = (argc >= 4) ? atof(argv[3]) : 30.0;
    const char *outdir = (argc >= 5) ? argv[4] : "";

    if (seconds <= 0.0) {
        fprintf(stderr, "秒数は正の値で指定してください。\n");
        return 1;
    }
    if (ensure_dir(outdir) != 0) return 1;

    if (strcmp(target, "all") == 0) {
        int rc = 0;
        for (size_t i = 0; i < PRESET_COUNT; i++)
            rc |= gen_one(&PRESETS[i], seconds, outdir);
        printf("\n完了: %zu ファイルを生成しました。\n", PRESET_COUNT);
        return rc;
    }

    /* キーは大文字小文字を無視して照合 */
    char keybuf[64];
    size_t n = 0;
    for (; target[n] && n < sizeof(keybuf) - 1; n++)
        keybuf[n] = (char)tolower((unsigned char)target[n]);
    keybuf[n] = '\0';

    const Preset *p = find_preset(keybuf);
    if (!p) {
        fprintf(stderr, "未知のプリセット '%s'。'list' で一覧を確認してください。\n", target);
        return 1;
    }
    return gen_one(p, seconds, outdir);
}

static int cmd_custom(int argc, char **argv) {
    if (argc < 6) {
        fprintf(stderr, "Usage: %s custom <carrier_hz> <beat_hz> <seconds> <out.wav>\n", argv[0]);
        return 1;
    }
    double carrier = atof(argv[2]);
    double beat    = atof(argv[3]);
    double seconds = atof(argv[4]);
    const char *out = argv[5];

    if (carrier <= 0.0 || seconds <= 0.0) {
        fprintf(stderr, "carrier と seconds は正の値で指定してください。\n");
        return 1;
    }
    if (write_wav(out, carrier, beat, seconds) != 0) return 1;

    printf("生成: %s  carrier=%.1fHz beat=%.1fHz(%s) %.1fs\n",
           out, carrier, beat, band_name(beat), seconds);
    return 0;
}

static void usage(const char *prog) {
    printf("バイオフィードバック 音(サイン波)ジェネレータ\n\n");
    printf("Usage:\n");
    printf("  %s list\n", prog);
    printf("  %s gen <preset|all> [seconds] [outdir]\n", prog);
    printf("  %s custom <carrier_hz> <beat_hz> <seconds> <out.wav>\n\n", prog);
    printf("注意: 本ツールは音響トーン発生器です。プリセット名はラベルであり、\n");
    printf("      薬剤や治療効果を再現・代替するものではありません。\n");
}

int main(int argc, char **argv) {
    if (argc < 2) {
        usage(argv[0]);
        return 1;
    }
    if (strcmp(argv[1], "list") == 0)   return cmd_list(), 0;
    if (strcmp(argv[1], "gen") == 0)    return cmd_gen(argc, argv);
    if (strcmp(argv[1], "custom") == 0) return cmd_custom(argc, argv);

    if (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0) {
        usage(argv[0]);
        return 0;
    }
    fprintf(stderr, "未知のコマンド '%s'\n\n", argv[1]);
    usage(argv[0]);
    return 1;
}
