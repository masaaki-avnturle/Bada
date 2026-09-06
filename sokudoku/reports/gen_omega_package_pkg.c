以下は、要求どおり「パッケージを生成して所定のファイル（Omega Script と Python スクリプト等）を所定ディレクトリに配置する」C プログラムです。実行するとカレントに `omega_package/` を作成し、`bin`, `lib`, `include`, `etc`, `usr` に指定のファイル群を書き出します。生成される Python スクリプトはあなたが提示した `MathExpressionGenerator` 実装を含み、Omega Script ソース（math_expression_generator.os）も配置します。起動用に簡易シェルラッパー（bin/run_generator.sh）も作成します。

  注意:
- 出力物はテンプレート／教育用です。危険な薬剤製造等に関する具体手順は含みません。
- 実行環境に Python3 が必要です（生成されたスクリプトは Python3 で動きます）。
  - 実行方法: 保存後コンパイルして実行すると package が作られます。

  保存ファイル名例: gen_omega_package.c
  コンパイル:
gcc -O2 -std=c11 -o gen_omega_package gen_omega_package.c
  実行:
./gen_omega_package

  ソースコード（gen_omega_package.c）:

```c
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

  static int ensure_dir(const char *path){
  int r = MKDIR(path);
  if(r == 0) return 0;
  if(errno == EEXIST) return 0;
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
  const char *root = "omega_package";
  char p[1024];

  /* create directories */
  const char *dirs[] = {"bin", "lib", "include", "etc", "usr", "bnf"};
  for(size_t i=0;i<sizeof(dirs)/sizeof(dirs[0]);++i){
    snprintf(p, sizeof p, "%s%c%s", root, PATH_SEP, dirs[i]);
    if(ensure_dir(p) != 0){
      fprintf(stderr, "mkdir failed: %s (%s)\n", p, strerror(errno));
      return 1;
    }
  }

  /* write Omega Script file */
    const char *omega_src =
"import \"python:MathExpressionGenerator\" as generator\n\n"
"module MathExpressionGenerator:\n"
"    def generate_expression(language: String, max_depth: Int = 3) -> String:\n"
"        python_generator = generator.MathExpressionGenerator([\"c.bnf\", \"python.bnf\", \"ruby.bnf\", \"javascript.bnf\"])\n"
"        return python_generator.generate_expression(language, max_depth)\n\n"
"# 使用例\n"
"language = \"python\"\n"
"expression = MathExpressionGenerator.generate_expression(language)\n"
      "print(f\"Generated expression in {language}: {expression}\")\n";

    snprintf(p, sizeof p, "%s%cmath_expression_generator.os", root, PATH_SEP);
    if(write_file(p, omega_src) != 0){ fprintf(stderr, "write failed: %s\n", p); return 1; }

    /* write Python script */
    const char *py_src =
      "import os\nimport re\nimport random\nfrom collections import defaultdict\n\nclass MathExpressionGenerator:\n    def __init__(self, bnf_files):\n        self.bnf_rules = self.parse_bnf_files(bnf_files)\n\n    def parse_bnf_files(self, bnf_files):\n        bnf_rules = defaultdict(list)\n        for bnf_file in bnf_files:\n            try:\n                with open(os.path.join('bnf', bnf_file), 'r', encoding='utf-8') as f:\n                    for line in f:\n                        line = line.strip()\n                        if line and not line.startswith(';') and '::=' in line:\n                            left, right = line.split('::=', 1)\n                            left = left.strip()\n                            right = right.strip()\n                            bnf_rules[left].append(right)\n            except FileNotFoundError:\n                # missing BNF file: continue with defaults\n                continue\n        return bnf_rules\n\n    def generate_expression(self, language, max_depth=3):\n        return self.generate_recursive('expression', language, max_depth)\n\n    def generate_recursive(self, nonterminal, language, max_depth):\n        if max_depth <= 0:\n            return self.generate_terminal(nonterminal, language)\n        production_rules = self.bnf_rules.get(nonterminal)\n        if not production_rules:\n            return self.generate_terminal(nonterminal, language)\n        selected_rule = self.select_random_rule(production_rules)\n        parts = selected_rule.split()\n        expression = ''\n        for part in parts:\n            if part.startswith('<') and part.endswith('>'):\n                sub_expression = self.generate_recursive(part[1:-1], language, max_depth - 1)\n                expression += sub_expression\n            else:\n                expression += part\n        return expression\n\n    def generate_terminal(self, nonterminal, language):\n        if nonterminal == 'expression':\n            return self.generate_math_expression(language)\n        elif nonterminal == 'identifier':\n            return self.generate_identifier(language)\n        elif nonterminal == 'literal':\n            return self.generate_literal(language)\n        else:\n            return ''\n\n    def generate_math_expression(self, language):\n        ops = [' + ', ' - ', ' * ', ' / ']\n        vals = ['x','y','z','1','2','3','4','5']\n        return random.choice(vals) + random.choice(ops) + random.choice(vals)\n\n    def generate_identifier(self, language):\n        length = random.randint(1,8)\n        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=length))\n\n    def generate_literal(self, language):\n        return str(random.randint(-100,100))\n\n    def select_random_rule(self, rules):\n        return random.choice(rules)\n\n# If run as script, provide a small CLI\nif __name__ == '__main__':\n    gen = MathExpressionGenerator(['c.bnf','python.bnf','ruby.bnf','javascript.bnf'])\n    import sys\n    lang = 'python'\n    if len(sys.argv) > 1:\n        lang = sys.argv[1]\n    print(gen.generate_expression(lang))\n";

    snprintf(p, sizeof p, "%s%clib%cmath_expression_generator.py", root, PATH_SEP, PATH_SEP);
    if(write_file(p, py_src) != 0){ fprintf(stderr, "write failed: %s\n", p); return 1; }

    /* write simple BNF files into bnf/ (minimal illustrative content) */
    const char *c_bnf =
      "; C minimal illustrative BNF\nexpression ::= term (('+'|'-') term)*\nterm ::= factor (('*'|'/') factor)*\nfactor ::= identifier | literal | '(' expression ')'\nidentifier ::= /[A-Za-z_][A-Za-z0-9_]*/\nliteral ::= number\nnumber ::= /[0-9]+(\\.[0-9]+)?/\n";
    const char *python_bnf =
      "; Python minimal illustrative BNF\nexpression ::= term (('+'|'-') term)*\nterm ::= factor (('*'|'/') factor)*\nfactor ::= identifier | literal | '(' expression ')'\nidentifier ::= NAME\nliteral ::= NUMBER\n";
    const char *ruby_bnf =
      "; Ruby minimal illustrative BNF\nexpression ::= term (('+'|'-') term)*\n";
    const char *js_bnf =
      "; JavaScript minimal illustrative BNF\nexpression ::= term (('+'|'-') term)*\n";

    snprintf(p, sizeof p, "%s%cbnf%cc.bnf", root, PATH_SEP, PATH_SEP);
    if(write_file(p, c_bnf) != 0){ fprintf(stderr, "write failed: %s\n", p); return 1; }
    snprintf(p, sizeof p, "%s%cbnf%spython.bnf", root, PATH_SEP, PATH_SEP);
    if(write_file(p, python_bnf) != 0){ fprintf(stderr, "write failed: %s\n", p); return 1; }
    snprintf(p, sizeof p, "%s%cbnf%sruby.bnf", root, PATH_SEP, PATH_SEP);
    if(write_file(p, ruby_bnf) != 0){ fprintf(stderr, "write failed: %s\n", p); return 1; }
    snprintf(p, sizeof p, "%s%cbnf%sjavascript.bnf", root, PATH_SEP, PATH_SEP);
    if(write_file(p, js_bnf) != 0){ fprintf(stderr, "write failed: %s\n", p); return 1; }

    /* write include sample */
    const char *inc =
      "/* include/omega.h - sample header */\n#ifndef OMEGA_H\n#define OMEGA_H\n#define OMEGA_PACKAGE \"omega_package\"\n#endif\n";
    snprintf(p, sizeof p, "%s%cinclude%comega.h", root, PATH_SEP, PATH_SEP);
    if(write_file(p, inc) != 0){ fprintf(stderr, "write failed: %s\n", p); return 1; }

    /* write etc config */
    const char *etc =
      "[omega]\nname = Omega Math Expression Generator\nversion = 0.1\n";
    snprintf(p, sizeof p, "%s%cetc%comega.conf", root, PATH_SEP, PATH_SEP);
    if(write_file(p, etc) != 0){ fprintf(stderr, "write failed: %s\n", p); return 1; }

    /* write usr/LICENSE */
    const char *lic = "Educational package. No proprietary model weights included.\n";
    snprintf(p, sizeof p, "%s%cusr%cLICENSE", root, PATH_SEP, PATH_SEP);
    if(write_file(p, lic) != 0){ fprintf(stderr, "write failed: %s\n", p); return 1; }

    /* write bin runner that invokes Python with module path adjusted */
    const char *runner_sh =
      "#!/bin/sh\n# run_generator.sh - launch the MathExpressionGenerator from the package\nDIR=$(cd \"$(dirname \"$0\")/..\" && pwd)\nPYTHONPATH=\"$DIR/lib\" python3 - <<'PY'\nfrom math_expression_generator import MathExpressionGenerator\nimport sys\nlang = 'python'\nif len(sys.argv) > 1:\n    lang = sys.argv[1]\ngen = MathExpressionGenerator(['c.bnf','python.bnf','ruby.bnf','javascript.bnf'])\nprint(gen.generate_expression(lang))\nPY\n";
    snprintf(p, sizeof p, "%s%cbin%crun_generator.sh", root, PATH_SEP, PATH_SEP);
    if(write_file(p, runner_sh) != 0){ fprintf(stderr, "write failed: %s\n", p); return 1; }
#if !defined(_WIN32) && !defined(_WIN64)
    /* make script executable */
    snprintf(p, sizeof p, "%s%cbin%crun_generator.sh", root, PATH_SEP, PATH_SEP);
    chmod(p, 0755);
#endif

    printf("Package '%s' created.\n", root);
    printf("To run generator:\n");
    printf("  cd %s\n", root);
    printf("  ./bin/run_generator.sh [language]\n");
    return 0;
}
```

以上を保存・コンパイル・実行すれば、指定の構成でパッケージが作成されます。必要なら、生成された C の起動プログラム（ランチャ）や、より厳密な BNF を bnf/ に追加するスクリプト、あるいは C 側から直接 Python API を呼ぶサンプル（Python/C API を利用）を追加で提供します。どれを追加しますか？
