"""Bada language lexer.

Tokenises Bada source into a flat token stream.  The Bada language is the
operator-algebra language described in the TupleSpace report (Bada1.pdf):
non-commutative left action ``<-``, manifold integral ``-<``, quantum right
action ``>-``, stream forward ``>>`` and the map/transform arrow ``=>``, with
the ``Omega::DATABASE[tuplespace]`` Akashic store.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Token:
    kind: str          # NUMBER, STRING, IDENT, OP, KW, LBRACE, ...
    value: str
    line: int
    col: int

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"Token({self.kind},{self.value!r},{self.line}:{self.col})"


KEYWORDS = {
    "print", "say", "if", "else", "while", "repeat",
    "push", "pop", "true", "false", "nil",
    "Omega",  # part of Omega::DATABASE
}

# Multi-character operators, longest first so the scanner is greedy.
OPERATORS = [
    "::",          # namespace
    "<-", "-<", ">-", ">>", "=>",   # the five Bada manifold operators
    "==", "!=", "<=", ">=",
    "+", "-", "*", "/", "%",
    "<", ">", "=",
    "(", ")", "[", "]", "{", "}",
    ",", ";",
]


class LexError(SyntaxError):
    pass


def tokenize(src: str) -> list[Token]:
    toks: list[Token] = []
    i, line, col = 0, 1, 1
    n = len(src)

    def adv(k: int = 1):
        nonlocal i, col
        i += k
        col += k

    while i < n:
        c = src[i]

        # whitespace
        if c == "\n":
            line += 1
            col = 1
            i += 1
            continue
        if c in " \t\r":
            adv()
            continue

        # line comment //...
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue

        # string literal "..." or '...'
        if c in "\"'":
            quote = c
            start_col = col
            adv()
            buf = []
            while i < n and src[i] != quote:
                if src[i] == "\\" and i + 1 < n:
                    nxt = src[i + 1]
                    buf.append({"n": "\n", "t": "\t", "\\": "\\",
                                quote: quote}.get(nxt, nxt))
                    adv(2)
                else:
                    if src[i] == "\n":
                        line += 1
                        col = 1
                    buf.append(src[i])
                    i += 1
                    col += 1
            if i >= n:
                raise LexError(f"unterminated string at line {line}")
            adv()  # closing quote
            toks.append(Token("STRING", "".join(buf), line, start_col))
            continue

        # number
        if c.isdigit() or (c == "." and i + 1 < n and src[i + 1].isdigit()):
            start_col = col
            j = i
            dot = False
            while j < n and (src[j].isdigit() or (src[j] == "." and not dot)):
                if src[j] == ".":
                    dot = True
                j += 1
            num = src[i:j]
            adv(j - i)
            toks.append(Token("NUMBER", num, line, start_col))
            continue

        # identifier / keyword
        if c.isalpha() or c == "_":
            start_col = col
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            word = src[i:j]
            adv(j - i)
            kind = "KW" if word in KEYWORDS else "IDENT"
            toks.append(Token(kind, word, line, start_col))
            continue

        # operators (greedy longest match)
        matched = False
        for op in OPERATORS:
            if src.startswith(op, i):
                start_col = col
                adv(len(op))
                toks.append(Token("OP", op, line, start_col))
                matched = True
                break
        if matched:
            continue

        raise LexError(f"unexpected character {c!r} at line {line} col {col}")

    toks.append(Token("EOF", "", line, col))
    return toks
