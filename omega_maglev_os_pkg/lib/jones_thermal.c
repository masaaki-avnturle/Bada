/* lib/jones_thermal.c — Jones polynomial of the "thermal-energy body".
 *
 * The car body + coils carry a heat-flow field. We represent its topology as
 * a knot/link diagram (the same crossing format used by omega_jones_crypto_pkg)
 * and evaluate the Kauffman bracket <D> via a state-sum over all A/B smoothings.
 * The bracket is then folded together with a gamma-function "global partial
 * integration" weight so the thermal invariant depends on body temperature.
 *
 * Diagram file format (one crossing per line):
 *     id e0 e1 e2 e3 sign
 * '#' comments and blank lines are ignored.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "../include/omega_maglev.h"

/* ---- Lanczos approximation of the Gamma function ----------------------- */
double om_gamma(double x)
{
    static const double g = 7.0;
    static const double c[9] = {
        0.99999999999980993, 676.5203681218851, -1259.1392167224028,
        771.32342877765313, -176.61502916214059, 12.507343278686905,
        -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7
    };
    if (x < 0.5) {
        /* reflection: Gamma(x) = pi / (sin(pi x) Gamma(1-x)) */
        return OM_PI / (sin(OM_PI * x) * om_gamma(1.0 - x));
    }
    x -= 1.0;
    double a = c[0];
    double t = x + g + 0.5;
    for (int i = 1; i < 9; i++) a += c[i] / (x + i);
    return sqrt(2.0 * OM_PI) * pow(t, x + 0.5) * exp(-t) * a;
}

double om_gamma_global_partial(double a, double b)
{
    /* beta-style global partial integration factor:
       B(a,b) = Gamma(a) Gamma(b) / Gamma(a+b)  — the repo's zeta = beta/log x
       gauge lives one level up; here we return the raw beta weight.        */
    return om_gamma(a) * om_gamma(b) / om_gamma(a + b);
}

/* ---- Kauffman bracket state-sum (same engine as the crypto pkg) -------- */
typedef struct { int id; int e[4]; int sign; } Crossing;

static int load_diagram(const char *path, Crossing **out, int *n)
{
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    Crossing *a = NULL; int cap = 0, cnt = 0; char buf[256];
    while (fgets(buf, sizeof buf, f)) {
        char *s = buf; while (*s == ' ' || *s == '\t') s++;
        if (*s == '#' || *s == '\n' || *s == '\0') continue;
        int id, a0, a1, a2, a3, sg;
        if (sscanf(s, "%d %d %d %d %d %d", &id, &a0, &a1, &a2, &a3, &sg) < 6) continue;
        if (cnt >= cap) { cap = cap ? cap * 2 : 16; a = realloc(a, sizeof(Crossing) * cap); }
        a[cnt].id = id; a[cnt].e[0] = a0; a[cnt].e[1] = a1;
        a[cnt].e[2] = a2; a[cnt].e[3] = a3;
        a[cnt].sign = (sg >= 0) ? 1 : -1; cnt++;
    }
    fclose(f); *out = a; *n = cnt; return 0;
}

/* union-find over edge labels to count loops in a smoothing state */
typedef struct { int p; } UF;
static void uf_init(UF *u, int N) { for (int i = 0; i < N; i++) u[i].p = -1; }
static int  uf_find(UF *u, int a) { if (u[a].p < 0) return a; u[a].p = uf_find(u, u[a].p); return u[a].p; }
static void uf_union(UF *u, int a, int b) {
    a = uf_find(u, a); b = uf_find(u, b); if (a == b) return;
    if (u[a].p < u[b].p) { u[a].p += u[b].p; u[b].p = a; }
    else { u[b].p += u[a].p; u[a].p = b; }
}

static double kauffman_bracket(Crossing *cross, int n, double A)
{
    if (n == 0) return 1.0;
    unsigned long long states = 1ULL << n;
    double sum = 0.0; int maxlbl = 0;
    for (int i = 0; i < n; i++)
        for (int k = 0; k < 4; k++)
            if (cross[i].e[k] > maxlbl) maxlbl = cross[i].e[k];
    int U = maxlbl + 1;
    UF *uf = malloc(sizeof(UF) * (U > 0 ? U : 1));
    for (unsigned long long st = 0; st < states; st++) {
        uf_init(uf, U); int a_cnt = 0, b_cnt = 0;
        for (int i = 0; i < n; i++) {
            int bit = (st >> i) & 1ULL;
            if (bit == 0) { uf_union(uf, cross[i].e[0], cross[i].e[1]);
                            uf_union(uf, cross[i].e[2], cross[i].e[3]); a_cnt++; }
            else          { uf_union(uf, cross[i].e[1], cross[i].e[2]);
                            uf_union(uf, cross[i].e[3], cross[i].e[0]); b_cnt++; }
        }
        int *seen = calloc(U, sizeof(int)); int loops = 0;
        for (int lbl = 0; lbl < U; ++lbl) { int r = uf_find(uf, lbl); if (!seen[r]) { seen[r] = 1; loops++; } }
        free(seen);
        int e = a_cnt - b_cnt;
        double weight = pow(A, e);
        double d = -(A * A) - 1.0 / (A * A);
        double loops_factor = pow(d, (loops > 0 ? loops - 1 : 0));
        sum += weight * loops_factor;
    }
    free(uf); return sum;
}

int om_thermal_jones(const char *diagram_path, double A, double body_temp_k,
                     double *bracket_out, double *jones_thermal_out)
{
    Crossing *cs = NULL; int n = 0;
    if (load_diagram(diagram_path, &cs, &n) != 0) return -1;
    double bracket = kauffman_bracket(cs, n, A);
    free(cs);

    /* Thermal coupling: map temperature to a dimensionless (a,b) pair and
       weight the bracket by the gamma global-partial factor. Warmer bodies
       (higher T) carry more thermal "genus", shifting the invariant.        */
    double t = body_temp_k / 300.0;              /* ~1 at room temperature  */
    double a = 1.0 + t;
    double b = 1.0 + 1.0 / (t + 1e-3);
    double gweight = om_gamma_global_partial(a, b);

    if (bracket_out)       *bracket_out = bracket;
    if (jones_thermal_out) *jones_thermal_out = bracket * gweight;
    return 0;
}
