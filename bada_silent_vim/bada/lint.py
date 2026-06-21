"""Bada grammar / syntax checker.

Runs the real toolchain (tokenize -> parse -> compile) and turns any failure
into a structured :class:`Diagnostic` with a line/column, so editors can show
errors inline.  ``is_valid`` is a quick boolean check.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .lexer import tokenize, LexError
from .parser import parse, ParseError
from .compiler import compile_source, CompileError


@dataclass
class Diagnostic:
    line: int
    col: int
    severity: str        # "error"
    message: str

    def __str__(self) -> str:
        return f"{self.line}:{self.col}: {self.severity}: {self.message}"


def _pos(msg: str) -> tuple[int, int]:
    line = int(m.group(1)) if (m := re.search(r"line (\d+)", msg)) else 0
    col = int(m.group(1)) if (m := re.search(r"col (\d+)", msg)) else 0
    return line, col


def lint(src: str) -> list[Diagnostic]:
    """Return a list of diagnostics (empty if the program is well-formed)."""
    try:
        tokenize(src)
    except LexError as e:
        line, col = _pos(str(e))
        return [Diagnostic(line, col, "error", str(e))]

    try:
        parse(src)
    except ParseError as e:
        line, col = _pos(str(e))
        return [Diagnostic(line, col, "error", str(e))]

    try:
        compile_source(src)
    except CompileError as e:
        return [Diagnostic(0, 0, "error", str(e))]

    return []


def is_valid(src: str) -> bool:
    return not lint(src)
