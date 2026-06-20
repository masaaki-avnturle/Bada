"""The Bada language: lexer, parser, compiler and VM interpreter.

Bada is the operator-algebra / TupleSpace language described in Bada1.pdf.
This package gives it a working toolchain::

    from bada import run_source, compile_source, disassemble

The pipeline is  source -> tokenize -> parse -> compile (bytecode) -> BadaVM.
"""

from .lexer import tokenize
from .parser import parse
from .compiler import compile_source, disassemble
from .vm import BadaVM, run_source, to_text
from .loader import load_program, run_program

__all__ = [
    "tokenize", "parse", "compile_source", "disassemble",
    "BadaVM", "run_source", "to_text",
    "load_program", "run_program",
]
