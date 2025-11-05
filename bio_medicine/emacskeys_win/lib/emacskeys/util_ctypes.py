import ctypes
import ctypes.wintypes
try:
    import psutil
except Exception:
    psutil = None

user32 = ctypes.WinDLL("user32", use_last_error=True)
GetForegroundWindow = user32.GetForegroundWindow
GetForegroundWindow.restype = ctypes.wintypes.HWND

GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetWindowThreadProcessId.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.DWORD)]
GetWindowThreadProcessId.restype = ctypes.wintypes.DWORD

GetWindowTextW = user32.GetWindowTextW
GetWindowTextW.argtypes = [ctypes.wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
GetWindowTextW.restype = ctypes.c_int

GetClassNameW = user32.GetClassNameW
GetClassNameW.argtypes = [ctypes.wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
GetClassNameW.restype = ctypes.c_int

def get_foreground_info():
    try:
        hwnd = GetForegroundWindow()
        if not hwnd:
            return None, None, ""
        pid = ctypes.wintypes.DWORD()
        _ = GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        pid_val = pid.value
        proc_name = None
        if psutil:
            try:
                p = psutil.Process(pid_val)
                proc_name = p.name().lower()
            except Exception:
                proc_name = None
        else:
            proc_name = None
        try:
            buf = ctypes.create_unicode_buffer(256)
            res = GetClassNameW(hwnd, buf, ctypes.sizeof(buf))
            cls = buf.value.lower() if res > 0 else None
        except Exception:
            cls = None
        try:
            buf2 = ctypes.create_unicode_buffer(1024)
            res2 = GetWindowTextW(hwnd, buf2, ctypes.sizeof(buf2))
            title = buf2.value if res2 > 0 else ""
        except Exception:
            title = ""
        return proc_name, cls, title
    except Exception:
        return None, None, ""
