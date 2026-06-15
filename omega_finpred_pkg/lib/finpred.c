/*
 * lib/finpred.c — implementation of the omega_finpred_pkg API.
 *
 * Honest note: a small, transparent toy model. The "complex transform"
 * zeta(x) = i*sin(i*x*log(x)) is a real, well-defined function (it reduces to
 * -sinh(x*ln x) for x>0); prediction is a plain moving average. This is for
 * experimentation, not financial advice.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <complex.h>
#include "finpred.h"

#define MAX_LINE 8192
#define MAX_FIELDS 64

/* Split a CSV line (in place) into fields; returns the field count. */
static int split_csv(char *line, char *fields[], int max) {
    int n = 0;
    char *p = line;
    /* strip trailing CR/LF */
    size_t len = strlen(p);
    while (len > 0 && (p[len-1] == '\n' || p[len-1] == '\r')) p[--len] = '\0';
    /* skip a UTF-8 BOM if present at the very start */
    if ((unsigned char)p[0] == 0xEF && (unsigned char)p[1] == 0xBB && (unsigned char)p[2] == 0xBF) p += 3;
    fields[n++] = p;
    for (; *p && n < max; ++p) {
        if (*p == ',') { *p = '\0'; fields[n++] = p + 1; }
    }
    return n;
}

/* zeta(x) = i*sin(i*x*log(x)); NaN for x<=0 (log undefined). */
static double complex zeta_transform(double x) {
    if (x <= 0.0 || !isfinite(x)) return CMPLX(NAN, NAN);
    return I * csin(I * x * log(x));
}

/* Is the string a parseable finite number? */
static int parse_number(const char *s, double *out) {
    if (!s || !*s) return 0;
    char *end = NULL;
    double v = strtod(s, &end);
    if (end == s || !isfinite(v)) return 0;
    *out = v;
    return 1;
}

int finpred_ingest_csv(const char *path) {
    FILE *in = fopen(path, "rb");
    if (!in) { fprintf(stderr, "finpred: cannot open %s\n", path); return 1; }

    char line[MAX_LINE];
    long rows = 0;
    while (fgets(line, sizeof line, in)) {
        char *f[MAX_FIELDS];
        int nf = split_csv(line, f, MAX_FIELDS);
        if (nf < 2) continue;

        /* require a numeric date in column 0 (skips header rows) */
        double date_val;
        if (!parse_number(f[0], &date_val)) continue;

        const char *date = f[0];
        const char *symbol = f[1];
        double price = 0.0;
        if (nf >= 3) (void)parse_number(f[2], &price);   /* 0 if non-numeric */

        double complex z = zeta_transform(price);

        char out[512];
        snprintf(out, sizeof out, "data/%s.csv", symbol);
        FILE *o = fopen(out, "a");
        if (!o) continue;
        fprintf(o, "%s,%g,%g,%g\n", date, price, creal(z), cimag(z));
        fclose(o);
        rows++;
    }
    fclose(in);
    printf("ingested %ld rows from %s\n", rows, path);
    return 0;
}

int finpred_transform_csv(const char *path) {
    FILE *in = fopen(path, "rb");
    if (!in) { fprintf(stderr, "finpred: cannot open %s\n", path); return 1; }

    char line[MAX_LINE];
    printf("date,symbol,price,zeta_re,zeta_im\n");
    while (fgets(line, sizeof line, in)) {
        char *f[MAX_FIELDS];
        int nf = split_csv(line, f, MAX_FIELDS);
        if (nf < 2) continue;
        double date_val;
        if (!parse_number(f[0], &date_val)) continue;
        double price = 0.0;
        if (nf >= 3) (void)parse_number(f[2], &price);
        double complex z = zeta_transform(price);
        printf("%s,%s,%g,%g,%g\n", f[0], f[1], price, creal(z), cimag(z));
    }
    fclose(in);
    return 0;
}

double finpred_predict(const char *symbol, int window) {
    if (window <= 0) window = 5;
    char path[512];
    snprintf(path, sizeof path, "data/%s.csv", symbol);
    FILE *in = fopen(path, "rb");
    if (!in) { fprintf(stderr, "finpred: no data for %s (%s)\n", symbol, path); return NAN; }

    /* keep the last `window` prices in a ring buffer */
    double *ring = calloc((size_t)window, sizeof(double));
    if (!ring) { fclose(in); return NAN; }
    int count = 0, head = 0;

    char line[MAX_LINE];
    while (fgets(line, sizeof line, in)) {
        char *f[MAX_FIELDS];
        int nf = split_csv(line, f, MAX_FIELDS);
        if (nf < 2) continue;
        double price;
        if (!parse_number(f[1], &price)) continue;   /* per-symbol col1 = price */
        ring[head] = price;
        head = (head + 1) % window;
        count++;
    }
    fclose(in);

    if (count == 0) { free(ring); return NAN; }
    int used = count < window ? count : window;
    double sum = 0.0;
    for (int i = 0; i < used; ++i) sum += ring[i];
    free(ring);
    return sum / used;
}
