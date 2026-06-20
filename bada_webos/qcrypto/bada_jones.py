"""Bridge to the Bada-language Jones library.

Runs ``apps/lib/jones.bada`` (the Jones polynomial implemented in Bada) for an
arbitrary braid and returns the result to Python — so the same computation is
reachable from the terminal (``qcrypto badajones``) and is cross-checked
against the reference implementation in tests.
"""

from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stdout

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)                 # bada_webos/
_ROOT = os.path.dirname(_PKG)                 # repo root
for p in (_ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from bada import load_program, run_source     # noqa: E402

_LIB = os.path.join(_PKG, "apps", "lib", "jones.bada")


def _braid_literal(braid: list[int]) -> str:
    return "[" + ", ".join(str(g) for g in braid) + "]"


def _run(extra: str) -> list[str]:
    src = load_program(_LIB) + "\n" + extra
    buf = io.StringIO()
    with redirect_stdout(buf):
        vm = run_source(src)
    return vm.output


def bada_jones_show(braid: list[int]) -> str:
    """V(t) as a string, computed by the Bada library."""
    out = _run(f"braid <- {_braid_literal(braid)}\n"
               f"print jones_show(braid, nstrands(braid))\n")
    return out[-1].strip()


def bada_bracket(braid: list[int]) -> dict:
    """Kauffman bracket <L> as {A-exponent: coeff}, computed by Bada."""
    out = _run(
        f"braid <- {_braid_literal(braid)}\n"
        "b <- lt_sort(kauffman(braid, nstrands(braid)))\n"
        "i <- 0\n"
        'while i < len(b) { print b[i][0] + ":" + b[i][1]  i <- i + 1 }\n')
    result = {}
    for line in out:
        e, _, c = line.partition(":")
        result[int(e)] = int(c)
    return result
