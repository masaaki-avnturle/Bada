"""BadaVim: a modal (vim-like) editor for the Bada language.

The editor core is fully headless and scriptable so it can be driven by
keystrokes *or* by silent-talk tokens, and tested without a terminal.  A
curses front-end (:func:`run_interactive`) is provided for real use.

Editor commands (symbolic names shared with the silent-talk lexicon):

    INSERT ESCAPE UP DOWN LEFT RIGHT NEWLINE DELETE SAVE QUIT RUN

In NORMAL mode a command name is an action; in INSERT mode dictated text is
inserted at the cursor.  RUN feeds the buffer through the Bada compiler+VM
and shows the captured output.
"""

from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass, field

# Make the sibling `bada` package importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bada import run_source  # noqa: E402

NORMAL = "NORMAL"
INSERT = "INSERT"

COMMANDS = {"INSERT", "ESCAPE", "UP", "DOWN", "LEFT", "RIGHT",
            "NEWLINE", "DELETE", "SAVE", "QUIT", "RUN"}


@dataclass
class BadaVim:
    filename: str = "untitled.bada"
    lines: list[str] = field(default_factory=lambda: [""])
    cy: int = 0
    cx: int = 0
    mode: str = NORMAL
    message: str = "-- NORMAL --  i:insert  esc:normal  !:run  :w :q"
    output: list[str] = field(default_factory=list)
    quit: bool = False
    dirty: bool = False
    history: list[str] = field(default_factory=list)  # log of actions

    # -- construction ------------------------------------------------------
    @classmethod
    def open(cls, path: str) -> "BadaVim":
        ed = cls(filename=path)
        if os.path.exists(path):
            with open(path) as f:
                text = f.read()
            ed.lines = text.split("\n") or [""]
            if ed.lines == []:
                ed.lines = [""]
        return ed

    # -- cursor helpers ----------------------------------------------------
    def _clamp(self):
        self.cy = max(0, min(self.cy, len(self.lines) - 1))
        line_len = len(self.lines[self.cy])
        hi = line_len if self.mode == INSERT else max(0, line_len - 1)
        self.cx = max(0, min(self.cx, hi))

    # -- normal-mode actions ----------------------------------------------
    def apply_command(self, name: str):
        name = name.upper()
        self.history.append(name)
        if name == "INSERT":
            self.mode = INSERT
        elif name == "ESCAPE":
            self.mode = NORMAL
            if self.cx > 0 and self.cx >= len(self.lines[self.cy]):
                self.cx = max(0, len(self.lines[self.cy]) - 1)
        elif name == "UP":
            self.cy -= 1
        elif name == "DOWN":
            self.cy += 1
        elif name == "LEFT":
            self.cx -= 1
        elif name == "RIGHT":
            self.cx += 1
        elif name == "NEWLINE":     # open line below, like vim 'o'
            self.lines.insert(self.cy + 1, "")
            self.cy += 1
            self.cx = 0
            self.mode = INSERT
            self.dirty = True
        elif name == "DELETE":      # delete char under cursor, like 'x'
            line = self.lines[self.cy]
            if self.cx < len(line):
                self.lines[self.cy] = line[:self.cx] + line[self.cx + 1:]
                self.dirty = True
        elif name == "SAVE":
            self.save()
        elif name == "QUIT":
            self.quit = True
        elif name == "RUN":
            self.run_buffer()
        else:
            self.message = f"?unknown command {name}"
            return
        self._clamp()
        self._refresh_status()

    # -- insert-mode text --------------------------------------------------
    def type_text(self, text: str):
        self.history.append(f"TEXT:{text!r}")
        if self.mode != INSERT:
            self.mode = INSERT
        for ch in text:
            if ch == "\n":
                rest = self.lines[self.cy][self.cx:]
                self.lines[self.cy] = self.lines[self.cy][:self.cx]
                self.lines.insert(self.cy + 1, rest)
                self.cy += 1
                self.cx = 0
            elif ch == "\b":  # backspace
                if self.cx > 0:
                    line = self.lines[self.cy]
                    self.lines[self.cy] = line[:self.cx - 1] + line[self.cx:]
                    self.cx -= 1
                elif self.cy > 0:
                    prev = self.lines[self.cy - 1]
                    self.cx = len(prev)
                    self.lines[self.cy - 1] = prev + self.lines[self.cy]
                    del self.lines[self.cy]
                    self.cy -= 1
            else:
                line = self.lines[self.cy]
                self.lines[self.cy] = line[:self.cx] + ch + line[self.cx:]
                self.cx += 1
        self.dirty = True
        self._refresh_status()

    # -- routing for silent-talk tokens -----------------------------------
    def feed_token(self, token) -> bool:
        """Apply one decoded silent-talk Token. Returns True if it did
        something."""
        # ESCAPE always wins, regardless of mode.
        if token.command == "ESCAPE":
            self.apply_command("ESCAPE")
            return True
        # In INSERT mode, NEWLINE means "break the line here".
        if self.mode == INSERT and token.command == "NEWLINE":
            self.type_text("\n")
            return True
        if self.mode == INSERT and token.text is not None:
            self.type_text(token.text)
            return True
        if self.mode == NORMAL and token.command is not None:
            self.apply_command(token.command)
            return True
        # Unrecognised in current mode.
        self.message = f"?ignored {token.visemes} in {self.mode}"
        return False

    # -- file + run --------------------------------------------------------
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

    def save(self, path: str | None = None):
        path = path or self.filename
        with open(path, "w") as f:
            f.write(self.text())
        self.filename = path
        self.dirty = False
        self.message = f'"{path}" {len(self.lines)}L written'

    def run_buffer(self):
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                vm = run_source(self.text())
            out = buf.getvalue().splitlines()
            self.output = out
            self.message = f"-- RAN ok: {len(out)} line(s) of output --"
        except Exception as exc:  # report Bada compile/runtime errors inline
            self.output = [f"{type(exc).__name__}: {exc}"]
            self.message = "-- RUN error --"

    def _refresh_status(self):
        flag = "*" if self.dirty else " "
        if self.mode == INSERT:
            self.message = f"-- INSERT --{flag} {self.filename} " \
                           f"({self.cy + 1},{self.cx + 1})"
        elif not self.message.startswith(('"', '?', '--')):
            self.message = f"-- NORMAL --{flag} {self.filename}"


