"""Recursive-descent parser for the Bada language.

Produces a small AST of tuples consumed by :mod:`bada.compiler`.

Grammar (informal)::

    program    := stmt*
    stmt       := assign | print | tuplespace | if | while | repeat | exprstmt
    assign     := IDENT ('<-' | '=') expr
    print      := ('print' | 'say') expr
    tuplespace := 'Omega' '::' 'DATABASE' '[' IDENT ']' '{' tstmt* '}'
    tstmt      := 'push' '(' expr ')' | 'pop' '(' ')'
    if         := 'if' expr block ('else' block)?
    while      := 'while' expr block
    repeat     := 'repeat' expr block
    block      := '{' stmt* '}'
    expr       := pipe
    pipe       := compare (('>>' | '=>' | '>-' | '-<') compare)*
    compare    := add (('==' | '!=' | '<' | '>' | '<=' | '>=') add)*
    add        := mul (('+' | '-') mul)*
    mul        := unary (('*' | '/' | '%') unary)*
    unary      := '-'? primary
    primary    := NUMBER | STRING | IDENT | bool | nil
                | '[' (expr (',' expr)*)? ']' | '(' expr ')'
"""

from __future__ import annotations

from .lexer import Token, tokenize


class ParseError(SyntaxError):
    pass


PIPE_OPS = {">>", "=>", ">-", "-<"}
CMP_OPS = {"==", "!=", "<", ">", "<=", ">="}


class Parser:
    def __init__(self, toks: list[Token]):
        self.toks = toks
        self.pos = 0

    # -- token helpers -----------------------------------------------------
    @property
    def cur(self) -> Token:
        return self.toks[self.pos]

    def at(self, kind: str, value: str | None = None) -> bool:
        t = self.cur
        return t.kind == kind and (value is None or t.value == value)

    def eat(self, kind: str, value: str | None = None) -> Token:
        t = self.cur
        if t.kind != kind or (value is not None and t.value != value):
            want = value if value is not None else kind
            raise ParseError(
                f"expected {want!r} but found {t.value!r} at line {t.line}")
        self.pos += 1
        return t

    def accept(self, kind: str, value: str | None = None) -> Token | None:
        if self.at(kind, value):
            return self.eat(kind, value)
        return None

    # -- entry -------------------------------------------------------------
    def parse(self) -> list:
        stmts = []
        while not self.at("EOF"):
            stmts.append(self.statement())
        return stmts

    # -- statements --------------------------------------------------------
    def statement(self):
        t = self.cur

        if t.kind == "KW" and t.value in ("print", "say"):
            self.eat("KW")
            e = self.expr()
            self.accept("OP", ";")
            return ("print", t.value, e)

        if t.kind == "KW" and t.value == "Omega":
            return self.tuplespace()

        if t.kind == "KW" and t.value == "if":
            return self.if_stmt()

        if t.kind == "KW" and t.value == "while":
            self.eat("KW")
            cond = self.expr()
            body = self.block()
            return ("while", cond, body)

        if t.kind == "KW" and t.value == "repeat":
            self.eat("KW")
            count = self.expr()
            body = self.block()
            return ("repeat", count, body)

        # assignment: IDENT ('<-' | '=') expr   (lookahead)
        if t.kind == "IDENT":
            nxt = self.toks[self.pos + 1]
            if nxt.kind == "OP" and nxt.value in ("<-", "="):
                name = self.eat("IDENT").value
                self.eat("OP")  # <- or =
                e = self.expr()
                self.accept("OP", ";")
                return ("assign", name, e)

        e = self.expr()
        self.accept("OP", ";")
        return ("exprstmt", e)

    def tuplespace(self):
        self.eat("KW", "Omega")
        self.eat("OP", "::")
        self.eat("IDENT", "DATABASE")
        self.eat("OP", "[")
        name = self.eat("IDENT").value
        self.eat("OP", "]")
        self.eat("OP", "{")
        ops = []
        while not self.at("OP", "}"):
            if self.at("KW", "push"):
                self.eat("KW")
                self.eat("OP", "(")
                e = self.expr()
                self.eat("OP", ")")
                self.accept("OP", ";")
                ops.append(("push", e))
            elif self.at("KW", "pop"):
                self.eat("KW")
                self.eat("OP", "(")
                self.eat("OP", ")")
                self.accept("OP", ";")
                ops.append(("pop",))
            else:
                raise ParseError(
                    f"only push/pop allowed in tuplespace, "
                    f"found {self.cur.value!r} at line {self.cur.line}")
        self.eat("OP", "}")
        return ("tuplespace", name, ops)

    def if_stmt(self):
        self.eat("KW", "if")
        cond = self.expr()
        then_block = self.block()
        else_block = None
        if self.accept("KW", "else"):
            else_block = self.block()
        return ("if", cond, then_block, else_block)

    def block(self):
        self.eat("OP", "{")
        stmts = []
        while not self.at("OP", "}"):
            stmts.append(self.statement())
        self.eat("OP", "}")
        return stmts

    # -- expressions -------------------------------------------------------
    def expr(self):
        return self.pipe()

    def pipe(self):
        node = self.compare()
        while self.cur.kind == "OP" and self.cur.value in PIPE_OPS:
            op = self.eat("OP").value
            rhs = self.compare()
            node = ("bin", op, node, rhs)
        return node

    def compare(self):
        node = self.add()
        while self.cur.kind == "OP" and self.cur.value in CMP_OPS:
            op = self.eat("OP").value
            rhs = self.add()
            node = ("bin", op, node, rhs)
        return node

    def add(self):
        node = self.mul()
        while self.cur.kind == "OP" and self.cur.value in ("+", "-"):
            op = self.eat("OP").value
            rhs = self.mul()
            node = ("bin", op, node, rhs)
        return node

    def mul(self):
        node = self.unary()
        while self.cur.kind == "OP" and self.cur.value in ("*", "/", "%"):
            op = self.eat("OP").value
            rhs = self.unary()
            node = ("bin", op, node, rhs)
        return node

    def unary(self):
        if self.at("OP", "-"):
            self.eat("OP")
            return ("neg", self.unary())
        return self.primary()

    def primary(self):
        t = self.cur
        if t.kind == "NUMBER":
            self.eat("NUMBER")
            val = float(t.value) if "." in t.value else int(t.value)
            return ("num", val)
        if t.kind == "STRING":
            self.eat("STRING")
            return ("str", t.value)
        if t.kind == "KW" and t.value in ("true", "false"):
            self.eat("KW")
            return ("bool", t.value == "true")
        if t.kind == "KW" and t.value == "nil":
            self.eat("KW")
            return ("nil",)
        if t.kind == "IDENT":
            self.eat("IDENT")
            return ("var", t.value)
        if self.at("OP", "["):
            self.eat("OP", "[")
            elems = []
            if not self.at("OP", "]"):
                elems.append(self.expr())
                while self.accept("OP", ","):
                    elems.append(self.expr())
            self.eat("OP", "]")
            return ("array", elems)
        if self.at("OP", "("):
            self.eat("OP", "(")
            e = self.expr()
            self.eat("OP", ")")
            return e
        raise ParseError(
            f"unexpected token {t.value!r} ({t.kind}) at line {t.line}")


def parse(src: str) -> list:
    return Parser(tokenize(src)).parse()
