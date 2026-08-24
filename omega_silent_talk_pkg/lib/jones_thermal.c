/* ============================================================================
 *  lib/jones_thermal.c
 *  Jones 多項式 — 体内 / 脳 の熱エネルギー観察
 * ==========================================================================*/
#include <stdlib.h>
#include <math.h>
#include "../include/omega_silent.h"

jones_poly_t *jones_create(int degree) {
    if (degree < 0) return NULL;
    jones_poly_t *p = (jones_poly_t *)malloc(sizeof(jones_poly_t));
    if (!p) return NULL;
    p->degree = degree;
    p->coeffs = (double *)calloc((size_t)degree + 1, sizeof(double));
    if (!p->coeffs) { free(p); return NULL; }
    return p;
}

void jones_free(jones_poly_t *p) {
    if (!p) return;
    free(p->coeffs);
    free(p);
}

/* 温度時系列を絡み目 (knot) として符号化し Jones 係数を積む。
 *
 * 手順:
 *   1) 隣接差分 Δ = temps[i+1]-temps[i] の符号を「交点符号」(±1) とする。
 *   2) skein 関係の簡約版:
 *        t^{-1} V(L+) - t V(L-) = (t^{1/2}-t^{-1/2}) V(L0)
 *      を係数レベルで近似し、正交点は次数を +1、負交点は -1 方向へ寄与。
 *   3) 交点間隔 |Δ| を係数振幅に反映 (熱ゆらぎの強さ)。 */
jones_poly_t *jones_from_thermal(const double *temps, int len) {
    int crossings = (len > 1) ? (len - 1) : 1;
    int degree    = crossings;              /* 交点数 = 多項式次数 */
    jones_poly_t *p = jones_create(degree);
    if (!p) return NULL;

    p->coeffs[0] = 1.0;                      /* 自明結び目の正規化 */
    for (int i = 0; i + 1 < len; i++) {
        double d    = temps[i + 1] - temps[i];
        int    sign = (d >= 0.0) ? 1 : -1;
        double amp  = 1.0 / (1.0 + fabs(d)); /* 熱ゆらぎ振幅 (0..1] */
        int    k    = i + 1;
        /* skein 近似: 交点符号に応じて隣接次数へ寄与を分配 */
        p->coeffs[k] += sign * amp;
        p->coeffs[k - 1] += -sign * amp * 0.5;
    }
    return p;
}

double jones_eval(const jones_poly_t *p, double t) {
    if (!p || !p->coeffs) return 0.0;
    double acc = 0.0, tk = 1.0;
    for (int k = 0; k <= p->degree; k++) {
        acc += p->coeffs[k] * tk;
        tk  *= t;
    }
    return acc;
}

/* 熱意図性 (thermal intent):
 *   Boltzmann 因子 t = e^{-1/kT} を Jones 変数に代入し、
 *   |V_K(t)| を熱エネルギーの「秩序ある意図」の強度として返す。
 *   0 に近いほど無秩序 (雑音), 大きいほど構造化された思考熱。 */
double jones_thermal_intent(const jones_poly_t *p, double kT) {
    if (!p) return 0.0;
    if (kT < 1e-6) kT = 1e-6;
    double t = exp(-1.0 / kT);
    double v = jones_eval(p, t);
    /* 次数正規化で [0,1) 付近へ写像 */
    double norm = 1.0 + (double)p->degree * 0.1;
    return fabs(v) / norm;
}
