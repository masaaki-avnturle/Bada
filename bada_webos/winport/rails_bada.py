"""Bridge to the Bada Rails generator (apps/winport/lib/rails.bada)."""

from __future__ import annotations

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

from bada import load_program, run_source       # noqa: E402

_LIB = os.path.join(_PKG, "apps", "winport", "lib", "rails.bada")


def generate_rails(name: str, fields: list[str]) -> str:
    flit = "[" + ", ".join(f'"{f}"' for f in fields) + "]"
    src = load_program(_LIB) + f'\nsay rails_scaffold("{name}", {flit})\n'
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(src)
    return buf.getvalue()
