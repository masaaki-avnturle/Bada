/*以下は、指摘のエラー（例: "'save' undeclared here (not in function)" や "stray '\xxx' in program" 等）を起こす原因を取り除き、文字列リテラルやコメント、改行エスケープを正しく修正した完全な `pkg_finpred_gen.c`（修正版）です。保存してコンパイルすればエラーが出ないように整理してあります。

コンパイル:
gcc -O2 -std=c11 -Wall -Wextra -o pkg_finpred_gen pkg_finpred_gen.c

  ソースコード（そのまま保存してください）:

*/
  /*
   * pkg_finpred_gen.c (fixed)
   *
   * Generate a finance-prediction package "omega_finpred_pkg".
   * This fixed generator avoids stray characters and undeclared identifiers
   * by keeping string literals and comments well-formed.
   *
   * Build generator:
   *   gcc -O2 -std=c11 -Wall -Wextra -o pkg_finpred_gen pkg_finpred_gen.c
   * Run:
   *   ./pkg_finpred_gen
   *
   * The program writes the package directory "omega_finpred_pkg".
   */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

  static int ensure_dir(const char *p) {
  if (!p) return -1;
  struct stat st;
  if (stat(p, &st) == 0) return S_ISDIR(st.st_mode) ? 0 : -1;
  if (mkdir(p, 0755) == 0) return 0;
  if (errno == EEXIST) return 0;
  return -1;
}

static int write_file(const char *path, const char *data, int mode) {
  FILE *f = fopen(path, "wb");
  if (!f) return -1;
  size_t L = strlen(data);
  if (L && fwrite(data, 1, L, f) != L) { fclose(f); return -1; }
  fclose(f);
  if (mode) chmod(path, (mode_t)mode);
  return 0;
}

/* Minimal package files (Makefile, README, C source for lib, headers, example script) */
static const char *makefile_content =
"CC = gcc\n"
"CFLAGS = -O2 -std=c11 -Wall -Wextra -Iinclude\n"
"LDFLAGS =\n"
"\n"
"all: bin/finpred lib/libfinpred.a\n"
"\n"
"bin/finpred: bin/finpred.c lib/libfinpred.a\n"
"\t$(CC) $(CFLAGS) -o $@ bin/finpred.c lib/libfinpred.a $(LDFLAGS)\n"
"\n"
"lib/libfinpred.a: lib/finpred.o\n"
"\tar rcs $@ $^\n"
"\n"
"lib/finpred.o: lib/finpred.c include/finpred.h\n"
"\t$(CC) $(CFLAGS) -c -o $@ lib/finpred.c\n"
"\n"
"clean:\n"
"\trm -f lib/*.o lib/*.a bin/finpred\n"
"\n"
  ".PHONY: all clean\n";

static const char *readme =
"omega_finpred_pkg\n"
"\n"
"This package provides simple tools to:\n"
"- ingest CSV price data (date,symbol,price)\n"
"- compute a complex transform zeta(x) = i*sin(i*x*log(x)) per price value\n"
"- save per-symbol transformed series under data/<symbol>.csv\n"
"- run simple prediction (moving average or linear regression) to produce a point forecast\n"
"\n"
  "See bin/finpred usage for details.\n";

static const char *bin_finpred_c =
  "/* bin/finpred.c - small CLI to ingest CSV, compute transform, and predict */\n"
"#include <stdio.h>\n"
"#include <stdlib.h>\n"
"#include <string.h>\n"
"#include <math.h>\n"
"#include \"finpred.h\"\n"
"\n"
"static void usage(const char *p) {\n"
"    fprintf(stderr, \"Usage: %s ingest input.csv\\n\", p);\n"
"    fprintf(stderr, \"       %s transform input.csv\\n\", p);\n"
"    fprintf(stderr, \"       %s predict SYMBOL window\\n\", p);\n"
"}\n"
"\n"
"int main(int argc, char **argv) {\n"
"    if (argc < 2) { usage(argv[0]); return 1; }\n"
"    if (strcmp(argv[1], \"ingest\") == 0) {\n"
"        if (argc < 3) { usage(argv[0]); return 1; }\n"
"        if (finpred_ingest_csv(argv[2]) != 0) {\n"
"            fprintf(stderr, \"ingest failed\\n\"); return 1;\n"
"        }\n"
"        return 0;\n"
"    } else if (strcmp(argv[1], \"transform\") == 0) {\n"
"        if (argc < 3) { usage(argv[0]); return 1; }\n"
"        if (finpred_transform_csv(argv[2]) != 0) { fprintf(stderr, \"transform failed\\n\"); return 1; }\n"
"        return 0;\n"
"    } else if (strcmp(argv[1], \"predict\") == 0) {\n"
"        if (argc < 4) { usage(argv[0]); return 1; }\n"
"        const char *symbol = argv[2];\n"
"        int window = atoi(argv[3]); if (window <= 0) window = 5;\n"
"        double pred = finpred_predict(symbol, window);\n"
"        if (isnan(pred)) { fprintf(stderr, \"prediction failed\\n\"); return 1; }\n"
"        printf(\"Prediction for %s (window=%d): %.6f\\n\", symbol, window, pred);\n"
"        return 0;\n"
"    }\n"
"    usage(argv[0]);\n"
"    return 1;\n"
  "}\n";

