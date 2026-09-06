以下は、要求どおり「外部入力ファイル（アプリごとのキーバインドを記述した JSON）を SHA256 ハッシュで HKCU レジストリに保存し、レジストリのマッピングを読み出して各アプリケーションに対して Emacs の主要なキーバインドでメニュー操作・文章移動ができるようにする」Python パッケージの完全なソースコード一式です。bin と lib パッケージ形式で提供します。

注意（必読）
- Windows 専用（winreg / pywin32 は HKCU 操作で標準ライブラリのみで動きますが `keyboard`, `psutil` は必要です）。
- レジストリへは HKCU\Software\EmacsKeysRegistry\<sha256> に JSON テキストを保存します（値名 "data", "source_path"）。
- 管理者権限は不要（HKCU に書くため）ですが、キーボードフックのため実行はユーザー権限で行ってください。
- 「Emacsの全てのキーバインド」を完全再現することは現実的に困難なため、下に用意した `mappings.py` は Emacs の主要コマンド群（移動、編集、検索、ウィンドウ操作、矩形操作の代表、メニュー操作に相当する Alt 系など）を幅広くカバーします。必要に応じて JSON で上書き・拡張してください。
- 実行前に必ずコードと外部マッピングを確認してください。

ファイル構成（作成してください）
- setup.py
- bin/emacskeys.py
- bin/emacskeys_gui.py
- lib/emacskeys/
  - __init__.py
  - runner.py
  - registry_store.py
  - config.py
  - util.py
  - sender.py
  - listener.py
  - mappings.py
  - gui_tool.py

以下をファイルとして保存してください。

1) setup.py
```python
from setuptools import setup, find_packages

setup(
    name="emacskeys_registry_full",
    version="0.3.0",
    description="Per-app Emacs-like keybindings stored in HKCU registry (hash-keyed)",
    packages=find_packages(where="lib"),
    package_dir={"": "lib"},
    entry_points={
        "console_scripts": [
            "emacskeys=emacskeys.runner:main",
            "emacskeys-gui=emacskeys.gui_tool:main"
        ]
    },
    install_requires=[
        "keyboard>=0.13.5",
        "psutil>=5.8.0"
    ],
)
```

2) bin/emacskeys.py
```python
#!/usr/bin/env python3
from emacskeys.runner import main

if __name__ == "__main__":
    main()
```

3) bin/emacskeys_gui.py
```python
#!/usr/bin/env python3
from emacskeys.gui_tool import main

if __name__ == "__main__":
    main()
```

4) lib/emacskeys/__init__.py
```python
__version__ = "0.3.0"
```

5) lib/emacskeys/registry_store.py
```python
import hashlib
import json
import winreg

REG_BASE = r"Software\EmacsKeysRegistry"

def compute_hash_of_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def compute_hash_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def store_text_under_hash(text: str, source_path: str = "") -> str:
    hs = compute_hash_of_text(text)
    keypath = REG_BASE + "\\" + hs
    k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, keypath)
    winreg.SetValueEx(k, "data", 0, winreg.REG_SZ, text)
    winreg.SetValueEx(k, "source_path", 0, winreg.REG_SZ, source_path)
    winreg.CloseKey(k)
    return hs

def store_file_to_registry(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    return store_text_under_hash(txt, source_path=path)

def load_mapping_by_hash(hs: str):
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_BASE + "\\" + hs, 0, winreg.KEY_READ)
        raw, _ = winreg.QueryValueEx(k, "data")
        winreg.CloseKey(k)
        return json.loads(raw)
    except Exception:
        return None

def list_all_mappings():
    out = {}
    try:
        base = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_BASE, 0, winreg.KEY_READ)
    except FileNotFoundError:
        return out
    i = 0
    try:
        while True:
            sub = winreg.EnumKey(base, i); i += 1
            try:
                k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_BASE + "\\" + sub, 0, winreg.KEY_READ)
                raw, _ = winreg.QueryValueEx(k, "data")
                try:
                    src, _ = winreg.QueryValueEx(k, "source_path")
                except Exception:
                    src = ""
                try:
                    parsed = json.loads(raw)
                except Exception:
                    parsed = None
                out[sub] = {"raw": raw, "data": parsed, "source_path": src}
                winreg.CloseKey(k)
            except Exception:
                pass
            except OSError:
        pass
    try:
        winreg.CloseKey(base)
    except Exception:
        pass
    return out

def delete_hash(hs: str) -> bool:
    try:
        keypath = REG_BASE + "\\" + hs
        # delete values if exist
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, keypath, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(k, "data")
        except Exception:
            pass
        try:
            winreg.DeleteValue(k, "source_path")
        except Exception:
            pass
        winreg.CloseKey(k)
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, keypath)
        return True
    except Exception:
        return False
```

