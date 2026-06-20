"""A tiny module loader for Bada: resolves ``#include`` directives.

A line of the form::

    #include path/to/lib.bada

is replaced by the contents of that file (resolved relative to the including
file).  Each file is included at most once, so libraries can include each
other freely.  This is what lets Bada programs be split into reusable
libraries written in Bada itself.
"""

from __future__ import annotations

import os

from .vm import BadaVM
from .compiler import compile_source


def load_program(path: str, _seen: set | None = None) -> str:
    _seen = _seen if _seen is not None else set()
    path = os.path.abspath(path)
    if path in _seen:
        return ""
    _seen.add(path)
    base = os.path.dirname(path)
    out: list[str] = []
    with open(path) as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("#include"):
                inc = stripped[len("#include"):].strip().strip('"<>')
                out.append(load_program(os.path.join(base, inc), _seen))
            else:
                out.append(line.rstrip("\n"))
    return "\n".join(out)


def run_program(path: str) -> BadaVM:
    return BadaVM(compile_source(load_program(path))).run()
