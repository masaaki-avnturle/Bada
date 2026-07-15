/*
 * sensors.c — IR センサー + 温度計 抽象化の実装
 */
#define _POSIX_C_SOURCE 200809L
#include "sensors.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

static long now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long)ts.tv_sec * 1000L + ts.tv_nsec / 1000000L;
}

/* ファイルから先頭の数値(double)を読む。成功で 0 */
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

void sensor_init(SensorCtx *ctx) {
    memset(ctx, 0, sizeof(*ctx));
    const char *tp = getenv("BFA_TEMP_PATH");
    const char *ip = getenv("BFA_IR_PATH");
    if (tp) { strncpy(ctx->temp_path, tp, sizeof(ctx->temp_path) - 1); }
    if (ip) { strncpy(ctx->ir_path,   ip, sizeof(ctx->ir_path)   - 1); }

    /* どちらか一方でも実ファイルが読めれば FILE バックエンド */
    double probe;
    int real = 0;
    if (ctx->temp_path[0] && read_number_file(ctx->temp_path, &probe) == 0) real = 1;
    if (ctx->ir_path[0]   && read_number_file(ctx->ir_path,   &probe) == 0) real = 1;

    ctx->backend  = real ? SENSOR_BACKEND_FILE : SENSOR_BACKEND_SIM;
    ctx->sim_seed = (unsigned)time(NULL);
    ctx->sim_t    = 0.0;
}

const char *sensor_backend_name(const SensorCtx *ctx) {
    return ctx->backend == SENSOR_BACKEND_FILE ? "FILE/sysfs(実機)" : "SIM(シミュレーション)";
}

/* sysfs thermal_zone は millidegC。値が大きすぎる場合は /1000 する */
static double normalize_temp(double v) {
    if (v > 200.0) return v / 1000.0;  /* 例: 36500 -> 36.5 */
    return v;
}

static double frand(unsigned *seed) {
    /* 軽量な擬似乱数 0..1 */
    *seed = (*seed * 1103515245u + 12345u);
    return ((*seed >> 16) & 0x7fff) / 32767.0;
}

int sensor_read(SensorCtx *ctx, SensorReading *out) {
    out->ts_ms = now_ms();

    if (ctx->backend == SENSOR_BACKEND_FILE) {
        double t, ir;
        int got_t  = (read_number_file(ctx->temp_path, &t)  == 0);
        int got_ir = (read_number_file(ctx->ir_path,   &ir) == 0);

        out->ambient_c   = got_t  ? normalize_temp(t)  : 25.0;
        out->ir_object_c = got_ir ? normalize_temp(ir) : out->ambient_c;
        /* IR 生値: 体温域(30-40C)を 0..1 に正規化 */
        double r = (out->ir_object_c - 20.0) / 20.0;
        if (r < 0) r = 0;
        if (r > 1) r = 1;
        out->ir_raw  = r;
        out->present = (out->ir_object_c >= 28.0) ? 1 : 0; /* 体温域なら検知 */
        return 0;
    }

    /* --- シミュレーション --- */
    ctx->sim_t += 0.1;
    double drift_amb = 24.0 + 1.5 * sin(ctx->sim_t * 0.05);          /* 室温 ~24C 揺らぎ */
    double noise_amb = (frand(&ctx->sim_seed) - 0.5) * 0.3;
    out->ambient_c   = drift_amb + noise_amb;

    /* IR 対象: 人体相当 ~36.5C を中心に呼吸様の周期で揺らす */
    double breath    = 0.4 * sin(ctx->sim_t * 0.8);
    double noise_ir  = (frand(&ctx->sim_seed) - 0.5) * 0.2;
    out->ir_object_c = 36.5 + breath + noise_ir;

    double r = (out->ir_object_c - 20.0) / 20.0;
    if (r < 0) r = 0;
    if (r > 1) r = 1;
    out->ir_raw  = r;
    /* 近接検知: 周期的に対象が出入りする様子を模擬 */
    out->present = (sin(ctx->sim_t * 0.13) > -0.5) ? 1 : 0;
    return 0;
}
