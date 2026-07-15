#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mayu - a WORKING 窓使いの憂鬱 keyboard remapper for Windows 10 / 11.

Unlike the .reg files (which only *store* the configuration), this program is
the resident agent that actually makes the key bindings work: it installs a
low-level keyboard hook, watches every keystroke, and rewrites the Emacs / vim
chords from `keybindings.mayu` into real keystrokes in whatever application has
focus - Notepad, browsers, editors, anything.

Pure Python standard library (ctypes) - no third-party packages, no admin.

    python mayu_agent.py                 # run the remapper (Windows)
    python mayu_agent.py --keymap vim-normal
    python mayu_agent.py --config my.mayu
    python mayu_agent.py --selftest      # verify parsing/translation (any OS)
    python mayu_agent.py --list          # print the resolved key map and quit

Emacs bindings work everywhere because each symbolic command maps to the
Windows keystroke that does the same thing (C-a -> Home, C-k -> Shift+End then
Cut, C-f -> Right, ...).  Edit keybindings.mayu to change them.
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
  key C-s -> isearch-forward
  key M-f -> forward-word
  key M-b -> backward-word
  key C-g -> keyboard-quit
  key C-v -> scroll-up
  key M-v -> scroll-down
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
app "Explorer" {
  class CabinetWClass
  base vim-normal
  key j -> send Down
  key k -> send Up
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
            # window "Name" : base {
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
    """Translate an action into ('keys', [chords]) or ('type', text)."""
    action = action.strip()
    if action.startswith("send "):
        return ("keys", action[5:].split())
    if action.startswith("type "):
        return ("type", _quoted(action) or action[5:].strip())
    if action.startswith("exec "):
        return ("exec", _quoted(action) or action[5:].strip())
    if action in COMMAND_KEYS:
        return ("keys", list(COMMAND_KEYS[action]))
    # a raw chord like "C-Tab" used directly
    return ("keys", [action])


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
    """'C-a' -> ({'C'}, 'a').  Unknown -> (mods, rawkey)."""
    mods = set()
    s = chord
    while len(s) >= 2 and s[1] == "-" and s[0] in MODVK:
        mods.add(s[0])
        s = s[2:]
    return mods, s


# --------------------------------------------------------------------------
# Windows low-level keyboard hook (only imported/used on win32).
# --------------------------------------------------------------------------
def run_windows(cfg, default_keymap):
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    WH_KEYBOARD_LL = 13
    WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
    WM_SYSKEYDOWN, WM_SYSKEYUP = 0x0104, 0x0105
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004
    MAGIC = 0x1A2B3C4D            # tags our own injected events
    HC_ACTION = 0

    ULONG_PTR = wintypes.WPARAM

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
        # release whatever real modifiers are physically down first
        for mv in (0x11, 0x12, 0x10, 0x5B, 0x5C):
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

    # precompute the app scopes' class -> merged keymap
    app_maps = []
    for name, meta in cfg["apps"].items():
        if meta.get("class"):
            app_maps.append((meta["class"], effective(cfg, name)))
    base_map = effective(cfg, default_keymap)

    def active_map():
        cls = foreground_class()
        for klass, m in app_maps:
            if klass and klass in cls:
                return m
        return base_map

    GetAsyncKeyState = user32.GetAsyncKeyState

    def down(vk):
        return GetAsyncKeyState(vk) & 0x8000

    rev = {v: k for k, v in VK.items()}
    pending = {"prefix": None, "ts": 0.0}

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
        # shift is only meaningful for non-letter keys here
        if down(0x10) and not (0x41 <= vk <= 0x5A) and not (0x30 <= vk <= 0x39):
            pre += "S-"
        return pre + base

    HOOKPROC = ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_int,
                                wintypes.WPARAM, wintypes.LPARAM)

    def do_action(action):
        kind, val = action_to_keys(action)
        if kind == "keys":
            send_keys(val)
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
            # ignore lone modifier presses
            if vk in (0x10, 0x11, 0x12, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5,
                      0x5B, 0x5C):
                return user32.CallNextHookEx(None, nCode, wParam, lParam)
            chord = chord_from(vk)
            if chord:
                amap = active_map()
                # two-stroke handling
                now = time.time()
                if pending["prefix"] and now - pending["ts"] < 1.0:
                    combo = pending["prefix"] + " " + chord
                    pending["prefix"] = None
                    if combo in amap:
                        do_action(amap[combo])
                        return 1
                pending["prefix"] = None
                # is this chord the start of a two-stroke binding?
                if any(k.startswith(chord + " ") for k in amap):
                    pending["prefix"] = chord
                    pending["ts"] = now
                    return 1
                if chord in amap:
                    do_action(amap[chord])
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

    print("mayu is running - keymap '%s' active." % default_keymap)
    print("Emacs/vim keys now work in every application. Ctrl-C here to stop.")
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
# config loading + entry point
# --------------------------------------------------------------------------
def load_config(path):
    import os
    candidates = []
    if path:
        candidates.append(path)
    here = os.path.dirname(os.path.abspath(sys.argv[0]))
    candidates += [os.path.join(here, "keybindings.mayu"), "keybindings.mayu"]
    for c in candidates:
        try:
            with open(c, "r", encoding="utf-8") as f:
                return parse_mayu(f.read()), c
        except OSError:
            continue
    return parse_mayu(DEFAULT_MAYU), "(built-in default)"


def print_map(cfg, keymap):
    m = effective(cfg, keymap)
    print("keymap '%s':" % keymap)
    for chord in sorted(m):
        kind, val = action_to_keys(m[chord])
        rhs = " ".join(val) if isinstance(val, list) else repr(val)
        print("  %-10s -> %-22s => %s [%s]" % (chord, m[chord], rhs, kind))


def selftest():
    cfg = parse_mayu(DEFAULT_MAYU)
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(("  ok   " if cond else "  FAIL ") + msg)
        ok = ok and cond

    em = effective(cfg, "emacs")
    check(em.get("C-a") == "move-beginning-of-line", "emacs C-a parsed")
    check(action_to_keys("move-beginning-of-line") == ("keys", ["Home"]),
          "C-a -> Home")
    check(action_to_keys("kill-line") == ("keys", ["S-End", "C-x"]),
          "kill-line -> Shift+End, Cut")
    check(parse_chord("C-a") == ({"C"}, "a"), "chord C-a")
    check(parse_chord("M-f") == ({"M"}, "f"), "chord M-f")
    check(VK["a"] == 0x41 and VK["Home"] == 0x24, "VK table")
    ex = effective(cfg, "Explorer")
    check(ex.get("j") == "send Down", "app Explorer j -> send Down")
    check(action_to_keys("send Down") == ("keys", ["Down"]), "send passthrough")
    # two-stroke present
    check("C-x C-s" in em, "two-stroke C-x C-s present")
    print("SELFTEST", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


def main(argv):
    ap = argparse.ArgumentParser(description="mayu keyboard remapper")
    ap.add_argument("--config", default="")
    ap.add_argument("--keymap", default="emacs")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    cfg, src = load_config(args.config)
    if args.keymap not in cfg["scopes"]:
        # fall back to the first keymap defined
        keymaps = [k for k in cfg["scopes"] if k not in cfg["apps"]]
        args.keymap = keymaps[0] if keymaps else args.keymap
    print("mayu: loaded %s" % src)

    if args.list:
        print_map(cfg, args.keymap)
        return 0

    if sys.platform != "win32":
        print("mayu: the live remapper runs on Windows only.")
        print("      use --selftest / --list on this platform.")
        print_map(cfg, args.keymap)
        return 0

    return run_windows(cfg, args.keymap)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