static const char *include_finpred_h =
  "/* include/finpred.h */\n"
"#ifndef FINPRED_H\n"
"#define FINPRED_H\n"
"\n"
"int finpred_ingest_csv(const char *csvpath);\n"
"int finpred_transform_csv(const char *csvpath);\n"
"double finpred_predict(const char *symbol, int window);\n"
"\n"
  "#endif\n";

static const char *lib_finpred_c =
  "/* lib/finpred.c - implementations */\n"
"#include <stdio.h>\n"
"#include <stdlib.h>\n"
"#include <string.h>\n"
"#include <math.h>\n"
"#include <errno.h>\n"
"#include \"finpred.h\"\n"
"\n"
"/* Data layout: input CSV rows: date(YYYY-MM-DD),symbol,price\n"
"   ingest: append raw CSV lines into data/raw.csv\n"
"   transform: for each line compute transform and append to data/<symbol>.csv as: date,price,real,imag\n"
"   predict: load last N transformed values and compute simple prediction (moving average of real part)\n"
  "*/\n"
"\n"
"static const char *DATA_DIR = \"data\";\n"
"\n"
"static int ensure_data_dir(void) {\n"
"    struct stat st;\n" 
"    if (stat(DATA_DIR, &st) == 0) return 0;\n" 
"    if (mkdir(DATA_DIR, 0755) == 0) return 0;\n" 
"    return -1;\n" 
"}\n"
"\n"
  "/* safe log wrapper: return NaN if x<=0 */\n"
"static double safe_log(double x) {\n"
"    if (x <= 0.0) return NAN;\n"
"    return log(x);\n"
"}\n"
"\n"
"/* compute zeta-like transform: z(x) = i * sin(i * x * log x)\n" 
"   sin(i*a) = i*sinh(a) -> i * sin(i*a) = i*(i*sinh(a)) = -sinh(a)\n" 
"   thus result is real = -sinh(x*log x), imag = 0\n" 
  "*/\n"
"static void compute_zeta(double x, double *out_re, double *out_im) {\n"
"    if (out_re) *out_re = NAN;\n"
"    if (out_im) *out_im = NAN;\n" 
"    if (!(isfinite(x) && x > 0.0)) return;\n"
"    double a = x * safe_log(x);\n" 
"    if (!isfinite(a)) return;\n"
"    double s = sinh(a);\n"
"    if (out_re) *out_re = -s;\n"
"    if (out_im) *out_im = 0.0;\n"
"}\n"
"\n"
"int finpred_ingest_csv(const char *csvpath) {\n"
"    if (!csvpath) return -1;\n" 
"    if (ensure_data_dir() != 0) return -1;\n" 
"    FILE *in = fopen(csvpath, \"r\");\n" 
"    if (!in) return -1;\n" 
"    char outpath[512]; snprintf(outpath, sizeof(outpath), \"%s/raw.csv\", DATA_DIR);\n" 
"    FILE *out = fopen(outpath, \"a\");\n" 
"    if (!out) { fclose(in); return -1; }\n" 
"    char buf[1024];\n" 
"    while (fgets(buf, sizeof(buf), in)) {\n" 
"        fputs(buf, out);\n" 
"    }\n" 
"    fclose(in); fclose(out);\n" 
"    return 0;\n" 
"}\n"
"\n"
"int finpred_transform_csv(const char *csvpath) {\n"
"    if (!csvpath) return -1;\n" 
"    if (ensure_data_dir() != 0) return -1;\n" 
"    FILE *in = fopen(csvpath, \"r\");\n" 
"    if (!in) return -1;\n" 
"    char line[1024];\n" 
"    while (fgets(line, sizeof(line), in)) {\n"
"        char date[64] = \"\";\n" 
"        char sym[128] = \"\";\n" 
"        char price_s[128] = \"\";\n" 
  "        /* Try CSV parse: date,symbol,price */\n" 
"        int n = sscanf(line, \"%63[^,],%127[^,],%127s\", date, sym, price_s);\n" 
"        if (n < 3) {\n" 
  "            /* fallback tokenization */\n" 
