以下は、要求どおり「外部入力ファイル（JSON）」を読み、その内容をハッシュ化して Windows レジストリに保存（および読み戻し）する機能を持ち、各アプリケーションごとに Emacs ライクなキーバインドを適用する Python パッケージの最小実装一式です。bin と lib のパッケージ形式で提供します。

注意（必読）
- Windows 専用です（pywin32, keyboard, psutil が必要）。実行時に管理者権限が必要な操作があります（レジストリ書き込みは HKCU なので通常は不要）。
- 実環境で実行する前にソースを確認してください。
- この実装は「メニュー操作や文章移動」をキーバインドで行うため、単純にキーボードイベントを注入します（アプリ側で Alt+... や矢印/ホーム/End 等で操作できる前提）。アプリ固有の UIAutomation での特殊対応は含みませんが、per-application マッピングをサポートします。

ファイル構成（提供するもの）
- setup.py
- bin/emacskeys.py
- lib/emacskeys/__init__.py
- lib/emacskeys/runner.py
- lib/emacskeys/registry_store.py
- lib/emacskeys/config.py
- lib/emacskeys/util.py
- lib/emacskeys/sender.py
- lib/emacskeys/listener.py

以下が各ファイルの内容です。ファイルごとにそのまま保存して使ってください。

1) setup.py
```python
from setuptools import setup, find_packages

setup(
    name="emacskeys_registry",
    version="0.1.0",
    description="Per-app Emacs-like keybindings stored via hashed registry entries",
    packages=find_packages(where="lib"),
    package_dir={"": "lib"},
    entry_points={
        "console_scripts": [
            "emacskeys=emacskeys.runner:main",
        ]
    },
    install_requires=[
        "keyboard>=0.13.5",
        "pywin32>=306",
        "psutil>=5.8.0"
    ],
)
```

2) bin/emacskeys.py
```python
from emacskeys.runner import main

if __name__ == "__main__":
    main()
```

3) lib/emacskeys/__init__.py
```python
__version__ = "0.1.0"
```

4) lib/emacskeys/registry_store.py
```python
import hashlib
import json
import winreg

REG_BASE = r"Software\EmacsKeysRegistry"

def compute_hash_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def store_mapping_file_to_registry(file_path):
    """
    Read JSON mapping file, compute SHA256, store content under HKCU\REG_BASE\<hash> value "data".
    Returns the hash string.
    """
    hs = compute_hash_of_file(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        txt = f.read()
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_BASE + "\\" + hs)
        winreg.SetValueEx(key, "data", 0, winreg.REG_SZ, txt)
        winreg.SetValueEx(key, "source_path", 0, winreg.REG_SZ, file_path)
        winreg.CloseKey(key)
    except Exception as e:
        raise
    return hs

def load_mapping_from_registry_by_hash(hs):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_BASE + "\\" + hs, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, "data")
        winreg.CloseKey(key)
        return json.loads(val)
    except FileNotFoundError:
        return None
    except Exception:
        return None

def list_all_registry_mappings():
    """
    Returns dict: {hash: {data: <dict>, source_path: <str>}}
    """
    out = {}
    try:
        base = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_BASE, 0, winreg.KEY_READ)
    except FileNotFoundError:
        return out
    i = 0
    try:
        while True:
            sub = winreg.EnumKey(base, i)
            i += 1
            try:
                k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_BASE + "\\" + sub, 0, winreg.KEY_READ)
                data, _ = winreg.QueryValueEx(k, "data")
                source, _ = winreg.QueryValueEx(k, "source_path")
                winreg.CloseKey(k)
                try:
                    parsed = json.loads(data)
                except Exception:
                    parsed = None
                out[sub] = {"data": parsed, "source_path": source}
            except Exception:
                pass
            except OSError:
        pass
    try:
        winreg.CloseKey(base)
    except Exception:
        pass
    return out
```

5) lib/emacskeys/config.py
```python
import os
import json
from .registry_store import load_mapping_from_registry_by_hash, list_all_registry_mappings

DEFAULT = {
    "enabled_processes": [],   # empty = all
    "mappings": {},            # global mappings (emacs_key -> send_seq)
    "per_process_mappings": {},# process.exe -> {emacs_key: send_seq}
    "use_low_level_send": True,
    # If registry_hash provided, load mappings from registry; otherwise use file path mapping_file
    "registry_hash": None,
}

def load_config_from_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def load_config(config_path=None, registry_hash=None):
    cfg = DEFAULT.copy()
    # 1) if registry_hash given, try load from registry
    if registry_hash:
        reg = load_mapping_from_registry_by_hash(registry_hash)
        if isinstance(reg, dict):
            cfg.update(reg)
            cfg["registry_hash"] = registry_hash
            return cfg
    # 2) if config_path given and exists, try load file (not registry)
    if config_path and os.path.exists(config_path):
        user = load_config_from_file(config_path)
        if isinstance(user, dict):
            cfg.update(user)
            return cfg
    # 3) else, if any registry mapping exists, pick first
    regs = list_all_registry_mappings()
    if regs:
        # take first available mapping
        first_hash = next(iter(regs.keys()))
        reg = regs[first_hash]["data"]
        if isinstance(reg, dict):
            cfg.update(reg)
            cfg["registry_hash"] = first_hash
            return cfg
    return cfg
```

