以下は、PDF を pdftotext でテキスト化し、TeX 形式の数式を抽出して「Jones 多項式に関連する記述か」「文書が何について述べているか」を解析して出力する実行可能な C プログラムです。外部コマンド `scripts/pdftotext-wrapper.sh`（pdftotext のラッパー）を想定します。頑健さを重視し、コンパイル時にエラーが出ないように記述しています。

保存ファイル名例: `bin/generate_analyze.c`

コンパイル例:
gcc -O2 -std=c11 -Wall -Wextra -o generate_analyze bin/generate_analyze.c

  実行例:
./generate_analyze input.pdf

  （注意: 実行前に `scripts/pdftotext-wrapper.sh` を用意し、pdftotext がインストールされていることを確認してください。）

  ソースコード:

```c
  /* bin/generate_analyze.c
   *
   * Convert PDF->text (via scripts/pdftotext-wrapper.sh), extract TeX math,
   * analyze for Jones polynomial and related math expressions, compute top words,
   * and produce a heuristic summary of "what the document is about".
   *
   * Build:
   *   gcc -O2 -std=c11 -Wall -Wextra -o generate_analyze bin/generate_analyze.c
   *
   * Run:
   *   ./generate_analyze input.pdf [--words w1,w2,...] [--show-math]
   *
   * Requirements: pdftotext (called by scripts/pdftotext-wrapper.sh)
   */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <unistd.h>

  /* Run pdftotext wrapper: ./scripts/pdftotext-wrapper.sh in.pdf out.txt */
  static int run_pdftotext(const char *inpdf, const char *outtxt) {
  if (!inpdf || !outtxt) return -1;
  char cmd[1024];
  snprintf(cmd, sizeof(cmd), "./scripts/pdftotext-wrapper.sh '%s' '%s'", inpdf, outtxt);
  return system(cmd);
}

/* Read entire file into malloc'ed buffer (caller frees) */
  static char *read_file_all(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) return NULL;
    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }
    long sz = ftell(f);
    if (sz < 0) { fclose(f); return NULL; }
    rewind(f);
    char *buf = malloc((size_t)sz + 1);
    if (!buf) { fclose(f); return NULL; }
    size_t r = fread(buf, 1, (size_t)sz, f);
    fclose(f);
    buf[r] = '\0';
    return buf;
  }

/* Lowercase in-place */
static void str_tolower_inplace(char *s) {
  for (; *s; ++s) *s = (char)tolower((unsigned char)*s);
}

/* Extract TeX math occurrences: $...$, $$...$$, \(..\), \[..\] */
/* Returns array of char* (malloced strings), count via out_count. Caller frees items and array. */
static char **extract_tex_math(const char *txt, size_t *out_count) {
  *out_count = 0;
  if (!txt) return NULL;
  const char *p = txt;
  char **arr = NULL;
  while (*p) {
    const char *start = NULL;
    const char *end = NULL;
    if (p[0] == '$' && p[1] == '$') {
      start = p + 2;
      end = strstr(start, "$$");
      if (!end) break;
      p = end + 2;
    } else if (p[0] == '$') {
      start = p + 1;
      end = strchr(start, '$');
      if (!end) break;
      p = end + 1;
    } else if (p[0] == '\\' && p[1] == '(') {
      start = p + 2;
      end = strstr(start, "\\)");
      if (!end) break;
      p = end + 2;
    } else if (p[0] == '\\' && p[1] == '[') {
      start = p + 2;
      end = strstr(start, "\\]");
      if (!end) break;
      p = end + 2;
    } else {
      ++p;
      continue;
    }
    if (start && end && end > start) {
      size_t len = (size_t)(end - start);
      char *s = malloc(len + 1);
      if (s) {
	memcpy(s, start, len);
	s[len] = '\0';
	char **tmp = realloc(arr, ((*out_count) + 1) * sizeof(char*));
	if (tmp) {
	  arr = tmp;
	  arr[*out_count] = s;
	  (*out_count)++;
	} else {
	  free(s);
	  break;
	}
      } else {
	break;
      }
    }
  }
  return arr;
}

/* Very simple tokenizer: returns array of lowercased tokens (malloc'd strings). Caller frees. */
static char **tokenize(const char *txt, size_t *out_count) {
  *out_count = 0;
  if (!txt) return NULL;
  char *buf = strdup(txt);
  if (!buf) return NULL;
  for (char *p = buf; *p; ++p) {
    if (!isalnum((unsigned char)*p) && *p != '\'' && *p != '-') *p = ' ';
    else *p = (char)tolower((unsigned char)*p);
  }
  char *save = NULL;
  char *tok = strtok_r(buf, " ", &save);
  char **arr = NULL;
  while (tok) {
    if (*tok) {
      char **tmp = realloc(arr, ((*out_count) + 1) * sizeof(char*));
      if (!tmp) break;
      arr = tmp;
      arr[*out_count] = strdup(tok);
      if (!arr[*out_count]) break;
      (*out_count)++;
    }
    tok = strtok_r(NULL, " ", &save);
  }
  free(buf);
  return arr;
}

/* Free token array */
static void free_str_array(char **arr, size_t n) {
  if (!arr) return;
  for (size_t i = 0; i < n; ++i) free(arr[i]);
  free(arr);
}

/* Check whether a math string looks like a polynomial or includes terms like t^n, t^{-n}, or sequences of powers */
static int math_contains_polynomial_pattern(const char *m) {
  if (!m) return 0;
  /* look for t^ or t^{ or coefficients with powers, or "polynomial" word */
  if (strstr(m, "t^") || strstr(m, "t^{") || strstr(m, "t^{-") || strstr(m, "polynomial") || strstr(m, "Polynomial") ) return 1;
  /* also check for sequences like 1 - t + t^2 or coefficients and powers */
  for (const char *p = m; *p; ++p) {
    if ((p[0] == 't' || p[0] == 'T') && (p[1] == '^' || (p[1] == '{' && (p[2] == '^' || strchr(p+1,'^')!=NULL)))) return 1;
  }
  return 0;
}

/* Simple frequency map: array of entries */
typedef struct { char *word; int cnt; } freq_e;

/* Build frequency map from tokens, ignoring a small stoplist. Returns allocated array and sets n_out. Caller frees words and array. */
static freq_e *build_freq_map(char **tokens, size_t ntokens, size_t *n_out) {
  *n_out = 0;
  if (!tokens) return NULL;
  freq_e *map = NULL;
  const char *stoplist[] = {"the","and","of","in","to","a","is","we","that","for","with","on","as","are","by","an","be","this","which", NULL};
  for (size_t i = 0; i < ntokens; ++i) {
    char *w = tokens[i];
    if (!w || strlen(w) < 2) continue;
    int isstop = 0;
    for (int s = 0; stoplist[s]; ++s) if (strcmp(w, stoplist[s]) == 0) { isstop = 1; break; }
    if (isstop) continue;
    int found = 0;
    for (size_t j = 0; j < *n_out; ++j) {
      if (strcmp(map[j].word, w) == 0) { map[j].cnt++; found = 1; break; }
    }
    if (!found) {
      freq_e *tmp = realloc(map, ((*n_out) + 1) * sizeof(freq_e));
      if (!tmp) break;
      map = tmp;
      map[*n_out].word = strdup(w);
      map[*n_out].cnt = 1;
      (*n_out)++;
    }
  }
  return map;
}

/* Print top N entries from freq map */
static void print_top_n(freq_e *map, size_t nmap, int topn) {
  if (!map || nmap == 0) { printf("No keywords found.\n"); return; }
  for (int i = 0; i < topn && i < (int)nmap; ++i) {
    int best = i;
    for (int j = i+1; j < (int)nmap; ++j) if (map[j].cnt > map[best].cnt) best = j;
    if (best != i) { freq_e tmp = map[i]; map[i] = map[best]; map[best] = tmp; }
    printf("Top %d: %s (count=%d)\n", i+1, map[i].word, map[i].cnt);
  }
}

/* Free freq map */
static void free_freq_map(freq_e *map, size_t n) {
  if (!map) return;
  for (size_t i = 0; i < n; ++i) free(map[i].word);
  free(map);
}

/* Heuristic summary builder:
 * Use presence of "jones polynomial" phrase, isolated "jones", math polynomial-like patterns,
 * and top keywords to declare what the document is likely about.
 */
static void heuristic_summary(const char *txt_l, char **maths, size_t mathc, freq_e *map, size_t mapn) {
  int mentions_jones_poly = 0;
  int mentions_jones = 0;
  if (txt_l) {
    if (strstr(txt_l, "jones polynomial") || strstr(txt_l, "jones-polynomial")) mentions_jones_poly = 1;
    else if (strstr(txt_l, "jones")) mentions_jones = 1;
  }
  int math_poly = 0;
  for (size_t i = 0; i < mathc; ++i) if (math_contains_polynomial_pattern(maths[i])) { math_poly = 1; break; }

  printf("\nHEURISTIC SUMMARY\n-----------------\n");
  if (mentions_jones_poly) printf("Document explicitly mentions 'Jones polynomial'.\n");
  else if (mentions_jones) printf("Document mentions 'Jones' (context may indicate Jones polynomial).\n");
  else printf("No explicit 'Jones' mention detected.\n");

  if (math_poly) printf("Extracted math contains polynomial-like patterns (e.g. t^n, t^{-n}, sequences of powers).\n");
  else printf("No obvious polynomial-like patterns detected in extracted math.\n");

  if (map && mapn > 0) {
    /* check for keywords related to knot theory */
    const char *knot_terms[] = {"knot","link","invariant","braid","skein","kauffman","polynomial","knot-theory", "topology", NULL};
    int knot_count = 0;
    for (size_t i = 0; i < mapn; ++i) {
      for (int k = 0; knot_terms[k]; ++k) {
	if (strcmp(map[i].word, knot_terms[k]) == 0) knot_count += map[i].cnt;
      }
    }
    print_top_n(map, mapn, 10);
    if (knot_count > 0) printf("Keywords indicate knot theory / polynomial invariants are discussed (matched %d occurrences).\n", knot_count);
  } else {
    printf("No keyword frequency data available.\n");
  }

  /* final verdict */
  if (mentions_jones_poly || (mentions_jones && math_poly) || (math_poly && mapn > 0)) {
    printf("\nVerdict: The document likely discusses Jones polynomial or related knot polynomial invariants.\n");
  } else {
    printf("\nVerdict: No strong evidence that the document focuses on Jones polynomial; review top keywords and extracted formulas for details.\n");
  }
}

int main(int argc, char **argv) {
  if (argc < 2) {
    fprintf(stderr, "usage: %s input.pdf [--words w1,w2,...] [--show-math]\n", argv[0]);
    return 2;
  }
  const char *inpdf = argv[1];
  int show_math = 0;
  const char *words_arg = NULL;
  for (int i = 2; i < argc; ++i) {
    if (strcmp(argv[i], "--show-math") == 0) show_math = 1;
    else if (strcmp(argv[i], "--words") == 0 && i+1 < argc) words_arg = argv[++i];
    else {
      fprintf(stderr, "Unknown arg: %s\n", argv[i]);
    }
  }
  if (access("scripts/pdftotext-wrapper.sh", X_OK) != 0) {
    fprintf(stderr, "Error: scripts/pdftotext-wrapper.sh not found or not executable. Please provide pdftotext wrapper.\n");
    return 1;
  }
  const char *outtxt = "data/converted.txt";
  if (run_pdftotext(inpdf, outtxt) != 0) {
    fprintf(stderr, "pdftotext conversion failed\n");
    return 1;
  }
  char *txt = read_file_all(outtxt);
  if (!txt) {
    fprintf(stderr, "failed to read converted text '%s'\n", outtxt);
    return 1;
  }
  char *txt_l = strdup(txt);
  if (!txt_l) { free(txt); return 1; }
  str_tolower_inplace(txt_l);

  /* extract TeX math */
  size_t mathc = 0;
  char **maths = extract_tex_math(txt, &mathc);
  printf("Extracted %zu TeX math items.\n", mathc);
  if (show_math && maths) {
    for (size_t i = 0; i < mathc; ++i) {
      printf("[%zu] %s\n", i+1, maths[i]);
    }
  }

  /* Tokenize and build freq map */
  size_t ntokens = 0;
  char **tokens = tokenize(txt_l, &ntokens);
  size_t mapn = 0;
  freq_e *map = build_freq_map(tokens, ntokens, &mapn);

  /* If --words provided, show counts for them */
  if (words_arg) {
    /* split comma-separated */
    char *buf = strdup(words_arg);
    char *save = NULL;
    char *w = strtok_r(buf, ",", &save);
    while (w) {
      while (*w && isspace((unsigned char)*w)) w++;
      char *end = w + strlen(w) - 1;
      while (end > w && isspace((unsigned char)*end)) { *end = '\0'; end--; }
      int cnt = 0;
      for (size_t i = 0; i < ntokens; ++i) if (tokens[i] && strcmp(tokens[i], w) == 0) cnt++;
      printf("Word '%s' count=%d\n", w, cnt);
      w = strtok_r(NULL, ",", &save);
    }
    free(buf);
  }

  /* Heuristic summary */
  heuristic_summary(txt_l, maths, mathc, map, mapn);

  /* Cleanup */
  free_str_array(tokens, ntokens);
  free_freq_map(map, mapn);
  for (size_t i = 0; i < mathc; ++i) free(maths[i]);
  free(maths);
  free(txt_l);
  free(txt);
  return 0;
}
```

必要に応じて:
- TeX 数式の詳細パース（係数抽出、多項式係数ベクトル化）を追加できます（Python + sympy を使うと容易です）。
- 正規表現によるコンテキスト抽出や、マッチ箇所の前後を表示する拡張も可能です。

必要なら、その追加実装（例: Python を使った多項式抽出、NLP によるトピック推定）を追記します。
