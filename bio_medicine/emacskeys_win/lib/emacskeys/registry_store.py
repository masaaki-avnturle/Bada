import hashlib
import json
import winreg

REG_BASE = r"Software\\EmacsKeysRegistry"

def compute_hash_of_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def store_text_under_hash(text: str, source_path: str = "") -> str:
    hs = compute_hash_of_text(text)
    keypath = REG_BASE + "\\\\" + hs
    k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, keypath)
    winreg.SetValueEx(k, "data", 0, winreg.REG_SZ, text)
    winreg.SetValueEx(k, "source_path", 0, winreg.REG_SZ, source_path)
    winreg.CloseKey(k)
    return hs

def load_mapping_by_hash(hs: str):
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_BASE + "\\\\" + hs, 0, winreg.KEY_READ)
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
                k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_BASE + "\\\\" + sub, 0, winreg.KEY_READ)
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
        keypath = REG_BASE + "\\\\" + hs
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
