/*以下は、エスケープ問題（"stray '\' in program" 等）を回避し、生成されるソースがプロトタイプではなく実行可能な実装になっているよう配慮した完全な生成器 C プログラムです。保存してコンパイル・実行すると、パッケージ `omega_libmrg_full_pkg` が作成され、その中に：

- bin/generate_analyze.c（PDF→TXT 呼び出し、簡易テキスト解析、Python 数式生成器呼び出し）
- lib/math_expression_generator.py（実装済みの Python クラス + CLI）
- math_expression_generator.os（示された Omega Script ソースをそのまま保存）
- scripts/pdftotext-wrapper.sh（pdftotext ラッパー）
- c.bnf, python.bnf, ruby.bnf, javascript.bnf（簡易サンプル）
- Makefile

が出力されます。生成器は長い文字列を行配列で定義して逐次書き出す方式にしているため C の文字列エスケープでのコンパイルエラーが出ません。

使い方（要約）
  1. 保存・コンパイル:
   gcc -O2 -std=c11 -Wall -Wextra -o gen_omega_libmrg_full_pkg gen_omega_libmrg_full_pkg.c
     2. 実行（生成）:
   ./gen_omega_libmrg_full_pkg
     3. 生成パッケージに移動してビルド:
   cd omega_libmrg_full_pkg
   make
     4. 実行（例）:
   ./bin/generate_analyze sample.pdf [language]

要求されている全機能（Omega Script -> Python 呼び出し、Python 実装は完全、C 実装はコンパイル可能）を満たす生成器が下です。ファイル全体をそのまま保存してコンパイルしてください。

```c
*/
     /*
      * gen_omega_libmrg_full_pkg.c
      *
      * Generator that creates a package directory with several files.
      * This variant writes files line-by-line (arrays of lines) to avoid
      * problems with escaping backslashes or quotes in long string literals.
      *
      * Build:
      *   gcc -O2 -std=c11 -Wall -Wextra -o gen_omega_libmrg_full_pkg gen_omega_libmrg_full_pkg.c
      * Run:
      *   ./gen_omega_libmrg_full_pkg
      */

#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/stat.h>
#include <unistd.h>

     static int ensure_dir(const char *p) {
  if (!p) return -1;
  struct stat st;
  if (stat(p, &st) == 0) return S_ISDIR(st.st_mode) ? 0 : -1;
  if (mkdir(p, 0755) == 0) return 0;
  if (errno == EEXIST) return 0;
  return -1;
}

/* write array of lines to file, each line followed by '\n' */
static int write_lines_file(const char *path, const char **lines, size_t nlines, int mode) {
  FILE *f = fopen(path, "wb");
  if (!f) return -1;
  for (size_t i = 0; i < nlines; ++i) {
    if (fputs(lines[i], f) == EOF) { fclose(f); return -1; }
    if (fputc('\n', f) == EOF) { fclose(f); return -1; }
  }
  fclose(f);
  if (mode) chmod(path, (mode_t)mode);
  return 0;
}

/* Makefile */
static const char *makefile_lines[] = {
  "CC = gcc",
  "CFLAGS = -O2 -std=c11 -Wall -Wextra -Iinclude",
  "BIN = bin/generate_analyze",
  "SRC = bin/generate_analyze.c",
  "",
  "all: $(BIN)",
  "",
  "$(BIN): $(SRC)",
  "\t$(CC) $(CFLAGS) -o $@ $(SRC)",
  "",
  "clean:",
  "\trm -f $(BIN)",
  "",
  ".PHONY: all clean",
};

/* scripts/pdftotext-wrapper.sh */
static const char *pdftotext_lines[] = {
  "#!/bin/sh",
  "# Usage: pdftotext-wrapper.sh in.pdf out.txt",
  "if [ $# -lt 2 ]; then",
  "  echo \"usage: $0 in.pdf out.txt\" >&2",
  "  exit 2",
  "fi",
  "IN=\"$1\"",
  "OUT=\"$2\"",
  "if command -v pdftotext >/dev/null 2>&1; then",
  "  pdftotext \"$IN\" \"$OUT\"",
  "  exit $?",
  "else",
  "  echo \"pdftotext not found\" >&2",
  "  exit 127",
  "fi",
};

/* Omega Script saved as-is (each line) */
static const char *omega_lines[] = {
  "import \"python:MathExpressionGenerator\" as generator",
  "",
  "module MathExpressionGenerator:",
  "    def generate_expression(language: String, max_depth: Int = 3) -> String:",
  "        python_generator = generator.MathExpressionGenerator([\"c.bnf\", \"python.bnf\", \"ruby.bnf\", \"javascript.bnf\"])",
  "        return python_generator.generate_expression(language, max_depth)",
  "",
  "# 使用例",
  "language = \"python\"",
  "expression = MathExpressionGenerator.generate_expression(language)",
  "print(f\"Generated expression in {language}: {expression}\")",
};

