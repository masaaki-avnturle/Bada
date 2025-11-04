/*了解しました。以下は、先に作成したジェネレータを改訂し、添付レポート中の Omega スクリプト風コード（等号記法 `=>` と `>-` を含む）を生成物に組み込み、ランタイム側でそれらの記法を解釈・保持して出力できるように拡張した堅牢な `pkginstallgen.c` です。

主な変更点（要点）
- 生成される例 `omega_pkg/examples/objects.omega` を、あなたが提示した Omega スクリプト風コードに置換。
- ランタイムのパーサ（極簡易）は `=>`（分岐等号）と `>-`（変換代入）を認識して内部の「transform map / binding map」に格納する機能を追加。
  - `puts(name);` がマッピングやオブジェクト（配列・ハッシュ・list・func）を優先して表示するよう改善。
- 既存の配列/hash/list/func 登録機能は維持。不要な外部準備なしで動作するよう堅牢化。

注意：あくまで自動生成する「実用的な雛形」です。Omega スクリプトの完全な仕様が定義済みであれば、より厳密なパーサ／評価器に拡張できます。

保存してビルド・実行
1. 保存：pkginstallgen.c（下記全文）
2. ビルド：gcc -std=c11 -O2 -Wall -o pkginstallgen pkginstallgen.c
3. 実行：./pkginstallgen Bada++1.pdf
   - pdftotext が無ければ第1引数にプレーンテキストファイルを渡してください。
4. ビルド生成物：make -C omega_pkg all
5. 実行例：./omega_pkg/omega-bin omega_pkg/examples/objects.omega

pkginstallgen.c（全文）：

```c
*/
		  // pkginstallgen.c
		  // Generates omega_pkg with runtime that supports:
		  // - arrays, lists, hashes, func objects
		  // - Omega-style "=>", ">-" assignment/transform notations from the provided report
		  // Build: gcc -std=c11 -O2 -Wall -o pkginstallgen pkginstallgen.c
		  // Run:   ./pkginstallgen Bada++1.pdf   (or a plain text file)
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <ctype.h>
#include <errno.h>

#if defined(_WIN32) || defined(_WIN64)
# include <direct.h>
# define MKDIR(p) (_mkdir(p) == 0 ? 0 : (errno == EEXIST ? 0 : -1))
#else
# include <sys/stat.h>
# include <unistd.h>
# define MKDIR(p) (mkdir(p,0755)==0 ? 0 : (errno==EEXIST?0:-1))
#endif

		  static void die(const char *fmt, ...) {
  va_list ap; va_start(ap, fmt); vfprintf(stderr, fmt, ap); va_end(ap); fputc('\n', stderr); exit(1);
}
		  static void ensure_dir_recursive(const char *path) {
		    if (!path || !*path) die("invalid path");
		    char tmp[1024];
		    if (strlen(path) >= sizeof(tmp)) die("path too long");
		    strncpy(tmp, path, sizeof(tmp)); tmp[sizeof(tmp)-1]=0;
		    for (char *p = tmp+1; *p; ++p) {
		      if (*p == '/' || *p == '\\') {
			char c = *p; *p = 0;
			if (MKDIR(tmp) != 0 && errno != EEXIST) die("mkdir %s: %s", tmp, strerror(errno));
			*p = c;
		      }
		    }
		    if (MKDIR(tmp) != 0 && errno != EEXIST) die("mkdir %s: %s", tmp, strerror(errno));
		  }
