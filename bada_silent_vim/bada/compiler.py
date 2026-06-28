"""Bada compiler: AST -> BadaVM bytecode.

Bytecode is a flat list of ``(op, *args)`` tuples executed by
:class:`bada.vm.BadaVM`.  Control flow uses absolute instruction indices, so
the compiler patches forward jumps after emitting their bodies.
"""

from __future__ import annotations

from .parser import parse


class CompileError(Exception):
    pass


# builtin functions implemented directly by the VM
BUILTINS = {"len", "append", "idiv", "imod", "abs", "str", "pow2"}


class Compiler:
    def __init__(self):
        self.code: list[tuple] = []
        self._rep = 0          # counter for unique repeat-loop variables
        self.func_names: set = set()

    # -- emit helpers ------------------------------------------------------
    def emit(self, *instr) -> int:
        self.code.append(instr)
        return len(self.code) - 1

    def patch(self, idx: int, target: int):
        op = self.code[idx]
        self.code[idx] = (op[0], target)

    # -- program -----------------------------------------------------------
    def compile_program(self, stmts: list) -> list[tuple]:
        defs = [s for s in stmts if s[0] == "def"]
        body = [s for s in stmts if s[0] != "def"]
        self.func_names = {d[1] for d in defs}

        for s in body:
            self.stmt(s)
        self.emit("HALT")

        # function bodies live after HALT; reached only via CALL.  Each is
        # preceded by a FUNC marker the VM scans to build its dispatch table.
        for _, name, params, fbody in defs:
            self.emit("FUNC", name, params)     # entry = this index + 1
            for s in fbody:
                self.stmt(s)
            self.emit("CONST", None)            # default return value
            self.emit("RET")
        return self.code

    # -- statements --------------------------------------------------------
    def stmt(self, node):
        tag = node[0]
        if tag == "assign":
            _, name, e = node
            self.expr(e)
            self.emit("STORE", name)
        elif tag == "print":
            _, kind, e = node
            self.expr(e)
            self.emit("SAY" if kind == "say" else "PRINT")
        elif tag == "exprstmt":
            self.expr(node[1])
            self.emit("POP")
        elif tag == "tuplespace":
            self.tuplespace(node)
        elif tag == "if":
            self.if_stmt(node)
        elif tag == "while":
            self.while_stmt(node)
        elif tag == "repeat":
            self.repeat_stmt(node)
        elif tag == "return":
            if node[1] is None:
                self.emit("CONST", None)
            else:
                self.expr(node[1])
            self.emit("RET")
        elif tag == "setindex":
            _, base, idx, val = node
            self.expr(base)
            self.expr(idx)
            self.expr(val)
            self.emit("SETINDEX")
        else:
            raise CompileError(f"unknown statement {tag!r}")

    def tuplespace(self, node):
        _, space, ops = node
        for op in ops:
            if op[0] == "push":
                self.expr(op[1])
                self.emit("TPUSH", space)
            else:  # pop
                self.emit("TPOP", space)
                self.emit("POP")  # discard popped value at statement level

    def if_stmt(self, node):
        _, cond, then_block, else_block = node
        self.expr(cond)
        jfalse = self.emit("JFALSE", -1)
        for s in then_block:
            self.stmt(s)
        if else_block is not None:
            jend = self.emit("JMP", -1)
            self.patch(jfalse, len(self.code))
            for s in else_block:
                self.stmt(s)
            self.patch(jend, len(self.code))
        else:
            self.patch(jfalse, len(self.code))

    def while_stmt(self, node):
        _, cond, body = node
        start = len(self.code)
        self.expr(cond)
        jfalse = self.emit("JFALSE", -1)
        for s in body:
            self.stmt(s)
        self.emit("JMP", start)
        self.patch(jfalse, len(self.code))

    def repeat_stmt(self, node):
        _, count, body = node
        var = f"__rep{self._rep}"
        self._rep += 1
        self.expr(count)
        self.emit("STORE", var)
        start = len(self.code)
        self.emit("LOAD", var)
        self.emit("CONST", 0)
        self.emit("BIN", ">")
        jfalse = self.emit("JFALSE", -1)
        for s in body:
            self.stmt(s)
        self.emit("LOAD", var)
        self.emit("CONST", 1)
        self.emit("BIN", "-")
        self.emit("STORE", var)
        self.emit("JMP", start)
        self.patch(jfalse, len(self.code))

    # -- expressions -------------------------------------------------------
    def expr(self, node):
        tag = node[0]
        if tag == "num":
            self.emit("CONST", node[1])
        elif tag == "str":
            self.emit("CONST", node[1])
        elif tag == "bool":
            self.emit("CONST", node[1])
        elif tag == "nil":
            self.emit("CONST", None)
        elif tag == "var":
            self.emit("LOAD", node[1])
        elif tag == "neg":
            self.expr(node[1])
            self.emit("NEG")
        elif tag == "bin":
            _, op, l, r = node
            self.expr(l)
            self.expr(r)
            self.emit("BIN", op)
        elif tag == "array":
            for e in node[1]:
                self.expr(e)
            self.emit("ARRAY", len(node[1]))
        elif tag == "index":
            _, base, idx = node
            self.expr(base)
            self.expr(idx)
            self.emit("INDEX")
        elif tag == "call":
            _, name, args = node
            for a in args:
                self.expr(a)
            if name in BUILTINS:
                self.emit("CALLB", name, len(args))
            elif name in self.func_names:
                self.emit("CALL", name, len(args))
            else:
                raise CompileError(f"call to unknown function {name!r}")
        else:
            raise CompileError(f"unknown expression {tag!r}")


def compile_source(src: str) -> list[tuple]:
    return Compiler().compile_program(parse(src))


def disassemble(code: list[tuple]) -> str:
    lines = []
    for i, instr in enumerate(code):
        args = " ".join(repr(a) for a in instr[1:])
        lines.append(f"{i:4d}  {instr[0]:<8} {args}")
    return "\n".join(lines)
