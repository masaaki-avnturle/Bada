/*
 * bada_morphogenesis.c — Linux native port of the "Bada Morphogenesis" app.
 *
 * A faithful C port of the app's reproducible simulation core, runnable as a
 * native Linux executable instead of an Android APK:
 *   - MorphMath          : Thom cusp-catastrophe potential V(x)=x^4/4+a x^2/2+b x,
 *                          real cubic root solver (trig / Cardano), bistability
 *   - Bada protocol DSL  : the .bada protocol interpreter (5 lineage protocols)
 *   - ReactionDiffusion  : Gray-Scott on a circular grid -> Turing morphogenetic
 *                          field, rendered as ASCII
 *   - LineageTree        : stochastic iPS-differentiation branching + population
 *   - DrugBatch          : simulated manufacturing metrics (yield/purity/...)
 *
 * IMPORTANT / 重要:
 *   This is a mathematical simulation only. It does NOT represent a real cell
 *   culture protocol, a real medicine, an anti-gravity device, or any physical
 *   apparatus. Simulation parameters and outputs are illustrative.
 *
 * Build:  gcc -std=c11 -O2 -o bada_morphogenesis bada_morphogenesis.c -lm
 * Usage:  ./bada_morphogenesis                  # interactive menu
 *         ./bada_morphogenesis --list           # list protocols
 *         ./bada_morphogenesis cardio           # run a protocol simulation
 *         ./bada_morphogenesis --protocols FILE --grid 80 --steps 3000 neuro
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <unistd.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

static double clamp(double v, double lo, double hi) { return v < lo ? lo : (v > hi ? hi : v); }

/* ----------------------------------------------------------------------- */
/* MorphMath — cusp catastrophe + cubic roots (port of MorphMath.kt)        */
/* ----------------------------------------------------------------------- */

static double cusp_potential(double x, double a, double b) {
    return x*x*x*x/4.0 + a*x*x/2.0 + b*x;
}
static double signed_cbrt(double v) { return v < 0 ? -cbrt(-v) : cbrt(v); }

/* Real roots of x^3 + p x + q = 0; returns count (1 or 3), fills r[3]. */
static int cubic_real_roots(double p, double q, double r[3]) {
    double disc = -4.0*p*p*p - 27.0*q*q;     /* > 0 => three real roots */
    if (disc > 0.0 && p < 0.0) {
        double m = 2.0 * sqrt(-p / 3.0);
        double arg = clamp((3.0 * q) / (p * m), -1.0, 1.0);
        double theta = acos(arg);
        for (int k = 0; k < 3; ++k)
            r[k] = m * cos(theta / 3.0 - 2.0 * M_PI * k / 3.0);
        return 3;
    } else {
        double u = -q / 2.0;
        double v = sqrt(q*q/4.0 + p*p*p/27.0);
        r[0] = signed_cbrt(u + v) + signed_cbrt(u - v);
        return 1;
    }
}
/* Control point (a,b) inside the cusp (bistable) region? */
static int is_bistable(double a, double b) {
    return (a < 0.0) && ((4.0*a*a*a + 27.0*b*b) < 0.0);
}

/* ----------------------------------------------------------------------- */
/* Bada protocol DSL (port of BadaProtocol.kt + ProtocolInterpreter.kt)     */
/* ----------------------------------------------------------------------- */

typedef struct {
    char   id[64], label[128], target[64], drug[160], note[256];
    double field_strength, cusp_a, cusp_b, branch_prob, feed, kill;
} Protocol;

