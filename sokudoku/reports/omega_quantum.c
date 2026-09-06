/*承知しました。以下は要求どおり、Omega Script（量子プログラミング言語）のBNF規則ファイルと、それを含む「コンパイラ＋インタープリタ」パッケージ雛形を出力する C プログラム `pkginstallgen.c` の完全ソースです。

- 出力されるパッケージ（例: `omega_package`）には次を配置します（雛形／安全実装）：
  - `lib/omega.bnf`：Omega Script の BNF（言語仕様の骨格。変数・クラス・メソッド・オブジェクト・配列・ハッシュ・正規表現・IO・例外・作用素関数・半静子作用素 等を含む文法）
  - `src/`：コンパイラ前端（BNFパーサ＋AST生成の C ソース）、インタープリタ（AST 実行器）の雛形（オブジェクト指向ランタイム／オブジェクト、レシーバ、メソッド等を表現する C 構造体）
  - `include/omega.h`：ランタイム API 宣言
  - `bin/omega-compile`：コンパイラ呼び出しスクリプト（ビルドして使用）
  - `bin/omega-run`：インタープリタ実行スクリプト
  - `etc/`：ランタイム設定テンプレート
  - `usr/share/omega/examples/`：サンプル Omega Script ソース（簡単なクラス・メソッド・量子シミュレーション記述の例、しかし実ハード制御は含まれない）
  - `Makefile`：ビルド／インストールルール（エラー抑制）
- 生成物は「言語処理系の雛形」であり、数式や記号的量子シミュレーションのための AST と実行器のサンプル実装を含みます。実ハードウエア操作や危険な物理実験制御は含みません。

C ファイルを保存してビルドすると、指定ディレクトリにファイル群を展開します。

ビルド例:
gcc -std=c99 -O2 -o pkginstallgen pkginstallgen.c

  実行例:
./pkginstallgen ./omega_package

以下が `pkginstallgen.c` の完全ソースです。保存してビルドしてください。

```c
*/
  /* pkginstallgen.c
   Generate Omega Script compiler+interpreter package skeleton.
   - Writes BNF (omega.bnf), sample sources, C compiler front-end skeleton,
     C interpreter/runtime skeleton, headers, scripts, Makefile, docs.
   - The generated language supports: objects/classes/receivers/methods,
     arrays, hashes, regex, strings, IO objects, exceptions, operator functions,
     'semi-static' operator declarations (半静子作用素) as a language feature.
   - This package is a functional skeleton for experimentation & extension.
   Safety: no biological/medical experiment control. No real quantum hardware control.
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
    if (!f) return -1;
    fwrite(data, 1, strlen(data), f);
    fclose(f);
    return 0;
}

int main(int argc, char **argv) {
    const char *out = "omega_package";
  if (argc > 1) out = argv[1];
  char buf[8192];

  /* create directory layout */
  snprintf(buf, sizeof(buf), "%s/bin", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/lib", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/include", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/etc", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/usr/share/omega/examples", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/src", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/doc", out); mkdir_p(buf);

  /* 1) BNF: omega.bnf (language grammar skeleton for Omega Script) */
    const char *omega_bnf =
