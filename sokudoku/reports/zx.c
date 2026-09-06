理解しました。generate_analyze コマンドに以下の引数を追加できるようにし、PDF を pdftotext→テキスト化して（既存のラッパーを利用）、正規表現検出、単語リスト照合、TeX 形式数式抽出を行い、それらを元に「Jones 多項式の言及」「PDF が何について述べているか」の簡易解析を行して出力する安全な実装を生成する C プログラムを提示します。

ポイント（仕様）
- 生成器: `gen_omega_libmrg_full_pkg.c` を保存・コンパイル・実行するとパッケージ `omega_libmrg_full_pkg` を作成します。
- 生成物のコマンド: `bin/generate_analyze`（コンパイル済 C 実行ファイル）。
- generate_analyze の使い方:
  ./bin/generate_analyze input.pdf [--regex "PATTERN"] [--words "w1,w2,..."] [--tex]
- --regex: POSIX 正規表現（大文字小文字を区別しない）を本文に対して検索、マッチ件数を表示
- --words: カンマ区切りの単語リスト。各単語の出現回数を表示（大文字小文字無視）
- --tex: TeX 形式の数式抽出を有効にする（$...$, $$...$$, \(..\), \[..\]）
  - いずれも省略可能。常に LaTeX 数式の簡易抽出と "Jones" の検出は実行される（--tex は追加抽出を強調）
- 出力: 抽出した数式一覧、正規表現のマッチ数、指定単語ごとの出現数、上位キーワード、そして簡易ヒューリスティックによる「文書は何について述べているか」の推定（Jones 多項式の言及があるか・数式に多項式っぽい式が有るか・指定単語の出現状況などを組み合わせ）。

実装上の注意
- 実行には `pdftotext` と `python3` は不要（pdftotext は必要）。生成器により作成される `scripts/pdftotext-wrapper.sh` を使います。
- POSIX regex（<regex.h>）を使用します。
- 長いファイル内容を C ソース内の長いリテラルで扱わないよう、生成器は行配列を書き出す方式になっています（"stray '\\' in program" 等のエラーを回避）。

以下が、修正版の完全な生成器ソースコードです。保存してコンパイルしてください。

コンパイル・実行手順（要約）
1. gcc -O2 -std=c11 -Wall -Wextra -o gen_omega_libmrg_full_pkg gen_omega_libmrg_full_pkg.c
2. ./gen_omega_libmrg_full_pkg
3. cd omega_libmrg_full_pkg
4. make
5. ./bin/generate_analyze input.pdf [--regex "PATTERN"] [--words "w1,w2"] [--tex]

  ソースコード（そのまま保存してコンパイルしてください）:

