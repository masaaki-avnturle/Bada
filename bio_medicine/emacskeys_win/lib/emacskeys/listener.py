import keyboard
import threading
import time
from .util_ctypes import get_foreground_info
from .config import load_config
from .mappings import DEFAULT_MAPPINGS
from .sender import send_sequence

class KeyMapper:
    def __init__(self, config_path=None, registry_hash=None):
        self.cfg = load_config(config_path=config_path, registry_hash=registry_hash)
        self.global_mappings = DEFAULT_MAPPINGS.copy()
        self.global_mappings.update(self.cfg.get("mappings") or {})
        self.per_process = {}
        for proc, pm in (self.cfg.get("per_process_mappings") or {}).items():
            m = self.global_mappings.copy()
            m.update(pm or {})
            self.per_process[proc.lower()] = m
        self.enabled_processes = [p.lower() for p in (self.cfg.get("enabled_processes") or [])]
        self.use_low_level = bool(self.cfg.get("use_low_level_send", True))
        self._hotkeys = {}
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
        keys = set(self.global_mappings.keys())
        for pm in self.per_process.values():
            keys.update(pm.keys())
        for key in keys:
            try:
                keyboard.add_hotkey(key, lambda k=key: self._handle(k), suppress=True)
            except Exception:
                try:
                    keyboard.add_hotkey(key, lambda k=key: self._handle(k), suppress=False)
                except Exception:
                    pass

    def _handle(self, emacs_key):
        proc, cls, title = get_foreground_info()
        if not self._is_enabled_for(proc):
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
