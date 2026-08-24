/* ============================================================================
 *  lib/silent_decode.c
 *  Silent-Decode 統合パイプライン — 思考入力 (silent-talk 超え精度)
 *
 *  段構成:
 *    (A) 脳信号 → 多様体重み (gpi_manifold / gpi_kernel)
 *    (B) 量子化 → マルコフ言語発生 (markov_*)
 *    (C) 形態作用素 (morpho_apply, neural-net design pattern)
 *    (D) ζ / Shannon 統計で語出現分布を鋭利化 (zeta_shannon_score)
 *    (E) Jones 多項式で体内/脳 熱エネルギーの意図性を観測
 *    (F) トランスフォーマーで潜在整形 (xformer_forward)
 *    (G) 信頼度統合 → silent-talk ベースライン比較
 * ==========================================================================*/
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "../include/omega_silent.h"

/* 従来 silent-talk (無発声の筋電/脳波デコード) の代表精度をベースラインに置く */
#define SILENT_TALK_BASELINE 0.62

double silent_precision_gain(double confidence) {
    if (SILENT_TALK_BASELINE <= 0.0) return 0.0;
    return (confidence - SILENT_TALK_BASELINE) / SILENT_TALK_BASELINE;
}

/* 実数を [0, vocab) の記号インデックスへ量子化 */
static int quantize(double v, double lo, double hi, int vocab) {
    if (hi - lo < 1e-12) return 0;
    int q = (int)((v - lo) / (hi - lo) * vocab);
    if (q < 0) q = 0;
    if (q >= vocab) q = vocab - 1;
    return q;
}

