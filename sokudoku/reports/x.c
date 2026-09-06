以下は、pkginstallgen.c風の単一Cプログラムで、与えたBNFファイルから（簡易）サンプルソースを生成するだけでなく、各プログラミング言語向けの「インタープリタ」と「コンパイラ」の骨組み（スケルトン）ソースとビルドスクリプトを出力するものです。出力されるのはあくまで「テンプレート（教育目的の骨組み）」であり、実際の言語仕様を解釈・実行する完全なインタープリタ／コンパイラ実装ではありません。実行には標準Cライブラリのみが必要です。

保存名例: pkginstallgen.c
コンパイル:
gcc -o pkginstallgen pkginstallgen.c

実行:
./pkginstallgen

ソースコード（長いためファイル全体）:

```c
// pkginstallgen.c
#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <errno.h>
#include <time.h>

static int mkdir_p(const char *path) {
  char tmp[4096];
  size_t len;
  char *p;
  if (!path || !*path) return -1;
  snprintf(tmp, sizeof(tmp), "%s", path);
  len = strlen(tmp);
  if (tmp[len - 1] == '/') tmp[len - 1] = '\0';
  for (p = tmp + 1; *p; p++) {
    if (*p == '/') {
      *p = '\0';
      if (mkdir(tmp, 0755) != 0 && errno != EEXIST) return -1;
      *p = '/';
    }
  }
  if (mkdir(tmp, 0755) != 0 && errno != EEXIST) return -1;
  return 0;
}

static int write_file_with_dirs(const char *fullpath, const char *content) {
  char dirbuf[4096];
  const char *last_slash = strrchr(fullpath, '/');
  if (last_slash) {
    size_t dlen = last_slash - fullpath;
    if (dlen >= sizeof(dirbuf)) return -1;
    memcpy(dirbuf, fullpath, dlen);
    dirbuf[dlen] = '\0';
    if (mkdir_p(dirbuf) != 0) {
      fprintf(stderr, "mkdir_p failed for %s\n", dirbuf);
      return -1;
    }
  }
  FILE *f = fopen(fullpath, "w");
  if (!f) { perror(fullpath); return -1; }
  if (fputs(content, f) == EOF) { perror("fputs"); fclose(f); return -1; }
  fclose(f);
  return 0;
}

/* Very small BNF parsing (toy) */
typedef struct Alt { char *text; struct Alt *next; } Alt;
typedef struct Rule { char *name; Alt *alts; struct Rule *next; } Rule;
static Rule *rules_head = NULL;

static Rule* find_rule(const char *name) {
  for (Rule *r = rules_head; r; r = r->next) if (strcmp(r->name, name) == 0) return r;
  return NULL;
}
static Rule* add_rule(const char *name) {
  Rule *r = find_rule(name);
  if (r) return r;
  r = malloc(sizeof(Rule));
  r->name = strdup(name);
  r->alts = NULL;
  r->next = rules_head;
  rules_head = r;
  return r;
}
static void add_alt(Rule *r, const char *alttext) {
  Alt *a = malloc(sizeof(Alt));
  a->text = strdup(alttext);
  a->next = r->alts;
  r->alts = a;
}
static void free_rules(void) {
  while (rules_head) {
    Rule *r = rules_head; rules_head = r->next;
    Alt *a = r->alts;
    while (a) { Alt *nx = a->next; free(a->text); free(a); a = nx; }
    free(r->name); free(r);
  }
}

static int parse_bnf_text(const char *bnf_text) {
  char *copy = strdup(bnf_text);
  char *line = strtok(copy, "\n");
  while (line) {
    while (*line == ' ' || *line == '\t') line++;
    if (*line == '\0' || line[0] == '#') { line = strtok(NULL, "\n"); continue; }
    char *sep = strstr(line, "::=");
    if (!sep) { line = strtok(NULL, "\n"); continue; }
    *sep = '\0';
    char *lhs = line;
    char *rhs = sep + 3;
    while (*lhs==' '||*lhs=='\t') lhs++;
    char *e = lhs + strlen(lhs) - 1;
    while (e>lhs && (*e==' '||*e=='\t')) *e-- = '\0';
    while (*rhs==' '||*rhs=='\t') rhs++;
    e = rhs + strlen(rhs) - 1;
    while (e>rhs && (*e==' '||*e=='\t')) *e-- = '\0';
    Rule *r = add_rule(lhs);
    char *alt = strtok(rhs, "|");
    while (alt) {
      char *t = alt;
      while (*t==' '||*t=='\t') t++;
      char *end = t + strlen(t) - 1;
      while (end>t && (*end==' '||*end=='\t')) *end-- = '\0';
      add_alt(r, t);
      alt = strtok(NULL, "|");
    }
    line = strtok(NULL, "\n");
  }
  free(copy);
  return 0;
}

static const char* choose_alt(Rule *r) {
  int count = 0;
  for (Alt *a = r->alts; a; a = a->next) count++;
  if (count == 0) return "";
  int idx = (count==1) ? 0 : rand() % count;
  Alt *a = r->alts;
  for (int i = 0; i < idx; ++i) a = a->next;
  return a->text;
}
static void expand_to_buf(const char *text, char *buf, size_t bufsize, int depth) {
  if (depth <= 0) { strncat(buf, "...", bufsize - strlen(buf) - 1); return; }
  char *copy = strdup(text);
  char *tok = strtok(copy, " \t");
  while (tok) {
    Rule *r = find_rule(tok);
    if (r) {
      const char *alt = choose_alt(r);
      expand_to_buf(alt, buf, bufsize, depth - 1);
    } else {
      if (strlen(buf) + strlen(tok) + 2 < bufsize) {
	if (strlen(buf) > 0 && buf[strlen(buf)-1] != '\n') strncat(buf, " ", bufsize - strlen(buf) - 1);
	strncat(buf, tok, bufsize - strlen(buf) - 1);
      }
    }
    tok = strtok(NULL, " \t");
  }
  free(copy);
}
static char* generate_from(const char *start, int max_depth) {
  Rule *r = find_rule(start);
  if (!r) return NULL;
  char *buf = calloc(1, 16384);
  const char *alt = choose_alt(r);
  expand_to_buf(alt, buf, 16384, max_depth);
  return buf;
}

/* Some example toy BNFs embedded (very small) */
static const char *bnf_c =
"<program> ::= <includes> <function>\n"
"<includes> ::= #include<stdio.h> | #include<stdlib.h>\n"
"<function> ::= int main ( ) { <stmts> }\n"
"<stmts> ::= <stmt> | <stmt> <stmts>\n"
  "<stmt> ::= printf(\"Hello, C!\\n\"); | return 0;\n";

static const char *bnf_python =
"<program> ::= <imports> <body>\n"
"<imports> ::= import sys | import os\n"
"<body> ::= def main():\\n    <stmts>\n"
  "<stmts> ::= print('Hello, Python!') | print('Hello, Python!')\\n    return 0\n";

static const char *bnf_js =
"<program> ::= <stmts>\n"
  "<stmts> ::= console.log(\"Hello, JS!\"); | console.log(\"Hello, JS!\");\\nreturn 0;\n";

static const char *bnf_java =
"<program> ::= public class Hello { public static void main ( String [] args ) { <stmts> } }\n"
  "<stmts> ::= System.out.println(\"Hello, Java!\"); | System.out.println(\"Hello, Java!\");\n";

static const char *bnf_ruby =
"<program> ::= <stmts>\n"
  "<stmts> ::= puts 'Hello, Ruby!' | puts 'Hello, Ruby!'\n";

/* Templates for interpreter/compiler skeletons (very small educational stubs) */
static const char *interp_c_template =
"// Interpreter skeleton for %s (C)\n"
"// This is an educational stub that demonstrates a REPL loop and a placeholder parser entry.\n"
  "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\nint parse_and_execute(const char *code) {\n    // TODO: Implement parser using the language BNF and execute AST\n    printf(\"[interp:%s] executing code: %s\\n\", \"%s\", code);\n    return 0;\n}\n\nint main(void) {\n    char buf[4096];\n    printf(\"%s interpreter (stub). Type 'exit' to quit.\\n\", \"%s\");\n    while (1) {\n        printf(\"> \");\n        if (!fgets(buf, sizeof(buf), stdin)) break;\n        if (strncmp(buf, \"exit\", 4) == 0) break;\n        parse_and_execute(buf);\n    }\n    return 0;\n}\n";

static const char *compiler_c_template =
"// Compiler skeleton for %s (C)\n"
"// This is an educational stub that parses source (placeholder) and emits C code to stdout or file.\n"
  "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\nint parse_and_lower(const char *src, char *out, size_t outsz) {\n    // TODO: Implement real parsing and codegen\n    snprintf(out, outsz, \"/* lowered %s source (placeholder) */\\n%s\\n\", \"%s\", src);\n    return 0;\n}\n\nint main(int argc, char **argv) {\n    if (argc < 2) { fprintf(stderr, \"Usage: %s <source>\\n\", argv[0]); return 1; }\n    FILE *f = fopen(argv[1], \"r\");\n    if (!f) { perror(argv[1]); return 1; }\n    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);\n    char *src = malloc(sz+1); fread(src,1,sz,f); src[sz]='\\0'; fclose(f);\n    char out[65536]; parse_and_lower(src, out, sizeof(out));\n    printf(\"%s\", out);\n    free(src);\n    return 0;\n}\n";

/* Small helper: write README describing that generated interpreters/compilers are stubs */
static const char *readme_template =
  "Generated by pkginstallgen\n\nThis directory contains:\n- BNF files (toy examples)\n- generated/ : sample source files produced by expanding the BNF\n- interpreters/ : educational C interpreter skeletons for each language\n- compilers/ : educational C compiler skeletons for each language\n\nIMPORTANT: The 'interpreters' and 'compilers' produced here are skeletons (stubs) for demonstration only. They do not implement a full language runtime or code generator. To create a real interpreter/compiler you must implement parsing, AST construction, type checking, code generation or bytecode interpreter.\n";

/* Main program: create directories, BNF files, generate samples, and produce interpreter/compiler skeletons */
int main(void) {
  srand((unsigned)time(NULL));

  /* Create base directories */
  const char *dirs[] = {
    "omega_script/lib/math",
    "omega_script/lib/network",
    "omega_script/include",
    "omega_script/bin",
    "bnf",
    "generated",
    "interpreters",
        "compilers"
  };
  for (size_t i = 0; i < sizeof(dirs)/sizeof(dirs[0]); ++i) mkdir_p(dirs[i]);

  /* Write minimal library files (placeholders) */
  write_file_with_dirs("omega_script/lib/math/manifold.c",
		       "// omega_script/lib/math/manifold.c (placeholder)\n#include \"manifold.h\"\n#include <stdlib.h>\n\n/* Placeholder implementations */\n");
  write_file_with_dirs("omega_script/lib/network/tuplespace.c",
		       "// omega_script/lib/network/tuplespace.c (placeholder)\n#include \"tuplespace.h\"\n#include <stdlib.h>\n");
  write_file_with_dirs("omega_script/lib/network/virtualmachine.c",
		       "// omega_script/lib/network/virtualmachine.c (placeholder)\n#include \"virtualmachine.h\"\n#include <stdlib.h>\n");
  write_file_with_dirs("omega_script/include/omega_types.h",
		       "/* omega_types.h placeholder */\n#ifndef OMEGA_TYPES_H\n#define OMEGA_TYPES_H\ntypedef struct OmegaType OmegaType;\n#endif\n");
  write_file_with_dirs("omega_script/bin/omega_script.c",
		       "/* omega_script runner placeholder */\n#include <stdio.h>\nint main(void){ puts(\"omega_script runner placeholder\"); return 0; }\n");

  /* Write BNF files (toy) */
  write_file_with_dirs("bnf/c.bnf", bnf_c);
  write_file_with_dirs("bnf/python.bnf", bnf_python);
  write_file_with_dirs("bnf/javascript.bnf", bnf_js);
  write_file_with_dirs("bnf/java.bnf", bnf_java);
  write_file_with_dirs("bnf/ruby.bnf", bnf_ruby);

  /* Languages to produce skeletons for */
  const char *langs[] = { "c", "python", "javascript", "java", "ruby" };
  const char *bnfs[] = { bnf_c, bnf_python, bnf_js, bnf_java, bnf_ruby };

  /* For each language: parse BNF, generate sample, and write interpreter/compiler skeletons */
  for (size_t i = 0; i < sizeof(langs)/sizeof(langs[0]); ++i) {
    free_rules();
    parse_bnf_text(bnfs[i]);

    /* choose start nonterminal */
    const char *start = "<program>";
    if (!find_rule(start)) {
      if (rules_head) start = rules_head->name;
    }
    char *sample = generate_from(start, 12);
    if (!sample) sample = strdup("/* generation failed */\n");

    /* output sample file path by language */
    char outpath[256];
    if (strcmp(langs[i], "c") == 0) snprintf(outpath, sizeof(outpath), "generated/hello.c");
    else if (strcmp(langs[i], "python") == 0) snprintf(outpath, sizeof(outpath), "generated/hello.py");
    else if (strcmp(langs[i], "javascript") == 0) snprintf(outpath, sizeof(outpath), "generated/hello.js");
    else if (strcmp(langs[i], "java") == 0) snprintf(outpath, sizeof(outpath), "generated/Hello.java");
    else if (strcmp(langs[i], "ruby") == 0) snprintf(outpath, sizeof(outpath), "generated/hello.rb");
    else snprintf(outpath, sizeof(outpath), "generated/hello.txt");

    /* simple postprocess replacing literal \n occurrences with newlines */
    char finalbuf[16384] = {0};
    const char *p = sample;
    while (*p) {
      if (*p == '\\' && *(p+1) == 'n') { strncat(finalbuf, "\n", sizeof(finalbuf)-strlen(finalbuf)-1); p+=2; }
      else { strncat(finalbuf, (char[]){*p,0}, sizeof(finalbuf)-strlen(finalbuf)-1); p++; }
    }
    if (strlen(finalbuf) == 0) strcpy(finalbuf, sample);

    write_file_with_dirs(outpath, finalbuf);
    printf("Generated sample for %s: %s\n", langs[i], outpath);

    /* Write interpreter skeleton (C program) */
    char interp_path[256];
    snprintf(interp_path, sizeof(interp_path), "interpreters/%s_interpreter.c", langs[i]);
    char interp_content[4096];
    snprintf(interp_content, sizeof(interp_content), interp_c_template, langs[i], langs[i], langs[i], langs[i], langs[i]);
    write_file_with_dirs(interp_path, interp_content);
    printf("Interpreter skeleton: %s\n", interp_path);

    /* Write compiler skeleton (C program) */
    char comp_path[256];
    snprintf(comp_path, sizeof(comp_path), "compilers/%s_compiler.c", langs[i]);
    char comp_content[4096];
    snprintf(comp_content, sizeof(comp_content), compiler_c_template, langs[i], langs[i]);
    write_file_with_dirs(comp_path, comp_content);
    printf("Compiler skeleton: %s\n", comp_path);

    free(sample);
  }

  /* write simple Makefile snippets for building the C skeletons */
  write_file_with_dirs("interpreters/Makefile",
		       "CC=gcc\nCFLAGS=-O2 -Wall\n\nall: *.c\n\t@echo \"Build interpreters: run 'make <file>.out' manually or compile individual .c files.\"\n");
  write_file_with_dirs("compilers/Makefile",
		       "CC=gcc\nCFLAGS=-O2 -Wall\n\nall: *.c\n\t@echo \"Build compilers: run 'make <file>.out' manually or compile individual .c files.\"\n");

  /* README */
  write_file_with_dirs("README_pkginstallgen.txt", readme_template);

  printf("Done: generated BNF files, sample sources, interpreter and compiler skeletons.\n");
  return 0;
}
```

注意と補足（簡潔に）:
- 生成物は「教育用の骨組み（stubs）」であり、完全なインタープリタ／コンパイラ実装は含まれません。BNFの解析・展開は非常に簡易です。
- 実際に動くインタープリタ／コンパイラを作るには、字句解析、構文解析（再帰下降等）、AST設計、意味解析、コード生成またはバイトコード実行環境の実装が必要です。必要であれば、特定言語向けの実装ステップを順を追って支援します。

必要なら、このテンプレートを拡張して（例: 完全なBNFパーサ、ANTLRやBison/Flex出力の自動組み込み、簡易ASTと実行器の実装）具体的な実装を一緒に作成します。どの言語をまず本格実装したいか教えてください。
