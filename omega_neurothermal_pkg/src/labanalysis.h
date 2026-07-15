/* labanalysis.h
 *
 * 検体検査の装置機能モデル（シミュレーション）。
 *   - 血液検査: 主要マーカーの基準範囲判定
 *   - DNA 解析: 長さ/GC含量/塩基組成/k-mer
 *   - RNA 解析: 転写(DNA->RNA) と コドン→アミノ酸 翻訳
 *
 * 教育・可視化目的のみ。実検査・診断・治療判断には用いない。
 */
#ifndef OMEGA_LABANALYSIS_H
#define OMEGA_LABANALYSIS_H

#include <stddef.h>

/* ---- 血液検査 ---- */
typedef struct {
    const char *name;
    const char *unit;
    double value;
    double lo;   /* 基準下限 */
    double hi;   /* 基準上限 */
} blood_marker_t;

/* 標準パネル(グルコース,Hb,WBC,...)を value にサンプル値を入れて埋める。
 * thermal_bias は体熱エネルギーに比例した微小バイアス(デモ用)。
 * 返り値はマーカー数。 */
int blood_panel(blood_marker_t *out, int max, double thermal_bias, unsigned *seed);

/* 'L'(低)/'N'(正常)/'H'(高) を返す */
char blood_flag(const blood_marker_t *m);

/* ---- DNA 解析 ---- */
typedef struct {
    size_t length;
    size_t count[4];   /* A,C,G,T */
    double gc_content; /* 0..1 */
    int    valid;      /* 不正文字がなければ 1 */
} dna_stats_t;

/* 塩基配列(A/C/G/T、大小文字可)を解析。 */
dna_stats_t dna_analyze(const char *seq);

/* k-mer 頻度の上位を表示用に取得（簡易: k<=4）。最頻 k-mer を buf に格納。 */
void dna_top_kmer(const char *seq, int k, char *buf, size_t buflen, int *count);

/* ---- RNA 解析 ---- */
/* DNA センス鎖 -> mRNA (T->U)。out は十分大きいこと。 */
void rna_transcribe(const char *dna, char *out, size_t outlen);

/* mRNA をコドンごとに翻訳し、1文字アミノ酸列を out に書く(終止は '*')。 */
void rna_translate(const char *rna, char *out, size_t outlen);

#endif /* OMEGA_LABANALYSIS_H */
