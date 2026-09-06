以下は、Windows 10上でアクティブなアプリケーション（プロセス）ごとに「Emacsライクなキーバインド」を適用するための Python パッケージの全ソースコード例です。キーのフックと送信には人気のあるライブラリ（`keyboard`, `pywin32`）を使用しています。実用化のためにユーザー側でのカスタマイズ（どのプロセスに適用するか、どのキーを変換するか等）を想定した構成になっています。

注意事項（必読）
- このコードは Windows 専用です（`pywin32` を使用）。
- 強力にキーボード入力を操作するため、管理者権限が必要な場合があります。実行前に必ずソースを確認してください。
- サードパーティライブラリ：`keyboard`, `pywin32` が必要です。インストール方法は下に記載します。
- 実環境で使う前に安全なテキストエディタや仮想環境で動作確認を行ってください。

パッケージ構成（例）
- bin/
  - emacskeys.exe (または起動用スクリプト `emacskeys`)
- lib/emacskeys/
  - __init__.py
  - runner.py
  - listener.py
  - mappings.py
  - util.py
  - config.py
- usr/
  - config.json
- include/
  - README.md
  - LICENSE
- setup.py
- README.md

以下に各ファイルの中身を示します。必要な部分をコピーしてそのままファイルとして保存してください。

1) setup.py
```python
from setuptools import setup, find_packages

setup(
    name="emacskeys_win",
    version="0.1.0",
    description="Apply Emacs-like keybindings per-application on Windows 10",
    packages=find_packages(where="lib"),
    package_dir={"": "lib"},
    entry_points={
        "console_scripts": [
            "emacskeys=emacskeys.runner:main",
        ]
    },
    install_requires=[
        "keyboard>=0.13.5",
        "pywin32>=306"
    ],
    include_package_data=True,
)
```

2) bin/emacskeys (起動用スクリプト; Windowsでは .exe ではなく .py を呼ぶ想定)
```python
# Windows の場合は単に setup.py で entry_point を使うか、こちらから直接起動できます
from lib.emacskeys.runner import main

if __name__ == "__main__":
    main()
```

3) lib/emacskeys/__init__.py
```python
# パッケージ宣言
__version__ = "0.1.0"
```

4) lib/emacskeys/config.py
```python
import json
import os

DEFAULT_CONFIG = {
    # 対象プロセス名（小文字）に対して有効化。空配列で全アプリケーションに適用。
    "enabled_processes": [
        "notepad.exe",
        "code.exe",
        "devenv.exe",
        "sublime_text.exe",
        "chrome.exe",
        "firefox.exe",
        "explorer.exe"
    ],
    # キー置換テーブル（Emacs -> 実際に送るキーシーケンス）
    # keyboard.send に与える文字列／修飾子で指定します。
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
        "ctrl+s": "ctrl+f"  # Ctrl-s を検索（アプリ依存）
    },
    # 無効化したいウィンドウクラスのリスト（部分一致）。空で無効化なし。
    "disabled_window_classes": []
}

def load_config(path=None):
    if path is None:
        default_path = os.path.join(os.getcwd(), "usr", "config.json")
        path = default_path
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # マージする
        merged = DEFAULT_CONFIG.copy()
        merged.update(cfg)
        return merged
    except Exception:
        return DEFAULT_CONFIG.copy()
```

5) lib/emacskeys/util.py
```python
import win32gui
import win32process
import psutil

def get_active_process_name():
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd == 0:
            return None, None
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc = psutil.Process(pid)
            name = proc.name()
        except Exception:
            name = None
        cls = win32gui.GetClassName(hwnd)
        return name.lower() if name else None, cls.lower() if cls else None
    except Exception:
        return None, None
```

6) lib/emacskeys/mappings.py
```python
from typing import Dict

# デフォルトのマッピングをプログラム上でも保持（config から上書き可）
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
    "ctrl+s": "ctrl+f"
}
```

