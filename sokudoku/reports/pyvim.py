以下は簡易的な「vim風」テキストエディタを Python で実装した単一ファイルのスクリプトです。ターミナル上で動作し、ノーマルモードと挿入モードを持ち、基本的な移動・編集・保存・終了コマンド（:w, :q, :wq）をサポートします。高度な Vim 機能はありませんが、学習や拡張の出発点として使えます。

使い方（例）
- 保存先ファイルを指定して起動: python3 pyvim.py filename.txt
- 起動後:
  - ノーマルモード（デフォルト）: h/j/k/l で移動、x で文字削除、dd で行削除、yy で行ヤンク、p で貼り付け、i/I/a/A/o/O で挿入モードへ
  - 挿入モード: Esc でノーマルに戻る。文字入力は挿入されます。
  - コマンドライン: ノーマルで : を押してコマンド入力（:w :q :wq をサポート）
  - Ctrl-G でステータス表示（ファイル名/行数等）
  - UTF-8 対応（端末設定に依存）

保存ファイル: pyvim.py

```python
#!/usr/bin/env python3
# pyvim.py - minimal vim-like editor in Python using curses
# Supports: normal/insert modes, hjkl movement, basic edit, :w :q :wq, dd/yy/p, x, simple statusline

from __future__ import annotations
import curses
import sys
from typing import List, Optional

class Buffer:
    def __init__(self, lines: Optional[List[str]] = None):
        self.lines: List[str] = lines if lines is not None else [""]
        self.filename: Optional[str] = None
        self.modified = False
        self.clipboard: List[str] = []

    def load(self, filename: str):
        self.filename = filename
        try:
            with open(filename, "r", encoding="utf-8") as f:
                self.lines = [l.rstrip("\n") for l in f]
            if not self.lines:
                self.lines = [""]
            self.modified = False
        except FileNotFoundError:
            self.lines = [""]
            self.modified = False

    def save(self) -> bool:
        if not self.filename:
            return False
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                for i, line in enumerate(self.lines):
                    f.write(line + ("\n" if i < len(self.lines) else ""))
            self.modified = False
            return True
        except Exception:
            return False

class Editor:
    def __init__(self, stdscr, buf: Buffer):
        self.stdscr = stdscr
        self.buf = buf
        self.mode = "NORMAL"  # or "INSERT" or "CMD"
        self.cmdline = ""
        self.msg = ""
        self.cy = 0
        self.cx = 0
        self.top = 0  # top visible line
        self.count_prefix = ""  # for commands like 5j
        self.last_key = ""
        curses.curs_set(1)
        self.stdscr.keypad(True)

    def set_msg(self, s: str):
        self.msg = s

    def clamp_cursor(self):
        if self.cy < 0:
            self.cy = 0
        if self.cy >= len(self.buf.lines):
            self.cy = len(self.buf.lines) - 1
        line = self.buf.lines[self.cy]
        if self.cx < 0:
            self.cx = 0
        if self.cx > len(line):
            self.cx = len(line)

    def insert_char(self, ch: str):
        line = self.buf.lines[self.cy]
        self.buf.lines[self.cy] = line[:self.cx] + ch + line[self.cx:]
        self.cx += len(ch)
        self.buf.modified = True

    def backspace(self):
        if self.cx > 0:
            line = self.buf.lines[self.cy]
            self.buf.lines[self.cy] = line[:self.cx-1] + line[self.cx:]
            self.cx -= 1
            self.buf.modified = True
        else:
            if self.cy > 0:
                prev = self.buf.lines[self.cy-1]
                cur = self.buf.lines.pop(self.cy)
                self.cy -= 1
                self.cx = len(prev)
                self.buf.lines[self.cy] = prev + cur
                self.buf.modified = True

    def newline(self):
        line = self.buf.lines[self.cy]
        left = line[:self.cx]
        right = line[self.cx:]
        self.buf.lines[self.cy] = left
        self.buf.lines.insert(self.cy+1, right)
        self.cy += 1
        self.cx = 0
        self.buf.modified = True

    def delete_char(self):
        line = self.buf.lines[self.cy]
        if self.cx < len(line):
            self.buf.lines[self.cy] = line[:self.cx] + line[self.cx+1:]
            self.buf.modified = True
        else:
            if self.cy + 1 < len(self.buf.lines):
                nxt = self.buf.lines.pop(self.cy+1)
                self.buf.lines[self.cy] = line + nxt
                self.buf.modified = True

    def delete_line(self):
        y = self.cy
        if 0 <= y < len(self.buf.lines):
            self.buf.clipboard = [self.buf.lines[y]]
            self.buf.lines.pop(y)
            if not self.buf.lines:
                self.buf.lines = [""]
            if self.cy >= len(self.buf.lines):
                self.cy = len(self.buf.lines) - 1
            self.cx = min(self.cx, len(self.buf.lines[self.cy]))
            self.buf.modified = True

    def yank_line(self):
        if 0 <= self.cy < len(self.buf.lines):
            self.buf.clipboard = [self.buf.lines[self.cy]]

    def put_after(self):
        if self.buf.clipboard:
            ins = self.buf.clipboard
            self.buf.lines[self.cy+1:self.cy+1] = ins
            self.cy += len(ins)
            self.cx = 0
            self.buf.modified = True

    def process_normal(self, key):
        # handle numeric prefix
        if key.isdigit():
            self.count_prefix += key
            return
        count = int(self.count_prefix) if self.count_prefix else 1
        self.count_prefix = ""
        if key == "h":
            self.cx -= count
        elif key == "l":
            self.cx += count
        elif key == "j":
            self.cy += count
            self.cx = min(self.cx, len(self.buf.lines[self.cy])) if self.cy < len(self.buf.lines) else self.cx
        elif key == "k":
            self.cy -= count
            self.cx = min(self.cx, len(self.buf.lines[self.cy])) if self.cy < len(self.buf.lines) else self.cx
        elif key == "0":
            self.cx = 0
        elif key == "$":
            self.cx = len(self.buf.lines[self.cy])
        elif key == "i":
            self.mode = "INSERT"
        elif key == "I":
            self.cx = 0
            self.mode = "INSERT"
        elif key == "a":
            self.cx += 1
            self.mode = "INSERT"
        elif key == "A":
            self.cx = len(self.buf.lines[self.cy])
            self.mode = "INSERT"
        elif key == "o":
            self.cy += 1
            if self.cy > len(self.buf.lines):
                self.buf.lines.append("")
            else:
                self.buf.lines.insert(self.cy, "")
            self.cx = 0
            self.mode = "INSERT"
        elif key == "O":
            self.buf.lines.insert(self.cy, "")
            self.mode = "INSERT"
            self.cx = 0
        elif key == "x":
            for _ in range(count):
                self.delete_char()
        elif key == "p":
            for _ in range(count):
                self.put_after()
        elif key == "d":
            # support dd
            if self.last_key == "d":
                for _ in range(count):
                    self.delete_line()
            # else wait for second d
        elif key == "y":
            if self.last_key == "y":
                for _ in range(count):
                    self.yank_line()
            elif key == ":":
            self.mode = "CMD"
            self.cmdline = ""
        elif key == "\x07":  # Ctrl-G show status
            self.set_msg(f"file={self.buf.filename or '[NoName]'} lines={len(self.buf.lines)} modified={'+' if self.buf.modified else '-'}")
        elif key == "q":
            # quick quit without saving
            raise SystemExit()
        else:
            # unhandled
            pass
        self.last_key = key

    def process_cmd(self):
        cmd = self.cmdline.strip()
        if cmd == "w":
            if self.buf.filename:
                ok = self.buf.save()
                self.set_msg("Wrote " + (self.buf.filename or ""))
            else:
                self.set_msg("No filename. Use :w filename")
        elif cmd.startswith("w "):
            fn = cmd[2:].strip()
            self.buf.filename = fn
            ok = self.buf.save()
            self.set_msg("Wrote " + (fn if ok else "(failed)"))
        elif cmd == "q":
            raise SystemExit()
        elif cmd == "wq":
            if self.buf.filename:
                self.buf.save()
            raise SystemExit()
        else:
            self.set_msg("Unknown cmd: " + cmd)
        self.mode = "NORMAL"

    def refresh(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()
        nvis = h - 2  # reserve statusline and cmdline
        # adjust top
        if self.cy < self.top:
            self.top = self.cy
        elif self.cy >= self.top + nvis:
            self.top = self.cy - nvis + 1
        # draw lines
        for i in range(nvis):
            ln = self.top + i
            if ln >= len(self.buf.lines):
                break
            line = self.buf.lines[ln]
            disp = line[:w-1]
            try:
                self.stdscr.addstr(i, 0, disp)
            except Exception:
                pass
        # status line
        status = f" {self.mode} | {self.buf.filename or '[NoName]'} | {self.cy+1},{self.cx+1} {'[+]' if self.buf.modified else ''} {self.msg}"
        try:
            self.stdscr.addstr(h-2, 0, status[:w-1], curses.A_REVERSE)
        except Exception:
            pass
        # command line or input hint
        if self.mode == "CMD":
            line = ":" + self.cmdline
        elif self.mode == "INSERT":
            line = "-- INSERT --"
        else:
            line = ""
        try:
            self.stdscr.addstr(h-1, 0, line[:w-1], curses.A_BOLD)
        except Exception:
            pass
        # move cursor
        vis_y = self.cy - self.top
        vis_x = self.cx
        if vis_y < 0:
            vis_y = 0
        if vis_y >= nvis:
            vis_y = nvis - 1
        try:
            self.stdscr.move(vis_y, min(vis_x, w-1))
        except Exception:
            pass
        self.stdscr.refresh()

    def run(self):
        while True:
            self.clamp_cursor()
            self.refresh()
            ch = self.stdscr.get_wch()
            if isinstance(ch, str) and ch == "\x1b":  # ESC
                if self.mode == "INSERT":
                    self.mode = "NORMAL"
                elif self.mode == "CMD":
                    self.mode = "NORMAL"
                else:
                    # ESC in normal: clear prefix
                    self.count_prefix = ""
                continue

            if self.mode == "NORMAL":
                if isinstance(ch, str):
                    self.process_normal(ch)
                else:
                    # handle special keys
                    if ch == curses.KEY_LEFT:
                        self.process_normal("h")
                    elif ch == curses.KEY_RIGHT:
                        self.process_normal("l")
                    elif ch == curses.KEY_UP:
                        self.process_normal("k")
                    elif ch == curses.KEY_DOWN:
                        self.process_normal("j")
                    elif self.mode == "INSERT":
                if isinstance(ch, str):
                    if ch == "\n":
                        self.newline()
                    elif ch == "\x7f" or ch == "\b":
                        self.backspace()
                    else:
                        self.insert_char(ch)
                else:
                    # special keys in insert ignored for now
                    pass
            elif self.mode == "CMD":
                if isinstance(ch, str):
                    if ch == "\n":
                        try:
                            self.process_cmd()
                        except SystemExit:
                            raise
                    elif ch == "\x7f" or ch == "\b":
                        self.cmdline = self.cmdline[:-1]
                    else:
                        self.cmdline += ch
                else:
                    # ignore special keys in cmdline
                    pass

def main(stdscr):
    buf = Buffer()
    if len(sys.argv) > 1:
        fn = sys.argv[1]
        buf.load(fn)
    ed = Editor(stdscr, buf)
    try:
        ed.run()
    except SystemExit:
        return

if __name__ == "__main__":
    curses.wrapper(main)
```

注意と拡張案
- この実装は最小限の機能に留めています。行番号表示、検索（/）、置換、ビジュアルモード、多バイト文字の厳密な幅処理、RCS/.tex,v 特有のファイル表示などは未実装です。
- 拡張したい場合は、検索（/、n）、undo/redo、ビジュアル選択、設定読み込み等を追加してください。
- curses は端末依存の挙動があります。Windows では標準 curses が無いので Windows 用に別ライブラリ（windows-curses）を入れる必要があります。

