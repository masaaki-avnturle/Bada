"""w9wm — faithful reproduction of the w9wm window manager.

w9wm is Benjamin Drieu's extension of David Hogan's 9wm (the Plan 9 *rio* /
8½ look-and-feel window manager for X11).  Over 9wm it adds two things, both
reproduced here exactly:

  * **title bars** on every managed window, and
  * **8 virtual screens** (virtual desktops) selectable from the root menu.

Everything else follows 9wm semantics: a 4-pixel border, click-to-focus,
click-to-raise, and a button-3 root menu whose fixed entries are
``New  Reshape  Move  Delete  Hide`` followed by the virtual-screen list and
any hidden windows.  "New" sweeps a window, "Hide" unmaps it (and it then
appears in the menu to be restored), "Delete" closes it.

This is a headless model of that behaviour with ASCII and HTML renderers, so
the BadaWebOS desktop can run a real w9wm without an X server.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --- w9wm compile-time defaults (config.h) -----------------------------------
BORDER = 4              # window border width in px (9wm default)
TITLE_H = 18            # title-bar height in px (w9wm addition)
NUM_SCREENS = 8         # virtual screens (w9wm default is 8)
FIXED_MENU = ("New", "Reshape", "Move", "Delete", "Hide")


@dataclass
class Window:
    wid: int
    name: str
    x: int = 0
    y: int = 0
    w: int = 320
    h: int = 200
    screen: int = 0          # which virtual screen (0..NUM_SCREENS-1)
    hidden: bool = False
    mapped: bool = True

    def geom(self) -> str:
        return f"{self.w}x{self.h}+{self.x}+{self.y}"


class W9wm:
    def __init__(self, width: int = 1024, height: int = 768,
                 screens: int = NUM_SCREENS):
        self.width = width
        self.height = height
        self.screens = screens
        self.current = 0                  # current virtual screen (0-indexed)
        self.windows: list[Window] = []   # stacking order, last = top
        self.focused: int | None = None
        self._next_id = 1

    # -- window lifecycle (the "New" sweep) --------------------------------
    def new_window(self, name: str, x=None, y=None, w=320, h=200) -> Window:
        # 9wm: a new window is "swept" onto the *current* screen and raised.
        wid = self._next_id
        self._next_id += 1
        if x is None:
            x = 40 + (len(self.windows) % 6) * 30
        if y is None:
            y = 40 + (len(self.windows) % 6) * 30
        win = Window(wid, name, x, y, w, h, screen=self.current)
        self.windows.append(win)
        self.focus(wid)
        return win

    def _get(self, wid: int) -> Window:
        for win in self.windows:
            if win.wid == wid:
                return win
        raise KeyError(f"no window {wid}")

    # -- root menu actions -------------------------------------------------
    def reshape(self, wid: int, x: int, y: int, w: int, h: int):
        win = self._get(wid)
        win.x, win.y, win.w, win.h = x, y, w, h
        self.raise_window(wid)

    def move(self, wid: int, dx: int, dy: int):
        win = self._get(wid)
        win.x += dx
        win.y += dy
        self.raise_window(wid)

    def delete(self, wid: int):
        self.windows = [w for w in self.windows if w.wid != wid]
        if self.focused == wid:
            self.focused = self._top_on_current()

    def hide(self, wid: int):
        win = self._get(wid)
        win.hidden = True
        win.mapped = False
        if self.focused == wid:
            self.focused = self._top_on_current()

    def unhide(self, wid: int):
        win = self._get(wid)
        win.hidden = False
        win.mapped = True
        win.screen = self.current        # restored onto the current screen
        self.focus(wid)

    # -- focus / stacking (click-to-focus, click-to-raise) -----------------
    def focus(self, wid: int):
        win = self._get(wid)
        if win.hidden:
            return
        self.current = win.screen
        self.focused = wid
        self.raise_window(wid)

    def raise_window(self, wid: int):
        win = self._get(wid)
        self.windows.remove(win)
        self.windows.append(win)

    def _top_on_current(self) -> int | None:
        for win in reversed(self.windows):
            if win.screen == self.current and not win.hidden:
                return win.wid
        return None

    # -- virtual screens (w9wm's defining feature) -------------------------
    def switch_screen(self, n: int):
        if not 0 <= n < self.screens:
            raise ValueError(f"screen {n} out of range 0..{self.screens-1}")
        self.current = n
        self.focused = self._top_on_current()

    def windows_on(self, screen: int) -> list[Window]:
        return [w for w in self.windows
                if w.screen == screen and not w.hidden]

    def hidden_windows(self) -> list[Window]:
        return [w for w in self.windows if w.hidden]

    # -- the button-3 root menu --------------------------------------------
    def root_menu(self) -> list[str]:
        items = list(FIXED_MENU)
        items += [f"Screen {i + 1}" + (" *" if i == self.current else "")
                  for i in range(self.screens)]
        items += [f"Unhide {w.name}" for w in self.hidden_windows()]
        return items

    # -- renderers ---------------------------------------------------------
    def render_ascii(self) -> str:
        wins = self.windows_on(self.current)
        lines = [f"w9wm  screen {self.current + 1}/{self.screens}"
                 f"  [{len(wins)} win, {len(self.hidden_windows())} hidden]"]
        for win in wins:
            star = "*" if win.wid == self.focused else " "
            lines.append(f" {star}[{win.name}] {win.geom()}")
        return "\n".join(lines)

    def render_html(self) -> str:
        out = ['<div class="w9wm-root">']
        # screen-switch tab bar (w9wm virtual screens)
        out.append('<div class="w9wm-screens">')
        for i in range(self.screens):
            cls = "scr cur" if i == self.current else "scr"
            out.append(f'<span class="{cls}">{i + 1}</span>')
        out.append('</div>')
        for win in self.windows_on(self.current):
            foc = "win focused" if win.wid == self.focused else "win"
            style = (f"left:{win.x}px;top:{win.y}px;"
                     f"width:{win.w}px;height:{win.h}px;"
                     f"border-width:{BORDER}px")
            out.append(f'<div class="{foc}" style="{style}">')
            out.append(f'<div class="titlebar" style="height:{TITLE_H}px">'
                       f'{win.name}</div>')
            out.append(f'<div class="client">{win.name} client area</div>')
            out.append('</div>')
        out.append('</div>')
        return "\n".join(out)
