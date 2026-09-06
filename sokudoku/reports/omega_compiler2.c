```c
/*
pkginstallgen.c
Usage: compile and run:
  gcc -std=c11 -O2 -Wall -o pkginstallgen pkginstallgen.c
  ./pkginstallgen
Produces files: omega_script.bnf, compiler.c, interpreter.c, Makefile
The generated compiler/interpreter are minimal but build cleanly.
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *bnf_content =
  "/* omega_script.bnf -- inferred minimal grammar for Omega Script (from report)\n   Nonterminals in UPPER, terminals in quotes. Comments and whitespace ignored.\n   This BNF is intentionally compact to cover: class, method, receiver, arrays,\n   semistatic-decl (semi-static), hash, regex literal, list, matrix, string, op-symbols\n*/\n\n<program>        ::= <top_stmt>*\n<top_stmt>       ::= <class_decl> | <func_decl> | <var_decl> | <import_stmt>\n<import_stmt>    ::= \"import\" <identifier> (\".\" <identifier>)*\n<class_decl>     ::= \"class\" <identifier> \"{\" <class_body>* \"}\"\n<class_body>     ::= <method_decl> | <var_decl>\n<method_decl>    ::= \"def\" <identifier> \"(\" <param_list>? \")\" \"{\" <stmt>* \"}\"\n<func_decl>      ::= \"def\" <identifier> \"(\" <param_list>? \")\" \"{\" <stmt>* \"}\"\n<param_list>     ::= <identifier> (\",\" <identifier>)*\n<var_decl>       ::= \"var\" <identifier> (\"=\" <expr>)? \";\"\n<stmt>           ::= <var_decl> | <assign> \";\" | <expr> \";\" | <return_stmt>\n<return_stmt>    ::= \"return\" <expr>? \";\"\n<assign>         ::= <lhs> (\"=\" | \":=\") <expr>\n<lhs>            ::= <identifier> | <member_expr> | <index_expr>\n<expr>           ::= <binary_expr>\n<binary_expr>    ::= <unary_expr> ( <binop> <unary_expr> )*\n<unary_expr>     ::= (\"-\" | \"!\" )* <primary>\n<primary>        ::= <number> | <string> | <regex> | <identifier> | <array_literal>\n                   | <hash_literal> | <list_literal> | <matrix_literal>\n                   | <call_expr> | \"(\" <expr> \")\" | <semistatic_decl>\n<call_expr>      ::= <primary> \"(\" <arg_list>? \")\"\n<arg_list>       ::= <expr> (\",\" <expr>)*\n<member_expr>    ::= <primary> \".\" <identifier>\n<index_expr>     ::= <primary> \"[\" <expr> \"]\"\n<array_literal>  ::= \"[\" (<expr> (\",\" <expr>)*)? \"]\"\n<list_literal>   ::= \"list\" \"{\" (<expr> (\",\" <expr>)*)? \"}\"\n<matrix_literal> ::= \"matrix\" \"{\" (<array_literal> (\",\" <array_literal>)*)? \"}\"\n<hash_literal>   ::= \"{\" (<hash_pair> (\",\" <hash_pair>)*)? \"}\"\n<hash_pair>      ::= <expr> \":\" <expr>\n<string>         ::= '\"' (~'\"')* '\"'\n<regex>          ::= '/' (~'/' )* '/'\n<semistatic_decl> ::= \"semi\" \"<\" <identifier> \">\" <identifier> (\"=\" <expr>)?\n<number>         ::= [0-9]+ (\".\" [0-9]+)?\n<identifier>     ::= [A-Za-z_][A-Za-z0-9_]*\n<binop>          ::= \"+\" | \"-\" | \"*\" | \"/\" | \"%\" | \"==\" | \"!=\" | \"<\" | \">\" | \"<=\" | \">=\" | \"&&\" | \"||\" | \"->\" | \"=>\"\n\n/* Notes: - 'semi<name> id = expr' models the semi-static declaration (半静止型宣言子)\n          - member, receiver and op-symbols use '.' and symbolic tokens like '->' '=>'\n          - regex literal is /.../; matrix/list/hash/array cover complex objects\n*/\n";

static const char *compiler_c_template =
  "/* compiler.c -- minimal generator that parses tokens and emits a stub bytecode file */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\nstatic void usage(const char *p){ fprintf(stderr, \"Usage: %s <source.omega>\\n\", p); }\n\nint main(int argc, char **argv){\n    if(argc<2){ usage(argv[0]); return 1; }\n    FILE *f = fopen(argv[1], \"r\"); if(!f){ perror(\"fopen\"); return 2; }\n    char outname[512]; snprintf(outname, sizeof(outname), \"%s.bc\", argv[1]);\n    FILE *out = fopen(outname, \"wb\"); if(!out){ perror(\"fopen out\"); fclose(f); return 3; }\n    fseek(f,0,SEEK_END); long sz = ftell(f); fseek(f,0,SEEK_SET);\n    char *buf = malloc((size_t)sz+1);\n    if(!buf){ perror(\"malloc\"); fclose(f); fclose(out); return 4; }\n    fread(buf,1,sz,f); buf[sz]=0;\n    /* Very small token pass: write each non-space token as a line into .bc */\n    const char *p = buf; while(*p){\n        while(*p && (*p==' '||*p=='\\n'||*p=='\\r'||*p=='\\t')) ++p;\n        if(!*p) break;\n        const char *start = p; while(*p && *p!=' ' && *p!='\\n' && *p!='\\t' && *p!='\\r') ++p;\n        fwrite(start,1,(size_t)(p-start),out); fputc('\\n',out);\n    }\n    free(buf); fclose(f); fclose(out);\n    printf(\"Compiled '%s' -> '%s' (token-list stub)\\n\", argv[1], outname);\n    return 0;\n}\n";

static const char *interpreter_c_template =
  "/* interpreter.c -- minimal interpreter that reads .omega or .bc token-list and prints execution trace */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\nstatic void usage(const char *p){ fprintf(stderr, \"Usage: %s <source.omega|.bc>\\n\", p); }\n\nint main(int argc, char **argv){\n    if(argc<2){ usage(argv[0]); return 1; }\n    FILE *f = fopen(argv[1], \"r\"); if(!f){ perror(\"fopen\"); return 2; }\n    char line[4096];\n    printf(\"Omega Interpreter (trace mode)\\n\");\n    int lineno = 0;\n    while(fgets(line,sizeof(line),f)){\n        ++lineno;\n        /* trim newline */ char *nl = strchr(line,'\\n'); if(nl) *nl=0;\n        if(strlen(line)==0) continue;\n        printf(\"[%03d] EXEC: %s\\n\", lineno, line);\n        /* demo: detect simple statements */\n        if(strncmp(line,\"return\",6)==0) { printf(\"  -> return encountered\\n\"); }\n        if(strstr(line,\"class \")==line) { printf(\"  -> class declaration\\n\"); }\n    }\n    fclose(f);\n    return 0;\n}\n";

static const char *makefile_template =
  "CC = gcc\nCFLAGS = -std=c11 -O2 -Wall -Wextra\n\nall: compiler interpreter\n\ncompiler: compiler.c\n\t$(CC) $(CFLAGS) -o compiler compiler.c\n\ninterpreter: interpreter.c\n\t$(CC) $(CFLAGS) -o interpreter interpreter.c\n\nclean:\n\trm -f compiler interpreter *.bc\n\n.PHONY: all clean\n";

static int writefile(const char *path, const char *content){
  FILE *f = fopen(path, "wb");
  if(!f){ perror(path); return 1; }
  if(fputs(content, f) == EOF){ perror(\"fputs\"); fclose(f); return 1; }
  fclose(f); return 0;
}

int main(void){
  if(writefile(\"omega_script.bnf\", bnf_content)) return 1;
  if(writefile(\"compiler.c\", compiler_c_template)) return 1;
  if(writefile(\"interpreter.c\", interpreter_c_template)) return 1;
  if(writefile(\"Makefile\", makefile_template)) return 1;
  puts(\"Generated: omega_script.bnf, compiler.c, interpreter.c, Makefile\"); 
  puts(\"Run 'make' to build the generated compiler and interpreter.\"); 
  return 0;
}
```