static int write_lines(const char *path, const char **lines, size_t n, int exec) {
  FILE *f = fopen(path, "wb"); if (!f) return -1;
  for (size_t i=0;i<n;++i){ if (fputs(lines[i], f) == EOF) { fclose(f); return -1; } fputc('\n', f); }
  if (fclose(f) != 0) return -1;
#if !defined(_WIN32) && !defined(_WIN64)
  if (exec) chmod(path, 0755);
#endif
  return 0;
}
static char *read_all(const char *path) {
  FILE *f = fopen(path, "rb"); if (!f) return NULL;
  if (fseek(f,0,SEEK_END)!=0){ fclose(f); return NULL; }
  long s = ftell(f); if (s < 0) { fclose(f); return NULL; }
  rewind(f);
  char *b = malloc((size_t)s + 1); if (!b) { fclose(f); return NULL; }
  size_t r = fread(b,1,(size_t)s,f); b[r]=0; fclose(f); return b;
}
static char *pdf_to_text(const char *pdf) {
#if defined(_WIN32) || defined(_WIN64)
  (void)pdf; return NULL;
#else
  if (access("/usr/bin/pdftotext", X_OK) != 0 && access("/usr/local/bin/pdftotext", X_OK) != 0) return NULL;
  const char *tmp = ".__pkginstallgen_tmp.txt";
  char cmd[2048];
  snprintf(cmd, sizeof(cmd), "pdftotext \"%s\" \"%s\" 2>/dev/null", pdf, tmp);
  if (system(cmd) != 0) return NULL;
  char *s = read_all(tmp); remove(tmp); return s;
#endif
}