# --------------------------------------------------------------------------
# curses front-end
# --------------------------------------------------------------------------
KEY_TO_COMMAND_NORMAL = {
    "h": "LEFT", "j": "DOWN", "k": "UP", "l": "RIGHT",
    "i": "INSERT", "o": "NEWLINE", "x": "DELETE", "!": "RUN",
}


def run_interactive(ed: "BadaVim"):  # pragma: no cover - needs a terminal
    import curses

    def _main(stdscr):
        curses.use_default_colors()
        stdscr.keypad(True)
        cmdline = ""
        in_cmdline = False
        while not ed.quit:
            stdscr.erase()
            h, w = stdscr.getmaxyx()
            text_h = max(1, h - 2 - min(len(ed.output), 6))
            for i in range(text_h):
                if i < len(ed.lines):
                    stdscr.addnstr(i, 0, ed.lines[i], w - 1)
            # output pane
            base = text_h
            for j, line in enumerate(ed.output[:6]):
                stdscr.addnstr(base + j, 0, "| " + line, w - 1)
            # status
            status = (":" + cmdline) if in_cmdline else ed.message
            stdscr.addnstr(h - 1, 0, status[:w - 1], w - 1,
                           curses.A_REVERSE)
            stdscr.move(min(ed.cy, text_h - 1), min(ed.cx, w - 1))
            stdscr.refresh()

            ch = stdscr.getch()
            if in_cmdline:
                if ch in (10, 13):
                    _do_cmdline(ed, cmdline)
                    in_cmdline, cmdline = False, ""
                elif ch == 27:
                    in_cmdline, cmdline = False, ""
                elif ch in (curses.KEY_BACKSPACE, 127, 8):
                    cmdline = cmdline[:-1]
                else:
                    cmdline += chr(ch)
                continue

            if ed.mode == NORMAL:
                c = chr(ch) if 0 <= ch < 256 else ""
                if c == ":":
                    in_cmdline, cmdline = True, ""
                elif c in KEY_TO_COMMAND_NORMAL:
                    ed.apply_command(KEY_TO_COMMAND_NORMAL[c])
                elif ch in (curses.KEY_UP,):
                    ed.apply_command("UP")
                elif ch in (curses.KEY_DOWN,):
                    ed.apply_command("DOWN")
                elif ch in (curses.KEY_LEFT,):
                    ed.apply_command("LEFT")
                elif ch in (curses.KEY_RIGHT,):
                    ed.apply_command("RIGHT")
            else:  # INSERT
                if ch == 27:
                    ed.apply_command("ESCAPE")
                elif ch in (10, 13):
                    ed.type_text("\n")
                elif ch in (curses.KEY_BACKSPACE, 127, 8):
                    ed.type_text("\b")
                elif 0 <= ch < 256:
                    ed.type_text(chr(ch))

    curses.wrapper(_main)


def _do_cmdline(ed: "BadaVim", cmd: str):  # pragma: no cover
    cmd = cmd.strip()
    if cmd in ("w", "write"):
        ed.apply_command("SAVE")
    elif cmd in ("q", "quit"):
        ed.apply_command("QUIT")
    elif cmd == "wq":
        ed.apply_command("SAVE")
        ed.apply_command("QUIT")
    elif cmd in ("run", "!"):
        ed.apply_command("RUN")
    else:
        ed.message = f"?unknown :{cmd}"
