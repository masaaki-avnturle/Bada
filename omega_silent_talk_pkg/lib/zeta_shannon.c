/* ============================================================================
 *  lib/zeta_shannon.c
 *  ゼータ関数 と シャノンの公式 — 統計的言語発生スコア
 * ==========================================================================*/
#include <math.h>
#include "../include/omega_silent.h"

/* ζ(s) : s>1 の Dirichlet 級数。Euler-Maclaurin 末尾補正で加速。 */
double zeta_eval(double s) {
    if (s <= 1.0) return INFINITY;
    const int N = 200;
    double sum = 0.0;
    for (int n = 1; n <= N; n++) sum += pow((double)n, -s);
    /* 末尾 Σ_{N+1}^∞ ≈ ∫ + 補正 : N^{1-s}/(s-1) + 1/2 N^{-s} */
    double tail = pow((double)N, 1.0 - s) / (s - 1.0)
                + 0.5 * pow((double)N, -s)
                + (s / 12.0) * pow((double)N, -s - 1.0);
    return sum + tail;
}

/* H = -Σ p_i log2 p_i */
double shannon_entropy(const double *p, int n) {
    double H = 0.0;
    for (int i = 0; i < n; i++) {
        if (p[i] > 0.0) H -= p[i] * log2(p[i]);
    }
    return H;
}

/* ζ-Shannon 結合統計量:
 *   L = H(p) · ζ(s_temp)
 * counts[] を確率へ正規化し、シャノンエントロピー H を求め、
 * ゼータ重み ζ(s_temp) を掛ける。s_temp が大きいほど ζ→1 に近づき鋭くなる。 */
double zeta_shannon_score(const long *counts, int n, double s_temp) {
    long total = 0;
    for (int i = 0; i < n; i++) total += counts[i] > 0 ? counts[i] : 0;
    if (total == 0) return 0.0;

    double H = 0.0;
    for (int i = 0; i < n; i++) {
        if (counts[i] > 0) {
            double p = (double)counts[i] / (double)total;
            H -= p * log2(p);
        }
    }
    double z = (s_temp > 1.0) ? zeta_eval(s_temp) : zeta_eval(1.5);
    return H * z;
}
