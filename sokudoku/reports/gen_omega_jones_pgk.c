要件に沿って、C 言語で「パッケージ生成器」を提供します。これをコンパイル・実行するとカレントに `omega_jones_pkg/` ディレクトリを作成し、bin、lib、include、etc、usr 等を配置します。生成物は次を含みます（教育／プロトタイプ目的の実装）：

- Omega 言語の簡易インタープリタ（C）と簡易コンパイラ（C）のソース（lib/interpreter.c、lib/compiler.c） — シンプルなスクリプトを解釈／コンパイルして内部関数を呼べる形。
- PDF 抽出ラッパ（lib/pdf_extract.c） — システムの `pdftotext` を呼ぶ簡易実装。
- Jones 多項式の数値計算（lib/jones_compute.c） — Kauffman ブラケット（状態和）に基づく数値評価（double）実装。
- テキスト→Jones-ID（SHA256 短縮）変換（lib/id_map.c）。
- レポート内方程式（テンプレート）を ID として保持し、PDF を ID 化してマッピングし、解析・QA を行う統合ロジック（lib/analysis.c）。
- 実行スクリプト (bin/run_pipeline.sh) と C ランチャ (bin/launcher.c)。
- インクルードヘッダ（include/omega_jones.h）・簡易 README 等。

注意（重要）
- ここに含む実装は教育用テンプレートです。PDF から「結び目図」や「方程式の構造化データ」を自動的に生成する高度な処理は含まず、テキスト抽出→段落分割→ハッシュによる ID 化→既知方程式テンプレートとの単純マッチングで解析／応答を行います。
- Jones 多項式の本格的・厳密多項式演算（Laurent 多項式としての厳密表示）は別途 GMP 等を使った拡張が必要ですが、本パッケージには数値評価（double）版の Kauffman 状態和実装を含みます。
- 外部依存: pdftotext（poppler-utils）、OpenSSL の libcrypto（SHA256）を想定。無ければ適宜置換してください。

使い方（生成器のビルドと実行）
1. 保存: gen_omega_jones_pkg.c
2. ビルド: gcc -O2 -std=c11 -o gen_omega_jones_pkg gen_omega_jones_pkg.c
  3. 実行: ./gen_omega_jones_pkg
  4. 生成ディレクトリ: omega_jones_pkg/
  5. パッケージで動かす:
   - cd omega_jones_pkg
   - make
   - ./bin/run_pipeline.sh path/to/document.pdf

ソースコード（gen_omega_jones_pkg.c）。この単一の C プログラムを保存してコンパイル・実行してください。

