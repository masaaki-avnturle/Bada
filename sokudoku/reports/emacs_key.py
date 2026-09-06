以下は、要求された全機能（A: 特定アプリ向け改善、B: マッピング変更/拡張、C: インストーラ — Windows サービスおよびスタートアップ登録）を含む Python パッケージの完全なソースコード例です。ファイル構成は前回提案を拡張したものです。実行には管理者権限が必要な操作（サービスの登録やレジストリ書き込み）があります。安全上の理由で、実環境で使う前に必ずソースを確認してください。

パッケージ構成（配下ファイルをすべて作成してください）
- bin/
  - emacskeys.py
- lib/emacskeys/
  - __init__.py
  - runner.py
  - listener.py
  - mappings.py
  - util.py
  - config.py
  - sender.py
  - installer.py
  - service.py
- usr/
  - config.json
- include/
  - README.md
  - LICENSE
- setup.py
- README.md

注意: 依存ライブラリ
- keyboard
- pywin32
- psutil
- pywinauto (optional, used for some heuristics)
これらは requirements に記載します。

――――――――――――――――――
1) setup.py
```python
from setuptools import setup, find_packages

setup(
    name="emacskeys_win",
    version="0.2.0",
    description="Per-application Emacs-like keybindings for Windows 10 (with service/startup installer)",
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
        "psutil>=5.8.0",
        "pywinauto>=0.6.8"
    ],
    include_package_data=True,
)
```

――――――――――――――――――
2) bin/emacskeys.py
```python
# Simple launcher script (optional)
from emacskeys.runner import main

if __name__ == "__main__":
    main()
```

――――――――――――――――――
3) lib/emacskeys/__init__.py
```python
__version__ = "0.2.0"
```

――――――――――――――――――
4) lib/emacskeys/config.py
```python
import json
import os

DEFAULT_CONFIG = {
    "enabled_processes": [],  # 空 = 全てのプロセスに適用
    # per-process mappings override global mappings. Keys are process executable names (lowercase).
    "per_process_mappings": {
        "code.exe": {
            # VSCode: use Ctrl+P/ N etc. you can override here
        },
        "chrome.exe": {
            # Chrome-specific overrides (if any)
        }
    },
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
        "ctrl+d": "delete",
        "ctrl+v": "pagedown",
        "alt+v": "pageup",
        "ctrl+s": "ctrl+f"
    },
    "disabled_window_classes": [],
    # Some controls / windows (by title substrings or class) where mapping should be disabled
    "disabled_window_titles": [],
    # use_low_level_send: True to use SendInput (better for Chrome/VSCode), False uses keyboard.send
    "use_low_level_send": True,
    # installer options default
    "service_name": "EmacsKeysService",
    "startup_registry_name": "EmacsKeysStartup"
}

def load_config(path=None):
    if path is None:
        path = os.path.join(os.getcwd(), "usr", "config.json")
    cfg = DEFAULT_CONFIG.copy()
    try:
        with open(path, "r", encoding="utf-8") as f:
            user = json.load(f)
        # deep merge basic keys
        for k, v in user.items():
            if k in ("mappings", "per_process_mappings"):
                tmp = cfg.get(k, {}).copy()
                tmp.update(v or {})
                cfg[k] = tmp
            else:
                cfg[k] = v
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return cfg
```

――――――――――――――――――
5) lib/emacskeys/util.py
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

――――――――――――――――――
6) lib/emacskeys/mappings.py
```python
from typing import Dict

# base defaults — will be merged with config
DEFAULT_MAPPINGS: Dict[str, str] = {
    "ctrl+n": "down",
    "ctrl+p": "up",
    "ctrl+f": "right",
    "ctrl+b": "left",
    "ctrl+a": "home",
    "ctrl+e": "end",
    "alt+f": "ctrl+right",
    "alt+b": "ctrl+left",
    "ctrl+k": "shift+end, delete",
    "ctrl+d": "delete",
    "ctrl+v": "pagedown",
    "alt+v": "pageup",
    "ctrl+s": "ctrl+f",
    # Additional useful mappings:
    "ctrl+_": "undo",       # Ctrl-_ (often same as Ctrl-/)
    "ctrl+/": "undo",
    "ctrl+g": ""            # cancel (no-op)
}
```

