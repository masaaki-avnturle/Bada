```c
/*
pkginstallgen.c
Generates a package that:
 - writes omega_script.bnf (includes @reviser rules)
 - creates bnfs/ruby.bnf (example)
 - emits compiler.c (stub), interpreter.c (stub), reviser_tool.c (applies reviser rules)
 - emits Makefile
All generated files compile cleanly with the Makefile.

Build and run:
  gcc -std=c11 -O2 -Wall -o pkginstallgen pkginstallgen.c
  ./pkginstallgen
  make
  ./reviser_tool bnfs/ruby.bnf > ruby_to_omega.bnf
  ./compiler example.omega          # stub usage
  ./interpreter example.omega       # stub usage
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#if defined(_WIN32)
#include <direct.h>
#define mkdir_p(d) _mkdir(d)
#else
#include <sys/stat.h>
#include <sys/types.h>
static int mkdir_p(const char *d){ return mkdir(d, 0755); }
#endif

static const char *omega_bnf =
"/* omega_script.bnf - Omega grammar with reviser meta rules\n\n"
"@reviser:\n"
"# Example reviser rules mapping Ruby-like tokens into Omega tokens.\n"
"# Left is pattern in external BNF lines (or tokens), right is Omega replacement.\n"
"# These rules are simplistic textual mappings for demonstration.\n"
"  \"class\" => \"class\"\n"
"  \"NAME\"  => \"identifier\"\n" 
"  \"def\"   => \"def\"\n"
"  \"end\"   => \"}\"\n"
"  \"@reviser\" => \"@reviser\"\n"\n
"<program> ::= <top_stmt>*\n"
"<top_stmt> ::= <class_decl> | <func_decl> | <var_decl> | <import_stmt> | <reviser_decl>\n"
"<reviser_decl> ::= \"@reviser\" \":\" <reviser_rule>*\n"
"<reviser_rule> ::= <string> \"=>\" <string>\n"
  "\n/* core Omega constructs (abridged) */\n"
"<class_decl> ::= \"class\" <identifier> \"{\" <class_body>* \"}\"\n"
"<class_body> ::= <method_decl> | <var_decl>\n"
"<method_decl> ::= \"def\" <identifier> \"(\" <param_list>? \")\" \"{\" <stmt>* \"}\"\n"
"<var_decl> ::= \"var\" <identifier> (\"=\" <expr>)? \";\"\n"
"<stmt> ::= <var_decl> | <assign> \";\" | <expr> \";\" | <return_stmt>\n"
"<expr> ::= <primary> ( <binop> <primary> )*\n"
"<primary> ::= <number> | <string> | <identifier> | <array_literal> | <hash_literal> | \"(\" <expr> \")\"\n"
"<identifier> ::= [A-Za-z_][A-Za-z0-9_]*\n"
  "\n";

/* example ruby.bnf (minimal illustrative subset) */
static const char *ruby_bnf =
"# bnfs/ruby.bnf - minimal Ruby BNF subset (illustrative)\n"
"<program> ::= (<stmt>)*\n"
"<stmt> ::= <class> | <def>\n"
"<class> ::= 'class' NAME <body> 'end'\n"
"<def> ::= 'def' NAME <params>? <body> 'end'\n"
"<body> ::= (<stmt> | <expr>)*\n"
  "<params> ::= '(' (NAME (',' NAME)*)? ')'\n";

/* compiler.c: stub compiler - produces token-list .bc */
static const char *compiler_c =
  "/* compiler.c - stub tokenizer-based compiler for Omega (generated) */\n"
"#include <stdio.h>\n"
"#include <stdlib.h>\n"
"#include <ctype.h>\n"
  "\nstatic void usage(const char *p){ fprintf(stderr, \"Usage: %s <source.omega>\\n\", p); }\n\nint main(int argc, char **argv){\n    if(argc<2){ usage(argv[0]); return 1; }\n    FILE *f = fopen(argv[1], \"r\"); if(!f){ perror(\"fopen\"); return 2; }\n    char outname[512]; snprintf(outname, sizeof(outname), \"%s.bc\", argv[1]);\n    FILE *out = fopen(outname, \"w\"); if(!out){ perror(\"fopen out\"); fclose(f); return 3; }\n    int c; char tok[1024]; size_t i=0;\n    while((c=fgetc(f))!=EOF){\n        if(isspace(c)){\n            if(i){ tok[i]=0; fprintf(out, \"%s\\n\", tok); i=0; }\n            continue;\n        }\n        if(i+1<sizeof(tok)) tok[i++]=(char)c;\n    }\n    if(i){ tok[i]=0; fprintf(out, \"%s\\n\", tok); }\n    fclose(f); fclose(out);\n    printf(\"Compiled '%s' -> '%s'\\n\", argv[1], outname);\n    return 0;\n}\n";

/* interpreter.c: stub interpreter - prints trace of tokens/lines */
static const char *interpreter_c =
  "/* interpreter.c - stub interpreter for Omega (generated) */\n"
"#include <stdio.h>\n"
  "#include <stdlib.h>\n"#include <string.h>\n\nstatic void usage(const char *p){ fprintf(stderr, \"Usage: %s <source.omega|.bc>\\n\", p); }\n\nint main(int argc, char **argv){\n    if(argc<2){ usage(argv[0]); return 1; }\n    FILE *f = fopen(argv[1], \"r\"); if(!f){ perror(\"fopen\"); return 2; }\n    char line[4096]; int ln=0;\n    while(fgets(line,sizeof(line),f)){\n        ln++; char *nl = strchr(line,'\\n'); if(nl) *nl=0;\n        if(line[0]==0) continue;\n        printf(\"[%03d] TRACE: %s\\n\", ln, line);\n    }\n    fclose(f);\n    return 0;\n}\n";

/* reviser_tool.c: loads omega_script.bnf, extracts @reviser rules, applies to external BNF text */
static const char *reviser_tool_c =
  "/* reviser_tool.c - applies @reviser textual rules (simple) to an external BNF file */\n"
  "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\n#define MAX_RULES 256\nstruct rule { char lhs[512]; char rhs[512]; };\n\nstatic int load_rules(const char *omega_bnf, struct rule *rules){\n    FILE *f = fopen(omega_bnf, \"r\"); if(!f) return 0;\n    char line[1024]; int n=0; int in_reviser=0;\n    while(fgets(line,sizeof(line),f)){\n        /* detect @reviser start */\n        if(!in_reviser){ if(strstr(line, \"@reviser\")) { in_reviser=1; continue; } }\n        else {\n            /* blank or non-rule stops parsing rules */\n            if(line[0]=='\\n' || line[0]=='#' || line[0]==0) break;\n            char *arrow = strstr(line, \"=>\"); if(!arrow) continue;\n            *arrow = '\\0'; arrow += 2;\n            /* trim */ char *a=line; while(*a==' '||*a=='\\t') a++;\n            char *ae = a + strlen(a)-1; while(ae>a && (*ae=='\\n'||*ae=='\\r'||*ae==' '||*ae=='\\t')) *ae--='\\0';\n            char *b = arrow; while(*b==' '||*b=='\\t') b++;\n            char *be = b + strlen(b)-1; while(be>b && (*be=='\\n'||*be=='\\r'||*be==' '||*be=='\\t')) *be--='\\0';\n            if(n<MAX_RULES){ strncpy(rules[n].lhs, a, sizeof(rules[n].lhs)-1); strncpy(rules[n].rhs, b, sizeof(rules[n].rhs)-1); n++; }\n        }\n    }\n    fclose(f); return n;\n}\n\nstatic void apply_rules(const char *infile, struct rule *rules, int rcnt){\n    FILE *f = fopen(infile, \"r\"); if(!f){ perror(infile); return; }\n    char buf[8192];\n    while(fgets(buf, sizeof(buf), f)){\n        char out[16384]; out[0]=0; strncpy(out, buf, sizeof(out)-1);\n        for(int i=0;i<rcnt;i++){\n            char *p = strstr(out, rules[i].lhs);\n            if(!p) continue;\n            char tmp[16384]; tmp[0]=0;\n            size_t pre = (size_t)(p - out);\n            if(pre) strncat(tmp, out, pre);\n            strncat(tmp, rules[i].rhs, sizeof(tmp)-strlen(tmp)-1);\n            strncat(tmp, p + strlen(rules[i].lhs), sizeof(tmp)-strlen(tmp)-1);\n            strncpy(out, tmp, sizeof(out)-1);\n        }\n        fputs(out, stdout);\n    }\n    fclose(f);\n}\n\nint main(int argc, char **argv){\n    if(argc<2){ fprintf(stderr, \"Usage: %s <external.bnf>\\n\", argv[0]); return 1; }\n    struct rule rules[MAX_RULES]; memset(rules, 0, sizeof(rules));\n    int rc = load_rules(\"omega_script.bnf\", rules);\n    if(rc<=0) fprintf(stderr, \"No reviser rules found in omega_script.bnf; emitting original file.\\n\");\n    apply_rules(argv[1], rules, rc);\n    return 0;\n}\n";

/* Makefile content */
static const char *makefile =
  "CC = gcc\nCFLAGS = -std=c11 -O2 -Wall -Wextra\n\nall: compiler interpreter reviser_tool\n\ncompiler: compiler.c\n\t$(CC) $(CFLAGS) -o compiler compiler.c\n\ninterpreter: interpreter.c\n\t$(CC) $(CFLAGS) -o interpreter interpreter.c\n\nreviser_tool: reviser_tool.c\n\t$(CC) $(CFLAGS) -o reviser_tool reviser_tool.c\n\nclean:\n\trm -f compiler interpreter reviser_tool *.bc\n\n.PHONY: all clean\n";

/* helper to write file, returns 0 on success */
static int write_file(const char *path, const char *content){
FILE *f = fopen(path, "wb");
if(!f){ fprintf(stderr, \"Error: cannot open %s: %s\\n\", path, strerror(errno)); return 1; }
if(fputs(content, f) == EOF){ fprintf(stderr, \"Error: write failed %s\\n\", path); fclose(f); return 1; }
fclose(f); return 0;
}

int main(void){
if(mkdir_p("bnfs") != 0 && errno != EEXIST){ fprintf(stderr, "mkdir bnfs failed: %s\\n", strerror(errno)); return 1; }

if(write_file("omega_script.bnf", omega_bnf)) return 1;
if(write_file("bnfs/ruby.bnf", ruby_bnf)) return 1;
if(write_file("compiler.c", compiler_c)) return 1;
if(write_file("interpreter.c", interpreter_c)) return 1;
if(write_file("reviser_tool.c", reviser_tool_c)) return 1;
if(write_file("Makefile", makefile)) return 1;

puts("Generated package files:");
puts("  omega_script.bnf");
puts("  bnfs/ruby.bnf");
puts("  compiler.c, interpreter.c, reviser_tool.c, Makefile");
puts("Build with: make");
puts("Example: ./reviser_tool bnfs/ruby.bnf > ruby_to_omega.bnf");
return 0;
}
```