6) lib/emacskeys/config.py
```python
import os
import json
from .registry_store import load_mapping_by_hash, list_all_mappings

DEFAULT_CONFIG = {
    "enabled_processes": [],  # empty = all
    "mappings": {},           # global mappings
    "per_process_mappings": {},
    "use_low_level_send": True
}

def load_config(config_path=None, registry_hash=None):
    cfg = DEFAULT_CONFIG.copy()
    # 1) registry hash explicit
    if registry_hash:
        reg = load_mapping_by_hash(registry_hash)
        if isinstance(reg, dict):
            cfg.update(reg)
            cfg["registry_hash"] = registry_hash
            return cfg
    # 2) config file if provided
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                filecfg = json.load(f)
            cfg.update(filecfg)
            return cfg
        except Exception:
            pass
    # 3) auto-load first registry mapping if present
    regs = list_all_mappings()
    if regs:
        first = next(iter(regs.keys()))
        reg = regs[first]["data"]
        if isinstance(reg, dict):
            cfg.update(reg)
            cfg["registry_hash"] = first
            return cfg
    return cfg
```

7) lib/emacskeys/util.py
```python
import win32gui
import win32process
import psutil

def get_foreground_info():
    """
    Returns (process_name_lower, window_class_lower, window_title)
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

8) lib/emacskeys/sender.py
```python
import keyboard
import ctypes
import time

# Minimal SendInput helper for better reliability in some apps.
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
    "pagedown": 0x22, "pageup": 0x21, "enter": 0x0D, "tab": 0x09,
    "esc": 0x1B, "space": 0x20
}

def _send_vk(vk, flags=0):
    ki = KeyBdInput(vk, 0, flags, 0, None)
    inp = Input(1, Input_I(ki))
    SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

def send_low_level_key(keyname):
    k = keyname.lower()
    if k in VK:
        _send_vk(VK[k], 0)           # key down
        time.sleep(0.01)
        _send_vk(VK[k], 0x0002)     # key up
        time.sleep(0.01)
        return True
    return False

def send_sequence(seq, use_low_level=True):
    """
    seq examples: "ctrl+f", "alt+f, t", "shift+end, delete"
    Comma-separated actions are processed sequentially.
    """
    parts = [p.strip() for p in seq.split(",") if p.strip()]
    for part in parts:
        # simple single-key low-level
        if use_low_level and "+" not in part and part.lower() in VK:
            if send_low_level_key(part):
                continue
        # else use keyboard module for combos
        try:
            keyboard.send(part)
        except Exception:
            pass
        time.sleep(0.01)
```

9) lib/emacskeys/mappings.py
```python
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
    "meta+f": "ctrl+right",   # alt/meta synonyms
    "meta+b": "ctrl+left",
    # word/line/page
    "ctrl+v": "pagedown",
    "alt+v": "pageup",
    "ctrl+o": "enter",
    # editing
    "ctrl+d": "delete",
    "backspace": "backspace",
    "ctrl+k": "shift+end, delete",
    "ctrl+u": "ctrl+z",       # Emacs universal-argument mapped to undo as placeholder
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
    "ctrl+x r t": "",         # placeholder: often not mappable generically
    # window and buffer (map to common app commands where possible)
    "ctrl+x o": "alt+tab",    # switch window as placeholder
    "ctrl+x 1": "",           # maximize placeholder
    "ctrl+x 2": "",           # split placeholder
    # menus (send Alt+letter sequences). Users customize per-app.
    "alt+x": "alt+x",         # for apps where Alt+X is defined
    # universal cancel
    "ctrl+g": "",
    # more movement: paragraph or sentence not generically mappable; provide reasonable approximations
    "alt+{" : "ctrl+up",
    "alt+}" : "ctrl+down"
}
```

10) lib/emacskeys/listener.py
```python
import keyboard
import threading
import time
from .util import get_foreground_info
from .config import load_config
from .mappings import DEFAULT_MAPPINGS
from .sender import send_sequence