static void strip_comment(char *s) { char *c = strstr(s, "//"); if (c) *c = '\0'; }
static char *trim(char *s) {
    while (*s==' '||*s=='\t'||*s=='\r'||*s=='\n') s++;
    char *e = s + strlen(s);
    while (e>s && (e[-1]==' '||e[-1]=='\t'||e[-1]=='\r'||e[-1]=='\n')) *--e='\0';
    return s;
}
static void unquote(char *s) {
    size_t n = strlen(s);
    if (n>=2 && s[0]=='"' && s[n-1]=='"') { memmove(s, s+1, n-2); s[n-2]='\0'; }
}
static void proto_defaults(Protocol *p, const char *id) {
    memset(p, 0, sizeof *p);
    snprintf(p->id, sizeof p->id, "%s", id);
    snprintf(p->label, sizeof p->label, "%s", id);
    snprintf(p->target, sizeof p->target, "心筋細胞");
    snprintf(p->drug, sizeof p->drug, "候補薬 (シミュレーション)");
    p->field_strength = 0.5; p->cusp_a = -1.0; p->cusp_b = 0.0;
    p->branch_prob = 0.5; p->feed = 0.037; p->kill = 0.060;
}
static void proto_set(Protocol *p, const char *k, char *v) {
    if      (!strcmp(k,"label"))          snprintf(p->label, sizeof p->label, "%s", v);
    else if (!strcmp(k,"target"))         snprintf(p->target, sizeof p->target, "%s", v);
    else if (!strcmp(k,"drug"))           snprintf(p->drug, sizeof p->drug, "%s", v);
    else if (!strcmp(k,"note"))           snprintf(p->note, sizeof p->note, "%s", v);
    else if (!strcmp(k,"field_strength")) p->field_strength = atof(v);
    else if (!strcmp(k,"cusp_a"))         p->cusp_a = atof(v);
    else if (!strcmp(k,"cusp_b"))         p->cusp_b = atof(v);
    else if (!strcmp(k,"branch_prob"))    p->branch_prob = clamp(atof(v), 0.0, 1.0);
    else if (!strcmp(k,"feed"))           p->feed = atof(v);
    else if (!strcmp(k,"kill"))           p->kill = atof(v);
}
static int parse_protocols(char *src, Protocol *out, int max) {
    int count = 0; char *save;
    for (char *line = strtok_r(src, "\n", &save); line && count < max; line = strtok_r(NULL, "\n", &save)) {
        strip_comment(line);
        char *t = trim(line);
        char *kw = strstr(t, "protocol");
        char *q1 = strchr(t, '"');
        if (kw == t && q1) {
            char *q2 = strchr(q1+1, '"'); if (!q2) continue; *q2 = '\0';
            proto_defaults(&out[count], q1+1);
            for (char *bl = strtok_r(NULL, "\n", &save); bl; bl = strtok_r(NULL, "\n", &save)) {
                strip_comment(bl);
                char *bt = trim(bl);
                if (!strcmp(bt, "}")) break;
                char *eq = strchr(bt, '='); if (!eq) continue; *eq = '\0';
                char *key = trim(bt), *val = trim(eq+1);
                for (char *c = key; *c; ++c) if (*c>='A'&&*c<='Z') *c += 32;
                unquote(val);
                proto_set(&out[count], key, val);
            }
            count++;
        }
    }
    return count;
}
static int load_protocols(const char *path, Protocol *out, int max) {
    FILE *f = fopen(path, "rb"); if (!f) return -1;
    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
    if (sz < 0) { fclose(f); return -1; }
    char *buf = malloc((size_t)sz + 1); if (!buf) { fclose(f); return -1; }
    size_t r = fread(buf, 1, (size_t)sz, f); buf[r] = '\0'; fclose(f);
    int n = parse_protocols(buf, out, max); free(buf); return n;
}

/* ----------------------------------------------------------------------- */
/* Gray-Scott reaction-diffusion on a circular grid (port of               */
/* ReactionDiffusion.kt)                                                    */
/* ----------------------------------------------------------------------- */

typedef struct {
    int n;
    float *u, *v, *u2, *v2;
    char  *inside;
    float feed, kill, du, dv, field_strength, fieldX, fieldY;
} RD;

