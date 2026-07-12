"""Bootstrap: run the Reviser and language metadata that are written in Bada.

This is the self-hosting seed — the rewrite logic and the command manifest are
produced by Bada programs (``reviser.bada`` / ``commands.bada`` /
``lang.bada``), and Python merely tokenises and reserialises around them.
"""

from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stdout

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)                 # bada_silent_vim
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from bada import load_program, run_source, run_program   # noqa: E402
from bada.lexer import tokenize                           # noqa: E402

REVISER = os.path.join(_HERE, "reviser.bada")
COMMANDS = os.path.join(_HERE, "commands.bada")
LANG = os.path.join(_HERE, "lang.bada")


def _bada_str_array(values) -> str:
    def esc(v):
        return v.replace("\\", "\\\\").replace('"', '\\"')
    return "[" + ", ".join(f'"{esc(v)}"' for v in values) + "]"


def bada_revise_tokens(values: list[str]) -> list[str]:
    """Revise a list of token strings using the Bada reviser."""
    if not values:
        return []
    src = (load_program(REVISER) + "\n"
           + f'print revise_join({_bada_str_array(values)}, " ")\n')
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(src)
    out = buf.getvalue().splitlines()
    return out[-1].split(" ") if out and out[-1] else []


def bada_revise_source(src: str) -> str:
    """Tokenise classic Bada, revise the tokens with the Bada reviser, and
    re-serialise (string-literal-free programs round-trip cleanly)."""
    values = [t.value for t in tokenize(src) if t.kind != "EOF"]
    return " ".join(bada_revise_tokens(values))


def command_manifest() -> list[str]:
    """The method-command manifest, produced by Bada (commands.bada)."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_program(COMMANDS)
    return [line for line in buf.getvalue().splitlines() if line]


__all__ = ["bada_revise_tokens", "bada_revise_source", "command_manifest",
           "REVISER", "COMMANDS", "LANG"]