```c
     /* gen_omega_jones_pkg.c
      *
      * Generates a package 'omega_jones_pkg' with:
      *  - bin/run_pipeline.sh, bin/launcher.c
      *  - lib/pdf_extract.c
      *  - lib/jones_compute.c
      *  - lib/id_map.c
      *  - lib/analysis.c
      *  - lib/interpreter.c  (simple Omega-like interpreter stub)
      *  - lib/compiler.c     (simple Omega-like compiler stub)
      *  - include/omega_jones.h
      *  - Makefile, README
      *
      * Template / educational implementation.
      */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#if defined(_WIN32) || defined(_WIN64)
# include <direct.h>
# define MKDIR(p) _mkdir(p)
# define PATH_SEP '\\'
#else
# include <sys/stat.h>
# include <unistd.h>
# define MKDIR(p) mkdir((p), 0755)
# define PATH_SEP '/'
#endif

     static int ensure_dir(const char *p){
     int r = MKDIR(p);
     if(r==0) return 0;
     if(errno==EEXIST) return 0;
     return -1;
   }
static int write_file(const char *path, const char *data){
  FILE *f = fopen(path, "wb");
  if(!f) return -1;
  size_t n = strlen(data);
  if(fwrite(data,1,n,f) != n){ fclose(f); return -1; }
  fclose(f);
  return 0;
}

int main(void){
  const char *root = "omega_jones_pkg";
  char path[1024];

  const char *dirs[] = {"bin","lib","include","etc","usr","examples"};
  for(size_t i=0;i<sizeof(dirs)/sizeof(dirs[0]);++i){
    snprintf(path, sizeof path, "%s%c%s", root, PATH_SEP, dirs[i]);
    if(ensure_dir(path) != 0){ fprintf(stderr, "mkdir failed: %s (%s)\n", path, strerror(errno)); return 1; }
  }

  /* README */
    const char *readme =
"omega_jones_pkg\n\n"
"Educational package: Omega-like interpreter/compiler stubs, PDF extraction, Jones-ID mapping,\n"
"Jones polynomial numeric evaluator (Kauffman bracket), and analysis/QA pipeline.\n\n"
      "Build:\n  make\nRun:\n  ./bin/run_pipeline.sh path/to/doc.pdf\n\nNotes:\n  - Requires pdftotext (poppler-utils) and libcrypto (OpenSSL) for SHA256.\n  - Implementations are templates; adapt for production.\n";
    snprintf(path, sizeof path, "%s%creadme.txt", root, PATH_SEP);
    if(write_file(path, readme) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* include/omega_jones.h */
    const char *hdr =
      "/* include/omega_jones.h */\n#ifndef OMEGA_JONES_H\n#define OMEGA_JONES_H\n\n/* small API */\nint extract_text_from_pdf(const char *pdf_path, const char *out_txt_path);\nchar *text_to_jones_id(const char *text); /* caller frees */\ndouble evaluate_jones_at_t(const char *diagram_path, double t);\nchar *analyze_pdf_and_answer(const char *pdf_path, const char *question_json);\n\n#endif\n";
    snprintf(path, sizeof path, "%s%cinclude%comega_jones.h", root, PATH_SEP, PATH_SEP);
    if(write_file(path, hdr) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/pdf_extract.c */
    const char *pdf_extract =
      "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\nint extract_text_from_pdf(const char *pdf_path, const char *out_txt_path){\n    if(!pdf_path || !out_txt_path) return -1;\n    char cmd[4096];\n    /* attempt pdftotext -layout */\n    snprintf(cmd, sizeof cmd, \"pdftotext -layout '%s' '%s' 2>/dev/null\", pdf_path, out_txt_path);\n    int rc = system(cmd);\n    if(rc == 0) return 0;\n    /* fallback: write placeholder */\n    FILE *f = fopen(out_txt_path, \"w\"); if(!f) return -1;\n    fprintf(f, \"[pdf-text-unavailable:%s]\\n\", pdf_path);\n    fclose(f);\n    return 0;\n}\n";
    snprintf(path, sizeof path, "%s%clib%cpdf_extract.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, pdf_extract) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/id_map.c -- SHA256 based ID mapping (uses OpenSSL libcrypto) */
    const char *id_map =
      "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <openssl/sha.h>\n\nchar *text_to_jones_id(const char *text){\n    if(!text) return NULL;\n    unsigned char hash[SHA256_DIGEST_LENGTH];\n    SHA256((const unsigned char*)text, strlen(text), hash);\n    char *s = malloc(64+1);\n    if(!s) return NULL;\n    for(int i=0;i<16;i++) sprintf(s+2*i, \"%02x\", hash[i]);\n    s[32]=0;\n    char *out = malloc(5 + strlen(s));\n    if(!out){ free(s); return NULL; }\n    sprintf(out, \"JID-%s\", s);\n    free(s);\n    return out;\n}\n";
    snprintf(path, sizeof path, "%s%clib%cid_map.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, id_map) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/jones_compute.c -- numeric Kauffman bracket & wrapper evaluating from diagram file */
    const char *jones_compute =
      "/* lib/jones_compute.c */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <math.h>\n\ntypedef struct { int id; int e[4]; int sign; } Crossing;\n\n/* simple parser: lines 'id a b c d sign' */\nstatic int load_diagram(const char *path, Crossing **out, int *n){\n    FILE *f = fopen(path, \"r\"); if(!f) return -1;\n    int cap=16, cnt=0; Crossing *arr = malloc(sizeof(Crossing)*cap);\n    char buf[512]; while(fgets(buf,sizeof buf,f)){\n        char *s=buf; while(*s==' '||*s=='\\t') s++;\n        if(*s=='#' || *s=='\\n' || *s=='\\0') continue;\n        int id,a,b,c,d,sign; if(sscanf(s, \"%d %d %d %d %d %d\", &id,&a,&b,&c,&d,&sign)<6) continue;\n        if(cnt>=cap){ cap*=2; arr=realloc(arr,sizeof(Crossing)*cap); }\n        arr[cnt].id=id; arr[cnt].e[0]=a; arr[cnt].e[1]=b; arr[cnt].e[2]=c; arr[cnt].e[3]=d; arr[cnt].sign = (sign>=0)?1:-1; cnt++; }\n    fclose(f); *out=arr; *n=cnt; return 0;\n}\n\n/* union-find */\ntypedef struct { int p; } UF;\nstatic void uf_init(UF *u, int N){ for(int i=0;i<N;i++) u[i].p=-1; }\nstatic int uf_find(UF *u, int a){ if(u[a].p<0) return a; u[a].p = uf_find(u,u[a].p); return u[a].p; }\nstatic void uf_union(UF *u,int a,int b){ a=uf_find(u,a); b=uf_find(u,b); if(a==b) return; if(u[a].p<u[b].p){ u[a].p += u[b].p; u[b].p=a; } else { u[b].p += u[a].p; u[a].p=b; } }\n\ndouble compute_kauffman_bracket(Crossing *cross, int n, double A){\n    if(n==0) return 1.0; unsigned long long states = 1ULL<<n; double sum=0.0;\n    int maxlbl=0; for(int i=0;i<n;i++) for(int k=0;k<4;k++) if(cross[i].e[k]>maxlbl) maxlbl=cross[i].e[k]; int U=maxlbl+1;\n    UF *uf = malloc(sizeof(UF)* (U>0?U:1));\n    for(unsigned long long s=0;s<states;s++){\n        uf_init(uf, U);\n        int a_count=0,b_count=0;\n        for(int i=0;i<n;i++){\n            int bit = (s>>i)&1ULL;\n            if(bit==0){ uf_union(uf,cross[i].e[0], cross[i].e[1]); uf_union(uf,cross[i].e[2], cross[i].e[3]); a_count++; }\n            else { uf_union(uf,cross[i].e[1], cross[i].e[2]); uf_union(uf,cross[i].e[3], cross[i].e[0]); b_count++; }\n        }\n        int *seen = calloc(U, sizeof(int)); int loops=0;\n        for(int lbl=0; lbl<U; ++lbl){ int r=uf_find(uf,lbl); if(!seen[r]){ seen[r]=1; loops++; } }\n        free(seen);\n        int exp = a_count - b_count; double weight = pow(A, exp);\n        double d = -(A*A) - 1.0/(A*A);\n        double loops_factor = pow(d, (loops>0?loops-1:0));\n        sum += weight * loops_factor;\n    }\n    free(uf);\n    return sum;\n}\n\nint compute_writhe(Crossing *cross, int n){ int w=0; for(int i=0;i<n;i++) w+=cross[i].sign; return w; }\n\ndouble evaluate_jones_at_t(const char *diagram_path, double t){\n    Crossing *cs=NULL; int n=0; if(load_diagram(diagram_path,&cs,&n)!=0) return 0.0;\n    double A = pow(t, -0.25);\n    double bracket = compute_kauffman_bracket(cs, n, A);\n    int w = compute_writhe(cs, n);\n    double pref = pow(-A, -3.0 * w);\n    double V = pref * bracket;\n    free(cs);\n    return V;\n}\n";
    snprintf(path, sizeof path, "%s%clib%cjones_compute.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, jones_compute) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/analysis.c: integrate extraction, ID mapping, mapping to known equations, QA stub */
    const char *analysis =
      "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include \"../include/omega_jones.h\"\n\n/* Known equations (templates) kept here; in real use load from report */\nstatic const char *known_eqs[] = {\n    \"G_{μν}+Λ g_{μν}=κ T_{μν}\",\n    \"ζ(s)=Σ_{n=1}^∞ n^{-s}\",\n    \"L=(D_μ φ)†(D^μ φ)-V(φ)\",\n    NULL\n};\n\n/* Read extracted text, split into paragraphs, map to JIDs, and match equations by simple keyword search */\nchar *analyze_pdf_and_answer(const char *pdf_path, const char *question_json){\n    /* 1) extract text to tmp */\n    char tmpf[512]; snprintf(tmpf,sizeof tmpf, \"/tmp/ojp_%lu.txt\", (unsigned long)getpid());\n    if(extract_text_from_pdf(pdf_path, tmpf) != 0){ return strdup(\"{\\\"error\\\":\\\"extract_failed\\\"}\"); }\n    FILE *f = fopen(tmpf, \"r\"); if(!f) return strdup(\"{\\\"error\\\":\\\"open_failed\\\"}\");\n    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f,0,SEEK_SET);\n    char *buf = malloc(sz+1); fread(buf,1,sz,f); buf[sz]=0; fclose(f);\n    /* naive split on double newline */\n    char *saveptr=NULL; char *part = strtok_r(buf, \"\\n\\n\", &saveptr);\n    /* build JSON-like result */\n    char *out = malloc(8192); out[0]=0; strcat(out, \"{\\\"pdf\\\":\\\"\"); strcat(out, pdf_path); strcat(out, \"\\\", \\\"parts\\\": [\");\n    int first=1;\n    while(part){ char *trim=part; while(*trim=='\\n' || *trim=='\\r') trim++; if(*trim){ char *jid = text_to_jones_id(trim); if(!first) strcat(out, \",\"); first=0; strcat(out, \"{\\\"id\\\":\\\"\"); strcat(out, jid); strcat(out, \"\\\",\\\"matches\\\":[\");\n        /* match known eqs by simple keyword presence */\n        int mfirst=1; for(int i=0; known_eqs[i]; ++i){ if(strstr(trim, \"Einstein\") || strstr(known_eqs[i], \"G_{μν}\")){ if(!mfirst) strcat(out, \",\"); mfirst=0; strcat(out, \"\\\"Einstein\\\"\"); }\n            if(strstr(trim, \"zeta\") || strstr(known_eqs[i], \"ζ\")){ if(!mfirst) strcat(out, \",\"); mfirst=0; strcat(out, \"\\\"Zeta\\\"\"); }\n            if(strstr(trim, \"Higgs\") || strstr(known_eqs[i], \"φ\")){ if(!mfirst) strcat(out, \",\"); mfirst=0; strcat(out, \"\\\"Higgs\\\"\"); }\n        }\n        strcat(out, \"]}\"); free(jid); }\n        part = strtok_r(NULL, \"\\n\\n\", &saveptr);\n    }\n    strcat(out, \"]}\"); free(buf); remove(tmpf);\n    return out;\n}\n";
    snprintf(path, sizeof path, "%s%clib%canalysis.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, analysis) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/interpreter.c - tiny Omega-like interpreter that can call analysis API */
    const char *interpreter =
      "/* lib/interpreter.c - minimal Omega-like interpreter stub */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include \"../include/omega_jones.h\"\n\n/* very small: accept command 'analyze <pdf>' and print JSON answer */\nint omega_interpret(const char *script){\n    if(!script) return -1;\n    /* parse simple tokenization */\n    char cmd[1024]; char arg[1024]; if(sscanf(script, \"%s %s\", cmd, arg) < 1) return -1;\n    if(strcmp(cmd, \"analyze\") == 0){ char *res = analyze_pdf_and_answer(arg, NULL); if(res){ printf(\"%s\\n\", res); free(res); return 0; } return 2; }\n    if(strcmp(cmd, \"help\") == 0){ printf(\"Usage: analyze <pdf_path>\\n\"); return 0; }\n    printf(\"Unknown command\\n\"); return -1;\n}\n";
    snprintf(path, sizeof path, "%s%clib%cinterpreter.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, interpreter) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/compiler.c - simple transpiler: converts a tiny Omega script to a C stub that calls interpreter API (template) */ 
    const char *compiler =
      "/* lib/compiler.c - tiny 'compiler' stub: writes a C program that calls omega_interpret with given script */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\nint omega_compile_to_c(const char *script, const char *out_c_path){\n    FILE *f = fopen(out_c_path, \"w\"); if(!f) return -1;\n    fprintf(f, \"#include <stdio.h>\\n#include <stdlib.h>\\n#include \\\"../include/omega_jones.h\\\"\\nextern int omega_interpret(const char*);\\nint main(){ omega_interpret(\\\"%s\\\"); return 0; }\\n\", script);\n    fclose(f); return 0;\n}\n";
    snprintf(path, sizeof path, "%s%clib%ccompiler.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, compiler) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* bin/launcher.c - build and run pipeline: interpreter + analysis example */
    const char *launcher =
      "#include <stdio.h>\n#include <stdlib.h>\nint main(int argc, char **argv){\n    if(argc<2){ fprintf(stderr, \"Usage: %s <pdf>\\n\", argv[0]); return 1; }\n    char cmd[4096]; snprintf(cmd, sizeof cmd, \"./lib/interpreter_bin analyze %s\", argv[1]); return system(cmd);\n}\n";
    snprintf(path, sizeof path, "%s% cbin%clauncher.c", root, PATH_SEP, PATH_SEP); /* fix next */ 
    snprintf(path, sizeof path, "%s%cbin%clauncher.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, launcher) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/interpreter_bin.c - link-time: small main that uses interpreter API directly (build target) */
    const char *interpreter_bin =
      "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include \"../include/omega_jones.h\"\nint omega_interpret(const char*);\nint main(int argc, char **argv){\n    if(argc<2){ fprintf(stderr, \"Usage: %s <command> [arg]\\n\", argv[0]); return 1; }\n    char script[1024]; if(argc==2) snprintf(script,sizeof script, \"%s %s\", argv[1], argv[1]); /* placeholder */\n    /* For convenience, support: interpreter_bin analyze <pdf> */\n    if(argc>=3){ snprintf(script, sizeof script, \"%s %s\", argv[1], argv[2]); }\n    else { snprintf(script, sizeof script, \"%s\", argv[1]); }\n    return omega_interpret(script);\n}\n";
    snprintf(path, sizeof path, "%s%clib%cinterpreter_bin.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, interpreter_bin) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* examples/sample.pdf placeholder note and sample diagram for Jones evaluator */
    const char *example_note =
      "# Place your PDF at examples/sample.pdf\n# Example diagram for Jones evaluator (text format) in examples/diagram.txt\n";
    snprintf(path, sizeof path, "%s%cexamples%cREADME.txt", root, PATH_SEP, PATH_SEP);
    if(write_file(path, example_note) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    const char *example_diagram =
      "# simple 3-crossing example\n0 1 2 3 4 1\n1 3 4 5 6 1\n2 5 6 1 2 1\n";
    snprintf(path, sizeof path, "%s%cexamples%cdiagram.txt", root, PATH_SEP, PATH_SEP);
    if(write_file(path, example_diagram) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* Makefile */
    const char *makefile =
      "CC=gcc\nCFLAGS=-O2 -Iinclude\nLDFLAGS=-lcrypto -lm\n\nall: lib/interpreter_bin bin/launcher lib/jones_cli\n\nlib/id_map.o: lib/id_map.c\n\t$(CC) $(CFLAGS) -c -o lib/id_map.o lib/id_map.c\n\nlib/jones_compute.o: lib/jones_compute.c\n\t$(CC) $(CFLAGS) -c -o lib/jones_compute.o lib/jones_compute.c\n\nlib/analysis.o: lib/analysis.c lib/id_map.c lib/pdf_extract.c lib/jones_compute.c\n\t$(CC) $(CFLAGS) -c -o lib/analysis.o lib/analysis.c\n\nlib/interpreter.o: lib/interpreter.c lib/analysis.c lib/id_map.c lib/pdf_extract.c\n\t$(CC) $(CFLAGS) -c -o lib/interpreter.o lib/interpreter.c\n\nlib/interpreter_bin: lib/interpreter_bin.c lib/interpreter.o lib/analysis.o lib/id_map.o lib/jones_compute.o\n\t$(CC) $(CFLAGS) -o lib/interpreter_bin lib/interpreter_bin.c lib/interpreter.o lib/analysis.o lib/id_map.o lib/jones_compute.o $(LDFLAGS)\n\nbin/launcher: bin/launcher.c\n\t$(CC) $(CFLAGS) -o bin/launcher bin/launcher.c\n\nlib/jones_cli: lib/jones_cli.c lib/jones_compute.o\n\t$(CC) $(CFLAGS) -o bin/jones_cli lib/jones_cli.c lib/jones_compute.o -lm\n\nclean:\n\trm -f lib/*.o lib/interpreter_bin bin/launcher bin/jones_cli\n";
    snprintf(path, sizeof path, "%s%cMakefile", root, PATH_SEP);
    if(write_file(path, makefile) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* lib/jones_cli.c wrapper to call evaluate_jones_at_t from lib/jones_compute.c */
    const char *jones_cli =
      "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include \"../include/omega_jones.h\"\n\nextern double evaluate_jones_at_t(const char*, double);\nint main(int argc, char **argv){ if(argc<2){ fprintf(stderr,\"Usage: %s diagram.txt [t]\\n\",argv[0]); return 1;} double t=1.0; if(argc>=3) t=atof(argv[2]); double v=evaluate_jones_at_t(argv[1], t); printf(\"V(t) at t=%g : %g\\n\", t, v); return 0; }\n";
    snprintf(path, sizeof path, "%s%clib%cjones_cli.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, jones_cli) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }

    /* bin/run_pipeline.sh */
    const char *runsh =
      "#!/bin/sh\nset -e\nROOT=$(cd \"$(dirname \"$0\")/..\" && pwd)\ncd \"$ROOT\"\nmake\nif [ -z \"$1\" ]; then echo \"Usage: $0 <pdf>\"; exit 1; fi\nPDF=\"$1\"\n# 1) extract text\nTMP=/tmp/ojp_$$.txt\n$ROOT/lib/interpreter_bin analyze \"$PDF\" || true\n# Alternatively run launcher\n$ROOT/bin/launcher \"$PDF\"\n";
    snprintf(path, sizeof path, "%s%cbin%crun_pipeline.sh", root, PATH_SEP, PATH_SEP);
    if(write_file(path, runsh) != 0){ fprintf(stderr, "write failed: %s\n", path); return 1; }
#if !defined(_WIN32) && !defined(_WIN64)
    chmod(path, 0755);
#endif

    printf("Package '%s' created.\n", root);
    printf("To build and run:\n  cd %s\n  make\n  ./bin/run_pipeline.sh path/to/document.pdf\n", root);
    return 0;
}
```

補足（短く）
- 生成される C ソース群は教育的テンプレートです。必要なら各ファイル（lib/jones_compute.c、lib/analysis.c、lib/interpreter.c など）の詳細説明、または Jones 多項式の厳密多項式出力（GMP ベースで係数を Laurent 多項式として扱う実装）を次に追加します。どれを先に出しますか？
