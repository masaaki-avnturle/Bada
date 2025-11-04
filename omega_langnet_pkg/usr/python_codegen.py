# usr/python_codegen.py - simple codegen templates
import sys, json

def emit_python(ast, out):
    with open(out, 'w') as f:
        f.write('# generated python from bnf AST\n')
        f.write('print("Hello from generated Python")\n')

def emit_c(ast, out):
    with open(out, 'w') as f:
        f.write('/* generated C stub */\n#include <stdio.h>\nint main(){ printf("Hello from generated C\\n"); return 0; }\n')

if __name__ == '__main__':
    if len(sys.argv)<4:
        print('usage: python python_codegen.py <ast.json> <lang:c|py> <out>')
        sys.exit(1)
    ast = json.load(open(sys.argv[1]))
    if sys.argv[2]=='py': emit_python(ast, sys.argv[3])
    else: emit_c(ast, sys.argv[3])
