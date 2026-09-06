以下は、要求どおり「pkginstallgen.c」—— 実行するとカレントに `omega_demo/` パッケージ一式を生成するプログラムです。生成物はビルド可能で、簡易解析コマンド `bin/omega_demo`（ソース: `usr/lang/omega_demo.c`）と Makefile、README、run スクリプト、サンプル `reports/` ディレクトリを含みます。生成される `omega_demo` はレポート中の数式（'=' を含む行）を抽出し、簡単なトークン分解・候補生成・SymPy 用検証スクリプトの出力を行います。安全なバッファ処理・NULL チェック・ディレクトリ作成を行うよう注意して実装しています。

使い方（短く）
1. 保存: `pkginstallgen.c`
2. コンパイル: gcc -O2 -std=c11 -Wall -o pkginstallgen pkginstallgen.c
  3. 実行: ./pkginstallgen
  4. 生成ディレクトリへ移動してビルド:
   cd omega_demo
   make
     5. 報告ファイルを `omega_demo/reports/` に置き、実行:
   ./bin/omega_demo analyze reports output/paper.tex
     6. （オプション）検証: python3 output/verifier.py （sympy 必須）

以下が完全ソースです。ファイル全体を保存してコンパイルしてください。

```c
  /*
   * pkginstallgen.c
   *
   * Generate a demo package "omega_demo" containing:
   *  - bin/omega_demo (built from usr/lang/omega_demo.c)
   *  - Makefile, README.md, run.sh
   *  - reports/ (sample README)
   *  - usr/lang/omega_demo.c: simple analyzer extracting equations, producing LaTeX/JSON and verifier.py
   *
   * Build and run:
   *   gcc -O2 -std=c11 -Wall -o pkginstallgen pkginstallgen.c
   *   ./pkginstallgen
   *   cd omega_demo
   *   make
   *   # put .txt files in reports/
   *   ./bin/omega_demo analyze reports output/paper.tex
   *
   * Notes:
   *  - verifier.py requires python3 and sympy to run.
   *  - Generated analyzer is intentionally simple and safe (no shell exec).
   */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <errno.h>

  static int ensure_dir(const char *path) {
  if (!path) return -1;
  struct stat st;
  if (stat(path, &st) == 0) return S_ISDIR(st.st_mode) ? 0 : -1;
  if (mkdir(path, 0755) == 0) return 0;
  if (errno == ENOENT) {
    char tmp[4096];
    strncpy(tmp, path, sizeof(tmp)-1);
    tmp[sizeof(tmp)-1] = '\0';
    char *p = strrchr(tmp, '/');
    if (p && p != tmp) {
      *p = '\0';
      if (ensure_dir(tmp) == 0) return mkdir(path, 0755) == 0 ? 0 : -1;
    }
  }
  return -1;
}

static int write_file(const char *path, const char *content, int mode) {
  char dir[4096];
  strncpy(dir, path, sizeof(dir)-1);
  dir[sizeof(dir)-1] = '\0';
  char *p = strrchr(dir, '/');
  if (p) { *p = '\0'; ensure_dir(dir); }
  FILE *f = fopen(path, "wb");
  if (!f) { fprintf(stderr, "open %s: %s\n", path, strerror(errno)); return -1; }
  if (fputs(content, f) == EOF) { fclose(f); return -1; }
  fclose(f);
  if (mode) chmod(path, (mode_t)mode);
  return 0;
}

int main(void) {
  const char *root = "omega_demo";
  if (ensure_dir(root) != 0) { fprintf(stderr, "cannot create %s\n", root); return 1; }

  ensure_dir("omega_demo/bin");
  ensure_dir("omega_demo/usr");
  ensure_dir("omega_demo/usr/lang");
  ensure_dir("omega_demo/reports");
  ensure_dir("omega_demo/output");

    const char *makefile =
"CC ?= gcc\n"
"CFLAGS ?= -O2 -std=c11 -Wall -Wextra\n"
"PREFIX ?= .\n"
"BIN_DIR = $(PREFIX)/bin\n"
"DEMO_C = usr/lang/omega_demo.c\n"
"DEMO_BIN = $(BIN_DIR)/omega_demo\n"
".PHONY: all clean\n"
"all: $(DEMO_BIN)\n\n"
"$(DEMO_BIN): $(DEMO_C)\n"
"\t@mkdir -p $(BIN_DIR)\n"
"\t$(CC) $(CFLAGS) -o $@ $< -lm\n"
"\t@printf \"built: %s\\n\" \"$@\"\n\n"
"clean:\n"
      "\t-@rm -f $(DEMO_BIN)\n";
    write_file("omega_demo/Makefile", makefile, 0644);

    const char *readme =
"# omega_demo\n\n"
"Demo package that provides a simple analyzer `omega_demo`.\n\n"
"Build and run:\n\n"
"  cd omega_demo\n"
"  make\n\n"
"Place plain-text reports (.txt) in `reports/`. Run the analyzer:\n\n"
"  ./bin/omega_demo analyze reports output/paper.tex\n\n"
"Optional: run the generated verifier script with Python3 + sympy:\n\n"
      "  python3 output/verifier.py\n";
    write_file("omega_demo/README.md", readme, 0644);

    const char *runsh =
"#!/usr/bin/env sh\n"
"set -euo pipefail\n"
"if [ ! -f bin/omega_demo ]; then echo \"Build with 'make' first.\"; exit 1; fi\n"
      "exec bin/omega_demo \"$@\"\n";
    write_file("omega_demo/run.sh", runsh, 0755);

    const char *reports_readme =
      "Place .txt reports here. Lines containing '=' are treated as equations.\nExample:\n  Theorem: ...\n  a + b = c\n";
    write_file("omega_demo/reports/README.txt", reports_readme, 0644);

    /* usr/lang/omega_demo.c: simple analyzer */
    const char *demo_c =
"/* usr/lang/omega_demo.c\n"
" * Simple analyzer for demo: extract lines with '=', collect equations,\n"
" * produce a LaTeX skeleton and a Python SymPy verifier script.\n" 
      " */\n"
"#define _POSIX_C_SOURCE 200809L\n"
"#include <stdio.h>\n"
"#include <stdlib.h>\n"#include <string.h>\n"
"#include <ctype.h>\n"
"#include <dirent.h>\n"
"#include <sys/stat.h>\n"
"#include <errno.h>\n"
"\n"
"static char *read_whole(const char *path) {\n"
"    FILE *f = fopen(path, \"rb\"); if (!f) return NULL;\n"
"    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }\n"
"    long s = ftell(f); if (s < 0) { fclose(f); return NULL; }\n"
"    fseek(f, 0, SEEK_SET);\n"
"    char *buf = malloc((size_t)s + 1); if (!buf) { fclose(f); return NULL; }\n"
"    if (fread(buf, 1, (size_t)s, f) != (size_t)s) { free(buf); fclose(f); return NULL; }\n"
"    buf[s] = '\\0'; fclose(f); return buf;\n"
"}\n"
"\n"
"static int ensure_dir(const char *path) {\n"
"    if (!path) return -1; struct stat st;\n"
"    if (stat(path, &st) == 0) return S_ISDIR(st.st_mode) ? 0 : -1;\n"
"    if (mkdir(path, 0755) == 0) return 0;\n" 
"    char tmp[4096]; strncpy(tmp, path, sizeof(tmp)-1); tmp[sizeof(tmp)-1]=0; char *p = strrchr(tmp, '/');\n"
"    if (p) { *p = 0; if (ensure_dir(tmp) == 0) return mkdir(path,0755) == 0 ? 0 : -1; }\n"
"    return -1;\n"
"}\n"
"\n"
"static int is_regular_file(const char *dir, const char *name) {\n"
"    if (!dir || !name) return 0;\n" 
"    char path[1024]; if (snprintf(path, sizeof(path), \"%s/%s\", dir, name) >= (int)sizeof(path)) return 0;\n"
"    struct stat st; if (stat(path, &st) != 0) return 0; return S_ISREG(st.st_mode);\n"
"}\n"
"\n"
      "/* trim */\n"
"static void trim_copy(const char *s, char *out, size_t osz) {\n"
"    if (!s || !out || osz==0) return; const char *a = s; while (*a && isspace((unsigned char)*a)) a++; const char *b = s + strlen(s); while (b > a && isspace((unsigned char)*(b-1))) b--; size_t L = (size_t)(b - a); if (L >= osz) L = osz - 1; memcpy(out, a, L); out[L]='\\0';\n"
"}\n"
"\n"
      "/* collect equation lines from reports */\n"
"static int collect_equations(const char *dir, char ***out_eqs, int *out_n) {\n"
"    *out_eqs = NULL; *out_n = 0; DIR *d = opendir(dir); if (!d) return -1; struct dirent *e;\n"
"    while ((e = readdir(d)) != NULL) {\n"
"        const char *name = e->d_name; if (!is_regular_file(dir, name)) continue; size_t L = strlen(name); if (L>4 && strcasecmp(name+L-4, \".txt\")==0) {\n"
"            char path[1024]; if (snprintf(path, sizeof(path), \"%s/%s\", dir, name) >= (int)sizeof(path)) continue;\n"
      "            char *txt = read_whole(path); if (!txt) continue;\n"            char *save = NULL; char *ln = strtok_r(txt, \"\\n\", &save);\n"
"            while (ln) {\n"
"                const char *s = ln; while (*s && isspace((unsigned char)*s)) s++; if (*s && strchr(ln, '=')) {\n"
"                    char *dup = strdup(ln); if (!dup) break; char **tmp = realloc(*out_eqs, sizeof(char*) * ((*out_n) + 1)); if (!tmp) { free(dup); break; }\n"
  "                    *out_eqs = tmp; (*out_eqs)[(*out_n)++] = dup;\n"                }\n"
"                ln = strtok_r(NULL, \"\\n\", &save);\n"
"            }\n"
"            free(txt);\n"
"        }\n"
"    }\n"
"    closedir(d); return 0;\n"
"}\n"
"\n"
"/* naive split into lhs/rhs */\n"
"static int split_eq(const char *s, char *lhs, size_t lsz, char *rhs, size_t rsz) {\n"
"    const char *eq = strchr(s, '='); if (!eq) return 0; trim_copy(s, lhs, lsz);\n"
"    const char *c = eq + 1; while (*c && isspace((unsigned char)*c)) c++; size_t R = strlen(c); if (R >= rsz) R = rsz -1; strncpy(rhs, c, R); rhs[R] = '\\0'; return 1;\n"
"}\n"
"\n"
"/* generate a very small verifier.py (sympy) */\n"
"static int gen_verifier_py(const char *path, char **eqs, int n) {\n"
  "    if (!path) return -1; ensure_dir(\"output\"); FILE *f = fopen(path, \"wb\"); if (!f) return -1;\n"    fprintf(f, \"#!/usr/bin/env python3\\n\");\n"    fprintf(f, \"import json,random\\nfrom sympy import sympify,simplify,N\\nres={'{'}'accepted':[], 'rejected':[]}{'}'}\\n\\n\");\n"    for (int i=0;i<n;i++) {\n"        char lhs[512]={0}, rhs[512]={0}; if (!split_eq(eqs[i], lhs, sizeof(lhs), rhs, sizeof(rhs))) continue;\n"        /* escape */\n"        char esc[1024]; size_t eo=0; for (const char *p=eqs[i]; *p && eo+2<sizeof(esc); ++p) { if (*p=='\\\\') { esc[eo++]='\\\\'; esc[eo++]='\\\\'; } else if (*p=='\"') { esc[eo++]='\\\\'; esc[eo++]='\"'; } else if (*p=='\\n' || *p=='\\r') { } else esc[eo++]=*p; } esc[eo]=0;\n"        fprintf(f, \"try:\\n\");\n"        fprintf(f, \"    L = sympify(r\\\"\\\"\\\"%s\\\"\\\"\\\")\\n\", lhs);\n"        fprintf(f, \"    R = sympify(r\\\"\\\"\\\"%s\\\"\\\"\\\")\\n\", rhs);\n"        fprintf(f, \"    diff = simplify(L - R)\\n\");\n"        fprintf(f, \"    symbolic_ok = diff == 0\\n\");\n"        fprintf(f, \"    numeric_ok = True\\n    checks = []\\n\");\n"        fprintf(f, \"    for _ in range(5):\\n        vals = {}\\n        for s in list(diff.free_symbols): vals[str(s)] = random.uniform(0.1, 2.0)\\n        try:\\n            v = N(diff.subs({k: vals[k] for k in vals}), 15)\\n            ok = abs(float(v.evalf())) < 1e-6\\n        except Exception as e:\\n            ok = False; v = str(e)\\n        checks.append({'vals': vals, 'value': str(v), 'ok': ok})\\n        if not ok: numeric_ok = False\\n\");\n"        fprintf(f, \"    if symbolic_ok or numeric_ok:\\n        res['accepted'].append({'equation': \\\"%s\\\", 'symbolic': str(diff), 'numeric_ok': numeric_ok, 'checks': checks})\\n    else:\\n        res['rejected'].append({'equation': \\\"%s\\\", 'symbolic': str(diff), 'numeric_ok': numeric_ok, 'checks': checks})\\n\", esc, esc);\n"        fprintf(f, \"except Exception as e:\\n    res['rejected'].append({'equation': \\\"%s\\\", 'error': str(e)})\\n\", esc);\n"    }\n"    fprintf(f, \"print(json.dumps(res, ensure_ascii=False, indent=2))\\n\"); fclose(f); chmod(path, 0755); return 0;\n"
"}\n"
"\n"
"int main(int argc, char **argv) {\n"
"    if (argc < 4 || strcmp(argv[1], \"analyze\") != 0) { fprintf(stderr, \"usage: %s analyze <reports_dir> <out_tex>\\n\", argv[0]); return 1; }\n"
"    const char *dir = argv[2]; const char *out_tex = argv[3]; ensure_dir(\"output\");\n"
"    char **eqs = NULL; int eqn = 0; if (collect_equations(dir, &eqs, &eqn) != 0) { fprintf(stderr, \"failed to collect equations\\n\"); return 1; }\n"
"    if (eqn == 0) { fprintf(stderr, \"no equations found in %s\\n\", dir); return 1; }\n"
"    /* write LaTeX skeleton */\n"
											 "    FILE *ft = fopen(out_tex, \"wb\"); if (!ft) { fprintf(stderr, \"cannot write %s\\n\", out_tex); goto CLEAN; }\n"    fprintf(ft, \"\\\\documentclass{article}\\\\n\\\\usepackage{amsmath,amsthm,amssymb,verbatim}\\\\n\\\\begin{document}\\\\n\");\n"    fprintf(ft, \"\\\\title{omega_demo: Extracted Equations}\\\\maketitle\\\\n\");\n"    fprintf(ft, \"\\\\section*{Equations}\\\\n\\\\begin{enumerate}\\\\n\");\n"    for (int i=0;i<eqn;i++) fprintf(ft, \"\\\\item \\texttt{%s}\\\\n\", eqs[i]);\n"    fprintf(ft, \"\\\\end{enumerate}\\\\n\\\\section*{Verification}\\\\nRun 'python3 output/verifier.py' to check symbolic/numeric consistency.\\\\n\");\n"    fprintf(ft, \"\\\\end{document}\\\\n\"); fclose(ft);\n"
"    /* generate verifier.py */\n"
"    gen_verifier_py(\"output/verifier.py\", eqs, eqn);\n"
																																																																																												  "    /* JSON summary */\n"
"    FILE *fj = fopen(\"output/summary.json\",\"wb\"); if (fj) {\n"        fprintf(fj, \"{\\n  \\\"equation_count\\\": %d,\\n  \\\"equations\\\": [\\n\", eqn);\n"        for (int i=0;i<eqn;i++) fprintf(fj, \"    \\\"%s\\\"%s\\n\", eqs[i], (i+1<eqn)?\",\":\"\");\n"        fprintf(fj, \"  ]\\n}\\n\"); fclose(fj);\n"    }\n"
"    printf(\"Wrote %s, output/verifier.py, output/summary.json\\n\", out_tex);\n"
"CLEAN:\n"    for (int i=0;i<eqn;i++) free(eqs[i]); free(eqs);\n"    return 0;\n"
"}\n";

write_file("omega_demo/usr/lang/omega_demo.c", demo_c, 0644);

printf("omega_demo package generated.\nTo build:\n  cd omega_demo\n  make\nPlace .txt files in reports/ and run:\n  ./bin/omega_demo analyze reports output/paper.tex\n");

return 0;
}
```

必要であれば、生成される `usr/lang/omega_demo.c` の機能拡張（より高度な式分解、LaTeX での整形改善、検証結果を LaTeX に埋め込む等）や、verifier.py の強化（AST 正規化・追加テスト）を実装します。どの部分を重点的に改善したいか教えてください。
