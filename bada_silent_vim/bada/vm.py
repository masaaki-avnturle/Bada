"""BadaVM: the interpreter that executes Bada bytecode.

It is a small stack machine.  The five Bada manifold operators carry the
runtime semantics described in the TupleSpace report:

* ``<-`` non-commutative left action  -> assignment (handled at compile time
  as STORE) / "draw into".
* ``-<`` manifold integral / spawn     -> forms the pair ``[a, b]``.
* ``>-`` quantum right action / emit   -> combine (numbers add, sequences /
  strings concatenate).
* ``>>`` stream forward                -> push ``a`` onto sequence ``b`` (or
  forward ``a`` into the global stream when ``b`` is not a sequence).
* ``=>`` map / transform               -> map ``b`` over the elements of ``a``.

``Omega::DATABASE[space]`` is realised as a global dict-of-lists Akashic store.
"""

from __future__ import annotations

from .compiler import compile_source


class BadaRuntimeError(Exception):
    pass


def truthy(v) -> bool:
    if v is None or v is False:
        return False
    if v == 0 or v == "" or v == []:
        return False
    return True


def to_text(v) -> str:
    if v is True:
        return "true"
    if v is False:
        return "false"
    if v is None:
        return "nil"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, list):
        return "[" + ", ".join(to_text(x) for x in v) + "]"
    return str(v)


class BadaVM:
    def __init__(self, code: list[tuple]):
        self.code = code
        self.stack: list = []
        self.vars: dict = {}
        self.tuplespace: dict[str, list] = {}   # Omega::DATABASE
        self.stream: list = []                   # observable >> flow log
        self.output: list[str] = []              # captured print/say lines

    # -- public ------------------------------------------------------------
    def run(self) -> "BadaVM":
        ip = 0
        code = self.code
        n = len(code)
        while ip < n:
            instr = code[ip]
            op = instr[0]

            if op == "CONST":
                self.stack.append(instr[1])
            elif op == "LOAD":
                name = instr[1]
                if name not in self.vars:
                    raise BadaRuntimeError(f"undefined variable {name!r}")
                self.stack.append(self.vars[name])
            elif op == "STORE":
                self.vars[instr[1]] = self.stack.pop()
            elif op == "POP":
                self.stack.pop()
            elif op == "NEG":
                self.stack.append(-self.stack.pop())
            elif op == "ARRAY":
                count = instr[1]
                items = self.stack[len(self.stack) - count:]
                del self.stack[len(self.stack) - count:]
                self.stack.append(list(items))
            elif op == "PRINT" or op == "SAY":
                v = self.stack.pop()
                line = to_text(v)
                self.output.append(line)
                print(line)
            elif op == "BIN":
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(self._binary(instr[1], a, b))
            elif op == "TPUSH":
                space = instr[1]
                self.tuplespace.setdefault(space, []).append(self.stack.pop())
            elif op == "TPOP":
                space = instr[1]
                lst = self.tuplespace.get(space)
                self.stack.append(lst.pop() if lst else None)
            elif op == "JMP":
                ip = instr[1]
                continue
            elif op == "JFALSE":
                if not truthy(self.stack.pop()):
                    ip = instr[1]
                    continue
            elif op == "HALT":
                break
            else:
                raise BadaRuntimeError(f"bad opcode {op!r}")
            ip += 1
        return self

    # -- operators ---------------------------------------------------------
    def _binary(self, op, a, b):
        if op == "+":
            if isinstance(a, str) or isinstance(b, str):
                return to_text(a) + to_text(b)
            if isinstance(a, list) and isinstance(b, list):
                return a + b
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            if b == 0:
                raise BadaRuntimeError("division by zero")
            return a / b
        if op == "%":
            return a % b
        if op == "==":
            return a == b
        if op == "!=":
            return a != b
        if op == "<":
            return a < b
        if op == ">":
            return a > b
        if op == "<=":
            return a <= b
        if op == ">=":
            return a >= b

        # ---- the four Bada manifold pipe operators ----
        if op == "-<":      # manifold integral / spawn  -> pair
            return [a, b]
        if op == ">-":      # quantum right action / emit -> combine
            if isinstance(a, list) or isinstance(b, list):
                la = a if isinstance(a, list) else [a]
                lb = b if isinstance(b, list) else [b]
                return la + lb
            if isinstance(a, str) or isinstance(b, str):
                return to_text(a) + to_text(b)
            return a + b
        if op == ">>":      # stream forward
            self.stream.append(a)
            if isinstance(b, list):
                return b + [a]
            return b
        if op == "=>":      # map / transform
            if isinstance(a, list):
                return [self._combine(x, b) for x in a]
            return self._combine(a, b)

        raise BadaRuntimeError(f"unknown operator {op!r}")

    @staticmethod
    def _combine(x, y):
        if isinstance(x, str) or isinstance(y, str):
            return to_text(x) + to_text(y)
        return x * y if not isinstance(x, list) else x + [y]


def run_source(src: str) -> BadaVM:
    return BadaVM(compile_source(src)).run()
