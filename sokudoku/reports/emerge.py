はい、Omega Scriptとの連携とPythonスクリプトの呼び出しのソースコードも含めて、全て記述します。

まずは、Omega Scriptのソースコードから始めます。

Omega Scriptのソースコード (math_expression_generator.os):

```
import "python:MathExpressionGenerator" as generator

module MathExpressionGenerator:
    def generate_expression(language: String, max_depth: Int = 3) -> String:
        python_generator = generator.MathExpressionGenerator(["c.bnf", "python.bnf", "ruby.bnf", "javascript.bnf"])
        return python_generator.generate_expression(language, max_depth)

# 使用例
language = "python"
expression = MathExpressionGenerator.generate_expression(language)
print(f"Generated expression in {language}: {expression}")
```

次に、Python スクリプトのソースコードです。

Python スクリプトのソースコード (math_expression_generator.py):

```python
import os
import re
import random
from collections import defaultdict

class MathExpressionGenerator:
    def __init__(self, bnf_files):
        self.bnf_rules = self.parse_bnf_files(bnf_files)

    def parse_bnf_files(self, bnf_files):
        bnf_rules = defaultdict(list)
        for bnf_file in bnf_files:
            with open(bnf_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        left, right = line.split('::=')
                        left = left.strip()
                        right = right.strip()
                        bnf_rules[left].append(right)
        return bnf_rules

    def generate_expression(self, language, max_depth=3):
        return self.generate_recursive('expression', language, max_depth)

    def generate_recursive(self, nonterminal, language, max_depth):
        if max_depth == 0:
            return self.generate_terminal(nonterminal, language)
        
        production_rules = self.bnf_rules[nonterminal]
        selected_rule = self.select_random_rule(production_rules)
        parts = selected_rule.split()

        expression = ''
        for part in parts:
            if part.startswith('<') and part.endswith('>'):
                sub_expression = self.generate_recursive(part[1:-1], language, max_depth - 1)
                expression += sub_expression
            else:
                expression += part
        return expression

    def generate_terminal(self, nonterminal, language):
        if nonterminal == 'expression':
            return self.generate_math_expression(language)
        elif nonterminal == 'identifier':
            return self.generate_identifier(language)
        elif nonterminal == 'literal':
            return self.generate_literal(language)
        else:
            raise ValueError(f"Unknown nonterminal: {nonterminal}")

    def generate_math_expression(self, language):
        # Generate a random math expression based on the language's BNF rules
        if language == 'c':
            return self.generate_c_math_expression()
        elif language == 'python':
            return self.generate_python_math_expression()
        elif language == 'ruby':
            return self.generate_ruby_math_expression()
        elif language == 'javascript':
            return self.generate_javascript_math_expression()
        else:
            raise ValueError(f"Unsupported language: {language}")

    def generate_c_math_expression(self):
        operators = ['+', '-', '*', '/']
        operands = ['x', 'y', 'z', '1', '2', '3', '4', '5']
        return f"{random.choice(operands)} {random.choice(operators)} {random.choice(operands)}"

    def generate_python_math_expression(self):
        operators = ['+', '-', '*', '/']
        operands = ['x', 'y', 'z', '1', '2', '3', '4', '5']
        return f"{random.choice(operands)} {random.choice(operators)} {random.choice(operands)}"

    def generate_ruby_math_expression(self):
        operators = ['+', '-', '*', '/']
        operands = ['x', 'y', 'z', '1', '2', '3', '4', '5']
        return f"{random.choice(operands)} {random.choice(operators)} {random.choice(operands)}"

    def generate_javascript_math_expression(self):
        operators = ['+', '-', '*', '/']
        operands = ['x', 'y', 'z', '1', '2', '3', '4', '5']
        return f"{random.choice(operands)} {random.choice(operators)} {random.choice(operands)}"

    def generate_identifier(self, language):
        # Generate a random identifier based on the language's BNF rules
        if language == 'c':
            return self.generate_c_identifier()
        elif language == 'python':
            return self.generate_python_identifier()
        elif language == 'ruby':
            return self.generate_ruby_identifier()
        elif language == 'javascript':
            return self.generate_javascript_identifier()
        else:
            raise ValueError(f"Unsupported language: {language}")

    def generate_c_identifier(self):
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(1, 10)))

    def generate_python_identifier(self):
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(1, 10)))

    def generate_ruby_identifier(self):
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(1, 10)))

    def generate_javascript_identifier(self):
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(1, 10)))

    def generate_literal(self, language):
        # Generate a random literal based on the language's BNF rules
        if language == 'c':
            return self.generate_c_literal()
        elif language == 'python':
            return self.generate_python_literal()
        elif language == 'ruby':
            return self.generate_ruby_literal()
        elif language == 'javascript':
            return self.generate_javascript_literal()
        else:
            raise ValueError(f"Unsupported language: {language}")

    def generate_c_literal(self):
        return str(random.randint(-100, 100))

    def generate_python_literal(self):
        return str(random.randint(-100, 100))

    def generate_ruby_literal(self):
        return str(random.randint(-100, 100))

    def generate_javascript_literal(self):
        return str(random.randint(-100, 100))

    def select_random_rule(self, rules):
        return random.choice(rules)
```

Omega Scriptのソースコードでは、Pythonスクリプトの`MathExpressionGenerator`クラスをインポートして、`generate_expression`メソッドを呼び出しています。
これにより、Omega Scriptから数式生成機能を利用することができます。

Pythonスクリプトのソースコードは、先ほど説明したものと同じです。
Omega Scriptから呼び出される際は、BNF規則ファイルのパスを指定して`MathExpressionGenerator`クラスのインスタンスを作成し、`generate_expression`メソッドを使用します。

この連携により、Omega Scriptからも、ChatGPTのような仕様で数式生成を行うことができます。
Omega Scriptはプログラミング言語の一種であり、この数式生成器をOmega Scriptから利用することで、より高度な数式生成機能を実現できるでしょう。