class KeyMapper:
    def __init__(self, config_path=None, registry_hash=None):
        self.cfg = load_config(config_path=config_path, registry_hash=registry_hash)
        self.global_mappings = DEFAULT_MAPPINGS.copy()
        self.global_mappings.update(self.cfg.get("mappings", {}) or {})
        # per-process maps merge on top of global
        self.per_process = {}
        for proc, pm in (self.cfg.get("per_process_mappings") or {}).items():
            m = self.global_mappings.copy()
            m.update(pm or {})
            self.per_process[proc.lower()] = m
        self.enabled_processes = [p.lower() for p in (self.cfg.get("enabled_processes") or [])]
        self.use_low_level = bool(self.cfg.get("use_low_level_send", True))
        self._hotkey_ids = []
        self._stop = threading.Event()
        self._install_hotkeys()

    def _is_enabled_for(self, proc):
        if proc is None:
            return False
        if not self.enabled_processes:
            return True
        return proc in self.enabled_processes

    def _lookup_map(self, proc):
        if proc and proc in self.per_process:
            return self.per_process[proc]
        return self.global_mappings

    def _install_hotkeys(self):
        # collect unique keys
        keys = set(self.global_mappings.keys())
        for pm in self.per_process.values():
            keys.update(pm.keys())
        for key in keys:
            try:
                hid = keyboard.add_hotkey(key, lambda k=key: self._handle(k), suppress=True)
                self._hotkey_ids.append(hid)
            except Exception:
                try:
                    hid = keyboard.add_hotkey(key, lambda k=key: self._handle(k), suppress=False)
                    self._hotkey_ids.append(hid)
                except Exception:
                    pass

    def _handle(self, emacs_key):
        proc, cls, title = get_foreground_info()
        if not self._is_enabled_for(proc):
            # pass-through: re-inject original combo if possible
            try:
                keyboard.press_and_release(emacs_key)
            except Exception:
                pass
            return
        mapping = self._lookup_map(proc)
        seq = mapping.get(emacs_key)
        if seq is None:
            try:
                keyboard.press_and_release(emacs_key)
            except Exception:
                pass
            return
        if seq == "":
            # explicit noop
            return
        send_sequence(seq, use_low_level=self.use_low_level)

    def start(self):
        self._stop.clear()
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