――――――――――――――――――
7) lib/emacskeys/sender.py
```python
# Provides two sending mechanisms:
#  - keyboard.send (higher-level)
#  - low-level SendInput using ctypes (works better for some apps like Chrome/VSCode)
import keyboard
import ctypes
import time

SendInput = ctypes.windll.user32.SendInput

# C struct definitions for SendInput
PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL)
    ]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_short), ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong), ("time",ctypes.c_ulong), ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

# Helper to build keyboard event
def _build_key(scancode, flags):
    ki = KeyBdInput(0, scancode, flags, 0, None)
    return Input(ctypes.c_ulong(1), Input_I(ki))

# Map from key names (simple ASCII/keywords) to virtual-key/scancodes.
# For simplicity we'll rely on keyboard module's translation for complex sequences,
# but for single-key low-level sends we map a few useful keys.
VK = {
    "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "home": 0x24, "end": 0x23, "delete": 0x2E, "backspace": 0x08,
    "ctrl": 0x11, "shift": 0x10, "alt": 0x12,
    "pagedown": 0x22, "pageup": 0x21
}

def send_via_keyboard(seq):
    # seq may be "ctrl+right" or "shift+end, delete"
    for part in [p.strip() for p in seq.split(",") if p.strip()]:
        keyboard.send(part)
        time.sleep(0.01)

def send_low_level(seq):
    # For complex sequences, fall back to keyboard.send.
    # For simple single key like "down" use SendInput for better reliability.
    for part in [p.strip() for p in seq.split(",") if p.strip()]:
        # if contains modifier like ctrl+right -> use keyboard.send for simplicity
        if "+" in part or part.isalpha() is False and part not in VK:
            send_via_keyboard(part)
            continue
        key = part.lower()
        if key in VK:
            vk = VK[key]
            # Press
            inputs = (Input * 2)()
            inputs[0] = _build_key(ctypes.windll.user32.MapVirtualKeyW(vk, 0), 0)
            # key up has flag 0x0002
            inputs[1] = _build_key(ctypes.windll.user32.MapVirtualKeyW(vk, 0), 0x0002)
            SendInput(2, ctypes.byref(inputs), ctypes.sizeof(Input))
            time.sleep(0.01)
        else:
            # fallback
            send_via_keyboard(part)

def send_sequence(seq, use_low_level=True):
    if use_low_level:
        try:
            send_low_level(seq)
            return
        except Exception:
            pass
    send_via_keyboard(seq)
```

――――――――――――――――――
8) lib/emacskeys/listener.py
```python
import keyboard
import threading
import time
from .util import get_foreground_info
from .config import load_config
from .mappings import DEFAULT_MAPPINGS
from .sender import send_sequence

class KeyMapper:
    def __init__(self, config_path=None):
        self.cfg = load_config(config_path)
        # build mapping: base -> config mappings -> per-process override
        self.global_mappings = DEFAULT_MAPPINGS.copy()
        self.global_mappings.update(self.cfg.get("mappings", {}))
        self.per_process = {}
        for proc, m in self.cfg.get("per_process_mappings", {}).items():
            mm = self.global_mappings.copy()
            mm.update(m or {})
            self.per_process[proc.lower()] = mm
        self.enabled_processes = [p.lower() for p in self.cfg.get("enabled_processes", [])]
        self.disabled_window_classes = [c.lower() for c in self.cfg.get("disabled_window_classes", [])]
        self.disabled_window_titles = [t.lower() for t in self.cfg.get("disabled_window_titles", [])]
        self.use_low_level = bool(self.cfg.get("use_low_level_send", True))
        self._stop = threading.Event()
        self._hotkeys = {}
        self._install_hotkeys()

    def is_enabled_for(self, proc_name, win_class, title):
        if proc_name is None:
            return False
        if self.disabled_window_classes:
            for pattern in self.disabled_window_classes:
                if pattern in (win_class or ""):
                    return False
        if self.disabled_window_titles:
            for pattern in self.disabled_window_titles:
                if pattern in (title or "").lower():
                    return False
        if not self.enabled_processes:
            return True
        return proc_name in self.enabled_processes

    def _lookup_mapping(self, proc_name):
        if proc_name and proc_name in self.per_process:
            return self.per_process[proc_name]
        return self.global_mappings

    def _install_hotkeys(self):
        # Remove existing
        for h in list(self._hotkeys.keys()):
            try:
                keyboard.remove_hotkey(h)
            except Exception:
                pass
        self._hotkeys.clear()
        # Use union of all mapping keys across global and per-process
        keys = set(self.global_mappings.keys())
        for proc_map in self.per_process.values():
            keys.update(proc_map.keys())
        # register hooks
        for emacs_key in keys:
            try:
                hid = keyboard.add_hotkey(emacs_key, lambda ek=emacs_key: self._handler(ek), suppress=True)
                self._hotkeys[hid] = emacs_key
            except Exception:
                # fallback: try without suppress
                try:
                    hid = keyboard.add_hotkey(emacs_key, lambda ek=emacs_key: self._handler(ek), suppress=False)
                    self._hotkeys[hid] = emacs_key
                except Exception:
                    pass

    def _handler(self, emacs_key):
        proc, cls, title = get_foreground_info()
        if not self.is_enabled_for(proc, cls, title):
            # Not enabled: re-inject original key so app receives it
            # keyboard.press_and_release will send the original combo
            try:
                keyboard.press_and_release(emacs_key)
            except Exception:
                pass
            return
        mapping = self._lookup_mapping(proc)
        send_seq = mapping.get(emacs_key)
        if send_seq is None:
            # if not mapped explicitly, pass through
            try:
                keyboard.press_and_release(emacs_key)
            except Exception:
                pass
            return
        if send_seq == "":
            # explicit no-op (e.g., ctrl+g)
            return
        # send sequence via appropriate sender
        send_sequence(send_seq, use_low_level=self.use_low_level)

    def start(self):
        # nothing else; keyboard hooks are active once added
        self._stop.clear()
        # background thread to monitor configuration changes (reload not implemented yet)
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

――――――――――――――――――
9) lib/emacskeys/runner.py
```python
import argparse
import sys
import time
from .listener import KeyMapper
from .installer import Installer

