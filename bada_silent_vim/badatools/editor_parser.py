"""Emacs and vim parsers for editing Bada, plus a buffer-aware tools layer
(grammar check + word/functional-word completion).

The parsers turn editor input (vim modal keystrokes / emacs chords) into a
normalized command stream shared with the silent-talk parser, so either input
source drives an editor identically.

Normalized commands (tuples):
    ("mode", "INSERT"|"NORMAL")  ("move", DIR)  ("open",)  ("delete",)
    ("kill",) ("yank",) ("save",) ("quit",) ("run",) ("text", str)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bada import Completer, lint, prefix_at        # noqa: E402


# ---------------------------------------------------------------------------
# vim
# ---------------------------------------------------------------------------
class VimParser:
    NORMAL = {
        "h": ("move", "LEFT"), "j": ("move", "DOWN"),
        "k": ("move", "UP"), "l": ("move", "RIGHT"),
        "i": ("mode", "INSERT"), "a": ("mode", "INSERT"),
        "o": ("open",), "x": ("delete",), "!": ("run",),
    }

    def parse(self, keys: list[str]) -> list[tuple]:
        mode = "NORMAL"
        out: list[tuple] = []
        for k in keys:
            if mode == "NORMAL":
                if k in (":w", "w"):
                    out.append(("save",))
                elif k in (":q", "q"):
                    out.append(("quit",))
                elif k in (":wq", "wq", ":x"):
                    out.extend([("save",), ("quit",)])
                elif k == "ESC":
                    pass
                elif k in self.NORMAL:
                    cmd = self.NORMAL[k]
                    out.append(cmd)
                    if cmd == ("mode", "INSERT"):
                        mode = "INSERT"
            else:  # INSERT
                if k == "ESC":
                    out.append(("mode", "NORMAL"))
                    mode = "NORMAL"
                elif k == "RET":
                    out.append(("text", "\n"))
                else:
                    out.append(("text", k))
        return out


# ---------------------------------------------------------------------------
# emacs
# ---------------------------------------------------------------------------
class EmacsParser:
    CHORDS = {
        "C-f": ("move", "RIGHT"), "C-b": ("move", "LEFT"),
        "C-n": ("move", "DOWN"), "C-p": ("move", "UP"),
        "C-a": ("move", "BOL"), "C-e": ("move", "EOL"),
        "C-d": ("delete",), "C-k": ("kill",), "C-y": ("yank",),
        "C-x C-s": ("save",), "C-x C-c": ("quit",), "RET": ("text", "\n"),
    }

    def parse(self, chords: list[str]) -> list[tuple]:
        out: list[tuple] = []
        for c in chords:
            out.append(self.CHORDS.get(c, ("text", c)))
        return out


# ---------------------------------------------------------------------------
# buffer-aware Bada tools shared by both editors
# ---------------------------------------------------------------------------
class BadaEditorTools:
    def __init__(self):
        self.completer = Completer()

    def lint(self, lines: list[str]):
        return lint("\n".join(lines))

    def is_valid(self, lines: list[str]) -> bool:
        return not self.lint(lines)

    def complete(self, lines: list[str], cy: int, cx: int,
                 kind: str = "all") -> tuple:
        src = "\n".join(lines)
        line = lines[cy] if 0 <= cy < len(lines) else ""
        pre = prefix_at(line, cx)
        return self.completer.complete(src, pre, kind), pre
