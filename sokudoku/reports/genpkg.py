#!/usr/bin/env python3
# pkggen.py
# Generate a package that contains:
#  - simple BNF files for several languages
#  - a Python "omega_formula" tool that accepts Omega Script-like input
#    and returns template-based formulae / explanations.
#  - package layout: bin, lib, include, etc, usr
#
# Usage:
#   python3 pkggen.py
#
# After running, inspect ./omega_formula_pkg

import os
import sys
import json
from textwrap import dedent

ROOT = "omega_formula_pkg"

BNF_FILES = {
    "c.bnf": dedent("""\
        ; Very small illustrative C BNF (not complete)
        translation_unit ::= external_declaration*
        external_declaration ::= function_definition | declaration
        function_definition ::= type_specifier declarator compound_statement
        declaration ::= type_specifier init_declarator_list ';'
        type_specifier ::= "int" | "char" | "void" | "double"
        declarator ::= identifier '(' parameter_list ')' | identifier
        parameter_list ::= parameter_declaration (',' parameter_declaration)*
        parameter_declaration ::= type_specifier declarator
        compound_statement ::= '{' (declaration | statement)* '}'
        statement ::= expression_statement | compound_statement | return_statement
        expression_statement ::= expression ';'
        return_statement ::= 'return' expression ';'
        expression ::= assignment_expression (',' assignment_expression)*
        assignment_expression ::= conditional_expression | unary_expression '=' assignment_expression
        conditional_expression ::= logical_or_expression ('?' expression ':' conditional_expression)?
        logical_or_expression ::= logical_and_expression ('||' logical_and_expression)*
        logical_and_expression ::= equality_expression ('&&' equality_expression)*
        equality_expression ::= relational_expression (('=='|'!=') relational_expression)*
        relational_expression ::= additive_expression (('<'|'>'|'<='|'>=') additive_expression)*
        additive_expression ::= multiplicative_expression (('+'|'-') multiplicative_expression)*
        multiplicative_expression ::= unary_expression (('*'|'/'|'%') unary_expression)*
        unary_expression ::= ('+'|'-'|'!'|'~')? primary_expression
        primary_expression ::= identifier | constant | '(' expression ')'
        identifier ::= /[A-Za-z_][A-Za-z0-9_]*/
        constant ::= number | character
        number ::= /[0-9]+(\\.[0-9]+)?/
    """),
    "python.bnf": dedent("""\
        ; Very small illustrative Python-like BNF
        file_input ::= (stmt)* EOF
        stmt ::= simple_stmt | compound_stmt
        simple_stmt ::= small_stmt (';' small_stmt)* (';')? NEWLINE
        small_stmt ::= expression_stmt | assign_stmt | return_stmt
        expression_stmt ::= testlist
        assign_stmt ::= target_list '=' testlist
        return_stmt ::= 'return' testlist?
        compound_stmt ::= if_stmt | while_stmt | funcdef
        if_stmt ::= 'if' test ':' suite ('elif' test ':' suite)* ('else' ':' suite)?
        while_stmt ::= 'while' test ':' suite
        funcdef ::= 'def' NAME parameters ':' suite
        parameters ::= '(' (typedargslist)? ')'
        suite ::= simple_stmt | NEWLINE INDENT stmt+ DEDENT
        test ::= or_test ('if' or_test 'else' test)?
        or_test ::= and_test ('or' and_test)*
        and_test ::= not_test ('and' not_test)*
        not_test ::= 'not' not_test | comparison
        comparison ::= expr (comp_op expr)*
        expr ::= xor_expr ('|' xor_expr)*
        xor_expr ::= and_expr ('^' and_expr)*
        and_expr ::= shift_expr ('&' shift_expr)*
        shift_expr ::= arith_expr (('<<'|'>>') arith_expr)*
        arith_expr ::= term (('+'|'-') term)*
        term ::= factor (('*'|'/'|'%') factor)*
        factor ::= ('+'|'-'|'~') factor | power
        power ::= atom ['**' factor]
        atom ::= NAME | NUMBER | STRING | '(' testlist ')'
        NAME ::= /[A-Za-z_][A-Za-z0-9_]*/
    """),
    "ruby.bnf": dedent("""\
        ; Tiny illustrative Ruby BNF
        program ::= (statement)*
        statement ::= expression_stmt | def_stmt | if_stmt
        expression_stmt ::= expression NEWLINE
        def_stmt ::= 'def' NAME parameter_list? NEWLINE body 'end'
        if_stmt ::= 'if' expression NEWLINE body ('elsif' expression NEWLINE body)* ('else' NEWLINE body)? 'end'
        expression ::= assignment | call | literal | variable
        assignment ::= variable '=' expression
        call ::= primary ('.' NAME (argument_list)?)*
        primary ::= variable | literal | '(' expression ')'
        variable ::= NAME
        literal ::= NUMBER | STRING | 'true' | 'false' | 'nil'
        NAME ::= /[A-Za-z_][A-Za-z0-9_]*/
    """),
    "javascript.bnf": dedent("""\
        ; Tiny JS-like BNF (illustrative)
        Program ::= StatementList
        StatementList ::= (Statement)*
        Statement ::= VariableDeclaration | FunctionDeclaration | ExpressionStatement
        VariableDeclaration ::= ('var'|'let'|'const') VariableDeclaratorList ';'
        FunctionDeclaration ::= 'function' Identifier '(' ParameterList? ')' '{' FunctionBody '}'
        ExpressionStatement ::= Expression ';'
        Expression ::= AssignmentExpression
        AssignmentExpression ::= ConditionalExpression | LeftHandSideExpression '=' AssignmentExpression
        ConditionalExpression ::= LogicalORExpression ('?' AssignmentExpression ':' AssignmentExpression)?
        LogicalORExpression ::= LogicalANDExpression ('||' LogicalANDExpression)*
        LogicalANDExpression ::= EqualityExpression ('&&' EqualityExpression)*
        EqualityExpression ::= RelationalExpression (('=='|'!='|'===') RelationalExpression)*
        RelationalExpression ::= AdditiveExpression (('<'|'>'|'<='|'>=') AdditiveExpression)*
        AdditiveExpression ::= MultiplicativeExpression (('+'|'-') MultiplicativeExpression)*
        MultiplicativeExpression ::= UnaryExpression (('*'|'/'|'%') UnaryExpression)*
        UnaryExpression ::= ('+'|'-'|'!'|'~')? UpdateExpression
        UpdateExpression ::= LeftHandSideExpression (('++'|'--'))?
        LeftHandSideExpression ::= Identifier | CallExpression
        CallExpression ::= MemberExpression Arguments
        Identifier ::= /[A-Za-z_$][A-Za-z0-9_$]*/
    """),
    "java.bnf": dedent("""\
        ; Tiny Java-like BNF (illustrative)
        CompilationUnit ::= (TypeDeclaration)*
        TypeDeclaration ::= ClassDeclaration | InterfaceDeclaration
        ClassDeclaration ::= 'class' Identifier ('extends' Type)? ('implements' TypeList)? ClassBody
        ClassBody ::= '{' (ClassMemberDecl)* '}'
        ClassMemberDecl ::= FieldDecl | MethodDecl | ConstructorDecl
        FieldDecl ::= Type VariableDeclarators ';'
        MethodDecl ::= Type Identifier '(' ParameterList? ')' MethodBody
        Type ::= PrimitiveType | ReferenceType
        PrimitiveType ::= 'int'|'long'|'short'|'byte'|'char'|'boolean'|'float'|'double'
        Identifier ::= /[A-Za-z_][A-Za-z0-9_]*/
    """),
    "erlang.bnf": dedent("""\
        ; Tiny Erlang-like BNF
        module ::= (attribute)* (export_spec)? (function)*
        attribute ::= '-' NAME '(' args ')' '.'
        function ::= atom '(' args ')' '->' clauses '.'
        clauses ::= clause (';' clause)*
        clause ::= expr '->' expr
        expr ::= atom | number | tuple | list | call
        call ::= atom '(' args ')'
        atom ::= /[a-z][A-Za-z0-9_]*/
    """),
    "emacs_lisp.bnf": dedent("""\
        ; Tiny Emacs Lisp-like BNF
        program ::= form*
        form ::= atom | list
        list ::= '(' form* ')'
        atom ::= SYMBOL | STRING | NUMBER
        SYMBOL ::= /[A-Za-z_+-\\/*=><!?][A-Za-z0-9_+-\\/*=><!?]*/
    """),
}

