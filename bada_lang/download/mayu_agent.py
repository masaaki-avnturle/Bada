#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mayu - a WORKING 窓使いの憂鬱 keyboard remapper for Windows 10 / 11.

Unlike the .reg files (which only *store* the configuration), this program is
the resident agent that actually makes the key bindings work: it installs a
low-level keyboard hook, watches every keystroke, and rewrites the Emacs / vim
chords from `keybindings.mayu` into real keystrokes in whatever application has
focus - Notepad, browsers, editors, anything.

Pure Python standard library (ctypes) - no third-party packages, no admin.

    python mayu_agent.py                 # Emacs bindings everywhere (default)
    python mayu_agent.py --keymap vim    # modal vim (normal/insert) everywhere
    python mayu_agent.py --config my.mayu
    python mayu_agent.py --selftest      # verify parsing/translation (any OS)
    python mayu_agent.py --list          # print the resolved Emacs key map

EMACS mode: each command maps to the Windows keystroke that does the same thing
(C-a -> Home, C-k -> Shift+End then Cut, C-f -> Right, ...).  C-SPC sets the
mark, then movement selects, C-w cuts, M-w copies - real region editing.

VIM mode: a modal engine.  Start in NORMAL (h/j/k/l move, i/a/o insert, x
delete, dd cut line, yy copy line, p paste, u undo, gg/G top/bottom, w/b word).
ESC returns to NORMAL.  Works in Notepad and other text fields.
"""

import argparse
import sys
import time

# --------------------------------------------------------------------------
# Embedded fallback config (used if keybindings.mayu is not found next to us).
# --------------------------------------------------------------------------
DEFAULT_MAYU = """\
os win11
keymap emacs {
  key C-a -> move-beginning-of-line
  key C-e -> move-end-of-line
  key C-f -> forward-char
  key C-b -> backward-char
  key C-n -> next-line
  key C-p -> previous-line
  key C-d -> delete-char
  key C-k -> kill-line
  key C-y -> yank
  key C-w -> kill-region
  key M-w -> copy-region
  key C-SPC -> set-mark-command
  key C-s -> isearch-forward
  key M-f -> forward-word
  key M-b -> backward-word
  key M-v -> scroll-down
  key C-v -> scroll-up
  key C-g -> keyboard-quit
  key C-slash -> undo
  key C-x C-s -> save-buffer
}
keymap vim-normal {
  key h -> cursor-left
  key j -> cursor-down
  key k -> cursor-up
  key l -> cursor-right
  key x -> delete-char
  key d d -> delete-line
  key p -> yank
}
app "Notepad" {
  exe notepad.exe
  class Notepad
  base emacs
  key C-x C-s -> save-buffer
}
"""

# --------------------------------------------------------------------------
# Symbolic command  ->  output key sequence (each item is a chord string).
# This is what makes Emacs/vim editing commands work in ordinary Windows apps.
# --------------------------------------------------------------------------
COMMAND_KEYS = {
    "move-beginning-of-line": ["Home"],
    "move-end-of-line": ["End"],
    "beginning-of-line": ["Home"],
    "end-of-line": ["End"],
    "line-start": ["Home"],
    "line-end": ["End"],
    "forward-char": ["Right"],
    "backward-char": ["Left"],
    "cursor-right": ["Right"],
    "cursor-left": ["Left"],
    "cursor-up": ["Up"],
    "cursor-down": ["Down"],
    "next-line": ["Down"],
    "previous-line": ["Up"],
    "forward-word": ["C-Right"],
    "backward-word": ["C-Left"],
    "word-forward": ["C-Right"],
    "word-back": ["C-Left"],
    "delete-char": ["Delete"],
    "backward-delete-char": ["BackSpace"],
    "kill-line": ["S-End", "C-x"],       # select to end of line, then cut
    "delete-line": ["Home", "S-Down", "C-x"],
    "kill-region": ["C-x"],
    "copy-region": ["C-c"],
    "kill-ring-save": ["C-c"],
    "yank": ["C-v"],
    "paste": ["C-v"],
    "save-buffer": ["C-s"],
    "isearch-forward": ["C-f"],
    "isearch-backward": ["C-f"],
    "search": ["C-f"],
    "keyboard-quit": ["Escape"],
    "normal-mode": ["Escape"],
    "undo": ["C-z"],
    "scroll-up": ["Next"],               # Emacs C-v = page down
    "scroll-down": ["Prior"],            # Emacs M-v = page up
    "beginning-of-buffer": ["C-Home"],
    "end-of-buffer": ["C-End"],
    "newline": ["Return"],
}

# commands that MOVE the caret; when the Emacs mark is active they extend the
# selection instead (Shift is added to the output).
MOVEMENT_COMMANDS = {
    "move-beginning-of-line", "move-end-of-line", "beginning-of-line",
    "end-of-line", "line-start", "line-end", "forward-char", "backward-char",
    "cursor-right", "cursor-left", "cursor-up", "cursor-down", "next-line",
    "previous-line", "forward-word", "backward-word", "word-forward",
    "word-back", "beginning-of-buffer", "end-of-buffer",
}


# --------------------------------------------------------------------------
# .mayu config parser (a subset of the mayu DSL; matches lib/mayucfg.bada).
# --------------------------------------------------------------------------
def _strip_comment(line):
    q = False
    for i, c in enumerate(line):
        if c == '"':
            q = not q
        elif not q and c == "#":
            return line[:i]
        elif not q and c == "/" and i + 1 < len(line) and line[i + 1] == "/":
            return line[:i]
    return line


def parse_mayu(text):
    """Return {scopes: {name: {chord: action}}, inherits, apps: {name: meta}}."""
    scopes, inherits, apps = {}, {}, {}
    variables = {}
    cur = None
    curapp = None

    def subst(s):
        for k, v in variables.items():
            s = s.replace("$" + k, v)
        return s

    for raw in text.split("\n"):
        line = _strip_comment(raw).strip()
        if not line:
            continue
        if line == "}":
            cur = curapp = None
        elif line.startswith("os "):
            continue
        elif line.startswith("include "):
            continue                                  # expanded before parsing
        elif line.startswith("define "):
            body = line[7:]
            if "=" in body:
                name, val = body.split("=", 1)
                variables[name.strip()] = val.strip()
        elif line.startswith("keymap "):
            cur = line[7:].replace("{", "").strip()
            scopes.setdefault(cur, {})
            inherits[cur] = ""
        elif line.startswith("app "):
            name = _quoted(line[4:])
            cur = curapp = name
            scopes.setdefault(cur, {})
            apps.setdefault(name, {"class": "", "exe": "", "base": ""})
        elif curapp and line.startswith("class "):
            apps[curapp]["class"] = line[6:].strip()
        elif curapp and line.startswith("exe "):
            apps[curapp]["exe"] = line[4:].strip()
        elif curapp and line.startswith("base "):
            apps[curapp]["base"] = line[5:].strip()
            inherits[curapp] = line[5:].strip()
        elif line.startswith("window "):
            rest = line[7:]
            name = _quoted(rest)
            base = ""
            if ":" in rest:
                base = rest.split(":", 1)[1].replace("{", "").strip()
            cur = name
            scopes.setdefault(cur, {})
            inherits[cur] = base
        elif line.startswith("key "):
            body = subst(line[4:].strip())
            if "->" in body and cur is not None:
                chord, action = body.split("->", 1)
                scopes[cur][chord.strip()] = action.strip()
    return {"scopes": scopes, "inherits": inherits, "apps": apps}


def _quoted(s):
    a = s.find('"')
    if a < 0:
        return ""
    b = s.find('"', a + 1)
    return s[a + 1:b] if b > 0 else ""


def effective(cfg, name):
    """Merge a scope with the scopes it inherits from (base first)."""
    chain, seen = [], set()
    n = name
    while n and n in cfg["scopes"] and n not in seen:
        seen.add(n)
        chain.append(n)
        n = cfg["inherits"].get(n, "")
    out = {}
    for n in reversed(chain):
        out.update(cfg["scopes"][n])
    return out


def action_to_keys(action):
    """Translate an action into ('keys', [chords]) / ('type', text) / ('exec',..)."""
    action = action.strip()
    if action.startswith("send "):
        return ("keys", action[5:].split())
    if action.startswith("type "):
        return ("type", _quoted(action) or action[5:].strip())
    if action.startswith("exec "):
        return ("exec", _quoted(action) or action[5:].strip())
    if action in COMMAND_KEYS:
        return ("keys", list(COMMAND_KEYS[action]))
    return ("keys", [action])          # a raw chord like "C-Tab" used directly


def add_shift(chord):
    """Add the Shift modifier to a chord: Home -> S-Home, C-Right -> C-S-Right."""
    mods, key = parse_chord(chord)
    mods = set(mods)
    mods.add("S")
    order = [m for m in ("C", "M", "S", "W") if m in mods]
    return "-".join(order + [key])


def resolve_output(action, mark_active):
    """Emacs engine: action + mark state -> ('mark',None)/('keys',..)/('type',..)/('exec',..)."""
    a = action.strip()
    if a == "set-mark-command":
        return ("mark", None)
    kind, val = action_to_keys(a)
    if kind == "keys" and mark_active and a in MOVEMENT_COMMANDS:
        val = [add_shift(c) for c in val]
    return (kind, val)


# --------------------------------------------------------------------------
# Modal vim engine (used with --keymap vim).  Pure state machine so it can be
# unit-tested without Windows.
# --------------------------------------------------------------------------
VIM_SINGLE = {
    "h": (["Left"], "normal"),   "j": (["Down"], "normal"),
    "k": (["Up"], "normal"),     "l": (["Right"], "normal"),
    "0": (["Home"], "normal"),   "S-4": (["End"], "normal"),   # $
    "w": (["C-Right"], "normal"), "b": (["C-Left"], "normal"),
    "x": (["Delete"], "normal"), "S-x": (["BackSpace"], "normal"),
    "p": (["C-v"], "normal"),    "u": (["C-z"], "normal"),
    "i": ([], "insert"),
    "a": (["Right"], "insert"),
    "S-a": (["End"], "insert"),                       # A - append at EOL
    "S-i": (["Home"], "insert"),                      # I - insert at BOL
    "o": (["End", "Return"], "insert"),               # open line below
    "S-o": (["Home", "Return", "Up"], "insert"),      # O - open line above
    "S-g": (["C-End"], "normal"),                     # G - end of buffer
    "S-d": (["S-End", "C-x"], "normal"),              # D - delete to EOL
    "S-c": (["S-End", "C-x"], "insert"),              # C - change to EOL
}
VIM_OPERATORS = {"d", "y", "g"}
VIM_TWO = {
    "dd": (["Home", "S-Down", "C-x"], "normal"),      # delete line (cut)
    "yy": (["Home", "S-Down", "C-c", "Home"], "normal"),   # yank line (copy)
    "gg": (["C-Home"], "normal"),                     # top of buffer
}


def vim_step(mode, chord, pending):
    """Return (outputs, new_mode, new_pending, suppress).

    outputs None  => let the key pass through unchanged (suppress must be False).
    outputs []    => handled with no keystrokes (e.g. mode change), suppress True.
    outputs [..]  => inject these chords, suppress True.
    """
    if mode == "insert":
        if chord in ("Escape", "C-[", "C-c"):
            return ([], "normal", None, True)
        return (None, "insert", None, False)          # type normally

    # ---- NORMAL mode ----
    if pending:
        combo = pending + chord
        if combo in VIM_TWO:
            outs, nm = VIM_TWO[combo]
            return (outs, nm, None, True)
        pending = None                                # cancel; handle chord alone

    if chord in VIM_OPERATORS:
        return ([], "normal", chord, True)

    if chord in VIM_SINGLE:
        outs, nm = VIM_SINGLE[chord]
        return (outs, nm, None, True)

    # let modified chords through (Ctrl/Alt/Win: e.g. C-s save, C-Tab)
    mods, _ = parse_chord(chord)
    if mods & {"C", "M", "W"}:
        return (None, "normal", None, False)

    # a bare unhandled key in NORMAL mode: swallow it so it does not type text
    return ([], "normal", None, True)


# --------------------------------------------------------------------------
# Chord parsing + virtual-key table.
# --------------------------------------------------------------------------
VK = {
    "Home": 0x24, "End": 0x23, "Left": 0x25, "Up": 0x26, "Right": 0x27,
    "Down": 0x28, "Delete": 0x2E, "Insert": 0x2D, "BackSpace": 0x08,
    "Tab": 0x09, "Return": 0x0D, "Enter": 0x0D, "RET": 0x0D, "Escape": 0x1B,
    "ESC": 0x1B, "Space": 0x20, "SPC": 0x20, "Prior": 0x21, "PageUp": 0x21,
    "Next": 0x22, "PageDown": 0x22, "slash": 0xBF,
}
for _i in range(10):
    VK[str(_i)] = 0x30 + _i
for _c in range(ord("a"), ord("z") + 1):
    VK[chr(_c)] = ord(chr(_c).upper())
for _f in range(1, 13):
    VK["F%d" % _f] = 0x6F + _f

MODVK = {"C": 0x11, "M": 0x12, "A": 0x12, "S": 0x10, "W": 0x5B}


def parse_chord(chord):
    """'C-a' -> ({'C'}, 'a'), 'C-S-Right' -> ({'C','S'}, 'Right')."""
    mods = set()
    s = chord
    while len(s) >= 2 and s[1] == "-" and s[0] in MODVK:
        mods.add(s[0])
        s = s[2:]
    return mods, s


# --------------------------------------------------------------------------
# Windows low-level keyboard hook (only used on win32).
# --------------------------------------------------------------------------
def run_windows(cfg, keymap):
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    WH_KEYBOARD_LL = 13
    WM_KEYDOWN, WM_SYSKEYDOWN = 0x0100, 0x0104
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004
    MAGIC = 0x1A2B3C4D
    HC_ACTION = 0
    ULONG_PTR = wintypes.WPARAM
    vim_mode = keymap.startswith("vim")

    class KBDLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD),
                    ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                    ("dwExtraInfo", ULONG_PTR)]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                    ("dwExtraInfo", ULONG_PTR)]

    class INPUT(ctypes.Structure):
        class _U(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]
        _anonymous_ = ("u",)
        _fields_ = [("type", wintypes.DWORD), ("u", _U)]

    INPUT_KEYBOARD = 1
    SendInput = user32.SendInput
    SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)

    def _send(vk, up=False, unicode_ch=None):
        ki = KEYBDINPUT(0, 0, 0, 0, MAGIC)
        if unicode_ch is not None:
            ki.wScan = ord(unicode_ch)
            ki.dwFlags = KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if up else 0)
        else:
            ki.wVk = vk
            ki.dwFlags = KEYEVENTF_KEYUP if up else 0
        inp = INPUT(INPUT_KEYBOARD)
        inp.ki = ki
        SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def send_keys(chords):
        for mv in (0x11, 0x12, 0x10, 0x5B, 0x5C):     # drop physical modifiers
            _send(mv, up=True)
        for chord in chords:
            mods, key = parse_chord(chord)
            vk = VK.get(key)
            if vk is None:
                continue
            for m in mods:
                _send(MODVK[m])
            _send(vk)
            _send(vk, up=True)
            for m in mods:
                _send(MODVK[m], up=True)

    def send_text(text):
        for ch in text:
            _send(0, unicode_ch=ch)
            _send(0, up=True, unicode_ch=ch)

    GetForegroundWindow = user32.GetForegroundWindow
    GetClassNameW = user32.GetClassNameW

    def foreground_class():
        hwnd = GetForegroundWindow()
        buf = ctypes.create_unicode_buffer(256)
        GetClassNameW(hwnd, buf, 256)
        return buf.value

    app_maps = []
    for name, meta in cfg["apps"].items():
        if meta.get("class"):
            app_maps.append((meta["class"], effective(cfg, name)))
    base_map = effective(cfg, keymap)

    def active_map():
        cls = foreground_class()
        for klass, m in app_maps:
            if klass and klass in cls:
                return m
        return base_map

    GetAsyncKeyState = user32.GetAsyncKeyState

    def down(vk):
        return GetAsyncKeyState(vk) & 0x8000

    rev = {}
    for _name in ("Home", "End", "Left", "Up", "Right", "Down", "Delete",
                  "Insert", "BackSpace", "Tab", "Return", "Escape", "Space",
                  "Prior", "Next", "slash"):
        rev[VK[_name]] = _name
    for _i in range(10):
        rev[0x30 + _i] = str(_i)
    for _f in range(1, 13):
        rev[0x6F + _f] = "F%d" % _f

    def chord_from(vk):
        if 0x41 <= vk <= 0x5A:
            base = chr(vk + 32)
        elif vk in rev:
            base = rev[vk]
        else:
            return None
        pre = ""
        if down(0x11):
            pre += "C-"
        if down(0x12):
            pre += "M-"
        if down(0x10):
            pre += "S-"
        return pre + base

    HOOKPROC = ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_int,
                                wintypes.WPARAM, wintypes.LPARAM)

    state = {"mark": False, "mode": "normal", "pending": None, "estamp": 0.0}

    def do_emacs(action):
        kind, val = resolve_output(action, state["mark"])
        if kind == "mark":
            state["mark"] = True
        elif kind == "keys":
            send_keys(val)
            a = action.strip()
            if a in ("kill-region", "copy-region", "kill-ring-save", "yank",
                     "keyboard-quit"):
                state["mark"] = False
        elif kind == "type":
            send_text(val)
        elif kind == "exec":
            import subprocess
            try:
                subprocess.Popen(val, shell=True)
            except Exception:
                pass

    def ll_proc(nCode, wParam, lParam):
        if nCode == HC_ACTION and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
            kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            if kb.dwExtraInfo == MAGIC:
                return user32.CallNextHookEx(None, nCode, wParam, lParam)
            vk = kb.vkCode
            if vk in (0x10, 0x11, 0x12, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5,
                      0x5B, 0x5C):
                return user32.CallNextHookEx(None, nCode, wParam, lParam)
            chord = chord_from(vk)
            if chord:
                if vim_mode:
                    outs, nm, pend, suppress = vim_step(
                        state["mode"], chord, state["pending"])
                    if nm != state["mode"]:
                        state["mode"] = nm
                        print("-- %s --" % ("INSERT" if nm == "insert"
                                            else "NORMAL"))
                    state["pending"] = pend
                    if outs:
                        send_keys(outs)
                    if suppress:
                        return 1
                    return user32.CallNextHookEx(None, nCode, wParam, lParam)
                # ---- Emacs / keymap engine ----
                amap = active_map()
                now = time.time()
                if state["pending"] and now - state["estamp"] < 1.0:
                    combo = state["pending"] + " " + chord
                    state["pending"] = None
                    if combo in amap:
                        do_emacs(amap[combo])
                        return 1
                state["pending"] = None
                if any(k.startswith(chord + " ") for k in amap):
                    state["pending"] = chord
                    state["estamp"] = now
                    return 1
                if chord in amap:
                    do_emacs(amap[chord])
                    return 1
        return user32.CallNextHookEx(None, nCode, wParam, lParam)

    proc = HOOKPROC(ll_proc)
    user32.SetWindowsHookExW.restype = wintypes.HHOOK
    user32.SetWindowsHookExW.argtypes = (ctypes.c_int, HOOKPROC,
                                         wintypes.HINSTANCE, wintypes.DWORD)
    hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, proc,
                                    kernel32.GetModuleHandleW(None), 0)
    if not hook:
        print("mayu: failed to install keyboard hook (error %d)"
              % ctypes.get_last_error())
        return 1

    if vim_mode:
        print("mayu is running in VIM mode - starting in NORMAL.")
        print("h/j/k/l move, i/a/o insert, ESC normal, dd/yy/p, u undo, gg/G.")
    else:
        print("mayu is running - Emacs bindings active in every application.")
        print("C-a/C-e/C-f/C-b/C-n/C-p, C-k kill, C-SPC set mark, C-x C-s save.")
    print("Close this window (or Ctrl-C) to stop.")
    msg = wintypes.MSG()
    try:
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except KeyboardInterrupt:
        pass
    finally:
        user32.UnhookWindowsHookEx(hook)
    return 0


# --------------------------------------------------------------------------
# Windows-version detection + registry registration.
# --------------------------------------------------------------------------
def detect_os():
    """Return 'win11' or 'win10' (build 22000+ is Windows 11)."""
    if sys.platform == "win32":
        try:
            v = sys.getwindowsversion()
            return "win11" if v.build >= 22000 else "win10"
        except Exception:
            return "win11"
    return "win11"


def registry_plan(cfg, os_name):
    """The list of (subkey_path, value_name, value_data) to write under HKCU.

    Mirrors lib/mayucfg.bada: keymap/window scopes go to
      Software\\Mayu\\<os>\\<scope>
    and installed-app scopes to
      Software\\Mayu\\<os>\\apps\\<AppName>  with (exe)/(class)/(inherits).
    """
    base = "Software\\Mayu\\" + os_name
    plan = []
    for scope, binds in cfg["scopes"].items():
        if scope in cfg["apps"]:
            path = base + "\\apps\\" + scope
            meta = cfg["apps"][scope]
            if meta.get("exe"):
                plan.append((path, "(exe)", meta["exe"]))
            if meta.get("class"):
                plan.append((path, "(class)", meta["class"]))
            if meta.get("base"):
                plan.append((path, "(inherits)", meta["base"]))
        else:
            path = base + "\\" + scope
            inh = cfg["inherits"].get(scope, "")
            if inh:
                plan.append((path, "(inherits)", inh))
        for chord, action in binds.items():
            plan.append((path, chord, action))
    return plan


def register_to_registry(cfg, os_name):
    """Write the key bindings into HKCU\\Software\\Mayu\\<os>.  Returns count."""
    plan = registry_plan(cfg, os_name)
    if sys.platform != "win32":
        return len(plan)
    import winreg
    for path, name, data in plan:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, path)
        try:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, data)
        finally:
            winreg.CloseKey(key)
    return len(plan)


# --------------------------------------------------------------------------
# config loading (with `include`) + entry point
# --------------------------------------------------------------------------
def expand_includes(path, seen=None):
    """Read a .mayu file and inline any `include "other.mayu"` files."""
    import os
    if seen is None:
        seen = set()
    ap = os.path.abspath(path)
    if ap in seen:
        return ""
    seen.add(ap)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    base = os.path.dirname(ap)
    out = []
    for line in text.split("\n"):
        t = _strip_comment(line).strip()
        if t.startswith("include "):
            inc = _quoted(t[8:]) or t[8:].strip()
            try:
                out.append(expand_includes(os.path.join(base, inc), seen))
            except OSError:
                out.append("# (missing include: %s)" % inc)
        else:
            out.append(line)
    return "\n".join(out)


def load_config(path):
    import os
    candidates = []
    if path:
        candidates.append(path)
    here = os.path.dirname(os.path.abspath(sys.argv[0]))
    candidates += [os.path.join(here, "keybindings.mayu"), "keybindings.mayu"]
    for c in candidates:
        if os.path.isfile(c):
            try:
                return parse_mayu(expand_includes(c)), c
            except OSError:
                continue
    return parse_mayu(DEFAULT_MAYU), "(built-in default)"


def print_map(cfg, keymap):
    if keymap.startswith("vim"):
        print("vim modal engine: NORMAL h/j/k/l 0 $ w b x dd yy p u gg G "
              "i a A I o O D C  |  INSERT: ESC -> NORMAL")
        return
    m = effective(cfg, keymap)
    print("keymap '%s':" % keymap)
    for chord in sorted(m):
        kind, val = resolve_output(m[chord], False)
        rhs = " ".join(val) if isinstance(val, list) else str(val)
        print("  %-10s -> %-22s => %s [%s]" % (chord, m[chord], rhs, kind))


def selftest():
    ok = [True]

    def check(cond, msg):
        print(("  ok   " if cond else "  FAIL ") + msg)
        ok[0] = ok[0] and cond

    cfg = parse_mayu(DEFAULT_MAYU)
    em = effective(cfg, "emacs")
    check(em.get("C-a") == "move-beginning-of-line", "emacs C-a parsed")
    check(em.get("C-SPC") == "set-mark-command", "emacs C-SPC = set-mark")
    check(resolve_output("move-beginning-of-line", False) == ("keys", ["Home"]),
          "C-a -> Home")
    check(resolve_output("kill-line", False) == ("keys", ["S-End", "C-x"]),
          "kill-line -> Shift+End, Cut")
    check(resolve_output("set-mark-command", False) == ("mark", None),
          "C-SPC -> set mark")
    check(resolve_output("forward-char", True) == ("keys", ["S-Right"]),
          "with mark: forward-char extends selection")
    check(resolve_output("forward-word", True) == ("keys", ["C-S-Right"]),
          "with mark: forward-word -> Ctrl+Shift+Right")
    check(add_shift("Home") == "S-Home" and add_shift("C-Right") == "C-S-Right",
          "add_shift")
    # Notepad app resolves to Emacs
    np = effective(cfg, "Notepad")
    check(np.get("C-a") == "move-beginning-of-line", "Notepad inherits Emacs C-a")
    check(cfg["apps"]["Notepad"]["class"] == "Notepad", "Notepad class matched")
    # vim modal engine
    check(vim_step("normal", "h", None) == (["Left"], "normal", None, True),
          "vim NORMAL h -> Left")
    check(vim_step("normal", "i", None) == ([], "insert", None, True),
          "vim NORMAL i -> INSERT")
    check(vim_step("insert", "Escape", None) == ([], "normal", None, True),
          "vim INSERT ESC -> NORMAL")
    check(vim_step("insert", "x", None) == (None, "insert", None, False),
          "vim INSERT types normally")
    d1 = vim_step("normal", "d", None)
    check(d1 == ([], "normal", "d", True), "vim NORMAL d -> pending operator")
    check(vim_step("normal", "d", "d") == (["Home", "S-Down", "C-x"], "normal",
                                           None, True), "vim dd -> cut line")
    check(vim_step("normal", "S-g", None) == (["C-End"], "normal", None, True),
          "vim G -> end of buffer")
    check(vim_step("normal", "q", None) == ([], "normal", None, True),
          "vim NORMAL swallows bare unbound keys (no typing)")
    check(vim_step("normal", "C-s", None) == (None, "normal", None, False),
          "vim NORMAL passes Ctrl chords through (C-s save)")
    # registry registration plan (what running the .exe writes)
    check(detect_os() in ("win10", "win11"), "OS detection returns win10/win11")
    plan = registry_plan(cfg, "win11")
    check(("Software\\Mayu\\win11\\emacs", "C-a", "move-beginning-of-line")
          in plan, "registry plan: emacs C-a under HKCU\\Software\\Mayu\\win11")
    check(any(p[0] == "Software\\Mayu\\win11\\apps\\Notepad" and p[1] == "(class)"
              and p[2] == "Notepad" for p in plan),
          "registry plan: Notepad app under apps\\Notepad with (class)")
    check(("Software\\Mayu\\win10\\emacs", "C-a", "move-beginning-of-line")
          in registry_plan(cfg, "win10"), "registry plan honours win10 subtree")
    print("SELFTEST", "PASSED" if ok[0] else "FAILED")
    return 0 if ok[0] else 1


def main(argv):
    ap = argparse.ArgumentParser(description="mayu keyboard remapper")
    ap.add_argument("--config", default="")
    ap.add_argument("--keymap", default="emacs",
                    help="emacs (default) or vim")
    ap.add_argument("--vim", action="store_true", help="shortcut for --keymap vim")
    ap.add_argument("--os", default="", choices=["", "win10", "win11"],
                    help="target registry subtree (default: auto-detect)")
    ap.add_argument("--register", action="store_true",
                    help="only register the bindings into the registry, then exit")
    ap.add_argument("--no-register", action="store_true",
                    help="skip writing the registry; just run the remapper")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    keymap = "vim" if args.vim else args.keymap
    os_name = args.os or detect_os()
    cfg, src = load_config(args.config)
    if not keymap.startswith("vim") and keymap not in cfg["scopes"]:
        keymaps = [k for k in cfg["scopes"] if k not in cfg["apps"]]
        keymap = keymaps[0] if keymaps else keymap
    print("mayu: loaded %s" % src)

    if args.list:
        print_map(cfg, keymap)
        return 0

    # Register the config's key bindings into the Windows registry.  Running the
    # executable IS what writes HKCU\Software\Mayu\<os> - no separate .reg import.
    if not args.no_register:
        n = register_to_registry(cfg, os_name)
        where = "HKEY_CURRENT_USER\\Software\\Mayu\\" + os_name
        if sys.platform == "win32":
            print("mayu: registered %d values into %s (%s)" % (n, where, os_name))
        else:
            print("mayu: would register %d values into %s "
                  "(run on Windows to write the registry)" % (n, where))

    if args.register:
        return 0

    if sys.platform != "win32":
        print("mayu: the live remapper runs on Windows only.")
        print("      use --selftest / --list / --register on this platform.")
        print_map(cfg, keymap)
        return 0

    return run_windows(cfg, keymap)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
