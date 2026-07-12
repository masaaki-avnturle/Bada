"""Reserved words, builtins and operators of the Bada language — one source of
truth for tooling (grammar checker, completion, editor parsers)."""

from __future__ import annotations

from .lexer import KEYWORDS, OPERATORS
from .compiler import BUILTINS

# reserved keywords (control flow, literals, tuplespace, def/return)
RESERVED = sorted(KEYWORDS)

# builtin functions callable from any program
BUILTIN_FUNCS = sorted(BUILTINS)

# directive / manifold operators with their meanings (instruction-oriented)
DIRECTIVES = {
    "<-": "assignment object",
    "<->": "comparison object (==)",
    "-<": "branch object / manifold spawn",
    "->": "transition object (while)",
    ">-": "merge object / quantum emit",
    "=>": "map / transform",
    ">>": "stream forward",
    "::": "namespace (Omega::DATABASE)",
}

# "functional words" = keywords + builtins (the 機能語 of the language)
FUNCTIONAL_WORDS = sorted(set(RESERVED) | set(BUILTIN_FUNCS))


def is_reserved(word: str) -> bool:
    return word in KEYWORDS


def is_builtin(word: str) -> bool:
    return word in BUILTINS


def is_functional(word: str) -> bool:
    return is_reserved(word) or is_builtin(word)


def describe_operator(op: str) -> str | None:
    return DIRECTIVES.get(op)
