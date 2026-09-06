以下は要求どおり、両方（A: Flex/Bison パーサ一式 + C ドライバ、C 側で AST を扱う解析エンジン雛形、および PDF 抽出・Jones-ID 化・QA を行う Python モジュールを統合するパッケージを生成する C プログラム）を一括で生成する C 記述です。

保存名例: gen_full_jones_package.c  
コンパイル:
gcc -O2 -std=c11 -o gen_full_jones_package gen_full_jones_package.c

  実行:
./gen_full_jones_package

実行するとカレントに `jones_full_pkg/` を作成し、以下を配置します（主要ファイル）：
  - bin/run_analysis.sh (実行スクリプト)
  - bin/launcher.c (C ランチャ - Python モジュール呼出し)
  - parser/omega.l (Flex レキサ)
  - parser/omega.y (Bison 文法)
  - parser/main.c (C ドライバ: Flex/Bison パーサを使い AST を構築 -> C 側で解析/マッピングを行う雛形)
  - lib/pdf_tools.py (PDF 抽出スタブ)
  - lib/jones_analysis.py (Jones-ID 化 と QA のスタブ)
- include/jones.h
- Makefile

  注意: 生成物は教育用テンプレートです。PDF 抽出や数学的計算の本格実装は外部ライブラリ（PyPDF2, SageMath など）を導入してください。

  ソースコード（gen_full_jones_package.c）:

