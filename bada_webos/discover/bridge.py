"""Bridge to the discovery apps written in Bada (apps/discover/lib).

Runs the Bada libraries on the VM and returns their results to Python, so the
HPsi pattern finder, the odd-zeta regularity, and the Monster-denominator
a-priori engine are reachable from the terminal and the tests.
"""

from __future__ import annotations

import ast
import io
import os
import sys
from contextlib import redirect_stdout

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)                       # bada_webos/
_ROOT = os.path.dirname(_PKG)
for p in (_ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from bada import load_program, run_source           # noqa: E402

_LIB = os.path.join(_PKG, "apps", "discover", "lib")
APPS = os.path.join(_PKG, "apps", "discover")


def _run(libfile: str, extra: str) -> list[str]:
    src = load_program(os.path.join(_LIB, libfile)) + "\n" + extra
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(src)
    return buf.getvalue().splitlines()


def _val(out):
    return ast.literal_eval(out[-1])


# -- HPsi operator pattern finder -------------------------------------------
def hpsi_period() -> int:
    return int(_run("hpsi.bada", "print detect_period()")[-1])


def hpsi_eigen(x: float, M: int) -> list:
    return _val(_run("hpsi.bada", f"print find_real_eigen({x}, {M})"))


def hpsi_growth(x: float, L: int) -> float:
    return float(_run("hpsi.bada", f"print growth_ratio({x}, {L})")[-1])


# -- odd zeta regularity ----------------------------------------------------
def zeta(s: int, N: int = 2000) -> float:
    return float(_run("zeta.bada", f"print zeta({s}, {N})")[-1])


def odd_ratios(N: int = 2000) -> list:
    return _val(_run("zeta.bada", f"print odd_ratios({N})"))


# -- moonshine a-priori engine ----------------------------------------------
def gamma(K: int = 20, N: int = 1500) -> float:
    return float(_run("moonshine.bada", f"print gamma_via_zeta({K}, {N})")[-1])


def monster_denoms(N: int = 1500, maxmult: int = 120) -> list:
    return _val(_run("moonshine.bada",
                     f"print numerator_seq({N}, {maxmult})"))
