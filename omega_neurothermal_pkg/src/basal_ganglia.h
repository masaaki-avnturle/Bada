/* basal_ganglia.h
 *
 * 大脳基底核を通る「脳と体に流れるエネルギー体」のモデル。
 * Models thermal/neural energy injected by the gamma-thermal manifold into the
 * basal ganglia and propagated out to the body's extremities.
 *
 * 教育・可視化目的のシミュレーションである。
 */
#ifndef OMEGA_BASAL_GANGLIA_H
#define OMEGA_BASAL_GANGLIA_H

/* 基底核の主要核 / principal nuclei */
typedef enum {
    BG_CAUDATE = 0,   /* 尾状核   */
    BG_PUTAMEN,       /* 被殻     */
    BG_GPE,           /* 淡蒼球外節 */
    BG_GPI,           /* 淡蒼球内節 */
    BG_STN,           /* 視床下核 */
    BG_SNC,           /* 黒質緻密部 */
    BG_SNR,           /* 黒質網様部 */
    BG_NUCLEI_COUNT
} bg_nucleus_t;

/* 体の末端区分 / body segments (brain -> extremity path) */
typedef enum {
    SEG_THALAMUS = 0, /* 視床(中継) */
    SEG_TRUNK,        /* 体幹     */
    SEG_UPPER_LIMB,   /* 上肢     */
    SEG_LOWER_LIMB,   /* 下肢     */
    SEG_HAND,         /* 手末端   */
    SEG_FOOT,         /* 足末端   */
    SEG_COUNT
} body_segment_t;

typedef struct {
    double nucleus[BG_NUCLEI_COUNT];  /* 各核のエネルギー量 */
    double segment[SEG_COUNT];        /* 各体節へ伝播したエネルギー量 */
    double dopamine_gain;             /* SNc由来のドーパミン利得 */
} bg_state_t;

const char *bg_nucleus_name(bg_nucleus_t n);
const char *bg_segment_name(body_segment_t s);

/*
 * ガンマ熱多様体からの入力エネルギー source_energy を基底核へ注入し、
 * 直接路/間接路の利得を経て体末端まで伝播させる。
 * dopamine 0..1 は SNc のドーパミン作動性(直接路促進・間接路抑制)。
 */
void bg_propagate(bg_state_t *st, double source_energy, double dopamine);

/* 末端への総出力（全 SEG の合計） */
double bg_total_output(const bg_state_t *st);

#endif /* OMEGA_BASAL_GANGLIA_H */