def main():
    parser = argparse.ArgumentParser(description="Emacs-like keybindings for Windows apps")
    parser.add_argument("--config", "-c", help="Path to config.json", default=None)
    parser.add_argument("--install-service", action="store_true", help="Install as Windows service (requires admin)")
    parser.add_argument("--remove-service", action="store_true", help="Remove Windows service")
    parser.add_argument("--add-startup", action="store_true", help="Add app to user startup (registry)")
    parser.add_argument("--remove-startup", action="store_true", help="Remove startup entry")
    args = parser.parse_args()

    installer = Installer()
    if args.install_service:
        installer.install_service()
        return
    if args.remove_service:
        installer.remove_service()
        return
    if args.add_startup:
        installer.add_startup_entry()
        return
    if args.remove_startup:
        installer.remove_startup_entry()
        return

    mapper = KeyMapper(config_path=args.config)
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

――――――――――――――――――
10) lib/emacskeys/installer.py
```python
import os
import sys
import getpass
import winreg
import inspect
from .config import load_config

class Installer:
    def __init__(self, config_path=None):
        self.cfg = load_config(config_path)
        # determine path to current script/executable
        if getattr(sys, "frozen", False):
            self.executable = sys.executable
        else:
            # use python module launcher
            self.executable = sys.executable + ' -m emacskeys'
        self.service_name = self.cfg.get("service_name", "EmacsKeysService")
        self.startup_name = self.cfg.get("startup_registry_name", "EmacsKeysStartup")

    def add_startup_entry(self):
        # adds current launcher to HKCU\Software\Microsoft\Windows\CurrentVersion\Run
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)
            # store command line; if it's a python -m module, wrap in quotes with python path
            cmd = self.executable
            winreg.SetValueEx(key, self.startup_name, 0, winreg.REG_SZ, cmd)
            winreg.CloseKey(key)
            print("Startup entry added.")
        except Exception as e:
            print("Failed to add startup entry:", e)

    def remove_startup_entry(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, self.startup_name)
            winreg.CloseKey(key)
            print("Startup entry removed.")
        except Exception as e:
            print("Failed to remove startup entry:", e)

    def install_service(self):
        # Install a Windows service wrapper using pywin32 by invoking service.py
        # This requires admin. We will call 'python service.py install' as subprocess.
        import subprocess
        script_dir = os.path.dirname(os.path.abspath(__file__))
        service_script = os.path.join(script_dir, "service.py")
        if not os.path.exists(service_script):
            print("Service script not found:", service_script)
            return
        try:
            subprocess.check_call([sys.executable, service_script, "install"])
            print("Service installed. Start it from services.msc or 'python service.py start'")
        except Exception as e:
            print("Failed to install service:", e)

    def remove_service(self):
        import subprocess
        script_dir = os.path.dirname(os.path.abspath(__file__))
        service_script = os.path.join(script_dir, "service.py")
        try:
            subprocess.check_call([sys.executable, service_script, "remove"])
            print("Service removed.")
        except Exception as e:
            print("Failed to remove service:", e)
```