/* Emit files including enhanced runtime that understands => and >- */
static void emit_files_with_omega_logic(const char *report_text) {
  ensure_dir_recursive("omega_pkg");
  ensure_dir_recursive("omega_pkg/src");
  ensure_dir_recursive("omega_pkg/include");
  ensure_dir_recursive("omega_pkg/grammar");
  ensure_dir_recursive("omega_pkg/examples");
  ensure_dir_recursive("omega_pkg/bin");

  const char *hdr[] = {
    "/* omega.h */",
    "#ifndef OMEGA_H",
    "#define OMEGA_H",
    "int omega_eval_content(const char *content);",
    "int omega_report_only(void);",
    "int parse_and_run(const char *path);",
        "#endif"
  };
  write_lines("omega_pkg/include/omega.h", hdr, sizeof(hdr)/sizeof(hdr[0]), 0);

  /* grammar (informational) */
  const char *bnf[] = {
    "; omega.bnf (generated)",
    "<program> ::= { <statement> }",
    "<statement> ::= <decl> ';' | <assign> ';' | <expr> ';' | 'puts' '(' <ident> ')' ';'",
    "<assign> ::= <lhs> ( '=>' | '>-') <rhs>",
    "<lhs> ::= <ident> | <expr>",
    "<rhs> ::= <ident> | <expr> | <object-literal>",
    "<decl> ::= 'array' <ident> '=' '[' <string-list> ']'",
    "<decl> ::= 'list' <ident> '=' 'list' '(' <string-list> ')'",
    "<decl> ::= 'hash' <ident> '=' '{' <hash-pairs> '}'",
    "<decl> ::= 'func' <ident> '=' 'func' '(' <number> ')'",
    "<expr> ::= <ident> | <call> | <string> | <number>",
    "<call> ::= <ident> '(' [ <args> ] ')'",
    "<string-list> ::= <string> { ',' <string> }",
    "<hash-pairs> ::= <string> ':' <number> { ',' <string> ':' <number> }",
    "<ident> ::= /[A-Za-z_][A-Za-z0-9_:]*/",
    "<string> ::= /\\\"(?:[^\\\"\\\\]|\\\\.)*\\\"/",
        "<number> ::= /[0-9]+/"
  };
  write_lines("omega_pkg/grammar/omega.bnf", bnf, sizeof(bnf)/sizeof(bnf[0]), 0);

  /* runtime.c: fully implemented object storage + handling of => and >- */
  const char *runtime[] = {
    "/* runtime.c - runtime with arrays/lists/hashes/func and '=>', '>-' support */",
    "#include <stdio.h>",
    "#include <stdlib.h>",
    "#include <string.h>",
    "#include <ctype.h>",
    "#include \"../include/omega.h\"",
    "",
    "typedef struct StrNode { char *s; struct StrNode *next; } StrNode;",
    "typedef struct ArrayObj { char *name; StrNode *items; struct ArrayObj *next; } ArrayObj;",
    "typedef struct ListObj  { char *name; StrNode *items; struct ListObj *next; } ListObj;",
    "typedef struct FuncObj  { char *name; long data; struct FuncObj *next; } FuncObj;",
    "typedef struct HashPair { char *k; long v; struct HashPair *next; } HashPair;",
    "typedef struct HashObj  { char *name; HashPair *pairs; struct HashObj *next; } HashObj;",
    "",
    "/* generic mapping for => and >- : store simple bindings (lhs -> rhs string) */",
    "typedef struct Bind { char *lhs; char *op; char *rhs; struct Bind *next; } Bind;",
    "static Bind *bindings = NULL;",
    "",
    "static ArrayObj *arrays = NULL; static ListObj *lists = NULL; static FuncObj *funcs = NULL; static HashObj *hashes = NULL;",
    "",
    "static char *dupstr(const char *s){ if(!s) return NULL; size_t n=strlen(s)+1; char *r=malloc(n); if(!r) return NULL; memcpy(r,s,n); return r; }",
    "static void push_str(StrNode **root, char *s){ StrNode *n=malloc(sizeof(*n)); if(!n) return; n->s=s; n->next=*root; *root=n; }",
    "static void reverse_list(StrNode **root){ StrNode *r=NULL,*it=*root; while(it){ StrNode *nx=it->next; it->next=r; r=it; it=nx; } *root=r; }",
    "",
    "static void add_array(const char *name, char **items, size_t n){ ArrayObj *a=malloc(sizeof(*a)); if(!a) return; a->name=dupstr(name); a->items=NULL; a->next=arrays; arrays=a; for(size_t i=0;i<n;i++) push_str(&a->items, dupstr(items[i])); reverse_list(&a->items); }",
    "static void add_list(const char *name, char **items, size_t n){ ListObj *l=malloc(sizeof(*l)); if(!l) return; l->name=dupstr(name); l->items=NULL; l->next=lists; lists=l; for(size_t i=0;i<n;i++) push_str(&l->items, dupstr(items[i])); reverse_list(&l->items); }",
    "static void add_func(const char *name, long v){ FuncObj *f=malloc(sizeof(*f)); if(!f) return; f->name=dupstr(name); f->data=v; f->next=funcs; funcs=f; }",
    "static void add_hash(const char *name, char **keys, long *vals, size_t n){ HashObj *h=malloc(sizeof(*h)); if(!h) return; h->name=dupstr(name); h->pairs=NULL; h->next=hashes; hashes=h; for(size_t i=0;i<n;i++){ HashPair *p=malloc(sizeof(*p)); if(!p) continue; p->k=dupstr(keys[i]); p->v=vals[i]; p->next=h->pairs; h->pairs=p; } /* reverse to preserve order */ HashPair *rev=NULL,*it=h->pairs; while(it){ HashPair *nx=it->next; it->next=rev; rev=it; it=nx; } h->pairs=rev; }",
    "",
    "static void add_binding(const char *lhs, const char *op, const char *rhs){ Bind *b=malloc(sizeof(*b)); if(!b) return; b->lhs=dupstr(lhs); b->op=dupstr(op); b->rhs=dupstr(rhs); b->next=bindings; bindings=b; }",
    "",
    "static int print_by_name(const char *name){ if(!name) return 0; for(ArrayObj *a=arrays;a;a=a->next){ if(a->name && strcmp(a->name,name)==0){ putchar('['); StrNode *it=a->items; int first=1; while(it){ if(!first) putchar(','); printf(\"\\\"%s\\\"\", it->s); first=0; it=it->next; } puts(\"]\"); return 1; } }",
    " for(HashObj *h=hashes;h;h=h->next){ if(h->name && strcmp(h->name,name)==0){ putchar('{'); HashPair *hp=h->pairs; int first=1; while(hp){ if(!first) putchar(','); printf(\"\\\"%s\\\":%ld\", hp->k, hp->v); first=0; hp=hp->next; } puts(\"}\"); return 1; } }",
    " for(ListObj *l=lists;l;l=l->next){ if(l->name && strcmp(l->name,name)==0){ putchar('('); StrNode *it=l->items; int first=1; while(it){ if(!first) putchar(','); printf(\"\\\"%s\\\"\", it->s); first=0; it=it->next; } puts(\")\"); return 1; } }",
    " for(FuncObj *f=funcs; f; f=f->next){ if(f->name && strcmp(f->name,name)==0){ printf(\"%ld\\n\", f->data); return 1; } }",
    " /* bindings */ for(Bind *b=bindings;b;b=b->next){ if(strcmp(b->lhs,name)==0){ printf(\"%s %s %s\\n\", b->lhs, b->op, b->rhs); return 1; } }",
    " return 0; }",
    "",
    "/* parse helpers */",
    "static char *read_quoted(const char **pp){ const char *p=*pp; while(*p && *p!='\\\"') ++p; if(!*p) return NULL; p++; size_t cap=64; char *b=malloc(cap); if(!b) return NULL; size_t n=0; while(*p && *p!='\\\"'){ char c=*p++; if(c=='\\\\' && *p){ char e=*p++; if(e=='n') c='\\n'; else if(e=='t') c='\\t'; else c=e; } if(n+1>=cap){ cap*=2; char *t=realloc(b,cap); if(!t){ free(b); return NULL; } b=t; } b[n++]=c; } b[n]=0; if(*p=='\\\"') ++p; *pp=p; return b; }",
    "",
    "/* very small recursive parser focusing on constructs and =>, >- */",
    "static void parse_build(const char *content){ if(!content) return; const char *p=content; while(*p){ const char *semi = strchr(p,';'); if(!semi) break; size_t len = (size_t)(semi - p); char *line = malloc(len+1); if(!line) break; memcpy(line,p,len); line[len]=0; char *s=line; while(*s && isspace((unsigned char)*s)) s++;",
    "    /* declarations */",
    "    if (strncmp(s, \"array\", 5)==0 && (s[5]==' '||s[5]=='\\t')){ char name[128]={0}; const char *q=s+5; while(*q==' '||*q=='\\t') ++q; size_t i=0; while(*q && *q!=' ' && *q!='=' && *q!='[' && i+1<sizeof(name)) name[i++]=*q++; name[i]=0; const char *lb=strchr(s,'['); const char *rb=strchr(s,']'); if(lb&&rb&&rb>lb){ const char *t=lb+1; char *items[128]; size_t in=0; while(t<rb && in<128){ while(*t==' '||*t==','||*t=='\\t') ++t; if(*t=='\\\"'){ char *v = read_quoted(&t); if(v) items[in++]=v; } else break; } if(in>0){ char **ci = malloc(sizeof(char*)*in); for(size_t ii=0;ii<in;++ii) ci[ii]=items[ii]; add_array(name,ci,in); free(ci); for(size_t ii=0;ii<in;++ii) free(items[ii]); } } }",
    "",
    "    else if (strncmp(s, \"list\", 4)==0 && (s[4]==' '||s[4]=='\\t')){ char name[128]={0}; const char *q=s+4; while(*q==' '||*q=='\\t') ++q; size_t i=0; while(*q && *q!=' ' && *q!='=' && *q!='(' && i+1<sizeof(name)) name[i++]=*q++; name[i]=0; const char *op=strchr(s,'('); const char *cp=strchr(s,')'); if(op&&cp&&cp>op){ const char *t=op+1; char *items[128]; size_t in=0; while(t<cp && in<128){ while(*t==' '||*t==','||*t=='\\t') ++t; if(*t=='\\\"'){ char *v=read_quoted(&t); if(v) items[in++]=v; } else break; } if(in>0){ char **ci=malloc(sizeof(char*)*in); for(size_t ii=0;ii<in;++ii) ci[ii]=items[ii]; add_list(name,ci,in); free(ci); for(size_t ii=0;ii<in;++ii) free(items[ii]); } } }",
    "",
    "    else if (strncmp(s, \"func\",4)==0 && (s[4]==' '||s[4]=='\\t')){ char name[128]={0}; const char *q=s+4; while(*q==' '||*q=='\\t') ++q; size_t i=0; while(*q && *q!=' ' && *q!='=' && *q!='(' && i+1<sizeof(name)) name[i++]=*q++; name[i]=0; const char *op=strchr(s,'('); const char *cp=strchr(s,')'); if(op&&cp&&cp>op){ char num[64]={0}; size_t ln=(size_t)(cp-op-1); if(ln<sizeof(num)){ memcpy(num, op+1, ln); num[ln]=0; long v = atol(num); add_func(name, v); } } }",
    "",
    "    else if (strchr(s,'{')){ const char *lb=strchr(s,'{'); const char *rb=strchr(s,'}'); if(lb&&rb&&rb>lb){ const char *t=lb+1; char *keys[128]; long vals[128]; size_t kn=0; while(t<rb && kn<128){ while(*t==' '||*t==','||*t=='\\t') ++t; if(*t=='\\\"'){ char *k=read_quoted(&t); while(*t==' '||*t=='\\t') ++t; if(*t==':') ++t; while(*t==' '||*t=='\\t') ++t; char num[64]={0}; size_t ni=0; while(*t && *t!=',' && *t!='}') { if(ni+1<sizeof(num)) num[ni++]=*t; ++t; } num[ni]=0; long v=atol(num); keys[kn]=k; vals[kn]=v; kn++; } else break; } if(kn>0){ char **ck = malloc(sizeof(char*)*kn); for(size_t ii=0;ii<kn;++ii) ck[ii]=keys[ii]; add_hash(\"H\", ck, vals, kn); free(ck); for(size_t ii=0;ii<kn;++ii) free(keys[ii]); } } }",
    "",
    "    else { /* handle assignments with => or >- */",
    "        /* find => or >- */",
    "        const char *p_op = strstr(s, \"=>\");",
    "        const char *p_op2 = strstr(s, \">-\");",
    "        if (p_op || p_op2) {",
    "            const char *op = p_op ? p_op : p_op2;",
    "            size_t lhs_len = (size_t)(op - s);",
    "            char *lhs = malloc(lhs_len+1); if(!lhs) { free(line); p = semi+1; continue; }",
    "            memcpy(lhs, s, lhs_len); lhs[lhs_len] = 0; /* trim */",
    "            char *ltrim = lhs; while(*ltrim && isspace((unsigned char)*ltrim)) ltrim++; char *rend = ltrim + strlen(ltrim)-1; while(rend>ltrim && isspace((unsigned char)*rend)) *rend--=0;",
    "            const char *rstart = op + (p_op ? 2 : 2); /* both ops length 2 */",
    "            while(*rstart && isspace((unsigned char)*rstart)) rstart++; /* extract rhs until end */",
    "            char *rhs = strdup(rstart); if(!rhs){ free(lhs); free(line); p = semi+1; continue; } /* trim trailing spaces */",
    "            char *r = rhs + strlen(rhs) - 1; while(r>rhs && isspace((unsigned char)*r)) *r--=0;",
    "            const char *opstr = p_op ? \"=>\" : \">-\";",
    "            /* record binding */",
    "            add_binding(ltrim, opstr, rhs);",
    "            free(lhs); free(rhs);",
    "        } else { /* maybe puts or other call handled below */ }",
    "    }",
    "",
    "    /* calls like puts(X); */",
    "    if (strncmp(s, \"puts\", 4)==0){ const char *op = strchr(s, '('); const char *cp = strchr(s, ')'); if(op&&cp&&cp>op){ const char *t = op+1; while(*t && isspace((unsigned char)*t)) ++t; char id[256]={0}; size_t ii=0; while(*t && (isalnum((unsigned char)*t) || *t=='_' || *t==':' ) && ii+1<sizeof(id)) id[ii++]=*t++; id[ii]=0; if(ii>0) { if(!print_by_name(id)) printf(\"%s\\n\", id); } } }",
    "",
    "    free(line); p = semi + 1; } }",
    "",
"int omega_eval_content(const char *content){ if(!content) return 1; parse_build(content); return 0; }"
  };
  write_lines("omega_pkg/src/runtime.c", runtime, sizeof(runtime)/sizeof(runtime[0]), 0);

  /* parser.c: driver */
  const char *parser[] = {
    "#include <stdio.h>",
    "#include <stdlib.h>",
    "#include <string.h>",
    "#include \"../include/omega.h\"",
    "static char *read_file_all(const char *p){ FILE *f=fopen(p,\"rb\"); if(!f) return NULL; if(fseek(f,0,SEEK_END)!=0){ fclose(f); return NULL; } long s=ftell(f); if(s<0){ fclose(f); return NULL; } rewind(f); char *b=malloc((size_t)s+1); if(!b){ fclose(f); return NULL; } size_t r=fread(b,1,(size_t)s,f); b[r]='\\0'; fclose(f); return b; }",
        "int parse_and_run(const char *path){ char *c = read_file_all(path); if(!c){ fprintf(stderr,\"cannot read %s\\n\", path); return 1; } int rc = omega_eval_content(c); free(c); return rc; }"
  };
  write_lines("omega_pkg/src/parser.c", parser, sizeof(parser)/sizeof(parser[0]), 0);

  /* omega_bin.c */
  const char *omega_bin[] = {
    "#include <stdio.h>",
    "int parse_and_run(const char *path);",
        "int main(int argc,char **argv){ const char *p=(argc>=2)?argv[1]:\"examples/objects.omega\"; return parse_and_run(p); }"
  };
  write_lines("omega_pkg/src/omega_bin.c", omega_bin, sizeof(omega_bin)/sizeof(omega_bin[0]), 0);

  /* bnf_codegen stub */
  const char *bgenc[] = {
    "/* bnf_codegen - stub */",
    "#include <stdio.h>",
    "#include <stdlib.h>",
    "int main(int argc,char **argv){ if(argc<3){ fprintf(stderr,\"Usage: %s <bnf> <out.c>\\n\",argv[0]); return 1;} FILE *f=fopen(argv[1],\"rb\"); if(!f){ perror(\"open\"); return 2; } fseek(f,0,SEEK_END); long s=ftell(f); rewind(f); char *b=malloc(s+1); fread(b,1,s,f); b[s]=0; fclose(f); FILE *o=fopen(argv[2],\"wb\"); if(!o){ free(b); return 3; } fprintf(o,\"/* parser stub generated from %s */\\n\", argv[1]); fprintf(o,\"/* grammar:\\n%s\\n*/\\n\", b); fclose(o); free(b); printf(\"generated %s\\n\", argv[2]); return 0; }"
  };
  write_lines("omega_pkg/src/bnf_codegen.c", bgenc, sizeof(bgenc)/sizeof(bgenc[0]), 0);

  /* Makefile */
  const char *mk[] = {
    "CC = gcc",
    "CFLAGS = -Iinclude -O2",
    "SRCDIR = src",
    "all: omega-bin bnf_codegen",
    "$(SRCDIR)/%.o: $(SRCDIR)/%.c",
    "\t$(CC) $(CFLAGS) -c -o $@ $<",
    "omega-bin: $(SRCDIR)/runtime.o $(SRCDIR)/parser.o $(SRCDIR)/omega_bin.o",
    "\t$(CC) -o $@ $(SRCDIR)/runtime.o $(SRCDIR)/parser.o $(SRCDIR)/omega_bin.o",
    "bnf_codegen: $(SRCDIR)/bnf_codegen.c",
    "\t$(CC) -o bnf_codegen $(SRCDIR)/bnf_codegen.c",
    "clean:",
        "\trm -f $(SRCDIR)/*.o omega-bin bnf_codegen __omega_embedded.c compiled_omega_exec"
  };
  write_lines("omega_pkg/Makefile", mk, sizeof(mk)/sizeof(mk[0]), 0);

  /* examples: insert the provided Omega-style code (converted to plain text Omega script) */
  const char *example[] = {
    "# Omega-style example derived from the report (uses => and >- forms)",
    "Omega::DATABASE[tuplespace] {",
    "  class Operator {",
    "    Operator.coefficient >- 0",
    "    Operator.variable >- \"0\"",
    "    /* multiply */",
    "    def mul(self, other) {",
    "      other.is_operator => Operator.new(self.coefficient * other.coefficient, self.variable * other.variable);",
    "      other.is_complex => Operator.new(self.coefficient * other, self.variable);",
    "      _ => raise(\"Cannot multiply Operator with other\")",
    "    }",
    "    /* add */",
    "    def add(self, other) {",
    "      other.is_operator => Operator.new(self.coefficient + other.coefficient, self.variable);",
    "      other.is_complex => Operator.new(self.coefficient + other, self.variable);",
    "      _ => raise(\"Cannot add Operator with other\")",
    "    }",
    "    def to_s(self) { self.coefficient.to_s + self.variable }",
    "  }",
    "",
    "  class Knot {",
    "    Knot.crossings >- []",
    "    def add_crossing(self, sign) { self.crossings.push(sign) }",
    "    def jones_polynomial(self) {",
    "      state >- Operator.new(1, \"0\")",
    "      jones >- state",
    "      for c in self.crossings {",
    "        /* simplified evaluate */",
    "        jones >- jones /* placeholder for evaluate */",
    "      }",
    "      jones",
    "    }",
    "    def valid?(self) { jones >- self.jones_polynomial; jones.to_s != \"0\" }",
    "  }",
    "",
    "  def generate_random_knot(n) {",
    "    knot >- Knot.new",
    "    i = 0",
    "    while i < n {",
    "      sign >- (rand(2) * 2 - 1)",
    "      knot.add_crossing(sign)",
    "      i = i + 1",
    "    }",
    "    knot",
    "  }",
    "",
    "  num_knots >- 100",
    "  num_crossings >- 5",
    "  /* generate and validate - here simplified */",
    "  valid_knots >- []",
    "  invalid_knots >- []",
    "  i = 0",
    "  while i < num_knots {",
    "    k >- generate_random_knot(num_crossings)",
    "    if k.valid? => valid_knots.push(k) else => invalid_knots.push(k)",
    "    i = i + 1",
    "  }",
    "  puts(\"Valid knots: \")",
    "  puts(valid_knots.length.to_s)",
    "  puts(\"Invalid knots: \")",
    "  puts(invalid_knots.length.to_s)",
    "}",
        ""
  };
  write_lines("omega_pkg/examples/objects.omega", example, sizeof(example)/sizeof(example[0]), 0);

  /* launcher */
  const char *launcher[] = {
    "#!/bin/sh",
    "BASEDIR=\"`dirname \"$0\"`/..\"",
        "exec \"$BASEDIR/omega-bin\" \"$@\""
  };
  write_lines("omega_pkg/bin/omega", launcher, sizeof(launcher)/sizeof(launcher[0]), 1);
}

int main(int argc, char **argv) {
  if (argc < 2) { fprintf(stderr, "Usage: %s <pdf-or-text-file>\n", argv[0]); return 1; }
  char *text = pdf_to_text(argv[1]);
  if (!text) {
    text = read_all(argv[1]);
    if (!text) die("cannot extract text from PDF and cannot read file");
  }
  emit_files_with_omega_logic(text);
  free(text);
  puts("pkginstallgen: generated omega_pkg with Omega-style logic support (=> and >-).");
  puts("Run: make -C omega_pkg all && ./omega_pkg/omega-bin omega_pkg/examples/objects.omega");
  return 0;
}

/*
必要ならこの生成物を次の点でさらに強化します（指示ください）：
- `=>` / `>-` の意味論を厳密に（例：左辺が式の場合の評価戦略、オブジェクト不変性のトラッキング）実装する。
- Omega スクリプトの完全な文法に沿うパーサ（トークナイザ→AST→実行）を自動生成する。
- 生成した BNF をもとに C の再帰下降パーサを自動生成し、全ての例を実行可能にする。

どのレベルで自動化／厳密化するか指示ください。
*/
