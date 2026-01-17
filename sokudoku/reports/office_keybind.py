以下は、先ほどの Office 用モーダルレイヤーに Emacs ライクなキーバインド（主要な移動・編集・キル/ヤンク・検索など）を追加した完全な Python スクリプトです。Word/Excel 等のフォーカス時に動作し、Vim 風ノーマル/インサート/コマンドモードに加え、Emacs スタイルのキーバインドも取り扱います。

注意（必読）
- Windows 向け、依存: keyboard, pywin32, psutil
  - pip install keyboard pywin32 psutil
- レジストリや COM を使わずキーボード注入で操作する簡易実装です。COM を用いると確実になります（必要なら追加提供可）。
- 実行中はキーボードフックが有効になります。テスト環境でまず確認してください。

ファイル: office_modal_emacs.py

```python
# office_modal_emacs.py
# Requirements: pip install keyboard pywin32 psutil
import keyboard
import time
import threading
import psutil
import win32gui
import win32process
import sys

# --- 設定: 対象プロセス名(小文字) ---
TARGET_PROCS = {"winword.exe", "excel.exe", "outlook.exe", "powerpnt.exe"}

# モード管理: "normal" (Vimノーマル), "insert", "command"
mode = "insert"
mode_lock = threading.Lock()

# コマンドモードの入力バッファ（簡易）
command_buffer = ""

# 数値プレフィクス (例: 3j)
repeat_count = 0

# 簡易バッファ（dd, yy 等）
_key_buf = ""
_key_buf_time = 0

# 最後のイベント時刻（デバウンス）
_last_event_time = 0

# --- ヘルパ関数 ---
def get_foreground_process_name():
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd == 0:
            return None
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        return proc.name().lower()
    except Exception:
        return None

def send_keys(seq):
    # seq は keyboard.send が受け取る形式 (例 "ctrl+right" や "shift+end")
    try:
        keyboard.send(seq)
    except Exception:
        pass

def press_and_release(key):
    try:
        keyboard.press_and_release(key)
    except Exception:
        pass

# --- Emacs / Vim コマンド実装 ---
def do_move_left(rc=1):
    for _ in range(rc): send_keys("left")

def do_move_right(rc=1):
    for _ in range(rc): send_keys("right")

def do_move_up(rc=1):
    for _ in range(rc): send_keys("up")

def do_move_down(rc=1):
    for _ in range(rc): send_keys("down")

def do_word_forward(rc=1):
    for _ in range(rc): send_keys("ctrl+right")

def do_word_backward(rc=1):
    for _ in range(rc): send_keys("ctrl+left")

def do_line_start():
    send_keys("home")

def do_line_end():
    send_keys("end")

def do_page_down():
    send_keys("pagedown")

def do_page_up():
    send_keys("pageup")

def do_delete_char():
    send_keys("delete")

def do_backspace():
    send_keys("backspace")

def do_kill_line():
    # Emacs C-k: kill to end of line -> Shift+End then Ctrl+X then store (we simply cut)
    send_keys("shift+end")
    time.sleep(0.01)
    send_keys("ctrl+x")  # not standard in Office; use Ctrl+X to cut selection
    time.sleep(0.01)
    send_keys("ctrl+x")  # ensure cut (may be redundant)

def do_kill_region_copy():
    send_keys("ctrl+x")  # placeholder

def do_yank():
    send_keys("ctrl+v")

def do_undo():
    send_keys("ctrl+z")

def do_redo():
    send_keys("ctrl+y")

def do_search_forward():
    # Emacs C-s mapped to app search (Ctrl+f)
    send_keys("ctrl+f")

def do_search_backward():
    # Emacs C-r approximate
    send_keys("ctrl+shift+f")

def do_select_all():
    send_keys("ctrl+a")

def do_open_menu_alt(letter_seq=None):
    # send Alt+letter, or sequence like "alt+f, t"
    if not letter_seq:
        return
    for part in [p.strip() for p in letter_seq.split(",") if p.strip()]:
        send_keys(part)
        time.sleep(0.05)

# --- ノーマルモードコマンド実行 ---
def normal_mode_command(key, rc=1):
    # key may be single or multi (e.g., "dd" or "ctrl+a")
    if key == "h":
        do_move_left(rc)
    elif key == "l":
        do_move_right(rc)
    elif key == "j":
        do_move_down(rc)
    elif key == "k":
        do_move_up(rc)
    elif key == "w":
        do_word_forward(rc)
    elif key == "b":
        do_word_backward(rc)
    elif key == "0":
        do_line_start()
    elif key == "$":
        do_line_end()
    elif key == "dd":
        # delete line: Home, Shift+End, Delete
        do_line_start()
        time.sleep(0.01)
        send_keys("shift+end")
        time.sleep(0.01)
        do_delete_char()
    elif key == "yy":
        # yank (copy) line
        do_line_start()
        time.sleep(0.01)
        send_keys("shift+end")
        time.sleep(0.01)
        send_keys("ctrl+c")
    elif key == "p":
        do_yank()
    elif key == "u":
        do_undo()
    elif key == "ctrl+a":
        do_line_start()
    elif key == "ctrl+e":
        do_line_end()
    elif key == ":":
        enter_command_mode()
    # Emacs-specific keys in normal mode (invoke action and suppress)
elif key == "ctrl+f":
        do_move_right(rc)
elif key == "ctrl+b":
        do_move_left(rc)
elif key == "ctrl+n":
        do_move_down(rc)
elif key == "ctrl+p":
        do_move_up(rc)
elif key == "ctrl+k":
        # kill line
        do_kill_line()
elif key == "ctrl+y":
        do_yank()
elif key == "ctrl+_":
        do_undo()
elif key == "ctrl+/":
        do_undo()
elif key == "alt+f":
        do_word_forward(rc)
elif key == "alt+b":
        do_word_backward(rc)
elif key == "ctrl+s":
        do_search_forward()
elif key == "ctrl+r":
        do_search_backward()
elif key == "ctrl+v":
        do_page_down()
elif key == "alt+v":
        do_page_up()
else:
        # unmapped: no-op
        return

# --- コマンドモード（:コマンド） ---
def enter_command_mode():
    global mode, command_buffer
    with mode_lock:
        mode = "command"
    sys.stdout.write("\n:")  # console prompt
    sys.stdout.flush()
    def cmd_reader():
        global mode, command_buffer
        try:
            cmd = sys.stdin.readline()
            if not cmd:
                cmd = ""
            cmd = cmd.strip()
            command_buffer = cmd
            process_command(cmd)
        finally:
            with mode_lock:
                mode = "normal"
    t = threading.Thread(target=cmd_reader, daemon=True)
    t.start()

def process_command(cmd):
    if cmd == "w":
        send_keys("ctrl+s")
    elif cmd == "q":
        send_keys("alt+f4")
    elif cmd in ("wq", "x"):
        send_keys("ctrl+s")
        time.sleep(0.1)
        send_keys("alt+f4")
    else:
        print("Unknown command:", cmd)

# --- グローバルキーイベントハンドラ ---
def on_key_event(e):
    global mode, _last_event_time, repeat_count, _key_buf, _key_buf_time

    # only handle key down
    if e.event_type != "down":
        return

    now = time.time()
    if now - _last_event_time < 0.01:
        pass
    _last_event_time = now

    proc = get_foreground_process_name()
    if proc not in TARGET_PROCS:
        return  # not Office

    name = e.name  # e.g. 'a', 'esc', 'ctrl+a' depending on keyboard lib
    # Normalize ctrl combos for consistency
    if e.modifiers:
        mods = "+".join(sorted(m.replace("left ","").replace("right ","") for m in e.modifiers))
        # if name is a single char and modifiers present, produce "ctrl+a" style
        if len(name) == 1:
            name = mods + "+" + name

    with mode_lock:
        cur_mode = mode

    # ESC always -> normal mode
    if name == "esc":
        with mode_lock:
            mode = "normal"
        try:
            e.suppress_event()
        except Exception:
            pass
        return

    # Emacs keybindings should work in insert mode too (e.g., Ctrl+a / Ctrl+e)
    if cur_mode == "insert":
        # Emacs navigation in insert mode
        if name in ("ctrl+a", "ctrl+e", "ctrl+f", "ctrl+b", "ctrl+n", "ctrl+p",
                    "alt+f", "alt+b", "ctrl+left", "ctrl+right"):
            # perform navigation and suppress original
            normal_mode_command(name, rc=1)
            try:
                e.suppress_event()
            except Exception:
                pass
            return
        # undo/redo in insert mode
        if name in ("ctrl+z", "ctrl+y", "ctrl+_","ctrl+/"):
            if name in ("ctrl+z","ctrl+_","ctrl+/"):
                do_undo()
            else:
                do_redo()
            try:
                e.suppress_event()
            except Exception:
                pass
            return
        # otherwise let insert behave normally
        return

    if cur_mode == "normal":
        # digits accumulate repeat count
        if len(name) == 1 and name.isdigit():
            try:
                digit = int(name)
                repeat_count = repeat_count * 10 + digit
            except Exception:
                pass
            try:
                e.suppress_event()
            except Exception:
                pass
            return

        # maintain short buffer for multi-key like dd, yy
        if time.time() - _key_buf_time > 0.6:
            _key_buf = ""
        _key_buf_time = time.time()
        _key_buf += name

        # ctrl combos: keyboard library may deliver 'ctrl+a' directly
        if "+" in name and name.startswith("ctrl"):
            rc = repeat_count if repeat_count > 0 else 1
            normal_mode_command(name, rc)
            repeat_count = 0
            _key_buf = ""
            try:
                e.suppress_event()
            except Exception:
                pass
            return

        # two-key commands
        if _key_buf in ("dd", "yy"):
            rc = repeat_count if repeat_count > 0 else 1
            normal_mode_command(_key_buf, rc)
            repeat_count = 0
            _key_buf = ""
            try:
                e.suppress_event()
            except Exception:
                pass
            return

        # single-key commands
        if name in ("h","j","k","l","w","b","0","$","p","u",":","i"):
            if name == "i":
                with mode_lock:
                    mode = "insert"
                repeat_count = 0
                _key_buf = ""
                try:
                    e.suppress_event()
                except Exception:
                    pass
                return
            rc = repeat_count if repeat_count > 0 else 1
            normal_mode_command(name, rc)
            repeat_count = 0
            _key_buf = ""
            try:
                e.suppress_event()
            except Exception:
                pass
            return

        # unmapped: suppress to avoid accidental input
        try:
            e.suppress_event()
        except Exception:
            pass
        _key_buf = ""
        repeat_count = 0
        return

    if cur_mode == "command":
        # in command mode we read from stdin; suppress keys to avoid input duplication
        try:
            e.suppress_event()
        except Exception:
            pass
        return

# --- スタートとループ ---
def start():
    print("Office modal layer (Vim+Emacs) starting.")
    print("ESC -> normal, i -> insert, : -> command. Emacs keys (Ctrl+a/e/f/b/n/p/k/y) supported.")
    keyboard.hook(on_key_event, suppress=False)  # we'll suppress inside handler
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        keyboard.unhook_all()

if __name__ == "__main__":
    start()
```

必要なら:
- Word/Excel 向けに COM (win32com.client) を使って Selection や Range を直接操作する版（行削除や矩形選択を確実に行える）を示しますか？
- モード表示オーバーレイ（現在モードを画面に表示）を追加しますか？
- キルリング（複数の切り取りを保持して yank で復元）を導入しますか？

どれを追加しましょうか？
