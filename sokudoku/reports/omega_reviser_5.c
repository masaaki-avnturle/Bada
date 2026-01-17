ファイル: omega_bnf.txt
```
# Omega Script — minimal BNF for core objects (class, array, regex, list, tuple, string, io)

<program>       ::= <statement>*
  <statement>     ::= <import_stmt> | <class_def> | <expr_stmt> | <eof>
  <import_stmt>   ::= "import" <module_path>
  <module_path>   ::= <identifier> ("::" <identifier>)* ( "<" <identifier> ">" )?
  <class_def>     ::= "class" <identifier> "{" <class_body> "}"
  <class_body>    ::= (<member>)* 
  <member>        ::= <property> | <method>
  <property>      ::= <type>? <identifier> ";"
  <method>        ::= "def" <identifier> "(" <param_list>? ")" <block>
  <param_list>    ::= <identifier> ("," <identifier>)*
  <block>         ::= "{" <statement>* "}"

# Objects and collections
  <array>         ::= "[" <expr_list>? "]"
  <expr_list>     ::= <expression> ("," <expression>)*
  <list_object>   ::= "(" <expr_list>? ")"
  <tuple_object>  ::= "{" <expr_list>? "}"
  <string>        ::= "\"" <chars> "\""

# Regular expressions
  <regex>         ::= "/" <pattern> "/" <regex_flags>?
  <pattern>       ::= <chars_except_slash>*
  <regex_flags>   ::= [imsxu]*

# IO objects
  <io>            ::= "stdin" | "stdout" | "stderr" | "File" "(" <string> ")"

# Expressions (minimal)
  <expression>    ::= <literal> | <identifier> | <call> | <access>
  <call>          ::= <identifier> "(" <expr_list>? ")"
  <access>        ::= <identifier> ("." <identifier>)*
  <literal>       ::= <number> | <string> | <regex> | <array> | <list_object> | <tuple_object>

# Tokens
  <identifier>    ::= [A-Za-z_][A-Za-z0-9_]*
  <number>        ::= [0-9]+(\.[0-9]+)?
  <chars>         ::= any UTF-8 character sequence except control
  <eof>           ::= <empty>
```

  ファイル: pkginstallgen.c