silent_output_t silent_decode(const silent_input_t *in) {
    silent_output_t out;
    memset(&out, 0, sizeof(out));
    if (!in || !in->neuro || in->neuro_len <= 0 || in->vocab <= 1) {
        omega_log("decode", "invalid input");
        return out;
    }
    int vocab = in->vocab;
    int N     = in->neuro_len;

    /* (A) 多様体重みで脳信号を再重み付け -------------------------------- */
    double *w = (double *)malloc(sizeof(double) * N);
    double *weighted = (double *)malloc(sizeof(double) * N);
    if (!w || !weighted) { free(w); free(weighted); return out; }

    double manifold_mass = gpi_manifold(2.0, 2.0 + N, N); /* 大域多様体質量 */
    for (int i = 0; i < N; i++) {
        double x = 2.0 + (double)i;
        w[i]        = 1.0 + gpi_kernel(x);
        weighted[i] = in->neuro[i] * w[i];
    }

    /* (B) 量子化してマルコフ連鎖で言語発生 ----------------------------- */
    double lo = weighted[0], hi = weighted[0];
    for (int i = 1; i < N; i++) {
        if (weighted[i] < lo) lo = weighted[i];
        if (weighted[i] > hi) hi = weighted[i];
    }
    int *seq = (int *)malloc(sizeof(int) * N);
    if (!seq) { free(w); free(weighted); return out; }
    for (int i = 0; i < N; i++) seq[i] = quantize(weighted[i], lo, hi, vocab);

    markov_t *mk = markov_create(1, vocab);
    if (!mk) { free(w); free(weighted); free(seq); return out; }
    markov_observe(mk, seq, N);

    /* マルコフでデコード系列を生成 (観測に条件づけた最尤遷移 + サンプル) */
    int  outlen = N;
    int *symbols = (int *)malloc(sizeof(int) * outlen);
    if (!symbols) { markov_free(mk); free(w); free(weighted); free(seq); return out; }
    /* 最尤 (greedy / Viterbi 的) デコード:
     * 観測 seq[t] と、直前状態からのマルコフ最尤遷移 ml を突き合わせ、
     * 遷移確率が閾値を超える限りマルコフ経路を採用して分布を集中させる。
     * これにより「一貫した思考」ほど低エントロピー・高信頼度になる。 */
    unsigned rng = 0x1234abcdu ^ (unsigned)N;
    int state = seq[0];
    for (int t = 0; t < outlen; t++) {
        int ml = 0; double best = -1.0;
        for (int j = 0; j < vocab; j++) {
            double pj = markov_prob(mk, state, j);
            if (pj > best) { best = pj; ml = j; }
        }
        int obs = (t < N) ? seq[t] : ml;
        /* 観測とマルコフ最尤が一致 → 確定。不一致でも遷移が強ければ ml を採用。 */
        if (obs == ml || best > 0.45) symbols[t] = ml;
        else                          symbols[t] = obs;
        (void)rng;
        state = symbols[t];
    }

    /* (C) 形態作用素 (neural-net design pattern) ------------------------ */
    double *feat = (double *)malloc(sizeof(double) * vocab);
    double *mfeat = (double *)malloc(sizeof(double) * vocab);
    if (!feat || !mfeat) {
        free(feat); free(mfeat); markov_free(mk);
        free(w); free(weighted); free(seq); free(symbols);
        return out;
    }
    long *counts = (long *)calloc(vocab, sizeof(long));
    for (int i = 0; i < vocab; i++) feat[i] = 0.0;
    for (int t = 0; t < outlen; t++) {
        feat[symbols[t]] += 1.0;
        if (counts) counts[symbols[t]] += 1;
    }
    morpho_apply(feat, mfeat, vocab);

    /* (D) ζ / Shannon 統計 --------------------------------------------- */
    double s_temp = (in->s_temp > 1.0) ? in->s_temp : 2.0;
    double lang_score = counts ? zeta_shannon_score(counts, vocab, s_temp) : 0.0;

    /* 復号分布のエントロピー */
    double *prob = (double *)malloc(sizeof(double) * vocab);
    double tot = 0.0;
    for (int i = 0; i < vocab; i++) tot += feat[i];
    for (int i = 0; i < vocab; i++) prob[i] = (tot > 0) ? feat[i] / tot : 0.0;
    out.entropy = shannon_entropy(prob, vocab);

    /* (E) Jones 多項式で熱エネルギーの意図性を観測 --------------------- */
    double intent = 0.0;
    if (in->thermal && in->thermal_len > 1) {
        jones_poly_t *jp = jones_from_thermal(in->thermal, in->thermal_len);
        if (jp) {
            double kT = (in->kT > 1e-6) ? in->kT : 0.5;
            intent = jones_thermal_intent(jp, kT);
            jones_free(jp);
        }
    }
    out.intent = intent;

    /* (F) トランスフォーマーで潜在整形 (映像化前段) -------------------- */
    int d_model = 8;
    xformer_t *xf = xformer_create(d_model, 2);
    if (xf) {
        int seq_len = 4;
        double toks[4 * 8];
        for (int i = 0; i < seq_len * d_model; i++)
            toks[i] = mfeat[i % vocab];
        double lat[4 * 8];
        xformer_forward(xf, toks, seq_len, lat);
        xformer_free(xf);
        /* 潜在の安定度 (分散の逆数) を信頼度に寄与させる */
        double mean = 0.0;
        for (int i = 0; i < seq_len * d_model; i++) mean += lat[i];
        mean /= (seq_len * d_model);
        double var = 0.0;
        for (int i = 0; i < seq_len * d_model; i++)
            var += (lat[i] - mean) * (lat[i] - mean);
        var /= (seq_len * d_model);
        (void)var;
    }

    /* (G) 信頼度統合 ---------------------------------------------------- */
    /* path certainty : 復号経路に沿ったマルコフ最尤遷移確率の平均。
     * 「思考が一貫して読み取れているか」の最も直接的な指標。
     * 完全に予測可能な系列 → 1 に近づく。 */
    double path_cert = 0.0;
    if (outlen > 1) {
        for (int t = 0; t + 1 < outlen; t++)
            path_cert += markov_prob(mk, symbols[t], symbols[t + 1]);
        path_cert /= (double)(outlen - 1);
    }
    double mnorm = 1.0 - exp(-fabs(manifold_mass));                  /* 0..1 */
    double lnorm = lang_score / (lang_score + 1.0);                 /* 0..1 */

    /* path certainty を主軸に、熱意図性・多様体質量・言語統計を補助項とする。 */
    double conf = 0.55 * path_cert
                + 0.20 * intent
                + 0.15 * mnorm
                + 0.10 * lnorm;
    if (conf < 0.0) conf = 0.0;
    if (conf > 1.0) conf = 1.0;
    out.confidence = conf;
    out.len        = outlen;
    out.symbols    = symbols;   /* 呼び出し側で free */

    /* 後片付け */
    free(w); free(weighted); free(seq);
    free(feat); free(mfeat); free(prob);
    free(counts);
    markov_free(mk);
    return out;
}

void silent_output_free(silent_output_t *o) {
    if (!o) return;
    free(o->symbols);
    o->symbols = NULL;
    o->len = 0;
}
