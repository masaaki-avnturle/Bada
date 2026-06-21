"""Drive the vim editor written in Bada (vimbada/lib/vim.bada).

Bada has no interactive terminal IO, so the editor *logic* lives in Bada and is
driven by a keystroke script; an interactive front-end (curses) is the existing
Python BadaVim editor.  This bridge runs a key script through the Bada vim and
returns the resulting buffer / mode / last command.
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)                 # bada_silent_vim
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from bada import load_program, run_source       # noqa: E402

_VIM = os.path.join(_HERE, "lib", "vim.bada")
_SRC = None

# special multi-char key tokens the Bada vim understands
SPECIAL = {"ESC", "RET", "BS", "dd", ":w", ":q", ":wq", "$"}


def _esc(tok: str) -> str:
    return tok.replace("\\", "\\\\").replace('"', '\\"')


def _arr(keys) -> str:
    return "[" + ", ".join(f'"{_esc(k)}"' for k in keys) + "]"


def run(keys: list[str]) -> dict:
    """Feed a list of key tokens to the Bada vim; return text/mode/lastcmd."""
    global _SRC
    if _SRC is None:
        _SRC = load_program(_VIM)
    src = (_SRC + "\ns <- vim_new()\n"
           f"vim_feed(s, {_arr(keys)})\n"
           "Omega::DATABASE[vim] {\n"
           "  push(vim_text(s))\n  push(vim_mode(s))\n"
           "  push(vim_lastcmd(s))\n}\n")
    vm = run_source(src)
    text, mode, lastcmd = vm.tuplespace["vim"]
    return {"text": text, "mode": mode, "lastcmd": lastcmd}


def type_text(text: str) -> dict:
    """Convenience: enter insert mode, type `text` (with newlines), escape."""
    keys = ["i"]
    for ch in text:
        keys.append("RET" if ch == "\n" else ch)
    keys.append("ESC")
    return run(keys)