――――――――――――――――――
11) lib/emacskeys/service.py
```python
# Windows service wrapper using pywin32. This allows running mapper as a service.
import os
import sys
import time
import servicemanager
import win32event
import win32service
import win32serviceutil

# Service name is read from config, but for pywin32 we provide a default.
SERVICE_NAME = "EmacsKeysService"
SERVICE_DISPLAY_NAME = "Emacs-like Keybindings Service"

class AppServerSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = SERVICE_NAME
    _svc_display_name_ = SERVICE_DISPLAY_NAME

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False

    def SvcDoRun(self):
        import logging
        logging.basicConfig(
            filename=os.path.join(os.path.dirname(__file__), "service.log"),
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s")
        servicemanager.LogInfoMsg("EmacsKeys service is starting")
        from .listener import KeyMapper
        mapper = KeyMapper()
        mapper.start()
        while self.running:
            rc = win32event.WaitForSingleObject(self.stop_event, 1000)
            if rc == win32event.WAIT_OBJECT_0:
                break
        mapper.stop()
        servicemanager.LogInfoMsg("EmacsKeys service is stopping")

if __name__ == '__main__':
    # Allow command line: install, remove, start, stop
    if len(sys.argv) == 1:
        try:
            win32serviceutil.HandleCommandLine(AppServerSvc)
        except Exception:
            pass
        else:
        win32serviceutil.HandleCommandLine(AppServerSvc)
```

――――――――――――――――――
12) usr/config.json (サンプル。必要に応じて編集)
```json
{
  "enabled_processes": [
      "notepad.exe",
      "code.exe",
      "chrome.exe",
    "firefox.exe"
  ],
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
      "ctrl+d": "delete",
      "ctrl+v": "pagedown",
      "alt+v": "pageup",
      "ctrl+s": "ctrl+f",
      "ctrl+/": "undo",
    "ctrl+g": ""
  },
  "per_process_mappings": {
    "code.exe": {
        "ctrl+s": "ctrl+s",
      "ctrl+n": "ctrl+n"
    },
    "chrome.exe": {
      "ctrl+s": "ctrl+s"  // override so save dialogs work normally
    }
  },
  "disabled_window_titles": [
      "password",
    "login"
  ],
    "use_low_level_send": true,
    "service_name": "EmacsKeysService",
  "startup_registry_name": "EmacsKeysStartup"
}
```

――――――――――――――――――
13) include/README.md
```
EmacsKeys for Windows

This package provides per-application Emacs-like keybindings, improved handling
for applications such as Visual Studio Code and Chrome, configurable mappings,
and installer helpers:
 - Windows service wrapper (pywin32) via emacskeys.service
 - Registry startup entry via Installer.add_startup_entry()

Usage examples:
 - Run interactively:
   python -m emacskeys.runner --config usr/config.json

 - Install to startup (current user):
   python -m emacskeys.runner --add-startup

 - Install as service (requires admin):
   python -m emacskeys.runner --install-service

Dependencies:
 - keyboard, pywin32, psutil, pywinauto
```

――――――――――――――――――
14) include/LICENSE (MIT)
```
MIT License
Copyright (c) 2025
Permission is hereby granted, free of charge, to any person obtaining a copy
... (standard MIT text) ...
```

――――――――――――――――――
15) README.md (project root)
```
Emacs-like Keybindings for Windows (with installer)

Requirements:
- Python 3.8+
- pip install -r requirements.txt
  requirements.txt:
    keyboard
    pywin32
    psutil
    pywinauto

Install:
- pip install -e .

Run:
- python -m emacskeys.runner --config usr/config.json

Install startup (current user):
- python -m emacskeys.runner --add-startup

Install service (admin):
- python -m emacskeys.runner --install-service
  (You can also run the generated service script: python lib/emacskeys/service.py install)
```

――――――――――――――――――
説明（短い注意）
- Chrome/VSCode: low-level SendInput を用いることで、キー注入信頼性が向上します。ただし、すべての環境で完全に動作するとは限りません。必要なら `use_low_level_send` を false にして keyboard.send を使用してください。
- サービス: サービスとして実行した場合、ユーザーのデスクトップセッションに対するキーボードフックは制限されるため、一般的には「現在ログイン中のユーザーで起動する常駐プロセス（スタートアップ登録）」を推奨します。サービスは管理者・自動起動のためのオプションです。
- セキュリティ: フックとキー送信は強力な操作のため、管理者権限が求められる場合があります。必ずコードを確認してから実行してください。

必要なら:
- Chrome/VSCode 向けにさらに堅牢な検出（フォーカスが編集可能か、UIAutomation による入力可能判定）を追加しますか？
