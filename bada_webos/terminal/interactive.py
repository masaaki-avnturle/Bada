"""Interactive character input for the terminal's vim and emacs.

Two front-ends per editor:

* a full-screen **curses** UI when stdin is a real terminal — you type and the
  characters go into the buffer (vim INSERT mode / emacs self-insert), with the
  usual motion/command keys; and
* a **line-input fallback** when there is no tty (pipes, CI, the web shell) so
  character input still works everywhere.

Both persist to the VFS through the session's ``save()``.
"""

from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _p in (_ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from editor import INSERT, NORMAL                       # noqa: E402


def _has_tty() -> bool:
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


# ===========================================================================
# public entry points
# ===========================================================================
def run_vim(sess, instream=None, out=None, force_line: bool = False):
    if not force_line and _has_tty():
        try:
            return _curses_vim(sess)
        except Exception:
            pass
    return line_vim(sess, instream or sys.stdin, out or sys.stdout)


def run_emacs(sess, instream=None, out=None, force_line: bool = False):
    if not force_line and _has_tty():
        try:
            return _curses_emacs(sess)
        except Exception:
            pass
    return line_emacs(sess, instream or sys.stdin, out or sys.stdout)


# ===========================================================================
# curses: vim
# ===========================================================================
_VIM_NORMAL_KEYS = {"i": "INSERT", "a": "INSERT", "o": "NEWLINE",
                    "x": "DELETE", "h": "LEFT", "j": "DOWN", "k": "UP",
                    "l": "RIGHT"}


def _curses_vim(sess):                                   # pragma: no cover
    import curses

    ed = sess.ed

    def _main(scr):
        curses.use_default_colors()
        scr.keypad(True)
        cmdline, in_cmd, quit = "", False, False
        while not quit:
            scr.erase()
            h, w = scr.getmaxyx()
            for i, line in enumerate(ed.lines[:h - 1]):
                scr.addnstr(i, 0, line, w - 1)
            status = (":" + cmdline) if in_cmd else \
                f"-- {ed.mode} --  {sess.filename}  (i:insert ESC :wq)"
            scr.addnstr(h - 1, 0, status[:w - 1], w - 1, curses.A_REVERSE)
            scr.move(min(ed.cy, h - 2), min(ed.cx, max(0, w - 1)))
            scr.refresh()

            ch = scr.getch()
            if in_cmd:
                if ch in (10, 13):
                    c = cmdline.strip()
                    if c in ("w", "wq"):
                        sess.save()
                    if c in ("q", "wq", "q!"):
                        quit = True
                    in_cmd, cmdline = False, ""
                elif ch == 27:
                    in_cmd, cmdline = False, ""
                elif ch in (curses.KEY_BACKSPACE, 127, 8):
                    cmdline = cmdline[:-1]
                elif 0 <= ch < 256:
                    cmdline += chr(ch)
                continue

            if ed.mode == NORMAL:
                c = chr(ch) if 0 <= ch < 256 else ""
                if c == ":":
                    in_cmd, cmdline = True, ""
                elif c in _VIM_NORMAL_KEYS:
                    ed.apply_command(_VIM_NORMAL_KEYS[c])
                elif ch == curses.KEY_UP:
                    ed.apply_command("UP")
                elif ch == curses.KEY_DOWN:
                    ed.apply_command("DOWN")
                elif ch == curses.KEY_LEFT:
                    ed.apply_command("LEFT")
                elif ch == curses.KEY_RIGHT:
                    ed.apply_command("RIGHT")
            else:  # INSERT — characters go straight into the buffer
                if ch == 27:
                    ed.apply_command("ESCAPE")
                elif ch in (10, 13):
                    ed.type_text("\n")
                elif ch in (curses.KEY_BACKSPACE, 127, 8):
                    ed.type_text("\b")
                elif 0 <= ch < 256:
                    ed.type_text(chr(ch))

    curses.wrapper(_main)
    sess.alive = False
    return sess


# ===========================================================================
# curses: emacs
# ===========================================================================
_EMACS_CTRL = {1: "C-a", 2: "C-b", 4: "C-d", 5: "C-e", 6: "C-f",
               11: "C-k", 14: "C-n", 16: "C-p", 25: "C-y"}


def _curses_emacs(sess):                                 # pragma: no cover
    import curses

    def _main(scr):
        curses.use_default_colors()
        scr.keypad(True)
        while sess.alive:
            scr.erase()
            h, w = scr.getmaxyx()
            for i, line in enumerate(sess.lines[:h - 1]):
                scr.addnstr(i, 0, line, w - 1)
            status = f"-- emacs --  {sess.filename}  " \
                     f"(C-x C-s save  C-x C-c exit)  {sess.message}"
            scr.addnstr(h - 1, 0, status[:w - 1], w - 1, curses.A_REVERSE)
            scr.move(min(sess.cy, h - 2), min(sess.cx, max(0, w - 1)))
            scr.refresh()

            ch = scr.getch()
            if ch == 24:                       # C-x prefix
                nxt = scr.getch()
                if nxt == 19:                  # C-x C-s
                    sess._chord("C-x C-s")
                elif nxt == 3:                 # C-x C-c
                    sess._chord("C-x C-c")
                continue
            if ch in _EMACS_CTRL:
                sess._chord(_EMACS_CTRL[ch])
            elif ch in (10, 13):
                sess._chord("RET")
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                if sess.cx > 0:
                    sess._chord("C-b")
                    sess._chord("C-d")
            elif ch == curses.KEY_LEFT:
                sess._chord("C-b")
            elif ch == curses.KEY_RIGHT:
                sess._chord("C-f")
            elif ch == curses.KEY_UP:
                sess._chord("C-p")
            elif ch == curses.KEY_DOWN:
                sess._chord("C-n")
            elif 32 <= ch < 256:               # printable -> self-insert
                sess._chord(chr(ch))

    curses.wrapper(_main)
    return sess


# ===========================================================================
# line-input fallbacks (no tty) — still real character input
# ===========================================================================
def line_vim(sess, instream, out):
    """Line-oriented vim: each typed line is appended; ``:wq`` saves+quits,
    ``:q`` quits, ``:w`` saves and continues."""
    out.write(f'-- vim "{sess.filename}" (type lines; ":wq" save+quit, '
              f'":q" quit, ":w" save) --\n')
    out.flush()
    ed = sess.ed
    if ed.text() == "":
        ed.lines = [""]
    while True:
        raw = instream.readline()
        if not raw:
            break
        line = raw.rstrip("\n")
        cmd = line.strip()
        if cmd in (":wq", ":x"):
            sess.save()
            break
        if cmd == ":q":
            break
        if cmd == ":w":
            sess.save()
            out.write(f'"{sess.filename}" written\n')
            out.flush()
            continue
        # append the typed line to the buffer
        if ed.lines == [""]:
            ed.lines = [line]
        else:
            ed.lines.append(line)
    sess.alive = False
    return sess


def line_emacs(sess, instream, out):
    """Line-oriented emacs: typed lines self-insert as new lines; the tokens
    ``C-x C-s`` (save) and ``C-x C-c`` (exit) act as in emacs."""
    out.write(f'-- emacs "{sess.filename}" (type lines; "C-x C-s" save, '
              f'"C-x C-c" exit) --\n')
    out.flush()
    if sess.text() == "":
        sess.lines = [""]
        sess.cy = sess.cx = 0
    while True:
        raw = instream.readline()
        if not raw:
            break
        line = raw.rstrip("\n")
        token = line.strip()
        if token == "C-x C-c":
            sess._chord("C-x C-c")
            break
        if token == "C-x C-s":
            sess.save()
            out.write(f"Wrote {sess.filename}\n")
            out.flush()
            continue
        if sess.lines == [""]:
            sess.lines = [line]
            sess.cy, sess.cx = 0, len(line)
        else:
            sess.lines.append(line)
            sess.cy, sess.cx = len(sess.lines) - 1, len(line)
    return sess
