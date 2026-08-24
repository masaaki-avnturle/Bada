/* ============================================================================
 *  omega_silent.h  —  omega_silent_talk_pkg
 *
 *  Gamma-function Global Partial-Integration Manifold AGI
 *  思考入力エンジン (silent-talk 超え精度) の共通ヘッダ
 *
 *  理論対応 (レポート群より):
 *    Γ(s)              : gamma_eval           — ガンマ関数
 *    ∬ 1/(x·log x)² dx : gpi_manifold         — 大域的部分積分多様体
 *    ζ(s)              : zeta_eval            — ゼータ関数
 *    H = -Σ p log p    : shannon_entropy      — シャノンの公式
 *    Markov P(w_t|w_-) : markov_*             — マルコフ連鎖 (言語発生)
 *    形態作用素 M[·]    : morpho_apply         — 形態作用素 (design pattern = NN)
 *    V_K(t)            : jones_thermal_*      — Jones 多項式 (体内/脳 熱エネルギー)
 *    Transformer       : xformer_*            — 映像化トランスフォーマー
 *    silent decode     : silent_decode_*      — 思考入力デコード統合パイプライン
 *
 *  © 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research
 *  Prototype — research / conceptual implementation.
 * ==========================================================================*/
#ifndef OMEGA_SILENT_H
#define OMEGA_SILENT_H

#include <stddef.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* --- log helper --------------------------------------------------------- */
void omega_log(const char *tag, const char *msg);

/* ========================================================================
 *  1. ガンマ関数 / 大域的部分積分多様体 (Global Partial-Integration Manifold)
 * ======================================================================== */

/* Γ(s) : Lanczos 近似による実ガンマ関数 */
double gamma_eval(double s);

/* β(p,q) = Γ(p)Γ(q)/Γ(p+q) : ベータ積分 (README の ζ(s)=β(p,q)/log x に対応) */
double beta_eval(double p, double q);

/* 大域的部分積分多様体 M(a,b) = ∬_a^b 1/(x·log x)² dx を
 * 部分積分の再帰核で数値評価する。多様体上のノード重みとして用いる。 */
double gpi_manifold(double a, double b, int nodes);

/* 多様体核 k(x) = 1/(x·(log x)^2) の単点評価 (x>1) */
double gpi_kernel(double x);

/* ========================================================================
 *  2. ゼータ関数 / シャノンの公式 (統計的言語発生)
 * ======================================================================== */

/* ζ(s) : s>1 の Dirichlet 級数 (加速収束付き部分和) */
double zeta_eval(double s);

/* シャノンエントロピー H = -Σ p_i log2 p_i (確率ベクトル入力) */
double shannon_entropy(const double *p, int n);

/* ζ-Shannon 結合統計量:
 * 記号出現頻度 counts[] から、ζ 重み付きの言語発生スコアを返す。
 * L = H(counts) · ζ(s_temp)  — 温度 s_temp で言語生成の鋭さを制御。 */
double zeta_shannon_score(const long *counts, int n, double s_temp);

/* ========================================================================
 *  3. マルコフ連鎖 (言語発生) + 形態作用素 (design pattern = neural net)
 * ======================================================================== */

typedef struct markov_t markov_t;

markov_t *markov_create(int order, int nstates);
void      markov_free(markov_t *m);
/* 観測系列 (状態インデックス列) を投入し遷移統計を更新 */
void      markov_observe(markov_t *m, const int *seq, int len);
/* 現在状態から次状態をサンプリング (rng_state は xorshift シード) */
int       markov_next(const markov_t *m, int state, unsigned *rng_state);
/* 遷移確率 P(next|state) */
double    markov_prob(const markov_t *m, int state, int next);

/* 形態作用素 M[v] : ニューラルネット的な非線形変換を design pattern として適用。
 * gamma-deprivation 活性 σ_Γ(x) = x·Γ(1+ x)^{-1} を各成分に作用させ、
 * 多様体核で正規化する。in/out は長さ n のベクトル。 */
void morpho_apply(const double *in, double *out, int n);

/* ========================================================================
 *  4. Jones 多項式 — 体内 / 脳の熱エネルギー観察
 * ======================================================================== */

typedef struct {
    int     degree;
    double *coeffs;   /* coeffs[k] = t^k の係数 */
} jones_poly_t;

jones_poly_t *jones_create(int degree);
void          jones_free(jones_poly_t *p);

/* 温度サンプル列 temps[](体内/脳の熱エネルギー時系列, ケルビン相当) から
 * 絡み目不変量として Jones 係数を構築する。
 * 熱ゆらぎの符号交差を交点(crossing)として符号化。 */
jones_poly_t *jones_from_thermal(const double *temps, int len);

/* V_K(t) を実点 t で評価 */
double jones_eval(const jones_poly_t *p, double t);

/* 熱エネルギーの「意図性」指標 :
 * Jones 不変量の t=e^{-E/kT} での値から、思考の活性度スカラを返す。 */
double jones_thermal_intent(const jones_poly_t *p, double kT);

/* ========================================================================
 *  5. 映像化トランスフォーマー (Visualization Transformer)
 * ======================================================================== */

typedef struct xformer_t xformer_t;

/* d_model 次元, heads ヘッド数の軽量トランスフォーマーを生成 */
xformer_t *xformer_create(int d_model, int heads);
void       xformer_free(xformer_t *x);

/* π-softmax 注意 (README: ℏ_eff 注意スケーリング) を用いた 1 ブロック前向き計算。
 * tokens[seq_len * d_model] → out[seq_len * d_model]。 */
void xformer_forward(xformer_t *x, const double *tokens, int seq_len, double *out);

/* 潜在表現を映像フレーム(グレースケール w*h)へ投影する。 */
void xformer_render(xformer_t *x, const double *latent, int seq_len,
                    unsigned char *frame, int w, int h);

/* ========================================================================
 *  6. Silent-Decode 統合パイプライン (思考入力)
 * ======================================================================== */

typedef struct {
    /* --- 入力 --- */
    const double *neuro;      /* 脳信号サンプル (EEG/近赤外 等の代理) */
    int           neuro_len;
    const double *thermal;    /* 体内/脳 熱エネルギー時系列 */
    int           thermal_len;
    /* --- パラメータ --- */
    int    vocab;             /* 記号(語)数 */
    double s_temp;            /* ζ 温度 */
    double kT;                /* 熱スケール */
} silent_input_t;

typedef struct {
    double  confidence;       /* 復号信頼度 0..1 (silent-talk 超え指標) */
    double  intent;           /* Jones 熱意図性 */
    double  entropy;          /* 復号分布のエントロピー */
    int     len;              /* 復号された記号数 */
    int    *symbols;          /* 復号記号列 (呼び出し側で free) */
} silent_output_t;

/* 全段(多様体重み→マルコフ言語発生→形態作用素→ζ/Shannon 統計→Jones 熱→
 * トランスフォーマー整形)を通した思考入力デコード。 */
silent_output_t silent_decode(const silent_input_t *in);
void            silent_output_free(silent_output_t *o);

/* 信頼度を従来 silent-talk ベースライン (=0.62 と仮定) と比較した超過率 */
double silent_precision_gain(double confidence);

#ifdef __cplusplus
}
#endif
#endif /* OMEGA_SILENT_H */
