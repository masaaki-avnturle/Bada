"""Bridge to the extra report surfaces written in Bada
(apps/slideshow/lib/reports.bada)."""

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

_LIB = os.path.join(_PKG, "apps", "slideshow", "lib", "reports.bada")
_SRC = None


def _run(extra: str):
    global _SRC
    if _SRC is None:
        _SRC = load_program(_LIB)
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(_SRC + "\n" + extra)
    return buf.getvalue().splitlines()


def names() -> list:
    s = _run("print catalog_names()")[-1].strip().lstrip("[").rstrip("]")
    return [x.strip() for x in s.split(",") if x.strip()]


def frames(name: str, n: int = 16, T: int = 20) -> list:
    out = []
    for k in range(T):
        flat = ast.literal_eval(
            _run(f'print frame_flat("{name}", {n}, {k / T})')[-1])
        out.append([flat[r * n:(r + 1) * n] for r in range(n)])
    return out
