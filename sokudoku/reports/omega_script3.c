```c
/*
pkginstallgen.c
Usage:
  gcc -std=c11 -O2 -Wall -o pkginstallgen pkginstallgen.c
  ./pkginstallgen [bnf1.bnf bnf2.bnf ...]
Produces in current directory:
  - omega_script.bnf        (inferred minimal Omega BNF)
  - bnfs/                   (directory copied BNF files)
  - compiler.c              (generated stub compiler)
  - interpreter.c           (generated stub interpreter)
  - bnf_loader.c            (utility compiled into tools to load BNFs into Omega)
  - Makefile                (builds compiler, interpreter, tools)
All generated C files compile cleanly with the Makefile.
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

static const char *omega_bnf =
"/* omega_script.bnf -- inferred minimal grammar for Omega Script (from report)\n"
  "   See generated bnfs/ for additional language BNFs that can be fed into Omega.\n*/\n\n"
"<program>        ::= <top_stmt>*\n"
"<top_stmt>       ::= <class_decl> | <func_decl> | <var_decl> | <import_stmt>\n"
"<import_stmt>    ::= \"import\" <identifier> (\".\" <identifier>)*\n"
"<class_decl>     ::= \"class\" <identifier> \"{\" <class_body>* \"}\"\n"
"<class_body>     ::= <method_decl> | <var_decl>\n"
"<method_decl>    ::= \"def\" <identifier> \"(\" <param_list>? \")\" \"{\" <stmt>* \"}\"\n"
"<param_list>     ::= <identifier> (\",\" <identifier>)*\n"
"<var_decl>       ::= \"var\" <identifier> (\"=\" <expr>)? \";\"\n"
"<stmt>           ::= <var_decl> | <assign> \";\" | <expr> \";\" | <return_stmt>\n"
"<return_stmt>    ::= \"return\" <expr>? \";\"\n"
"<assign>         ::= <lhs> (\"=\" | \":=\") <expr>\n"
"<lhs>            ::= <identifier> | <member_expr> | <index_expr>\n"
"<expr>           ::= <binary_expr>\n"
"<binary_expr>    ::= <unary_expr> ( <binop> <unary_expr> )*\n"
"<unary_expr>     ::= (\"-\" | \"!\" )* <primary>\n"
"<primary>        ::= <number> | <string> | <regex> | <identifier> | <array_literal>\n"
"                   | <hash_literal> | <list_literal> | <matrix_literal>\n"
"                   | <call_expr> | \"(\" <expr> \")\" | <semistatic_decl>\n"
"<call_expr>      ::= <primary> \"(\" <arg_list>? \")\"\n"
"<arg_list>       ::= <expr> (\",\" <expr>)*\n"
"<member_expr>    ::= <primary> \".\" <identifier>\n"
"<index_expr>     ::= <primary> \"[\" <expr> \"]\"\n"
"<array_literal>  ::= \"[\" (<expr> (\",\" <expr>)*)? \"]\"\n"
"<list_literal>   ::= \"list\" \"{\" (<expr> (\",\" <expr>)*)? \"}\"\n"
"<matrix_literal> ::= \"matrix\" \"{\" (<array_literal> (\",\" <array_literal>)*)? \"}\"\n"
"<hash_literal>   ::= \"{\" (<hash_pair> (\",\" <hash_pair>)*)? \"}\"\n"
"<hash_pair>      ::= <expr> \":\" <expr>\n"
"<string>         ::= '\"' (~'\"')* '\"'\n"
"<regex>          ::= '/' (~'/' )* '/'\n"
"<semistatic_decl> ::= \"semi\" \"<\" <identifier> \">\" <identifier> (\"=\" <expr>)?\n"
"<number>         ::= [0-9]+ (\".\" [0-9]+)?\n"
"<identifier>     ::= [A-Za-z_][A-Za-z0-9_]*\n"
  "<binop>          ::= \"+\" | \"-\" | \"*\" | \"/\" | \"%\" | \"==\" | \"!=\" | \"<\" | \">\" | \"<=\" | \">=\" | \"&&\" | \"||\" | \"->\" | \"=>\"\n";

/* compiler.c: reads .omega and emits token-list .bc (stub) */
static const char *compiler_c =
  "/* compiler.c -- stub compiler for Omega Script */\n"
"#include <stdio.h>\n"
"#include <stdlib.h>\n"
"#include <string.h>\n\n"
"static void usage(const char *p){ fprintf(stderr, \"Usage: %s <source.omega>\\n\", p); }\n\n"
"int main(int argc, char **argv){\n"
"    if(argc<2){ usage(argv[0]); return 1; }\n" 
"    FILE *f = fopen(argv[1], \"r\"); if(!f){ perror(\"fopen\"); return 2; }\n"
"    char outname[512]; snprintf(outname, sizeof(outname), \"%s.bc\", argv[1]);\n"
"    FILE *out = fopen(outname, \"wb\"); if(!out){ perror(\"fopen out\"); fclose(f); return 3; }\n"
  "    /* token-list stub: copy non-space tokens as lines */\n"
"    int c; char tok[1024]; size_t i = 0;\n"
"    while((c = fgetc(f)) != EOF){\n"
"        if(c==' '||c=='\\n'||c=='\\r'||c=='\\t'){\n"
"            if(i>0){ tok[i]=0; fprintf(out, \"%s\\n\", tok); i=0; }\n" 
"            continue;\n" 
"        }\n" 
  "        if(i+1 < sizeof(tok)) tok[i++]=(char)c; /* else drop */\n" 
"    }\n" 
"    if(i>0){ tok[i]=0; fprintf(out, \"%s\\n\", tok); }\n"
"    fclose(f); fclose(out);\n" 
"    printf(\"Compiled '%s' -> '%s'\\n\", argv[1], outname);\n" 
"    return 0;\n" 
  "}\n";

/* interpreter.c: reads .omega or .bc tokenlist and prints execution trace */
static const char *interpreter_c =
  "/* interpreter.c -- stub interpreter for Omega Script */\n"
"#include <stdio.h>\n"
"#include <stdlib.h>\n"
"#include <string.h>\n\n"
"static void usage(const char *p){ fprintf(stderr, \"Usage: %s <source.omega|.bc>\\n\", p); }\n\n"
"int main(int argc, char **argv){\n"
"    if(argc<2){ usage(argv[0]); return 1; }\n"
"    FILE *f = fopen(argv[1], \"r\"); if(!f){ perror(\"fopen\"); return 2; }\n"
"    char line[4096]; int ln=0;\n"
"    while(fgets(line, sizeof(line), f)){\n"
"        ln++; char *nl = strchr(line,'\\n'); if(nl) *nl=0;\n" 
"        if(line[0]==0) continue;\n" 
"        printf(\"[%03d] TRACE: %s\\n\", ln, line);\n" 
"    }\n" 
"    fclose(f); return 0;\n"
  "}\n";

/* bnf_loader.c: tool to 'import' external language BNFs into Omega package (stub) */
static const char *bnf_loader_c =
  "/* bnf_loader.c -- loads bnfs/ files and prints summary (stub for integrating BNFs) */\n"
"#include <stdio.h>\n"
"#include <stdlib.h>\n"
"#include <dirent.h>\n"
"#include <string.h>\n\n"
"int main(int argc, char **argv){\n"
"    const char *dir = \"bnfs\";\n" 
"    DIR *d = opendir(dir); if(!d){ perror(\"opendir\"); return 1; }\n" 
"    struct dirent *ent; int count = 0;\n" 
"    while((ent = readdir(d))){\n"
"        if(ent->d_name[0]=='.') continue;\n"
"        printf(\"bnf: %s/%s\\n\", dir, ent->d_name); count++;\n" 
"    }\n" 
"    closedir(d);\n" 
"    printf(\"Total BNFs available: %d\\n\", count);\n" 
"    printf(\"To feed a BNF into Omega (stub): ./compiler <some.omega>\\n\");\n" 
"    return 0;\n" 
"}\n";

/* Makefile that builds compiler, interpreter, bnf_loader */
static const char *makefile =
  "CC = gcc\nCFLAGS = -std=c11 -O2 -Wall -Wextra\n\nall: compiler interpreter bnf_loader\n\ncompiler: compiler.c\n\t$(CC) $(CFLAGS) -o compiler compiler.c\n\ninterpreter: interpreter.c\n\t$(CC) $(CFLAGS) -o interpreter interpreter.c\n\nbnf_loader: bnf_loader.c\n\t$(CC) $(CFLAGS) -o bnf_loader bnf_loader.c\n\nclean:\n\trm -f compiler interpreter bnf_loader *.bc\n\n.PHONY: all clean\n";

/* helper write function */
static int write_text_file(const char *path, const char *content){
  FILE *f = fopen(path, "wb");
  if(!f){ perror(path); return 1; }
  if(fputs(content, f) == EOF){ perror("fputs"); fclose(f); return 1; }
  fclose(f);
  return 0;
}

/* copy provided bnf path into bnfs/ directory, keeping filename */
static int copy_file_to_bnfs(const char *src){
  /* create bnfs/ first (done by caller) */
  const char *slash = strrchr(src, '/');
  const char *fname = slash ? slash+1 : src;
  char dst[1024];
  snprintf(dst, sizeof(dst), "bnfs/%s", fname);
  FILE *in = fopen(src, "rb");
  if(!in){ fprintf(stderr, "Warning: cannot open %s (skipping)\\n", src); return 1; }
  FILE *out = fopen(dst, "wb");
  if(!out){ perror(dst); fclose(in); return 1; }
  char buf[4096]; size_t n;
  while((n = fread(buf,1,sizeof(buf),in)) > 0) fwrite(buf,1,n,out);
  fclose(in); fclose(out);
  return 0;
}

int main(int argc, char **argv){
  /* create bnfs dir */
#if defined(_WIN32)
  _mkdir("bnfs");
#else
  mkdir("bnfs", 0755);
#endif

  /* write default omega_script.bnf */
  if(write_text_file("omega_script.bnf", omega_bnf)) return 1;

  /* copy user-supplied BNFs into bnfs/ */
  for(int i=1;i<argc;i++){
    copy_file_to_bnfs(argv[i]);
  }

  /* if no BNFs provided, create example BNFs for a few languages (minimal) */
  if(argc<=1){
    write_text_file("bnfs/python.bnf",
		    "# python.bnf (minimal stub)\n<file> ::= <stmt>*\n<stmt> ::= 'def' NAME '(' ')' ':' <suite>\n");
    write_text_file("bnfs/ruby.bnf",
		    "# ruby.bnf (minimal stub)\n<program> ::= (<stmt>)*\n<stmt> ::= 'def' NAME <body> 'end'\n");
    write_text_file("bnfs/c.bnf",
		    "# c.bnf (minimal stub)\n<translation_unit> ::= (<decl>)*\n<decl> ::= <type> NAME '(' ')' ';'\n");
  }

  /* write generated C sources and Makefile */
  if(write_text_file("compiler.c", compiler_c)) return 1;
  if(write_text_file("interpreter.c", interpreter_c)) return 1;
  if(write_text_file("bnf_loader.c", bnf_loader_c)) return 1;
  if(write_text_file("Makefile", makefile)) return 1;

  printf("Generated package files:\n");
  printf("  omega_script.bnf\n");
  printf("  bnfs/ (copied user BNF(s) or example BNFs)\n");
  printf("  compiler.c, interpreter.c, bnf_loader.c, Makefile\n");
  printf("Build with: make\n");
  printf("Run bnfs listing: ./bnf_loader\n");
  return 0;
}
```