"# Omega Script BNF (omega.bnf)\n"
"# Top-level: program -> list of statements\n"
"<program> ::= <stmt_list>\n"
"<stmt_list> ::= <stmt> | <stmt> <stmt_list>\n"
"\n"
"# Statements\n"
"<stmt> ::= <expr_stmt> ;\n"
"         | <var_decl> ;\n"
"         | <class_decl>\n"
"         | <function_decl>\n"
"         | <if_stmt>\n"
"         | <while_stmt>\n"
"         | <return_stmt> ;\n"
"         | <try_catch>\n"
"\n"
"<expr_stmt> ::= <expr>\n"
"<var_decl> ::= var <identifier> ( '=' <expr> )?\n"
"\n"
"# Classes, objects, receivers (method receiver syntax: receiver.method(args))\n"
"<class_decl> ::= class <identifier> '{' <class_body> '}'\n"
"<class_body> ::= <class_member> | <class_member> <class_body>\n"
"<class_member> ::= <var_decl> ';' | <function_decl>\n"
"\n"
"<function_decl> ::= func <identifier> '(' <param_list_opt> ')' '{' <stmt_list_opt> '}'\n"
"<param_list_opt> ::=  | <param_list>\n"
"<param_list> ::= <identifier> | <identifier> ',' <param_list>\n"
"<stmt_list_opt> ::=  | <stmt_list>\n"
"\n"
"# Control flow\n"
"<if_stmt> ::= if '(' <expr> ')' <stmt_block> ( else <stmt_block> )?\n"
"<while_stmt> ::= while '(' <expr> ')' <stmt_block>\n"
"<return_stmt> ::= return <expr_opt>\n"
"<expr_opt> ::=  | <expr>\n"
"<stmt_block> ::= '{' <stmt_list_opt> '}'\n"
"\n"
"# Exception handling\n"
"<try_catch> ::= try <stmt_block> catch '(' <identifier> ')' <stmt_block>\n"
"\n"
"# Expressions: object creation, method call, operators, regex, literals\n"
"<expr> ::= <assign_expr>\n"
"<assign_expr> ::= <logical_or_expr> | <identifier> '=' <assign_expr>\n"
"<logical_or_expr> ::= <logical_and_expr> | <logical_or_expr> '||' <logical_and_expr>\n"
"<logical_and_expr> ::= <equality_expr> | <logical_and_expr> '&&' <equality_expr>\n"
"<equality_expr> ::= <rel_expr> | <equality_expr> ('==' | '!=') <rel_expr>\n"
"<rel_expr> ::= <add_expr> | <rel_expr> ('<' | '>' | '<=' | '>=') <add_expr>\n"
"<add_expr> ::= <mul_expr> | <add_expr> ('+'|'-') <mul_expr>\n"
"<mul_expr> ::= <unary_expr> | <mul_expr> ('*'|'/'|'%') <unary_expr>\n"
"<unary_expr> ::= ('+'|'-'|'!') <unary_expr> | <postfix_expr>\n"
"<postfix_expr> ::= <primary_expr> ( <postfix_tail> )*\n"
"<postfix_tail> ::= '.' <identifier> | '(' <arg_list_opt> ')' | '[' <expr> ']' | '::' <identifier>\n"
    "<arg_list_opt> ::=  | <arg_list>\n"<arg_list> ::= <expr> | <expr> ',' <arg_list>\n"
