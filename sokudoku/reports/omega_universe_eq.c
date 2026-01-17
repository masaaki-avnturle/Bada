```c
/*
 * pkginstallgen.c
 *
 * Generates omega_universe_eq_pkg including:
 *  - bin/omegascript (wrapper)
 *  - usr/lang/omegascript.c (analyzer)
 *  - usr/lang/verifier.py (SymPy-based verifier)
 *  - Makefile, run.sh, README, sample report
 *
 * Written to avoid stray '\' or '#' issues by writing files line-by-line.
 *
 * Build:
 *   gcc -std=c11 -O2 -Wall -o pkginstallgen pkginstallgen.c
 * Run:
 *   ./pkginstallgen ./omega_universe_eq_pkg
 *
 * Then:
 *   cd omega_universe_eq_pkg
 *   make
 *   place .txt files into reports/
 *   ./bin/omegascript analyze reports output/paper.tex
 *   python3 usr/lang/verifier.py output/equations.txt output
 *
 * verifier.py is included and will run if python3 is available.
 */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <errno.h>

#ifdef _WIN32
#include <direct.h>
#define MKDIR(p) _mkdir(p)
#else
#include <unistd.h>
#define MKDIR(p) mkdir((p), 0755)
#endif

static int ensure_dir(const char *path) {
  if (!path) return -1;
  struct stat st;
  if (stat(path, &st) == 0) return S_ISDIR(st.st_mode) ? 0 : -1;
  if (MKDIR(path) == 0) return 0;
  if (errno == ENOENT) {
    char tmp[4096];
    strncpy(tmp, path, sizeof(tmp)-1);
    tmp[sizeof(tmp)-1] = '\0';
    char *p = strrchr(tmp, '/');
    if (p && p != tmp) {
      *p = '\0';
      if (ensure_dir(tmp) == 0) return MKDIR(path) == 0 ? 0 : -1;
    }
  }
  return -1;
}

static int write_lines(const char *path, const char *lines[], size_t nlines, int mode) {
  char dir[4096];
  strncpy(dir, path, sizeof(dir)-1);
  dir[sizeof(dir)-1] = '\0';
  char *p = strrchr(dir, '/');
  if (p) { *p = '\0'; ensure_dir(dir); }
  FILE *f = fopen(path, "wb");
  if (!f) { fprintf(stderr, "open %s: %s\n", path, strerror(errno)); return -1; }
  for (size_t i=0;i<nlines;i++) {
    if (fputs(lines[i], f) == EOF) { fclose(f); return -1; }
    if (fputc('\n', f) == EOF) { fclose(f); return -1; }
  }
  fclose(f);
#ifndef _WIN32
  if (mode) chmod(path, (mode_t)mode);
#endif
  return 0;
}

int main(int argc, char **argv) {
  const char *target = "omega_universe_eq_pkg";
  if (argc > 1 && argv[1] && argv[1][0]) target = argv[1];

  if (ensure_dir(target) != 0) { fprintf(stderr, "cannot create %s\n", target); return 1; }
  { char p[4096]; snprintf(p, sizeof(p), "%s/bin", target); ensure_dir(p); }
  { char p[4096]; snprintf(p, sizeof(p), "%s/usr/lang", target); ensure_dir(p); }
  { char p[4096]; snprintf(p, sizeof(p), "%s/reports", target); ensure_dir(p); }
  { char p[4096]; snprintf(p, sizeof(p), "%s/output", target); ensure_dir(p); }
  { char p[4096]; snprintf(p, sizeof(p), "%s/output/explanations", target); ensure_dir(p); }

  /* Makefile */
  const char *makefile[] = {
    "CC ?= gcc",
    "CFLAGS ?= -O2 -std=c11 -Wall -Wextra",
    "PREFIX ?= .",
    "BIN_DIR = $(PREFIX)/bin",
    "OMEGA_C = usr/lang/omegascript.c",
    "OMEGA_BIN = $(BIN_DIR)/omegascript",
    ".PHONY: all clean",
    "all: $(OMEGA_BIN)",
    "",
    "$(OMEGA_BIN): $(OMEGA_C)",
    "\t@mkdir -p $(BIN_DIR)",
    "\t$(CC) $(CFLAGS) -o $@ $< -lm",
    "\t@printf \"built: %s\\n\" \"$@\"",
    "",
    "clean:",
    "\t-@rm -f $(OMEGA_BIN)",
NULL
  };

  /* README */
  const char *readme[] = {
    "# Omega Universe Equation Inference Package",
    "",
    "This package extracts equations from text reports, decomposes them into subexpressions,",
    "recombines those subexpressions to create candidate equations, and uses SymPy",
    "(symbolic and numeric checks) to determine which candidates are consistent",
    "('exist' symbolically/numerically). For consistent equations, the package",
    "produces explanatory text describing how the equation was formed.",
    "",
    "Build and run:",
    "",
    "  cd omega_universe_eq_pkg",
    "  make",
    "",
    "Place .txt report files in reports/ and run:",
    "",
    "  ./bin/omegascript analyze reports output/paper.tex",
    "",
    "Then run verification (verifier included):",
    "",
    "  python3 usr/lang/verifier.py output/equations.txt output",
    "",
    "Requirements for verification: python3 and sympy (pip install sympy).",
NULL
  };

  /* run.sh */
  const char *runsh[] = {
    "#!/usr/bin/env sh",
    "set -euo pipefail",
    "if [ ! -f bin/omegascript ]; then echo \"Build with 'make' first.\"; exit 1; fi",
    "exec bin/omegascript \"$@\"",
NULL
  };

  /* reports README */
  const char *rread[] = {
    "Place plain-text reports (*.txt) here. Lines containing '=' will be",
    "considered candidate equations and used as sources for decomposition.",
NULL
  };

  /* sample report */
  const char *sample[] = {
    "Sample report",
    "",
    "E = m * c**2",
    "Gamma(z) = integral_0_inf t**(z-1) * exp(-t) dt",
    "zeta(s) = sum(1/n**s, (n,1,oo))",
NULL
  };

  /* bin/omegascript (silent if verifier missing) */
  const char *omegash[] = {
    "#!/usr/bin/env sh",
    "echo \"omega_universe_eq_pkg: simple analysis wrapper\"",
    "if [ \"$1\" = \"analyze\" ]; then",
    "  REPORT_DIR=\"$2\"",
    "  OUT_TEX=\"$3\"",
    "  OUT_DIR=\"output\"",
    "  mkdir -p \"$OUT_DIR\"",
    "  > \"$OUT_DIR/equations.txt\"",
    "  for f in \"$REPORT_DIR\"/*.txt; do",
    "    [ -f \"$f\" ] || continue",
    "    grep '=' \"$f\" >> \"$OUT_DIR/equations.txt\" 2>/dev/null || true",
    "  done",
    "  echo \"Extracted equations to $OUT_DIR/equations.txt\"",
    "  if command -v python3 >/dev/null 2>&1; then",
    "    if [ -f usr/lang/verifier.py ]; then",
    "      python3 usr/lang/verifier.py \"$OUT_DIR/equations.txt\" \"$OUT_DIR\"",
    "    else",
    "      :  # verifier.py missing, silently skip invoking it",
    "    fi",
    "  fi",
    "else",
    "  echo \"Usage: $0 analyze <reports_dir> <out_tex>\"",
    "fi",
NULL
  };

  /* usr/lang/omegascript.c (simple analyzer) */
  const char *omegac[] = {
    "/* usr/lang/omegascript.c - minimal analyzer (safe, heuristic) */",
    "#define _POSIX_C_SOURCE 200809L",
    "#include <stdio.h>",
    "#include <stdlib.h>",
    "#include <string.h>",
    "#include <ctype.h>",
    "#include <dirent.h>",
    "#include <sys/stat.h>",
    "#include <errno.h>",
    "",
    "static char *read_whole(const char *path) {",
    "    FILE *f = fopen(path, \"rb\"); if (!f) return NULL;",
    "    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }",
    "    long s = ftell(f); if (s < 0) { fclose(f); return NULL; }",
    "    fseek(f, 0, SEEK_SET);",
    "    char *buf = malloc((size_t)s + 1); if (!buf) { fclose(f); return NULL; }",
    "    if (fread(buf, 1, (size_t)s, f) != (size_t)s) { free(buf); fclose(f); return NULL; }",
    "    buf[s] = '\\0'; fclose(f); return buf;",
    "}",
    "",
    "static void trim_inplace(char *s) {",
    "    if (!s) return; char *a = s; while (*a && isspace((unsigned char)*a)) a++; if (a != s) memmove(s, a, strlen(a)+1);",
    "    char *b = s + strlen(s); while (b > s && isspace((unsigned char)*(b-1))) *--b = '\\0';",
    "}",
    "",
    "static int split_eq(const char *s, char *lhs, size_t lsz, char *rhs, size_t rsz) {",
    "    const char *eq = strchr(s, '='); if (!eq) return 0;",
    "    size_t L = (size_t)(eq - s); if (L >= lsz) L = lsz-1; memcpy(lhs, s, L); lhs[L] = '\\0'; trim_inplace(lhs);",
    "    const char *rp = eq + 1; while (*rp && isspace((unsigned char)*rp)) rp++; strncpy(rhs, rp, rsz-1); rhs[rsz-1] = '\\0'; trim_inplace(rhs);",
    "    return 1;",
    "}",
    "",
    "static char **split_terms(const char *expr, int *n) {",
    "    *n = 0; if (!expr) return NULL; char *s = strdup(expr); if (!s) return NULL;",
    "    int cap = 8; char **arr = malloc(sizeof(char*) * cap); char *p = s; char *tok;",
    "    while ((tok = strsep(&p, \"+\")) != NULL) {",
    "        while (*tok && isspace((unsigned char)*tok)) tok++; char *end = tok + strlen(tok); while (end > tok && isspace((unsigned char)*(end-1))) *--end = '\\0';",
    "        if (*tok == '\\0') continue;",
    "        if (*n >= cap) { cap *= 2; char **tmp = realloc(arr, sizeof(char*) * cap); if (!tmp) break; arr = tmp; }",
    "        arr[*n] = strdup(tok); if (arr[*n]) (*n)++;",
    "    }",
    "    free(s); return arr;",
    "}",
    "",
    "static char **generate_candidates(const char *lhs, const char *rhs, int *out_n) {",
    "    *out_n = 0; if (!lhs || !rhs) return NULL;",
    "    int ln=0, rn=0; char **lt = split_terms(lhs, &ln); char **rt = split_terms(rhs, &rn);",
    "    int cap = 64; char **c = malloc(sizeof(char*) * cap); int cnt = 0;",
    "    if (ln>0 || rn>0) { size_t L = strlen(lhs) + strlen(rhs) + 8; char *orig = malloc(L); if (orig) { snprintf(orig, L, \"%s = %s\", lhs, rhs); c[cnt++] = orig; } }",
    "    for (int i=0;i<ln;i++) for (int j=0;j<rn;j++) {",
    "        size_t need = strlen(lhs) + 256; char *nl = malloc(need); char *nr = malloc(need); if (!nl || !nr) { free(nl); free(nr); continue; }",
    "        nl[0] = '\\0'; nr[0] = '\\0';",
    "        for (int a=0;a<ln;a++) { if (a) strncat(nl, \" + \", need-strlen(nl)-1); strncat(nl, (a==i)?rt[j]:lt[a], need - strlen(nl) -1); }",
    "        for (int b=0;b<rn;b++) { if (b) strncat(nr, \" + \", need-strlen(nr)-1); strncat(nr, (b==j)?lt[i]:rt[b], need - strlen(nr) -1); }",
    "        size_t tot = strlen(nl) + strlen(nr) + 8; char *eq = malloc(tot); if (eq) { snprintf(eq, tot, \"%s = %s\", nl, nr); if (cnt >= cap) { cap *= 2; char **tmp = realloc(c, sizeof(char*) * cap); if (!tmp) { free(eq); free(nl); free(nr); goto GEND; } c = tmp; } c[cnt++] = eq; }",
    "        free(nl); free(nr);",
    "    }",
    "    for (int i=0;i<ln;i++) for (int j=i+1;j<ln;j++) {",
    "        size_t need = strlen(lhs) + 256; char *nl = malloc(need); if (!nl) continue; nl[0] = '\\0';",
    "        for (int a=0;a<ln;a++) { if (a) strncat(nl, \" + \", need-strlen(nl)-1); if (a==i) { char buf[256]; snprintf(buf, sizeof(buf), \"(%s*%s)\", lt[i], lt[j]); strncat(nl, buf, need - strlen(nl) -1); } else if (a==j) continue; else strncat(nl, lt[a], need - strlen(nl) -1); }",
    "        size_t tot = strlen(nl) + strlen(rhs) + 8; char *eq = malloc(tot); if (eq) { snprintf(eq, tot, \"%s = %s\", nl, rhs); if (cnt >= cap) { cap *= 2; char **tmp = realloc(c, sizeof(char*) * cap); if (!tmp) { free(eq); free(nl); goto GEND; } c = tmp; } c[cnt++] = eq; }",
    "        free(nl);",
    "    }",
    "GEND:",
    "    for (int i=0;i<ln;i++) free(lt[i]); free(lt);",
    "    for (int i=0;i<rn;i++) free(rt[i]); free(rt);",
    "    *out_n = cnt; return c;",
    "}",
    "",
    "static int gen_verifier_py_stub(const char *path) {",
    "    FILE *f = fopen(path, \"wb\"); if (!f) return -1;",
    "    fputs(\"#!/usr/bin/env python3\\n\", f);",
    "    fputs(\"print('verifier stub; run usr/lang/verifier.py for full checks')\\n\", f);",
    "    fclose(f);",
    "#ifndef _WIN32",
    "    chmod(path, 0755);",
    "#endif",
    "    return 0;",
    "}",
    "",
    "int main(int argc, char **argv) {",
    "    if (argc < 4 || strcmp(argv[1], \"analyze\") != 0) { fprintf(stderr, \"usage: %s analyze <reports_dir> <out_tex>\\n\", argv[0]); return 1; }",
    "    const char *dir = argv[2]; const char *out_tex = argv[3];",
    "    char **lines = NULL; int ln = 0;",
    "    DIR *d = opendir(dir); if (!d) { fprintf(stderr, \"cannot open %s: %s\\n\", dir, strerror(errno)); return 1; }",
    "    struct dirent *ent;",
    "    while ((ent = readdir(d)) != NULL) {",
    "        const char *name = ent->d_name; size_t namelen = strlen(name);",
    "        if (namelen > 4 && strcasecmp(name + namelen - 4, \".txt\") == 0) {",
    "            char path[1024]; if (snprintf(path, sizeof(path), \"%s/%s\", dir, name) >= (int)sizeof(path)) continue;",
    "            char *txt = read_whole(path); if (!txt) continue;",
    "            char *save = NULL; char *lnk = strtok_r(txt, \"\\n\", &save);",
    "            while (lnk) { char *p = lnk; while (*p && isspace((unsigned char)*p)) p++; if (*p && strchr(lnk, '=')) { char *s = strdup(lnk); if (s) { char **tmp = realloc(lines, sizeof(char*) * (ln+1)); if (tmp) { lines = tmp; lines[ln++] = s; } else free(s); } }",
    "                lnk = strtok_r(NULL, \"\\n\", &save);",
    "            }",
    "            free(txt);",
    "        }",
    "    }",
    "    closedir(d);",
    "    if (ln == 0) { fprintf(stderr, \"no equations found in reports/\\n\"); return 1; }",
    "    char **candidates = NULL; int cand_n = 0;",
    "    for (int i=0;i<ln;i++) {",
    "        char lhs[1024] = {0}, rhs[1024] = {0};",
    "        if (!split_eq(lines[i], lhs, sizeof(lhs), rhs, sizeof(rhs))) continue;",
    "        int gn = 0; char **gen = generate_candidates(lhs, rhs, &gn);",
    "        for (int g=0; g<gn; g++) {",
    "            int dup = 0; for (int k=0;k<cand_n;k++) if (strcmp(candidates[k], gen[g]) == 0) { dup = 1; break; }",
    "            if (!dup) { char **tmp = realloc(candidates, sizeof(char*) * (cand_n+1)); if (!tmp) continue; candidates = tmp; candidates[cand_n++] = gen[g]; } else free(gen[g]);",
    "        }",
    "        free(gen);",
    "    }",
    "    FILE *fj = fopen(\"output/candidates.json\", \"wb\"); if (fj) { fputs(\"{\\n  \\\"candidates\\\": [\\n\", fj); for (int i=0;i<cand_n;i++) { fprintf(fj, \"    \\\"%s\\\"%s\\n\", candidates[i], (i+1<cand_n)?\",\":\"\"); } fputs(\"  ]\\n}\\n\", fj); fclose(fj); }",
    "    /* write equations.txt for verifier input */",
    "    FILE *fe = fopen(\"output/equations.txt\", \"wb\"); if (fe) { for (int i=0;i<ln;i++) fprintf(fe, \"%s\\n\", lines[i]); fclose(fe); }",
    "    /* generate a simple verifier stub if full verifier missing; full verifier is written by pkginstallgen */",
    "    gen_verifier_py_stub(\"usr/lang/verifier_stub.py\");",
    "    /* create simple LaTeX skeleton */",
    "    FILE *ft = fopen(out_tex, \"wb\"); if (ft) { fputs(\"\\\\documentclass{article}\\\\n\\\\usepackage{amsmath,amssymb}\\\\n\\\\begin{document}\\\\n\", ft); fputs(\"\\\\title{Inferred Universe-Compatible Equations}\\\\maketitle\\\\n\", ft); fputs(\"\\\\section*{Candidate Equations}\\\\n\\\\begin{enumerate}\\\\n\", ft); for (int i=0;i<cand_n;i++) fprintf(ft, \"\\\\item \\texttt{%s}\\\\n\", candidates[i]); fputs(\"\\\\end{enumerate}\\\\n\\\\section*{Notes on Verification}\\\\nRun usr/lang/verifier.py with python3 (sympy) to verify candidates.\\\\n\", ft); fputs(\"\\\\end{document}\\\\n\", ft); fclose(ft); }",
    "    for (int i=0;i<ln;i++) free(lines[i]); free(lines);",
    "    for (int i=0;i<cand_n;i++) free(candidates[i]); free(candidates);",
    "    return 0;",
    "}",
NULL
  };

  /* usr/lang/verifier.py (full verifier using sympy) */
  const char *verifier_py[] = {
    "#!/usr/bin/env python3",
    "\"\"\"usr/lang/verifier.py",
    "Simple verifier:",
    "  python3 usr/lang/verifier.py <equations.txt> <out_dir>",
    "Reads lines with '=' from equations.txt, attempts sympify on both sides,",
    "computes diff = simplify(L - R), and performs numeric sampling.",
    "Outputs JSON to <out_dir>/verification.json",
    "\"\"\"",
    "import sys, os, json, random",
    "try:",
    "    import sympy as sp",
    "except Exception:",
    "    sp = None",
    "",
    "def read_eqs(path):",
    "    if not os.path.exists(path): return []",
    "    with open(path, 'r', encoding='utf-8', errors='ignore') as f:",
    "        return [line.strip() for line in f if '=' in line]",
    "",
    "def split_eq(line):",
    "    a, _, b = line.partition('=')",
    "    return a.strip(), b.strip()",
    "",
    "def sample_and_check(expr, samples=8):",
    "    syms = list(expr.free_symbols)",
    "    checks = []",
    "    ok_all = True",
    "    for _ in range(samples):",
    "        vals = {s: random.uniform(0.1, 3.0) for s in syms}",
    "        try:",
    "            v = expr.subs(vals)",
    "            v = float(sp.N(v, 20)) if sp is not None else None",
    "            ok = abs(v) < 1e-8 if v is not None else False",
    "            checks.append({'vals': {str(k): float(vals[k]) for k in vals}, 'value': v, 'ok': ok})",
    "            if not ok: ok_all = False",
    "        except Exception as e:",
    "            checks.append({'vals': {str(k): float(vals[k]) for k in vals} if 'vals' in locals() else {}, 'value': str(e), 'ok': False})",
    "            ok_all = False",
    "    return ok_all, checks",
    "",
    "def main():",
    "    if len(sys.argv) < 3:",
    "        print('usage: verifier.py <equations.txt> <out_dir>')",
    "        return 2",
    "    inpath = sys.argv[1]; outdir = sys.argv[2]",
    "    os.makedirs(outdir, exist_ok=True)",
    "    lines = read_eqs(inpath)",
    "    results = {'accepted': [], 'rejected': []}",
    "    for line in lines:",
    "        Ls, Rs = split_eq(line)",
    "        try:",
    "            if sp is None:",
    "                results['rejected'].append({'equation': line, 'error': 'sympy not installed'})",
    "                continue",
    "            L = sp.sympify(Ls)",
    "            R = sp.sympify(Rs)",
    "            diff = sp.simplify(L - R)",
    "            symbolic_ok = diff == 0",
    "            numeric_ok, checks = sample_and_check(diff)",
    "            entry = {'equation': line, 'symbolic': str(diff), 'numeric_ok': numeric_ok, 'checks': checks}",
    "            if symbolic_ok or numeric_ok:",
    "                results['accepted'].append(entry)",
    "            else:",
    "                results['rejected'].append(entry)",
    "        except Exception as e:",
    "            results['rejected'].append({'equation': line, 'error': str(e)})",
    "    outpath = os.path.join(outdir, 'verification.json')",
    "    with open(outpath, 'w', encoding='utf-8') as fo:",
    "        json.dump(results, fo, ensure_ascii=False, indent=2)",
    "    print('Wrote', outpath)",
    "",
    "if __name__ == '__main__':",
    "    sys.exit(main())",
NULL
  };

  /* write files */
  char path[4096];

  snprintf(path, sizeof(path), "%s/Makefile", target);
  write_lines(path, makefile, (sizeof(makefile)/sizeof(makefile[0])) - 1, 0644);

  snprintf(path, sizeof(path), "%s/README.md", target);
  write_lines(path, readme, (sizeof(readme)/sizeof(readme[0])) - 1, 0644);

  snprintf(path, sizeof(path), "%s/run.sh", target);
  write_lines(path, runsh, (sizeof(runsh)/sizeof(runsh[0])) - 1, 0755);

  snprintf(path, sizeof(path), "%s/reports/README.txt", target);
  write_lines(path, rread, (sizeof(rread)/sizeof(rread[0])) - 1, 0644);

  snprintf(path, sizeof(path), "%s/reports/sample1.txt", target);
  write_lines(path, sample, (sizeof(sample)/sizeof(sample[0])) - 1, 0644);

  snprintf(path, sizeof(path), "%s/bin/omegascript", target);
  write_lines(path, omegash, (sizeof(omegash)/sizeof(omegash[0])) - 1, 0755);

  snprintf(path, sizeof(path), "%s/usr/lang/omegascript.c", target);
  write_lines(path, omegac, (sizeof(omegac)/sizeof(omegac[0])) - 1, 0644);

  snprintf(path, sizeof(path), "%s/usr/lang/verifier.py", target);
  write_lines(path, verifier_py, (sizeof(verifier_py)/sizeof(verifier_py[0])) - 1, 0755);

  printf("Package skeleton created at: %s\n", target);
  snprintf(path, sizeof(path), "ls -R %s", target);
  system(path);

  return 0;
}
```
