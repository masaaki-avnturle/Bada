以下は、要求どおり「(3) PDF→テキスト自動化（pdftotext 呼び出し統合）」と「(4) LaTeX での定理環境自動生成」を組み込んだ単一ファイルの C ジェネレータ `pkginstallgen.c` です。これをコンパイルして実行すると、作業ディレクトリに `omega_report_pkg/` が生成され、中にビルド可能な `usr/lang/omegascript`（C ソース）が作られます。生成された `omegascript` は：

- reports/ にある PDF を自動で `pdftotext` によってテキスト化（--pdf2txt オプション）して `.txt` を作成
- テキストファイル群を解析し、題名・定理（"Theorem"/"定理"など）・数式行・証明・結論を抽出
- 抽出した定理を LaTeX の theorem 環境（\begin{theorem}...\end{theorem}）として出力
- --advanced を使うと n-gram エントロピー、Jones/ζ 指標、zeta 部分和等の高度指標を計算して LaTeX と JSON に出力

使い方（簡潔）
1. ビルド generator:
   gcc -O2 -std=c11 -Wall -o pkginstallgen pkginstallgen.c
  2. 生成パッケージ:
   ./pkginstallgen
  3. パッケージへ移動してビルド:
   cd omega_report_pkg
   make
  4. レポートを置く:
  - 元が PDF の場合: put PDFs in `reports/`
   - 既にテキストなら `.txt` を置く
  5. PDF を自動でテキスト化して高度解析:
   ./usr/lang/omegascript analyze --advanced --pdf2txt reports output/paper.tex
  生成: `output/paper.tex` と `output/paper.tex.summary.json`

  重要: PDF→テキスト変換には外部ツール `pdftotext`（poppler または xpdf 等）が必要。システムに無い場合は `--pdf2txt` を省いてください。