"\n"
"# Primary: object literal, array, hash, regex, identifier, literal, function literal\n"
"<primary_expr> ::= <identifier> | <literal> | <array_literal> | <hash_literal> | <regex_literal> | '(' <expr> ')' | 'new' <identifier> '(' <arg_list_opt> ')'\n"
"<array_literal> ::= '[' <arg_list_opt> ']'\n"
"<hash_literal> ::= '{' <hash_entries_opt> '}'\n"
"<hash_entries_opt> ::=  | <hash_entries>\n"
"<hash_entries> ::= <hash_entry> | <hash_entry> ',' <hash_entries>\n"
"<hash_entry> ::= <expr> ':' <expr>\n"
"<regex_literal> ::= / <regex_body> / <regex_flags_opt>\n"
"<regex_flags_opt> ::=  | [a-zA-Z]+\n"
"\n"
"# Literals\n"
"<literal> ::= <number> | <string> | <boolean> | null\n"
"<number> ::= [0-9]+ ('.' [0-9]+)?\n"
"<string> ::= '([^'\\\\]|\\\\.)*' | \"([^\"]|\\\\.)*\"\n"
"<boolean> ::= true | false\n"
"\n"
"# Operator-functions and semi-static operator declaration (半静子作用素)\n"
"<operator_decl> ::= operator <symbol> '(' <param_list_opt> ')' '{' <stmt_list_opt> '}'\n"
"<symbol> ::= '+' | '-' | '*' | '/' | '^' | '⊠' | '∘'\n"
"\n"
"# Comments and whitespace handled by lexer (not in BNF)\n"
    ;
  snprintf(buf, sizeof(buf), "%s/lib/omega.bnf", out);
  write_file(buf, omega_bnf);

  /* 2) include/omega.h - runtime API (AST structures + runtime API declarations) */
    const char *omega_h =
      "/* include/omega.h - Omega Script runtime API (skeleton) */\n#ifndef OMEGA_H\n#define OMEGA_H\n\n#include <stdint.h>\n#include <stddef.h>\n\n/* Basic value types */\ntypedef enum { OTYPE_NULL, OTYPE_NUMBER, OTYPE_STRING, OTYPE_BOOL, OTYPE_OBJECT, OTYPE_ARRAY, OTYPE_HASH, OTYPE_FUNCTION } OType;\n\ntypedef struct OValue {\n    OType type;\n    union {\n        double num;\n        char *str;\n        int boolean;\n        void *obj; /* pointer to object representation */\n    } v;\n} OValue;\n\n/* Forward declarations */\ntypedef struct OObject OObject;\ntypedef struct OEnv OEnv;\n\n/* Object runtime API */\nOObject* oobject_new(const char *classname);\nvoid oobject_set_field(OObject *o, const char *name, OValue val);\nOValue oobject_get_field(OObject *o, const char *name);\n\n/* Environment (scopes) */\nOEnv* oenv_new(void);\nvoid oenv_free(OEnv*);\nvoid oenv_set(OEnv*, const char *name, OValue val);\nOValue oenv_get(OEnv*, const char *name);\n\n/* Interpreter entry */\nint omega_interpret(const char *source, int argc, char **argv);\n\n/* Utility constructors */\nOValue oval_null();\nOValue oval_number(double x);\nOValue oval_string(const char *s);\nOValue oval_bool(int b);\n\n#endif /* OMEGA_H */\n";
    snprintf(buf, sizeof(buf), "%s/include/omega.h", out);
    write_file(buf, omega_h);

    /* 3) src/ast.h - AST node definitions (skeleton) */
    const char *ast_h =
      "/* src/ast.h - AST node declarations (skeleton) */\n#ifndef OMEGA_AST_H\n#define OMEGA_AST_H\n\n#include \"../include/omega.h\"\n\ntypedef enum { AST_PROGRAM, AST_STMT, AST_EXPR, AST_CLASS, AST_FUNC, AST_VARDECL } ASTNodeType;\n\ntypedef struct ASTNode {\n    ASTNodeType type;\n    int line;\n    /* union payload omitted for brevity in skeleton */\n    void *payload;\n} ASTNode;\n\nASTNode* ast_parse(const char *source);\nvoid ast_free(ASTNode*);\n\n#endif\n";
    snprintf(buf, sizeof(buf), "%s/src/ast.h", out);
    write_file(buf, ast_h);

    /* 4) src/ast.c - very small parser stub that returns NULL AST (placeholder) */
    const char *ast_c =
      "/* src/ast.c - parser skeleton (placeholder)\n   For a complete implementation, integrate a proper lexer/parser (e.g., hand-written or generated from grammar).\n*/\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include \"ast.h\"\n\nASTNode* ast_parse(const char *source) {\n    /* Placeholder: in real system, tokenize and parse according to omega.bnf */\n    (void)source;\n    return NULL; /* return a real AST in full implementation */\n}\n\nvoid ast_free(ASTNode *n) {\n    (void)n;\n}\n";
    snprintf(buf, sizeof(buf), "%s/src/ast.c", out);
    write_file(buf, ast_c);

    /* 5) src/runtime.c - runtime skeleton implementing objects and env */
    const char *runtime_c =
      "/* src/runtime.c - runtime skeleton implementing objects, env, basic values */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include \"../include/omega.h\"\n\n/* Minimal object and env representations for skeleton */\nstruct OObject { char *classname; /* simple single field map - full impl requires hash table */\n    char *field_name; OValue field_val; };\n\nstruct OEnv { char *name; OValue val; OEnv *next; };\n\nOObject* oobject_new(const char *classname) {\n    OObject *o = (OObject*)malloc(sizeof(OObject));\n    o->classname = strdup(classname?classname:\"Object\");\n    o->field_name = NULL; o->field_val = oval_null();\n    return o;\n}\nvoid oobject_set_field(OObject *o, const char *name, OValue val) {\n    /* simple single-field store (demo) */\n    if (o->field_name) free(o->field_name);\n    o->field_name = strdup(name);\n    o->field_val = val;\n}\nOValue oobject_get_field(OObject *o, const char *name) {\n    if (o->field_name && strcmp(o->field_name,name)==0) return o->field_val;\n    return oval_null();\n}\n\nOEnv* oenv_new(void) { return NULL; }\nvoid oenv_free(OEnv* e) { (void)e; }\nvoid oenv_set(OEnv* e, const char *name, OValue val) { (void)e; (void)name; (void)val; }\nOValue oenv_get(OEnv* e, const char *name) { (void)e; (void)name; return oval_null(); }\n\nOValue oval_null() { OValue v; v.type = OTYPE_NULL; return v; }\nOValue oval_number(double x) { OValue v; v.type = OTYPE_NUMBER; v.v.num = x; return v; }\nOValue oval_string(const char *s) { OValue v; v.type = OTYPE_STRING; v.v.str = strdup(s? s : \"\"); return v; }\nOValue oval_bool(int b) { OValue v; v.type = OTYPE_BOOL; v.v.boolean = b?1:0; return v; }\n\n/* Interpreter entry: placeholder that prints info */\nint omega_interpret(const char *source, int argc, char **argv) {\n    (void)argc; (void)argv;\n    printf(\"Omega interpreter (skeleton) running. Source length=%zu\\n\", source?strlen(source):0);\n    /* in real interpreter: parse AST, then execute AST nodes using runtime APIs above */\n    return 0;\n}\n";
    snprintf(buf, sizeof(buf), "%s/src/runtime.c", out);
    write_file(buf, runtime_c);

    /* 6) src/driver.c - small CLI that uses ast and runtime */
    const char *driver_c =
      "/* src/driver.c - front-end CLI for compile/run (skeleton) */\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include \"../include/omega.h\"\n#include \"ast.h\"\n\nint main(int argc, char **argv) {\n    if (argc < 2) { fprintf(stderr, \"Usage: %s <file.os>\\n\", argv[0]); return 2; }\n    const char *path = argv[1];\n    FILE *f = fopen(path, \"rb\");\n    if (!f) { perror(\"open\"); return 2; }\n    fseek(f,0,SEEK_END); long sz = ftell(f); fseek(f,0,SEEK_SET);\n    char *src = malloc(sz+1); fread(src,1,sz,f); src[sz]=0; fclose(f);\n    /* interpret (skeleton) */\n    int rc = omega_interpret(src, argc-1, argv+1);\n    free(src);\n    return rc;\n}\n";
    snprintf(buf, sizeof(buf), "%s/src/driver.c", out);
    write_file(buf, driver_c);

    /* 7) bin scripts (compile/run) */
    const char *bin_compile =
      "#!/bin/sh\n# omega-compile - compile Omega Script (skeleton)\nset -e\nOUTDIR=${1:-./build}\nmkdir -p \"$OUTDIR\"\n# build C runtime and driver\ngcc -Iinclude src/runtime.c src/driver.c src/ast.c -o \"$OUTDIR/omega\" 2>/dev/null || true\nif [ -x \"$OUTDIR/omega\" ]; then echo \"Built $OUTDIR/omega\"; else echo \"Build produced no binary (check dependencies)\"; fi\n";
    snprintf(buf, sizeof(buf), "%s/bin/omega-compile", out);
    write_file(buf, bin_compile);

    const char *bin_run =
      "#!/bin/sh\n# omega-run - run Omega Script using built interpreter\nif [ \"$#\" -lt 1 ]; then echo \"Usage: omega-run <file.os> [args]\"; exit 2; fi\nBUILD=${OMEGA_BUILD:-./build}\nBIN=\"$BUILD/omega\"\nif [ ! -x \"$BIN\" ]; then echo \"Interpreter not built. Run bin/omega-compile first.\"; exit 2; fi\n\"$BIN\" \"$@\"\n";
    snprintf(buf, sizeof(buf), "%s/bin/omega-run", out);
    write_file(buf, bin_run);

    /* 8) etc/omega.conf - runtime config template */
    const char *etc_conf =
      "# Omega runtime config (template)\n# logging, optimization, and safety toggles\nlog_level = info\noptimizations = none\nenable_dynamic_load = false\n";
    snprintf(buf, sizeof(buf), "%s/etc/omega.conf", out);
    write_file(buf, etc_conf);

    /* 9) usr examples: sample omega file demonstrating OOP and operators */
    const char *example_os =
      "// examples/hello.os - Omega Script sample (quantum-sim style, symbolic only)\nclass Qubit {\n  var state = [1.0, 0.0];\n  func apply(unitary) {\n    // In actual system, unitary would be a matrix; here we store symbolic\n    this.state = unitary(this.state);\n  }\n}\n\nfunc hadamard(v) {\n  // placeholder symbolic transform\n  return v; // no-op in skeleton\n}\n\nvar q = new Qubit();\nq.apply(hadamard);\nprint(\"Qubit state:\", q.state);\n";
																																						    snprintf(buf, sizeof(buf), "%s/usr/share/omega/examples/hello.os", out);
    write_file(buf, example_os);

    /* 10) Makefile (package build) */
    const char *makefile =
      "# Makefile - build/install skeleton\nPREFIX ?= /usr/local\nBINDIR = $(DESTDIR)$(PREFIX)/bin\nLIBDIR = $(DESTDIR)$(PREFIX)/share/omega\nall: build\nbuild:\n\t@echo \"Building runtime (skeleton)...\"\n\t@mkdir -p build\n\t@gcc -Iinclude src/runtime.c src/driver.c src/ast.c -o build/omega 2>/dev/null || true\n\t@if [ -x build/omega ]; then echo \"Built build/omega\"; else echo \"Build failed or produced no binary\"; fi\ninstall: build\n\t@mkdir -p $(BINDIR) $(LIBDIR)\n\t@cp -r bin/* $(BINDIR)/ 2>/dev/null || true\n\t@cp -r lib/* $(LIBDIR)/ 2>/dev/null || true\n\t@cp -r src include etc usr doc $(LIBDIR)/ 2>/dev/null || true\n\t@echo \"Installed omega skeleton to $(LIBDIR) and scripts to $(BINDIR)\"\nclean:\n\t@rm -rf build\n";
    snprintf(buf, sizeof(buf), "%s/Makefile", out);
    write_file(buf, makefile);

    /* 11) doc/README.md */
    const char *doc_readme =
      "# Omega Script - Compiler/Interpreter Skeleton\n\nThis package is a skeleton implementation of a language called Omega Script (quantum-programming-style DSL).\n\nContents:\n- lib/omega.bnf : language grammar (skeleton)\n- include/omega.h : runtime API declarations\n- src/ : C sources (parser stub, runtime skeleton, driver)\n- bin/omega-compile, bin/omega-run : build/run scripts\n- usr/share/omega/examples : example scripts\n- etc/omega.conf : runtime settings template\n\nHow to build (local):\n  make\n\nHow to run (example):\n  ./bin/omega-compile\n  ./bin/omega-run usr/share/omega/examples/hello.os\n\nNotes:\n- This is a research/education skeleton. To become a full compiler/interpreter you must implement the lexer, parser, AST, codegen or bytecode VM, GC, execution of methods, exception propagation, operator-function dispatch, and proper data structures for arrays/hashes/regex.\n- 'Semi-static operator' (半静子作用素) feature is represented in grammar; hooking into runtime requires operator registry and dispatch.\n- No real quantum hardware control is included; quantum constructs are symbolic placeholders.\n";
    snprintf(buf, sizeof(buf), "%s/doc/README.md", out);
    write_file(buf, doc_readme);

    /* 12) set executable flags on POSIX */
#ifndef _WIN32
    {
      char cmd[8192];
      snprintf(cmd, sizeof(cmd),
	       "chmod +x \"%s/bin/omega-compile\" \"%s/bin/omega-run\" 2>/dev/null || true",
	       out, out);
      system(cmd);
    }
#endif

    printf("Omega Script package skeleton created at: %s\n", out);
    printf("Next: run 'make' inside the package to build the interpreter skeleton (may produce no binary if dependencies missing).\n");
    return 0;
}
/*
```

備考（短く）
- ここにあるコードは「言語処理系の骨格」を自動生成するプログラムです。完全なコンパイラ／インタープリタにするには、字句解析器（lexer）、パーサ（BNF→構文解析器）、AST 実装、実行モデル（バイトコード VM or AST インタプリタ）、メモリ管理（GC）、例外の正しい伝播、メソッド呼び出し時のレシーバ解決などを実装する必要があります。上記はその出発点（安全な雛形）です。
- 追加で特定の機能（例: 完全な再帰下降パーサ実装、オブジェクトフィールドハッシュ、メソッドディスパッチ、半静子作用素の詳細仕様、テストケース集）を実装する希望があれば、優先順位を指示してください。
*/
