/*
 * biosignal.c — 脳波計(EEG) + 心電図(ECG) 抽象化の実装
 */
#define _POSIX_C_SOURCE 200809L
#include "biosignal.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#if defined(_WIN32)
#include <windows.h>
#endif

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* 帯域の代表周波数(Goertzel 用) と 表示名 */
static const double BAND_HZ[BIO_BAND_COUNT]   = { 2.5, 6.0, 10.0, 20.0, 35.0 };
static const char  *BAND_NAME[BIO_BAND_COUNT] = { "delta", "theta", "alpha", "beta", "gamma" };

static long now_ms(void) {
#if defined(_WIN32)
    return (long)GetTickCount64();   /* Windows: 単調増加のミリ秒 */
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long)ts.tv_sec * 1000L + ts.tv_nsec / 1000000L;
#endif
}

static double frand(unsigned *seed) {
    *seed = (*seed * 1103515245u + 12345u);
    return ((*seed >> 16) & 0x7fff) / 32767.0;
}

static int read_number_file(const char *path, double *out) {
    if (!path || path[0] == '\0') return -1;
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    double v;
    int n = fscanf(f, "%lf", &v);
    fclose(f);
    if (n != 1) return -1;
    *out = v;
    return 0;
}

const char *bio_band_name(int band_index) {
    if (band_index < 0 || band_index >= BIO_BAND_COUNT) return "?";
    return BAND_NAME[band_index];
}

const char *bio_backend_name(const BioCtx *ctx) {
    return ctx->backend == BIO_BACKEND_FILE ? "FILE(実機)" : "SIM(シミュレーション)";
}

void bio_init(BioCtx *ctx) {
    memset(ctx, 0, sizeof(*ctx));
    const char *ep = getenv("BFA_EEG_PATH");
    const char *cp = getenv("BFA_ECG_PATH");
    if (ep) strncpy(ctx->eeg_path, ep, sizeof(ctx->eeg_path) - 1);
    if (cp) strncpy(ctx->ecg_path, cp, sizeof(ctx->ecg_path) - 1);

    double probe;
    int real = 0;
    if (ctx->eeg_path[0] && read_number_file(ctx->eeg_path, &probe) == 0) real = 1;
    if (ctx->ecg_path[0] && read_number_file(ctx->ecg_path, &probe) == 0) real = 1;

    ctx->backend    = real ? BIO_BACKEND_FILE : BIO_BACKEND_SIM;
    ctx->seed       = (unsigned)time(NULL) ^ 0x9e3779b9u;
    ctx->sim_hr     = 72.0;          /* 安静時心拍 */
    ctx->bpm_smooth = 72.0;
    ctx->last_peak_no = -1;
}

/* リングバッファ push */
static void push_ring(double *buf, int win, int *head, int *filled, double v) {
    buf[*head] = v;
    *head = (*head + 1) % win;
    if (*filled < win) (*filled)++;
}

/* リングバッファを時系列順に out[win] へ展開(古い→新しい) */
static void linearize(const double *buf, int win, int head, int filled, double *out) {
    /* filled < win のときは先頭側を 0 埋め */
    int start = (filled < win) ? 0 : head;
    int pad   = win - filled;
    for (int i = 0; i < pad; i++) out[i] = 0.0;
    for (int i = 0; i < filled; i++)
        out[pad + i] = buf[(start + i) % win];
}

/* Goertzel: 信号 x[n] (n=0..N-1) の周波数 f の相対パワー */
static double goertzel_power(const double *x, int N, double f, double fs) {
    double w = 2.0 * M_PI * f / fs;
    double cw = cos(w), coeff = 2.0 * cw;
    double s0 = 0, s1 = 0, s2 = 0;
    for (int n = 0; n < N; n++) {
        s0 = x[n] + coeff * s1 - s2;
        s2 = s1;
        s1 = s0;
    }
    double power = s1 * s1 + s2 * s2 - coeff * s1 * s2;
    return power > 0 ? power : 0;
}

/* EEG 帯域パワー + 支配帯域を計算 */
static void analyze_eeg(BioCtx *ctx, BioReading *out) {
    double lin[EEG_WIN];
    linearize(ctx->eeg_buf, EEG_WIN, ctx->eeg_head, ctx->eeg_filled, lin);

    /* 平均除去(DC 成分を抜く) */
    double mean = 0;
    for (int i = 0; i < EEG_WIN; i++) mean += lin[i];
    mean /= EEG_WIN;
    for (int i = 0; i < EEG_WIN; i++) lin[i] -= mean;

    double total = 0;
    for (int b = 0; b < BIO_BAND_COUNT; b++) {
        double p = goertzel_power(lin, EEG_WIN, BAND_HZ[b], EEG_FS);
        out->eeg_band[b] = p;
        total += p;
    }
    int dom = 0;
    double best = -1;
    for (int b = 0; b < BIO_BAND_COUNT; b++) {
        out->eeg_band[b] = (total > 0) ? out->eeg_band[b] / total : 0.0;
        if (out->eeg_band[b] > best) { best = out->eeg_band[b]; dom = b; }
    }
    out->eeg_dominant = dom;

    /* 表示用波形(正規化) */
    double maxa = 1e-9;
    for (int i = 0; i < EEG_WIN; i++) { double a = fabs(lin[i]); if (a > maxa) maxa = a; }
    for (int i = 0; i < EEG_WIN; i++) out->eeg_wave[i] = (float)(lin[i] / maxa);
    out->eeg_count = ctx->eeg_filled;
}

