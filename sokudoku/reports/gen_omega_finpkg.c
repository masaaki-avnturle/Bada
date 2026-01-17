  /*
   * gen_omega_finpkg.c
   *
   * Generator for "omega_fin_pkg":
   * - creates directories: bin, lib, include, etc, usr, examples
   * - writes prototype C modules:
   *   - lib/zeta.c : prototype zeta-like transform zeta(x) = i*sin(i*x*log x) implemented to return real feature
   *   - lib/data.c : CSV loader for daily price data (time,price) per symbol
   *   - lib/db.c   : simple per-day CSV database writer
   *   - lib/predict.c : simple linear-regression predictor on transformed features
   *   - include/omega_fin.h : public headers
   *   - bin/tools.c : CLI to ingest CSVs, build DB, compute transforms, and run prediction
   *   - usr/python_postproc.py : simple postprocessing helper (optional)
   * - Generated code is a prototype for experimentation. Not a production trading tool.
   *
   * Build generator:
   *   gcc -O2 -std=c11 -Wall -Wextra -o gen_omega_finpkg gen_omega_finpkg.c -lm
   *
   * Run generator:
   *   ./gen_omega_finpkg
   *
   * After running:
   *   cd omega_fin_pkg
   *   make
   *   Place CSV files in examples/ (format: date,price per line) named SYMBOL.csv
   *   ./bin/tools ingest SYMBOL examples/SYMBOL.csv
   *   ./bin/tools predict SYMBOL days_ahead
   *
   * Note: This is a minimal, self-contained prototype. Validate carefully before use.
   */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#if defined(_WIN32) || defined(_WIN64)
# include <direct.h>
# define MKDIR(p) _mkdir(p)
# define PATH_SEP '\\'
#else
# include <sys/stat.h>
# include <unistd.h>
# define MKDIR(p) mkdir((p), 0755)
# define PATH_SEP '/'
#endif

  static int ensure_dir(const char *p) {
  if (!p) return -1;
  int r = MKDIR(p);
  if (r == 0) return 0;
  if (errno == EEXIST) return 0;
  return -1;
}

static int write_file(const char *path, const char *data, int exec) {
  FILE *f = fopen(path, "wb");
  if (!f) return -1;
  size_t n = fwrite(data, 1, strlen(data), f);
  fclose(f);
  if (n != strlen(data)) return -1;
#if !defined(_WIN32) && !defined(_WIN64)
  if (exec) chmod(path, 0755);
#endif
  return 0;
}