6) lib/emacskeys/util.py
```python
import win32gui
import win32process
import psutil

def get_foreground_info():
    """
    Return (process_name_lower, window_class_lower, window_title)
    """
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd == 0:
            return None, None, None
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid)
            name = proc.name().lower()
        except Exception:
            name = None
        try:
            cls = win32gui.GetClassName(hwnd).lower()
        except Exception:
            cls = None
        try:
            title = win32gui.GetWindowText(hwnd)
        except Exception:
            title = None
        return name, cls, title
    except Exception:
        return None, None, None
```

7) lib/emacskeys/sender.py
```python
import keyboard
import ctypes
import time

# Minimal low-level send using SendInput for certain named keys; else fallback to keyboard.send

SendInput = ctypes.windll.user32.SendInput

PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

VK = {
    "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "home": 0x24, "end": 0x23, "delete": 0x2E, "backspace": 0x08,
    "pagedown": 0x22, "pageup": 0x21, "enter": 0x0D, "tab": 0x09
}

def _press_vk(vk):
    # key down
    ki = KeyBdInput(vk, 0, 0, 0, None)
    inp = Input(1, Input_I(ki))
    SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

def _release_vk(vk):
    ki = KeyBdInput(vk, 0, 0x0002, 0, None)
    inp = Input(1, Input_I(ki))
    SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

def send_low_level_single(keyname):
    k = keyname.lower()
    if k in VK:
        vk = VK[k]
        _press_vk(vk)
        time.sleep(0.01)
        _release_vk(vk)
        time.sleep(0.01)
        return True
    return False

def send_sequence(seq, use_low_level=True):
    """
    seq: a string, e.g. "ctrl+right" or "shift+end, delete" or "alt+f"
    Comma-separated actions are processed sequentially.
    """
    parts = [p.strip() for p in seq.split(",") if p.strip()]
    for part in parts:
        # if simple single key recognized and low-level desired -> use SendInput
        if use_low_level and "+" not in part and part.lower() in VK:
            ok = send_low_level_single(part)
            if ok:
                continue
        # otherwise use keyboard.send for complex combos
        try:
            keyboard.send(part)
        except Exception:
            pass
        time.sleep(0.01)
```

8) lib/emacskeys/listener.py
```python
import keyboard
import threading
import time
from .util import get_foreground_info
from .config import load_config
from .sender import send_sequence
from .mappings_fallback import DEFAULT_MAPPINGS  # defined below or you can inline

# Simple fallback mappings if not provided by config
try:
    from .mappings_fallback import DEFAULT_MAPPINGS
except Exception:
    DEFAULT_MAPPINGS = {
        "ctrl+n": "down",
        "ctrl+p": "up",
        "ctrl+f": "right",
        "ctrl+b": "left",
        "ctrl+a": "home",
        "ctrl+e": "end",
        "ctrl+k": "shift+end, delete",
        "alt+f": "ctrl+right",
        "alt+b": "ctrl+left",
    }

class KeyMapper:
    def __init__(self, config_path=None, registry_hash=None):
        self.cfg = load_config(config_path=config_path, registry_hash=registry_hash)
        # prepare mappings
        self.global_mappings = DEFAULT_MAPPINGS.copy()
        self.global_mappings.update(self.cfg.get("mappings", {}) or {})
        # per-process: merge with global
        self.per_process = {}
        for proc, mapd in (self.cfg.get("per_process_mappings") or {}).items():
            mm = self.global_mappings.copy()
            mm.update(mapd or {})
            self.per_process[proc.lower()] = mm
        self.enabled_processes = [p.lower() for p in (self.cfg.get("enabled_processes") or [])]
        self.use_low_level = bool(self.cfg.get("use_low_level_send", True))
        self._hotkey_ids = []
        self._stop = threading.Event()
        self._install_hotkeys()

    def _is_enabled_for(self, proc_name):
        if proc_name is None:
            return False
        if not self.enabled_processes:
            return True
        return proc_name in self.enabled_processes

    def _lookup(self, proc_name):
        if proc_name and proc_name in self.per_process:
            return self.per_process[proc_name]
        return self.global_mappings

    def _install_hotkeys(self):
        # collect keyset
        keys = set(self.global_mappings.keys())
        for pm in self.per_process.values():
            keys.update(pm.keys())
        # register
        for k in keys:
            try:
                hid = keyboard.add_hotkey(k, lambda key=k: self._handler(key), suppress=True)
                self._hotkey_ids.append(hid)
            except Exception:
                try:
                    hid = keyboard.add_hotkey(k, lambda key=k: self._handler(key), suppress=False)
                    self._hotkey_ids.append(hid)
                except Exception:
                    pass

    def _handler(self, emacs_key):
        proc, cls, title = get_foreground_info()
        if not self._is_enabled_for(proc):
            # pass-through: re-inject original combo
            try:
                keyboard.press_and_release(emacs_key)
            except Exception:
                pass
            return
        mapping = self._lookup(proc)
        seq = mapping.get(emacs_key)
        if seq is None:
            # not mapped: pass through
            try:
                keyboard.press_and_release(emacs_key)
            except Exception:
                pass
            return
        if seq == "":
            # explicit no-op
            return
        # send mapped sequence
        send_sequence(seq, use_low_level=self.use_low_level)

    def start(self):
        self._stop.clear()
        # watcher thread to keep process alive and allow future reload hooks
        t = threading.Thread(target=self._watcher, daemon=True)
        t.start()

    def stop(self):
        self._stop.set()
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass

    def _watcher(self):
        while not self._stop.is_set():
            time.sleep(1)
```

