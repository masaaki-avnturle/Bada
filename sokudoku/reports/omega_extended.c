```c
/*
pkginstallgen.c

Generate an Omega Script package skeleton that includes:
 - bin/omega (interpreter driver placeholder)
 - bin/omega-proof-extended.c (C proof/LaTeX generator from previous message)
 - bin/omega-extract.py (Python: extract formulas, compute entropies, infer title/theorem/proof)
 - lib/ (placeholder)
 - include/omega.h
 - etc/omega.conf
 - usr/share/omega/README.md
 - package/src/ (placeholders)
 - robust Makefile that builds the C tool and suppresses errors

Build:
  gcc -o pkginstallgen pkginstallgen.c

Run:
  ./pkginstallgen ./omega_package

This program writes source files (C and Python) and supporting files into the target directory.
*/

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <direct.h>
#define MKDIR(p) _mkdir(p)
#else
#include <sys/stat.h>
#include <sys/types.h>
#define MKDIR(p) mkdir((p),0755)
#endif

static void mkdir_p(const char *path) {
  char tmp[4096];
  char *p = NULL;
  size_t len;
  snprintf(tmp, sizeof(tmp), "%s", path);
  len = strlen(tmp);
  if (len == 0) return;
  if (tmp[len - 1] == '/' ) tmp[len - 1] = 0;
  for (p = tmp + 1; *p; p++) {
    if (*p == '/') {
      *p = 0;
      MKDIR(tmp);
      *p = '/';
    }
  }
  MKDIR(tmp);
}

static int write_file(const char *path, const char *data) {
  FILE *f = fopen(path, "wb");
  if (!f) return -1;
  fwrite(data, 1, strlen(data), f);
  fclose(f);
  return 0;
}

int main(int argc, char **argv) {
  const char *out = "omega_package";
  if (argc > 1) out = argv[1];
  char buf[4096];

  // create directories
  snprintf(buf, sizeof(buf), "%s/bin", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/lib", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/include", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/etc", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/usr/share/omega", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/package/src", out); mkdir_p(buf);

  // include/omega.h
    const char *omega_h =
      "/* include/omega.h - public header for Omega Script runtime and proof tool */\n"
"#ifndef OMEGA_H\n"
"#define OMEGA_H\n\n"
"#include <stdio.h>\n"
"#include <stdlib.h>\n\n"
"typedef enum { OMEGA_N_NUM, OMEGA_N_BINOP, OMEGA_N_VAR, OMEGA_N_CALL } omega_node_type;\n"
"typedef struct omega_node {\n"
"    omega_node_type type;\n"
"    double num;\n"
"    char *op;\n"
  "    struct omega_node *left, *right;\n"} omega_node;\n\n"
							 "/* runtime API (placeholders) */\n"
"omega_node *omega_parse(const char *src);\n"
"double omega_eval(omega_node *n);\n"
"void omega_free_node(omega_node *n);\n\n"
							 "#endif /* OMEGA_H */\n";

    snprintf(buf, sizeof(buf), "%s/include/omega.h", out);
    write_file(buf, omega_h);

    // bin/omega (simple driver)
    const char *bin_omega =
"#!/bin/sh\n"
"# omega - placeholder interpreter driver\n"
"if [ \"$#\" -lt 1 ]; then\n"
"  echo \"Usage: $0 '<expression>'\" >&2\n" 
"  exit 2\n"
"fi\n"
"expr=\"$1\"\n"
"echo \"omega interpreter placeholder: expression -> $expr\"\n"
      "exit 0\n";
    snprintf(buf, sizeof(buf), "%s/bin/omega", out);
    write_file(buf, bin_omega);

    // bin/omega-proof-extended.c (from previous assistant message) - trimmed header included
    const char *proof_c =
      "/* bin/omega-proof-extended.c\n   Extended proof-verifier + LaTeX generator (C99).\n   Build: gcc -std=c99 -O2 -o bin/omega-proof-extended bin/omega-proof-extended.c -lm\n   Usage: ./bin/omega-proof-extended input.txt output.tex\n*/\n\n#define _POSIX_C_SOURCE 200809L\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <math.h>\n\n#define MAXLINE 4096\n#define MAXCOEFF 16\n#define MAXBRANCH 8\n#define MAXEXPR 256\n\nstatic char **read_input(const char *path, int *out_n) {\n    FILE *f = fopen(path, \"r\"); if (!f) return NULL;\n    char **lines = NULL; int cap = 0, n = 0; char buf[MAXLINE];\n    while (fgets(buf, sizeof(buf), f)) {\n        size_t L = strlen(buf); while (L && (buf[L-1]=='\\n' || buf[L-1]=='\\r')) buf[--L]=0;\n        char *s = buf; while (*s==' '||*s=='\\t') s++; if (*s==0 || *s=='#') continue;\n        if (n+1 > cap) { cap = cap ? cap*2 : 16; lines = realloc(lines, cap * sizeof(char*)); }\n        lines[n++] = strdup(s);\n    }\n    fclose(f); *out_n = n; return lines;\n}\n\nstatic void pseudo_jones(const char *s, double coeffs[], int *deg) {\n    unsigned long seed = 1469598103934665603u; for (const unsigned char *p=(const unsigned char*)s; *p; ++p) seed = (seed ^ *p) * 1099511628211u;\n    seed ^= seed >> 32; int d = 1 + (seed % 5); if (d > MAXCOEFF-1) d = MAXCOEFF-1; *deg = d;\n    for (int k=0;k<=d;k++) { unsigned long v = (seed * (k+1)) ^ (k * 2654435761u); int ai = (int)(v % 41) - 20; coeffs[k] = (double)ai; }\n    int allz=1; for (int k=0;k<=d;k++) if (fabs(coeffs[k])>1e-12) { allz=0; break; } if (allz) coeffs[0]=1.0;\n}\n\nstatic double coeffs_entropy(const double coeffs[], int deg) {\n    double mags[MAXCOEFF], s=0.0; for (int i=0;i<=deg;i++) { mags[i]=fabs(coeffs[i]); s+=mags[i]; }\n    if (s==0.0) return 0.0; double H=0.0; for (int i=0;i<=deg;i++) { double p = mags[i]/s; if (p>0.0) H -= p * (log(p)/log(2.0)); } return H;\n}\n\nstatic double pseudo_zeta_from_coeffs(const double coeffs[], int deg, double H) {\n    double s = 1.0 + (H / (1.0 + H)); double acc = 0.0; for (int k=0;k<=deg;k++) acc += coeffs[k] / pow((double)(k+1), s); return acc;\n}\nstatic double pseudo_gamma_indicator(const double coeffs[], int deg) {\n    double sum=0.0; for (int k=0;k<=deg;k++) sum += fabs(coeffs[k]); double mean = sum / (double)(deg+1); double x = mean + 1.0; if (x <= 0.0) return 1.0; double lg = (x-0.5)*log(x) - x + 0.5*log(2*M_PI); return exp(lg);\n}\nstatic double pseudo_amgm_ratio(const double coeffs[], int deg) {\n    double sum=0.0, prod=1.0; int n=deg+1; for (int k=0;k<=deg;k++) { double a = fabs(coeffs[k]); sum += a; if (a <= 0.0) a = 1e-12; prod *= a; if (!isfinite(prod) || prod>1e300) prod = fmod(prod, 1e308); }\n    double am = sum/(double)n; double gm = pow(prod, 1.0/(double)n); if (gm <= 1e-12) return am / 1e-12; return am / gm;\n}\nstatic double pseudo_global_diff_manifold(const double coeffs[], int deg, double H) { double var=0.0, mean=0.0; for (int k=0;k<=deg;k++) mean += coeffs[k]; mean /= (deg+1); for (int k=0;k<=deg;k++){ double d = coeffs[k]-mean; var += d*d; } var /= (deg+1); return sqrt(var) * (1.0 + H/5.0); }\nstatic double pseudo_integration_by_parts_index(const double coeffs[], int deg) { int altern=0; for (int k=1;k<=deg;k++) if (coeffs[k]*coeffs[k-1] < 0) altern++; double decay=0.0; for (int k=1;k<=deg;k++) decay += fabs(coeffs[k])/(1.0 + (double)k); return (double)altern + 0.1 * decay; }\n\nstruct branch_item { char *text; double value; int has_value; };\nstatic void branch_formulas(const char *expr, double H, struct branch_item out[], int branches) {\n    for (int i=0;i<branches;i++) { double offset = fmod(H * 73.0, 11.0) * (0.05 + 0.03 * i); int need = snprintf(NULL,0,\"(%s) * (1 + %.8g)\", expr, offset) + 1; char *variant = malloc(need); snprintf(variant, need, \"(%s) * (1 + %.8g)\", expr, offset); out[i].text = variant; out[i].has_value = 0; out[i].value = 0.0; const char *p = expr; while (*p==' '||*p=='\\t') p++; if ((*p>='0'&&*p<='9')||*p=='.'||*p=='+'||*p=='-') { char *end; double v = strtod(p,&end); if (end != p) { out[i].value = v * (1.0 + offset); out[i].has_value = 1; } } }\n}\nstatic int merge_branches(struct branch_item branches[], int n, double *out_mean) { double s=0.0; int cnt=0; for (int i=0;i<n;i++) if (branches[i].has_value) { s+=branches[i].value; cnt++; } if (cnt==0) return 0; *out_mean = s/(double)cnt; return 1; }\nstatic double combined_entropy_score(const double coeffs[], int deg, double H) { double z = pseudo_zeta_from_coeffs(coeffs, deg, H); double G = pseudo_gamma_indicator(coeffs, deg); double amgm = pseudo_amgm_ratio(coeffs, deg); double gdm = pseudo_global_diff_manifold(coeffs, deg, H); double gip = pseudo_integration_by_parts_index(coeffs, deg); double s1 = fabs(z) / (1.0 + fabs(z)); double s2 = log(1.0 + G) / (1.0 + log(1.0 + G)); double s3 = amgm / (1.0 + amgm); double s4 = gdm / (1.0 + gdm); double s5 = gip / (1.0 + gip); double score = 0.25*s1 + 0.20*s2 + 0.18*s3 + 0.20*s4 + 0.17*s5; if (score < 0.0) score = 0.0; if (score > 1.0) score = 1.0; return score; }\nstatic void latex_escape(const char *in, FILE *f) { for (const char *p=in; *p; ++p) { switch (*p) { case '\\\\': fputs(\"\\\\textbackslash{}\", f); break; case '_': fputs(\"\\\\_\", f); break; case '%': fputs(\"\\\\%\", f); break; case '&': fputs(\"\\\\&\", f); break; case '#': fputs(\"\\\\#\", f); break; case '{': fputs(\"\\\\{\", f); break; case '}': fputs(\"\\\\}\", f); break; case '$': fputs(\"\\\\$\", f); break; default: fputc(*p,f); break; } } }\n\nstatic int write_latex(const char *outpath, int n, char **exprs, double coeffs[MAXEXPR][MAXCOEFF], int degs[MAXEXPR], double entropies[MAXEXPR], double scores[MAXEXPR], double zetas[MAXEXPR], double gammas[MAXEXPR], double amgms[MAXEXPR], double gdm[MAXEXPR], double gip[MAXEXPR], struct branch_item branches[MAXEXPR][MAXBRANCH]) {\n    FILE *f = fopen(outpath, \"w\"); if (!f) return -1; fprintf(f, \"\\\\documentclass{article}\\n\\\\usepackage{amsmath,amssymb}\\n\\\\begin{document}\\n\"); fprintf(f, \"\\\\title{Automated entropy-driven report (omega-proof)}\\\\maketitle\\n\\n\"); for (int i=0;i<n;i++) { fprintf(f, \"\\\\section*{Expression %d}\\n\", i+1); fprintf(f, \"\\\\paragraph{Title}\\\\ \\\\newline\\n\"); latex_escape(exprs[i],f); fprintf(f, \"\\n\\n\"); fprintf(f, \"\\\\paragraph{Indicators}\\\\begin{itemize}\\n\"); fprintf(f, \"\\\\item Entropy H = %.6g\\n\", entropies[i]); fprintf(f, \"\\\\item Composite score S = %.6g\\n\", scores[i]); fprintf(f, \"\\\\item pseudo-zeta = %.6g\\n\", zetas[i]); fprintf(f, \"\\\\item pseudo-gamma = %.6g\\n\", gammas[i]); fprintf(f, \"\\\\item AM-GM ratio = %.6g\\n\", amgms[i]); fprintf(f, \"\\\\item global-diff-manifold = %.6g\\n\", gdm[i]); fprintf(f, \"\\\\item integration-by-parts-index = %.6g\\n\", gip[i]); fprintf(f, \"\\\\end{itemize}\\n\\n\"); fprintf(f, \"\\\\paragraph{Jones-like polynomial coefficients}\\\\( \"); for (int k=0;k<=degs[i];k++) { fprintf(f, \"%.6g t^{%d}\", coeffs[i][k], k); if (k<degs[i]) fprintf(f, \" + \"); } fprintf(f, \" \\\\)\\n\\n\"); fprintf(f, \"\\\\paragraph{Branches}\\\\begin{verbatim}\\n\"); for (int b=0;b<MAXBRANCH;b++) { fprintf(f, \"%s => \", branches[i][b].text); if (branches[i][b].has_value) fprintf(f, \"%.12g\\n\", branches[i][b].value); else fprintf(f, \"N/A\\n\"); } fprintf(f, \"\\\\end{verbatim}\\n\\n\\\\hrule\\n\\n\"); }\n    fprintf(f, \"\\\\end{document}\\n\"); fclose(f); return 0; }\n\nint main(int argc, char **argv) {\n    if (argc < 3) { fprintf(stderr, \"Usage: %s input.txt output.tex\\n\", argv[0]); return 2; }\n    const char *input = argv[1], *output = argv[2]; int n; char **lines = read_input(input, &n); if (!lines) { fprintf(stderr, \"Cannot read input: %s\\n\", input); return 3; } if (n==0) { fprintf(stderr, \"No expressions found\\n\"); return 4; }\n    static double coeffs[MAXEXPR][MAXCOEFF]; static int degs[MAXEXPR]; static double entropies[MAXEXPR], scores[MAXEXPR]; static double zetas[MAXEXPR], gammas[MAXEXPR], amgms[MAXEXPR], gdm[MAXEXPR], gip[MAXEXPR]; static struct branch_item branches[MAXEXPR][MAXBRANCH];\n    for (int i=0;i<n;i++) { pseudo_jones(lines[i], coeffs[i], &degs[i]); entropies[i] = coeffs_entropy(coeffs[i], degs[i]); zetas[i] = pseudo_zeta_from_coeffs(coeffs[i], degs[i], entropies[i]); gammas[i] = pseudo_gamma_indicator(coeffs[i], degs[i]); amgms[i] = pseudo_amgm_ratio(coeffs[i], degs[i]); gdm[i] = pseudo_global_diff_manifold(coeffs[i], degs[i], entropies[i]); gip[i] = pseudo_integration_by_parts_index(coeffs[i], degs[i]); scores[i] = combined_entropy_score(coeffs[i], degs[i], entropies[i]); branch_formulas(lines[i], entropies[i], branches[i], MAXBRANCH); }\n    int rc = write_latex(output, n, lines, coeffs, degs, entropies, scores, zetas, gammas, amgms, gdm, gip, branches);\n    if (rc) { fprintf(stderr, \"Failed to write LaTeX\\n\"); return 5; }\n    for (int i=0;i<n;i++) for (int b=0;b<MAXBRANCH;b++) free(branches[i][b].text);\n    for (int i=0;i<n;i++) free(lines[i]); free(lines);\n    printf(\"Wrote LaTeX: %s\\n\", output); return 0; }\n";
    snprintf(buf, sizeof(buf), "%s/bin/omega-proof-extended.c", out);
    write_file(buf, proof_c);

    // bin/omega-extract.py : Python script to extract formulas and compute simple entropy and prepare input for proof tool
    const char *extract_py =
      "#!/usr/bin/env python3\n\"\"\"\nomega-extract.py\nExtract formulas from a report text (heuristic), compute simple coefficient-entropy and write formulas one per line.\nUsage: omega-extract.py report.txt formulas.txt\n\"\"\"\nimport sys, re, math\nif len(sys.argv)<3:\n    print('Usage: omega-extract.py report.txt formulas.txt')\n    sys.exit(2)\nrep = sys.argv[1]; out = sys.argv[2]\ntext = open(rep, 'r', encoding='utf-8').read()\n# simple heuristic: capture TeX inline math $...$ and displayed \\[ ... \\] and \\begin{equation} ...\nforms = []\nforms += re.findall(r'\\$(.+?)\\$', text, flags=re.S)\nforms += re.findall(r'\\\\\\[(.+?)\\\\\\]', text, flags=re.S)\nforms += re.findall(r'\\\\begin\\{equation\\}(.+?)\\\\end\\{equation\\}', text, flags=re.S)\n# also lines that look like expressions (contain = or ** or + or -)\nfor line in text.splitlines():\n    if '=' in line or '**' in line or '+' in line or '-' in line:\n        s = line.strip()\n        if len(s)>3 and len(s)<200:\n            forms.append(s)\n# sanitize and dedupe\nseen = set(); good = []\nfor f in forms:\n    s = ' '.join(f.split())\n    if s not in seen and len(s)>0:\n        seen.add(s); good.append(s)\nopen(out,'w',encoding='utf-8').write('\\n'.join(good))\nprint('Wrote', len(good), 'formulas to', out)\n";
    snprintf(buf, sizeof(buf), "%s/bin/omega-extract.py", out);
    write_file(buf, extract_py);

    // package/src/README
    const char *pkg_readme = "Sources: runtime, lexer, parser, proof tool\nUse bin/omega-proof-extended.c and bin/omega-extract.py to extract formulas, compute indicators and generate LaTeX reports.\n";
    snprintf(buf, sizeof(buf), "%s/package/README", out);
    write_file(buf, pkg_readme);

    // etc/omega.conf
    const char *etc_conf =
      "# Omega Script configuration (generated)\nprecision=12\nproof_threshold=0.6\n";
    snprintf(buf, sizeof(buf), "%s/etc/omega.conf", out);
    write_file(buf, etc_conf);

    // usr/share/omega/README.md
    const char *usr_readme =
      "# Omega Script generated package\n\nUse bin/omega-extract.py to extract formulas from a report and bin/omega-proof-extended to generate a LaTeX report inferred from entropies and indicators.\n";
    snprintf(buf, sizeof(buf), "%s/usr/share/omega/README.md", out);
    write_file(buf, usr_readme);

    // lib placeholder
    const char *lib_placeholder = "/* lib placeholder */\n";
    snprintf(buf, sizeof(buf), "%s/lib/libomega.a", out);
    write_file(buf, lib_placeholder);

    // Makefile (robust)
    const char *makefile =
      "# Robust Makefile for Omega package\nCC := gcc\nCFLAGS := -Iinclude -O2 -std=c99\nBINDIR := bin\nSRCDIR := package/src\n\n.PHONY: all proof extract clean install\nall: proof\n\nproof:\n\t@mkdir -p $(BINDIR) 2>/dev/null || true\n\t@if [ -f \"$(BINDIR)/omega-proof-extended.c\" ]; then \\\n\t  echo \"Compiling omega-proof-extended...\"; \\\n\t  $(CC) $(CFLAGS) -o $(BINDIR)/omega-proof-extended $(BINDIR)/omega-proof-extended.c -lm 2>/dev/null || true; \\\n\telse \\\n\t  echo \"No omega-proof-extended.c found in $(BINDIR), skipping\"; \\\n\tfi\n\nextract:\n\t@chmod +x $(BINDIR)/omega-extract.py 2>/dev/null || true\n\t@echo \"extract ready\"\n\ninstall: all extract\n\t@mkdir -p $(DESTDIR)/usr/local/bin 2>/dev/null || true\n\t@cp -f $(BINDIR)/omega $(DESTDIR)/usr/local/bin/omega 2>/dev/null || true\n\t@cp -f $(BINDIR)/omega-proof-extended $(DESTDIR)/usr/local/bin/omega-proof-extended 2>/dev/null || true\n\t@cp -f $(BINDIR)/omega-extract.py $(DESTDIR)/usr/local/bin/omega-extract 2>/dev/null || true\n\t@chmod +x $(DESTDIR)/usr/local/bin/omega* 2>/dev/null || true\n\t@echo \"install complete (errors suppressed)\"\n\nclean:\n\t@-rm -f $(BINDIR)/omega-proof-extended 2>/dev/null || true\n\t@-rm -f $(BINDIR)/*.o 2>/dev/null || true\n\t@echo \"clean done\"\n";
    snprintf(buf, sizeof(buf), "%s/Makefile", out);
    write_file(buf, makefile);

    // Make extracted scripts executable (best effort)
#ifndef _WIN32
    char cmd[4096];
    snprintf(cmd, sizeof(cmd), "chmod +x \"%s/bin/omega\" \"%s/bin/omega-extract.py\" 2>/dev/null || true", out, out);
    system(cmd);
#endif

    printf("Omega package skeleton with proof/extract tools generated at: %s\n", out);
    return 0;
  }
```
