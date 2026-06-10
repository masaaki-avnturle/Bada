/*
 * apriori_cpu.c  —  Ω-Apriori Core : 未知事前エンジン CPU の中核 (実装)
 *
 * ビルド (共有ライブラリ, Python ctypes 用):
 *     cc -O2 -fPIC -shared -o libaprioricpu.so apriori_cpu.c
 * ビルド (スタンドアロン・デモ):
 *     cc -O2 -DAPRIORI_MAIN -o apriori_demo apriori_cpu.c && ./apriori_demo
 *
 * ⚠ 概念実証・教育用。実在の人体/医療/余命予測とは無関係。
 */
#include "apriori_cpu.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

Fabric *fab_create(int inbits, int layers, int width, int outbits,
                   uint16_t telo_init, uint16_t telo_hayflick)
{
    Fabric *f = (Fabric*)calloc(1, sizeof(Fabric));
    if (!f) return NULL;
    f->inbits = inbits; f->layers = layers; f->width = width;
    f->outbits = outbits; f->telo_init = telo_init; f->telo_hayflick = telo_hayflick;
    f->cells = (Cell*)calloc((size_t)layers * width, sizeof(Cell));
    if (!f->cells) { free(f); return NULL; }
    for (int i = 0; i < layers * width; i++) {
        f->cells[i].telomere = telo_init;
        f->cells[i].senescent = 0;
        f->cells[i].lut = 0;
    }
    return f;
}

void fab_destroy(Fabric *f) { if (f) { free(f->cells); free(f); } }

int fab_genome_size(const Fabric *f) { return f->layers * f->width * CELL_BYTES; }

/* 層 L のセルが選べるソース数 */
static int sources_for_layer(const Fabric *f, int layer) {
    return (layer == 0) ? f->inbits : f->width;
}

void fab_load(Fabric *f, const uint8_t *g, int len) {
    int need = fab_genome_size(f);
    if (len < need) return;
    int idx = 0;
    for (int L = 0; L < f->layers; L++) {
        int src = sources_for_layer(f, L);
        for (int w = 0; w < f->width; w++) {
            Cell *c = &f->cells[L * f->width + w];
            const uint8_t *p = g + idx * CELL_BYTES;
            for (int k = 0; k < LUT_INPUTS; k++) c->in[k] = (uint8_t)(p[k] % (src > 0 ? src : 1));
            c->lut = (uint16_t)(p[4] | (p[5] << 8));
            idx++;
        }
    }
}

void fab_dump(const Fabric *f, uint8_t *g, int len) {
    int need = fab_genome_size(f);
    if (len < need) return;
    int idx = 0;
    for (int L = 0; L < f->layers; L++) {
        for (int w = 0; w < f->width; w++) {
            Cell *c = &f->cells[L * f->width + w];
            uint8_t *p = g + idx * CELL_BYTES;
            for (int k = 0; k < LUT_INPUTS; k++) p[k] = c->in[k];
            p[4] = (uint8_t)(c->lut & 0xFF);
            p[5] = (uint8_t)((c->lut >> 8) & 0xFF);
            idx++;
        }
    }
}

/* 前方伝播評価 */
uint32_t fab_eval(const Fabric *f, uint32_t input) {
    uint32_t prev = input & ((f->inbits >= 32) ? 0xFFFFFFFFu : ((1u << f->inbits) - 1));
    uint32_t cur = 0;
    int src_count = f->inbits;
    for (int L = 0; L < f->layers; L++) {
        cur = 0;
        for (int w = 0; w < f->width; w++) {
            Cell *c = &f->cells[L * f->width + w];
            int addr = 0;
            for (int k = 0; k < LUT_INPUTS; k++) {
                int sel = c->in[k];
                if (sel >= src_count) sel = src_count ? (sel % src_count) : 0;
                int bit = (prev >> sel) & 1u;
                addr |= (bit << k);
            }
            int out;
            if (c->senescent) {
                /* 複製老化セル: 第1入力を恒等通過 (機能停止≒中立) */
                int sel = c->in[0]; if (src_count && sel >= src_count) sel %= src_count;
                out = (prev >> sel) & 1u;
            } else {
                out = (c->lut >> addr) & 1u;
            }
            cur |= ((uint32_t)out << w);
        }
        prev = cur;
        src_count = f->width;
    }
    /* 出力: 最終層の下位 outbits */
    return cur & ((f->outbits >= 32) ? 0xFFFFFFFFu : ((1u << f->outbits) - 1));
}

