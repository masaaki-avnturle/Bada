#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
madokey.py — 窓使いのキー (MadoKey)
================================================================================
奈由太氏の「窓使いの憂鬱」へのオマージュ。設定ファイル (madokey.mayu) に書いた
キーバインドを常駐で待ち受け、前面のアプリ (Word / Excel / LibreOffice Writer /
Calc) を自動判定して、ルビ付け・合計・コピー・任意コマンドを「ひと押し」で
送り込みます。

使い方:
    pip install -r requirements.txt          # pynput (必須), pywin32 (Windows)
    python madokey.py                         # madokey.mayu を読み込み常駐
    python madokey.py -c my.mayu              # 別の設定ファイル
    python madokey.py --check                 # 設定を解析して一覧表示 (常駐しない)
    python madokey.py --emit-ahk out.ahk      # AutoHotkey v1 スクリプトを書き出し

設計:
  * キー入力の待ち受けは pynput。Ctrl+Alt+<X> 系の組み合わせを使うので、
    アプリ本来のキーを奪いません (サプレス不要)。
  * 前面アプリの判定:
      - Windows: 前面ウィンドウのプロセス名 (WINWORD/EXCEL/soffice) + タイトル。
      - Linux  : xdotool / wmctrl でアクティブ ウィンドウ名を取得。
  * アクションの実行:
      - copy/cut/paste/keys/text : キー送出 (pynput) — 追加設定なしでどこでも動作。
      - sum(Excel)               : Alt+= (オート SUM) を送出。
      - mso <IdMso>              : Windows で Word/Excel を COM 取得し
                                   Application.CommandBars.ExecuteMso を実行。
      - uno <.uno:Cmd> / sum(Calc)/ruby(Writer):
                                   起動中の LibreOffice に UNO 接続して dispatch。
                                   (soffice を --accept="socket,host=localhost,port=2002;urp;"
                                    付きで起動しておくと確実。未接続時はキー送出に代替。)
  * pynput / pywin32 / uno が無い環境でも import は失敗せず、--check と
    --emit-ahk は動作します (常駐実行時に必要な依存だけ後から要求)。