/* ECG R 波検出 + BPM。新規に push したサンプルだけ判定する */
static void detect_ecg(BioCtx *ctx, const double *new_samples, int n, BioReading *out) {
    out->beat = 0;
    /* 適応しきい値: 直近ウィンドウの最大振幅の 60% */
    double lin[ECG_WIN];
    linearize(ctx->ecg_buf, ECG_WIN, ctx->ecg_head, ctx->ecg_filled, lin);
    double maxa = 1e-9;
    for (int i = 0; i < ECG_WIN; i++) { double a = fabs(lin[i]); if (a > maxa) maxa = a; }
    double thr = 0.6 * maxa;
    int refractory_samples = (int)(0.25 * ECG_FS); /* 250ms 不応期 */

    for (int i = 0; i < n; i++) {
        ctx->ecg_sample_no++;
        if (ctx->refractory > 0) { ctx->refractory--; continue; }
        if (new_samples[i] > thr) {
            /* R 波検出 */
            if (ctx->last_peak_no >= 0) {
                long d = ctx->ecg_sample_no - ctx->last_peak_no;
                if (d > 0) {
                    double inst_bpm = 60.0 * ECG_FS / (double)d;
                    if (inst_bpm > 30 && inst_bpm < 220)
                        ctx->bpm_smooth = 0.8 * ctx->bpm_smooth + 0.2 * inst_bpm;
                }
            }
            ctx->last_peak_no = ctx->ecg_sample_no;
            ctx->refractory   = refractory_samples;
            out->beat = 1;
        }
    }
    out->bpm = ctx->bpm_smooth;

    /* 表示用波形 */
    for (int i = 0; i < ECG_WIN; i++) out->ecg_wave[i] = (float)(lin[i] / maxa);
    out->ecg_count = ctx->ecg_filled;
}

/* --- シミュレーション波形生成 --- */

/* EEG: 帯域成分の重ね合わせ。時間でゆっくり alpha<->beta が優勢に揺らぐ */
static double sim_eeg_sample(BioCtx *ctx) {
    ctx->eeg_t += 1.0 / EEG_FS;
    double t = ctx->eeg_t;
    /* 各帯域の振幅をゆっくり変調 */
    double a_alpha = 0.8 + 0.6 * sin(t * 0.07);
    double a_beta  = 0.5 + 0.4 * cos(t * 0.05);
    double v =
        0.6 * sin(2 * M_PI * 2.5  * t) +          /* delta */
        0.5 * sin(2 * M_PI * 6.0  * t) +          /* theta */
        a_alpha * sin(2 * M_PI * 10.0 * t) +      /* alpha */
        a_beta  * sin(2 * M_PI * 20.0 * t) +      /* beta  */
        0.3 * sin(2 * M_PI * 35.0 * t);           /* gamma */
    v += (frand(&ctx->seed) - 0.5) * 0.4;         /* ノイズ */
    return v * 0.25;
}

/* ECG: 心拍周期に同期した簡易 QRS(ガウシアン合成) */
static double sim_ecg_sample(BioCtx *ctx) {
    ctx->ecg_t += 1.0 / ECG_FS;
    /* 心拍数をゆっくり揺らす(呼吸性洞性不整脈) */
    double hr = ctx->sim_hr + 4.0 * sin(ctx->ecg_t * 0.25);
    double period = 60.0 / hr;
    double ph = fmod(ctx->ecg_t, period) / period; /* 0..1 心周期位相 */

    /* P(0.15), Q(-,0.33), R(+,0.38), S(-,0.43), T(0.65) をガウシアンで近似 */
    double v = 0;
    #define GAUSS(c,w,a) (a) * exp(-((ph-(c))*(ph-(c)))/(2.0*(w)*(w)))
    v += GAUSS(0.15, 0.025, 0.12);   /* P */
    v += GAUSS(0.33, 0.012, -0.18);  /* Q */
    v += GAUSS(0.38, 0.010, 1.0);    /* R */
    v += GAUSS(0.43, 0.012, -0.25);  /* S */
    v += GAUSS(0.65, 0.045, 0.30);   /* T */
    #undef GAUSS
    v += (frand(&ctx->seed) - 0.5) * 0.03;
    return v;
}

int bio_read(BioCtx *ctx, BioReading *out) {
    memset(out, 0, sizeof(*out));
    out->ts_ms = now_ms();

    /* --- EEG サンプル取り込み --- */
    for (int i = 0; i < EEG_STEP; i++) {
        double v;
        if (ctx->backend == BIO_BACKEND_FILE && read_number_file(ctx->eeg_path, &v) == 0) {
            /* 実機: 任意スケール。緩やかに正規化 */
            v = v / 100.0;
        } else {
            v = sim_eeg_sample(ctx);
        }
        push_ring(ctx->eeg_buf, EEG_WIN, &ctx->eeg_head, &ctx->eeg_filled, v);
    }
    analyze_eeg(ctx, out);

    /* --- ECG サンプル取り込み --- */
    double new_ecg[ECG_STEP];
    for (int i = 0; i < ECG_STEP; i++) {
        double v;
        if (ctx->backend == BIO_BACKEND_FILE && read_number_file(ctx->ecg_path, &v) == 0) {
            v = v / 1000.0;
        } else {
            v = sim_ecg_sample(ctx);
        }
        new_ecg[i] = v;
        push_ring(ctx->ecg_buf, ECG_WIN, &ctx->ecg_head, &ctx->ecg_filled, v);
    }
    detect_ecg(ctx, new_ecg, ECG_STEP, out);

    return 0;
}
