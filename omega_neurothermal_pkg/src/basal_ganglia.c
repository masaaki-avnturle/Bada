/* basal_ganglia.c — see basal_ganglia.h */
#include "basal_ganglia.h"
#include <math.h>

static const char *NUC_NAMES[BG_NUCLEI_COUNT] = {
    "Caudate (尾状核)", "Putamen (被殻)", "GPe (淡蒼球外節)",
    "GPi (淡蒼球内節)", "STN (視床下核)", "SNc (黒質緻密部)",
    "SNr (黒質網様部)"
};
static const char *SEG_NAMES[SEG_COUNT] = {
    "Thalamus (視床)", "Trunk (体幹)", "Upper limb (上肢)",
    "Lower limb (下肢)", "Hand (手末端)", "Foot (足末端)"
};

const char *bg_nucleus_name(bg_nucleus_t n)
{
    return (n >= 0 && n < BG_NUCLEI_COUNT) ? NUC_NAMES[n] : "?";
}
const char *bg_segment_name(body_segment_t s)
{
    return (s >= 0 && s < SEG_COUNT) ? SEG_NAMES[s] : "?";
}

void bg_propagate(bg_state_t *st, double source_energy, double dopamine)
{
    if (!st) return;
    if (dopamine < 0.0) dopamine = 0.0;
    if (dopamine > 1.0) dopamine = 1.0;
    st->dopamine_gain = dopamine;

    /* 線条体(入力部)が外部エネルギーを受ける */
    double striatum = source_energy;
    st->nucleus[BG_CAUDATE] = 0.45 * striatum;
    st->nucleus[BG_PUTAMEN] = 0.55 * striatum;

    /* 黒質緻密部のドーパミン作動 */
    st->nucleus[BG_SNC] = dopamine * striatum;

    /* 直接路: 線条体 -| GPi  (ドーパミンで促進 → GPi抑制 → 視床脱抑制) */
    double direct = (st->nucleus[BG_CAUDATE] + st->nucleus[BG_PUTAMEN])
                    * (0.5 + 0.5 * dopamine);

    /* 間接路: 線条体 -| GPe -| STN -> GPi (ドーパミンで抑制) */
    st->nucleus[BG_GPE] = striatum * (0.5 - 0.4 * dopamine);
    if (st->nucleus[BG_GPE] < 0.0) st->nucleus[BG_GPE] = 0.0;
    st->nucleus[BG_STN] = 0.6 * striatum - 0.5 * st->nucleus[BG_GPE];
    if (st->nucleus[BG_STN] < 0.0) st->nucleus[BG_STN] = 0.0;
    double indirect = st->nucleus[BG_STN] * (1.0 - dopamine);

    /* GPi/SNr 出力 = 間接路 - 直接路（抑制性出力。低いほど運動が通る） */
    st->nucleus[BG_GPI] = fmax(0.0, 0.8 * indirect - 0.6 * direct + 0.3 * striatum);
    st->nucleus[BG_SNR] = 0.5 * st->nucleus[BG_GPI];

    /* 視床は GPi 抑制から脱抑制された分だけ通過させる */
    double thalamus_drive = fmax(0.0, striatum - st->nucleus[BG_GPI]);
    st->segment[SEG_THALAMUS] = thalamus_drive;

    /* 視床 → 体末端へ、距離減衰(指数)で伝播 */
    static const double dist[SEG_COUNT] = {0.0, 1.0, 2.2, 2.6, 3.4, 4.0};
    const double lambda = 0.28; /* 減衰係数 */
    for (int s = SEG_TRUNK; s < SEG_COUNT; ++s)
        st->segment[s] = thalamus_drive * exp(-lambda * dist[s]);
}

double bg_total_output(const bg_state_t *st)
{
    double sum = 0.0;
    if (!st) return 0.0;
    for (int s = 0; s < SEG_COUNT; ++s) sum += st->segment[s];
    return sum;
}