# Simple templates for Omega Script -> math/physics generation
TEMPLATES = {
    "zeta": {
        "title": "Riemann zeta function",
        "body": dedent("""\
            Definition:
              ζ(s) = Σ_{n=1}^∞ n^{-s},  (Re(s) > 1)

            Analytic continuation and relation (Gamma & Mellin transform form, schematic):
              ζ(s) = (1 / (Γ(s/2) π^{s/2})) ∫_0^∞ x^{s/2 - 1} Θ(x) dx  (conceptual)

            Notable values:
              ζ(2) = π^2 / 6
              ζ(2n) expressed in terms of Bernoulli numbers and π^{2n}

            Note: numerical evaluation for real s>1 via Dirichlet series; use libraries for high-precision.
        """)
    },
    "einstein": {
        "title": "Einstein field equations (global manifold form)",
        "body": dedent("""\
            Local form (Einstein equation):
              G_{μν} + Λ g_{μν} = κ T_{μν}
            where G_{μν} = R_{μν} - 1/2 R g_{μν},  κ = 8πG / c^4

            Action (global integral form):
              S[g] = (1 / 2κ) ∫_M (R - 2Λ) √|g| d^4x + S_matter
            Variation δS/δg = 0 yields the field equations.

            For a closed manifold M, global integrals of curvature relate to topological invariants (Gauss–Bonnet etc.) in lower dimensions.
        """)
    },
    "higgs": {
        "title": "Higgs field (Lagrangian and EoM)",
        "body": dedent("""\
            Lagrangian (complex scalar doublet φ, schematic):
              L = (D_μ φ)† (D^μ φ) - V(φ)
              V(φ) = -μ^2 φ†φ + λ (φ†φ)^2

            Euler-Lagrange equation:
              D_μ D^μ φ + ∂V/∂φ† = 0

            Spontaneous symmetry breaking: vacuum expectation value |⟨φ⟩| = v ≠ 0 gives mass to gauge bosons and yields a physical Higgs scalar.
        """)
    }
}

