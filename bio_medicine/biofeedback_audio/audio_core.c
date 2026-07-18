/*
 * audio_core.c — プリセット定義と WAV サイン波合成の実装
 */
#define _GNU_SOURCE          /* strcasestr ほか(POSIX も内包) */
#include "audio_core.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <math.h>
#include <stdint.h>
#include <ctype.h>
#include <errno.h>
#include <locale.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

const Preset BFA_PRESETS[] = {
    /* key            jp                 carrier  beat */
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
    { "saphris",     "シクレスト",        222.0,   5.0 },
    { "sennoside",   "センノサイド",      288.0,   9.0 },
    { "akineton",    "アキネトン",        256.0,   8.0 },
    { "biperiden",   "ビペリデン",        264.0,   8.5 },
    { "amel",        "アメル",            333.0,   9.5 },
    { "benzalin",    "ベンザリン",        144.0,   2.0 },
    { "levotomin",   "レボトミン",        160.0,   4.0 },
};
const size_t BFA_PRESET_COUNT = sizeof(BFA_PRESETS) / sizeof(BFA_PRESETS[0]);

const char *bfa_band_name(double beat) {
    if (beat < 4.0)  return "delta";
    if (beat < 8.0)  return "theta";
    if (beat < 13.0) return "alpha";
    return "beta";
}

const Preset *bfa_find_preset(const char *key) {
    char buf[64];
    size_t n = 0;
    if (!key) return NULL;
    for (; key[n] && n < sizeof(buf) - 1; n++)
        buf[n] = (char)tolower((unsigned char)key[n]);
    buf[n] = '\0';
    for (size_t i = 0; i < BFA_PRESET_COUNT; i++)
        if (strcmp(BFA_PRESETS[i].key, buf) == 0)
            return &BFA_PRESETS[i];
    return NULL;
}

void bfa_sample_at(double t, double carrier, double beat,
                   double *left, double *right) {
    if (left)  *left  = sin(2.0 * M_PI * carrier * t);
    if (right) *right = sin(2.0 * M_PI * (carrier + beat) * t);
}

/* ---- WAV little-endian ヘルパ ---- */
static void wu32(FILE *f, uint32_t v) {
    uint8_t b[4] = { (uint8_t)v, (uint8_t)(v>>8), (uint8_t)(v>>16), (uint8_t)(v>>24) };
    fwrite(b, 1, 4, f);
}
static void wu16(FILE *f, uint16_t v) {
    uint8_t b[2] = { (uint8_t)v, (uint8_t)(v>>8) };
    fwrite(b, 1, 2, f);
}

int bfa_write_wav(const char *path, double carrier, double beat, double seconds) {
    if (seconds <= 0.0) seconds = 1.0;
    if (carrier <= 0.0) carrier = 1.0;

    uint32_t frames = (uint32_t)(seconds * BFA_SAMPLE_RATE + 0.5);
    uint32_t bpf    = BFA_CHANNELS * (BFA_BITS_PER_SAMP / 8);
    uint32_t dbytes = frames * bpf;

    FILE *f = fopen(path, "wb");
    if (!f) {
        fprintf(stderr, "出力を開けません '%s': %s\n", path, strerror(errno));
        return 1;
    }

    fwrite("RIFF", 1, 4, f);
    wu32(f, 36 + dbytes);
    fwrite("WAVE", 1, 4, f);
    fwrite("fmt ", 1, 4, f);
    wu32(f, 16);
    wu16(f, 1);                         /* PCM */
    wu16(f, BFA_CHANNELS);
    wu32(f, BFA_SAMPLE_RATE);
    wu32(f, BFA_SAMPLE_RATE * bpf);
    wu16(f, (uint16_t)bpf);
    wu16(f, BFA_BITS_PER_SAMP);
    fwrite("data", 1, 4, f);
    wu32(f, dbytes);

    double left_hz  = carrier;
    double right_hz = carrier + beat;
    uint32_t fade = (uint32_t)(BFA_FADE_SECONDS * BFA_SAMPLE_RATE);
    if (fade * 2 > frames) fade = frames / 2;

    for (uint32_t i = 0; i < frames; i++) {
        double t = (double)i / BFA_SAMPLE_RATE;
        double env = 1.0;
        if (fade > 0) {
            if (i < fade)                  env = (double)i / fade;
            else if (i >= frames - fade)   env = (double)(frames - 1 - i) / fade;
        }
        double lv = sin(2.0 * M_PI * left_hz  * t) * BFA_AMPLITUDE * env;
        double rv = sin(2.0 * M_PI * right_hz * t) * BFA_AMPLITUDE * env;
        wu16(f, (uint16_t)(int16_t)(lv * 32767.0));
        wu16(f, (uint16_t)(int16_t)(rv * 32767.0));
    }

    int err = ferror(f);
    fclose(f);
    if (err) {
        fprintf(stderr, "書き込みエラー '%s'\n", path);
        return 1;
    }
    return 0;
}