11) lib/emacskeys/gui_tool.py
```python
"""
Tkinter GUI to list / view / edit / import / export / delete registry mappings.
Provides quick apply info (prints hash) — KeyMapper runner accepts --registry-hash.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import winreg
import hashlib
from .registry_store import list_all_mappings, store_text_under_hash, delete_hash

REG_BASE = r"Software\EmacsKeysRegistry"

def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

class GuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EmacsKeys Registry Editor")
        self.root.geometry("900x600")
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        p = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        p.pack(fill="both", expand=True)
        left = ttk.Frame(p, width=320)
        right = ttk.Frame(p)
        p.add(left, weight=1)
        p.add(right, weight=3)

        ttk.Label(left, text="Stored mappings").pack(anchor="w", padx=6, pady=(6,0))
        self.listbox = tk.Listbox(left)
        self.listbox.pack(fill="both", expand=True, padx=6, pady=6)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        lfbtn = ttk.Frame(left)
        lfbtn.pack(fill="x", padx=6, pady=6)
        ttk.Button(lfbtn, text="Refresh", command=self._refresh).pack(side="left", padx=4)
        ttk.Button(lfbtn, text="Import...", command=self._import).pack(side="left", padx=4)
        ttk.Button(lfbtn, text="Delete", command=self._delete).pack(side="left", padx=4)
        ttk.Button(lfbtn, text="Export...", command=self._export).pack(side="left", padx=4)

        meta = ttk.Frame(right)
        meta.pack(fill="x", padx=6, pady=6)
        ttk.Label(meta, text="Hash:").grid(row=0, column=0, sticky="w")
        self.hash_var = tk.StringVar()
        ttk.Entry(meta, textvariable=self.hash_var, state="readonly", width=80).grid(row=0, column=1, sticky="w")
        ttk.Label(meta, text="Source:").grid(row=1, column=0, sticky="w")
        self.src_var = tk.StringVar()
        ttk.Entry(meta, textvariable=self.src_var, state="readonly", width=80).grid(row=1, column=1, sticky="w")

        ttk.Label(right, text="JSON data").pack(anchor="w", padx=6)
        self.text = tk.Text(right, wrap="none")
        self.text.pack(fill="both", expand=True, padx=6, pady=(0,6))
        xbar = ttk.Scrollbar(right, orient="horizontal", command=self.text.xview)
        xbar.pack(side="bottom", fill="x")
        ybar = ttk.Scrollbar(right, orient="vertical", command=self.text.yview)
        ybar.pack(side="right", fill="y")
        self.text.configure(xscrollcommand=xbar.set, yscrollcommand=ybar.set)

        bot = ttk.Frame(right)
        bot.pack(fill="x", padx=6, pady=6)
        ttk.Button(bot, text="Validate", command=self._validate).pack(side="left", padx=4)
        ttk.Button(bot, text="Save to registry", command=self._save).pack(side="left", padx=4)
        ttk.Button(bot, text="Save to file", command=self._save_file).pack(side="left", padx=4)
        ttk.Button(bot, text="Apply (print hash)", command=self._apply).pack(side="right", padx=4)
        ttk.Button(bot, text="Close", command=self.root.quit).pack(side="right", padx=4)

    def _refresh(self):
        self.listbox.delete(0, tk.END)
        self.mapdata = list_all_mappings()
        for hs, info in self.mapdata.items():
            src = info.get("source_path") or ""
            label = f"{hs[:8]}...  {src}"
            self.listbox.insert(tk.END, label)
        self.hash_var.set("")
        self.src_var.set("")
        self.text.delete("1.0", tk.END)

    def _get_selected_hash(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        idx = sel[0]
        keys = list(self.mapdata.keys())
        if idx >= len(keys):
            return None
        return keys[idx]

    def _on_select(self, ev=None):
        hs = self._get_selected_hash()
        if not hs:
            return
        info = self.mapdata.get(hs, {})
        self.hash_var.set(hs)
        self.src_var.set(info.get("source_path") or "")
        raw = info.get("raw") or ""
        try:
            parsed = info.get("data")
            if parsed is not None:
                pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
            else:
                pretty = raw
        except Exception:
            pretty = raw
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", pretty)

    def _import(self):
        path = filedialog.askopenfilename(filetypes=[("JSON","*.json"),("All","*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                txt = f.read()
            json.loads(txt)
        except Exception as e:
            messagebox.showerror("Import failed", str(e))
            return
        hs = store_text_under_hash(txt, source_path=path)
        messagebox.showinfo("Imported", f"Stored under hash:\n{hs}")
        self._refresh()

    def _delete(self):
        hs = self._get_selected_hash()
        if not hs:
            messagebox.showwarning("No selection", "Select an item first.")
            return
        if not messagebox.askyesno("Confirm", f"Delete mapping {hs}?"):
            return
        ok = delete_hash(hs)
        if ok:
            messagebox.showinfo("Deleted", "Deleted.")
            self._refresh()
        else:
            messagebox.showerror("Failed", "Delete failed.")

    def _export(self):
        hs = self._get_selected_hash()
        if not hs:
            messagebox.showwarning("No selection", "Select.")
            return
        info = self.mapdata.get(hs, {})
        raw = info.get("raw") or ""
        dest = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if not dest:
            return
        try:
            with open(dest, "w", encoding="utf-8") as f:
                f.write(raw)
            messagebox.showinfo("Exported", dest)
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    def _validate(self):
        txt = self.text.get("1.0", tk.END).strip()
        if not txt:
            messagebox.showwarning("Empty", "Empty editor.")
            return
        try:
            json.loads(txt)
            messagebox.showinfo("Valid", "JSON valid.")
        except Exception as e:
            messagebox.showerror("Invalid", str(e))

    def _save(self):
        txt = self.text.get("1.0", tk.END).strip()
        if not txt:
            messagebox.showwarning("Empty", "Empty editor.")
            return
        try:
            json.loads(txt)
        except Exception as e:
            messagebox.showerror("Invalid JSON", str(e))
            return
        # Save new entry; if editing existing, new hash will be created. Optionally delete old.
        hs_new = store_text_under_hash(txt, source_path=self.src_var.get() or "")
        messagebox.showinfo("Saved", f"Saved under hash:\n{hs_new}")
        self._refresh()

    def _save_file(self):
        txt = self.text.get("1.0", tk.END).strip()
        if not txt:
            messagebox.showwarning("Empty", "Empty.")
            return
        dest = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if not dest:
            return
        try:
            json.loads(txt)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(txt)
            messagebox.showinfo("Saved", dest)
        except Exception as e:
            messagebox.showerror("Failed", str(e))

    def _apply(self):
        hs = self._get_selected_hash()
        if not hs:
            messagebox.showwarning("No selection", "Select.")
            return
        messagebox.showinfo("Apply", f"Selected mapping hash:\n{hs}\nUse: emacskeys --registry-hash {hs}")

def main():
    root = tk.Tk()
    app = GuiApp(root)
    root.mainloop()
```

