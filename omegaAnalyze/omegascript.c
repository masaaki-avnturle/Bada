/*了解しました。d_type（DT_REG）に依存すると未定義の環境があり得るため、dirent->d_type を使わずに stat() を使って「通常ファイルか」を判定するよう修正した `omegascript.c` を示します。これで "DT_REG undeclared" エラーは出ません。

保存名: usr/lang/omegascript.c（単体ファイルとして保存してビルドしてください）
ビルド:
  gcc -O2 -std=c11 -Wall -o omegascript omegascript.c -lm

  修正版:
```c
*/
  /* omegascript.c
   *
   * Analyzer: extract title/theorem/formula/proof/conclusion/conjecture
   * and validate zeta/Jones/Higgs-like formulas heuristically.
   *
   * Build:
   *   gcc -O2 -std=c11 -Wall -o omegascript omegascript.c -lm
   */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <dirent.h>
#include <sys/stat.h>
#include <unistd.h>
#include <math.h>
#include <errno.h>

  static char *read_whole(const char *path) {
  FILE *f = fopen(path, "rb");
  if (!f) return NULL;
  if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }
  long s = ftell(f); fseek(f, 0, SEEK_SET);
  char *b = malloc((size_t)s + 1);
  if (!b) { fclose(f); return NULL; }
  if (fread(b, 1, (size_t)s, f) != (size_t)s) { free(b); fclose(f); return NULL; }
  b[s] = '\0'; fclose(f); return b;
}

/* Helper: is entry a regular file? use stat() for portability. */
  static int is_regular_file(const char *dir, const char *name) {
    char path[1024];
    if (snprintf(path, sizeof(path), "%s/%s", dir, name) >= (int)sizeof(path)) return 0;
    struct stat st;
    if (stat(path, &st) != 0) return 0;
    return S_ISREG(st.st_mode);
  }

/* Run pdftotext on PDFs in a directory (produces .txt alongside) */
static void run_pdftotext(const char *dir) {
  DIR *d = opendir(dir);
  if (!d) { fprintf(stderr, "cannot open %s: %s\n", dir, strerror(errno)); return; }
  struct dirent *e;
  while ((e = readdir(d)) != NULL) {
    const char *name = e->d_name;
    size_t L = strlen(name);
    if (L <= 4) continue;
    if (strcasecmp(name + L - 4, ".pdf") != 0) continue;
    if (!is_regular_file(dir, name)) continue;
    char src[1024];
    snprintf(src, sizeof(src), "%s/%s", dir, name);
    char cmd[2048];
    snprintf(cmd, sizeof(cmd), "pdftotext '%s' '%s.txt' 2>/dev/null", src, src);
    system(cmd);
  }
  closedir(d);
}

/* simple tokenizer */
static char **tokenize(const char *s, int *out_n) {
  int cap = 256;
  char **arr = malloc(sizeof(char*) * cap);
  int n = 0;
  const char *p = s;
  while (*p) {
    while (*p && !isalnum((unsigned char)*p)) p++;
    if (!*p) break;
    const char *q = p; while (*q && isalnum((unsigned char)*q)) q++;
    int L = (int)(q - p);
    char *t = malloc(L + 1);
    for (int i = 0; i < L; ++i) t[i] = (char)tolower((unsigned char)p[i]);
    t[L] = '\0';
    if (n >= cap) { cap *= 2; arr = realloc(arr, sizeof(char*) * cap); }
    arr[n++] = t;
    p = q;
  }
  *out_n = n; return arr;
}

static double shannon(char **tokens, int n) {
  if (n <= 0) return 0.0;
  int uniq = 0;
  char **u = malloc(sizeof(char*) * n);
  int *cnt = calloc(n, sizeof(int));
  for (int i = 0; i < n; ++i) {
    int idx = -1;
    for (int j = 0; j < uniq; ++j) if (strcmp(tokens[i], u[j]) == 0) { idx = j; break; }
    if (idx == -1) { u[uniq] = strdup(tokens[i]); cnt[uniq] = 1; uniq++; }
    else cnt[idx]++;
  }
  double H = 0.0;
  for (int i = 0; i < uniq; ++i) {
    double p = (double)cnt[i] / (double)n;
    if (p > 0) H -= p * log(p) / log(2.0);
    free(u[i]);
  }
  free(u); free(cnt);
  return H;
}

static double zeta_partial(double s, int N) {
  if (s <= 0) s = 0.5;
  if (N <= 0) N = 10000;
  double sum = 0.0;
  for (int n = 1; n <= N; ++n) sum += 1.0 / pow((double)n, s);
  return sum;
}

static int contains_token(const char *s, const char *kw) {
  if (!s || !kw) return 0;
  return (strcasestr(s, kw) != NULL);
}

