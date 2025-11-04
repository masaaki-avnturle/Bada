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