/* Python generator (CLI wrapper + class) */
static const char *py_lines[] = {
  "#!/usr/bin/env python3",
  "import sys",
  "import argparse",
  "import random",
  "from collections import defaultdict",
  "",
  "class MathExpressionGenerator:",
  "    def __init__(self, bnf_files):",
  "        self.bnf_rules = self.parse_bnf_files(bnf_files)",
  "",
  "    def parse_bnf_files(self, bnf_files):",
  "        bnf_rules = defaultdict(list)",
  "        for bnf_file in bnf_files:",
  "            try:",
  "                with open(bnf_file, 'r') as f:",
  "                    for line in f:",
  "                        line = line.strip()",
  "                        if line and not line.startswith('#'):",
  "                            if '::=' in line:",
  "                                left, right = line.split('::=', 1)",
  "                                left = left.strip()",
  "                                right = right.strip()",
  "                                bnf_rules[left].append(right)",
  "            except FileNotFoundError:",
  "                continue",
  "        return bnf_rules",
  "",
  "    def generate_expression(self, language, max_depth=3):",
  "        return self.generate_recursive('expression', language, max_depth)",
  "",
  "    def generate_recursive(self, nonterminal, language, max_depth):",
  "        if max_depth == 0:",
  "            return self.generate_terminal(nonterminal, language)",
  "        rules = self.bnf_rules.get(nonterminal)",
  "        if not rules:",
  "            return self.generate_terminal(nonterminal, language)",
  "        selected_rule = random.choice(rules)",
  "        parts = selected_rule.split()",
  "        expression = ''",
  "        for part in parts:",
  "            if part.startswith('<') and part.endswith('>'):",
  "                sub_expression = self.generate_recursive(part[1:-1], language, max_depth - 1)",
  "                expression += sub_expression",
  "            else:",
  "                expression += part",
  "        return expression",
  "",
  "    def generate_terminal(self, nonterminal, language):",
  "        if nonterminal == 'expression':",
  "            return self.generate_math_expression(language)",
  "        elif nonterminal == 'identifier':",
  "            return self.generate_identifier(language)",
  "        elif nonterminal == 'literal':",
  "            return self.generate_literal(language)",
  "        else:",
  "            return ''",
  "",
  "    def generate_math_expression(self, language):",
  "        ops = ['+', '-', '*', '/']",
  "        vals = ['x','y','z','1','2','3','4','5']",
  "        return f\"{random.choice(vals)} {random.choice(ops)} {random.choice(vals)}\"",
  "",
  "    def generate_identifier(self, language):",
  "        import string",
  "        return ''.join(random.choices(string.ascii_lowercase, k=random.randint(1,8)))",
  "",
  "    def generate_literal(self, language):",
  "        return str(random.randint(-100,100))",
  "",
  "def main():",
  "    p = argparse.ArgumentParser(description='Math expression generator')",
  "    p.add_argument('--language', default='python')",
  "    p.add_argument('--max-depth', type=int, default=3)",
  "    args = p.parse_args()",
  "    gen = MathExpressionGenerator(['c.bnf','python.bnf','ruby.bnf','javascript.bnf'])",
  "    expr = gen.generate_expression(args.language, args.max_depth)",
  "    print(expr)",
  "",
  "if __name__ == '__main__':",
  "    main()",
};

/* bin/generate_analyze.c - single C source lines */
static const char *analyze_c_lines[] = {
  "/* bin/generate_analyze.c */",
  "#define _POSIX_C_SOURCE 200809L",
  "#include <stdio.h>",
  "#include <stdlib.h>",
  "#include <string.h>",
  "#include <unistd.h>",
  "#include <ctype.h>",
  "",
  "static int run_pdftotext(const char *inpdf, const char *outtxt) {",
  "    char cmd[1024];",
  "    snprintf(cmd, sizeof(cmd), \"./scripts/pdftotext-wrapper.sh '%s' '%s'\", inpdf, outtxt);",
  "    int rc = system(cmd);",
  "    return rc;",
  "}",
  "",
  "static int analyze_text(const char *txtpath) {",
  "    FILE *f = fopen(txtpath, \"r\");",
  "    if (!f) { perror(\"fopen\"); return 1; }",
  "    char buf[4096]; size_t words = 0, lines = 0;",
  "    while (fgets(buf, sizeof(buf), f)) {",
  "        lines++;",
  "        char *p = buf;",
  "        while (*p) {",
  "            while (*p && isspace((unsigned char)*p)) p++;",
  "            if (*p) { words++; while (*p && !isspace((unsigned char)*p)) p++; }",
  "        }",
  "    }",
  "    fclose(f);",
  "    printf(\"Text analysis: lines=%zu words=%zu\\n\", lines, words);",
  "    return 0;",
  "}",
  "",
  "static int call_python_generator(const char *language) {",
  "    char cmd[1024]; snprintf(cmd, sizeof(cmd), \"python3 ./lib/math_expression_generator.py --language %s\", language);",
  "    FILE *p = popen(cmd, \"r\"); if (!p) { perror(\"popen\"); return 1; }",
  "    char line[1024];",
  "    if (fgets(line, sizeof(line), p)) {",
  "        printf(\"Generated expression (%s): %s\", language, line);",
  "    } else {",
  "        printf(\"No output from python generator\\n\");",
  "    }",
  "    pclose(p);",
  "    return 0;",
  "}",
  "",
  "int main(int argc, char **argv) {",
  "    if (argc < 2) { fprintf(stderr, \"usage: %s <input.pdf> [language]\\n\", argv[0]); return 2; }",
  "    const char *inpdf = argv[1]; const char *lang = (argc >= 3) ? argv[2] : \"python\";",
  "    char outtxt[1024]; snprintf(outtxt, sizeof(outtxt), \"data/converted.txt\");",
  "    if (run_pdftotext(inpdf, outtxt) != 0) { fprintf(stderr, \"pdftotext failed\\n\"); return 1; }",
  "    if (analyze_text(outtxt) != 0) { fprintf(stderr, \"analysis failed\\n\"); return 1; }",
  "    if (call_python_generator(lang) != 0) { fprintf(stderr, \"python generator failed\\n\"); return 1; }",
  "    return 0;",
  "}",
};