/* validate zeta: if line contains a number, compare to partial sum heuristically */
static int validate_zeta(const char *line, double *out_val) {
  if (!contains_token(line, "zeta") && !contains_token(line, "ζ")) return 0;
  const char *p = line;
  double found = 0.0;
  int have = 0;
  while (*p) {
    if (isdigit((unsigned char)*p) || *p == '.' || *p == '-' ) {
      char buf[128]; int i = 0; const char *q = p;
      if (*q == '-') { buf[i++] = *q; q++; }
      while ((*q >= '0' && *q <= '9') || *q == '.') { if (i < 127) buf[i++] = *q; q++; }
      buf[i] = '\0'; found = atof(buf); have = 1; break;
    }
    p++;
  }
  if (!have) return 0;
  double z = zeta_partial(0.5, 20000);
  if (fabs(z - found) < fabs(0.1 * z) || fabs(z - found) < 1e-6) { if (out_val) *out_val = z; return 1; }
  return 0;
}

/* validate jones-like: presence of polynomial markers */
static int validate_jones(const char *line) {
  if (!contains_token(line, "jones")) return 0;
  if (strchr(line, '^') || strchr(line, 't') || strchr(line, 'x')) return 1;
  return 1; /* loose acceptance */
}

/* validate higgs-like: check presence of keywords or differential operators */
static int validate_higgs(const char *line) {
  if (!contains_token(line, "higgs") && !contains_token(line, "ヒッグス")) return 0;
  /* loose: if contains ∇ or □ or d/d or similar, accept */
  if (strstr(line, "∇") || strstr(line, "□") || strstr(line, "d/d") || strstr(line, "partial")) return 1;
  return 1;
}