```c
  /*
 pkginstallgen.c
 - Generates omega_bnf.txt (if missing)
 - Generates a simple Omega source loader and a "reviser" that applies
   transformations guided by the BNF file (basic token-driven extension).
 - Produces an executable "omega_reviser" that reads an Omega source,
   loads omega_bnf.txt, and writes an output expanded source.
 Note: minimal, self-contained implementation for demonstration.
  */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define BNF_PATH "omega_bnf.txt"
#define BUF 8192

static const char *bnf_default =
"# Omega Script — minimal BNF for core objects (class, array, regex, list, tuple, string, io)\n\n"
"<program>       ::= <statement>*\n"
"<statement>     ::= <import_stmt> | <class_def> | <expr_stmt> | <eof>\n"
"<import_stmt>   ::= \"import\" <module_path>\n"
"<module_path>   ::= <identifier> (\"::\" <identifier>)* ( \"<\" <identifier> \">\" )?\n"
"<class_def>     ::= \"class\" <identifier> \"{\" <class_body> \"}\"\n"
"<class_body>    ::= (<member>)* \n"
"<member>        ::= <property> | <method>\n"
"<property>      ::= <type>? <identifier> \";\"\n"
"<method>        ::= \"def\" <identifier> \"(\" <param_list>? \")\" <block>\n"
"<param_list>    ::= <identifier> (\",\" <identifier>)*\n"
"<block>         ::= \"{\" <statement>* \"}\"\n\n"
"# Objects and collections\n"
"<array>         ::= \"[\" <expr_list>? \"]\"\n"
"<expr_list>     ::= <expression> (\",\" <expression>)*\n"
"<list_object>   ::= \"(\" <expr_list>? \")\"\n"
"<tuple_object>  ::= \"{\" <expr_list>? \"}\"\n"
"<string>        ::= \"\\\"\" <chars> \"\\\"\"\n\n"
"# Regular expressions\n"
"<regex>         ::= \"/\" <pattern> \"/\" <regex_flags>?\n"
"<pattern>       ::= <chars_except_slash>*\n"
"<regex_flags>   ::= [imsxu]*\n\n"
"# IO objects\n"
"<io>            ::= \"stdin\" | \"stdout\" | \"stderr\" | \"File\" \"(\" <string> \")\"\n\n"
"# Expressions (minimal)\n"
"<expression>    ::= <literal> | <identifier> | <call> | <access>\n"
"<call>          ::= <identifier> \"(\" <expr_list>? \")\"\n"
"<access>        ::= <identifier> (\".\" <identifier>)*\n"
"<literal>       ::= <number> | <string> | <regex> | <array> | <list_object> | <tuple_object>\n\n"
"# Tokens\n"
"<identifier>    ::= [A-Za-z_][A-Za-z0-9_]*\n"
"<number>        ::= [0-9]+(\\.[0-9]+)?\n"
"<chars>         ::= any UTF-8 character sequence except control\n"
"<eof>           ::= <empty>\n";

/* write default BNF if not present */
static void ensure_bnf(void) {
FILE *f = fopen(BNF_PATH, "r");
if (f) { fclose(f); return; }
f = fopen(BNF_PATH, "w");
if (!f) { perror("create bnf"); exit(1); }
fwrite(bnf_default, 1, strlen(bnf_default), f);
fclose(f);
}

/* simple tokenizer for identifiers, strings, regex, punctuation */
typedef struct { char *s; size_t pos; } Src;

static int peek(Src *src) {
return src->s[src->pos] ? (unsigned char)src->s[src->pos] : 0;
}
static int nextc(Src *src) { int c = peek(src); if (c) src->pos++; return c; }

static void write_file(const char *path, const char *data) {
FILE *f = fopen(path, "w");
if (!f) { perror("write"); exit(1); }
fwrite(data,1,strlen(data),f);
fclose(f);
}

/* naive reviser:
   - reads BNF file into memory (not parsed in detail)
   - scans source for "import" lines referencing a module matching "Omega::Tuplespace"
   - when found, injects helper skeletons for classes/objects as defined by BNF patterns
   - expands shorthand tokens: "->" => ".assign(", "<< " => ".push("
								    */
static char *load_text(const char *path) {
  FILE *f = fopen(path,"r");
  if (!f) return NULL;
  fseek(f,0,SEEK_END);
  long sz = ftell(f); fseek(f,0,SEEK_SET);
  char *buf = malloc(sz+1);
  if (!buf) { fclose(f); return NULL; }
  fread(buf,1,sz,f); buf[sz]=0; fclose(f); return buf;
}

static int contains_module(const char *src, const char *mod) {
  return strstr(src, mod) != NULL;
}

static char *reviser_expand(const char *src, const char *bnf_text) {
  /* Build output buffer */
  size_t cap = strlen(src) * 3 + 4096;
  char *out = malloc(cap);
  if (!out) return NULL;
  out[0]=0;

  /* If source imports Omega::Tuplespace, inject class templates */
  int need_templates = contains_module(src, "Omega::Tuplespace") || contains_module(src, "Omega::DATABASE");
  if (need_templates) {
    strcat(out,
            "// --- injected by reviser: Omega object templates ---\n"
            "class Object {\n"
	   "  /* generic base object */\n"
            "};\n"
            "class Tuple {\n"
            "  Object **items; int n;\n"
            "};\n"
            "class List {\n"
            "  Object **items; int n; void push(Object*o){}\n"
            "};\n"
            "class Regex {\n"
            "  const char *pattern; const char *flags;\n"
            "};\n"
            "class IO {\n"
            "  static Object* stdin; static Object* stdout; static Object* stderr;\n"
            "};\n\n"
	   );
  }

  /* copy source, performing small macro rewrites */
  const char *p = src;
  while (*p) {
    if (p[0] == '-' && p[1] == '>') {
      strcat(out, ".assign("); p+=2;
      continue;
    }
    if (p[0] == '<' && p[1] == '<') {
      strcat(out, ".push("); p+=2;
      continue;
    }
    /* replace "import <module>" to include comment about bnf */
    if (strncmp(p, "import", 6)==0 && isspace((unsigned char)p[6])) {
      /* copy "import" token */
      strncat(out, "import", 6);
      p+=6;
      /* copy whitespace */
      while (*p && isspace((unsigned char)*p)) { strncat(out, " ", 1); p++; }
      /* copy module name */
      const char *q = p;
      while (*q && *q!='\n') q++;
      char mod[256]={0};
      size_t L = (q-p) < sizeof(mod)-1 ? q-p : sizeof(mod)-1;
      strncpy(mod, p, L); mod[L]=0;
      /* inject BNF note */
      strcat(out, mod);
      strcat(out, " /* reviser: grammar loaded from omega_bnf.txt */");
      p = q;
      continue;
    }
    /* default copy one char */
    size_t olen = strlen(out);
    out[olen] = *p; out[olen+1]=0;
    p++;
  }

  /* if bnf_text contains regex token description, add simple helper */
  if (strstr(bnf_text, "<regex>")) {
    strcat(out,
	   "\n// regex helper\nRegex *regex_new(const char *p,const char *f){ Regex *r=(Regex*)malloc(sizeof(Regex)); r->pattern=p; r->flags=f; return r; }\n");
  }

  return out;
}

int main(int argc, char **argv) {
  ensure_bnf();

  /* write a small installer helper (this program also outputs omega_reviser) */
  const char *usage = "Usage: omega_reviser <input.omega> <output.omega>\n";
  if (argc < 3) {
    printf("%s", usage);
    printf("Note: This program also writes omega_bnf.txt if missing.\n");
    return 0;
  }

  char *src = load_text(argv[1]);
  if (!src) { fprintf(stderr,"failed to read %s\n", argv[1]); return 1; }
  char *bnf = load_text(BNF_PATH);
  if (!bnf) { fprintf(stderr,"failed to read %s\n", BNF_PATH); free(src); return 1; }

  char *out = reviser_expand(src, bnf);
  if (!out) { fprintf(stderr,"reviser failed\n"); free(src); free(bnf); return 1; }

  write_file(argv[2], out);
  printf("Revised Omega source written to %s\n", argv[2]);

  free(src); free(bnf); free(out);
  return 0;
}
```

使用手順（簡潔）
1. 上記2ファイルを作成する（omega_bnf.txt は省略可：pkginstallgen.c が生成します）。
2. コンパイル:
   gcc -O2 -o pkginstallgen pkginstallgen.c
   3. 実行（Omegaソースを入力して拡張された出力を得る）:
   ./pkginstallgen input.omega output.omega

以上。
