"""Bridge to the Beta-function algorithms written in Bada (apps/beta/lib)."""

from __future__ import annotations

import ast
import io
import os
import sys
from contextlib import redirect_stdout

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_PKG)
for p in (_ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from bada import load_program, run_source           # noqa: E402

_LIB = os.path.join(_PKG, "apps", "beta", "lib", "betalib.bada")


def _run(extra: str):
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(load_program(_LIB) + "\n" + extra)
    return buf.getvalue().splitlines()


def beta(p: int, q: int) -> float:
    return float(_run(f"print beta({p}, {q})")[-1])


def pascal_holds(p: int, q: int) -> bool:
    lhs = float(_run(f"print pascal_lhs({p}, {q})")[-1])
    rhs = float(_run(f"print pascal_rhs({p}, {q})")[-1])
    return abs(lhs - rhs) < 1e-9


def zeta2_from_beta() -> float:
    return float(_run("print zeta2_from_beta()")[-1])


def zeta3(N: int = 20000) -> float:
    return float(_run(f"print zeta3({N})")[-1])


def adapt_x_for_zeta(zval: float) -> float:
    return float(_run(f"print adapt_x_for_zeta({zval})")[-1])


def fln(x: float) -> float:
    return float(_run(f"print fln({x})")[-1])


def generate_relations() -> list:
    return ast.literal_eval(_run("print generate_relations()")[-1])