int main(void) {
  const char *root = "omega_fin_pkg";
  const char *dirs[] = {
    "bin", "lib", "include", "etc", "usr", "examples", "etc/www"
  };
  char path[1024];

  if (ensure_dir(root) != 0) { fprintf(stderr, "mkdir %s failed: %s\n", root, strerror(errno)); return 1; }
  for (size_t i = 0; i < sizeof(dirs)/sizeof(dirs[0]); ++i) {
    snprintf(path, sizeof(path), "%s%c%s", root, PATH_SEP, dirs[i]);
    if (ensure_dir(path) != 0) { fprintf(stderr, "mkdir %s failed: %s\n", path, strerror(errno)); return 1; }
  }

  /* include/omega_fin.h */
    const char *hdr =
      "/* include/omega_fin.h */\n"
"#ifndef OMEGA_FIN_H\n"
"#define OMEGA_FIN_H\n\n"
"#include <stddef.h>\n"\n
      "/* Data row: date (YYYY-MM-DD) and price */\n"
"typedef struct { char date[32]; double price; } price_row_t;\n\n"
      "/* zeta-like transform: prototype mapping positive x->double feature */\n"
      "double zeta_transform(double x);\n\n/* data loader/writer */\n"
      "int load_csv_prices(const char *path, price_row_t **out_rows, size_t *out_n);\nint write_daily_db(const char *symbol, const char *date, double value);\n\n/* predictor: train on past N days, predict next day (simple linear regression) */\n"
      "int predict_next_price(const char *symbol, int lookback, double *out_pred);\n\n#endif\n";
    snprintf(path, sizeof(path), "%s%cinclude%comega_fin.h", root, PATH_SEP, PATH_SEP);
    if (write_file(path, hdr, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/zeta.c */
    const char *zeta_c =
      "/* lib/zeta.c - prototype zeta-like transform\n * The requested formula zeta(s) = i*sin(i*x*log x) is interpreted as a mapping\n * from positive real x to a real-valued feature using identities:\n *  i*sin(i*x*log x) = i * i * sinh(x*log x) = -sinh(x*log x)\n * We return -sinh(x*log x) as a numeric feature but cap values to avoid overflow.\n */\n#include <math.h>\n#include <float.h>\n#include \"../include/omega_fin.h\"\n\ndouble zeta_transform(double x) {\n    if (!(x > 0.0)) return 0.0;\n    double t = x * log(x);\n    /* sinh may overflow for large t; use safe checks */\n    if (t > 700) t = 700; /* avoid exp overflow */\n    if (t < -700) t = -700;\n    double s = sinh(t);\n    /* per identity above, return -sinh(t) */\n    return -s;\n}\n";
    snprintf(path, sizeof(path), "%s%clib%czeta.c", root, PATH_SEP, PATH_SEP);
    if (write_file(path, zeta_c, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/data.c : CSV loader, minimal and robust for simple CSV of date,price lines */
    const char *data_c =
      "/* lib/data.c - CSV loader for date,price lines */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include \"../include/omega_fin.h\"\n\nint load_csv_prices(const char *path, price_row_t **out_rows, size_t *out_n) {\n    if (!path || !out_rows || !out_n) return -1;\n    FILE *f = fopen(path, \"r\"); if (!f) return -1;\n    size_t cap = 128; size_t n = 0;\n    price_row_t *rows = (price_row_t*)malloc(sizeof(price_row_t)*cap);\n    if (!rows) { fclose(f); return -1; }\n    char line[256]; while (fgets(line, sizeof(line), f)) {\n        char date[64]; double price;\n        if (sscanf(line, \" %63[^,], %lf\", date, &price) == 2) {\n            if (n >= cap) { cap *= 2; price_row_t *tmp = realloc(rows, sizeof(price_row_t)*cap); if (!tmp) { free(rows); fclose(f); return -1; } rows = tmp; }\n            strncpy(rows[n].date, date, sizeof(rows[n].date)-1); rows[n].date[sizeof(rows[n].date)-1] = '\\0'; rows[n].price = price; n++;\n        }\n    }\n    fclose(f);\n    *out_rows = rows; *out_n = n; return 0;\n}\n\nint write_daily_db(const char *symbol, const char *date, double value) {\n    if (!symbol || !date) return -1;\n    char path[512]; snprintf(path, sizeof(path), \"daily_db_%s.csv\", symbol);\n    /* append CSV: date,value */\n    FILE *f = fopen(path, \"a\"); if (!f) return -1;\n    fprintf(f, \"%s,%.10g\\n\", date, value);\n    fclose(f); return 0;\n}\n";
    snprintf(path, sizeof(path), "%s%clib% cdata.c", root, PATH_SEP, PATH_SEP); /* safe temporary; fix below */
    snprintf(path, sizeof(path), "%s%clib%cdata.c", root, PATH_SEP, PATH_SEP);
    if (write_file(path, data_c, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/predict.c : simple linear regression on transformed features to predict next price */
    const char *predict_c =
      "/* lib/predict.c - simple predictor using linear regression on zeta-transformed prices */\n#include <stdlib.h>\n#include <stdio.h>\n#include <string.h>\n#include <math.h>\n#include \"../include/omega_fin.h\"\n\n/* Helper: compute linear regression slope/intercept for points (x_i,y_i)\n   returns 0 on success, -1 on failure */\nstatic int linear_regression(const double *x, const double *y, size_t n, double *out_a, double *out_b) {\n    if (!x || !y || n < 2 || !out_a || !out_b) return -1;\n    double sx=0, sy=0, sxx=0, sxy=0;\n    for (size_t i=0;i<n;++i) { sx += x[i]; sy += y[i]; sxx += x[i]*x[i]; sxy += x[i]*y[i]; }\n    double denom = (double)n * sxx - sx*sx;\n    if (fabs(denom) < 1e-12) return -1;\n    *out_a = ((double)n * sxy - sx*sy) / denom; /* slope */\n    *out_b = (sy - (*out_a)*sx) / (double)n;    /* intercept */\n    return 0;\n}\n\nint predict_next_price(const char *symbol, int lookback, double *out_pred) {\n    if (!symbol || !out_pred || lookback < 2) return -1;\n    /* read daily_db_SYMBOL.csv created by write_daily_db (CSV date,value) */\n    char path[512]; snprintf(path, sizeof(path), \"daily_db_%s.csv\", symbol);\n    FILE *f = fopen(path, \"r\"); if (!f) return -1;\n    /* load into arrays */\n    double *vals = NULL; size_t cap = 0, n = 0;\n    char line[256]; while (fgets(line, sizeof(line), f)) {\n        char date[64]; double v; if (sscanf(line, \" %63[^,], %lf\", date, &v) == 2) {\n            if (n >= cap) { size_t nc = cap?cap*2:128; double *t = realloc(vals, sizeof(double)*nc); if (!t) { free(vals); fclose(f); return -1; } vals = t; cap = nc; }\n            vals[n++] = v;\n        }\n    }\n    fclose(f);\n    if (n < (size_t)lookback) { free(vals); return -1; }\n    /* use last 'lookback' values, compute x = zeta_transform(price), y = price_next (shifted) */\n    size_t m = (size_t)lookback - 1; /* number of points for regression */\n    double *x = (double*)malloc(sizeof(double)*m); double *y = (double*)malloc(sizeof(double)*m);\n    if (!x || !y) { free(vals); free(x); free(y); return -1; }\n    for (size_t i=0;i<m;++i) {\n        double p = vals[n - lookback + i]; /* current */\n        double pnext = vals[n - lookback + i + 1]; /* next */\n        x[i] = zeta_transform(p);\n        y[i] = pnext;\n    }\n    double a=0,b=0; int rc = linear_regression(x,y,m,&a,&b);\n    double last_price = vals[n-1]; double last_x = zeta_transform(last_price);\n    double pred = (rc==0) ? (a*last_x + b) : last_price; /* fallback: no change */\n    *out_pred = pred;\n    free(vals); free(x); free(y); return rc==0?0:0; /* return 0 even if regression failed but produced fallback */\n}\n";
    snprintf(path, sizeof(path), "%s%clib%cpredict.c", root, PATH_SEP, PATH_SEP);
    if (write_file(path, predict_c, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* bin/tools.c : CLI to ingest CSV and run prediction */
    const char *tools_c =
      "/* bin/tools.c - CLI: ingest and predict (prototype) */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include \"../include/omega_fin.h\"\n\nint main(int argc, char **argv) {\n    if (argc < 2) { fprintf(stderr, \"usage: %s <command> [args]\\ncommands: ingest SYMBOL FILE, predict SYMBOL LOOKBACK\\n\", argv[0]); return 1; }\n    if (strcmp(argv[1], \"ingest\") == 0) {\n        if (argc < 4) { fprintf(stderr, \"usage: %s ingest SYMBOL FILE\\n\", argv[0]); return 1; }\n        const char *sym = argv[2]; const char *file = argv[3];\n        price_row_t *rows = NULL; size_t n=0; if (load_csv_prices(file, &rows, &n) != 0) { fprintf(stderr, \"failed to load %s\\n\", file); return 1; }\n        for (size_t i=0;i<n;++i) {\n            double feat = zeta_transform(rows[i].price);\n            /* write per-day DB: symbol -> daily_db_SYMBOL.csv (date, transformed_feature) */\n            if (write_daily_db(sym, rows[i].date, feat) != 0) fprintf(stderr, \"warn: write failed for %s %s\\n\", sym, rows[i].date);\n        }\n        for (size_t i=0;i<n;++i) free(rows[i].date); free(rows); printf(\"ingest done: %zu rows\\n\", n); return 0;\n    }\n    if (strcmp(argv[1], \"predict\") == 0) {\n        if (argc < 4) { fprintf(stderr, \"usage: %s predict SYMBOL LOOKBACK\\n\", argv[0]); return 1; }\n        const char *sym = argv[2]; int lookback = atoi(argv[3]); double pred=0.0;\n        if (predict_next_price(sym, lookback, &pred) == 0) printf(\"predicted next price for %s: %.10g\\n\", sym, pred);\n        else printf(\"prediction failed for %s\\n\", sym);\n        return 0;\n    }\n    fprintf(stderr, \"unknown command\\n\"); return 1;\n}\n";
    snprintf(path, sizeof(path), "%s%cbin%ctools.c", root, PATH_SEP, PATH_SEP);
    if (write_file(path, tools_c, 1) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* usr/python_postproc.py - optional helper to aggregate daily DBs */
    const char *py_post =
      "# usr/python_postproc.py - aggregate daily_db_SYMBOL.csv into per-day master CSV (prototype)\nimport sys, glob, csv\n\nif __name__ == '__main__':\n    if len(sys.argv)<2:\n        print('usage: python3 python_postproc.py out_master.csv')\n        sys.exit(1)\n    out = sys.argv[1]\n    files = glob.glob('daily_db_*.csv')\n    data = {}\n    for f in files:\n        sym = f[len('daily_db_'):-len('.csv')]\n        with open(f) as fh:\n            for line in fh:\n                line=line.strip()\n                if not line: continue\n                date,val = line.split(',',1)\n                data.setdefault(date, {})[sym]=val\n    syms = sorted({s for d in data.values() for s in d.keys()})\n    with open(out, 'w', newline='') as fo:\n        w = csv.writer(fo)\n        w.writerow(['date']+syms)\n        for date in sorted(data.keys()):\n            row = [date] + [data[date].get(s,'') for s in syms]\n            w.writerow(row)\n    print('wrote', out)\n";
    snprintf(path, sizeof(path), "%s%cusr%cpython_postproc.py", root, PATH_SEP, PATH_SEP);
    if (write_file(path, py_post, 1) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* examples/README and sample CSV format comment */
    const char *exread = "Put per-symbol CSV files here (date,price) lines. Example: 2025-01-02,123.45\n";
    snprintf(path, sizeof(path), "%s%cexamples%creadme.txt", root, PATH_SEP, PATH_SEP);
    if (write_file(path, exread, 0) != 0) { /* non-fatal */ ; }

    /* Makefile */
    const char *makefile =
      "CC=gcc\nCFLAGS=-O2 -Iinclude\nLIBS=-lm\n\nall: bin/tools\n\nbin/tools: bin/tools.c lib/zeta.c lib/data.c lib/predict.c\n\t$(CC) $(CFLAGS) -o bin/tools bin/tools.c lib/zeta.c lib/data.c lib/predict.c $(LIBS)\n\nclean:\n\trm -f bin/tools daily_db_*.csv\n";
    snprintf(path, sizeof(path), "%s%cMakefile", root, PATH_SEP);
    if (write_file(path, makefile, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* README */
    const char *readme =
      "omega_fin_pkg - prototype financial analysis package\n\nUsage:\n  1) Place CSV files in examples/: SYMBOL.csv with lines 'YYYY-MM-DD,price'\n  2) Build: make\n  3) Ingest: ./bin/tools ingest SYMBOL examples/SYMBOL.csv\n     This writes daily_db_SYMBOL.csv with date,transformed_feature\n  4) Predict: ./bin/tools predict SYMBOL LOOKBACK\n     LOOKBACK = number of days to use (>=2). Predictor runs simple linear regression on zeta-transformed prices.\n\nNotes:\n - zeta_transform implements the provided formula as numeric feature: returns -sinh(x*log x) safely capped.\n - This is a research prototype. Do not use for live trading without thorough validation.\n";
    snprintf(path, sizeof(path), "%s%cREADME.txt", root, PATH_SEP);
    if (write_file(path, readme, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

    printf(\"Generated package '%s' successfully.\\n\", root);
    printf(\"cd %s && make ; place CSVs in examples/ ; ./bin/tools ingest SYMBOL examples/SYMBOL.csv ; ./bin/tools predict SYMBOL LOOKBACK\\n\", root);
    return 0;
}