ファイル：pkginstallgen.c
```c
  /*
   * pkginstallgen.c
   *
   * Generate omega_report_pkg with:
   *  - omegascript C runtime supporting:
   *      * PDF->text conversion using pdftotext (--pdf2txt)
   *      * analyze --advanced: extracts title/theorems/formulas/proofs/conclusions
   *      * wraps extracted theorems into LaTeX theorem environments
   *      * advanced metrics (n-gram entropies, Jones/zeta heuristics)
   *
   * Build:
   *   gcc -O2 -std=c11 -Wall -o pkginstallgen pkginstallgen.c
   * Run:
   *   ./pkginstallgen
   *
   * Then:
   *   cd omega_report_pkg
   *   make
   *   # place PDFs or .txt into reports/
   *   ./usr/lang/omegascript analyze --advanced --pdf2txt reports output/paper.tex
   *
   * Note: pdftotext must be installed for --pdf2txt to work.
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
    tmp[sizeof(tmp)-1] = 0;
    char *p = strrchr(tmp, '/');
    if (p && p != tmp) { *p = 0; if (ensure_dir(tmp) == 0) return mkdir(path, 0755) == 0 ? 0 : -1; }
  }
  return -1;
}

static int write_file(const char *path, const char *data, int mode) {
  char dir[4096];
  strncpy(dir, path, sizeof(dir)-1); dir[sizeof(dir)-1]=0;
  char *p = strrchr(dir, '/');
  if (p) { *p = 0; ensure_dir(dir); }
  FILE *f = fopen(path, "wb");
  if (!f) { fprintf(stderr, "open %s: %s\n", path, strerror(errno)); return -1; }
  if (data && fputs(data, f) == EOF) { fclose(f); return -1; }
  fclose(f);
  if (mode) chmod(path, (mode_t)mode);
  return 0;
}

int main(void) {
  const char *root = "omega_report_pkg";
  if (ensure_dir(root) != 0) { fprintf(stderr, "cannot create %s\n", root); return 1; }

  write_file("omega_report_pkg/README.md",
"# omega_report_pkg (PDF->text + theorem env + advanced metrics)\n\n"
"This package provides an omegascript analyzer that can convert PDFs to text (pdftotext) and\n"
"generate LaTeX papers with extracted theorem environments and advanced heuristic metrics.\n\n"
	     "Usage summary:\n  cd omega_report_pkg\n  make\n  # place reports (PDF or .txt) into reports/\n  ./usr/lang/omegascript analyze --advanced --pdf2txt reports output/paper.tex\n", 0644);

  write_file("omega_report_pkg/Makefile",
	     "CC ?= gcc\nCFLAGS ?= -O2 -std=c11 -Wall -Wextra\nUSR_LANG = usr/lang\nOMEGA_C = $(USR_LANG)/omegascript.c\nOMEGA_BIN = $(USR_LANG)/omegascript\n.PHONY: all clean\nall: $(OMEGA_BIN)\n$(OMEGA_BIN): $(OMEGA_C)\n\t@mkdir -p $(USR_LANG)\n\t$(CC) $(CFLAGS) -o $@ $<\n\t@printf \"built: %s\\n\" \"$@\"\nclean:\n\t-@rm -f $(OMEGA_BIN)\n", 0644);

  write_file("omega_report_pkg/config.ru",
	     "require 'rack'; require 'erb'\nclass App; def call(env)\n req=Rack::Request.new(env); if req.path_info=='/'\n  [200,{'Content-Type'=>'text/html'}, [ERB.new(File.read('app/views/home/index.html.erb')).result(binding)]]\n else [404,{'Content-Type'=>'text/plain'},['Not Found']] end; end; end; run App.new\n", 0644);

  ensure_dir("omega_report_pkg/app/views");
  write_file("omega_report_pkg/app/views/home/index.html.erb",
	     "<!doctype html><html><head><meta charset='utf-8'><title>Omega Report</title></head><body>\n<h1>Omega Report - Analyzer</h1>\n<p>Use ./usr/lang/omegascript analyze --advanced --pdf2txt reports output/paper.tex</p>\n</body></html>\n", 0644);

  ensure_dir("omega_report_pkg/usr/lang");

  /* omegascript.c with PDF->text integration and theorem environment generation */
  write_file("omega_report_pkg/usr/lang/omegascript.c",
	     "/* omegascript.c\n * analyze [--advanced] [--pdf2txt] <reports_dir> <out_tex> [--zeta-s S]\n * - --pdf2txt : convert PDFs in reports_dir to text via pdftotext\n * - extracts theorem blocks and wraps them in LaTeX theorem envs\n * - advanced metrics similar to earlier version\n */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <dirent.h>\n#include <ctype.h>\n#include <math.h>\n#include <sys/stat.h>\n\nstatic char *read_file(const char *path){ FILE*f=fopen(path,\"rb\"); if(!f) return NULL; fseek(f,0,SEEK_END); long s=ftell(f); fseek(f,0,SEEK_SET); char*b=malloc(s+1); if(!b){fclose(f);return NULL;} if(fread(b,1,s,f)!=(size_t)s){free(b);fclose(f);return NULL;} b[s]='\\0'; fclose(f); return b; }\nstatic void ensure_dir(const char *p){ struct stat st; if(stat(p,&st)!=0) mkdir(p,0755); }\n\n/* run pdftotext on all PDFs in dir (creates .txt alongside) */\nstatic void pdf_to_text(const char *dir){ DIR *d=opendir(dir); if(!d){fprintf(stderr,\"cannot open %s\\n\",dir); return;} struct dirent *e; char cmd[1024]; while((e=readdir(d))){ if(e->d_type==DT_REG){ const char*n=e->d_name; size_t L=strlen(n); if(L>4 && strcasecmp(n+L-4,\".pdf\")==0){ char src[1024]; snprintf(src,sizeof(src),\"%s/%s\",dir,n); char dst[1024]; strncpy(dst,src,sizeof(dst)); dst[sizeof(dst)-1]=0; /* pdftotext auto writes .txt */ snprintf(cmd,sizeof(cmd),\"pdftotext '%s' '%s.txt' 2>/dev/null\", src, src); system(cmd); } } } closedir(d); }\n\n/* simple tokenization */\nstatic char **tokenize(const char *s,int *cnt){ int cap=256; char**a=malloc(sizeof(char*)*cap); int n=0; const char*p=s; while(*p){ while(*p && !isalnum((unsigned char)*p)) p++; if(!*p) break; const char*q=p; while(*q && isalnum((unsigned char)*q)) q++; int L=q-p; char*t=malloc(L+1); memcpy(t,p,L); t[L]='\\0'; if(n>=cap){cap*=2; a=realloc(a,sizeof(char*)*cap);} a[n++]=t; p=q; } *cnt=n; return a; }\nstatic double shannon_entropy(char**tokens,int n){ if(n<=0) return 0.0; int unique=0; char**uniq=malloc(sizeof(char*)*n); int*cnt=calloc(n,sizeof(int)); for(int i=0;i<n;i++){ int f=-1; for(int j=0;j<unique;j++) if(strcasecmp(tokens[i],uniq[j])==0){f=j;break;} if(f==-1){ uniq[unique]=strdup(tokens[i]); cnt[unique]=1; unique++; } else cnt[f]++; } double H=0.0; for(int i=0;i<unique;i++){ double p=(double)cnt[i]/(double)n; if(p>0) H -= p*log(p)/log(2.0); free(uniq[i]); } free(uniq); free(cnt); return H; }\n\n/* detect theorem-like lines and collect block until blank or next header */\nstatic void extract_theorems_and_sections(const char *text, char *theorems, size_t thcap, char *proofs, size_t pcap, char *formulas, size_t fcap, char *conclusions, size_t ccap){ const char *p=text; char line[4096]; int in_proof=0; while(*p){ /* read line */ const char *nl = strchr(p,'\\n'); size_t L = nl ? (size_t)(nl-p) : strlen(p); if(L >= sizeof(line)) L = sizeof(line)-1; memcpy(line,p,L); line[L]='\\0'; p = nl ? nl+1 : p+L; /* trim */ const char* s=line; while(*s && isspace((unsigned char)*s)) s++; if(*s==0){ in_proof=0; continue; }\n        if (strcasestr(s,\"Theorem\") || strchr(s,'定') || strstr(s,\"主張\")){\n            /* append as theorem environment */\n            strncat(theorems, \"\\\\begin{theorem}\\n\", thcap-strlen(theorems)-1);\n            strncat(theorems, s, thcap-strlen(theorems)-1);\n            strncat(theorems, \"\\\\end{theorem}\\n\\n\", thcap-strlen(theorems)-1);\n            continue;\n        }\n        if (strcasestr(s,\"Proof\") || strstr(s,\"証明\")){\n            in_proof=1; strncat(proofs, s, pcap-strlen(proofs)-1); strncat(proofs, \"\\n\", pcap-strlen(proofs)-1); continue; }\n        if (in_proof){ strncat(proofs, s, pcap-strlen(proofs)-1); strncat(proofs, \"\\n\", pcap-strlen(proofs)-1); continue; }\n        if (strcasestr(s,\"Conclusion\") || strstr(s,\"結論\") || strstr(s,\"まとめ\")){\n            strncat(conclusions, s, ccap-strlen(conclusions)-1); strncat(conclusions, \"\\n\", ccap-strlen(conclusions)-1); continue;\n        }\n        /* formulas: lines containing '=', '\\\\', '∫', 'ζ', '^' or many math chars */\n        if (strpbrk(s,\"=^\\\\∫ζΓπΣψλ\")) { strncat(formulas, s, fcap-strlen(formulas)-1); strncat(formulas, \"\\n\", fcap-strlen(formulas)-1); }\n    }\n}\n\n/* polynomial degree heuristics (scan '^number' occurrences) */\nstatic void poly_stats(const char *text,int *maxdeg,double *avgdeg){ *maxdeg=0; *avgdeg=0.0; int cnt=0; const char*p=text; while((p=strchr(p,'^'))){ p++; int val=0, read=0; while(isdigit((unsigned char)*p)){ val = val*10 + (*p - '0'); p++; read=1; } if(read){ if(val>*maxdeg) *maxdeg=val; *avgdeg += val; cnt++; } }\n if(cnt>0) *avgdeg/=cnt; }\n\n/* zeta partial sum (moderate N to keep runtime small) */\nstatic double zeta_partial(double s,int N){ if(s<=0) s=0.5; if(N<=0) N=10000; double sum=0.0; for(int n=1;n<=N;n++) sum += 1.0 / pow((double)n, s); return sum; }\n\nstatic void analyze_dir(const char *dir,const char *out_tex,int advanced,int do_pdf2txt,double zeta_s){ if(do_pdf2txt) pdf_to_text(dir);\n    DIR *d=opendir(dir); if(!d){ fprintf(stderr,\"cannot open %s\\n\",dir); return; }\n    ensure_dir(\"output\"); FILE *tex=fopen(out_tex,\"wb\"); if(!tex){ fprintf(stderr,\"cannot open %s\\n\",out_tex); closedir(d); return; }\n    char jsonpath[1024]; snprintf(jsonpath,sizeof(jsonpath),\"%s.summary.json\",out_tex); FILE *json=fopen(jsonpath,\"wb\"); if(!json){ fprintf(stderr,\"cannot open %s\\n\",jsonpath); fclose(tex); closedir(d); return; }\n    struct dirent *ent; int any=0; size_t cap=1<<20; char *all=malloc(cap); all[0]='\\0'; size_t len=0;\n    while((ent=readdir(d))){ if(ent->d_type==DT_REG){ const char*n=ent->d_name; size_t L=strlen(n); if(L>4 && strcasecmp(n+L-4,\".txt\")==0){ char path[1024]; snprintf(path,sizeof(path),\"%s/%s\",dir,n); char *t=read_file(path); if(!t) continue; any=1; size_t need=len+strlen(t)+128; if(need>cap){ cap = need*2; all=realloc(all,cap);} strcat(all,\"\\n==== FILE: \"); strcat(all,n); strcat(all,\" ====\\n\"); strcat(all,t); len=strlen(all); free(t); } } }\n    if(!any) fprintf(stderr,\"no .txt reports found in %s\\n\",dir);\n\n    /* extract sections */\n    char theorems[16384]; theorems[0]='\\0'; char proofs[16384]; proofs[0]='\\0'; char formulas[16384]; formulas[0]='\\0'; char conclusions[8192]; conclusions[0]='\\0';\n    extract_theorems_and_sections(all, theorems, sizeof(theorems), proofs, sizeof(proofs), formulas, sizeof(formulas), conclusions, sizeof(conclusions));\n\n    /* tokens */ int tn=0; char **toks = NULL; toks = NULL; toks = NULL; toks = (char**)malloc(sizeof(char*)); /* placeholder */\n    /* reuse earlier tokenizer */ int tmpn=0; char **tmp = NULL; tmp = (char**)malloc(1); tmpn=0; /* we'll call tokenize by copying function locally */\n    /* simple tokenization inline */ {\n        int cap2=256; char **a=malloc(sizeof(char*)*cap2); int n=0; const char *p=all; while(*p){ while(*p && !isalnum((unsigned char)*p)) p++; if(!*p) break; const char*q=p; while(*q && isalnum((unsigned char)*q)) q++; int L=q-p; char *t=malloc(L+1); memcpy(t,p,L); t[L]='\\0'; if(n>=cap2){ cap2*=2; a=realloc(a,sizeof(char*)*cap2);} a[n++]=t; p=q; } tmp=a; tmpn=n; }\n    double H_tokens = shannon_entropy(tmp, tmpn);\n\n    /* advanced metrics */\n    double H_c1=0,H_c2=0,H_c3=0; int jones_kw=0,zeta_kw=0; int poly_max=0; double poly_avg=0.0; double zeta_val=0.0;\n    if (advanced) {\n        /* char n-gram entropies */\n        /* implement small ngram entropy: reuse simple routines */\n        /* H1,H2,H3 approximations: count distinct n-grams */\n        size_t L = strlen(all);\n        /* H1 */ { int map[256]={0}; int total=0; for(size_t i=0;i<L;i++){ unsigned char c=(unsigned char)all[i]; if(isprint(c)){ map[c]++; total++; } } double H=0.0; for(int i=0;i<256;i++) if(map[i]){ double p=(double)map[i]/(double)total; H -= p*log(p)/log(2.0); } H_c1=H; }\n        /* H2,H3 crude */ { int cap=100003; /* hash table for bigrams/trigrams via simple linear probing */\n            char *buf = all; int total2=0; /* bigrams */\n            /* bigrams */ { unsigned long *keys = calloc(cap,sizeof(unsigned long)); int *cnt = calloc(cap,sizeof(int)); for(size_t i=0;i+1<L;i++){ if(!isprint((unsigned char)buf[i])||!isprint((unsigned char)buf[i+1])) continue; unsigned long k = ((unsigned long)(unsigned char)buf[i]<<8) | (unsigned char)buf[i+1]; unsigned long h = (k*11400714819323198485UL) % cap; while(keys[h] && keys[h]!=k) { h=(h+1)%cap; } keys[h]=k; cnt[h]++; total2++; } double H=0.0; for(int i=0;i<cap;i++) if(cnt[i]){ double p=(double)cnt[i]/(double)total2; H -= p*log(p)/log(2.0); } H_c2=H; free(keys); free(cnt); }\n            /* trigrams */ { unsigned long *keys = calloc(200003,sizeof(unsigned long)); int *cnt = calloc(200003,sizeof(int)); int cap3=200003; int total3=0; for(size_t i=0;i+2<L;i++){ if(!isprint((unsigned char)buf[i])||!isprint((unsigned char)buf[i+1])||!isprint((unsigned char)buf[i+2])) continue; unsigned long k = ((unsigned long)(unsigned char)buf[i]<<16) | ((unsigned long)(unsigned char)buf[i+1]<<8) | (unsigned char)buf[i+2]; unsigned long h = (k*11400714819323198485UL) % cap3; while(keys[h] && keys[h]!=k) h=(h+1)%cap3; keys[h]=k; cnt[h]++; total3++; } double H=0.0; for(int i=0;i<cap3;i++) if(cnt[i]){ double p=(double)cnt[i]/(double)total3; H -= p*log(p)/log(2.0); } H_c3=H; free(keys); free(cnt); }\n        /* keyword counts */ for(int i=0;i<tmpn;i++){ if(strcasestr(tmp[i],\"jones\")||strcasestr(tmp[i],\"knot\")) jones_kw++; if(strcasestr(tmp[i],\"zeta\")||strcasestr(tmp[i],\"ζ\")) zeta_kw++; }\n        poly_stats(all, &poly_max, &poly_avg);\n        zeta_val = zeta_partial(zeta_s, 20000);\n    }\n\n    /* heuristics and LaTeX output */\n    /* combined scores (simple) */\n    double jones_score = (jones_kw>0)? (1.0 - exp(-0.6 * jones_kw)) * ( (poly_max>0)? (0.5 + 0.5*(poly_avg/(poly_max+1e-9))) : 0.5) : 0.0;\n    if (jones_score>1.0) jones_score=1.0;\n    double zeta_score = (zeta_kw>0)? (1.0 - exp(-0.6 * zeta_kw)) * (1.0 - exp(-fabs(zeta_val)/100.0)) : 0.0; if(zeta_score>1.0) zeta_score=1.0;\n    double ent_norm = H_tokens/12.0; if(ent_norm>1.0) ent_norm=1.0;\n    double ngram_norm = (H_c1 + H_c2 + H_c3)/30.0; if(ngram_norm>1.0) ngram_norm=1.0;\n    double combined = 0.4*ent_norm + 0.2*ngram_norm + 0.2*jones_score + 0.2*zeta_score; if(combined>1.0) combined=1.0;\n\n    /* write LaTeX with theorem envs */\n    fprintf(tex, \"\\\\documentclass{article}\\\\n\\\\usepackage{amsmath,amsthm,amssymb}\\\\n\\\\begin{document}\\\\n\");\n    fprintf(tex, \"\\\\title{Generated Report}\\\\maketitle\\\\n\");\n    if(theorems[0]){ fprintf(tex, \"\\\\section{Extracted Theorems}\\\\n%s\\\\n\", theorems); }\n    if(formulas[0]){ fprintf(tex, \"\\\\section{Formulas}\\\\n\\\\begin{verbatim}\\\\n%s\\\\n\\\\end{verbatim}\\\\n\", formulas); }\n    if(proofs[0]){ fprintf(tex, \"\\\\section{Proofs}\\\\n\\\\begin{verbatim}\\\\n%s\\\\n\\\\end{verbatim}\\\\n\", proofs); }\n    if(conclusions[0]){ fprintf(tex, \"\\\\section{Conclusion}\\\\n%s\\\\n\", conclusions); }\n    if(advanced){ fprintf(tex, \"\\\\section{Advanced Evaluation}\\\\n\\\\begin{itemize}\\\\n\");\n        fprintf(tex, \"\\\\item Token Shannon entropy: %.6f bits\\\\n\", H_tokens);\n        fprintf(tex, \"\\\\item Char n-gram entropies: H1=%.4f H2=%.4f H3=%.4f\\\\n\", H_c1, H_c2, H_c3);\n        fprintf(tex, \"\\\\item Jones keywords: %d, poly max=%d avg=%.3f score=%.4f\\\\n\", jones_kw, poly_max, poly_avg, jones_score);\n        fprintf(tex, \"\\\\item Zeta keywords: %d, zeta(s=%.3f) partial=%g score=%.4f\\\\n\", zeta_kw, zeta_s, zeta_val, zeta_score);\n        fprintf(tex, \"\\\\item Combined heuristic validity: %.4f\\\\n\", combined);\n        fprintf(tex, \"\\\\end{itemize}\\\\n\"); }\n    fprintf(tex, \"\\\\end{document}\\\\n\");\n\n    /* JSON summary */\n    fprintf(json, \"{\\n  \\\"token_count\\\": %d,\\n  \\\"token_entropy\\\": %.6f,\\n\", tmpn, H_tokens);\n    fprintf(json, \"  \\\"ngram\\\": {\\\"H1\\\": %.6f, \\\"H2\\\": %.6f, \\\"H3\\\": %.6f},\\n\", H_c1, H_c2, H_c3);\n    fprintf(json, \"  \\\"jones_kw\\\": %d, \\\"poly_max\\\": %d, \\\"poly_avg\\\": %.6f, \\\"jones_score\\\": %.6f,\\n\", jones_kw, poly_max, poly_avg, jones_score);\n    fprintf(json, \"  \\\"zeta_kw\\\": %d, \\\"zeta_s\\\": %.6f, \\\"zeta_partial\\\": %.6f, \\\"zeta_score\\\": %.6f,\\n\", zeta_kw, zeta_s, zeta_val, zeta_score);\n    fprintf(json, \"  \\\"combined_validity\\\": %.6f\\n}\\n\", combined);\n\n    /* cleanup */ for(int i=0;i<tmpn;i++) free(tmp[i]); free(tmp); free(all); fclose(tex); fclose(json); closedir(d);\n    printf(\"Wrote %s and %s\\n\", out_tex, jsonpath);\n}\n\nint main(int argc,char **argv){ if(argc<2){ fprintf(stderr,\"Usage: %s analyze [--advanced] [--pdf2txt] <reports_dir> <out_tex> [--zeta-s S]\\n\", argv[0]); return 1; }\n    if(strcmp(argv[1],\"analyze\")==0){ int advanced=0, pdf2txt=0; double zeta_s=0.5; int idx=2; if(argc>2 && strcmp(argv[2],\"--advanced\")==0){ advanced=1; idx=3; } if(argc>idx && strcmp(argv[idx],\"--pdf2txt\")==0){ pdf2txt=1; idx++; }\n        if(argc<=idx){ fprintf(stderr,\"need args\\n\"); return 1; }\n        const char *dir = argv[idx++]; const char *out = (idx<argc)?argv[idx++]:\"output/paper.tex\";\n        for(int i=idx;i<argc;i++){ if(strcmp(argv[i],\"--zeta-s\")==0 && i+1<argc) zeta_s = atof(argv[i+1]); }\n        analyze_dir(dir, out, advanced, pdf2txt, zeta_s); return 0; }\n    fprintf(stderr,\"unknown command\\n\"); return 2; }\n", 0644);

  ensure_dir("omega_report_pkg/reports");
  write_file("omega_report_pkg/reports/README.txt",
	     "Place PDFs or .txt into reports/. To convert PDFs automatically, ensure `pdftotext` is installed and run:\n  ./usr/lang/omegascript analyze --advanced --pdf2txt reports output/paper.tex\n", 0644);

  write_file("omega_report_pkg/run_all.sh",
	     "#!/usr/bin/env bash\nset -euo pipefail\nmake\nif [ ! -d reports ] || [ -z \"$(ls -A reports)\" ]; then echo \"Place PDFs or .txt in reports/\"; exit 1; fi\n./usr/lang/omegascript analyze --advanced --pdf2txt reports output/paper.tex\n", 0755);

  printf(\"omega_report_pkg generated. cd omega_report_pkg && make to build omegascript.\\n\");
  return 0;
}
```

必要なら今回の生成物をさらに
- pdftotext が無い場合のフォールバック（Poppler インストール案内自動出力）
- LaTeX に theorem numbering, environments style（amsthm 設定）や BibTeX 自動生成
- Jones 多項式のより精密な構文抽出（正規表現強化）や、外部 knot ライブラリとの連携
などで拡張できます。どれを優先しますか？
