# Comprehensive-ish Emacs-like mapping set (default). Users should override via JSON.
# Keys are keyboard hotkey strings accepted by keyboard.add_hotkey, e.g. "ctrl+n"
DEFAULT_MAPPINGS = {
    # basic movement
    "ctrl+f": "right",
    "ctrl+b": "left",
    "ctrl+n": "down",
    "ctrl+p": "up",
    "ctrl+a": "home",
    "ctrl+e": "end",
    "alt+f": "ctrl+right",
    "alt+b": "ctrl+left",
    "meta+f": "ctrl+right",
    "meta+b": "ctrl+left",
    # word/line/page
    "ctrl+v": "pagedown",
    "alt+v": "pageup",
    "ctrl+o": "enter",
    # editing
    "ctrl+d": "delete",
    "backspace": "backspace",
    "ctrl+k": "shift+end, delete",
    "ctrl+u": "ctrl+z",
    "ctrl+/": "ctrl+z",
    "ctrl+_": "ctrl+z",
    # search
    "ctrl+s": "ctrl+f",
    "ctrl+r": "ctrl+shift+f",
    # kill/yank
    "ctrl+y": "ctrl+v",
    "alt+w": "ctrl+c",
    "ctrl+w": "ctrl+x",
    # rectangle / transpose / exchange (best-effort)
    "ctrl+x r t": "",
    # window and buffer (map to common app commands where possible)
    "ctrl+x o": "alt+tab",
    "ctrl+x 1": "",
    "ctrl+x 2": "",
    # menus (send Alt+letter sequences). Users customize per-app.
    "alt+x": "alt+x",
    "ctrl+g": "",
    # more movement: paragraph or sentence approximations
    "alt+{" : "ctrl+up",
    "alt+}" : "ctrl+down"
}
