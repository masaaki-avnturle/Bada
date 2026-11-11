/* labanalysis.c — see labanalysis.h */
#include "labanalysis.h"
#include <string.h>
#include <ctype.h>
#include <stdlib.h>
#include <math.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* ---- 血液検査 ---- */
typedef struct { const char *name, *unit; double lo, hi, mid, sd; } panel_def_t;
static const panel_def_t PANEL[] = {
    {"Glucose",     "mg/dL",  70.0, 110.0,  92.0, 12.0},
    {"Hemoglobin",  "g/dL",   13.0,  17.0,  14.8,  1.0},
    {"WBC",         "x10^3",   4.0,  10.0,   6.5,  1.4},
    {"Platelet",    "x10^3", 150.0, 400.0, 250.0, 45.0},
    {"Sodium",      "mmol/L",135.0, 145.0, 140.0,  2.0},
    {"Potassium",   "mmol/L",  3.5,   5.0,   4.2,  0.3},
    {"Creatinine",  "mg/dL",   0.6,   1.2,   0.9,  0.12},
    {"CRP",         "mg/dL",   0.0,   0.3,   0.1,  0.08},
};

static double gauss(unsigned *seed)
{
    double u1 = (rand_r(seed) + 1.0) / ((double)RAND_MAX + 2.0);
    double u2 = (rand_r(seed) + 1.0) / ((double)RAND_MAX + 2.0);
    return sqrt(-2.0 * log(u1)) * cos(2.0 * M_PI * u2);
}

int blood_panel(blood_marker_t *out, int max, double thermal_bias, unsigned *seed)
{
    int n = (int)(sizeof(PANEL)/sizeof(PANEL[0]));
    if (n > max) n = max;
    for (int i = 0; i < n; ++i) {
        double v = PANEL[i].mid + PANEL[i].sd * (seed ? gauss(seed) : 0.0);
        /* 体熱エネルギーが高いと炎症/代謝マーカーが上振れ(デモ表現) */
        if (i == 0) v += 4.0 * thermal_bias;   /* Glucose */
        if (i == 2) v += 0.6 * thermal_bias;   /* WBC */
        if (i == 7) v += 0.05 * thermal_bias;  /* CRP */
        out[i].name  = PANEL[i].name;
        out[i].unit  = PANEL[i].unit;
        out[i].value = v;
        out[i].lo    = PANEL[i].lo;
        out[i].hi    = PANEL[i].hi;
    }
    return n;
}

char blood_flag(const blood_marker_t *m)
{
    if (m->value < m->lo) return 'L';
    if (m->value > m->hi) return 'H';
    return 'N';
}

/* ---- DNA ---- */
static int base_index(char c)
{
    switch (toupper((unsigned char)c)) {
        case 'A': return 0; case 'C': return 1;
        case 'G': return 2; case 'T': return 3;
        default:  return -1;
    }
}

dna_stats_t dna_analyze(const char *seq)
{
    dna_stats_t s;
    memset(&s, 0, sizeof(s));
    s.valid = 1;
    for (const char *p = seq; *p; ++p) {
        if (isspace((unsigned char)*p)) continue;
        int b = base_index(*p);
        if (b < 0) { s.valid = 0; continue; }
        s.count[b]++;
        s.length++;
    }
    if (s.length > 0)
        s.gc_content = (double)(s.count[1] + s.count[2]) / (double)s.length;
    return s;
}

void dna_top_kmer(const char *seq, int k, char *buf, size_t buflen, int *count)
{
    if (k < 1) k = 1;
    if (k > 4) k = 4;
    /* 純配列を抽出 */
    char clean[4096]; size_t cl = 0;
    for (const char *p = seq; *p && cl < sizeof(clean)-1; ++p)
        if (base_index(*p) >= 0) clean[cl++] = (char)toupper((unsigned char)*p);
    clean[cl] = 0;

    int best = 0; char bestk[8] = "";
    for (size_t i = 0; cl >= (size_t)k && i + k <= cl; ++i) {
        int c = 0;
        for (size_t j = 0; j + k <= cl; ++j)
            if (strncmp(clean + i, clean + j, k) == 0) c++;
        if (c > best) { best = c; strncpy(bestk, clean + i, k); bestk[k] = 0; }
    }
    if (buf && buflen) { strncpy(buf, bestk, buflen-1); buf[buflen-1] = 0; }
    if (count) *count = best;
}

/* ---- RNA ---- */
void rna_transcribe(const char *dna, char *out, size_t outlen)
{
    size_t o = 0;
    for (const char *p = dna; *p && o < outlen-1; ++p) {
        int b = base_index(*p);
        if (b < 0) continue;
        char u = "ACGU"[b == 3 ? 3 : b]; /* T(3)->U */
        if (b == 3) u = 'U';
        out[o++] = u;
    }
    out[o] = 0;
}

/* 標準遺伝暗号 (RNA コドン -> 1文字アミノ酸, '*'=終止) */
static char codon_aa(const char *c)
{
    static const char *tab =
      /* U** */ "FFLLSSSSYY**CC*W"
      /* C** */ "LLLLPPPPHHQQRRRR"
      /* A** */ "IIIMTTTTNNKKSSRR"
      /* G** */ "VVVVAAAADDEEGGGG";
    int idx[3];
    for (int i = 0; i < 3; ++i) {
        switch (toupper((unsigned char)c[i])) {
            case 'U': idx[i]=0; break; case 'C': idx[i]=1; break;
            case 'A': idx[i]=2; break; case 'G': idx[i]=3; break;
            default: return 'X';
        }
    }
    return tab[idx[0]*16 + idx[1]*4 + idx[2]];
}

void rna_translate(const char *rna, char *out, size_t outlen)
{
    size_t o = 0, L = strlen(rna);
    for (size_t i = 0; i + 3 <= L && o < outlen-1; i += 3)
        out[o++] = codon_aa(rna + i);
    out[o] = 0;
}
