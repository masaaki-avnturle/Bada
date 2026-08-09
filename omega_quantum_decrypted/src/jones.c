/* jones.c — Kauffman bracket state sum -> Jones polynomial -> key seed. */
#include "jones.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

enum {
    OQD_J_OK        =  0,
    OQD_J_OPEN      = -1,   /* cannot open file          */
    OQD_J_EMPTY     = -2,   /* no crossings parsed       */
    OQD_J_TOOBIG    = -3,   /* too many crossings        */
    OQD_J_NOMEM     = -4,   /* allocation failure        */
    OQD_J_SMALLBUF  = -5    /* seed buffer too small     */
};

const char *oqd_jones_strerror(int code) {
    switch (code) {
        case OQD_J_OK:       return "ok";
        case OQD_J_OPEN:     return "cannot open knot key file";
        case OQD_J_EMPTY:    return "no crossings found in knot key file";
        case OQD_J_TOOBIG:   return "too many crossings (max 24)";
        case OQD_J_NOMEM:    return "out of memory";
        case OQD_J_SMALLBUF: return "seed buffer too small";
        default:             return "unknown error";
    }
}

typedef struct { int id; int e[4]; int sign; } Crossing;

static int load_diagram(const char *path, Crossing **out, int *n) {
    FILE *f = fopen(path, "r");
    if (!f) return OQD_J_OPEN;
    Crossing *a = NULL; int cap = 0, cnt = 0;
    char buf[512];
    while (fgets(buf, sizeof buf, f)) {
        char *s = buf;
        while (*s == ' ' || *s == '\t') s++;
        if (*s == '#' || *s == '\n' || *s == '\r' || *s == '\0') continue;
        int id, a0, a1, a2, a3, sg;
        if (sscanf(s, "%d %d %d %d %d %d", &id, &a0, &a1, &a2, &a3, &sg) < 6)
            continue;
        if (cnt >= cap) {
            int ncap = cap ? cap * 2 : 16;
            Crossing *na = realloc(a, sizeof(Crossing) * ncap);
            if (!na) { free(a); fclose(f); return OQD_J_NOMEM; }
            a = na; cap = ncap;
        }
        a[cnt].id = id;
        a[cnt].e[0] = a0; a[cnt].e[1] = a1; a[cnt].e[2] = a2; a[cnt].e[3] = a3;
        a[cnt].sign = (sg >= 0) ? 1 : -1;
        cnt++;
    }
    fclose(f);
    if (cnt == 0) { free(a); return OQD_J_EMPTY; }
    *out = a; *n = cnt;
    return OQD_J_OK;
}

/* ---- union-find over edge labels (to count loops in a smoothed state) ---- */
static int uf_find(int *p, int a) { while (p[a] != a) { p[a] = p[p[a]]; a = p[a]; } return a; }
static void uf_union(int *p, int a, int b) { a = uf_find(p, a); b = uf_find(p, b); if (a != b) p[a] = b; }

/* ---- Laurent polynomial helpers ---- */
static int lpoly_alloc(oqd_lpoly *P, int lo, int hi) {
    P->lo = lo; P->hi = hi; P->n = (size_t)(hi - lo + 1);
    P->coeff = calloc(P->n, sizeof(long long));
    return P->coeff ? 0 : -1;
}
static void lpoly_free(oqd_lpoly *P) { free(P->coeff); P->coeff = NULL; P->n = 0; }
static void lpoly_add_term(oqd_lpoly *P, int exp, long long c) {
    if (exp < P->lo || exp > P->hi) return; /* bounds guaranteed by caller */
    P->coeff[exp - P->lo] += c;
}

/* Serialise polynomial term-by-term into out (le). Returns bytes or -1. */
static int lpoly_serialize(const oqd_lpoly *P, uint8_t *out, size_t cap, size_t *used) {
    for (size_t i = 0; i < P->n; i++) {
        if (P->coeff[i] == 0) continue;
        int exp = P->lo + (int)i;
        long long c = P->coeff[i];
        if (*used + 12 > cap) return -1;
        int32_t e = (int32_t)exp;
        int64_t v = (int64_t)c;
        memcpy(out + *used, &e, 4); *used += 4;
        memcpy(out + *used, &v, 8); *used += 8;
    }
    return 0;
}