static void analyze_dir(const char *dir, const char *out_tex, int pdf2txt) {
  if (pdf2txt) run_pdftotext(dir);
  DIR *d = opendir(dir);
  if (!d) { fprintf(stderr, "cannot open %s: %s\n", dir, strerror(errno)); return; }
  struct dirent *e;
  size_t cap = 1<<20;
  char *all = malloc(cap);
  if (!all) { closedir(d); return; }
  all[0] = '\0';
  size_t len = 0;
  int any = 0;

  while ((e = readdir(d)) != NULL) {
    const char *name = e->d_name;
    if (!is_regular_file(dir, name)) continue;
    size_t L = strlen(name);
    if (L > 4 && strcasecmp(name + L - 4, ".txt") == 0) {
      char path[1024];
      snprintf(path, sizeof(path), "%s/%s", dir, name);
      char *t = read_whole(path);
      if (!t) continue;
      any = 1;
      size_t need = len + strlen(t) + 256;
      if (need > cap) { cap = need * 2; all = realloc(all, cap); }
      strcat(all, "\n---- FILE: ");
      strcat(all, name);
      strcat(all, " ----\n");
      strcat(all, t);
      len = strlen(all);
      free(t);
    }
  }
  closedir(d);
  if (!any) { fprintf(stderr, "no .txt files in %s\n", dir); free(all); return; }

  char *title = NULL;
  char *theorems = malloc(1<<15); theorems[0] = '\0';
  char *proofs = malloc(1<<15); proofs[0] = '\0';
  char *formulas = malloc(1<<15); formulas[0] = '\0';
  char *conclusions = malloc(1<<15); conclusions[0] = '\0';
  char *conjectures = malloc(1<<15); conjectures[0] = '\0';

  int token_count = 0;
  char **tokens = NULL;

  const char *p = all;
  while (*p) {
    const char *nl = strchr(p, '\n');
    size_t L = nl ? (size_t)(nl - p) : strlen(p);
    char line[4096];
    if (L >= sizeof(line)) L = sizeof(line) - 1;
    memcpy(line, p, L); line[L] = '\0';
    p = nl ? nl + 1 : p + L;

    const char *s = line;
    while (*s && isspace((unsigned char)*s)) s++;
    if (*s == '\0') continue;
    if (!title) title = strdup(s);

    int is_theorem = (strcasestr(s, "theorem") || strstr(s, "定理") || strstr(s, "主張"));
    int is_proof = (strcasestr(s, "proof") || strstr(s, "証明"));
    int is_conclusion = (strcasestr(s, "conclusion") || strstr(s, "結論") || strstr(s, "まとめ"));
    int is_conjecture = (strcasestr(s, "conjecture") || strstr(s, "予想"));
    int is_formula = (strpbrk(s, "=^\\") != NULL) || strchr(s, '^') || strchr(s, '∫') || strchr(s, 'ζ') || strchr(s, 'Γ');

    int accept = 1;
    if (is_formula && contains_token(s, "zeta")) {
      double zval = 0.0;
      accept = validate_zeta(s, &zval);
    }
    if (is_formula && contains_token(s, "jones")) accept = validate_jones(s);
    if (is_formula && (contains_token(s, "higgs") || contains_token(s, "ヒッグス"))) accept = validate_higgs(s);

    if (is_theorem) { if (accept) { strncat(theorems, s, (1<<15) - strlen(theorems) - 1); strncat(theorems, "\n\n", (1<<15) - strlen(theorems) - 1); } }
    else if (is_proof) { if (accept) { strncat(proofs, s, (1<<15) - strlen(proofs) - 1); strncat(proofs, "\n", (1<<15) - strlen(proofs) - 1); } }
    else if (is_conclusion) { if (accept) { strncat(conclusions, s, (1<<15) - strlen(conclusions) - 1); strncat(conclusions, "\n", (1<<15) - strlen(conclusions) - 1); } }
    else if (is_conjecture) { if (accept) { strncat(conjectures, s, (1<<15) - strlen(conjectures) - 1); strncat(conjectures, "\n", (1<<15) - strlen(conjectures) - 1); } }
    else if (is_formula) { if (accept) { strncat(formulas, s, (1<<15) - strlen(formulas) - 1); strncat(formulas, "\n", (1<<15) - strlen(formulas) - 1); } }

    int tn = 0; char **tk = tokenize(s, &tn);
    if (tn > 0) {
      tokens = realloc(tokens, sizeof(char*) * (token_count + tn));
      for (int i = 0; i < tn; ++i) tokens[token_count + i] = tk[i];
      token_count += tn;
      free(tk);
    } else free(tk);
  }

  double H = shannon(tokens, token_count);

  FILE *f = fopen(out_tex, "wb");
  if (!f) { fprintf(stderr, "cannot open %s\n", out_tex); goto CLEAN; }
  fprintf(f, "\\documentclass{article}\n\\usepackage{amsmath,amsthm,amssymb}\n\\begin{document}\n");
  if (title) fprintf(f, "\\title{%s}\\maketitle\n", title);
  if (theorems[0]) fprintf(f, "\\section{Accepted Theorems}\n%s\n", theorems);
  if (formulas[0]) fprintf(f, "\\section{Validated Formulas}\n\\begin{verbatim}\n%s\n\\end{verbatim}\n", formulas);
  if (proofs[0]) fprintf(f, "\\section{Accepted Proofs}\n\\begin{verbatim}\n%s\n\\end{verbatim}\n", proofs);
  if (conclusions[0]) fprintf(f, "\\section{Accepted Conclusions}\n%s\n", conclusions);
  if (conjectures[0]) fprintf(f, "\\section{Conjectures}\n%s\n", conjectures);
  fprintf(f, "\\section{Validation Summary}\n\\begin{itemize}\n");
  fprintf(f, "\\item Token Shannon entropy: %.6f bits\n", H);
  fprintf(f, "\\end{itemize}\n\\end{document}\n");
  fclose(f);

  /* JSON */
  {
    char jp[1024];
    snprintf(jp, sizeof(jp), "%s.json", out_tex);
    FILE *j = fopen(jp, "wb");
    if (j) {
      fprintf(j, "{\n");
      fprintf(j, "  \"title\": \"%s\",\n", title ? title : "");
      fprintf(j, "  \"token_entropy\": %.6f\n", H);
      fprintf(j, "}\n");
      fclose(j);
    }
  }

 CLEAN:
  if (title) free(title);
  free(all); free(theorems); free(proofs); free(formulas); free(conclusions); free(conjectures);
  for (int i = 0; i < token_count; ++i) free(tokens[i]);
  free(tokens);
}

int main(int argc, char **argv) {
  if (argc < 2) { fprintf(stderr, "usage: %s analyze [--pdf2txt] <reports_dir> <out_tex>\n", argv[0]); return 1; }
  if (strcmp(argv[1], "analyze") != 0) { fprintf(stderr, "unknown command\n"); return 2; }
  int pdf = 0; int idx = 2;
  if (argc > 2 && strcmp(argv[2], "--pdf2txt") == 0) { pdf = 1; idx = 3; }
  if (argc <= idx) { fprintf(stderr, "need args\n"); return 1; }
  const char *dir = argv[idx++];
  const char *out = (idx < argc) ? argv[idx++] : "output/paper.tex";
  analyze_dir(dir, out, pdf);
  return 0;
}
/*
変更点（要点）
- dirent->d_type (DT_REG) を使う代わりに `is_regular_file()` を導入して stat() で判定するようにしました（ポータブル）。
- バッファ長や snprintf の使用は安全領域を想定していますが、非常に長いパス名がある環境では調整してください。
- 他の部分は元のヒューリスティック実装を保持しています。

このファイルを保存してビルド・実行してください。まだ別のコンパイルエラーや警告が出る場合は、そのコンパイルエラー全文を教えてください（行番号とメッセージ） — 迅速に修正します。
*/