void fab_telomere_tick(Fabric *f, int amount) {
    for (int i = 0; i < f->layers * f->width; i++) {
        Cell *c = &f->cells[i];
        if (c->senescent) continue;
        int t = (int)c->telomere - amount;
        if (t <= (int)f->telo_hayflick) { c->telomere = f->telo_hayflick; c->senescent = 1; }
        else c->telomere = (uint16_t)t;
    }
}

void fab_inherit_telomere(Fabric *child, const Fabric *parent, int attrition) {
    int n = child->layers * child->width;
    int pn = parent->layers * parent->width;
    for (int i = 0; i < n && i < pn; i++) {
        int t = (int)parent->cells[i].telomere - attrition;
        if (t <= (int)child->telo_hayflick) { child->cells[i].telomere = child->telo_hayflick; child->cells[i].senescent = 1; }
        else { child->cells[i].telomere = (uint16_t)t; child->cells[i].senescent = 0; }
    }
}

void fab_telomerase(Fabric *f, uint16_t to_len) {
    for (int i = 0; i < f->layers * f->width; i++) {
        f->cells[i].telomere = to_len;
        f->cells[i].senescent = 0;
    }
}

int fab_senescent_count(const Fabric *f) {
    int n = 0;
    for (int i = 0; i < f->layers * f->width; i++) n += f->cells[i].senescent;
    return n;
}

double fab_fitness(const Fabric *f, uint32_t (*target)(uint32_t), int ncases) {
    long match = 0, total = 0;
    for (uint32_t x = 0; x < (uint32_t)ncases; x++) {
        uint32_t y = fab_eval(f, x);
        uint32_t t = target(x) & ((1u << f->outbits) - 1);
        uint32_t diff = y ^ t;
        for (int b = 0; b < f->outbits; b++) { total++; if (!((diff >> b) & 1u)) match++; }
    }
    return total ? (double)match / (double)total : 0.0;
}

/* ============================================================= */
#ifdef APRIORI_MAIN
/* スタンドアロン・デモ: ランダム探索でも popcount を少し学ぶ様子を確認 */
static uint32_t target_popcount(uint32_t x) {
    int c = 0; for (int i = 0; i < 6; i++) c += (x >> i) & 1u; return (uint32_t)c;
}
int main(void) {
    Fabric *f = fab_create(6, 3, 8, 3, 1000, 200);
    int gs = fab_genome_size(f);
    uint8_t *g = (uint8_t*)malloc(gs);
    uint8_t *best = (uint8_t*)malloc(gs);
    double bf = 0;
    srand(12345);
    for (int it = 0; it < 20000; it++) {
        for (int i = 0; i < gs; i++) g[i] = (uint8_t)(rand() & 0xFF);
        fab_load(f, g, gs);
        double fit = fab_fitness(f, target_popcount, 64);
        if (fit > bf) { bf = fit; memcpy(best, g, gs); }
    }
    printf("Omega-Apriori Core demo\n");
    printf("genome bytes      : %d\n", gs);
    printf("best fitness (rnd): %.4f\n", bf);
    fab_load(f, best, gs);
    fab_telomere_tick(f, 850);
    printf("after 850 divisions, senescent cells: %d / %d\n",
           fab_senescent_count(f), f->layers * f->width);
    free(g); free(best); fab_destroy(f);
    return 0;
}
#endif