static RD *rd_new(int n, double feed, double kill, double field_strength) {
    RD *s = calloc(1, sizeof *s);
    s->n = n;
    s->u = malloc(sizeof(float)*n*n); s->v = malloc(sizeof(float)*n*n);
    s->u2 = malloc(sizeof(float)*n*n); s->v2 = malloc(sizeof(float)*n*n);
    s->inside = malloc(n*n);
    s->feed = (float)feed; s->kill = (float)kill; s->du = 0.16f; s->dv = 0.08f;
    s->field_strength = (float)field_strength; s->fieldX = 0.6f; s->fieldY = 0.2f;
    float r = n / 2.0f;
    for (int y = 0; y < n; ++y) for (int x = 0; x < n; ++x) {
        int i = y*n + x; float dx = x - r, dy = y - r;
        s->inside[i] = (dx*dx + dy*dy) <= (r-1)*(r-1);
        s->u[i] = 1.0f; s->v[i] = 0.0f;
    }
    int c = n/2;
    for (int y = c-4; y < c+4; ++y) for (int x = c-4; x < c+4; ++x) {
        int i = y*n + x; if (i >= 0 && i < n*n) { s->u[i] = 0.5f; s->v[i] = 0.25f; }
    }
    return s;
}
static void rd_free(RD *s){ free(s->u);free(s->v);free(s->u2);free(s->v2);free(s->inside);free(s);}
static float laplacian(const float *g, int n, int x, int y) {
    int i = y*n + x;
    return g[i-1] + g[i+1] + g[i-n] + g[i+n] - 4.0f*g[i];
}
static void rd_step(RD *s, int steps) {
    int n = s->n;
    for (int it = 0; it < steps; ++it) {
        for (int y = 1; y < n-1; ++y) for (int x = 1; x < n-1; ++x) {
            int i = y*n + x;
            if (!s->inside[i]) { s->u2[i] = 1.0f; s->v2[i] = 0.0f; continue; }
            float lu = laplacian(s->u, n, x, y), lv = laplacian(s->v, n, x, y);
            float uvv = s->u[i]*s->v[i]*s->v[i];
            float bias = s->field_strength * 0.02f;
            float adU = bias*(s->fieldX*(s->u[i+1]-s->u[i-1]) + s->fieldY*(s->u[i+n]-s->u[i-n]));
            float adV = bias*(s->fieldX*(s->v[i+1]-s->v[i-1]) + s->fieldY*(s->v[i+n]-s->v[i-n]));
            float nu = s->u[i] + s->du*lu - uvv + s->feed*(1.0f - s->u[i]) - adU;
            float nv = s->v[i] + s->dv*lv + uvv - (s->feed + s->kill)*s->v[i] - adV;
            s->u2[i] = (float)clamp(nu, 0.0, 1.0);
            s->v2[i] = (float)clamp(nv, 0.0, 1.0);
        }
        float *t;
        t = s->u; s->u = s->u2; s->u2 = t;
        t = s->v; s->v = s->v2; s->v2 = t;
    }
}
static double rd_diff_fraction(const RD *s, float threshold) {
    int hit = 0, tot = 0, n = s->n;
    for (int i = 0; i < n*n; ++i) if (s->inside[i]) { tot++; if (s->v[i] > threshold) hit++; }
    return tot ? (double)hit/tot : 0.0;
}
/* Render the v field as ASCII, sampled to cols x rows (terminal aspect ~2:1). */
static void rd_render(const RD *s, int cols, int rows) {
    static const char *ramp = " .:-=+*#%@";
    int n = s->n;
    for (int ry = 0; ry < rows; ++ry) {
        printf("      ");
        for (int rx = 0; rx < cols; ++rx) {
            int x = (int)((rx + 0.5) / cols * n);
            int y = (int)((ry + 0.5) / rows * n);
            if (x < 0) x = 0;
            if (x >= n) x = n-1;
            if (y < 0) y = 0;
            if (y >= n) y = n-1;
            int i = y*n + x;
            if (!s->inside[i]) { putchar(' '); continue; }
            double val = clamp(s->v[i] * 3.0, 0.0, 1.0);
            putchar(ramp[(int)(val * 8.999)]);
        }
        putchar('\n');
    }
}

