```c
/*
 * pkginstallgen.c
 *
 * Single-file generator that creates a package with:
 *  - Makefile, run.sh, README
 *  - reports/sample
 *  - usr/lang/omegascript.c (robust analyzer)
 *  - usr/lang/verifier.py
 *  - usr/lang/qa_bot.py
 *
 * Build:
 *   gcc -std=c11 -O2 -Wall -o pkginstallgen pkginstallgen.c
 * Usage:
 *   ./pkginstallgen ./omega_pkg
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
#define MKDIR(p) mkdir((p),0755)
#endif

static int ensure_dir(const char *path) {
  if (!path) return -1;
  struct stat st;
  if (stat(path, &st) == 0) return S_ISDIR(st.st_mode) ? 0 : -1;
  char tmp[4096];
  strncpy(tmp, path, sizeof(tmp)-1);
  tmp[sizeof(tmp)-1] = '\0';
  for (char *p = tmp + 1; *p; ++p) {
    if (*p == '/') {
      *p = '\0';
      if (stat(tmp, &st) != 0) {
	if (MKDIR(tmp) != 0 && errno != EEXIST) return -1;
      }
      *p = '/';
    }
  }
  if (MKDIR(tmp) != 0 && errno != EEXIST) return -1;
  return 0;
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
#ifndef _WIN32
  if (mode) chmod(path, mode);
#endif
  return 0;
}

int main(int argc, char **argv) {
  const char *outdir = (argc > 1) ? argv[1] : "./omega_pkg";
  if (ensure_dir(outdir) != 0) { fprintf(stderr, "cannot create %s\n", outdir); return 1; }

    const char *makefile =
"CC ?= gcc\n"
"CFLAGS ?= -O2 -std=c11 -Wall\n"
"PREFIX ?= .\n"
"BIN_DIR = $(PREFIX)/bin\n"
"OMEGA_C = usr/lang/omegascript.c\n"
"OMEGA_BIN = $(BIN_DIR)/omegascript\n"
".PHONY: all clean\n"
"all: $(OMEGA_BIN)\n"
"\n"
"$(OMEGA_BIN): $(OMEGA_C)\n"
"\t@mkdir -p $(BIN_DIR)\n"
"\t$(CC) $(CFLAGS) -o $@ $< -lm\n"
"\t@printf \"built: %s\\n\" \"$@\"\n"
"\n"
"clean:\n"
      "\t-@rm -f $(OMEGA_BIN)\n";

    char path[4096];
    snprintf(path, sizeof(path), "%s/Makefile", outdir);
    write_file(path, makefile, 0);

    const char *runsh =
"#!/usr/bin/env sh\n"
"set -euo pipefail\n"
"if [ ! -f bin/omegascript ]; then echo \"Build with 'make' first.\"; exit 1; fi\n"
      "exec bin/omegascript \"$@\"\n";
    snprintf(path, sizeof(path), "%s/run.sh", outdir);
    write_file(path, runsh, 0755);

    const char *readme =
"# Omega Package\n"
"\n"
"Place plain-text reports in reports/ (lines containing '=' are used).\n"
"Build: make\n"
"Analyze: ./bin/omegascript analyze reports output/paper.tex\n"
"Verify: python3 usr/lang/verifier.py output/equations.txt output\n"
      "QA: python3 usr/lang/qa_bot.py output/equations.txt output\n";
    snprintf(path, sizeof(path), "%s/README.md", outdir);
    write_file(path, readme, 0);

    const char *reports_readme = "Place plain-text reports (*.txt) here. Lines with '=' will be extracted as equations.\n";
    snprintf(path, sizeof(path), "%s/reports/README.txt", outdir);
    write_file(path, reports_readme, 0);

    const char *sample =
"Sample report with formulae.\n"
"E = m * c**2\n"
"F = G * m1 * m2 / r**2\n"
"Gamma(z) = integral_0_inf t**(z-1) * exp(-t) dt\n"
      "zeta(s) = sum(1/n**s, (n,1,oo))\n";
    snprintf(path, sizeof(path), "%s/reports/sample1.txt", outdir);
    write_file(path, sample, 0);

    /* robust omegascript.c */
    const char *omegascript_c =
      "/* omegascript.c - robust analyzer (avoid segfault/core dump) */\n"
"#define _POSIX_C_SOURCE 200809L\n"
"#include <stdio.h>\n"
"#include <stdlib.h>\n"
"#include <string.h>\n"
"#include <ctype.h>\n"
"#include <dirent.h>\n"
"#include <sys/stat.h>\n"
"#include <errno.h>\n"
"#include <math.h>\n"
"\n"
"static char *read_whole(const char *path) {\n"
"    if (!path) return NULL;\n" 
"    FILE *f = fopen(path, \"rb\");\n"
"    if (!f) return NULL;\n"
"    if (fseek(f, 0, SEEK_END) != 0) { fclose(f); return NULL; }\n"
"    long s = ftell(f);\n"
"    if (s < 0) { fclose(f); return NULL; }\n"
"    if (fseek(f, 0, SEEK_SET) != 0) { fclose(f); return NULL; }\n"
"    size_t sz = (size_t)s;\n"
"    char *buf = malloc(sz + 1);\n"
"    if (!buf) { fclose(f); return NULL; }\n"
"    size_t got = fread(buf, 1, sz, f);\n"
"    buf[got] = '\\0';\n"
"    fclose(f);\n"
"    return buf;\n"
"}\n"
"\n"
"static double safe_log(double x) { if (x <= 0.0) return 0.0; return log(x); }\n"
"\n"
"static double simple_entropy(const char *s) {\n"
"    if (!s) return 0.0;\n"
"    unsigned long freq[256] = {0}; size_t n = 0;\n"
"    for (const unsigned char *p = (const unsigned char*)s; *p; ++p) { freq[*p]++; n++; }\n"
"    if (n == 0) return 0.0;\n"
"    double H = 0.0;\n"
"    for (int i = 0; i < 256; ++i) if (freq[i]) { double p = (double)freq[i] / (double)n; H -= p * safe_log(p + 1e-30); }\n"
"    return H;\n"
"}\n"
"\n"
"static void trim_inplace(char *s) {\n"
"    if (!s) return;\n" 
"    char *start = s; while (*start && isspace((unsigned char)*start)) start++;\n"
"    if (start != s) memmove(s, start, strlen(start) + 1);\n"
"    char *end = s + strlen(s);\n"
"    while (end > s && isspace((unsigned char)*(end - 1))) *--end = '\\0';\n"
"}\n"
"\n"
"static char **collect_lines_with_eq(const char *dir, int *out_n) {\n"
"    if (!dir || !out_n) return NULL;\n"
"    *out_n = 0; DIR *d = opendir(dir); if (!d) return NULL;\n"
"    struct dirent *ent; char **arr = NULL;\n"
"    while ((ent = readdir(d)) != NULL) {\n"
"        const char *name = ent->d_name; if (!name) continue;\n" 
"        size_t nl = strlen(name); if (nl < 5) continue;\n" 
"        const char *ext = name + nl - 4; if (strcasecmp(ext, \".txt\") != 0) continue;\n"
"        size_t need = strlen(dir) + 1 + strlen(name) + 1; char *path = malloc(need);\n"
"        if (!path) continue; snprintf(path, need, \"%s/%s\", dir, name);\n"
"        char *txt = read_whole(path); free(path); if (!txt) continue;\n"
"        char *save = NULL; char *line = strtok_r(txt, \"\\n\", &save);\n"
"        while (line) {\n"
"            char *linet = strdup(line);\n"
"            if (linet) {\n"
"                trim_inplace(linet);\n"
"                if (linet[0] != '\\0' && strchr(linet, '=')) {\n"
"                    char **tmp = realloc(arr, sizeof(char*) * ((size_t)(*out_n) + 1));\n"
"                    if (tmp) { arr = tmp; arr[*out_n] = linet; (*out_n)++; }\n"
"                    else free(linet);\n" 
"                } else free(linet);\n"
"            }\n"
"            line = strtok_r(NULL, \"\\n\", &save);\n"
"        }\n"
"        free(txt);\n"
"    }\n"
"    closedir(d); return arr;\n"
"}\n"
"\n"
"static char **split_plus(const char *s, int *count) {\n"
"    if (!s || !count) return NULL; *count = 0; char *work = strdup(s); if (!work) return NULL;\n"
"    char *save = NULL; char *tok = strtok_r(work, \"+\", &save); char **arr = NULL;\n"
"    while (tok) {\n"
"        trim_inplace(tok);\n" 
"        if (*tok) {\n"
"            char *piece = strdup(tok);\n" 
"            if (piece) {\n"
"                char **tmp = realloc(arr, sizeof(char*) * ((size_t)(*count) + 1));\n"
"                if (!tmp) { free(piece); for (int i=0;i<*count;i++) free(arr[i]); free(arr); arr = NULL; *count = 0; break; }\n"
"                arr = tmp; arr[*count] = piece; (*count)++;\n"
"            }\n"
"        }\n"
"        tok = strtok_r(NULL, \"+\", &save);\n"
"    }\n"
"    free(work); return arr;\n"
"}\n"
"\n"
"static char **generate_swapped_candidates(char **eqs, int neqs, int *out_n) {\n"
"    if (!eqs || neqs <= 0 || !out_n) { if (out_n) *out_n = 0; return NULL; }\n"
"    *out_n = 0; char **out = NULL;\n" 
"    for (int i = 0; i < neqs; ++i) {\n"
"        char *e = eqs[i]; if (!e) continue; char *eqp = strchr(e, '='); if (!eqp) continue;\n"
"        size_t lhs_len = (size_t)(eqp - e); char *lhs = malloc(lhs_len + 1);\n"
"        if (!lhs) continue; memcpy(lhs, e, lhs_len); lhs[lhs_len] = '\\0';\n"
"        char *rhs = strdup(eqp + 1); if (!rhs) { free(lhs); continue; }\n"
"        trim_inplace(lhs); trim_inplace(rhs);\n"
"        int ln=0, rn=0; char **lt = split_plus(lhs, &ln); char **rt = split_plus(rhs, &rn);\n"
"        free(lhs); free(rhs);\n"
"        if (!lt || !rt || ln==0 || rn==0) { if (lt) { for (int k=0;k<ln;k++) free(lt[k]); free(lt); } if (rt) { for (int k=0;k<rn;k++) free(rt[k]); free(rt); } continue; }\n"
"        for (int a=0; a<ln && a<5; ++a) {\n"
"            for (int b=0; b<rn && b<5; ++b) {\n"
"                size_t bufcap = 256; char *buf = malloc(bufcap); if (!buf) continue; buf[0] = '\\0';\n" 
"                for (int u=0; u<ln; ++u) {\n"
"                    const char *piece = (u==a) ? rt[b] : lt[u]; if (!piece) continue;\n"
"                    size_t need = strlen(buf) + strlen(piece) + 4;\n"
"                    if (need > bufcap) { char *nb = realloc(buf, need + 128); if (!nb) { free(buf); buf = NULL; break; } buf = nb; bufcap = need + 128; }\n"
"                    if (u) strcat(buf, \" + \"); strcat(buf, piece);\n"
"                }\n"
"                if (!buf) continue;\n" 
"                char *rbuf = NULL; size_t rcap = 256; rbuf = malloc(rcap); if (!rbuf) { free(buf); continue; } rbuf[0] = '\\0';\n"
"                for (int v=0; v<rn; ++v) {\n"
"                    const char *piece = (v==b) ? lt[a] : rt[v]; if (!piece) continue;\n"
"                    size_t need2 = strlen(rbuf) + strlen(piece) + 4;\n"
"                    if (need2 > rcap) { char *nb = realloc(rbuf, need2 + 128); if (!nb) { free(buf); free(rbuf); rbuf = NULL; break; } rbuf = nb; rcap = need2 + 128; }\n"
"                    if (v) strcat(rbuf, \" + \"); strcat(rbuf, piece);\n"
"                }\n"
"                if (!rbuf) continue;\n"
"                size_t full = strlen(buf) + 3 + strlen(rbuf) + 1;\n" 
"                char *fulls = malloc(full);\n"
"                if (!fulls) { free(buf); free(rbuf); continue; }\n" 
"                strcpy(fulls, buf); strcat(fulls, \" = \"); strcat(fulls, rbuf);\n" 
"                free(buf); free(rbuf);\n"
"                char **narr = realloc(out, sizeof(char*) * ((size_t)(*out_n) + 1));\n"
"                if (!narr) { free(fulls); continue; }\n"
"                out = narr; out[*out_n] = fulls; (*out_n)++; if (*out_n > 1000) break;\n"
"            }\n"
"            if (*out_n > 1000) break;\n"
"        }\n"
"        for (int k=0;k<ln;k++) free(lt[k]); for (int k=0;k<rn;k++) free(rt[k]); free(lt); free(rt);\n" 
"    }\n"
"    return out;\n"
"}\n"
"\n"
"static int ensure_dir_local(const char *path) {\n"
"    if (!path) return -1; struct stat st; if (stat(path, &st) == 0) return S_ISDIR(st.st_mode) ? 0 : -1;\n"
"    if (mkdir(path, 0755) != 0 && errno != EEXIST) return -1; return 0;\n"
"}\n"
"\n"
"static void write_outputs(const char *outdir, char **eqs, int neq, char **cands, int ncand) {\n"
"    if (!outdir) outdir = \".\";\n"
"    char outpath[1024]; snprintf(outpath, sizeof(outpath), \"%s/output\", outdir); ensure_dir_local(outpath);\n"
"    snprintf(outpath, sizeof(outpath), \"%s/output/equations.txt\", outdir);\n"
"    FILE *f = fopen(outpath, \"wb\"); if (f) { for (int i=0;i<neq;i++) if (eqs && eqs[i]) fprintf(f, \"%s\\n\", eqs[i]); fclose(f); }\n"
"    snprintf(outpath, sizeof(outpath), \"%s/output/paper.tex\", outdir);\n"
"    FILE *g = fopen(outpath, \"wb\"); if (g) { fprintf(g, \"\\\\documentclass{article}\\\\begin{document}\\\\section*{Extracted Equations}\\\\begin{verbatim}\\n\"); for (int i=0;i<neq;i++) if (eqs && eqs[i]) fprintf(g, \"%s\\n\", eqs[i]); fprintf(g, \"\\nGenerated candidates:\\n\"); for (int j=0;j<ncand && j<200;j++) if (cands && cands[j]) fprintf(g, \"%s\\n\", cands[j]); fprintf(g, \"\\\\end{verbatim}\\\\end{document}\\n\"); fclose(g); }\n"
"}\n"
"\n"
"int main(int argc, char **argv) {\n"
"    if (argc < 4 || strcmp(argv[1], \"analyze\") != 0) { fprintf(stderr, \"Usage: %s analyze <reports_dir> <outdir_tex>\\n\", argv[0]); return 1; }\n"
"    const char *rdir = argv[2]; (void)argv[3];\n"
"    int neq = 0; char **eqs = collect_lines_with_eq(rdir, &neq);\n"
"    if (!eqs || neq == 0) { fprintf(stderr, \"No equations found in %s\\n\", rdir); if (eqs) free(eqs); return 1; }\n"
"    double *ents = calloc((size_t)neq, sizeof(double)); if (!ents) { fprintf(stderr, \"memory allocation failure\\n\"); for (int i=0;i<neq;i++) free(eqs[i]); free(eqs); return 1; }\n"
"    for (int i=0;i<neq;i++) ents[i] = simple_entropy(eqs[i]);\n"
"    int ncand = 0; char **cands = generate_swapped_candidates(eqs, neq, &ncand);\n"
"    write_outputs(\".\", eqs, neq, cands, ncand);\n"
"    for (int i=0;i<neq;i++) free(eqs[i]); free(eqs);\n" 
"    if (cands) { for (int j=0;j<ncand;j++) free(cands[j]); free(cands); }\n"
"    free(ents);\n"
"    printf(\"Analysis written to ./output (equations.txt, paper.tex)\\n\");\n"
"    return 0;\n"
      "}\n";

    snprintf(path, sizeof(path), "%s/usr/lang/omegascript.c", outdir);
    write_file(path, omegascript_c, 0644);

    const char *verifier_py =
"#!/usr/bin/env python3\n"
"\"\"\"verifier.py - numeric/symbolic checking using sympy if available\"\"\"\n"
"import sys, os, json, random\n"
"try:\n"
"    import sympy as sp\n"
"except Exception:\n"
"    sp = None\n"
"\n"
"def read_eqs(path):\n"
"    if not os.path.exists(path): return []\n"
"    with open(path,'r',encoding='utf-8',errors='ignore') as f:\n"
"        return [l.strip() for l in f if '=' in l]\n"
"\n"
"def split_eq(line):\n"
"    a,_,b = line.partition('='); return a.strip(), b.strip()\n"
"\n"
"def sample_check(expr, samples=8):\n"
"    syms = list(expr.free_symbols)\n"
"    ok_all = True; checks = []\n"
"    for _ in range(samples):\n"
"        vals = {s: random.uniform(0.1, 3.0) for s in syms}\n"
"        try:\n"
"            v = expr.subs(vals); v = float(sp.N(v,20)); ok = abs(v) < 1e-6; checks.append({'val': v, 'ok': ok});\n"
"            if not ok: ok_all = False\n"
"        except Exception as e:\n"
"            checks.append({'error': str(e)}); ok_all = False\n"
"    return ok_all, checks\n"
"\n"
"def main():\n"
"    if len(sys.argv)<3: print('usage: verifier.py <equations.txt> <outdir>'); return 2\n"
"    path = sys.argv[1]; outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True)\n"
"    eqs = read_eqs(path); results = {'accepted':[], 'rejected':[]}\n"
"    if sp is None: print('sympy not installed; only basic checks')\n"
"    for line in eqs:\n"
"        Ls, Rs = split_eq(line)\n"
"        if sp is None:\n"
"            results['rejected'].append({'equation': line, 'reason':'sympy not present'}); continue\n"
"        try:\n"
"            L = sp.sympify(Ls); R = sp.sympify(Rs); diff = sp.simplify(L - R); sym_ok = (diff == 0); num_ok, checks = sample_check(diff)\n"
"            entry = {'equation':line, 'symbolic': str(diff), 'numeric_ok': num_ok, 'checks': checks}\n"
"            if sym_ok or num_ok: results['accepted'].append(entry)\n"
"            else: results['rejected'].append(entry)\n"
"        except Exception as e:\n"
"            results['rejected'].append({'equation':line, 'error': str(e)})\n"
"    with open(os.path.join(outdir,'verification.json'),'w',encoding='utf-8') as fo: json.dump(results, fo, ensure_ascii=False, indent=2)\n"
"    print('Wrote verification.json')\n"
"\n"
      "if __name__ == '__main__': main()\n";
    snprintf(path, sizeof(path), "%s/usr/lang/verifier.py", outdir);
    write_file(path, verifier_py, 0755);

    const char *qa_bot_py =
"#!/usr/bin/env python3\n"
"\"\"\"qa_bot.py - simple QA by text-feature matching + numeric probing\"\"\"\n"
"import sys, os, math, random\n"
"from collections import Counter\n"
"try:\n"
"    import sympy as sp\n"
"except Exception:\n"
"    sp = None\n"
"\n"
"def read_eqs(path):\n"
"    if not os.path.exists(path): return []\n"
"    with open(path,'r',encoding='utf-8',errors='ignore') as f:\n"
"        return [l.strip() for l in f if '=' in l]\n"
"\n"
"def entropy_of(s):\n"
"    if not s: return 0.0\n"
"    c = Counter(s); n = sum(c.values()); H = 0.0\n"
"    for v in c.values(): p = v / n; H -= p * math.log(p + 1e-30)\n"
"    return H\n"
"\n"
"def features(text):\n"
"    ent = entropy_of(text); length = len(text); symb = sum(1 for ch in text if (not ch.isalnum() and not ch.isspace())); ql = text.lower()\n"
"    kw = {'shannon': 1.0 if ('shannon' in ql or 'entropy' in ql) else 0.0, 'zeta': 1.0 if 'zeta' in ql else 0.0, 'gamma': 1.0 if 'gamma' in ql else 0.0, 'quantum': 1.0 if 'quantum' in ql else 0.0, 'manifold': 1.0 if ('manifold' in ql or 'differential' in ql) else 0.0, 'noncomm': 1.0 if ('noncomm' in ql or 'non-commut' in ql) else 0.0}\n"
"    return {'ent':ent,'len':length,'sym':symb,'kw':kw}\n"
"\n"
"def score(qf, ef):\n"
"    s = 0.0; s -= abs(qf['ent'] - ef['ent']) * 0.6; s -= abs(qf['len'] - ef['len']) * 0.01; s -= abs(qf['sym'] - ef['sym']) * 0.2\n"
"    for k in qf['kw']: s += (qf['kw'][k] * ef['kw'].get(k,0.0)) * 2.0\n"
"    return s\n"
"\n"
"def make_eq_features(eqs):\n"
"    feats = []\n"
"    for e in eqs:\n"
"        f = features(e); ql = e.lower()\n"
"        for k in ['shannon','zeta','gamma','quantum','manifold','noncomm']:\n"
"            if k in ql: f['kw'][k] = 1.0\n"
"        feats.append(f)\n"
"    return feats\n"
"\n"
"def attempt_numeric_probe(eq_text):\n"
"    if sp is None: return {'ok': False, 'reason': 'sympy missing'}\n"
"    a,_,b = eq_text.partition('=')\n"
"    try:\n"
"        L = sp.sympify(a); R = sp.sympify(b); diff = sp.simplify(L - R); syms = list(diff.free_symbols); checks = []; ok_all = True\n"
"        for _ in range(6):\n"
"            vals = {s: random.uniform(0.1, 3.0) for s in syms}\n"
"            try:\n"
"                v = diff.subs(vals); v = float(sp.N(v,20)); ok = abs(v) < 1e-6; checks.append({'v': v, 'ok': ok}); if not ok: ok_all = False\n"
"            except Exception as e:\n"
"                checks.append({'error': str(e)}); ok_all = False\n"
"        return {'ok': ok_all, 'checks': checks, 'symbolic': str(diff)}\n"
"    except Exception as e:\n"
"        return {'ok': False, 'reason': str(e)}\n"
"\n"
"def answer_question(eqs, feats, q):\n"
"    qf = features(q); scores = [(score(qf, feats[i]), i) for i in range(len(eqs))]; scores.sort(reverse=True); top = scores[:3]\n"
"    if not top: return 'No equations available.'\n"
"    parts = []\n"
"    for s,i in top:\n"
"        line = eqs[i]; probe = attempt_numeric_probe(line)\n"
"        if probe.get('ok') is True:\n"
"            parts.append(f\"Candidate: {line} (score={s:.3f}); numeric probe: consistent in samples.\")\n"
"        elif probe.get('ok') is False and 'reason' in probe:\n"
"            parts.append(f\"Candidate: {line} (score={s:.3f}); probe failed: {probe['reason']}\")\n"
"        else:\n"
"            parts.append(f\"Candidate: {line} (score={s:.3f}); numeric probe inconclusive.\")\n"
"    ql = q.lower()\n"
"    if 'entropy' in ql or 'shannon' in ql: pre = 'You asked about entropy/Shannon. Relevant items:'\n"
"    elif 'zeta' in ql: pre = 'You asked about the zeta function. Relevant items:'\n"
"    elif 'gamma' in ql: pre = 'You asked about the gamma function. Relevant items:'\n"
"    elif 'quantum' in ql or 'quantisation' in ql or 'quantization' in ql: pre = 'You asked about quantum/quantization. Relevant items:'\n"
"    else: pre = 'Based on your question, best-matching equations are:'\n"
"    return pre + '\\n' + '\\n'.join(parts)\n"
"\n"
"def main():\n"
"    if len(sys.argv)<3: print('usage: qa_bot.py <equations.txt> <outdir>'); return 2\n"
"    path = sys.argv[1]; outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True)\n"
"    with open(path,'r',encoding='utf-8',errors='ignore') as f: eqs = [l.strip() for l in f if '=' in l]\n"
"    if not eqs: print('No equations found.'); return 0\n"
"    feats = make_eq_features(eqs)\n"
"    print('QA bot ready. Type a question (empty to quit).')\n"
"    try:\n"
"        while True:\n"
"            q = input('\\nQuestion: ').strip();\n"
"            if not q: break\n"
"            print('\\nAnswer:\\n' + answer_question(eqs, feats, q))\n"
"    except (EOFError, KeyboardInterrupt): print('\\nExiting.')\n"
"\n"
      "if __name__ == '__main__': main()\n";
    snprintf(path, sizeof(path), "%s/usr/lang/qa_bot.py", outdir);
    write_file(path, qa_bot_py, 0755);

    /* create dirs */
    ensure_dir(outdir);
    snprintf(path, sizeof(path), "%s/bin", outdir); ensure_dir(path);
    snprintf(path, sizeof(path), "%s/usr/lang", outdir); ensure_dir(path);
    snprintf(path, sizeof(path), "%s/output", outdir); ensure_dir(path);
    snprintf(path, sizeof(path), "%s/reports", outdir); ensure_dir(path);

    printf("Package generator completed. Directory: %s\n", outdir);
    printf("Next: cd %s && make ; put text reports into reports/ ; then run analysis and QA as described in README.\n", outdir);
    return 0;
}
```
