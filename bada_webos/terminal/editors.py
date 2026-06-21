"""vim and emacs for the BadaWebOS terminal, both editing VFS files.

``VimSession`` reuses the modal :class:`BadaVim` editor from
``bada_silent_vim/editor`` (NORMAL/INSERT, hjkl, :w :q).  ``EmacsSession`` is a
compact emacs: C-f/C-b/C-n/C-p/C-a/C-e motion, C-d delete, C-k kill-line,
C-y yank, C-x C-s save, C-x C-c exit, and self-inserting text.  Both are
keystroke-scriptable so the terminal can drive them headlessly.
"""

from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _p in (_ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from editor import BadaVim, INSERT, NORMAL          # noqa: E402

from .vfs import VFS


# ---------------------------------------------------------------------------
# vim  (reuses the BadaVim modal editor)
# ---------------------------------------------------------------------------
class VimSession:
    def __init__(self, vfs: VFS, filename: str | None):
        self.vfs = vfs
        self.filename = filename or "noname.txt"
        self.ed = BadaVim(filename=self.filename)
        if filename and vfs.is_file(filename):
            self.ed.lines = vfs.read(filename).split("\n") or [""]
        self.alive = True

    # script: a list of vim keystrokes / ex commands
    def feed(self, steps: list[str]):
        for s in steps:
            self._key(s)
        return self

    def _key(self, s: str):
        ed = self.ed
        if s == ":w":
            self.save()
        elif s == ":q":
            self.alive = False
        elif s == ":wq":
            self.save()
            self.alive = False
        elif s == "ESC":
            ed.apply_command("ESCAPE")
        elif ed.mode == NORMAL and s in ("i", "o", "x", "h", "j", "k", "l"):
            ed.apply_command({"i": "INSERT", "o": "NEWLINE", "x": "DELETE",
                              "h": "LEFT", "j": "DOWN", "k": "UP",
                              "l": "RIGHT"}[s])
        elif ed.mode == INSERT:
            ed.type_text(s)
        # else: ignore unknown normal-mode keys

    def save(self):
        self.vfs.write(self.filename, self.ed.text())

    def text(self) -> str:
        return self.ed.text()

    def status(self) -> str:
        return f'vim "{self.filename}" [{self.ed.mode}] {len(self.ed.lines)}L'


# ---------------------------------------------------------------------------
# emacs
# ---------------------------------------------------------------------------
class EmacsSession:
    def __init__(self, vfs: VFS, filename: str | None):
        self.vfs = vfs
        self.filename = filename or "*scratch*"
        text = vfs.read(filename) if (filename and vfs.is_file(filename)) else ""
        self.lines = text.split("\n") if text else [""]
        self.cy = 0
        self.cx = 0
        self.killring = ""
        self.alive = True
        self.message = f'emacs — {self.filename}'

    def feed(self, chords: list[str]):
        for c in chords:
            self._chord(c)
        return self

    def _clamp(self):
        self.cy = max(0, min(self.cy, len(self.lines) - 1))
        self.cx = max(0, min(self.cx, len(self.lines[self.cy])))

    def _chord(self, c: str):
        if c == "C-f":
            self.cx += 1
        elif c == "C-b":
            self.cx -= 1
        elif c == "C-n":
            self.cy += 1
        elif c == "C-p":
            self.cy -= 1
        elif c == "C-a":
            self.cx = 0
        elif c == "C-e":
            self.cx = len(self.lines[self.cy])
        elif c == "C-d":
            line = self.lines[self.cy]
            if self.cx < len(line):
                self.lines[self.cy] = line[:self.cx] + line[self.cx + 1:]
        elif c == "C-k":                       # kill to end of line
            line = self.lines[self.cy]
            self.killring = line[self.cx:]
            self.lines[self.cy] = line[:self.cx]
        elif c == "C-y":                       # yank
            self._insert(self.killring)
        elif c == "RET":
            self._insert("\n")
        elif c == "C-x C-s":                   # save
            self.save()
            self.message = f'Wrote {self.filename}'
            return
        elif c == "C-x C-c":                   # exit
            self.alive = False
            return
        else:                                  # self-insert literal text
            self._insert(c)
        self._clamp()

    def _insert(self, text: str):
        for ch in text:
            if ch == "\n":
                rest = self.lines[self.cy][self.cx:]
                self.lines[self.cy] = self.lines[self.cy][:self.cx]
                self.lines.insert(self.cy + 1, rest)
                self.cy += 1
                self.cx = 0
            else:
                line = self.lines[self.cy]
                self.lines[self.cy] = line[:self.cx] + ch + line[self.cx:]
                self.cx += 1

    def save(self):
        self.vfs.write(self.filename, self.text())

    def text(self) -> str:
        return "\n".join(self.lines)

    # -- Bada language tooling: grammar check + completion -----------------
    def lint(self):
        from bada import lint as _lint
        return _lint(self.text())

    def complete(self, kind: str = "all"):
        from bada import Completer, prefix_at
        line = self.lines[self.cy] if 0 <= self.cy < len(self.lines) else ""
        pre = prefix_at(line, self.cx)
        return Completer().complete(self.text(), pre, kind), pre

    def status(self) -> str:
        return f'emacs "{self.filename}" ({self.cy + 1},{self.cx + 1})'