/* ----------------------------------------------------------------------- */
/* Lineage tree + population (port of LineageTree.kt)                       */
/* ----------------------------------------------------------------------- */

static const char *GERM[3] = { "外胚葉", "中胚葉", "内胚葉" };
static const char *TERMINAL[3][3] = {
    { "神経細胞", "表皮細胞", "網膜細胞" },   /* 外胚葉 */
    { "心筋細胞", "血球細胞", "骨格筋細胞" }, /* 中胚葉 */
    { "肝細胞",   "膵β細胞", "肺胞細胞" }    /* 内胚葉 */
};
static int germ_index(const char *fate) {
    for (int g = 0; g < 3; ++g) if (!strcmp(fate, GERM[g])) return g;
    return -1;
}
static int is_terminal_type(const char *fate) {
    for (int g = 0; g < 3; ++g) for (int t = 0; t < 3; ++t)
        if (!strcmp(fate, TERMINAL[g][t])) return 1;
    return 0;
}

/* deterministic PRNG (so a seed reproduces a run) */
static unsigned long g_rng = 42UL;
static double rng_d(void) { g_rng = g_rng*6364136223846793005UL + 1442695040888963407UL; return ((g_rng >> 11) & 0xFFFFFFFFFFFFF) / (double)0x10000000000000; }
static int rng_i(int n) { return (int)(rng_d() * n); }

typedef struct { int depth; char fate[32]; int terminal; } Cell;
static Cell g_nodes[20000]; static int g_ncount;

static void grow(int depth, const char *parent_fate, int parent_terminal, int max_depth,
                 double cuspA, double cuspB, double branch_prob) {
    if (depth >= max_depth) return;
    int bistable = is_bistable(cuspA, cuspB);
    double eff = bistable ? branch_prob : branch_prob * 0.35;
    int branches = (depth == 0) ? 3 : (rng_d() < eff ? 2 : 1);
    for (int b = 0; b < branches && g_ncount < 20000; ++b) {
        int cd = depth + 1;
        char fate[32];
        if (depth == 0) snprintf(fate, sizeof fate, "%s", GERM[b % 3]);
        else if (depth == 1) {
            int gi = germ_index(parent_fate);
            if (gi >= 0) snprintf(fate, sizeof fate, "%s", TERMINAL[gi][b % 3]);
            else snprintf(fate, sizeof fate, "前駆細胞");
        } else {
            int gi = germ_index(parent_fate);
            if (parent_terminal) snprintf(fate, sizeof fate, "%s", parent_fate);
            else if (gi >= 0) snprintf(fate, sizeof fate, "%s", TERMINAL[gi][rng_i(3)]);
            else { int gg = rng_i(3); snprintf(fate, sizeof fate, "%s", TERMINAL[gg][rng_i(3)]); }
        }
        int terminal = (cd >= max_depth) || is_terminal_type(fate);
        g_nodes[g_ncount].depth = cd; g_nodes[g_ncount].terminal = terminal;
        snprintf(g_nodes[g_ncount].fate, sizeof g_nodes[g_ncount].fate, "%s", fate);
        g_ncount++;
        if (!terminal) grow(cd, fate, terminal, max_depth, cuspA, cuspB, branch_prob);
    }
}