(補助) もし mappings_fallback.py を別ファイルにしたい場合は下記を保存してください。必須ではありません。

lib/emacskeys/mappings_fallback.py
```python
DEFAULT_MAPPINGS = {
    "ctrl+n": "down",
    "ctrl+p": "up",
    "ctrl+f": "right",
    "ctrl+b": "left",
    "ctrl+a": "home",
    "ctrl+e": "end",
    "ctrl+k": "shift+end, delete",
    "alt+f": "ctrl+right",
    "alt+b": "ctrl+left",
}
```

9) lib/emacskeys/runner.py
```python
import argparse
import sys
import time
from .listener import KeyMapper
from .registry_store import store_mapping_file_to_registry, list_all_registry_mappings

def main():
    parser = argparse.ArgumentParser(description="Emacs-like per-app keybindings (registry-backed)")
    parser.add_argument("--config-file", "-f", help="External JSON mapping file to import to registry", default=None)
    parser.add_argument("--registry-hash", "-r", help="Registry mapping hash to load", default=None)
    parser.add_argument("--list-registry", action="store_true", help="List stored mappings in registry")
    args = parser.parse_args()

    if args.config_file:
        try:
            h = store_mapping_file_to_registry(args.config_file)
            print("Stored mapping to registry with hash:", h)
        except Exception as e:
            print("Failed to store mapping:", e)
        return

    if args.list_registry:
        regs = list_all_registry_mappings()
        if not regs:
            print("No mappings in registry.")
            return
        for hs, info in regs.items():
            print("Hash:", hs, "source:", info.get("source_path"))
        return

    mapper = KeyMapper(config_path=None, registry_hash=args.registry_hash)
    try:
        print("Starting Emacs key mapper. Press Ctrl+C to exit.")
        mapper.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        mapper.stop()
        sys.exit(0)
```

使い方（簡潔）
- 依存ライブラリをインストール:
  - pip install keyboard pywin32 psutil
- パッケージを配置してインストール（任意）:
  - pip install -e .
- 外部 JSON マッピングファイルをレジストリに投入（ハッシュキー保存）:
  - python -m emacskeys.runner --config-file path\to\mappings.json
  - 出力されるハッシュ値を控える。
- 実行（レジストリのハッシュを指定して読み込ませる）:
  - python -m emacskeys.runner --registry-hash <hash>
- あるいは、レジストリに保存された最初のマッピングが自動で読み込まれます。

外部マッピング JSON 形式（例）
```json
{
    "enabled_processes": ["notepad.exe", "code.exe", "chrome.exe"],
  "mappings": {
      "ctrl+n": "down",
      "ctrl+p": "up",
      "ctrl+f": "right",
      "ctrl+b": "left",
      "ctrl+a": "home",
      "ctrl+e": "end",
      "alt+f": "ctrl+right",
      "alt+b": "ctrl+left",
      "ctrl+k": "shift+end, delete",
    "ctrl+g": ""
  },
  "per_process_mappings": {
    "code.exe": {
        "ctrl+s": "ctrl+s",
      "ctrl+n": "ctrl+n"
    },
    "chrome.exe": {
      "ctrl+s": "ctrl+s"
    }
  },
  "use_low_level_send": true
}
```

補足
- Menu 操作も Alt+<letter> などを送れば動きます。上のマッピングでメニューを操作したい場合は "alt+f" や "alt+f, t" のように指定してください。
- レジストリは HKCU\Software\EmacsKeysRegistry\<sha256> に JSON テキストを保存します。削除や管理は list_all_registry_mappings を参考に実装できます。

必要なら、次を提供できます：
- レジストリ内のマッピングをGUIで一覧・編集する小ツール
- アプリ固有（VSCode/Chrome）向けに UIAutomation を用いたフォーカス/入力可能判定機能

どれを追加しますか？