int bfa_play_wav(const char *path, double carrier, double beat, double seconds) {
    if (bfa_write_wav(path, carrier, beat, seconds) != 0)
        return 1;

    /* 利用可能な再生コマンドを順に試す(ベストエフォート、バックグラウンド) */
    static const char *players[] = { "aplay", "paplay", "ffplay", "afplay", NULL };
    for (int i = 0; players[i]; i++) {
        char probe[128];
        snprintf(probe, sizeof(probe), "command -v %s >/dev/null 2>&1", players[i]);
        if (system(probe) == 0) {
            char cmd[1280];
            if (strcmp(players[i], "ffplay") == 0)
                snprintf(cmd, sizeof(cmd),
                         "ffplay -autoexit -nodisp -loglevel quiet '%s' >/dev/null 2>&1 &", path);
            else
                snprintf(cmd, sizeof(cmd),
                         "%s '%s' >/dev/null 2>&1 &", players[i], path);
            if (system(cmd) == -1) return 0;
            return 0;
        }
    }
    /* プレイヤーが無くても WAV は生成済み */
    return 0;
}

double bfa_feedback_beat(double base_beat, double ambient_c) {
    double b = base_beat + (ambient_c - 24.0) * 0.5;
    if (b < 0.5)  b = 0.5;
    if (b > 30.0) b = 30.0;
    return b;
}

double bfa_feedback_carrier(double base_carrier, double ir_object_c) {
    double c = base_carrier + (ir_object_c - 30.0) * 10.0;
    if (c < 80.0)   c = 80.0;
    if (c > 1200.0) c = 1200.0;
    return c;
}

double bfa_eeg_beat(int dominant_band) {
    /* delta/theta/alpha/beta/gamma の代表周波数 */
    static const double hz[5] = { 2.5, 6.0, 10.0, 20.0, 35.0 };
    if (dominant_band < 0) dominant_band = 0;
    if (dominant_band > 4) dominant_band = 4;
    return hz[dominant_band];
}

double bfa_ecg_carrier(double base_carrier, double bpm) {
    double c = base_carrier + (bpm - 60.0) * 1.0;
    if (c < 80.0)   c = 80.0;
    if (c > 1200.0) c = 1200.0;
    return c;
}

/* 大文字小文字を無視した部分一致(strcasestr は GNU 拡張で MinGW に無いため自前実装)。 */
static int contains_ci(const char *hay, const char *needle) {
    if (!hay || !needle) return 0;
    size_t nl = strlen(needle);
    if (nl == 0) return 1;
    for (const char *p = hay; *p; p++) {
        size_t i = 0;
        while (i < nl && p[i] &&
               tolower((unsigned char)p[i]) == tolower((unsigned char)needle[i]))
            i++;
        if (i == nl) return 1;
    }
    return 0;
}

static int locale_is_utf8(const char *s) {
    if (!s) return 0;
    return contains_ci(s, "utf-8") || contains_ci(s, "utf8");
}

const char *bfa_enable_utf8_locale(void) {
    /* まず環境の指定を尊重 */
    const char *cur = setlocale(LC_ALL, "");
    if (locale_is_utf8(cur))
        return cur;

    /* 環境が UTF-8 でない(POSIX/C 等)。広く存在する UTF-8 ロケールを順に試す。
     * LC_CTYPE だけ UTF-8 にすればワイド文字/フォント選択は機能する。 */
    static const char *cands[] = {
        "C.UTF-8", "C.utf8", "en_US.UTF-8", "ja_JP.UTF-8", "ja_JP.utf8", NULL
    };
    for (int i = 0; cands[i]; i++) {
        const char *r = setlocale(LC_CTYPE, cands[i]);
        if (r) return r;
    }
    return NULL; /* 見つからなければ既定のまま */
}
