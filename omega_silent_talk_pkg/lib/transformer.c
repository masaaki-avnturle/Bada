/* ============================================================================
 *  lib/transformer.c
 *  映像化トランスフォーマー (Visualization Transformer)
 *  π-softmax / ℏ_eff 注意スケーリング (README omega_llm に対応)
 * ==========================================================================*/
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "../include/omega_silent.h"

struct xformer_t {
    int    d_model;
    int    heads;
    double hbar_eff;   /* ℏ_eff 注意スケール */
};

xformer_t *xformer_create(int d_model, int heads) {
    if (d_model <= 0) d_model = 8;
    if (heads   <= 0) heads   = 1;
    if (d_model % heads != 0) heads = 1;
    xformer_t *x = (xformer_t *)calloc(1, sizeof(xformer_t));
    if (!x) return NULL;
    x->d_model  = d_model;
    x->heads    = heads;
    x->hbar_eff = 1.0 / sqrt((double)(d_model / heads));
    return x;
}

void xformer_free(xformer_t *x) { free(x); }

/* π-softmax:
 *   a_i = exp(π · ℏ_eff · s_i) / Σ_j exp(π · ℏ_eff · s_j)
 * README の pi_softmax 実装に整合。 */
static void pi_softmax(const double *s, double *a, int n, double hbar) {
    double mx = s[0];
    for (int i = 1; i < n; i++) if (s[i] > mx) mx = s[i];
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        a[i] = exp(M_PI * hbar * (s[i] - mx));
        sum += a[i];
    }
    if (sum < 1e-12) sum = 1e-12;
    for (int i = 0; i < n; i++) a[i] /= sum;
}

/* 単一ブロックの自己注意 (Q=K=V=tokens, スケール ℏ_eff) */
void xformer_forward(xformer_t *x, const double *tokens, int seq_len, double *out) {
    if (!x || !tokens || !out || seq_len <= 0) return;
    int d = x->d_model;
    double *scores = (double *)malloc(sizeof(double) * seq_len);
    double *attn   = (double *)malloc(sizeof(double) * seq_len);
    if (!scores || !attn) { free(scores); free(attn); return; }

    for (int i = 0; i < seq_len; i++) {
        /* i 番目クエリと全キーの内積 */
        for (int j = 0; j < seq_len; j++) {
            double dot = 0.0;
            for (int k = 0; k < d; k++)
                dot += tokens[i * d + k] * tokens[j * d + k];
            scores[j] = dot * x->hbar_eff;
        }
        pi_softmax(scores, attn, seq_len, x->hbar_eff);
        /* 注意加重和 → 残差接続 */
        for (int k = 0; k < d; k++) {
            double acc = 0.0;
            for (int j = 0; j < seq_len; j++)
                acc += attn[j] * tokens[j * d + k];
            out[i * d + k] = tokens[i * d + k] + acc;   /* residual */
        }
    }
    free(scores);
    free(attn);
}

/* 潜在表現を w*h グレースケールフレームへ投影 (映像化) */
void xformer_render(xformer_t *x, const double *latent, int seq_len,
                    unsigned char *frame, int w, int h) {
    if (!x || !latent || !frame || w <= 0 || h <= 0) return;
    int d = x->d_model;
    double mn = 1e300, mx = -1e300;
    for (int i = 0; i < seq_len * d; i++) {
        if (latent[i] < mn) mn = latent[i];
        if (latent[i] > mx) mx = latent[i];
    }
    double range = (mx - mn) > 1e-12 ? (mx - mn) : 1.0;

    for (int y = 0; y < h; y++) {
        for (int px = 0; px < w; px++) {
            /* 潜在格子を画素にマッピング */
            int si = (int)((double)px / w * seq_len);
            int ki = (int)((double)y  / h * d);
            if (si >= seq_len) si = seq_len - 1;
            if (ki >= d)       ki = d - 1;
            double v = (latent[si * d + ki] - mn) / range;
            frame[y * w + px] = (unsigned char)(v * 255.0);
        }
    }
}