int oqd_jones_from_file(const char *path, oqd_knot_invariant *out) {
    Crossing *cs = NULL; int n = 0;
    int rc = load_diagram(path, &cs, &n);
    if (rc != OQD_J_OK) return rc;
    if (n > OQD_MAX_CROSSINGS) { free(cs); return OQD_J_TOOBIG; }

    memset(out, 0, sizeof *out);
    out->n_crossings = n;

    int writhe = 0;
    int maxlbl = 0;
    for (int i = 0; i < n; i++) {
        writhe += cs[i].sign;
        for (int k = 0; k < 4; k++) if (cs[i].e[k] > maxlbl) maxlbl = cs[i].e[k];
    }
    out->writhe = writhe;
    int U = maxlbl + 1;

    /* d = -A^2 - A^-2. Each state contributes A^(a-b) * d^(loops-1).
     * Bracket exponents lie in [-(n + 2*max_loops), n + 2*max_loops].
     * With n crossings the number of loops is at most U, but the
     * exponent magnitude is bounded by n + 2*(loops-1) <= n + 2*U. */
    int bound = n + 2 * (U + 1) + 4;
    oqd_lpoly bracket;
    if (lpoly_alloc(&bracket, -bound, bound) != 0) { free(cs); return OQD_J_NOMEM; }

    int *parent = malloc(sizeof(int) * (U > 0 ? U : 1));
    int *seen   = malloc(sizeof(int) * (U > 0 ? U : 1));
    /* scratch polynomial for d^(loops-1) accumulation, plus a multiply buffer */
    oqd_lpoly term;
    long long *mulbuf = NULL;
    if (!parent || !seen || lpoly_alloc(&term, -bound, bound) != 0) {
        free(parent); free(seen); lpoly_free(&bracket); free(cs);
        return OQD_J_NOMEM;
    }
    mulbuf = calloc(term.n, sizeof(long long));
    if (!mulbuf) {
        free(parent); free(seen); lpoly_free(&term); lpoly_free(&bracket); free(cs);
        return OQD_J_NOMEM;
    }

    unsigned long long states = (n < 63) ? (1ULL << n) : 0;
    out->n_states = (int)states;

    for (unsigned long long s = 0; s < states; s++) {
        for (int i = 0; i < U; i++) parent[i] = i;
        int a_cnt = 0, b_cnt = 0;
        for (int i = 0; i < n; i++) {
            int bit = (int)((s >> i) & 1ULL);
            if (bit == 0) {  /* A-smoothing: connect (e0,e1) and (e2,e3) */
                uf_union(parent, cs[i].e[0], cs[i].e[1]);
                uf_union(parent, cs[i].e[2], cs[i].e[3]);
                a_cnt++;
            } else {          /* B-smoothing: connect (e1,e2) and (e3,e0) */
                uf_union(parent, cs[i].e[1], cs[i].e[2]);
                uf_union(parent, cs[i].e[3], cs[i].e[0]);
                b_cnt++;
            }
        }
        memset(seen, 0, sizeof(int) * (U > 0 ? U : 1));
        int loops = 0;
        for (int lbl = 0; lbl < U; lbl++) {
            int r = uf_find(parent, lbl);
            if (!seen[r]) { seen[r] = 1; loops++; }
        }
        int base_exp = a_cnt - b_cnt;
        int dpow = (loops > 0) ? loops - 1 : 0;

        /* term = A^base_exp * (-A^2 - A^-2)^dpow, built iteratively */
        memset(term.coeff, 0, sizeof(long long) * term.n);
        lpoly_add_term(&term, base_exp, 1);
        for (int p = 0; p < dpow; p++) {
            /* multiply term by d = -A^2 - A^-2 into mulbuf, then swap back */
            memset(mulbuf, 0, sizeof(long long) * term.n);
            for (size_t i = 0; i < term.n; i++) {
                if (term.coeff[i] == 0) continue;
                long long c = term.coeff[i];
                int e = term.lo + (int)i;
                int e1 = e + 2, e2 = e - 2;
                if (e1 >= term.lo && e1 <= term.hi) mulbuf[e1 - term.lo] += -c;
                if (e2 >= term.lo && e2 <= term.hi) mulbuf[e2 - term.lo] += -c;
            }
            memcpy(term.coeff, mulbuf, sizeof(long long) * term.n);
        }
        for (size_t i = 0; i < term.n; i++)
            if (term.coeff[i]) lpoly_add_term(&bracket, term.lo + (int)i, term.coeff[i]);
    }

    lpoly_free(&term);
    free(mulbuf);
    free(parent); free(seen); free(cs);

    /* Jones normalisation: f(A) = (-A)^(-3w) * <D>.
     * (-A)^(-3w) = (-1)^(-3w) * A^(-3w) = (-1)^(3w) * A^(-3w).
     * So shift every exponent by -3w and multiply sign by (-1)^(3w)=(-1)^w. */
    int shift = -3 * writhe;
    int sgn = (writhe & 1) ? -1 : 1;
    oqd_lpoly jones;
    int jlo = bracket.lo + shift, jhi = bracket.hi + shift;
    if (lpoly_alloc(&jones, jlo, jhi) != 0) { lpoly_free(&bracket); return OQD_J_NOMEM; }
    for (size_t i = 0; i < bracket.n; i++) {
        if (bracket.coeff[i] == 0) continue;
        int e = bracket.lo + (int)i + shift;
        jones.coeff[e - jones.lo] += sgn * bracket.coeff[i];
    }

    /* trim reported span to nonzero support */
    int flo = jhi, fhi = jlo, any = 0;
    for (size_t i = 0; i < jones.n; i++) {
        if (jones.coeff[i]) { int e = jones.lo + (int)i; if (!any) { flo = e; fhi = e; any = 1; } if (e < flo) flo = e; if (e > fhi) fhi = e; }
    }
    out->span = any ? (double)(fhi - flo) : 0.0;

    out->bracket = bracket;
    out->jones = jones;
    return OQD_J_OK;
}

void oqd_jones_free(oqd_knot_invariant *inv) {
    lpoly_free(&inv->bracket);
    lpoly_free(&inv->jones);
}

int oqd_jones_seed(const oqd_knot_invariant *inv, uint8_t *out, size_t cap) {
    size_t used = 0;
    if (cap < 16) return OQD_J_SMALLBUF;
    /* header: magic, writhe, crossings, states */
    const char *magic = "OQD-JONES-v1";
    size_t ml = strlen(magic);
    if (used + ml > cap) return OQD_J_SMALLBUF;
    memcpy(out + used, magic, ml); used += ml;
    int32_t hdr[3] = { inv->writhe, inv->n_crossings, inv->n_states };
    if (used + sizeof hdr > cap) return OQD_J_SMALLBUF;
    memcpy(out + used, hdr, sizeof hdr); used += sizeof hdr;
    /* the topological payload: the Jones invariant, then the raw bracket */
    if (lpoly_serialize(&inv->jones, out, cap, &used) != 0) return OQD_J_SMALLBUF;
    if (lpoly_serialize(&inv->bracket, out, cap, &used) != 0) return OQD_J_SMALLBUF;
    return (int)used;
}