/* population model -> counts for the 9 terminal types (+ target boosted) */
typedef struct { const char *type; int count; } TypeCount;
static int population(const Protocol *p, int total, TypeCount out[9]) {
    int idx = 0;
    for (int g = 0; g < 3; ++g) for (int t = 0; t < 3; ++t) out[idx++].type = TERMINAL[g][t];
    int bistable = is_bistable(p->cusp_a, p->cusp_b);
    double boost = clamp(p->branch_prob + (bistable ? 0.15 : 0.0), 0.0, 1.0);
    double target_frac = clamp(0.35 + 0.55 * boost, 0.0, 0.95);
    int target_count = (int)(total * target_frac);
    /* find target index */
    int ti = -1;
    for (int i = 0; i < 9; ++i) if (!strcmp(out[i].type, p->target)) ti = i;
    int others = (ti >= 0) ? 8 : 9;
    int remaining = total - (ti >= 0 ? target_count : 0);
    int per = remaining / others, given = 0, oi = 0;
    for (int i = 0; i < 9; ++i) {
        if (i == ti) { out[i].count = target_count; continue; }
        int give = (oi == others - 1) ? (remaining - given) : per;
        out[i].count = give; given += give; oi++;
    }
    return 9;
}

/* ----------------------------------------------------------------------- */
/* DrugBatch (port of DrugBatch.kt)                                         */
/* ----------------------------------------------------------------------- */

static double round1(double v) { return ((double)(long)(v*10.0 + (v<0?-0.5:0.5))) / 10.0; }

static void drug_batch(const Protocol *p, const TypeCount *counts, int ncounts,
                       double diff_fraction) {
    int total = 0, target = 0;
    for (int i = 0; i < ncounts; ++i) { total += counts[i].count; if (!strcmp(counts[i].type, p->target)) target += counts[i].count; }
    if (total < 1) total = 1;
    int committed = total; if (committed < 1) committed = 1;
    double yieldp = 100.0 * target / total;
    double purity = 100.0 * target / committed;
    double viability = clamp(78.0 + 18.0*diff_fraction - 6.0*(1.0 - p->field_strength), 40.0, 99.0);
    double titer = target * (purity/100.0) * (viability/100.0) * 10.0;
    int pass = (purity >= 75.0) && (viability >= 80.0) && (target > 0);

    printf("  ┌ 製造シミュレーション (DrugBatch) — %s\n", p->drug);
    printf("  │ target type : %-10s    total cells : %d\n", p->target, total);
    printf("  │ yield   : %6.1f%%      purity   : %6.1f%%\n", round1(yieldp), round1(purity));
    printf("  │ viability:%6.1f%%      titer    : %8.1f (arb.)\n", round1(viability), round1(titer));
    printf("  └ spec    : %s\n", pass ? "PASS ✓ (purity≥75%, viability≥80%)" : "FAIL ✗ (below spec)");
}

/* ----------------------------------------------------------------------- */
/* Cusp catastrophe display                                                 */
/* ----------------------------------------------------------------------- */

static void show_cusp(const Protocol *p) {
    double a = p->cusp_a, b = p->cusp_b, r[3];
    int nr = cubic_real_roots(a, b, r);
    int bist = is_bistable(a, b);
    printf("  カタストロフィ (cusp): a=%.2f b=%.2f  →  %s\n",
           a, b, bist ? "双安定 (bistable / 分岐領域)" : "単安定 (monostable)");
    printf("    平衡点 (dV/dx=0): ");
    for (int i = 0; i < nr; ++i) {
        int stable = (3.0*r[i]*r[i] + a) > 0.0;
        printf("x=%+.3f%s%s", r[i], stable ? "(安定)" : "(不安定)", i < nr-1 ? ", " : "");
    }
    printf("\n");
    /* ASCII potential curve V(x) over x in [-2,2] */
    int W = 56, H = 9;
    double xs = -2.0, xe = 2.0, vmin = 1e9, vmax = -1e9, vals[64];
    for (int c = 0; c < W; ++c) { double x = xs + (xe-xs)*c/(W-1); vals[c] = cusp_potential(x,a,b); if (vals[c]<vmin) vmin=vals[c]; if (vals[c]>vmax) vmax=vals[c]; }
    for (int row = 0; row < H; ++row) {
        double level = vmax - (vmax-vmin)*row/(H-1);
        printf("      ");
        for (int c = 0; c < W; ++c) {
            double next = (row<H-1)? vmax-(vmax-vmin)*(row+1)/(H-1) : -1e9;
            putchar((vals[c] <= level && vals[c] > next) ? '*' : ' ');
        }
        putchar('\n');
    }
    printf("      x=-2 %.*s x=+2   V(x)=x⁴/4 + a·x²/2 + b·x\n", W-10, "------------------------------------------------------------");
}

