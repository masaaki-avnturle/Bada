"""Recursive-descent parser (構文解析器) for the Bada language.

Consumes the token stream produced by the lexer and builds an AST.
"""

from . import nodes as N
from .lexer import tokenize, EOF, OP, KEYWORD, IDENT, NUMBER, STRING
from .errors import BadaSyntaxError


# Operator symbols that may be overloaded via `operator <sym> (...)`.
OVERLOADABLE = {
    "+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=",
    "<~", "~>", "-<",
}

# Map operator symbols to the dunder method names used at runtime.
OP_METHODS = {
    "+": "__add__", "-": "__sub__", "*": "__mul__", "/": "__div__",
    "%": "__mod__", "==": "__eq__", "!=": "__ne__",
    "<": "__lt__", ">": "__gt__", "<=": "__le__", ">=": "__ge__",
    "<~": "__lact__", "~>": "__ract__", "-<": "__branch__",
}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # --- token helpers ----------------------------------------------------

    @property
    def cur(self):
        return self.tokens[self.pos]

    def at_end(self):
        return self.cur.type == EOF

    def check(self, type_, value=None):
        t = self.cur
        if t.type != type_:
            return False
        return value is None or t.value == value

    def check_kw(self, *words):
        return self.cur.type == KEYWORD and self.cur.value in words

    def check_op(self, *symbols):
        return self.cur.type == OP and self.cur.value in symbols

    def advance(self):
        t = self.cur
        if not self.at_end():
            self.pos += 1
        return t

    def match(self, type_, value=None):
        if self.check(type_, value):
            return self.advance()
        return None

    def match_op(self, *symbols):
        if self.check_op(*symbols):
            return self.advance()
        return None

    def match_kw(self, *words):
        if self.check_kw(*words):
            return self.advance()
        return None

    def expect(self, type_, value=None, what=None):
        if self.check(type_, value):
            return self.advance()
        exp = what or (f"{value!r}" if value else type_)
        got = self.cur.value if self.cur.value is not None else self.cur.type
        raise BadaSyntaxError(f"expected {exp}, got {got!r}", self.cur.line, self.cur.col)

    def expect_op(self, symbol):
        return self.expect(OP, symbol, what=f"'{symbol}'")

    def skip_semis(self):
        while self.match_op(";"):
            pass

    # --- entry point ------------------------------------------------------

    def parse(self):
        stmts = []
        self.skip_semis()
        while not self.at_end():
            stmts.append(self.statement())
            self.skip_semis()
        return N.Block(stmts)

    # --- statements -------------------------------------------------------

    def statement(self):
        if self.check_kw("let"):
            return self.let_stmt()
        if self.check_kw("class"):
            return self.class_decl()
        if self.check_kw("fun"):
            return self.func_decl()
        if self.check_kw("if"):
            return self.if_stmt()
        if self.check_kw("while"):
            return self.while_stmt()
        if self.check_kw("for"):
            return self.for_stmt()
        if self.check_kw("return"):
            return self.return_stmt()
        if self.check_kw("break"):
            line = self.advance().line
            self.skip_semis()
            return N.BreakStmt(line)
        if self.check_kw("continue"):
            line = self.advance().line
            self.skip_semis()
            return N.ContinueStmt(line)
        if self.check_kw("print"):
            return self.print_stmt()
        if self.check_kw("import"):
            return self.import_stmt()
        if self.check_op("{"):
            return self.block()
        return self.expr_stmt()

    def let_stmt(self):
        line = self.advance().line  # 'let'
        name = self.expect(IDENT, what="variable name").value
        self.expect_op("<-")
        value = self.expression()
        self.skip_semis()
        return N.LetStmt(name, value, line)

    def block(self):
        line = self.expect_op("{").line
        stmts = []
        self.skip_semis()
        while not self.check_op("}") and not self.at_end():
            stmts.append(self.statement())
            self.skip_semis()
        self.expect_op("}")
        return N.Block(stmts, line)

    def func_decl(self):
        line = self.advance().line  # 'fun'
        name = self.expect(IDENT, what="function name").value
        params = self.param_list()
        body = self.block()
        return N.FuncDecl(name, params, body, line)

    def param_list(self):
        self.expect_op("(")
        params = []
        if not self.check_op(")"):
            params.append(self.expect(IDENT, what="parameter").value)
            while self.match_op(","):
                params.append(self.expect(IDENT, what="parameter").value)
        self.expect_op(")")
        return params

    def class_decl(self):
        line = self.advance().line  # 'class'
        name = self.expect(IDENT, what="class name").value
        parent = None
        if self.match_op("<-"):
            parent = self.expect(IDENT, what="parent class name").value
        self.expect_op("{")
        fields, methods = [], []
        self.skip_semis()
        while not self.check_op("}") and not self.at_end():
            if self.check_kw("field"):
                fields.append(self.field_decl())
            elif self.check_kw("method", "static"):
                methods.append(self.method_decl())
            elif self.check_kw("operator"):
                methods.append(self.operator_decl())
            else:
                t = self.cur
                raise BadaSyntaxError(
                    f"expected field/method/operator in class body, got {t.value!r}",
                    t.line, t.col)
            self.skip_semis()
        self.expect_op("}")
        return N.ClassDecl(name, parent, fields, methods, line)

    def field_decl(self):
        line = self.advance().line  # 'field'
        name = self.expect(IDENT, what="field name").value
        default = None
        if self.match_op("<-"):
            default = self.expression()
        self.skip_semis()
        return N.FieldDecl(name, default, line)

    def method_decl(self):
        is_static = bool(self.match_kw("static"))
        line = self.expect(KEYWORD, "method", what="'method'").line
        name = self.expect(IDENT, what="method name").value
        params = self.param_list()
        body = self.block()
        return N.MethodDecl(name, params, body, is_static, line)

    def operator_decl(self):
        line = self.advance().line  # 'operator'
        if not self.check(OP) or self.cur.value not in OVERLOADABLE:
            t = self.cur
            raise BadaSyntaxError(f"cannot overload operator {t.value!r}", t.line, t.col)
        sym = self.advance().value
        method_name = OP_METHODS[sym]
        params = self.param_list()
        body = self.block()
        return N.MethodDecl(method_name, params, body, False, line)

    def if_stmt(self):
        line = self.advance().line  # 'if'
        branches = []
        cond = self.expression()
        body = self.block()
        branches.append((cond, body))
        else_block = None
        while self.check_kw("else"):
            self.advance()
            if self.check_kw("if"):
                self.advance()
                c = self.expression()
                b = self.block()
                branches.append((c, b))
            else:
                else_block = self.block()
                break
        return N.IfStmt(branches, else_block, line)

    def while_stmt(self):
        line = self.advance().line
        cond = self.expression()
        body = self.block()
        return N.WhileStmt(cond, body, line)

    def for_stmt(self):
        line = self.advance().line
        var = self.expect(IDENT, what="loop variable").value
        self.expect(KEYWORD, "in", what="'in'")
        iterable = self.expression()
        body = self.block()
        return N.ForStmt(var, iterable, body, line)

    def return_stmt(self):
        line = self.advance().line
        value = None
        if not self.check_op(";", "}") and not self.at_end():
            value = self.expression()
        self.skip_semis()
        return N.ReturnStmt(value, line)

    def print_stmt(self):
        line = self.advance().line  # 'print'
        args = []
        if not self.check_op(";", "}") and not self.at_end():
            args.append(self.expression())
            while self.match_op(","):
                args.append(self.expression())
        self.skip_semis()
        return N.PrintStmt(args, line)

    def import_stmt(self):
        line = self.advance().line
        parts = [self.expect(IDENT, what="module name").value]
        while self.match_op("::"):
            parts.append(self.expect(IDENT, what="module name").value)
        self.skip_semis()
        return N.ImportStmt(parts, line)

    def expr_stmt(self):
        expr = self.expression()
        self.skip_semis()
        return N.ExprStmt(expr, expr.line)

    # --- expressions ------------------------------------------------------

    def expression(self):
        return self.assignment()

    def assignment(self):
        expr = self.logic_or()
        if self.check_op("<-"):
            line = self.advance().line
            value = self.assignment()
            if isinstance(expr, (N.Identifier, N.Attribute, N.Index)):
                return N.Assign(expr, value, line)
            raise BadaSyntaxError("invalid assignment target", line)
        return expr

    def logic_or(self):
        expr = self.logic_and()
        while self.check_kw("or"):
            line = self.advance().line
            right = self.logic_and()
            expr = N.Logical("or", expr, right, line)
        return expr

    def logic_and(self):
        expr = self.equality()
        while self.check_kw("and"):
            line = self.advance().line
            right = self.equality()
            expr = N.Logical("and", expr, right, line)
        return expr

    def equality(self):
        expr = self.comparison()
        while self.check_op("==", "!="):
            op = self.advance()
            right = self.comparison()
            expr = N.Binary(op.value, expr, right, op.line)
        return expr

    def comparison(self):
        expr = self.term()
        while self.check_op("<", ">", "<=", ">="):
            op = self.advance()
            right = self.term()
            expr = N.Binary(op.value, expr, right, op.line)
        return expr

    def term(self):
        expr = self.factor()
        while self.check_op("+", "-"):
            op = self.advance()
            right = self.factor()
            expr = N.Binary(op.value, expr, right, op.line)
        return expr

    def factor(self):
        expr = self.unary()
        while self.check_op("*", "/", "%"):
            op = self.advance()
            right = self.unary()
            expr = N.Binary(op.value, expr, right, op.line)
        return expr

    def unary(self):
        if self.check_kw("not"):
            line = self.advance().line
            return N.Unary("not", self.unary(), line)
        if self.check_op("-"):
            line = self.advance().line
            return N.Unary("-", self.unary(), line)
        return self.manifold()

    def manifold(self):
        # The Bada "manifold" operators: left-action, right-action, branch.
        expr = self.postfix()
        while self.check_op("<~", "~>", "-<"):
            op = self.advance()
            right = self.postfix()
            expr = N.Binary(op.value, expr, right, op.line)
        return expr

    def postfix(self):
        expr = self.primary()
        while True:
            if self.check_op(".") or self.check_op("::"):
                line = self.advance().line
                name = self.expect(IDENT, what="attribute name").value
                expr = N.Attribute(expr, name, line)
            elif self.check_op("("):
                expr = self.finish_call(expr)
            elif self.check_op("["):
                line = self.advance().line
                idx = self.expression()
                self.expect_op("]")
                expr = N.Index(expr, idx, line)
            else:
                break
        return expr

    def finish_call(self, callee):
        line = self.expect_op("(").line
        args = []
        if not self.check_op(")"):
            args.append(self.expression())
            while self.match_op(","):
                args.append(self.expression())
        self.expect_op(")")
        if isinstance(callee, N.Attribute) and isinstance(callee.obj, N.SelfExpr):
            # leave as normal attribute call; handled at runtime
            pass
        return N.Call(callee, args, line)

    def primary(self):
        t = self.cur

        if self.match(NUMBER) is not None:
            return N.Literal(t.value, t.line)
        if self.match(STRING) is not None:
            return N.Literal(t.value, t.line)

        if self.check_kw("true"):
            self.advance(); return N.Literal(True, t.line)
        if self.check_kw("false"):
            self.advance(); return N.Literal(False, t.line)
        if self.check_kw("nil"):
            self.advance(); return N.Literal(None, t.line)
        if self.check_kw("self"):
            self.advance(); return N.SelfExpr(t.line)
        if self.check_kw("super"):
            return self.super_expr()

        if self.match(IDENT) is not None:
            return N.Identifier(t.value, t.line)

        if self.check_op("("):
            self.advance()
            expr = self.expression()
            self.expect_op(")")
            return expr

        if self.check_op("["):
            return self.list_literal()

        if self.check_op("{"):
            return self.map_literal()

        raise BadaSyntaxError(f"unexpected token {t.value!r}", t.line, t.col)

    def super_expr(self):
        line = self.advance().line  # 'super'
        self.expect_op(".")
        method = self.expect(IDENT, what="method name after 'super.'").value
        self.expect_op("(")
        args = []
        if not self.check_op(")"):
            args.append(self.expression())
            while self.match_op(","):
                args.append(self.expression())
        self.expect_op(")")
        return N.SuperCall(method, args, line)

    def list_literal(self):
        line = self.expect_op("[").line
        elems = []
        if not self.check_op("]"):
            elems.append(self.expression())
            while self.match_op(","):
                if self.check_op("]"):
                    break
                elems.append(self.expression())
        self.expect_op("]")
        return N.ListLit(elems, line)

    def map_literal(self):
        line = self.expect_op("{").line
        pairs = []
        if not self.check_op("}"):
            pairs.append(self.map_entry())
            while self.match_op(","):
                if self.check_op("}"):
                    break
                pairs.append(self.map_entry())
        self.expect_op("}")
        return N.MapLit(pairs, line)

    def map_entry(self):
        key = self.expression()
        self.expect_op(":")
        value = self.expression()
        return (key, value)


def parse(source, filename="<bada>"):
    return Parser(tokenize(source, filename)).parse()