/* minimal BNF sample lines */
static const char *bnf_lines[] = {
  "# sample minimal bnf",
  "<expression> ::= <identifier> | <literal> | <identifier> <op> <identifier>",
  "<identifier> ::= x | y | z",
  "<literal> ::= 1 | 2 | 3",
  "<op> ::= + | - | * | /",
};

int main(void) {
  const char *root = "omega_libmrg_full_pkg";
  char path[1024];

  if (ensure_dir(root) != 0) { fprintf(stderr, "cannot create %s\n", root); return 1; }

  const char *dirs[] = { "bin", "lib", "include", "etc", "usr", "scripts", "data", "web" };
  for (size_t i = 0; i < sizeof(dirs)/sizeof(dirs[0]); ++i) {
    snprintf(path, sizeof(path), "%s/%s", root, dirs[i]);
    if (ensure_dir(path) != 0) { fprintf(stderr, "cannot create %s\n", path); return 1; }
  }

  /* write Makefile */
  snprintf(path, sizeof(path), "%s/Makefile", root);
  if (write_lines_file(path, makefile_lines, sizeof(makefile_lines)/sizeof(makefile_lines[0]), 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  /* scripts/pdftotext-wrapper.sh */
  snprintf(path, sizeof(path), "%s/scripts/pdftotext-wrapper.sh", root);
  if (write_lines_file(path, pdftotext_lines, sizeof(pdftotext_lines)/sizeof(pdftotext_lines[0]), 0755) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  /* Omega Script */
  snprintf(path, sizeof(path), "%s/math_expression_generator.os", root);
  if (write_lines_file(path, omega_lines, sizeof(omega_lines)/sizeof(omega_lines[0]), 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  /* Python generator */
  snprintf(path, sizeof(path), "%s/lib/math_expression_generator.py", root);
  if (write_lines_file(path, py_lines, sizeof(py_lines)/sizeof(py_lines[0]), 0755) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  /* bin/generate_analyze.c */
  snprintf(path, sizeof(path), "%s/bin/generate_analyze.c", root);
  if (write_lines_file(path, analyze_c_lines, sizeof(analyze_c_lines)/sizeof(analyze_c_lines[0]), 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }

  /* bnf samples */
  snprintf(path, sizeof(path), "%s/c.bnf", root);
  if (write_lines_file(path, bnf_lines, sizeof(bnf_lines)/sizeof(bnf_lines[0]), 0) != 0) { fprintf(stderr, "write failed: %s\n", path); return 1; }
  snprintf(path, sizeof(path), "%s/python.bnf", root);
  write_lines_file(path, bnf_lines, sizeof(bnf_lines)/sizeof(bnf_lines[0]), 0);
  snprintf(path, sizeof(path), "%s/ruby.bnf", root);
  write_lines_file(path, bnf_lines, sizeof(bnf_lines)/sizeof(bnf_lines[0]), 0);
  snprintf(path, sizeof(path), "%s/javascript.bnf", root);
  write_lines_file(path, bnf_lines, sizeof(bnf_lines)/sizeof(bnf_lines[0]), 0);

  printf("Generated package '%s'\n", root);
  printf("To build and use:\n");
  printf("  cd %s\n", root);
  printf("  make\n");
  printf("  ./bin/generate_analyze <input.pdf> [language]\n");
  printf("Requirements: pdftotext, python3\n");
  return 0;
}
/*
```

必要であれば：
- `generate_analyze` の PDF アップロード・Web UI 統合や、Omega Script を直接実行するランタイムの追加を行えます。どれを優先するか指示してください。
*/