/* ----------------------------------------------------------------------- */
/* UI                                                                       */
/* ----------------------------------------------------------------------- */

static int g_grid = 80, g_steps = 3000;

static void hr(void){ printf("  ----------------------------------------------------------------\n"); }

static void show_protocol(const Protocol *p) {
    printf("\n  ● %s   [%s]\n", p->label, p->id);
    hr();
    printf("  target : %s    field_strength : %.2f    branch_prob : %.2f\n",
           p->target, p->field_strength, p->branch_prob);
    printf("  Gray-Scott feed=%.3f kill=%.3f    drug : %s\n", p->feed, p->kill, p->drug);
    if (p->note[0]) printf("  note : %s\n", p->note);
    hr();
    show_cusp(p);
    hr();

    /* reaction-diffusion morphogenetic field */
    RD *rd = rd_new(g_grid, p->feed, p->kill, p->field_strength);
    rd_step(rd, g_steps);
    double frac = rd_diff_fraction(rd, 0.2f);
    printf("  形態形成場 (Gray-Scott reaction-diffusion, %dx%d, %d steps):\n", g_grid, g_grid, g_steps);
    rd_render(rd, 48, 18);
    printf("      分化フラクション (differentiated fraction): %.1f%%\n", frac*100.0);
    rd_free(rd);
    hr();

    /* lineage tree + terminal counts */
    g_rng = 42UL; g_ncount = 0;
    grow(0, "iPS細胞", 0, 5, p->cusp_a, p->cusp_b, p->branch_prob);
    int terminals = 0; for (int i = 0; i < g_ncount; ++i) if (g_nodes[i].terminal) terminals++;
    printf("  分化系譜樹 (lineage tree): nodes=%d, terminal leaves=%d\n", g_ncount + 1, terminals);
    printf("      iPS細胞 → {外胚葉, 中胚葉, 内胚葉} → 終末細胞型\n");
    /* per-depth node counts as a small bar chart */
    int by_depth[8] = {0};
    for (int i = 0; i < g_ncount; ++i) if (g_nodes[i].depth < 8) by_depth[g_nodes[i].depth]++;
    for (int d = 1; d <= 5; ++d) {
        printf("      depth %d: ", d);
        for (int k = 0; k < by_depth[d] && k < 50; ++k) putchar('#');
        printf(" (%d)\n", by_depth[d]);
    }
    hr();

    /* population + manufacturing */
    TypeCount counts[9];
    int nc = population(p, 1000, counts);
    printf("  細胞集団 (population, 1000 cells):\n");
    for (int i = 0; i < nc; ++i) {
        int star = !strcmp(counts[i].type, p->target);
        printf("      %s%-10s %4d  ", star ? "★ " : "  ", counts[i].type, counts[i].count);
        for (int k = 0; k < counts[i].count/20; ++k) putchar('#');
        putchar('\n');
    }
    hr();
    drug_batch(p, counts, nc, frac);
    printf("\n  ※ これは数学シミュレーションです。実在の細胞培養・医薬品・物理装置ではありません。\n\n");
}

static void list_protocols(const Protocol *ps, int n) {
    printf("\n  Bada Morphogenesis — protocols (%d)\n", n);
    hr();
    for (int i = 0; i < n; ++i)
        printf("  %d) %-8s  %-14s  target: %-8s  (a=%.1f, branch=%.2f)\n",
               i+1, ps[i].id, ps[i].label, ps[i].target, ps[i].cusp_a, ps[i].branch_prob);
    hr();
}

