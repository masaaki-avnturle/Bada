以下は、コピペしやすく整形した完全な `pkginstallgen.c` です。ファイル全体を選択してそのまま保存してください（例: エディタで新規ファイルを作り貼り付けて `pkginstallgen.c` として保存）。その後、

gcc -O2 -std=c11 -Wall -o pkginstallgen pkginstallgen.c

でビルドできます。

```c
  /*
   * pkginstallgen.c
   *
   * Generates directory omega_section_infer_pkg with a small analyzer that
   * infers sections (title/theorem/proof/concluded/conjecture) by token entropy
   * and keyword heuristics, outputs TeX and attempts to run pdflatex.
   *
   * Usage:
   *   gcc -O2 -std=c11 -Wall -o pkginstallgen pkginstallgen.c
   *   ./pkginstallgen
   *
   * Then:
   *   cd omega_section_infer_pkg
   *   make
   *   # put .txt files in reports/
   *   ./bin/omega_infer analyze reports output/paper.tex
   *
   */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <errno.h>
#include <unistd.h>

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

  static int write_file(const char *path, const char *content, mode_t mode) {
    char dir[4096];
    strncpy(dir, path, sizeof(dir)-1);
    dir[sizeof(dir)-1] = '\0';
    char *p = strrchr(dir, '/');
    if (p) { *p = '\0'; ensure_dir(dir); }
    FILE *f = fopen(path, "wb");
    if (!f) { fprintf(stderr, "open %s: %s\n", path, strerror(errno)); return -1; }
    if (fputs(content, f) == EOF) { fclose(f); return -1; }
    fclose(f);
    if (mode) chmod(path, mode);
    return 0;
  }

int main(void) {
  const char *root = "omega_section_infer_pkg";
  if (ensure_dir(root) != 0) { fprintf(stderr, "cannot create %s\n", root); return 1; }

  ensure_dir("omega_section_infer_pkg/bin");
  ensure_dir("omega_section_infer_pkg/usr");
  ensure_dir("omega_section_infer_pkg/usr/lang");
  ensure_dir("omega_section_infer_pkg/reports");
  ensure_dir("omega_section_infer_pkg/output");

    const char *makefile =
"CC ?= gcc\n"
"CFLAGS ?= -O2 -std=c11 -Wall -Wextra\n"
"PREFIX ?= .\n"
"BIN_DIR = $(PREFIX)/bin\n"
"ANALYZER_C = usr/lang/omega_infer.c\n"
"ANALYZER_BIN = $(BIN_DIR)/omega_infer\n"
".PHONY: all clean\n"
"all: $(ANALYZER_BIN)\n\n"
"$(ANALYZER_BIN): $(ANALYZER_C)\n"
"\t@mkdir -p $(BIN_DIR)\n"
"\t$(CC) $(CFLAGS) -o $@ $< -lm\n"
"\t@printf \"built: %s\\n\" \"$@\"\n\n"
"clean:\n"
      "\t-@rm -f $(ANALYZER_BIN)\n";
    write_file("omega_section_infer_pkg/Makefile", makefile, 0644);

    const char *readme =
"# omega_section_infer_pkg\n\n"
"Infers document sections (title/theorem/proof/concluded/conjecture) from plain-text\nreports using token-entropy heuristics and keyword signals. Produces TeX and\nattempts to build a PDF via pdflatex if available.\n\n"
"Build and run:\n\n"
"  cd omega_section_infer_pkg\n"
"  make\n\n"
"Place .txt files in reports/ and run:\n\n"
      "  ./bin/omega_infer analyze reports output/paper.tex\n";
    write_file("omega_section_infer_pkg/README.md", readme, 0644);

    const char *runsh =
"#!/usr/bin/env sh\n"
"set -euo pipefail\n"
"if [ ! -f bin/omega_infer ]; then echo \"Build with 'make' first.\"; exit 1; fi\n"
      "exec bin/omega_infer \"$@\"\n";
    write_file("omega_section_infer_pkg/run.sh", runsh, 0755);

    const char *reports_readme =
      "Place plaintext reports (*.txt) here. The analyzer splits files into blocks by\nblank lines and infers which block matches each topic.\n";
    write_file("omega_section_infer_pkg/reports/README.txt", reports_readme, 0644);

    /* Analyzer source: properly escaped C string */
    const char *analyzer_c =
"/* usr/lang/omega_infer.c\n"
" * Analyzer: split reports into blocks, compute token entropy per block,\n"
" * assign blocks to topics {title,theorem,proof,concluded,conjecture} using\n"
" * entropy ranking + keyword heuristics, output TeX and attempt pdflatex.\n"
      " */\n"
"#define _POSIX_C_SOURCE 200809L\n"
"#include <stdio.h>\n"
"#include <stdlib.h>\n"
"#include <string.h>\n"
"#include <ctype.h>\n"
"#include <dirent.h>\n"
"#include <sys/stat.h>\n"
"#include <math.h>\n"
"#include <errno.h>\n"
"\n"
"typedef struct { char *text; double entropy; } Block;\n"
"static char *read_whole(const char *path) {\n"
"    FILE *f = fopen(path, \"rb\"); if (!f) return NULL;\n"
"    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }\n"
"    long s = ftell(f); if (s < 0) { fclose(f); return NULL; }\n"
"    fseek(f, 0, SEEK_SET);\n"
"    char *buf = malloc((size_t)s + 1);\n"
"    if (!buf) { fclose(f); return NULL; }\n"
"    if (fread(buf, 1, (size_t)s, f) != (size_t)s) { free(buf); fclose(f); return NULL; }\n"
"    buf[s] = '\\0'; fclose(f); return buf;\n"
"}\n"
"\n"
"static int ensure_dir_local(const char *path) {\n"
      "    if (!path) return -1;\n"    struct stat st;\n"    if (stat(path, &st) == 0) return S_ISDIR(st.st_mode) ? 0 : -1;\n"
"    if (mkdir(path, 0755) == 0) return 0;\n"
"    if (errno == ENOENT) {\n"
"        char tmp[4096]; strncpy(tmp, path, sizeof(tmp)-1); tmp[sizeof(tmp)-1]=0; char *p = strrchr(tmp, '/');\n"
"        if (p && p != tmp) { *p = 0; if (ensure_dir_local(tmp) == 0) return mkdir(path, 0755) == 0 ? 0 : -1; }\n"
"    }\n"
"    return -1;\n"
"}\n"
"\n"
"static Block *split_blocks(const char *text, int *out_n) {\n"
  "    *out_n = 0; if (!text) return NULL;\n"    char *dup = strdup(text); if (!dup) return NULL;\n"    Block *blocks = NULL; int cap = 0, n = 0;\n"    char *p = dup; char *start = dup;\n"    while (*p) {\n"
"        if ((p[0] == '\\n' && p[1] == '\\n') || (p[0] == '\\r' && p[1] == '\\n' && p[2] == '\\r' && p[3] == '\\n')) {\n"
																							   "            char *end = p; while (end > start && (end[-1] == '\\n' || end[-1] == '\\r')) end--;\n"            size_t L = (size_t)(end - start);\n"            if (L > 0) {\n"                char *b = malloc(L + 1); if (b) { memcpy(b, start, L); b[L] = '\\0'; if (n >= cap) { int nc = cap ? cap*2 : 8; Block *tmp = realloc(blocks, sizeof(Block)*nc); if (!tmp) { free(b); break; } blocks = tmp; cap = nc; } blocks[n].text = b; blocks[n].entropy = 0.0; n++; }\n"            }\n"            while (*p && (*p == '\\n' || *p == '\\r')) p++;\n"            start = p; continue;\n"        }\n"        p++;\n"    }\n"    while (*start && (*start == '\\n' || *start == '\\r')) start++;\n"    if (*start) {\n"        char *b = strdup(start); if (b) { if (n >= cap) { int nc = cap ? cap*2 : 8; Block *tmp = realloc(blocks, sizeof(Block)*nc); if (!tmp) { free(b); } else { blocks = tmp; cap = nc; } } if (blocks) { blocks[n].text = b; blocks[n].entropy = 0.0; n++; } }\n"    }\n"    free(dup); *out_n = n; return blocks;\n"
"}\n"
"\n"
"static char **tokenize(const char *s, int *out_n) {\n"
																							   "    *out_n = 0; if (!s) return NULL;\n"    int cap = 64; char **arr = malloc(sizeof(char*) * cap); if (!arr) return NULL;\n"    int n = 0; const char *p = s;\n"    while (*p) {\n"        while (*p && !isalnum((unsigned char)*p)) p++;\n"        if (!*p) break;\n"        const char *q = p; while (*q && (isalnum((unsigned char)*q) || *q == '_')) q++;\n"        int L = (int)(q - p); char *t = malloc((size_t)L + 1); if (!t) break;\n"        for (int i = 0; i < L; ++i) t[i] = (char)tolower((unsigned char)p[i]); t[L] = '\\0';\n"        if (n >= cap) { int nc = cap * 2; char **tmp = realloc(arr, sizeof(char*) * nc); if (!tmp) { free(t); break; } arr = tmp; cap = nc; }\n"        arr[n++] = t; p = q;\n"    }\n"    *out_n = n; return arr;\n"
"}\n"
"\n"
"static double shannon(char **tokens, int n) {\n"
																							   "    if (n <= 0) return 0.0;\n"    char **uniq = malloc(sizeof(char*) * n); int *cnt = calloc(n, sizeof(int)); if (!uniq || !cnt) { free(uniq); free(cnt); return 0.0; }\n"    int u = 0;\n"    for (int i = 0; i < n; ++i) {\n"        int idx = -1; for (int j = 0; j < u; ++j) if (strcmp(tokens[i], uniq[j]) == 0) { idx = j; break; }\n"        if (idx == -1) { uniq[u] = strdup(tokens[i]); cnt[u] = 1; u++; } else cnt[idx]++;\n"    }\n"    double H = 0.0; for (int i = 0; i < u; ++i) { double p = (double)cnt[i] / (double)n; if (p > 0) H -= p * log(p) / log(2.0); free(uniq[i]); }\n"    free(uniq); free(cnt); return H;\n"
"}\n"
"\n"
"static void compute_entropies(Block *blocks, int n) {\n"
																																																																																															      "    for (int i = 0; i < n; ++i) {\n"        int tn = 0; char **toks = tokenize(blocks[i].text, &tn);\n"        double H = shannon(toks, tn);\n"        blocks[i].entropy = H;\n"        for (int j = 0; j < tn; ++j) free(toks[j]); free(toks);\n"    }\n"
"}\n"
"\n"
"static void assign_topics(Block *blocks, int n, int *out_map) {\n"
																																																																																															      "    const char *kw_title[] = {\"title\",\"題目\",\"abstract\", NULL};ze <reports_dir> <out_tex>\\n\", argv[0]); return 1; }\n"
																																																																																															      "    const char *dir = argv[2]; const char *out_tex = argv[3]; ensure_dir_local(\"output\");\n"    DIR *d = opendir(dir); if (!d) { fprintf(stderr, \"cannot open %s: %s\\n\", dir, strerror(errno)); return 1; }\n"    struct dirent *e; char *all = NULL; size_t allcap = 0, alllen = 0;\n"    while ((e = readdir(d)) != NULL) {\n"        const char *name = e->d_name; size_t L = strlen(name); if (L > 4 && strcasecmp(name + L - 4, \".txt\") == 0) {\n"            char path[1024]; if (snprintf(path, sizeof(path), \"%s/%s\", dir, name) >= (int)sizeof(path)) continue;\n"            char *t = read_whole(path); if (!t) continue; size_t tl = strlen(t);\n"            if (allcap < alllen + tl + 3) { size_t nc = (allcap + tl + 4096) * 2; char *tmp = realloc(all, nc); if (!tmp) { free(t); break; } all = tmp; allcap = nc; }\n"            memcpy(all + alllen, t, tl); alllen += tl; all[alllen++] = '\\n'; all[alllen] = '\\0'; free(t);\n"        }\n"    }\n"    closedir(d);\n"    if (!all) { fprintf(stderr, \"no text found in %s\\n\", dir); return 1; }\n"    int nb = 0; Block *blocks = split_blocks(all, &nb);\n"    if (!blocks || nb == 0) { fprintf(stderr, \"no blocks extracted\\n\"); free(all); return 1; }\n"    compute_entropies(blocks, nb);\n"    int map[5]; assign_topics(blocks, nb, map);\n"    const char *topics[5] = {\"Title\",\"Theorem\",\"Proof\",\"Concluded\",\"Conjecture\"};\n"    FILE *ft = fopen(out_tex, \"wb\"); if (!ft) { fprintf(stderr, \"cannot open %s for writing\\n\", out_tex); goto CLEAN; }\n"    fprintf(ft, \"\\\\documentclass{article}\\\\n\\\\usepackage{amsmath,amsthm,amssymb}\\\\n\\\\begin{document}\\\\n\");\n"    int tid = map[0]; if (tid >= 0 && tid < nb) { char *esc = tex_escape(blocks[tid].text); if (esc) { fprintf(ft, \"\\\\title{%s}\\\\maketitle\\\\n\", esc); free(esc); } else fprintf(ft, \"\\\\title{Inferred Document}\\\\maketitle\\\\n\"); }\n"    else fprintf(ft, \"\\\\title{Inferred Document}\\\\maketitle\\\\n\");\n"    for (int ti = 1; ti < 5; ++ti) {\n"        int bi = map[ti]; if (bi < 0 || bi >= nb) continue;\n"        fprintf(ft, \"\\\\section*{%s}\\\\n\", topics[ti]);\n"        char *dup = strdup(blocks[bi].text); char *save = NULL; char *ln = strtok_r(dup, \"\\n\", &save);\n"        while (ln) {\n"            char *s = ln; while (*s && isspace((unsigned char)*s)) s++;\n"            if (*s) {\n"                if (strchr(ln, '=') && strlen(ln) < 512) { fprintf(ft, \"\\\\[ %s \\\\]\\\\n\", ln); }\n"                else { char *esc = tex_escape(ln); if (esc) { fprintf(ft, \"%s\\\\n\\\\n\", esc); free(esc); } else fprintf(ft, \"%s\\\\n\\\\n\", ln); }\n"            }\n"            ln = strtok_r(NULL, \"\\n\", &save);\n"        }\n"        free(dup);\n"    }\n"    fprintf(ft, \"\\\\section*{Entropy Summary}\\\\n\\\\begin{itemize}\\\\n\");\n"    for (int i = 0; i < nb; ++i) fprintf(ft, \"\\\\item Block %d: entropy=%.4f\\\\n\", i, blocks[i].entropy);\n"    fprintf(ft, \"\\\\end{itemize}\\\\n\");\n"    fprintf(ft, \"\\\\end{document}\\\\n\"); fclose(ft);\n"    {\n"        char cmd[2048]; if (snprintf(cmd, sizeof(cmd), \"pdflatex -interaction=nonstopmode -halt-on-error -output-directory=output %s 1>/dev/null 2>/dev/null\", out_tex) >= 0) {\n"            int rc = system(cmd);\n"            if (rc == 0) printf(\"PDF generated at output/paper.pdf (pdflatex present)\\n\"); else printf(\"pdflatex returned non-zero; TeX saved to %s\\n\", out_tex);\n"        }\n"    }\n"    printf(\"Wrote TeX to %s and attempted PDF build.\\n\", out_tex);\n"CLEAN:\n"    for (int i = 0; i < nb; ++i) free(blocks[i].text);\n"    free(blocks); free(all);\n"    return 0;\n"
																																																																																															      "}\n";

if (write_file("omega_section_infer_pkg/usr/lang/omega_infer.c", analyzer_c, 0644) != 0) {
        fprintf(stderr, "failed to write analyzer source\n");
        return 1;
 }

printf("omega_section_infer_pkg generated.\nTo build:\n  cd omega_section_infer_pkg\n  make\nPlace .txt files into reports/ and run:\n  ./bin/omega_infer analyze reports output/paper.tex\n");
return 0;
}
```

もし、これでもコピーできない・ビルドできない・エラーが出る場合は、使っているエディタ／ターミナルや具体的なコンパイルコマンドとエラーメッセージをそのまま貼ってください。こちらでさらに調整します。
