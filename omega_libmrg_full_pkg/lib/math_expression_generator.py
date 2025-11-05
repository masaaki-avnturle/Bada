#!/usr/bin/env python3
import sys
import argparse
import random
from collections import defaultdict

class MathExpressionGenerator:
    def __init__(self, bnf_files):
        self.bnf_rules = self.parse_bnf_files(bnf_files)

    def parse_bnf_files(self, bnf_files):
        bnf_rules = defaultdict(list)
        for bnf_file in bnf_files:
            try:
                with open(bnf_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '::=' in line:
                                left, right = line.split('::=', 1)
                                left = left.strip()
                                right = right.strip()
                                bnf_rules[left].append(right)
            except FileNotFoundError:
                continue
        return bnf_rules

    def generate_expression(self, language, max_depth=3):
        return self.generate_recursive('expression', language, max_depth)

    def generate_recursive(self, nonterminal, language, max_depth):
        if max_depth == 0:
            return self.generate_terminal(nonterminal, language)
        rules = self.bnf_rules.get(nonterminal)
        if not rules:
            return self.generate_terminal(nonterminal, language)
        selected_rule = random.choice(rules)
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
            return ''

    def generate_math_expression(self, language):
        ops = ['+', '-', '*', '/']
        vals = ['x','y','z','1','2','3','4','5']
        return f"{random.choice(vals)} {random.choice(ops)} {random.choice(vals)}"

    def generate_identifier(self, language):
        import string
        return ''.join(random.choices(string.ascii_lowercase, k=random.randint(1,8)))

    def generate_literal(self, language):
        return str(random.randint(-100,100))

def main():
    p = argparse.ArgumentParser(description='Math expression generator')
    p.add_argument('--language', default='python')
    p.add_argument('--max-depth', type=int, default=3)
    args = p.parse_args()
    gen = MathExpressionGenerator(['c.bnf','python.bnf','ruby.bnf','javascript.bnf'])
    expr = gen.generate_expression(args.language, args.max_depth)
    print(expr)

if __name__ == '__main__':
    main()
