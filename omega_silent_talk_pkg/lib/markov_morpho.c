/* ============================================================================
 *  lib/markov_morpho.c
 *  マルコフ連鎖 (言語発生) + 形態作用素 (design pattern = neural net)
 * ==========================================================================*/
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "../include/omega_silent.h"

/* ---- マルコフ連鎖 (1 次) ------------------------------------------------ */
struct markov_t {
    int      order;    /* 予約: 現状 1 次のみ実装 */
    int      n;        /* 状態数 */
    double  *trans;    /* n*n 遷移カウント (行=from, 列=to) */
    double  *rowsum;   /* 各行の総和 */
};

markov_t *markov_create(int order, int nstates) {
    if (nstates <= 0) nstates = 2;
    if (order   <= 0) order   = 1;
    markov_t *m = (markov_t *)calloc(1, sizeof(markov_t));
    if (!m) return NULL;
    m->order  = order;
    m->n      = nstates;
    m->trans  = (double *)calloc((size_t)nstates * nstates, sizeof(double));
    m->rowsum = (double *)calloc((size_t)nstates, sizeof(double));
    if (!m->trans || !m->rowsum) { markov_free(m); return NULL; }
    /* ラプラス平滑化 (発生ゼロを避ける) */
    for (int i = 0; i < nstates; i++) {
        for (int j = 0; j < nstates; j++) m->trans[i * nstates + j] = 1e-3;
        m->rowsum[i] = 1e-3 * nstates;
    }
    return m;
}

void markov_free(markov_t *m) {
    if (!m) return;
    free(m->trans);
    free(m->rowsum);
    free(m);
}

void markov_observe(markov_t *m, const int *seq, int len) {
    if (!m || !seq) return;
    for (int t = 0; t + 1 < len; t++) {
        int a = seq[t], b = seq[t + 1];
        if (a < 0 || a >= m->n || b < 0 || b >= m->n) continue;
        m->trans[a * m->n + b] += 1.0;
        m->rowsum[a]           += 1.0;
    }
}

double markov_prob(const markov_t *m, int state, int next) {
    if (!m || state < 0 || state >= m->n || next < 0 || next >= m->n) return 0.0;
    if (m->rowsum[state] <= 0.0) return 1.0 / m->n;
    return m->trans[state * m->n + next] / m->rowsum[state];
}

/* xorshift32 — 決定論的乱数 (再現性のため) */
static unsigned xs32(unsigned *s) {
    unsigned x = *s ? *s : 0x9e3779b9u;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    *s = x;
    return x;
}

int markov_next(const markov_t *m, int state, unsigned *rng_state) {
    if (!m || state < 0 || state >= m->n) return 0;
    double r = (double)(xs32(rng_state) & 0xffffff) / (double)0x1000000;
    double acc = 0.0;
    for (int j = 0; j < m->n; j++) {
        acc += markov_prob(m, state, j);
        if (r <= acc) return j;
    }
    return m->n - 1;
}

/* ---- 形態作用素 M[·] (neural-net 的 design pattern) --------------------- */
/* gamma-deprivation 活性:
 *   σ_Γ(x) = x / Γ(1 + |x|)
 * README の "gamma-deprivation" に対応。Γ が急増するため大振幅を抑圧する
 * 自己正規化ゲートとして働く (softmax 的だが多様体核で重みづけ)。 */
static double gamma_deprivation(double x) {
    double g = gamma_eval(1.0 + fabs(x));
    if (g < 1e-12) g = 1e-12;
    return x / g;
}

void morpho_apply(const double *in, double *out, int n) {
    if (!in || !out || n <= 0) return;

    /* 1) 各成分に gamma-deprivation 活性 */
    double norm = 0.0;
    for (int i = 0; i < n; i++) {
        out[i] = gamma_deprivation(in[i]);
        norm  += out[i] * out[i];
    }
    norm = sqrt(norm);
    if (norm < 1e-12) norm = 1.0;

    /* 2) 多様体核による位置重み付け + L2 正規化 (形態=形を保つ作用素) */
    for (int i = 0; i < n; i++) {
        double x = 2.0 + (double)i;            /* x>1 のチャート座標 */
        double w = 1.0 + gpi_kernel(x);        /* 多様体重み */
        out[i] = (out[i] / norm) * w;
    }
}
