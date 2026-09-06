以下は要求どおり、単一のCプログラム（pkginstallgen.c相当）です。実行するとディレクトリ `omega_zeta_infer/src/` に、（1）レポートテキストから意味の通る文章を生成する簡易テンプレートエンジン、（2）生成された文章から類推して数式（数学的表現）を組み立てる簡易ルールベースの式合成器、（3）デモ実行プログラム、Makefile を出力します。すべてCで完結する「ジェネレータ」です。先のジェネレータと同様にレポートのテキストを omega_zeta_infer/explorerfiles.txt に置いてください。

保存名: pkginstallgen.c

コンパイル・実行例:
gcc -O2 -std=c11 -o pkginstallgen pkginstallgen.c
./pkginstallgen
# 出力先にレポートを置く:
# pdftotext explorerfiles.pdf omega_zeta_infer/explorerfiles.txt
cd omega_zeta_infer/src && make
./omega_zeta_infer_demo

  ソースコード（そのまま保存してコンパイルしてください）:

```c
  // pkginstallgen.c
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>
#include <time.h>

  static int mkdir_p(const char *path){
  char tmp[4096]; char *p; size_t len;
  if(!path || !*path) return -1;
  snprintf(tmp,sizeof(tmp),"%s",path);
  len=strlen(tmp);
  if(tmp[len-1]=='/') tmp[len-1]=0;
  for(p=tmp+1; *p; ++p) if(*p=='/'){ *p=0; if(mkdir(tmp,0755)!=0 && errno!=EEXIST) return -1; *p='/'; }
  if(mkdir(tmp,0755)!=0 && errno!=EEXIST) return -1;
  return 0;
}

static int write_file(const char *path, const char *content){
  const char *last = strrchr(path,'/');
  if(last){
    char dir[4096]; size_t n = last - path;
    if(n>=sizeof(dir)) return -1;
    memcpy(dir,path,n); dir[n]=0;
    if(mkdir_p(dir)!=0){ fprintf(stderr,"mkdir_p failed for %s\n",dir); return -1; }
  }
  FILE *f = fopen(path,"w"); if(!f){ perror(path); return -1; }
  fputs(content,f); fclose(f); return 0;
}

/* Simple helpers for tokenization */
static char *slurp(const char *path){
  FILE *f = fopen(path,"r"); if(!f) return NULL;
  fseek(f,0,SEEK_END); long s = ftell(f); fseek(f,0,SEEK_SET);
  char *b = malloc(s+1); if(!b){ fclose(f); return NULL; }
  fread(b,1,s,f); b[s]=0; fclose(f); return b;
}

/* Main generator */
int main(void){
  srand((unsigned)time(NULL));
  if(mkdir_p("omega_zeta_infer/src")!=0){ fprintf(stderr,"mkdir create failed\n"); return 1; }

  /* Header: interfaces for text+formula generator */
  write_file("omega_zeta_infer/src/infer.h",
"// infer.h: minimal interfaces for text and formula generation\n"
	     "#ifndef INFER_H\n#define INFER_H\n#include <stddef.h>\nchar* generate_meaningful_sentence(const char *report_text);\nchar* generate_equation_from_sentence(const char *sentence);\nvoid free_str(char *s);\n#endif\n");

  /* Implementation: rule-based extraction + templates */
  write_file("omega_zeta_infer/src/infer.c",
"// infer.c: simple rule-based text generator and formula synthesizer\n"
	     "#include \"infer.h\"\n#include <stdlib.h>\n#include <string.h>\n#include <stdio.h>\n#include <ctype.h>\n\n/* produce a short coherent sentence by extracting keywords and plugging into templates */\nstatic const char *templates[] = {\n    \"The analysis links the zeta function to global Gamma integrals and quantized geometry.\",\n    \"We map topology decompositions to local quantum equations such as Hamiltonian and beta-terms.\",\n    \"The report suggests that Euler product structure yields entropy invariants in knot/Jones polynomials.\",\n    \"A derived pathway: zeta -> Gamma -> Beta -> local field equations for gravity and anti-gravity.\",\n    \"Topological genus decompositions produce operator-valued contributions to the system Hamiltonian.\"\n};\nstatic const size_t ntemplates = sizeof(templates)/sizeof(templates[0]);\n\nchar* generate_meaningful_sentence(const char *report_text){\n    /* Rule: prefer templates that match present keywords. If keywords absent, pick random. */\n    if(!report_text) return NULL;\n    int score[ntemplates]; for(size_t i=0;i<ntemplates;i++) score[i]=0;\n    /* simple keyword matching */\n    if(strstr(report_text,\"zeta\") || strstr(report_text,\"ゼータ\")){\n        for(size_t i=0;i<ntemplates;i++) if(strstr(templates[i],\"zeta\")||strstr(templates[i],\"Gamma\") ) score[i]+=3;\n    }\n    if(strstr(report_text,\"Gamma\") || strstr(report_text,\"ガンマ\") ){\n        for(size_t i=0;i<ntemplates;i++) if(strstr(templates[i],\"Gamma\")) score[i]+=2;\n    }\n    if(strstr(report_text,\"Jones\") || strstr(report_text,\"Jones多項式\")){\n        for(size_t i=0;i<ntemplates;i++) if(strstr(templates[i],\"Jones\")) score[i]+=4;\n    }\n    /* pick best-scoring template */\n    int best = -1; int bestv = -1; for(size_t i=0;i<ntemplates;i++){ int v = score[i] + (rand()%2); if(v>bestv){ bestv=v; best=(int)i; } }\n    if(best<0) best = rand()%ntemplates;\n    char *out = strdup(templates[best]); return out;\n}\n\n/* Very small formula synthesizer: map sentence patterns to simple math expressions */\nchar* generate_equation_from_sentence(const char *sentence){\n    if(!sentence) return NULL;\n    /* A few pattern rules mapping English phrases to LaTeX-like math strings (plain text) */\n    if(strstr(sentence,\"zeta\") && strstr(sentence,\"Gamma\")){\n        return strdup(\"Z(s)=\\\\prod_p (1-p^{-s})^{-1},\\\\quad\\\\Gamma(s)=\\int_0^{\\\\infty} e^{-x} x^{s-1} dx\");\n    }\n    if(strstr(sentence,\"Jones\") || strstr(sentence,\"knot\") ){\n        return strdup(\"Entropy_{Jones}= -\\\\sum_k p_k \\log p_k,\\\\quad p_k \\propto |J_k(q)|^2\");\n    }\n    if(strstr(sentence,\"Hamiltonian\") || strstr(sentence,\"quantum\")){\n        return strdup(\"H=\\\\sum_i T_i + V(Top),\\\\quad i\\hbox{ local modes from topology}\");\n    }\n    if(strstr(sentence,\"beta\") || strstr(sentence,\"Beta\")){\n        return strdup(\"B(p,q)=\\\\frac{\\\\Gamma(p)\\\\Gamma(q)}{\\\\Gamma(p+q)}\");\n    }\n    /* fallback: build a composed expression by extracting nouns as symbols */\n    /* extract simple tokens as variable names */\n    char buf[512]; buf[0]=0; int n=0; const char *p=sentence; while(*p && n<5){ while(*p && !isalpha((unsigned char)*p)) p++; if(!*p) break; char tok[64]; int i=0; while(*p && isalpha((unsigned char)*p) && i<60) tok[i++]=tolower((unsigned char)*p++); tok[i]=0; if(i>2){ if(n) strncat(buf, \"+\", sizeof(buf)-strlen(buf)-1); strncat(buf, tok, sizeof(buf)-strlen(buf)-1); n++; } }\n    if(n>0){ char out[1024]; snprintf(out,sizeof(out),\"F(%s)=\\\\int_M e^{-f} dvol\", buf); return strdup(out); }\n    return strdup(\"E=mc^2\");\n}\n\nvoid free_str(char *s){ free(s); }\n");

  /* Demo: ties infer with simple CLI and file reading */
  write_file("omega_zeta_infer/src/demo.c",
	     "// demo.c: demo for generating sentences and equations from a report\n#include \"infer.h\"\n#include <stdio.h>\n#include <stdlib.h>\n\nint main(void){ char *report = NULL; report = NULL; FILE *f = fopen(\"../explorerfiles.txt\",\"r\"); if(f){ fseek(f,0,SEEK_END); long sz = ftell(f); fseek(f,0,SEEK_SET); report = malloc(sz+1); if(report){ fread(report,1,sz,f); report[sz]=0; } fclose(f); }\n if(!report) printf(\"Warning: explorerfiles.txt not found; generator will use default heuristics.\\n\");\n char *sent = generate_meaningful_sentence(report);\n printf(\"Generated sentence:\\n%s\\n\\n\", sent?sent:\"(none)\");\n char *eq = generate_equation_from_sentence(sent);\n printf(\"Inferred equation (text form):\\n%s\\n\\n\", eq?eq:\"(none)\");\n free_str(sent); free_str(eq); free(report);\n printf(\"Enter 'gen' to generate again or 'exit' to quit.\\n\");\n char cmd[128]; while(1){ printf(\"> \"); if(!fgets(cmd,sizeof(cmd),stdin)) break; if(strncmp(cmd,\"exit\",4)==0) break; if(strncmp(cmd,\"gen\",3)==0){ char *s2 = generate_meaningful_sentence(report); char *e2 = generate_equation_from_sentence(s2); printf(\"Sentence:\\n%s\\nEquation:\\n%s\\n\", s2,e2); free_str(s2); free_str(e2); } else printf(\"Commands: gen, exit\\n\"); }\n return 0; }\n");

  write_file("omega_zeta_infer/src/Makefile",
	     "CC = gcc\nCFLAGS = -O2 -std=c11 -I.\nSOURCES = infer.c demo.c\nTARGET = omega_zeta_infer_demo\nall: $(TARGET)\n\t$(CC) $(CFLAGS) -o $(TARGET) $(SOURCES)\nclean:\n\trm -f $(TARGET)\n");

  write_file("omega_zeta_infer/README.txt",
	     "omega_zeta_infer generator output\n\nPlace the report text as omega_zeta_infer/explorerfiles.txt (plain text extracted from PDF).\nBuild:\n  cd omega_zeta_infer/src && make\nRun demo:\n  ./omega_zeta_infer_demo\n\nDescription:\n- generate_meaningful_sentence(report_text): template+keyword heuristic produces a short coherent sentence.\n- generate_equation_from_sentence(sentence): rule-based mapping from sentence patterns to textual math expressions (LaTeX-like plain text).\n\nThis is a prototype. For stronger results integrate a symbolic engine and an LLM-based parser.\n");

  printf("Generated omega_zeta_infer/src. Place report text at omega_zeta_infer/explorerfiles.txt and then:\n  cd omega_zeta_infer/src && make && ./omega_zeta_infer_demo\n");
  return 0;
}
```

必要な拡張（任意、指定してください）
- 生成文の多様性と文法向上：文法テンプレートを増やす／n-gramモデル実装（Cでの簡易言語モデル）。
- 数式合成の厳密化：Cで簡易シンボリック処理器（項・係数・演算子ツリー）、もしくは外部SymPy連携。
- LLM連携：自然言語→意味表現→式合成を高品質にするための外部API接続（別プロセス／HTTP呼び出し）。

どの拡張を優先しますか？