# Safety: forbid requests about drug formulation etc.
FORBIDDEN_TERMS = ["薬", "調合", "製造", "合成", "処方", "リスペリid", "risperidone", "毒", "爆発"]

def mkdir_p(path):
    os.makedirs(path, exist_ok=True)

def write_file(path, data, mode="w"):
    mkdir_p(os.path.dirname(path) or ".")
    with open(path, mode) as f:
        f.write(data)

def create_package():
    # dirs
    dirs = ["bin", "lib", "include", "etc", "usr", "bnf"]
    for d in dirs:
        mkdir_p(os.path.join(ROOT, d))
    # write BNF files
    for name, content in BNF_FILES.items():
        write_file(os.path.join(ROOT, "bnf", name), content)
    # write include sample
    write_file(os.path.join(ROOT, "include", "omega_defs.h"), dedent("""\
        /* Sample include for Omega-based tooling */
        #ifndef OMEGA_DEFS_H
        #define OMEGA_DEFS_H
        #define OMEGA_VERSION "0.1"
        #endif
    """))
    # write lib util (python)
    write_file(os.path.join(ROOT, "lib", "util.py"), dedent("""\
        # utility functions for omega_formula package
        import math
        def approx_zeta(s, n=100000):
            if s <= 1.0:
                return float('nan')
            total = 0.0
            for k in range(1, n+1):
                total += 1.0 / (k**s)
            return total
    """))
    # write etc config
    write_file(os.path.join(ROOT, "etc", "omega.conf"), dedent("""\
        [omega]
        name = Omega Formula Generator
        version = 0.1
    """))
    # write usr sample
    write_file(os.path.join(ROOT, "usr", "LICENSE.txt"), "Educational stub package. No model weights included.\n")
    # write README
    write_file(os.path.join(ROOT, "README.md"), dedent(f"""\
        # Omega Formula Package (generated)
        This package is a template that contains:
        - BNF files for several programming languages (bnf/)
        - A simple Omega Script -> formula generator (bin/omega_formula.py)
        - lib/ include/ etc/ usr/ layout
        - This is a non-proprietary, educational scaffold (no model code or weights).
    """))
    # write generator script to bin
    write_file(os.path.join(ROOT, "bin", "omega_formula.py"), dedent("""\
        #!/usr/bin/env python3
        import sys, os, re
        from textwrap import dedent
        # small local imports
        libpath = os.path.join(os.path.dirname(__file__), "..", "lib")
        libpath = os.path.abspath(libpath)
        if libpath not in sys.path:
            sys.path.insert(0, libpath)
        try:
            import util
        except Exception:
            util = None

        # templates (embedded small set)
        TEMPLATES = """ + json.dumps(TEMPLATES) + """

        FORBIDDEN = """ + json.dumps(FORBIDDEN_TERMS) + """

        def contains_forbidden(s):
            s_low = s.lower()
            for term in FORBIDDEN:
                if term.lower() in s_low:
                    return True
            return False

        def detect_intent(line):
            low = line.lower()
            if any(k in low for k in ['zeta', 'ゼータ', 'ζ']):
                return 'zeta'
            if any(k in low for k in ['一般相対', 'アインシュタイン', 'einstein', '多様体']):
                return 'einstein'
            if any(k in low for k in ['ヒッグス', 'higgs']):
                return 'higgs'
            return None

        def handle_prompt(line):
            if contains_forbidden(line):
                print('安全上の理由により、危険または規制対象の内容（製造や調合など）には対応できません。')
                return
            intent = detect_intent(line)
            if intent and intent in TEMPLATES:
                tpl = TEMPLATES[intent]
                print('----', tpl['title'], '----')
                print(dedent(tpl['body']))
                # if util available, add an approximate numeric demo
                if util and intent == 'zeta':
                    try:
                        s = 2.0
                        val = util.approx_zeta(s, n=10000)
                        print('Example numeric (approx): zeta(2) ~', val)
                    except Exception:
                        pass
            else:
                # fallback: echo with help
                print('I can generate formula templates for requests like:')
                print(' - "オイラーのゼータ関数を記述してください"')
                print(' - "一般相対性理論の大域的多様体の式を記述してください"')
                print(' - "ヒッグス場方程式を記述してください"')
                print('\\n(この tool はテンプレートベースの生成器です。)')

        def repl():
            print('Omega Formula Generator (template-based). Ctrl-D to exit.')
            try:
                while True:
                    line = input('omega> ').strip()
                    if not line:
                        continue
                    handle_prompt(line)
            except EOFError:
                print('\\ngoodbye')

        if __name__ == "__main__":
            repl()
    """), mode="w")
    # make executable
    os.chmod(os.path.join(ROOT, "bin", "omega_formula.py"), 0o755)

    # write a simple Makefile to build (none build steps, but create bin)
    write_file(os.path.join(ROOT, "Makefile"), dedent("""\
        .PHONY: all install clean
        all:
        \t@echo "No compilation necessary; Python scripts are in bin/"
        install:
        \tmkdir -p $(PREFIX)/bin
        \tcp bin/omega_formula.py $(PREFIX)/bin/omega_formula
        clean:
        \t@echo "Nothing to clean"
    """))

    print(f"Package generated under '{ROOT}'.")
    print("Run the formula generator:")
    print(f"  python3 {os.path.join(ROOT, 'bin', 'omega_formula.py')}")
    print("BNF files are in", os.path.join(ROOT, "bnf"))

if __name__ == "__main__":
    create_package()
