/* ============================================================================
 *  lib/gamma_manifold.c
 *  ガンマ関数と大域的部分積分多様体 (Global Partial-Integration Manifold)
 * ==========================================================================*/
#include <math.h>
#include <stdio.h>
#include "../include/omega_silent.h"

void omega_log(const char *tag, const char *msg) {
    fprintf(stderr, "[omega:%s] %s\n", tag ? tag : "silent", msg ? msg : "");
}

/* --- Lanczos 近似による Γ(s) -------------------------------------------- */
static double gamma_lanczos(double x) {
    static const double g = 7.0;
    static const double c[9] = {
        0.99999999999980993, 676.5203681218851, -1259.1392167224028,
        771.32342877765313, -176.61502916214059, 12.507343278686905,
        -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7
    };
    if (x < 0.5) {
        /* 反射公式 Γ(x)Γ(1-x) = π / sin(πx) */
        return M_PI / (sin(M_PI * x) * gamma_lanczos(1.0 - x));
    }
    x -= 1.0;
    double a = c[0];
    double t = x + g + 0.5;
    for (int i = 1; i < 9; i++) a += c[i] / (x + i);
    return sqrt(2.0 * M_PI) * pow(t, x + 0.5) * exp(-t) * a;
}

double gamma_eval(double s) { return gamma_lanczos(s); }

double beta_eval(double p, double q) {
    return gamma_eval(p) * gamma_eval(q) / gamma_eval(p + q);
}

/* --- 大域的部分積分多様体 ---------------------------------------------- */
/* 多様体核 k(x) = 1 / (x · (log x)^2), 定義域 x>1                          */
double gpi_kernel(double x) {
    if (x <= 1.0 + 1e-12) return 0.0;
    double lx = log(x);
    return 1.0 / (x * lx * lx);
}

/* M(a,b) = ∬_a^b 1/(x·log x)^2 dx
 *
 * 解析的には ∫ 1/(x (log x)^2) dx = -1/log x なので、部分積分の閉形式は
 *   M(a,b) = 1/log a - 1/log b
 * だが、本プロトタイプでは「多様体上の nodes 個の局所チャート」を
 * 部分積分再帰で積み上げ、大域的(global)な和として構成する。
 * 各チャートは Simpson 則、境界項は部分積分の残差として合流させる。 */
double gpi_manifold(double a, double b, int nodes) {
    if (nodes < 2) nodes = 2;
    if (a <= 1.0) a = 1.0 + 1e-6;
    if (b <= a)   return 0.0;

    double h = (b - a) / (double)nodes;
    double acc = 0.0;

    for (int i = 0; i < nodes; i++) {
        double x0 = a + h * i;
        double x1 = x0 + h;
        double xm = 0.5 * (x0 + x1);
        /* Simpson: ローカルチャート上の積分 */
        double local = (h / 6.0) *
                       (gpi_kernel(x0) + 4.0 * gpi_kernel(xm) + gpi_kernel(x1));
        /* 部分積分の境界残差 (大域的接続項) [-1/log x]_{x0}^{x1} との整合補正 */
        double boundary = (1.0 / log(x0 > 1 ? x0 : 1.000001)) -
                          (1.0 / log(x1));
        /* 局所積分と境界残差を平均して大域多様体に合流 */
        acc += 0.5 * (local + boundary);
    }
    return acc;
}