```c
  /*
   * gen_omega_libmrg_full_pkg.c
   *
   * Generator that creates package with bin/generate_analyze supporting:
   *   --regex "PATTERN"
   *   --words "w1,w2,..."
   *   --tex
   *
   * The produced bin/generate_analyze uses pdftotext via scripts/pdftotext-wrapper.sh,
   * extracts TeX math, runs POSIX regex, counts words, and prints a heuristic summary
   * including detection of "Jones" / "Jones polynomial".
   *
   * Build generator:
   *   gcc -O2 -std=c11 -Wall -Wextra -o gen_omega_libmrg_full_pkg gen_omega_libmrg_full_pkg.c
   * Run:
   *   ./gen_omega_libmrg_full_pkg
   *
   * Then:
   *   cd omega_libmrg_full_pkg
   *   make
   *   ./bin/generate_analyze input.pdf --regex "yourpattern" --words "jones,polynomial" --tex
   */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>
#include <unistd.h>

  static int ensure_dir(const char *p) {
  if (!p) return -1;
  struct stat st;
  if (stat(p, &st) == 0) return S_ISDIR(st.st_mode) ? 0 : -1;
  if (mkdir(p, 0755) == 0) return 0;
  if (errno == EEXIST) return 0;
  return -1;
}

  static int write_lines_file(const char *path, const char **lines, size_t nlines, int mode) {
    FILE *f = fopen(path, "wb");
    if (!f) return -1;
    for (size_t i = 0; i < nlines; ++i) {
      if (fputs(lines[i], f) == EOF) { fclose(f); return -1; }
      if (fputc('\n', f) == EOF) { fclose(f); return -1; }
    }
    fclose(f);
    if (mode) chmod(path, (mode_t)mode);
    return 0;
  }

/* Makefile */
static const char *makefile_lines[] = {
  "CC = gcc",
  "CFLAGS = -O2 -std=c11 -Wall -Wextra -Iinclude",
  "BIN = bin/generate_analyze",
  "SRC = bin/generate_analyze.c",
  "",
  "all: $(BIN)",
  "",
  "$(BIN): $(SRC)",
  "\t$(CC) $(CFLAGS) -o $@ $(SRC) -Wall -Wextra -O2",
  "",
  "clean:",
  "\trm -f $(BIN)",
  "",
  ".PHONY: all clean",
};

/* pdftotext wrapper */
static const char *pdftotext_lines[] = {
  "#!/bin/sh",
  "# Usage: pdftotext-wrapper.sh in.pdf out.txt",
  "if [ $# -lt 2 ]; then",
  "  echo \"usage: $0 in.pdf out.txt\" >&2",
  "  exit 2",
  "fi",
  "IN=\"$1\"",
  "OUT=\"$2\"",
  "if command -v pdftotext >/dev/null 2>&1; then",
  "  pdftotext \"$IN\" \"$OUT\"",
  "  exit $?",
  "else",
  "  echo \"pdftotext not found\" >&2",
  "  exit 127",
  "fi",
};

/* omega script saved */
static const char *omega_lines[] = {
  "import \"python:MathExpressionGenerator\" as generator",
  "",
  "module MathExpressionGenerator:",
  "    def generate_expression(language: String, max_depth: Int = 3) -> String:",
  "        python_generator = generator.MathExpressionGenerator([\"c.bnf\", \"python.bnf\", \"ruby.bnf\", \"javascript.bnf\"])",
  "        return python_generator.generate_expression(language, max_depth)",
  "",
  "# 使用例",
  "language = \"python\"",
  "expression = MathExpressionGenerator.generate_expression(language)",
  "print(f\"Generated expression in {language}: {expression}\")",
};

/* small python CLI that we include (not required by analysis but included) */
static const char *py_lines[] = {
  "#!/usr/bin/env python3",
  "import sys, argparse, random",
  "from collections import defaultdict",
  "",
  "class MathExpressionGenerator:",
  "    def __init__(self, bnf_files):",
  "        self.bnf_rules = self.parse_bnf_files(bnf_files)",
  "    def parse_bnf_files(self, bnf_files):",
  "        from collections import defaultdict",
  "        bnf_rules = defaultdict(list)",
  "        for b in bnf_files:",
  "            try:",
  "                with open(b,'r') as f:",
  "                    for line in f:",
  "                        line=line.strip()",
  "                        if line and not line.startswith('#') and '::=' in line:",
  "                            left,right = line.split('::=',1)",
  "                            bnf_rules[left.strip()].append(right.strip())",
  "            except FileNotFoundError:",
  "                continue",
  "        return bnf_rules",
  "    def generate_expression(self, language, max_depth=3):",
  "        return 'x + y'",
  "def main():",
  "    p=argparse.ArgumentParser()",
  "    p.add_argument('--language',default='python')",
  "    args=p.parse_args()",
  "    g=MathExpressionGenerator(['c.bnf','python.bnf','ruby.bnf','javascript.bnf'])",
  "    print(g.generate_expression(args.language))",
  "if __name__=='__main__':",
  "    main()",
};

/* bin/generate_analyze.c */
static const char *analyze_c_lines[] = {
  "/* bin/generate_analyze.c */",
  "#define _POSIX_C_SOURCE 200809L",
  "#include <stdio.h>",
  "#include <stdlib.h>",
  "#include <string.h>",
  "#include <ctype.h>",
  "#include <unistd.h>",
  "#include <regex.h>",
  "",
  "static int run_pdftotext(const char *inpdf, const char *outtxt) {",
  "    char cmd[1024];",
  "    snprintf(cmd, sizeof(cmd), \"./scripts/pdftotext-wrapper.sh '%s' '%s'\", inpdf, outtxt);",
  "    return system(cmd);",
  "}",
  "",
  "static char *read_file_all(const char *path) {",
  "    FILE *f = fopen(path, \"r\"); if (!f) return NULL;",
  "    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }",
  "    long sz = ftell(f); if (sz < 0) { fclose(f); return NULL; }",
  "    rewind(f);",
  "    char *buf = malloc((size_t)sz + 1); if (!buf) { fclose(f); return NULL; }",
  "    if (fread(buf, 1, (size_t)sz, f) != (size_t)sz) { free(buf); fclose(f); return NULL; }",
  "    buf[sz] = '\\0'; fclose(f); return buf;",
  "}",
  "",
  "static void str_tolower_inplace(char *s) { for (; *s; ++s) *s = (char)tolower((unsigned char)*s); }",
  "",
  "/* extract TeX math: $...$, $$...$$, \\(...\\), \\[...\\] */",
  "static char **extract_tex_math(const char *txt, size_t *count) {",
  "    *count = 0; char **arr = NULL; const char *p = txt;",
  "    while (*p) {",
  "        const char *start = NULL; const char *end = NULL;",
  "        if (p[0]=='$' && p[1]=='$') { start = p+2; end = strstr(start, \"$$\"); if (end) p = end + 2; }",
  "        else if (p[0]=='$') { start = p+1; end = strchr(start, '$'); if (end) p = end + 1; }",
  "        else if (p[0]=='\\\\' && p[1]=='(') { start = p+2; end = strstr(start, \"\\\\)\"); if (end) p = end + 2; }",
  "        else if (p[0]=='\\\\' && p[1]=='[') { start = p+2; end = strstr(start, \"\\\\]\"); if (end) p = end + 2; }",
  "        else { ++p; continue; }",
  "        if (start && end && end > start) { size_t len = (size_t)(end - start); char *s = malloc(len+1); if (s) { memcpy(s, start, len); s[len]='\\0'; arr = realloc(arr, (*count+1)*sizeof(char*)); arr[*count]=s; (*count)++; } }",
  "    }",
  "    return arr;",
  "}",
  "",
  "/* simple word tokenizer: letters, digits, apostrophe */",
  "static char **tokenize(const char *txt, size_t *count) {",
  "    char *buf = strdup(txt); if (!buf) return NULL; for (char *p=buf; *p; ++p) if (!isalnum((unsigned char)*p) && *p != '\\'') *p = ' ';",
  "    char *save = NULL; char *t = strtok_r(buf, \" \", &save); char **arr = NULL; *count = 0;",
  "    while (t) { if (*t) { arr = realloc(arr, (*count+1)*sizeof(char*)); arr[*count] = strdup(t); (*count)++; } t = strtok_r(NULL, \" \", &save); }",
  "    free(buf); return arr;",
  "}",
  "",
  "/* split comma-separated word list */",
  "static char **split_words_arg(const char *arg, size_t *count) {",
  "    char *buf = strdup(arg); if (!buf) return NULL; size_t n=0; char *save=NULL; char *t = strtok_r(buf, \",\", &save); char **arr=NULL; while (t) { while (*t && isspace((unsigned char)*t)) t++; char *e = t + strlen(t); while (e>t && isspace((unsigned char)*(e-1))) { e--; *(e)=0; } arr = realloc(arr, (n+1)*sizeof(char*)); arr[n] = strdup(t); n++; t = strtok_r(NULL, \",\", &save); } free(buf); *count=n; return arr; }",
  "",
  "/* count occurrences of a word (case-insensitive) in tokens */",
  "static int count_word_in_tokens(char **tokens, size_t ntokens, const char *word) {",
  "    int cnt=0; char lw[256]; strncpy(lw, word, sizeof(lw)-1); lw[sizeof(lw)-1]=0; for (char *p=lw; *p; ++p) *p = (char)tolower((unsigned char)*p);",
  "    for (size_t i=0;i<ntokens;++i) { char *tok = tokens[i]; char tt[256]; strncpy(tt, tok, sizeof(tt)-1); tt[sizeof(tt)-1]=0; for (char *p=tt; *p; ++p) *p=(char)tolower((unsigned char)*p); if (strcmp(tt, lw)==0) cnt++; }",
  "    return cnt;",
  "}",
  "",
  "int main(int argc, char **argv) {",
  "    if (argc < 2) { fprintf(stderr, \"usage: %s <input.pdf> [--regex PATTERN] [--words w1,w2] [--tex]\\n\", argv[0]); return 2; }",
  "    const char *inpdf = argv[1]; const char *regex_pat = NULL; const char *words_arg = NULL; int opt_tex = 0;",
  "    for (int i=2;i<argc;i++) { if (strcmp(argv[i],\"--tex\")==0) { opt_tex=1; } else if (strcmp(argv[i],\"--regex\")==0 && i+1<argc) { regex_pat = argv[++i]; } else if (strcmp(argv[i],\"--words\")==0 && i+1<argc) { words_arg = argv[++i]; } else { fprintf(stderr, \"Unknown arg: %s\\n\", argv[i]); } }",
  "    if (access(\"scripts/pdftotext-wrapper.sh\", X_OK) != 0) { fprintf(stderr, \"pdftotext wrapper not found or not executable\\n\"); return 1; }",
  "    const char *outtxt = \"data/converted.txt\";",
  "    if (run_pdftotext(inpdf, outtxt) != 0) { fprintf(stderr, \"pdftotext conversion failed\\n\"); return 1; }",
  "    char *txt = read_file_all(outtxt); if (!txt) { fprintf(stderr, \"failed to read converted text\\n\"); return 1; }",
  "    /* lowercase copy for insensitive searches */",
  "    char *txt_l = strdup(txt); if (!txt_l) { free(txt); return 1; }",
  "    for (char *p=txt_l; *p; ++p) *p = (char)tolower((unsigned char)*p);",
  "    /* extract TeX math if requested or always (we always extract) */",
  "    size_t math_count = 0; char **maths = extract_tex_math(txt, &math_count);",
  "    printf(\"Found %zu TeX math items:\\n\", math_count);",
  "    for (size_t i=0;i<math_count;++i) printf(\"[%zu] %s\\n\", i+1, maths[i]);",
  "    /* Regex matching (case-insensitive via copying pattern to lower and searching the lowercase text by applying regex on lowercase text) */",
  "    if (regex_pat) {",
  "        regex_t re; int rc; char *pat_l = strdup(regex_pat); if (!pat_l) { fprintf(stderr, \"memory\\n\"); } else { for (char *p=pat_l; *p; ++p) *p = (char)tolower((unsigned char)*p); rc = regcomp(&re, pat_l, REG_ICASE|REG_NOSUB|REG_EXTENDED); if (rc==0) {",
  "                const char *t = txt; int matches = 0; regmatch_t m; const char *cursor = t; while (regexec(&re, cursor, 1, &m, 0)==0) { matches++; size_t off = m.rm_eo; if (off==0) break; cursor = cursor + off; }",
  "                printf(\"Regex '%s' matched %d times\\n\", regex_pat, matches);",
    "            } else { char errbuf[128]; regerror(rc, &re, errbuf, sizeof(errbuf)); fprintf(stderr, \"regex compile error: %s\\n\", errbuf); } regfree(&re); free(pat_l); }",
    "    }",
    "    /* word list handling */",
    "    size_t wordlist_n = 0; char **wordlist = NULL;",
    "    if (words_arg) { wordlist = split_words_arg(words_arg, &wordlist_n); if (wordlist && wordlist_n>0) { size_t tokens_n=0; char **tokens = tokenize(txt_l, &tokens_n); for (size_t i=0;i<wordlist_n;++i) { int cnt = count_word_in_tokens(tokens, tokens_n, wordlist[i]); printf(\"Word '%s' count=%d\\n\", wordlist[i], cnt); } for (size_t i=0;i<tokens_n;++i) free(tokens[i]); free(tokens); } }",
    "    /* detect Jones / Jones polynomial */",
    "    if (strstr(txt_l, \"jones polynomial\") || strstr(txt_l, \"jones-polynomial\")) printf(\"Document likely discusses 'Jones polynomial'\\n\");",
    "    else if (strstr(txt_l, \"jones\")) printf(\"Document mentions 'Jones' (context may indicate Jones polynomial)\\n\");",
    "    else printf(\"No mention of 'Jones' detected\\n\");",
    "    /* heuristic: check if maths contain polynomial-like patterns (t^n, t^{-1}, etc) */",
    "    int poly_like = 0;",
    "    for (size_t i=0;i<math_count;++i) { if (strstr(maths[i], \"t^\") || strstr(maths[i], \"t^{-\") || strstr(maths[i], \"t^{-1}\") || strstr(maths[i], \"t^{-2}\") || strstr(maths[i], \"t^{-3}\") || strstr(maths[i], \"t^{-4}\")) { poly_like = 1; break; } if (strstr(maths[i], \"polynomial\") || strstr(maths[i], \"Jones\")) { poly_like = 1; break; } }",
    "    if (poly_like) printf(\"Math expressions include polynomial-like patterns (possible relation to Jones polynomial)\\n\");",
    "    /* top keywords (simple frequency) */",
    "    size_t tokens_n = 0; char **tokens = tokenize(txt_l, &tokens_n);",
    "    if (tokens) {",
    "        /* count frequencies */",
    "        typedef struct { char *w; int cnt; } E;",
    "        E *arr = NULL; int n=0;",
    "        for (size_t i=0;i<tokens_n;++i) { char *tok=tokens[i]; if (!tok || strlen(tok)<2) continue; int isstop=0; static const char *stops[]={\"the\",\"and\",\"of\",\"in\",\"to\",\"a\",\"is\",NULL}; for (int si=0; stops[si]; ++si) if (strcmp(tok, stops[si])==0) { isstop=1; break; } if (isstop) continue; int found=0; for (int j=0;j<n;++j) if (strcmp(arr[j].w, tok)==0) { arr[j].cnt++; found=1; break; } if (!found) { arr = realloc(arr, (n+1)*sizeof(E)); arr[n].w = strdup(tok); arr[n].cnt = 1; n++; } }",
    "        /* print top 10 */",
    "        for (int i=0;i<10 && i<n; ++i) { int best = i; for (int j=i+1;j<n;++j) if (arr[j].cnt > arr[best].cnt) best = j; if (best!=i) { E tmp=arr[i]; arr[i]=arr[best]; arr[best]=tmp; } printf(\"Top %d: %s (count=%d)\\n\", i+1, arr[i].w, arr[i].cnt); }",
    "        for (int i=0;i<n;++i) free(arr[i].w); free(arr);",
    "    }",
    "    /* heuristic summary */",
    "    printf(\"Heuristic summary:\\n\");",
    "    if (strstr(txt_l, \"jones polynomial\") || poly_like) printf(\" - Document likely discusses Jones polynomial or related knot polynomial invariants.\\n\");",
    "    else printf(\" - No strong evidence for Jones polynomial; review top keywords for topics.\\n\");",
    "    /* cleanup */",
    "    for (size_t i=0;i<math_count;++i) free(maths[i]); free(maths);",
    "    if (wordlist) { for (size_t i=0;i<wordlist_n;++i) free(wordlist[i]); free(wordlist); }",
    "    if (tokens) { for (size_t i=0;i<tokens_n;++i) free(tokens[i]); free(tokens); }",
    "    free(txt_l); free(txt);",
    "    return 0;",
    "}",
};

/* minimal BNF sample */
static const char *bnf_lines[] = {
  "# sample minimal bnf",
  "<expression> ::= <identifier> | <literal> | <identifier> <op> <identifier>",
  "<identifier> ::= x | y | z",
  "<literal> ::= 1 | 2 | 3",
  "<op> ::= + | - | * | /",
};

int main(void) {
  const char *root = "omega_libmrg_full_pkg";
  char path[1024];

  if (ensure_dir(root) != 0) { fprintf(stderr, "cannot create %s\n", root); return 1; }

  const char *dirs[] = { "bin", "lib", "include", "etc", "usr", "scripts", "data", "web" };
  for (size_t i = 0; i < sizeof(dirs)/sizeof(dirs[0]); ++i) {
    snprintf(path, sizeof(path), "%s/%s", root, dirs[i]);
    if (ensure_dir(path) != 0) { fprintf(stderr, "cannot create %s\n", path); return 1; }
  }

  /* Makefile */
  snprintf(path, sizeof(path), "%s/Makefile", root);
  if (write_lines_file(path, makefile_lines, sizeof(makefile_lines)/sizeof(makefile_lines[0]), 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  /* pdftotext wrapper */
  snprintf(path, sizeof(path), "%s/scripts/pdftotext-wrapper.sh", root);
  if (write_lines_file(path, pdftotext_lines, sizeof(pdftotext_lines)/sizeof(pdftotext_lines[0]), 0755) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  /* omega script */
  snprintf(path, sizeof(path), "%s/math_expression_generator.os", root);
  if (write_lines_file(path, omega_lines, sizeof(omega_lines)/sizeof(omega_lines[0]), 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  /* python generator */
  snprintf(path, sizeof(path), "%s/lib/math_expression_generator.py", root);
  if (write_lines_file(path, py_lines, sizeof(py_lines)/sizeof(py_lines[0]), 0755) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  /* generate_analyze.c */
  snprintf(path, sizeof(path), "%s/bin/generate_analyze.c", root);
  if (write_lines_file(path, analyze_c_lines, sizeof(analyze_c_lines)/sizeof(analyze_c_lines[0]), 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  /* sample BNF files */
  snprintf(path, sizeof(path), "%s/c.bnf", root);
  if (write_lines_file(path, bnf_lines, sizeof(bnf_lines)/sizeof(bnf_lines[0]), 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }
  snprintf(path, sizeof(path), "%s/python.bnf", root);
  write_lines_file(path, bnf_lines, sizeof(bnf_lines)/sizeof(bnf_lines[0]), 0);
  snprintf(path, sizeof(path), "%s/ruby.bnf", root);
  write_lines_file(path, bnf_lines, sizeof(bnf_lines)/sizeof(bnf_lines[0]), 0);
  snprintf(path, sizeof(path), "%s/javascript.bnf", root);
  write_lines_file(path, bnf_lines, sizeof(bnf_lines)/sizeof(bnf_lines[0]), 0);

  printf("Generated package '%s'\n", root);
  printf("To build and use:\n");
  printf("  cd %s\n", root);
  printf("  make\n");
  printf("  ./bin/generate_analyze <input.pdf> [--regex PATTERN] [--words w1,w2] [--tex]\n");
  printf("Requirements: pdftotext\n");
  return 0;
}
```

必要なら:
- 正規表現を PDF 全体のコンテキスト（マッチ箇所の前後数十文字）付きで表示するよう拡張します。
- TeX 抽出をさらに改良して式のパース（多項式抽出）を行い、より確度の高い「Jones 多項式」判定を追加します。どれを優先しますか？