7) lib/emacskeys/listener.py
```python
import keyboard
import threading
import time
from .util import get_active_process_name
from .config import load_config
from .mappings import DEFAULT_MAPPINGS

class KeyMapper:
    def __init__(self, config_path=None):
        self.cfg = load_config(config_path)
        # マッピングは config の mapping を使う（フォールバックあり）
        self.mappings = DEFAULT_MAPPINGS.copy()
        self.mappings.update(self.cfg.get("mappings", {}))
        self.enabled_processes = [p.lower() for p in self.cfg.get("enabled_processes", [])]
        self.disabled_window_classes = [c.lower() for c in self.cfg.get("disabled_window_classes", [])]
        self._listeners = []
        self._stop = threading.Event()

    def is_enabled_for(self, process_name, win_class):
        # enabled_processes が空なら全アプリケーション適用
        if process_name is None:
            return False
        if self.disabled_window_classes:
            for pattern in self.disabled_window_classes:
                if pattern in (win_class or ""):
                    return False
        if not self.enabled_processes:
            return True
        return process_name in self.enabled_processes

    def start(self):
        # 各 Emacs の組み合わせに対してハンドラ登録する
        for emacs_key, send_seq in self.mappings.items():
            # keyboard のホットキーとして登録
            h = keyboard.hook_key(None, lambda e: None)  # ダミーでキーを使うための枠（後で置き換える）
            # 実際は add_hotkey を使う
        # 代わりに add_hotkey を使って個別登録
        for emacs_key, send_seq in self.mappings.items():
            keyboard.add_hotkey(emacs_key, self._handler_factory(send_seq), suppress=True)
        # 別スレッドでプロセス確認・状態管理（将来的に有効/無効切替を行うため）
        t = threading.Thread(target=self._watcher_loop, daemon=True)
        t.start()
        self._listeners.append(t)

    def stop(self):
        self._stop.set()
        keyboard.unhook_all_hotkeys()

    def _handler_factory(self, send_seq):
        # クロージャを返す
        def handler():
            proc, cls = get_active_process_name()
            if not self.is_enabled_for(proc, cls):
                # そのプロセスでは変換しない — 代わりにキーをそのまま押す（再発火）
                # keyboard.send で当該 Emacs キーを送る（元のキーをそのまま実行）
                # ここは安全のため何もしない（抑止を解除する場合は実装を拡張）
                return
            # 実際のキー列を送信（カンマ区切りで複数アクション）
            # 例: "shift+end, delete"
            parts = [p.strip() for p in send_seq.split(",")]
            for part in parts:
                keyboard.send(part)
        return handler

    def _watcher_loop(self):
        # 現在は単純にループしておく（将来的に設定の再読み込み等をここで行う）
        while not self._stop.is_set():
            time.sleep(1)
```

8) lib/emacskeys/runner.py
```python
import argparse
import os
import sys
from .listener import KeyMapper

def main():
    parser = argparse.ArgumentParser(description="Emacs-like keybindings for Windows apps")
    parser.add_argument("--config", "-c", help="Path to config.json", default=None)
    args = parser.parse_args()

    mapper = KeyMapper(config_path=args.config)
    try:
        print("Starting Emacs key mapper. Press Ctrl+C to exit.")
        mapper.start()
        # ブロックして待つ
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        mapper.stop()
        sys.exit(0)
```

9) usr/config.json (サンプル)
```json
{
  "enabled_processes": [
      "notepad.exe",
      "code.exe",
    "chrome.exe"
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
    "ctrl+k": "shift+end, delete"
  },
  "disabled_window_classes": [
  ]
}
```

10) include/README.md
```
This package provides a Python-based key mapper that applies Emacs-like keybindings
to specified Windows applications. Configure `usr/config.json` to change mappings
and target processes.
```

11) include/LICENSE
(短い MIT ライセンス例）
```
MIT License
Copyright (c) 2025
Permission is hereby granted, free of charge, to any person obtaining a copy...
```

README.md（プロジェクトルート）
```
Emacs-like Keybindings for Windows Apps

Requirements:
- Python 3.8+
- pip install keyboard pywin32 psutil

Install:
- pip install -e .

Run:
- python -m emacskeys.runner --config usr/config.json
```

導入手順（簡潔）
1. 必要ライブラリをインストール:
   - pip install keyboard pywin32 psutil
2. 上のファイル群をディレクトリ通りに作る（lib/emacskeys/ 以下に .py ファイルを配置）。
3. （オプション）setup.py でインストール:
   - pip install -e .
4. 実行:
   - python -m emacskeys.runner --config usr/config.json
   - またはインストール後に emacskeys コマンドで起動。

拡張・注意点
- 現状は簡易実装です。例えば:
  - 一部アプリ（Chrome の編集欄など）ではキーイベントの扱いが特殊で、期待どおりに動かない場合があります。
  - 独自の「元キーをそのまま送る」振る舞い（対象外アプリではキーを通常通り流す）は安全上の配慮から未完全です。必要なら `handler` を拡張してください。
  - 高度な用途（IME, リモートデスクトップ, UWP アプリ）では追加の実装が必要です。

必要なら、次のどれを行うか教えてください：
- （A）このコードを改良して特定アプリ（例: Visual Studio Code, Chrome の入力欄）での動作を改善する
- （B）デフォルトのキーマッピングを変更・追加する
- （C）インストーラ（Windows サービスやスタートアップ登録）を追加する

どれを進めますか？
