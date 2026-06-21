"""Bridge to the 'Integrate of theorem' transport engine written in Bada
(apps/transport/lib/transport.bada): the binomial equation generator and the
report's manifolds (Seifert, Kaluza-Klein, critical line, AM-GM, binomial)."""

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

_LIB = os.path.join(_PKG, "apps", "transport", "lib", "transport.bada")
_SRC = None


def _run(extra: str):
    global _SRC
    if _SRC is None:
        _SRC = load_program(_LIB)
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(_SRC + "\n" + extra)
    return buf.getvalue().splitlines()


# -- the binomial equation generator ----------------------------------------
def binom(n: int, r: int) -> float:
    return float(_run(f"print binom({n}, {r})")[-1])


def series_binom(n: int, f: float) -> float:
    return float(_run(f"print series_binom({n}, {f})")[-1])


def series_alt(n: int, f: float) -> float:
    return float(_run(f"print series_alt({n}, {f})")[-1])


def generate_P(s: int, n: int, f: float, N: int = 1000) -> float:
    return float(_run(f"print generate_P({s}, {n}, {f}, {N})")[-1])


def flow_in(s: int, n: int, N: int = 1000, flo: float = 0.0, fhi: float = 1.0,
            steps: int = 1000) -> list:
    return ast.literal_eval(
        _run(f"print flow_in({s}, {n}, {N}, {flo}, {fhi}, {steps})")[-1])


def amgm_gap(a: float, b: float) -> float:
    return float(_run(f"print amgm_gap({a}, {b})")[-1])


# -- manifolds for the video dictionary -------------------------------------
def names() -> list:
    s = _run("print catalog_names()")[-1].strip().lstrip("[").rstrip("]")
    return [x.strip() for x in s.split(",") if x.strip()]


def frames(name: str, n: int = 16, T: int = 20) -> list:
    out = []
    for k in range(T):
        t = k / T
        flat = ast.literal_eval(_run(f'print frame_flat("{name}", {n}, {t})')[-1])
        out.append([flat[r * n:(r + 1) * n] for r in range(n)])
    return out


def displacement(name: str, T: int = 20) -> float:
    return float(_run(f'print displacement("{name}", {T})')[-1])
