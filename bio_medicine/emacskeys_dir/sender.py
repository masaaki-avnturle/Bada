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
