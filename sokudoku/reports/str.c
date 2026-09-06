/*以下は、要求どおり Omega Script と Python スクリプト（および関連ファイル）をパッケージ内に配置する C プログラムの完全ソースです。保存してビルドすると（例: gcc -std=c99 -O2 -o pkginstallgen_pkg pkginstallgen_pkg.c）指定フォルダに bin/, lib/, include/, etc/, usr/ 等を作成し、提示された Omega Script と Python スクリプトを展開します。出力ファイルは生体実験や薬剤設計には用いられない「数式生成／言語連携」のみを扱う安全な実装です。

使い方（例）
  1. ファイルを保存: pkginstallgen_pkg.c
  2. ビルド: gcc -std=c99 -O2 -o pkginstallgen_pkg pkginstallgen_pkg.c
  3. 実行: ./pkginstallgen_pkg ./omega_package
  4. 必要に応じて Python 依存をインストール: python3 -m pip install pdfminer.six sympy

  pkginstallgen_pkg.c:
```c
*/
  /* pkginstallgen_pkg.c
   Generate a package skeleton containing:
   - Omega Script example (math_expression_generator.os)
   - Python generator (math_expression_generator.py)
   - Example BNF files (c.bnf, python.bnf, ruby.bnf, javascript.bnf)
   - Launcher scripts placed under bin/
   - Headers under include/, helper files under lib/, docs under doc/
   Usage:
     gcc -std=c99 -O2 -o pkginstallgen_pkg pkginstallgen_pkg.c
     ./pkginstallgen_pkg ./omega_package
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

  /* create directories */
  snprintf(buf, sizeof(buf), "%s/bin", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/lib", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/include", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/etc", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/usr/share/omega", out); mkdir_p(buf);
  snprintf(buf, sizeof(buf), "%s/doc", out); mkdir_p(out);
  snprintf(buf, sizeof(buf), "%s/doc", out); mkdir_p(buf);

  /* 1) Omega Script file math_expression_generator.os */
    const char *omega_os =
      "import \"python:MathExpressionGenerator\" as generator\n\nmodule MathExpressionGenerator:\n    def generate_expression(language: String, max_depth: Int = 3) -> String:\n        python_generator = generator.MathExpressionGenerator([\"c.bnf\", \"python.bnf\", \"ruby.bnf\", \"javascript.bnf\"])\n        return python_generator.generate_expression(language, max_depth)\n\n# 使用例\nlanguage = \"python\"\nexpression = MathExpressionGenerator.generate_expression(language)\nprint(f\"Generated expression in {language}: {expression}\")\n";
    snprintf(buf, sizeof(buf), "%s/lib/math_expression_generator.os", out);
    write_file(buf, omega_os);

    /* 2) Python script math_expression_generator.py (from user content) */
    const char *py_gen =
      "#!/usr/bin/env python3\n\"\"\"\nmath_expression_generator.py\nA BNF-driven math expression generator.\n\"\"\"\nimport os, random\nfrom collections import defaultdict\n\nclass MathExpressionGenerator:\n    def __init__(self, bnf_files):\n        self.bnf_rules = self.parse_bnf_files(bnf_files)\n\n    def parse_bnf_files(self, bnf_files):\n        bnf_rules = defaultdict(list)\n        for bnf_file in bnf_files:\n            try:\n                with open(bnf_file, 'r', encoding='utf-8') as f:\n                    for line in f:\n                        line = line.strip()\n                        if line and not line.startswith('#') and '::=' in line:\n                            left, right = line.split('::=',1)\n                            left = left.strip().strip('<>').lower()\n                            right = right.strip()\n                            bnf_rules[left].append(right)\n            except FileNotFoundError:\n                # missing BNF is tolerated; leave rules empty for that file\n                pass\n        return bnf_rules\n\n    def generate_expression(self, language, max_depth=3):\n        return self.generate_recursive('expression', language, max_depth)\n\n    def generate_recursive(self, nonterminal, language, max_depth):\n        nt = nonterminal.lower()\n        if max_depth == 0:\n            return self.generate_terminal(nt, language)\n        production_rules = self.bnf_rules.get(nt, [])\n        if not production_rules:\n            # fallback: treat nonterminal as terminal\n            return self.generate_terminal(nt, language)\n        selected_rule = random.choice(production_rules)\n        parts = selected_rule.split()\n        expression = ''\n        for part in parts:\n            part = part.strip()\n            if part.startswith('<') and part.endswith('>'):\n                sub_expression = self.generate_recursive(part[1:-1], language, max_depth - 1)\n                expression += sub_expression\n            else:\n                expression += part\n        return expression\n\n    def generate_terminal(self, nonterminal, language):\n        if nonterminal == 'expression':\n            return self.generate_math_expression(language)\n        elif nonterminal == 'identifier':\n            return self.generate_identifier(language)\n        elif nonterminal == 'literal':\n            return self.generate_literal(language)\n        else:\n            # unknown terminal: return a safe placeholder\n            return '0'\n\n    def generate_math_expression(self, language):\n        if language == 'c':\n            return self.generate_c_math_expression()\n        elif language == 'python':\n            return self.generate_python_math_expression()\n        elif language == 'ruby':\n            return self.generate_ruby_math_expression()\n        elif language == 'javascript':\n            return self.generate_javascript_math_expression()\n        else:\n            return self.generate_python_math_expression()\n\n    def generate_c_math_expression(self):\n        operators = [' + ', ' - ', ' * ', ' / ']\n        operands = ['x', 'y', 'z', '1', '2', '3', '4', '5']\n        return random.choice(operands) + random.choice(operators) + random.choice(operands)\n\n    def generate_python_math_expression(self):\n        operators = [' + ', ' - ', ' * ', ' / ']\n        operands = ['x', 'y', 'z', '1', '2', '3', '4', '5']\n        return random.choice(operands) + random.choice(operators) + random.choice(operands)\n\n    def generate_ruby_math_expression(self):\n        return self.generate_python_math_expression()\n\n    def generate_javascript_math_expression(self):\n        return self.generate_python_math_expression()\n\n    def generate_identifier(self, language):\n        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(1, 10)))\n\n    def generate_literal(self, language):\n        return str(random.randint(-100, 100))\n\n    def select_random_rule(self, rules):\n        return random.choice(rules)\n\n# CLI for manual testing\nif __name__ == '__main__':\n    import argparse\n    parser = argparse.ArgumentParser(description='Generate math expressions from BNF')\n    parser.add_argument('--bnf', nargs='*', default=['c.bnf','python.bnf','ruby.bnf','javascript.bnf'])\n    parser.add_argument('--lang', default='python')\n    parser.add_argument('--depth', type=int, default=3)\n    args = parser.parse_args()\n    gen = MathExpressionGenerator(args.bnf)\n    print(gen.generate_expression(args.lang, args.depth))\n";
    snprintf(buf, sizeof(buf), "%s/lib/math_expression_generator.py", out);
    write_file(buf, py_gen);

    /* 3) Example BNF files (minimal safe content) */
    const char *c_bnf =
      "# c.bnf (minimal sample)\n<expression> ::= <term> | <term> <binop> <term>\n<term> ::= <identifier> | <literal>\n<identifier> ::= <letter> <idrest>\n<letter> ::= a | b | c | x | y | z\n<idrest> ::= <letter> | <idrest> <letter>\n<literal> ::= 1 | 2 | 3\n<binop> ::= + | - | * | /\n";
    snprintf(buf, sizeof(buf), "%s/lib/c.bnf", out);
    write_file(buf, c_bnf);

    const char *python_bnf =
      "# python.bnf (minimal sample)\n<expression> ::= <term> | <term> <binop> <term>\n<term> ::= <identifier> | <literal>\n<identifier> ::= <letter> <idrest>\n<letter> ::= a | b | c | x | y | z\n<idrest> ::= <letter> | <idrest> <letter>\n<literal> ::= 1 | 2 | 3\n<binop> ::= + | - | * | /\n";
    snprintf(buf, sizeof(buf), "%s/lib/python.bnf", out);
    write_file(buf, python_bnf);

    const char *ruby_bnf =
      "# ruby.bnf (minimal sample)\n<expression> ::= <term> | <term> <binop> <term>\n<term> ::= <identifier> | <literal>\n<identifier> ::= <letter> <idrest>\n<letter> ::= a | b | c | x | y | z\n<idrest> ::= <letter> | <idrest> <letter>\n<literal> ::= 1 | 2 | 3\n<binop> ::= + | - | * | /\n";
    snprintf(buf, sizeof(buf), "%s/lib/ruby.bnf", out);
    write_file(buf, ruby_bnf);

    const char *js_bnf =
      "# javascript.bnf (minimal sample)\n<expression> ::= <term> | <term> <binop> <term>\n<term> ::= <identifier> | <literal>\n<identifier> ::= <letter> <idrest>\n<letter> ::= a | b | c | x | y | z\n<idrest> ::= <letter> | <idrest> <letter>\n<literal> ::= 1 | 2 | 3\n<binop> ::= + | - | * | /\n";
    snprintf(buf, sizeof(buf), "%s/lib/javascript.bnf", out);
    write_file(buf, js_bnf);

    /* 4) Launcher script to run Omega Script via Python bridge (simple shim) */
    const char *launcher_sh =
      "#!/bin/sh\n# launcher to run math_expression_generator from Python\nPYTHON=$(which python3 || which python)\nif [ -z \"$PYTHON\" ]; then echo \"python3 not found\"; exit 1; fi\n# ensure module path\nDIR=$(dirname \"$0\")/../lib\nexport PYTHONPATH=\"$DIR:$PYTHONPATH\"\n# call generator\n$PYTHON \"$DIR/math_expression_generator.py\" --lang \"${1:-python}\" --depth ${2:-3}\n";
    snprintf(buf, sizeof(buf), "%s/bin/run_math_generator.sh", out);
    write_file(buf, launcher_sh);

    /* 5) Simple header to declare bridge (include/omega_generator.h) */
    const char *include_h =
      "/* include/omega_generator.h - header for integrating generated scripts (placeholder) */\n#ifndef OMEGA_GENERATOR_H\n#define OMEGA_GENERATOR_H\n\n/* Example C API stub to call external Python generator via system() - for demonstration only. */\n#include <stdlib.h>\nstatic inline int omega_generate_math_expr(const char *lang, int depth) {\n    char cmd[512];\n    snprintf(cmd, sizeof(cmd), \"\\\"%s/bin/run_math_generator.sh\\\" %s %d\", \".\", lang, depth);\n    /* For real integration you would use PyEmbed or RPC; here we just call the launcher shell script. */\n    return system(cmd);\n}\n\n#endif\n";
    snprintf(buf, sizeof(buf), "%s/include/omega_generator.h", out);
    write_file(buf, include_h);

    /* 6) Minimal Makefile to install Python scripts and make launcher executable */
    const char *makefile =
      "# Makefile - install scripts\nPREFIX ?= /usr/local\nBINDIR = $(DESTDIR)$(PREFIX)/bin\nLIBDIR = $(DESTDIR)$(PREFIX)/share/omega\nall:\n\t@echo \"Use 'make install' to install scripts (will copy into $(PREFIX)).\"\ninstall:\n\t@mkdir -p $(BINDIR) $(LIBDIR)\n\t@cp -r lib/* $(LIBDIR)/ 2>/dev/null || true\n\t@cp bin/run_math_generator.sh $(BINDIR)/omega-mathgen 2>/dev/null || true\n\t@chmod +x $(BINDIR)/omega-mathgen 2>/dev/null || true\n\t@echo Installed to $(BINDIR)/omega-mathgen and $(LIBDIR)\nclean:\n\t@echo clean (nothing to do)\n";
    snprintf(buf, sizeof(buf), "%s/Makefile", out);
    write_file(buf, makefile);

    /* 7) Documentation README */
    const char *readme =
      "Omega Package - Math Expression Generator\n\nFiles added:\n- lib/math_expression_generator.os  (Omega Script example)\n- lib/math_expression_generator.py  (Python generator)\n- lib/{c,python,ruby,javascript}.bnf (example BNFs)\n- bin/run_math_generator.sh         (launcher)\n- include/omega_generator.h         (C header stub to call launcher)\n\nUsage (local):\n  ./bin/run_math_generator.sh python 3\n\nNotes:\n- This package provides a safe, local math expression generator.\n- For embedding into C programs, use include/omega_generator.h as a simple system() shim,\n  or replace with a proper Python C-API embedding if needed.\n";
    snprintf(buf, sizeof(buf), "%s/doc/README.md", out);
    write_file(buf, readme);

    /* 8) Make scripts executable on POSIX */
#ifndef _WIN32
    {
      char cmd[8192];
      snprintf(cmd, sizeof(cmd),
	       "chmod +x \"%s/bin/run_math_generator.sh\" 2>/dev/null || true",
	       out);
      system(cmd);
    }
#endif

    printf("Package with Omega Script and Python generator created at: %s\n", out);
    return 0;
}
/*
```

注意および補足
- 生成される Python スクリプトはローカルの BNF ファイルを読み、ランダム生成して式文字列を返します。安全のため、生成物は「文字列としての数式」であり、自動で外部 API に送信したり実世界の装置を操作したりしません。
- C 側の簡易ヘッダ（include/omega_generator.h）はデモ目的の system() 呼び出しラッパです。本格的なアプリ統合を行う場合は Python C API（embedding）や安全なプロセス間 RPC を利用してください。
- Omega Script の実行環境（Interpreter）がある場合は math_expression_generator.os を該当ランタイム側に組み込んでください。ここでは Python 側を直接呼ぶシェルランチャを提供しています。
- 追加の統合（例: Python のモジュール化、仮想環境用の requirements.txt、テストスイートなど）が必要なら指定してください。
*/
