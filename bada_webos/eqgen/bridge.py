"""Bridge to the equation-generator engine written in Bada (apps/eqgen/lib)."""

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

_LIB = os.path.join(_PKG, "apps", "eqgen", "lib", "eqgen.bada")


def _arr(xs):
    return "[" + ", ".join(str(x) for x in xs) + "]"


def _run(extra: str):
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(load_program(_LIB) + "\n" + extra)
    return buf.getvalue().splitlines()


def power_series(a: list, f: float) -> float:
    return float(_run(f"print power_series({_arr(a)}, {f})")[-1])


def o_from_zeta(zval: float, a: list, f: float) -> float:
    return float(_run(f"print o_from_zeta({zval}, {_arr(a)}, {f})")[-1])


def zeta_from_series(o: float, a: list, f: float) -> float:
    return float(_run(f"print zeta_from_series({o}, {_arr(a)}, {f})")[-1])


def flow_in(zval: float, a: list, flo: float, fhi: float, steps: int,
            target: float) -> list:
    return ast.literal_eval(_run(
        f"print flow_in({zval}, {_arr(a)}, {flo}, {fhi}, {steps}, "
        f"{target})")[-1])


def generate_equations(zval: float, a: list, fs: list) -> list:
    return ast.literal_eval(_run(
        f"print generate_equations({zval}, {_arr(a)}, {_arr(fs)})")[-1])


def euler_cf(b0: float, c: list, b: list) -> float:
    return float(_run(f"print euler_cf({b0}, {_arr(c)}, {_arr(b)})")[-1])
