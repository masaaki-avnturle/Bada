  /* pkginstallgen.c
   Generate Omega Script full-package skeleton:
   - Interpreter (lexer, parser stub, AST skeleton, evaluator skeleton)
   - Compiler to simple bytecode and stack VM
   - Runtime skeleton (values, objects, arrays, hashes, exceptions)
   - Standard library placeholders (IO, string, array, regex wrappers)
   - Build scripts, tests, examples, README
   Safety: Explicitly excludes any functionality to design, generate, or simulate chemical
           compounds, biological agents, or perform in-silico drug discovery. Intended
           only for language/algorithm/quantum-DSL education and prototyping.
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
  char *p;
  size_t len;
  snprintf(tmp, sizeof(tmp), "%s", path);
    len = strlen(tmp);
    if (len == 0) return;
    if (tmp[len-1] == '/') tmp[len-1] = 0;
    for (p = tmp + 1; *p; ++p) {
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
    if (!f) {
        fprintf(stderr, "write_file: cannot open %s\n", path);
		return -1;
		}
		fwrite(data, 1, strlen(data), f);
		fclose(f);
		return 0;
		}

		int main(int argc, char **argv) {
		const char *out = "omega_package";
		if (argc > 1) out = argv[1];
		char buf[8192];

		/* create directories */
		snprintf(buf, sizeof(buf), "%s/bin", out); mkdir_p(buf);
		snprintf(buf, sizeof(buf), "%s/lib", out); mkdir_p(buf);
		snprintf(buf, sizeof(buf), "%s/include", out); mkdir_p(buf);
		snprintf(buf, sizeof(buf), "%s/src", out); mkdir_p(buf);
		snprintf(buf, sizeof(buf), "%s/etc", out); mkdir_p(buf);
		snprintf(buf, sizeof(buf), "%s/usr/share/omega/examples", out); mkdir_p(buf);
		snprintf(buf, sizeof(buf), "%s/tests", out); mkdir_p(buf);
		snprintf(buf, sizeof(buf), "%s/doc", out); mkdir_p(buf);

		/* include/omega.h */
    const char *omega_h =
		"/* include/omega.h - public API for Omega Script (skeleton) */\n#ifndef OMEGA_H\n#define OMEGA_H\n#include <stdint.h>\n\ntypedef enum { VT_NULL, VT_NUMBER, VT_STRING, VT_BOOL, VT_OBJECT, VT_ARRAY, VT_HASH, VT_FUNC } VType;\n\ntypedef struct Value { VType type; union { double num; char *str; int boolean; void *ptr; } u; } Value;\n\n/* interpreter & vm entrypoints */\nint omega_interp_run_file(const char *path, int argc, char **argv);\nint omega_vm_run_file(const char *path, int argc, char **argv);\n\n/* value constructors */\nValue val_null(void); Value val_number(double); Value val_string(const char*); Value val_bool(int);\n#endif\n";
		snprintf(buf, sizeof(buf), "%s/include/omega.h", out);
		write_file(buf, omega_h);

		/* src/lexer.h */
    const char *lexer_h =
		"/* src/lexer.h - minimal token definitions */\n#ifndef OMEGA_LEXER_H\n#define OMEGA_LEXER_H\ntypedef enum { TK_EOF=0, TK_ID, TK_NUMBER, TK_STRING, TK_OP, TK_KEYWORD } TokenKind;\ntypedef struct Token { TokenKind kind; char *text; } Token;\nvoid lexer_init(const char *src);\nToken lexer_next(void);\n#endif\n";
		snprintf(buf, sizeof(buf), "%s/src/lexer.h", out);
		write_file(buf, lexer_h);

		/* src/lexer.c */
    const char *lexer_c =
		"/* src/lexer.c - simple lexer (not fully robust; demo only) */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <ctype.h>\n#include \"lexer.h\"\nstatic const char *s; static size_t pos, len;\nvoid lexer_init(const char *src){ s = src?src:\"\"; pos=0; len=strlen(s); }\nstatic void skip_ws(){ while(pos<len && (s[pos]==' '||s[pos]=='\\t'||s[pos]=='\\r'||s[pos]=='\\n')) pos++; }\nToken lexer_next(){ skip_ws(); Token t; t.kind=TK_EOF; t.text=NULL; if(pos>=len) return t; char c=s[pos];\n if (isalpha((unsigned char)c)||c=='_'){ size_t st=pos++; while(pos<len && (isalnum((unsigned char)s[pos])||s[pos]=='_')) pos++; size_t l=pos-st; char *id=malloc(l+1); memcpy(id,s+st,l); id[l]=0; /* keywords */ if(!strcmp(id,\"class\")||!strcmp(id,\"func\")||!strcmp(id,\"var\")||!strcmp(id,\"if\")||!strcmp(id,\"else\")||!strcmp(id,\"return\")||!strcmp(id,\"new\")||!strcmp(id,\"try\")||!strcmp(id,\"catch\")||!strcmp(id,\"operator\")) t.kind=TK_KEYWORD; else t.kind=TK_ID; t.text=id; return t; }\n if (isdigit((unsigned char)c)){ size_t st=pos++; while(pos<len && (isdigit((unsigned char)s[pos])||s[pos]=='.')) pos++; size_t l=pos-st; char *num=malloc(l+1); memcpy(num,s+st,l); num[l]=0; t.kind=TK_NUMBER; t.text=num; return t; }\n if (c=='\\\"' || c=='\\'') { char q=c; pos++; size_t st=pos; while(pos<len && s[pos]!=q){ if (s[pos]=='\\\\') pos+=2; else pos++; } size_t l=pos-st; char *str=malloc(l+1); memcpy(str,s+st,l); str[l]=0; if(pos<len) pos++; t.kind=TK_STRING; t.text=str; return t; }\n if (strchr(\"+-*/%^=<>!&|,.:;(){}[]\", c)) { char op[3]={0}; op[0]=c; pos++; if(pos<len){ char c2=s[pos]; if((c=='='&&c2=='=')||(c=='!'&&c2=='=')||(c=='<'&&c2=='=')||(c=='>'&&c2=='=')||(c=='&'&&c2=='&')||(c=='|'&&c2=='|')){ op[1]=c2; pos++; }} t.kind=TK_OP; t.text=strdup(op); return t; }\n pos++; return lexer_next(); }\n";
		snprintf(buf, sizeof(buf), "%s/src/lexer.c", out);
		write_file(buf, lexer_c);

		/* src/parser.h and parser.c (stubs) */
    const char *parser_h =
		"/* src/parser.h - parser stub interface */\n#ifndef OMEGA_PARSER_H\n#define OMEGA_PARSER_H\n#include \"ast.h\"\nASTNode* parser_parse(const char *src);\n#endif\n";
		snprintf(buf, sizeof(buf), "%s/src/parser.h", out);
		write_file(buf, parser_h);

    const char *parser_c =
		"/* src/parser.c - parser stub (returns NULL AST in skeleton) */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include \"parser.h\"\nASTNode* parser_parse(const char *src){ (void)src; return NULL; }\n";
		snprintf(buf, sizeof(buf), "%s/src/parser.c", out);
		write_file(buf, parser_c);

		/* src/ast.h & ast.c (very small) */
    const char *ast_h =
		"/* src/ast.h - AST skeleton */\n#ifndef OMEGA_AST_H\n#define OMEGA_AST_H\ntypedef struct ASTNode { int kind; /* payload omitted in skeleton */ } ASTNode;\nvoid ast_free(ASTNode*);\n#endif\n";
		snprintf(buf, sizeof(buf), "%s/src/ast.h", out);
		write_file(buf, ast_h);

    const char *ast_c =
		"#include <stdlib.h>\n#include \"ast.h\"\nvoid ast_free(ASTNode *n){ (void)n; }\n";
		snprintf(buf, sizeof(buf), "%s/src/ast.c", out);
		write_file(buf, ast_c);

		/* src/eval.c - interpreter runner (reads file and echoes + placeholder) */
    const char *eval_c =
		"/* src/eval.c - interpreter skeleton (safe demo) */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include \"../include/omega.h\"\nValue val_null(void){ Value v; v.type=VT_NULL; return v; }\nValue val_number(double x){ Value v; v.type=VT_NUMBER; v.u.num=x; return v; }\nValue val_string(const char*s){ Value v; v.type=VT_STRING; v.u.str=strdup(s?s:\"\"); return v; }\nValue val_bool(int b){ Value v; v.type=VT_BOOL; v.u.boolean = b?1:0; return v; }\nint omega_interp_run_file(const char *path, int argc, char **argv){ (void)argc; (void)argv; FILE*f=fopen(path,\"rb\"); if(!f){ perror(\"open\"); return 2; } fseek(f,0,SEEK_END); long sz=ftell(f); fseek(f,0,SEEK_SET); char *src=malloc(sz+1); fread(src,1,sz,f); src[sz]=0; fclose(f);\n printf(\"[Omega Interpreter] Running '%s' (length=%ld)\\n\", path, sz);\n printf(\"--- source start ---\\n%s\\n--- source end ---\\n\", src);\n /* In full implementation: parse and execute AST here. */\n free(src); return 0; }\nint omega_vm_run_file(const char *path, int argc, char **argv){ (void)path; (void)argc; (void)argv; printf(\"[Omega VM] VM run not implemented in skeleton. Use demo mode.\\n\"); return 0; }\n";
		snprintf(buf, sizeof(buf), "%s/src/eval.c", out);
		write_file(buf, eval_c);

		/* src/bytecode.c - simple VM demo */
    const char *bytecode_c =
		"/* src/bytecode.c - simple stack VM demo */\n#include <stdio.h>\n#include <string.h>\n#include <stdlib.h>\n#include \"../include/omega.h\"\nenum { OP_HALT=0, OP_CONST, OP_ADD, OP_PRINT };\nint omega_vm_run(const unsigned char *code, size_t n){ size_t ip=0; double stack[256]; int sp=0; while(ip<n){ unsigned char op=code[ip++]; switch(op){ case OP_HALT: return 0; case OP_CONST:{ if(ip+8>n) return -1; double val; memcpy(&val, code+ip, sizeof(double)); ip+=8; stack[sp++]=val; break;} case OP_ADD:{ double b=stack[--sp]; double a=stack[--sp]; stack[sp++]=a+b; break;} case OP_PRINT:{ double a=stack[--sp]; printf(\"VM PRINT: %g\\n\", a); break;} default: return -2; } } return 0; }\nint omega_vm_demo_run(void){ unsigned char code[256]; size_t ip=0; double a=1.0,b=2.0; code[ip++]=OP_CONST; memcpy(code+ip,&a,8); ip+=8; code[ip++]=OP_CONST; memcpy(code+ip,&b,8); ip+=8; code[ip++]=OP_ADD; code[ip++]=OP_PRINT; code[ip++]=OP_HALT; return omega_vm_run(code, ip); }\n";
		snprintf(buf, sizeof(buf), "%s/src/bytecode.c", out);
		write_file(buf, bytecode_c);

		/* src/main.c - CLI */
    const char *main_c =
		"/* src/main.c - CLI (interp|vm|demo) */\n#include <stdio.h>\n#include <string.h>\n#include \"../include/omega.h\"\nint omega_vm_demo_run(void);\nint main(int argc, char **argv){ if(argc<2){ fprintf(stderr,\"Usage: %s {interp|vm|demo} file\\n\", argv[0]); return 2; } if(strcmp(argv[1],\"interp\")==0){ if(argc<3){ fprintf(stderr,\"interp requires file\\n\"); return 2;} return omega_interp_run_file(argv[2], argc-2, argv+2);} else if(strcmp(argv[1],\"vm\")==0){ if(argc<3){ fprintf(stderr,\"vm requires bytecode file\\n\"); return 2;} return omega_vm_run_file(argv[2], argc-2, argv+2);} else if(strcmp(argv[1],\"demo\")==0){ return omega_vm_demo_run(); } fprintf(stderr,\"unknown command\\n\"); return 2; }\n";
		snprintf(buf, sizeof(buf), "%s/src/main.c", out);
		write_file(buf, main_c);

		/* lib/omega.bnf grammar (educational) */
    const char *omega_bnf =
		"# lib/omega.bnf - educational grammar skeleton for Omega Script\n<program> ::= <stmt_list>\n<stmt_list> ::= <stmt> | <stmt> <stmt_list>\n<stmt> ::= <expr_stmt> ';' | var <id> ';' | func <id> '(' <params_opt> ')' '{' <stmt_list_opt> '}' | class <id> '{' <class_body> '}'\n<expr_stmt> ::= <expr>\n<expr> ::= <assign>\n<assign> ::= <logic> | <id> '=' <assign>\n<logic> ::= <equality> ( ( '&&' | '||' ) <equality> )*\n<equality> ::= <rel> ( ('=='|'!=') <rel> )*\n<rel> ::= <add> ( ('<'|'>'|'<='|'>=') <add> )*\n<add> ::= <mul> ( ('+'|'-') <mul> )*\n<mul> ::= <unary> ( ('*'|'/'|'%') <unary> )*\n<unary> ::= ('+'|'-'|'!') <unary> | <primary>\n<primary> ::= <id> | <number> | <string> | '(' <expr> ')' | '[' <arglist_opt> ']'\n";
		snprintf(buf, sizeof(buf), "%s/lib/omega.bnf", out);
		write_file(buf, omega_bnf);

		/* lib/stdlib.os (placeholders) */
    const char *stdlib =
		"// lib/stdlib.os - standard library placeholders (no chemistry/biological features)\nfunc print(x) { /* bound to runtime print */ }\nfunc len(x) { /* array/string length */ }\n";
		snprintf(buf, sizeof(buf), "%s/lib/stdlib.os", out);
		write_file(buf, stdlib);

		/* usr example: qsim.os (quantum-circuit symbolic example; safe) */
    const char *example =
		"// usr/share/omega/examples/qsim.os - symbolic quantum-DSL example (no hardware control)\nfunc hadamard(q) { /* symbolic op */ return q; }\nvar q = [1,0];\nq = hadamard(q);\nprint(q);\n";
		snprintf(buf, sizeof(buf), "%s/usr/share/omega/examples/qsim.os", out);
		write_file(buf, example);

		/* tests/hello.os */
		const char *test_hello = "print(1 + 2 * 3);\n";
		snprintf(buf, sizeof(buf), "%s/tests/hello.os", out);
		write_file(buf, test_hello);

		/* bin scripts */
    const char *bin_build =
		"#!/bin/sh\nset -e\nmkdir -p build\ngcc -std=c99 -O2 -Iinclude src/*.c -o build/omega 2>/dev/null || true\nif [ -x build/omega ]; then echo \"Built build/omega\"; else echo \"Build failed (check gcc output)\"; fi\n";
		snprintf(buf, sizeof(buf), "%s/bin/build.sh", out);
		write_file(buf, bin_build);

		const char *bin_run_interp = "#!/bin/sh\nif [ $# -lt 1 ]; then echo \"Usage: run-interp file.os\"; exit 2; fi\n./build/omega interp \"$1\"\n";
		snprintf(buf, sizeof(buf), "%s/bin/run-interp", out);
		write_file(buf, bin_run_interp);

    const char *bin_test =
		"#!/bin/sh\nset -e\n./bin/build.sh\n./build/omega demo\n./build/omega interp usr/share/omega/examples/qsim.os\n";
		snprintf(buf, sizeof(buf), "%s/bin/test.sh", out);
		write_file(buf, bin_test);

		/* Makefile */
    const char *makefile =
		"all: build\nbuild:\n\t@mkdir -p build\n\t@gcc -std=c99 -O2 -Iinclude src/*.c -o build/omega 2>/dev/null || true\n\t@if [ -x build/omega ]; then echo \"build/omega ready\"; else echo \"Build failed (see output)\"; fi\nclean:\n\trm -rf build\n";
		snprintf(buf, sizeof(buf), "%s/Makefile", out);
		write_file(buf, makefile);

		/* doc/README.md (explicit safety note) */
    const char *readme =
		"# Omega Script package (generated skeleton)\n\nThis package is an educational/research language-processing skeleton (interpreter + compiler+VM + stdlib placeholders).\nIMPORTANT: This package explicitly DOES NOT include any functionality for designing, generating, or validating chemical compounds, biological agents, or drugs. It must not be used for any such purposes.\n\nBuild and run:\n  cd <package>\n  make\n  ./build/omega interp usr/share/omega/examples/qsim.os\n\nExtend parser, AST, evaluator and VM as needed for research/education.\n";
		snprintf(buf, sizeof(buf), "%s/doc/README.md", out);
		write_file(buf, readme);

		/* set execute bits on POSIX */
#ifndef _WIN32
		{
		  char cmd[8192];
		  snprintf(cmd, sizeof(cmd),
			   "chmod +x \"%s/bin/build.sh\" \"%s/bin/run-interp\" \"%s/bin/test.sh\" 2>/dev/null || true",
			   out, out, out);
		  system(cmd);
		}
#endif

		printf("Omega package skeleton (interpreter+compiler+VM) created at: %s\n", out);
		printf("Safety: package contains NO chemical/biological/drug-design functionality.\n");
		printf("Next: cd %s && make && ./build/omega interp usr/share/omega/examples/qsim.os\n", out);
		return 0;
    }
