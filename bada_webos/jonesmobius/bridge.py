"""Bridge to the Jones-Mobius causal analyzer written in Bada."""

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

from bada import load_program, run_source, run_program   # noqa: E402

_MOBIUS = os.path.join(_PKG, "apps", "jonesmobius", "lib", "mobius.bada")
APP = os.path.join(_PKG, "apps", "jonesmobius", "jonesmobius_app.bada")


def _run(extra: str):
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(load_program(_MOBIUS) + "\n" + extra)
    return buf.getvalue().splitlines()


def _arr(M):
    return "[" + ", ".join(str(x) for x in M) + "]"


def mobius_class(M: list) -> int:
    return int(_run(f"print mobius_class({_arr(M)})")[-1])


def mobius_apply(M: list, z: float) -> float:
    return float(_run(f"print mobius_apply({_arr(M)}, {z})")[-1])


def is_involution(M: list) -> bool:
    return _run(f"print mobius_is_involution({_arr(M)})")[-1] == "1"


def causal_graph() -> list:
    """[[src, dst, mobius_class, verified], ...] from the Bada app."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        vm = run_program(APP)
    return vm.tuplespace["causal"][0]