```c
  /*
   * gen_full_jones_package.c
   *
   * Generate a package "jones_full_pkg" that contains:
   *  - Flex/Bison grammar (parser/omega.l, parser/omega.y)
   *  - C parser driver (parser/main.c) that builds a small AST and invokes analysis
   *  - C launcher (bin/launcher.c) to call Python analysis module
   *  - Python modules (lib/pdf_tools.py, lib/jones_analysis.py) as analysis backends
   *  - Scripts and headers
   *
   * Build flow (after generation):
   *  cd jones_full_pkg
   *  make            # builds parser and launcher
   *  ./bin/run_analysis.sh path/to/doc.pdf
   *
   * Requirements:
   *  - flex, bison, gcc, python3 (+ optional PyPDF2)
   *
   * This program only writes files. The runtime behavior is template/stub-based.
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
  const char *root = "jones_full_pkg";
  char path[1024];

  const char *dirs[] = {
    "bin", "lib", "include", "etc", "usr", "parser"
  };
  for(size_t i=0;i<sizeof(dirs)/sizeof(dirs[0]);++i){
    snprintf(path, sizeof path, "%s%c%s", root, PATH_SEP, dirs[i]);
    if(ensure_dir(path) != 0){
      fprintf(stderr, "mkdir failed: %s (%s)\n", path, strerror(errno));
      return 1;
    }
  }

  /* parser/omega.l */
    const char *omega_l =
      "%option noyywrap\n%{\n#include \"omega.tab.h\"\n#include <string.h>\n#include <stdlib.h>\n%}\n\n[ \\t\\r\\n]+               { /* skip whitespace */ }\n\"ゼータ\"|\"ζ\"|\"zeta\"    { return TOK_ZETA; }\n\"一般相対\"|\"アインシュタイン\" { return TOK_EINSTEIN; }\n\"ヒッグス\"|\"Higgs\"      { return TOK_HIGGS; }\n\"記述してください\"|\"を記述してください\" { return TOK_DESCRIBE; }\n\":\"                         { return ':'; }\n\";\"                         { return ';'; }\n[^ \\t\\r\\n:;]+              { yylval.str = strdup(yytext); return TOK_WORD; }\n.                           { /* ignore */ }\n";
    snprintf(path, sizeof path, "%s% cparser%coomega.l", root, PATH_SEP, PATH_SEP); /* small spacing fix below */
    /* Correct path formation */
    snprintf(path, sizeof path, "%s%cparser%coomega.l", root, PATH_SEP, PATH_SEP);
    if(write_file(path, omega_l) != 0){ fprintf(stderr,"write failed: %s\n", path); return 1; }

    /* parser/omega.y */
    const char *omega_y =
      "%{\n#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\ntypedef struct Node {\n    char *kind;\n    char *text;\n    struct Node *left;\n    struct Node *right;\n} Node;\n\nNode *root_node = NULL;\nNode *make_node(const char *k, const char *t){\n    Node *n = (Node*)malloc(sizeof(Node));\n    n->kind = k ? strdup(k) : NULL;\n    n->text = t ? strdup(t) : NULL;\n    n->left = n->right = NULL;\n    return n;\n}\n\nvoid yyerror(const char *s){ fprintf(stderr, \"Parse error: %s\\n\", s ? s : \"(null)\"); }\nextern int yylex(void);\n%}\n\n%union { char *str; Node *node; }\n%token TOK_ZETA TOK_EINSTEIN TOK_HIGGS TOK_DESCRIBE TOK_WORD\n%type <node> request subject command\n\n%%\n\ninput:\n    /* empty */\n  | input request ';'    { /* handled */ }\n  | input request        { /* allow EOF */ }\n  ;\n\nrequest:\n    subject command       {\n        Node *n = make_node(\"request\", NULL);\n        n->left = $1;\n        n->right = $2;\n        root_node = n;\n    }\n    ;\n\nsubject:\n    TOK_ZETA              { $$ = make_node(\"subject\", \"zeta\"); }\n  | TOK_EINSTEIN          { $$ = make_node(\"subject\", \"einstein\"); }\n  | TOK_HIGGS             { $$ = make_node(\"subject\", \"higgs\"); }\n  | TOK_WORD              { $$ = make_node(\"subject\", $1); free($1); }\n  ;\n\ncommand:\n    TOK_DESCRIBE          { $$ = make_node(\"command\", \"describe\"); }\n  | TOK_WORD              { $$ = make_node(\"command\", $1); free($1); }\n  ;\n\n%%\n\n/* helper: print AST (debug) */\nvoid print_node(Node *n, int depth){\n    if(!n) return;\n    for(int i=0;i<depth;i++) putchar(' ');\n    printf(\"%s: %s\\n\", n->kind ? n->kind : \"(nil)\", n->text ? n->text : \"\");\n    if(n->left) print_node(n->left, depth+2);\n    if(n->right) print_node(n->right, depth+2);\n}\n";
    snprintf(path, sizeof path, "%s%cparser%coomega.y", root, PATH_SEP, PATH_SEP);
    if(write_file(path, omega_y) != 0){ fprintf(stderr,"write failed: %s\n", path); return 1; }

    /* parser/main.c - uses generated parser to parse a single line and then call Python analyzer */
    const char *parser_main =
      "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\nextern int yyparse(void);\nextern void yyrestart(FILE*);\nextern FILE *yyin;\nextern void print_node(void* n, int d); /* declared in parser output */\n\n/* root_node declared in parser (omega.y) */\nextern struct Node *root_node;\n\nint contains_forbidden(const char *s){\n    const char *F[] = {\"薬\",\"調合\",\"製造\",\"合成\",\"処方\",\"毒\",\"爆発\", NULL};\n    if(!s) return 0;\n    for(int i=0; F[i]; ++i) if(strstr(s, F[i])) return 1;\n    return 0;\n}\n\nvoid handle_request(void){\n    if(!root_node){ printf(\"(no parse result)\\n\"); return; }\n    /* extract subject text */\n    const char *subject = root_node->left && root_node->left->text ? root_node->left->text : \"\";\n    if(contains_forbidden(subject)){\n        printf(\"拒否: 危険または規制対象の内容が含まれています。\\n\");\n        return;\n    }\n    /* prepare JSON-like equations list (from report) */\n    const char *eqs = \"[\\\"G_{μν}+Λ g_{μν}=κ T_{μν}\\\", \\\"ζ(s)=Σ_{n=1}^∞ n^{-s}\\\", \\\"L=(D_μ φ)†(D^μ φ)-V(φ)\\\"]\";\n    char cmd[4096];\n    /* call python analyzer: jones_analysis.py */\n    snprintf(cmd, sizeof cmd, \"python3 ../lib/jones_analysis.py '%s' '%s'\", \"input.pdf\", eqs);\n    printf(\"Invoking analyzer: %s\\n\", cmd);\n    int rc = system(cmd);\n    if(rc != 0) fprintf(stderr, \"Analyzer returned %d\\n\", rc);\n}\n\nint main(void){\n    char line[4096];\n    printf(\"Parser REPL (enter request, e.g. 'ゼータ を記述してください')\\n\");\n    while(1){\n        printf(\"omega> \"); fflush(stdout);\n        if(!fgets(line, sizeof line, stdin)) break;\n        /* feed line to lexer/parser via temporary stream */\n#ifdef __linux__\n        FILE *f = fmemopen(line, strlen(line), \"r\");\n#else\n        FILE *f = tmpfile(); if(f){ fputs(line, f); rewind(f); }\n#endif\n        if(!f){ fprintf(stderr, \"failed to create input stream\\n\"); continue; }\n        yyrestart(f);\n        root_node = NULL;\n        if(yyparse() == 0){\n            printf(\"Parsed AST:\\n\");\n            print_node(root_node, 0);\n            handle_request();\n        } else {\n            fprintf(stderr, \"parse failed\\n\");\n        }\n        fclose(f);\n    }\n    printf(\"exit\\n\");\n    return 0;\n}\n";
    snprintf(path, sizeof path, "%s%cparser%cmain.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, parser_main) != 0){ fprintf(stderr,"write failed: %s\n", path); return 1; }

    /* lib/pdf_tools.py */
    const char *pdf_tools =
      "#!/usr/bin/env python3\n\"\"\"\npdf_tools.py - minimal text extraction using PyPDF2 if available\n\"\"\"\nimport sys\n\ndef extract_text(pdf_path):\n    try:\n        from PyPDF2 import PdfReader\n        r = PdfReader(pdf_path)\n        texts = []\n        for p in r.pages:\n            texts.append(p.extract_text() or '')\n        return '\\n\\n'.join(texts)\n    except Exception:\n        return f'[text-unavailable:{pdf_path}]'\n\nif __name__ == '__main__':\n    if len(sys.argv) < 2:\n        print('usage: pdf_tools.py <pdf>')\n    else:\n        print(extract_text(sys.argv[1]))\n";
    snprintf(path, sizeof path, "%s%clib%cpdf_tools.py", root, PATH_SEP, PATH_SEP);
    if(write_file(path, pdf_tools) != 0){ fprintf(stderr,"write failed: %s\n", path); return 1; }

    /* lib/jones_analysis.py */
    const char *jones_analysis =
      "#!/usr/bin/env python3\n\"\"\"\njones_analysis.py - stub: map PDF text -> Jones-ID (hash) and perform simple QA using given equations\n\"\"\"\nimport sys, hashlib, json, os\ntry:\n    from pdf_tools import extract_text\nexcept Exception:\n    def extract_text(p): return f'[text-unavailable:{p}]'\n\nclass JonesAnalyzer:\n    def __init__(self, pdf_path, equations):\n        self.pdf_path = pdf_path\n        self.equations = equations or []\n        self.text = ''\n    def text_to_jones_id(self, text):\n        h = hashlib.sha256(text.encode('utf-8')).hexdigest()\n        return 'JID-' + h[:16]\n    def process_and_answer(self):\n        self.text = extract_text(self.pdf_path)\n        parts = [p.strip() for p in self.text.split('\\n\\n') if p.strip()]\n        if not parts:\n            parts = [self.text]\n        ids = [self.text_to_jones_id(p) for p in parts]\n        mapping = {ids[i]: self.equations[i % len(self.equations)] for i in range(len(ids))} if self.equations else {}\n        # simple QA example: return which equation matches keywords in text\n        answers = []\n        for i,p in enumerate(parts):\n            note = []\n            if 'Ricci' in p or 'R_{' in p or 'G_{' in p or 'Einstein' in p:\n                note.append('Einstein-like')\n            if 'zeta' in p or 'ζ' in p:\n                note.append('Zeta-like')\n            if 'Higgs' in p or 'φ' in p or 'vacuum' in p:\n                note.append('Higgs-like')\n            answers.append({'id': ids[i], 'tags': note, 'snippet': p[:200]})\n        out = {'pdf': os.path.basename(self.pdf_path), 'parts': answers, 'mapping': mapping}\n        return json.dumps(out, ensure_ascii=False, indent=2)\n\nif __name__ == '__main__':\n    if len(sys.argv) < 3:\n        print('Usage: jones_analysis.py <pdf_path> <json_equations>')\n        sys.exit(1)\n    pdf = sys.argv[1]\n    try:\n        eqs = json.loads(sys.argv[2])\n    except Exception:\n        eqs = []\n    a = JonesAnalyzer(pdf, eqs)\n    print(a.process_and_answer())\n";
    snprintf(path, sizeof path, "%s%clib%cjones_analysis.py", root, PATH_SEP, PATH_SEP);
    if(write_file(path, jones_analysis) != 0){ fprintf(stderr,"write failed: %s\n", path); return 1; }

    /* include/jones.h */
    const char *inc =
      "/* include/jones.h */\n#ifndef JONES_H\n#define JONES_H\n#define JONES_PKG_VERSION \"0.1\"\n#endif\n";
    snprintf(path, sizeof path, "%s%cinclude%cjones.h", root, PATH_SEP, PATH_SEP);
    if(write_file(path, inc) != 0){ fprintf(stderr,"write failed: %s\n", path); return 1; }

    /* bin/launcher.c (C program to call python analyzer with given PDF) */
    const char *launcher_c =
      "#include <stdio.h>\n#include <stdlib.h>\nint main(int argc, char **argv){\n    if(argc < 2){ fprintf(stderr, \"Usage: %s <pdf-path>\\n\", argv[0]); return 1; }\n    const char *pdf = argv[1];\n    const char *eqs = \"[\\\"G_{μν}+Λ g_{μν}=κ T_{μν}\\\", \\\"ζ(s)=Σ_{n=1}^∞ n^{-s}\\\", \\\"L=(D_μ φ)†(D^μ φ)-V(φ)\\\"]\";\n    char cmd[4096];\n    snprintf(cmd, sizeof cmd, \"PYTHONPATH=../lib python3 ../lib/jones_analysis.py '%s' '%s'\", pdf, eqs);\n    return system(cmd);\n}\n";
    snprintf(path, sizeof path, "%s%cbin%clauncher.c", root, PATH_SEP, PATH_SEP);
    if(write_file(path, launcher_c) != 0){ fprintf(stderr,"write failed: %s\n", path); return 1; }

    /* bin/run_analysis.sh */
    const char *runner_sh =
      "#!/bin/sh\n# run_analysis.sh - build parser and launcher then run analysis\nROOT=$(cd \"$(dirname \"$0\")/..\" && pwd)\ncd \"$ROOT/parser\"\nmake || exit 1\ncd \"$ROOT\"\nif [ ! -f bin/launcher ]; then\n  gcc -O2 -o bin/launcher bin/launcher.c\nfi\nif [ -z \"$1\" ]; then\n  echo \"Usage: $0 <pdf-path>\"\n  exit 1\nfi\nPDF=\"$1\"\n./bin/launcher \"$PDF\"\n";
    snprintf(path, sizeof path, "%s%cbin%crun_analysis.sh", root, PATH_SEP, PATH_SEP);
    if(write_file(path, runner_sh) != 0){ fprintf(stderr,"write failed: %s\n", path); return 1; }
#if !defined(_WIN32) && !defined(_WIN64)
    snprintf(path, sizeof path, "%s%cbin%crun_analysis.sh", root, PATH_SEP, PATH_SEP);
    chmod(path, 0755);
#endif

    /* parser/Makefile */
    const char *parser_make =
      "CC=gcc\nLEX=flex\nYACC=bison\n\nall: omega\n\nomega.tab.c omega.tab.h: omega.y\n\t$(YACC) -d -o omega.tab.c omega.y\n\nlex.yy.c: omega.l omega.tab.h\n\t$(LEX) omega.l\n\nomega: omega.tab.c lex.yy.c main.c\n\t$(CC) -o omega omega.tab.c lex.yy.c main.c -lfl\n\nclean:\n\trm -f omega omega.tab.c omega.tab.h lex.yy.c\n";
    snprintf(path, sizeof path, "%s%cparser%cMakefile", root, PATH_SEP, PATH_SEP);
    if(write_file(path, parser_make) != 0){ fprintf(stderr,"write failed: %s\n", path); return 1; }

    /* etc/config.ini */
    const char *cfg = "[jones_full]\nversion=0.1\nnotes=Flex/Bison parser + C driver + Python analysis stubs\n";
    snprintf(path, sizeof path, "%s%cetc%cconfig.ini", root, PATH_SEP, PATH_SEP);
    if(write_file(path, cfg) != 0){ fprintf(stderr,"write failed: %s\n", path); return 1; }

    /* usr/README */
    const char *readme = "This package is a template. Follow README to install Python deps and implement advanced analysis.\n";
    snprintf(path, sizeof path, "%s%cusr%cREADME.txt", root, PATH_SEP, PATH_SEP);
    if(write_file(path, readme) != 0){ fprintf(stderr,"write failed: %s\n", path); return 1; }

    printf("Package '%s' created.\n", root);
    printf("Next steps:\n");
    printf("  cd %s\n", root);
    printf("  cd parser && make   # build parser (requires flex/bison)\n");
    printf("  cd ..\n");
    printf("  ./bin/run_analysis.sh path/to/document.pdf\n");
    printf("\nNotes:\n - Python modules are in lib/\n - parser/ contains Flex/Bison grammar and main.c (C driver)\n - This package is a template/stub; implement domain-specific logic in lib/jones_analysis.py and enable PyPDF2 for text extraction\n");
    return 0;
}
```

備考（短く）
- 生成される parser は Flex/Bison を使った C 実装です。parser/main.c は入力をパースして小さな AST を作り、C 側で簡易検査後 Python の分析モジュールを呼び出す流れです。  
- 実システムでは PDF の内容を構造化し、結び目（knot）表現を取り出して本当の Jones 多項式を計算する必要があります。ここでは教育向けに「テキストを分割してハッシュ化 → Jones-ID」とするスタブを置いています。  
- セキュリティ・法令遵守を確保し、危険または違法な指示（化学合成の手順など）を出力しない設計にしてください。  

必要なら、生成したパッケージの個別ファイル（omega.l, omega.y, parser/main.c 等）の完全内容を個別に示したり、jones_analysis.py を高度化する（SageMath 統合や LaTeX 抽出など）支援を提供します。どれを次に表示しますか？