static int find_protocol(const Protocol *ps, int n, const char *id) {
    for (int i = 0; i < n; ++i) if (!strcmp(ps[i].id, id) || !strcmp(ps[i].label, id)) return i;
    char *e; long k = strtol(id, &e, 10);
    if (*e == '\0' && k >= 1 && k <= n) return (int)(k-1);
    return -1;
}

static const char *default_path(const char *argv0, char *buf, size_t n) {
    const char *cands[4]; int c = 0;
    cands[c++] = "lineages.bada";
    cands[c++] = "protocols/lineages.bada";
    cands[c++] = "bada_morphogenesis_linux/lineages.bada";
    static char near[1024]; snprintf(near, sizeof near, "%s", argv0);
    char *slash = strrchr(near, '/');
    if (slash) { snprintf(slash+1, sizeof near - (slash+1-near), "lineages.bada"); cands[c++] = near; }
    for (int i = 0; i < c; ++i) { FILE *f = fopen(cands[i], "rb"); if (f) { fclose(f); snprintf(buf, n, "%s", cands[i]); return buf; } }
    snprintf(buf, n, "lineages.bada"); return buf;
}

int main(int argc, char **argv) {
    const char *path = NULL, *want = NULL; int do_list = 0;
    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--list") || !strcmp(argv[i], "list")) do_list = 1;
        else if (!strcmp(argv[i], "--protocols") && i+1 < argc) path = argv[++i];
        else if (!strcmp(argv[i], "--grid") && i+1 < argc) g_grid = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--steps") && i+1 < argc) g_steps = atoi(argv[++i]);
        else if (!strcmp(argv[i], "-h") || !strcmp(argv[i], "--help")) {
            printf("usage: %s [--list] [<id|index>] [--protocols FILE] [--grid N] [--steps N]\n", argv[0]);
            return 0;
        }
        else if (argv[i][0] != '-') want = argv[i];
    }
    if (g_grid < 24) g_grid = 24;
    if (g_grid > 200) g_grid = 200;
    if (g_steps < 0) g_steps = 0;

    char pbuf[1024];
    if (!path) path = default_path(argv[0], pbuf, sizeof pbuf);
    static Protocol ps[64];
    int n = load_protocols(path, ps, 64);
    if (n <= 0) { fprintf(stderr, "error: cannot read protocols from '%s'\n", path); return 1; }

    printf("\x1b[1m  Bada Morphogenesis (Linux)\x1b[0m — iPS 分化 + 製造シミュレーション\n");
    printf("  protocols: %s  (%d loaded)\n", path, n);

    if (do_list) { list_protocols(ps, n); return 0; }
    if (want) {
        int idx = find_protocol(ps, n, want);
        if (idx < 0) { fprintf(stderr, "error: protocol '%s' not found (try --list)\n", want); return 1; }
        show_protocol(&ps[idx]); return 0;
    }
    if (!isatty(0)) { list_protocols(ps, n); printf("  (run `%s <id>` to simulate)\n", argv[0]); return 0; }
    for (;;) {
        list_protocols(ps, n);
        printf("  select 1-%d (q to quit): ", n); fflush(stdout);
        char line[64]; if (!fgets(line, sizeof line, stdin)) break;
        char *t = trim(line);
        if (t[0]=='q'||t[0]=='Q'||t[0]=='\0') break;
        int idx = find_protocol(ps, n, t);
        if (idx < 0) { printf("  ? unknown selection\n"); continue; }
        show_protocol(&ps[idx]);
        printf("  press Enter to continue..."); fflush(stdout);
        if (!fgets(line, sizeof line, stdin)) break;
    }
    printf("  またね。\n");
    return 0;
}