"            char tmp[1024]; strncpy(tmp, line, sizeof(tmp)-1); tmp[sizeof(tmp)-1] = '\\0';\n" 
"            char *p = strtok(tmp, \",\\n\"); if (!p) continue; strncpy(date, p, sizeof(date)-1);\n" 
"            p = strtok(NULL, \",\\n\"); if (!p) continue; strncpy(sym, p, sizeof(sym)-1);\n" 
"            p = strtok(NULL, \",\\n\"); if (!p) continue; strncpy(price_s, p, sizeof(price_s)-1);\n" 
"        }\n" 
"        double price = strtod(price_s, NULL);\n" 
"        double re = NAN, im = NAN;\n" 
"        compute_zeta(price, &re, &im);\n" 
"        char outpath[512]; snprintf(outpath, sizeof(outpath), \"%s/%s.csv\", DATA_DIR, sym);\n" 
"        FILE *out = fopen(outpath, \"a\");\n" 
"        if (!out) continue;\n" 
"        fprintf(out, \"%s,%.12g,%.12g,%.12g\\n\", date, price, re, im);\n" 
"        fclose(out);\n" 
"    }\n" 
"    fclose(in);\n" 
"    return 0;\n" 
"}\n"
"\n"
"double finpred_predict(const char *symbol, int window) {\n"
"    if (!symbol || window <= 0) return NAN;\n" 
"    char path[512]; snprintf(path, sizeof(path), \"%s/%s.csv\", DATA_DIR, symbol);\n" 
"    FILE *f = fopen(path, \"r\"); if (!f) return NAN;\n" 
"    double *buf = malloc(sizeof(double) * (size_t)window);\n" 
"    if (!buf) { fclose(f); return NAN; }\n" 
"    int count = 0;\n" 
"    char line[1024];\n" 
"    while (fgets(line, sizeof(line), f)) {\n" 
"        char date[64]; double price, re, im;\n" 
"        if (sscanf(line, \"%63[^,],%lf,%lf,%lf\", date, &price, &re, &im) < 4) continue;\n" 
"        if (count < window) {\n" 
"            buf[count++] = re;\n" 
"        } else {\n" 
"            memmove(buf, buf + 1, sizeof(double) * (size_t)(window - 1));\n" 
"            buf[window - 1] = re;\n" 
"        }\n" 
"    }\n" 
"    fclose(f);\n" 
"    if (count == 0) { free(buf); return NAN; }\n" 
"    double sum = 0.0; int n = count < window ? count : window;\n" 
"    for (int i = 0; i < n; ++i) sum += buf[i];\n" 
"    free(buf);\n" 
"    return sum / (double)n;\n" 
  "}\n";

int main(void) {
  const char *root = "omega_finpred_pkg";
  char path[1024];

  if (ensure_dir(root) != 0) { fprintf(stderr, "failed to create %s\n", root); return 1; }

  /* create directories */
  const char *dirs[] = { "bin", "lib", "include", "etc", "usr", "data" };
  for (size_t i = 0; i < sizeof(dirs)/sizeof(dirs[0]); ++i) {
    snprintf(path, sizeof(path), "%s/%s", root, dirs[i]);
    ensure_dir(path);
  }

  /* write package files */
  snprintf(path, sizeof(path), "%s/Makefile", root);
  if (write_file(path, makefile_content, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  snprintf(path, sizeof(path), "%s/README.txt", root);
  if (write_file(path, readme, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  snprintf(path, sizeof(path), "%s/bin/finpred.c", root);
  if (write_file(path, bin_finpred_c, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  snprintf(path, sizeof(path), "%s/include/finpred.h", root);
  if (write_file(path, include_finpred_h, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  snprintf(path, sizeof(path), "%s/lib/finpred.c", root);
  if (write_file(path, lib_finpred_c, 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  printf("Generated package '%s'\n", root);
  printf("To build: cd %s && make\n", root);
  printf("Usage examples:\n");
  printf("  %s/bin/finpred ingest sample.csv\n", root);
  printf("  %s/bin/finpred transform sample.csv\n", root);
  printf("  %s/bin/finpred predict EURUSD 5\n", root);
  return 0;
}
/*
注意
- エラーメッセージにあった "'save' undeclared here (not in function)" は、通常ソース内に意図せず現れた識別子（例えば文字列中で閉じ忘れたクォートや stray バイト列）が原因で発生します。今回の修正では、全ての文字列リテラルを正しく閉じ、コメントとエスケープを整理しました。
- 上記を保存してコンパイルし、もしまだエラーメッセージが出る場合は、出力されるエラーメッセージ全文（行番号を含む）を示してください。それを元にさらに修正します。
*/
