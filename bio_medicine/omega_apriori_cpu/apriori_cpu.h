/*
 * apriori_cpu.h  —  Ω-Apriori Core : 未知事前エンジン CPU の中核
 *
 * テロメア分裂細胞の原理で自己構成する FPGA 様ロジックファブリック。
 * 各セルは 4 入力 LUT + ルーティング選択 + テロメアカウンタを持ち、
 * 分裂(再構成)ごとにテロメアが短縮し、Hayflick 限界でセンセッセント化する。
 *
 * ⚠ 教育・概念実証用。実在の人体/医療/予言とは無関係。
 */
#ifndef APRIORI_CPU_H
#define APRIORI_CPU_H
#include <stdint.h>

#define LUT_INPUTS   4          /* 4 入力 LUT (16bit 真理値表) */
#define CELL_BYTES   6          /* 4 routing-select + 2 LUT bytes */

typedef struct {
    uint16_t lut;               /* 16bit 真理値表 (2^4) */
    uint8_t  in[LUT_INPUTS];    /* 入力ソース選択 */
    uint16_t telomere;          /* テロメア長 (分裂で減少) */
    uint8_t  senescent;         /* 1=複製老化(LUT凍結, 恒等通過) */
} Cell;

typedef struct {
    int      inbits;            /* 一次入力ビット数 */
    int      layers;            /* 層数 */
    int      width;             /* 各層のセル数 */
    int      outbits;           /* 出力ビット数 */
    uint16_t telo_init;         /* 初期テロメア */
    uint16_t telo_hayflick;     /* Hayflick 限界 */
    Cell    *cells;             /* layers*width */
} Fabric;

/* 生成/破棄 */
Fabric *fab_create(int inbits, int layers, int width, int outbits,
                   uint16_t telo_init, uint16_t telo_hayflick);
void    fab_destroy(Fabric *f);

/* ゲノム: bytes 列。サイズ = layers*width*CELL_BYTES */
int     fab_genome_size(const Fabric *f);
void    fab_load(Fabric *f, const uint8_t *genome, int len);
void    fab_dump(const Fabric *f, uint8_t *genome, int len);

/* 評価: 一次入力 word -> 出力 word (LUTネットワークを前方伝播) */
uint32_t fab_eval(const Fabric *f, uint32_t input);

/* テロメア: 分裂を amount 回適用 (短縮, Hayflickでsenescent化) */
void    fab_telomere_tick(Fabric *f, int amount);
/* 世代継承: 親テロメアから attrition 分短縮して継ぐ */
void    fab_inherit_telomere(Fabric *child, const Fabric *parent, int attrition);
/* テロメラーゼ・イベント: 再活性化 (rejuvenation) */
void    fab_telomerase(Fabric *f, uint16_t to_len);
int     fab_senescent_count(const Fabric *f);

/* 適合度: 隠れた a-priori 目標関数 target() に対する一致率 (0..1) */
double  fab_fitness(const Fabric *f, uint32_t (*target)(uint32_t), int ncases);

#endif
