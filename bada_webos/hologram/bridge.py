"""Bridge to the hologram light-field library written in Bada
(apps/hologram/lib/hologram.bada).

Returns, to Python, the complex hologram light field (reality / imaginary
surfaces and magnitude) and the four-mirror reflection geometry from the
"Hologram Display" report.
"""

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

_LIB = os.path.join(_PKG, "apps", "hologram", "lib", "hologram.bada")
_SRC = None


def _run(extra: str):
    global _SRC
    if _SRC is None:
        _SRC = load_program(_LIB)
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(_SRC + "\n" + extra)
    return buf.getvalue().splitlines()


def quad_names() -> list:
    # Bada prints string arrays unquoted: "[before, after, left, right]"
    s = _run("print quad_names()")[-1].strip().lstrip("[").rstrip("]")
    return [x.strip() for x in s.split(",") if x.strip()]


def quad_rot(name: str) -> int:
    return int(float(_run(f'print quad_rot("{name}")')[-1]))


def light_grid(kind: str, n: int, t: float) -> list:
    """One n x n grid of the light field ('re' | 'im' | 'mag') at time t."""
    flat = ast.literal_eval(_run(f'print light_flat("{kind}", {n}, {t})')[-1])
    return [flat[r * n:(r + 1) * n] for r in range(n)]


def light_frames(kind: str, n: int = 16, T: int = 16) -> list:
    """T animation frames of the light field, each an n x n grid (in Bada)."""
    return [light_grid(kind, n, k / T) for k in range(T)]


def metric_ds2(v: float, c: float) -> float:
    return float(_run(f"print metric_ds2({v}, {c})")[-1])


def hologram_mass(p: float, c: float, V: float, S: float) -> float:
    return float(_run(f"print hologram_mass({p}, {c}, {V}, {S})")[-1])