12) lib/emacskeys/runner.py
```python
import argparse
import sys
import time
from .listener import KeyMapper
from .registry_store import store_file_to_registry, list_all_mappings

def main():
    parser = argparse.ArgumentParser(description="Emacs-like per-app keybindings (registry-backed)")
    parser.add_argument("--config-file", "-f", help="Import JSON mapping file to registry and exit", default=None)
    parser.add_argument("--registry-hash", "-r", help="Load mapping from registry by hash", default=None)
    parser.add_argument("--list-registry", action="store_true", help="List registry mappings")
    args = parser.parse_args()

    if args.config_file:
        try:
            hs = store_file_to_registry(args.config_file)
            print("Stored mapping with hash:", hs)
        except Exception as e:
            print("Failed to store mapping:", e)
        return

    if args.list_registry:
        regs = list_all_mappings()
        if not regs:
            print("No registry mappings found.")
            return
        for hs, info in regs.items():
            sp = info.get("source_path") or ""
            print(hs, sp)
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

使用方法（簡潔）
- 必要ライブラリをインストール:
  - pip install keyboard psutil
- パッケージを配置してインストール（任意）:
  - pip install -e .
- 外部 JSON マッピングファイルをレジストリへ登録:
  - python -m emacskeys.runner --config-file path\to\mappings.json
  - 出力される SHA256 ハッシュを控える。
- レジストリから指定ハッシュを読み込み実行:
  - python -m emacskeys.runner --registry-hash <hash>
  - あるいは保存されている最初のマッピングが自動で読み込まれます。
- GUI で一覧/編集/インポート/エクスポート:
  - python -m emacskeys.gui_tool
  - GUI の "Apply" ボタンは選択ハッシュを表示します（runner にそのハッシュを渡して起動してください）。

外部 JSON 例（推奨） — ファイル例: my_mappings.json
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
      "ctrl+y": "ctrl+v",
      "ctrl+s": "ctrl+f",
      "ctrl+g": "",
      "alt+f": "alt+f",               // menu access example
    "alt+f, t": "alt+f, t"          // open File menu then choose 't' (app-specific)
  },
  "per_process_mappings": {
    "code.exe": {
        "ctrl+s": "ctrl+s",           // keep native save in VSCode
      "ctrl+shift+f": "ctrl+shift+f"
    },
    "chrome.exe": {
        "ctrl+t": "ctrl+t",
      "ctrl+w": "ctrl+w"
    }
  },
  "use_low_level_send": true
}
```

補足
- メニュー操作: アプリによっては Alt+<letter> でメニューを操作できます。JSON に "alt+f, t" のように記述すれば順に送信します（アプリ固有のメニュー文字に合わせてください）。
- 全ての Emacs コマンド: 上の `mappings.py` と JSON を組み合わせ、必要なコマンドを JSON で追加してください。JSON 側が優先して上書きします。
- 信頼性: 一部アプリ（特に Electron ベースやリモートセッション）ではキースケジュール注入が期待通り動かないことがあります。`use_low_level_send` を切替えて試してください。

必要なら:
- 特定アプリ（VSCode/Chrome）向けに UIAutomation やアプリ内 API を使ってより確実にメニュー/テキスト操作する拡張を追加しますか？