================================================================================
"""

import argparse
import os
import re
import subprocess
import sys
import time

# ---- 任意依存 (無くても --check / --emit-ahk は動く) ------------------------
try:
    from pynput import keyboard
    from pynput.keyboard import Key, Controller
except Exception:                      # pragma: no cover - 実行時のみ必要
    keyboard = None
    Key = None
    Controller = None

IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

# ============================================================================
#  設定ファイルの解析
# ============================================================================
MODS = {"ctrl", "control", "alt", "shift", "win", "super", "cmd", "meta"}
_MOD_CANON = {"control": "ctrl", "super": "win", "cmd": "win", "meta": "win"}


class Bind(object):
    __slots__ = ("mods", "key", "app", "action", "arg", "combo")

    def __init__(self, mods, key, app, action, arg, combo):
        self.mods = mods          # frozenset of {"ctrl","alt","shift","win"}
        self.key = key            # normalized key name, lowercase (e.g. "c","f5")
        self.app = app            # "word"/"excel"/"writer"/"calc"/"any"
        self.action = action      # "copy"/"sum"/"ruby"/"mso"/"uno"/"keys"/"text"/"run"/"reload"/"quit"
        self.arg = arg            # string argument (may be "")
        self.combo = combo        # canonical combo string, e.g. "ctrl+alt+c"

    def __repr__(self):
        a = (" " + self.arg) if self.arg else ""
        return "%s @%s = %s%s" % (self.combo, self.app, self.action, a)


def _norm_token(tok):
    t = tok.strip().lower()
    return _MOD_CANON.get(t, t)


def parse_combo(spec):
    """'Ctrl+Alt+R' -> (frozenset({'ctrl','alt'}), 'r', 'ctrl+alt+r')."""
    parts = [p for p in re.split(r"\s*\+\s*", spec.strip()) if p]
    if not parts:
        raise ValueError("empty key spec")
    mods = set()
    key = None
    for p in parts:
        t = _norm_token(p)
        if t in MODS:
            mods.add(_MOD_CANON.get(t, t))
        else:
            key = t
    if key is None:
        raise ValueError("no non-modifier key in '%s'" % spec)
    canon = "+".join([m for m in ("ctrl", "alt", "shift", "win") if m in mods] + [key])
    return frozenset(mods), key, canon


def parse_config(text):
    """Return (list[Bind], list[str] errors)."""
    binds, errors = [], []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if not line.lower().startswith("bind"):
            errors.append("line %d: 'bind' で始まっていません: %s" % (lineno, raw.strip()))
            continue
        body = line[4:].strip()
        if "=" not in body:
            errors.append("line %d: '=' がありません" % lineno)
            continue
        left, right = body.split("=", 1)
        left, right = left.strip(), right.strip()
        # @app の抽出
        app = "any"
        m = re.search(r"@(\w+)", left)
        if m:
            app = m.group(1).lower()
            left = left[:m.start()].strip() + left[m.end():].strip()
        if app not in ("any", "word", "excel", "writer", "calc"):
            errors.append("line %d: 未知の対象 @%s" % (lineno, app))
            continue
        try:
            mods, key, combo = parse_combo(left)
        except ValueError as e:
            errors.append("line %d: %s" % (lineno, e))
            continue
        rparts = right.split(None, 1)
        action = rparts[0].lower()
        arg = rparts[1].strip() if len(rparts) > 1 else ""
        if action not in ("ruby", "sum", "copy", "cut", "paste",
                           "mso", "uno", "keys", "text", "run", "reload", "quit"):
            errors.append("line %d: 未知のアクション '%s'" % (lineno, action))
            continue
        binds.append(Bind(mods, key, app, action, arg, combo))
    return binds, errors


# ============================================================================
#  前面アプリの判定
# ============================================================================
def _linux_active_title():
    for cmd in (["xdotool", "getactivewindow", "getwindowname"],
                ["sh", "-c", "xprop -id $(xprop -root _NET_ACTIVE_WINDOW | grep -o '0x[0-9a-f]*') WM_NAME"]):
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=1.5)
            return out.decode("utf-8", "replace")
        except Exception:
            continue
    return ""


def _win_active():
    try:
        import win32gui
        import win32process
        import psutil
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd) or ""
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        pname = ""
        try:
            pname = psutil.Process(pid).name()
        except Exception:
            pass
        return pname, title
    except Exception:
        return "", ""


def detect_app():
    """Return one of 'word'/'excel'/'writer'/'calc'/'other'."""
    if IS_WIN:
        pname, title = _win_active()
        p = (pname or "").lower()
        t = (title or "").lower()
        if "winword" in p:
            return "word"
        if "excel" in p:
            return "excel"
        if "soffice" in p or "libreoffice" in p:
            if "calc" in t:
                return "calc"
            if "writer" in t:
                return "writer"
            return "writer"
        # フォールバックはタイトルで推定
        if "word" in t:
            return "word"
        if "excel" in t:
            return "excel"
        if "calc" in t:
            return "calc"
        if "writer" in t:
            return "writer"
        return "other"
    # Linux / mac
    t = _linux_active_title().lower()
    if "libreoffice calc" in t or " - calc" in t or "calc" in t and "libre" in t:
        return "calc"
    if "libreoffice writer" in t or " - writer" in t or ("writer" in t and "libre" in t):
        return "writer"
    if "microsoft word" in t or " - word" in t:
        return "word"
    if "microsoft excel" in t or " - excel" in t:
        return "excel"
    if "calc" in t:
        return "calc"
    if "writer" in t:
        return "writer"
    return "other"


# ============================================================================
#  アクションの実行
# ============================================================================
_KEYMAP = {
    "space": "space", "enter": "enter", "return": "enter", "tab": "tab",
    "esc": "esc", "escape": "esc", "backspace": "backspace", "delete": "delete",
    "del": "delete", "home": "home", "end": "end", "up": "up", "down": "down",
    "left": "left", "right": "right", "=": "=", "-": "-",
}


def _pk(name):
    """Map a token to a pynput key object or a single character."""
    if Key is None:
        return None
    name = name.lower()
    special = {
        "ctrl": Key.ctrl, "alt": Key.alt, "shift": Key.shift,
        "win": (Key.cmd if hasattr(Key, "cmd") else Key.ctrl),
        "space": Key.space, "enter": Key.enter, "return": Key.enter,
        "tab": Key.tab, "esc": Key.esc, "escape": Key.esc,
        "backspace": Key.backspace, "delete": Key.delete,
        "home": Key.home, "end": Key.end, "up": Key.up, "down": Key.down,
        "left": Key.left, "right": Key.right,
    }
    if name in special:
        return special[name]
    if re.fullmatch(r"f([1-9]|1[0-9]|2[0-4])", name):
        return getattr(Key, name)
    return name  # single character


class Emitter(object):
    def __init__(self):
        self._c = Controller() if Controller else None

    def tap_combo(self, spec):
        """Emit a chord like 'ctrl+c' or 'alt+='. Releases held mods first."""
        if not self._c:
            return
        mods, key, _ = parse_combo(spec)
        order = [m for m in ("ctrl", "alt", "shift", "win") if m in mods]
        held = [_pk(m) for m in order]
        target = _pk(key)
        for h in held:
            self._c.press(h)
        try:
            self._c.press(target)
            self._c.release(target)
        finally:
            for h in reversed(held):
                self._c.release(h)

    def type_text(self, s):
        if self._c and s:
            self._c.type(s)

    def release_all_mods(self):
        if not self._c:
            return
        for m in ("ctrl", "alt", "shift", "win"):
            try:
                self._c.release(_pk(m))
            except Exception:
                pass


# ---- Windows: Word/Excel の COM (ExecuteMso) --------------------------------
def _com_app(kind):
    """kind in {'word','excel'} -> running Application COM object, or None."""
    try:
        import win32com.client as w
    except Exception:
        return None
    prog = "Word.Application" if kind == "word" else "Excel.Application"
    try:
        return w.GetActiveObject(prog)
    except Exception:
        return None


def do_mso(kind, idmso):
    app = _com_app(kind if kind in ("word", "excel") else "word")
    if app is None:
        return False
    try:
        app.CommandBars.ExecuteMso(idmso)
        return True
    except Exception:
        return False


# ---- LibreOffice: UNO dispatch ----------------------------------------------
_UNO_CTX = {"desktop": None}


def _uno_desktop():
    if _UNO_CTX["desktop"] is not None:
        return _UNO_CTX["desktop"]
    try:
        import uno
        from com.sun.star.beans import PropertyValue  # noqa: F401
        localContext = uno.getComponentContext()
        resolver = localContext.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", localContext)
        ctx = resolver.resolve(
            "uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
        smgr = ctx.ServiceManager
        desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
        _UNO_CTX["desktop"] = desktop
        return desktop
    except Exception:
        _UNO_CTX["desktop"] = None
        return None


def do_uno(cmd):
    desktop = _uno_desktop()
    if desktop is None:
        return False
    try:
        import uno
        model = desktop.getCurrentComponent()
        frame = model.getCurrentController().getFrame()
        smgr = uno.getComponentContext().ServiceManager
        dispatcher = smgr.createInstanceWithContext(
            "com.sun.star.frame.DispatchHelper", uno.getComponentContext())
        dispatcher.executeDispatch(frame, cmd, "", 0, ())
        return True
    except Exception:
        return False


class Executor(object):
    """Resolve a Bind into a concrete effect for the currently focused app."""

    def __init__(self, emitter, on_reload, on_quit):
        self.e = emitter
        self.on_reload = on_reload
        self.on_quit = on_quit

    def run(self, b, app_now):
        a = b.action
        if a == "reload":
            self.on_reload()
            return
        if a == "quit":
            self.on_quit()
            return
        if a == "copy":
            self.e.tap_combo("ctrl+c")
            return
        if a == "cut":
            self.e.tap_combo("ctrl+x")
            return
        if a == "paste":
            self.e.tap_combo("ctrl+v")
            return
        if a == "keys":
            self.e.release_all_mods()
            self.e.tap_combo(b.arg)
            return
        if a == "text":
            self.e.release_all_mods()
            self.e.type_text(b.arg)
            return
        if a == "run":
            try:
                subprocess.Popen(b.arg, shell=True)
            except Exception as ex:
                print("run failed:", ex)
            return
        if a == "mso":
            if not do_mso(app_now, b.arg):
                print("mso %s: 実行できません (Word/Excel が必要)" % b.arg)
            return
        if a == "uno":
            if not do_uno(b.arg):
                # UNO 未接続ならキーへ代替はできないので通知のみ
                print("uno %s: LibreOffice に接続できません" % b.arg)
            return
        if a == "ruby":
            self._ruby(app_now)
            return
        if a == "sum":
            self._sum(app_now)
            return

    def _ruby(self, app_now):
        if app_now == "word":
            if not do_mso("word", "PhoneticGuide"):
                print("ルビ: Word を取得できません")
        elif app_now == "excel":
            if not do_mso("excel", "PhoneticShowOrHide"):
                print("ルビ: Excel を取得できません")
        elif app_now == "writer":
            if not do_uno(".uno:RubyDialog"):
                print("ルビ: LibreOffice Writer に接続できません")
        else:
            print("ルビ: 対応アプリ (Word/Excel/Writer) が前面にありません")

    def _sum(self, app_now):
        if app_now == "excel":
            self.e.release_all_mods()
            self.e.tap_combo("alt+=")            # オート SUM
        elif app_now == "calc":
            if not do_uno(".uno:AutoSum"):
                print("合計: LibreOffice Calc に接続できません")
        else:
            print("合計: Excel / Calc が前面にありません")


# ============================================================================
#  常駐ループ (pynput)
# ============================================================================
class Daemon(object):
    def __init__(self, cfg_path):
        self.cfg_path = cfg_path
        self.binds = []
        self.by_combo = {}
        self.emitter = None
        self.executor = None
        self._stop = False
        self._pressed = set()

    def load(self):
        with open(self.cfg_path, "r", encoding="utf-8") as f:
            text = f.read()
        binds, errors = parse_config(text)
        for e in errors:
            print("設定エラー:", e)
        self.binds = binds
        self.by_combo = {}
        for b in binds:
            self.by_combo.setdefault(b.combo, []).append(b)
        print("MadoKey: %d 個のバインドを読み込みました (%s)" %
              (len(binds), os.path.basename(self.cfg_path)))
        for b in binds:
            print("   ", b)

    def _pick(self, combo, app_now):
        cands = self.by_combo.get(combo, [])
        if not cands:
            return None
        for b in cands:
            if b.app == app_now:
                return b
        for b in cands:
            if b.app == "any":
                return b
        return cands[0]

    # -- key event handling ---------------------------------------------------
    _MOD_KEYS = {
        "ctrl", "alt", "shift", "win",
    }

    def _canon_key(self, k):
        """pynput key -> token string, or None to ignore."""
        if Key is not None and isinstance(k, Key):
            name = str(k).replace("Key.", "")
            if name in ("ctrl_l", "ctrl_r", "ctrl"):
                return "ctrl"
            if name in ("alt_l", "alt_r", "alt_gr", "alt"):
                return "alt"
            if name in ("shift_l", "shift_r", "shift"):
                return "shift"
            if name in ("cmd", "cmd_l", "cmd_r"):
                return "win"
            return name
        # KeyCode
        try:
            ch = k.char
        except Exception:
            ch = None
        if ch is None:
            return None
        return ch.lower()

    def _current_combo(self, key_token):
        mods = [m for m in ("ctrl", "alt", "shift", "win") if m in self._pressed]
        return "+".join(mods + [key_token])

    def on_press(self, k):
        tok = self._canon_key(k)
        if tok is None:
            return
        if tok in ("ctrl", "alt", "shift", "win"):
            self._pressed.add(tok)
            return
        combo = self._current_combo(tok)
        b = self._pick(combo, detect_app())
        if b is None:
            return
        app_now = detect_app()
        try:
            self.executor.run(b, app_now)
        except Exception as ex:
            print("実行エラー:", ex)

    def on_release(self, k):
        tok = self._canon_key(k)
        if tok in ("ctrl", "alt", "shift", "win"):
            self._pressed.discard(tok)
        if self._stop:
            return False

    def reload(self):
        try:
            self.load()
        except Exception as ex:
            print("再読込に失敗:", ex)

    def quit(self):
        print("MadoKey を終了します。")
        self._stop = True
        try:
            self._listener.stop()
        except Exception:
            pass

    def run(self):
        if keyboard is None:
            print("pynput が見つかりません。'pip install -r requirements.txt' を実行してください。")
            return 2
        self.load()
        self.emitter = Emitter()
        self.executor = Executor(self.emitter, self.reload, self.quit)
        print("待ち受け開始。Ctrl+Alt+F12 で終了。")
        with keyboard.Listener(on_press=self.on_press,
                               on_release=self.on_release) as self._listener:
            self._listener.join()
        return 0


# ============================================================================
#  AutoHotkey v1 へのエクスポート (Windows で Python 無しでも使える)
# ============================================================================
_AHK_MODS = {"ctrl": "^", "alt": "!", "shift": "+", "win": "#"}


def _ahk_hotkey(b):
    pre = "".join(_AHK_MODS[m] for m in ("ctrl", "alt", "shift", "win") if m in b.mods)
    return pre + b.key


def _ahk_action(b):
    a = b.action
    if a == "copy":
        return "SendInput ^c"
    if a == "cut":
        return "SendInput ^x"
    if a == "paste":
        return "SendInput ^v"
    if a == "keys":
        # 'Ctrl+Shift+V' -> '^+v'
        mods, key, _ = parse_combo(b.arg)
        pre = "".join(_AHK_MODS[m] for m in ("ctrl", "alt", "shift", "win") if m in mods)
        return "SendInput " + pre + "{" + key + "}"
    if a == "text":
        safe = b.arg.replace("`", "``").replace("\n", "`n")
        return "SendInput {Raw}" + safe
    if a == "run":
        return "Run, " + b.arg
    if a == "sum":
        return "SendInput !="  # Excel オート SUM
    if a == "ruby":
        return "MadoKeyMso(\"PhoneticGuide\")"
    if a == "mso":
        return "MadoKeyMso(\"" + b.arg + "\")"
    if a == "uno":
        return "; uno は Windows AHK では未対応: " + b.arg
    if a == "reload":
        return "Reload"
    if a == "quit":
        return "ExitApp"
    return "; (未対応) " + a


def emit_ahk(binds):
    out = []
    out.append("; madokey.ahk — MadoKey が madokey.mayu から生成 (AutoHotkey v1)")
    out.append("; Word/Excel の #IfWinActive で対象を切替。ExecuteMso は COM 経由。")
    out.append("#NoEnv")
    out.append("#SingleInstance force")
    out.append("SendMode Input")
    out.append("")
    out.append("MadoKeyMso(id) {")
    out.append("    try {")
    out.append("        app := ComObjActive(\"Word.Application\")")
    out.append("    } catch {")
    out.append("        try {")
    out.append("            app := ComObjActive(\"Excel.Application\")")
    out.append("        } catch {")
    out.append("            return")
    out.append("        }")
    out.append("    }")
    out.append("    try app.CommandBars.ExecuteMso(id)")
    out.append("}")
    out.append("")
    win = {"word": "ahk_exe WINWORD.EXE", "excel": "ahk_exe EXCEL.EXE",
           "writer": "ahk_exe soffice.bin", "calc": "ahk_exe soffice.bin"}
    # group by app scope
    for scope in ("any", "word", "excel", "writer", "calc"):
        group = [b for b in binds if b.app == scope]
        if not group:
            continue
        if scope != "any":
            out.append("#IfWinActive, " + win[scope])
        for b in group:
            out.append(_ahk_hotkey(b) + "::" + _ahk_action(b))
        if scope != "any":
            out.append("#IfWinActive")
        out.append("")
    return "\n".join(out) + "\n"


# ============================================================================
#  エントリポイント
# ============================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(description="MadoKey — 窓使いのキー")
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("-c", "--config", default=os.path.join(here, "madokey.mayu"),
                    help="設定ファイル (.mayu)")
    ap.add_argument("--check", action="store_true", help="設定を解析して一覧表示 (常駐しない)")
    ap.add_argument("--emit-ahk", metavar="OUT", help="AutoHotkey v1 スクリプトを書き出す")
    args = ap.parse_args(argv)

    if not os.path.exists(args.config):
        print("設定ファイルが見つかりません:", args.config)
        return 2

    with open(args.config, "r", encoding="utf-8") as f:
        text = f.read()
    binds, errors = parse_config(text)
    for e in errors:
        print("設定エラー:", e)

    if args.emit_ahk:
        with open(args.emit_ahk, "w", encoding="utf-8") as f:
            f.write(emit_ahk(binds))
        print("AutoHotkey スクリプトを書き出しました:", args.emit_ahk)
        return 0 if not errors else 1

    if args.check:
        print("MadoKey 設定チェック: %d 個のバインド" % len(binds))
        for b in binds:
            print("   ", b)
        return 0 if not errors else 1

    return Daemon(args.config).run()


if __name__ == "__main__":
    sys.exit(main())
