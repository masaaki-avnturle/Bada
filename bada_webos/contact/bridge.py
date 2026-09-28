"""Bridge to the Contact blueprint generator written in Bada
(apps/contact/contact_app.bada + apps/contact/lib/contact.bada)."""

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

from bada import load_program, run_source           # noqa: E402

APP = os.path.join(_PKG, "apps", "contact", "contact_app.bada")
LIB = os.path.join(_PKG, "apps", "contact", "lib", "contact.bada")

_LIB_SRC = None


def run_app() -> str:
    """Run contact_app.bada on the Bada VM and return its stdout."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(load_program(APP))
    return buf.getvalue()


def call(expr: str) -> str:
    """Evaluate one Bada expression against the library; return printed text."""
    global _LIB_SRC
    if _LIB_SRC is None:
        _LIB_SRC = load_program(LIB)
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(_LIB_SRC + "\nprint " + expr)
    return buf.getvalue().strip().splitlines()[-1]


def num(expr: str) -> float:
    return float(call(expr))


def split_output(text: str) -> tuple[str, str]:
    """Split the app output into (report, obj)."""
    head, _, rest = text.partition("---- BEGIN OBJ ----\n")
    obj, _, _ = rest.partition("---- END OBJ ----")
    return head.rstrip() + "\n", obj.strip() + "\n"


def parse_obj(obj: str) -> list[dict]:
    """Parse the generated OBJ into parts: [{name, vertices, edges}]."""
    parts: list[dict] = []
    verts: list[list[float]] = []
    for line in obj.splitlines():
        tok = line.split()
        if not tok or tok[0].startswith("#"):
            continue
        if tok[0] == "o":
            parts.append({"name": tok[1], "base": len(verts),
                          "vertices": [], "edges": []})
        elif tok[0] == "v":
            v = [float(t) for t in tok[1:4]]
            verts.append(v)
            parts[-1]["vertices"].append(v)
        elif tok[0] == "l":
            a, b = int(tok[1]) - 1, int(tok[2]) - 1
            parts[-1]["edges"].append([a - parts[-1]["base"],
                                       b - parts[-1]["base"]])
    for p in parts:
        del p["base"]
    return parts
