以下は、選択 (1) に基づく C プログラム `pkginstallgen.c` です。実行するとカレントディレクトリにパッケージ構成（bin/, lib/emacskeys/ 以下のファイル群および setup.py）を生成します。ファイル内容は、直前に提示した Python パッケージ（レジストリ格納・ハッシュ管理・GUI 等を含む完全実装）のソースコードをそのまま書き出します。

使い方（簡単）
- Windows または POSIX 環境でコンパイル：
  - gcc pkginstallgen.c -o pkginstallgen
- 実行：
  - ./pkginstallgen
- 実行後、カレントディレクトリに `bin/`, `lib/emacskeys/`, などのファイルが作成されます。

注意
- 既存の同名ファイルは上書きされます。必要に応じてバックアップしてください。
- 生成されるファイルは長文の Python ソースです。生成後に内容を確認してください。

以下が `pkginstallgen.c` のソースコードです。

```c
  /* pkginstallgen.c
   Run this program to create the Python package files (bin/, lib/emacskeys/, setup.py, ...)
   The program writes multiple files. Existing files with the same paths will be overwritten.
  */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <direct.h>
#define MKDIR(s) _mkdir(s)
#else
#include <sys/stat.h>
#include <sys/types.h>
#define MKDIR(s) mkdir((s), 0755)
#endif

  static int ensure_dir(const char *path) {
  /* create directory path, including intermediate directories */
  char tmp[1024];
  char *p = NULL;
  size_t len;
  snprintf(tmp, sizeof(tmp), "%s", path);
  len = strlen(tmp);
  if (len == 0) return -1;
  if (tmp[len - 1] == '/' || tmp[len - 1] == '\\') tmp[len - 1] = 0;
  for (p = tmp + 1; *p; p++) {
    if (*p == '/' || *p == '\\') {
      *p = 0;
      MKDIR(tmp);
      *p = '/';
    }
  }
  MKDIR(tmp);
  return 0;
}

static int write_file(const char *path, const char *content) {
  FILE *f;
  /* ensure directory exists */
  char dir[1024];
  strncpy(dir, path, sizeof(dir)); dir[sizeof(dir)-1]=0;
  char *last_slash = strrchr(dir, '/');
  if (!last_slash) last_slash = strrchr(dir, '\\');
  if (last_slash) {
    *last_slash = 0;
    ensure_dir(dir);
  }
  f = fopen(path, "wb");
  if (!f) {
    fprintf(stderr, "Failed to open %s for writing\n", path);
    return -1;
  }
  fwrite(content, 1, strlen(content), f);
  fclose(f);
  printf("Wrote %s\n", path);
  return 0;
}

int main(void) {
  /* create directories */
  ensure_dir("bin");
  ensure_dir("lib/emacskeys");

  /* setup.py */
    const char *setup_py =
"from setuptools import setup, find_packages\n\n"
"setup(\n"
"    name=\"emacskeys_registry_full\",\n"
"    version=\"0.3.0\",\n"
"    description=\"Per-app Emacs-like keybindings stored in HKCU registry (hash-keyed)\",\n"
"    packages=find_packages(where=\"lib\"),\n"
"    package_dir={\"\": \"lib\"},\n"
"    entry_points={\n"
"        \"console_scripts\": [\n"
"            \"emacskeys=emacskeys.runner:main\",\n"
"            \"emacskeys-gui=emacskeys.gui_tool:main\"\n"
"        ]\n"
"    },\n"
"    install_requires=[\n"
"        \"keyboard>=0.13.5\",\n"
"        \"psutil>=5.8.0\"\n"
"    ],\n"
      ")\n";
    write_file("setup.py", setup_py);

    /* bin/emacskeys.py */
    const char *bin_emacskeys =
      "#!/usr/bin/env python3\nfrom emacskeys.runner import main\n\nif __name__ == \"__main__\":\n    main()\n";
    write_file("bin/emacskeys.py", bin_emacskeys);

    /* bin/emacskeys_gui.py */
    const char *bin_gui =
      "#!/usr/bin/env python3\nfrom emacskeys.gui_tool import main\n\nif __name__ == \"__main__\":\n    main()\n";
    write_file("bin/emacskeys_gui.py", bin_gui);

    /* lib/emacskeys/__init__.py */
    const char *init_py =
      "__version__ = \"0.3.0\"\n";
    write_file("lib/emacskeys/__init__.py", init_py);

    /* lib/emacskeys/registry_store.py */
    const char *registry_store_py =
      "import hashlib\nimport json\nimport winreg\n\nREG_BASE = r\"Software\\EmacsKeysRegistry\"\n\ndef compute_hash_of_text(text: str) -> str:\n    return hashlib.sha256(text.encode(\"utf-8\")).hexdigest()\n\ndef compute_hash_of_file(path: str) -> str:\n    h = hashlib.sha256()\n    with open(path, \"rb\") as f:\n        for chunk in iter(lambda: f.read(8192), b\"\"):\n            h.update(chunk)\n    return h.hexdigest()\n\ndef store_text_under_hash(text: str, source_path: str = \"\") -> str:\n    hs = compute_hash_of_text(text)\n    keypath = REG_BASE + \"\\\\\" + hs\n    k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, keypath)\n    winreg.SetValueEx(k, \"data\", 0, winreg.REG_SZ, text)\n    winreg.SetValueEx(k, \"source_path\", 0, winreg.REG_SZ, source_path)\n    winreg.CloseKey(k)\n    return hs\n\ndef store_file_to_registry(path: str) -> str:\n    with open(path, \"r\", encoding=\"utf-8\") as f:\n        txt = f.read()\n    return store_text_under_hash(txt, source_path=path)\n\ndef load_mapping_by_hash(hs: str):\n    try:\n        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_BASE + \"\\\\\" + hs, 0, winreg.KEY_READ)\n        raw, _ = winreg.QueryValueEx(k, \"data\")\n        winreg.CloseKey(k)\n        return json.loads(raw)\n    except Exception:\n        return None\n\ndef list_all_mappings():\n    out = {}\n    try:\n        base = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_BASE, 0, winreg.KEY_READ)\n    except FileNotFoundError:\n        return out\n    i = 0\n    try:\n        while True:\n            sub = winreg.EnumKey(base, i); i += 1\n            try:\n                k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_BASE + \"\\\\\" + sub, 0, winreg.KEY_READ)\n                raw, _ = winreg.QueryValueEx(k, \"data\")\n                try:\n                    src, _ = winreg.QueryValueEx(k, \"source_path\")\n                except Exception:\n                    src = \"\"\n                try:\n                    parsed = json.loads(raw)\n                except Exception:\n                    parsed = None\n                out[sub] = {\"raw\": raw, \"data\": parsed, \"source_path\": src}\n                winreg.CloseKey(k)\n            except Exception:\n                pass\n    except OSError:\n        pass\n    try:\n        winreg.CloseKey(base)\n    except Exception:\n        pass\n    return out\n\ndef delete_hash(hs: str) -> bool:\n    try:\n        keypath = REG_BASE + \"\\\\\" + hs\n        # delete values if exist\n        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, keypath, 0, winreg.KEY_SET_VALUE)\n        try:\n            winreg.DeleteValue(k, \"data\")\n        except Exception:\n            pass\n        try:\n            winreg.DeleteValue(k, \"source_path\")\n        except Exception:\n            pass\n        winreg.CloseKey(k)\n        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, keypath)\n        return True\n    except Exception:\n        return False\n";
    write_file("lib/emacskeys/registry_store.py", registry_store_py);

    /* lib/emacskeys/config.py */
    const char *config_py =
      "import os\nimport json\nfrom .registry_store import load_mapping_by_hash, list_all_mappings\n\nDEFAULT_CONFIG = {\n    \"enabled_processes\": [],  # empty = all\n    \"mappings\": {},           # global mappings\n    \"per_process_mappings\": {},\n    \"use_low_level_send\": True\n}\n\ndef load_config(config_path=None, registry_hash=None):\n    cfg = DEFAULT_CONFIG.copy()\n    # 1) registry hash explicit\n    if registry_hash:\n        reg = load_mapping_by_hash(registry_hash)\n        if isinstance(reg, dict):\n            cfg.update(reg)\n            cfg[\"registry_hash\"] = registry_hash\n            return cfg\n    # 2) config file if provided\n    if config_path and os.path.exists(config_path):\n        try:\n            with open(config_path, \"r\", encoding=\"utf-8\") as f:\n                filecfg = json.load(f)\n            cfg.update(filecfg)\n            return cfg\n        except Exception:\n            pass\n    # 3) auto-load first registry mapping if present\n    regs = list_all_mappings()\n    if regs:\n        first = next(iter(regs.keys()))\n        reg = regs[first][\"data\"]\n        if isinstance(reg, dict):\n            cfg.update(reg)\n            cfg[\"registry_hash\"] = first\n            return cfg\n    return cfg\n";
    write_file("lib/emacskeys/config.py", config_py);

    /* lib/emacskeys/util.py */
    const char *util_py =
      "import win32gui\nimport win32process\nimport psutil\n\ndef get_foreground_info():\n    \"\"\"\n    Returns (process_name_lower, window_class_lower, window_title)\n    \"\"\"\n    try:\n        hwnd = win32gui.GetForegroundWindow()\n        if hwnd == 0:\n            return None, None, None\n        _, pid = win32process.GetWindowThreadProcessId(hwnd)\n        try:\n            proc = psutil.Process(pid)\n            name = proc.name().lower()\n        except Exception:\n            name = None\n        try:\n            cls = win32gui.GetClassName(hwnd).lower()\n        except Exception:\n            cls = None\n        try:\n            title = win32gui.GetWindowText(hwnd)\n        except Exception:\n            title = None\n        return name, cls, title\n    except Exception:\n        return None, None, None\n";
    write_file("lib/emacskeys/util.py", util_py);

    /* lib/emacskeys/sender.py */
    const char *sender_py =
      "import keyboard\nimport ctypes\nimport time\n\n# Minimal SendInput helper for better reliability in some apps.\nSendInput = ctypes.windll.user32.SendInput\nPUL = ctypes.POINTER(ctypes.c_ulong)\n\nclass KeyBdInput(ctypes.Structure):\n    _fields_ = [(\"wVk\", ctypes.c_ushort), (\"wScan\", ctypes.c_ushort),\n                (\"dwFlags\", ctypes.c_ulong), (\"time\", ctypes.c_ulong), (\"dwExtraInfo\", PUL)]\n\nclass Input_I(ctypes.Union):\n    _fields_ = [(\"ki\", KeyBdInput)]\n\nclass Input(ctypes.Structure):\n    _fields_ = [(\"type\", ctypes.c_ulong), (\"ii\", Input_I)]\n\nVK = {\n    \"left\": 0x25, \"up\": 0x26, \"right\": 0x27, \"down\": 0x28,\n    \"home\": 0x24, \"end\": 0x23, \"delete\": 0x2E, \"backspace\": 0x08,\n    \"pagedown\": 0x22, \"pageup\": 0x21, \"enter\": 0x0D, \"tab\": 0x09,\n    \"esc\": 0x1B, \"space\": 0x20\n}\n\ndef _send_vk(vk, flags=0):\n    ki = KeyBdInput(vk, 0, flags, 0, None)\n    inp = Input(1, Input_I(ki))\n    SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))\n\ndef send_low_level_key(keyname):\n    k = keyname.lower()\n    if k in VK:\n        _send_vk(VK[k], 0)           # key down\n        time.sleep(0.01)\n        _send_vk(VK[k], 0x0002)     # key up\n        time.sleep(0.01)\n        return True\n    return False\n\ndef send_sequence(seq, use_low_level=True):\n    \"\"\"\n    seq examples: \"ctrl+f\", \"alt+f, t\", \"shift+end, delete\"\n    Comma-separated actions are processed sequentially.\n    \"\"\"\n    parts = [p.strip() for p in seq.split(\",\") if p.strip()]\n    for part in parts:\n        # simple single-key low-level\n        if use_low_level and \"+\" not in part and part.lower() in VK:\n            if send_low_level_key(part):\n                continue\n        # else use keyboard module for combos\n        try:\n            keyboard.send(part)\n        except Exception:\n            pass\n        time.sleep(0.01)\n";
    write_file("lib/emacskeys/sender.py", sender_py);

    /* lib/emacskeys/mappings.py */
    const char *mappings_py =
      "# Comprehensive-ish Emacs-like mapping set (default). Users should override via JSON.\n# Keys are keyboard hotkey strings accepted by keyboard.add_hotkey, e.g. \"ctrl+n\"\nDEFAULT_MAPPINGS = {\n    # basic movement\n    \"ctrl+f\": \"right\",\n    \"ctrl+b\": \"left\",\n    \"ctrl+n\": \"down\",\n    \"ctrl+p\": \"up\",\n    \"ctrl+a\": \"home\",\n    \"ctrl+e\": \"end\",\n    \"alt+f\": \"ctrl+right\",\n    \"alt+b\": \"ctrl+left\",\n    \"meta+f\": \"ctrl+right\",\n    \"meta+b\": \"ctrl+left\",\n    # word/line/page\n    \"ctrl+v\": \"pagedown\",\n    \"alt+v\": \"pageup\",\n    \"ctrl+o\": \"enter\",\n    # editing\n    \"ctrl+d\": \"delete\",\n    \"backspace\": \"backspace\",\n    \"ctrl+k\": \"shift+end, delete\",\n    \"ctrl+u\": \"ctrl+z\",\n    \"ctrl+/\": \"ctrl+z\",\n    \"ctrl+_\": \"ctrl+z\",\n    # search\n    \"ctrl+s\": \"ctrl+f\",\n    \"ctrl+r\": \"ctrl+shift+f\",\n    # kill/yank\n    \"ctrl+y\": \"ctrl+v\",\n    \"alt+w\": \"ctrl+c\",\n    \"ctrl+w\": \"ctrl+x\",\n    # rectangle / transpose / exchange (best-effort)\n    \"ctrl+x r t\": \"\",\n    # window and buffer (map to common app commands where possible)\n    \"ctrl+x o\": \"alt+tab\",\n    \"ctrl+x 1\": \"\",\n    \"ctrl+x 2\": \"\",\n    # menus (send Alt+letter sequences). Users customize per-app.\n    \"alt+x\": \"alt+x\",\n    \"ctrl+g\": \"\",\n    # more movement: paragraph or sentence approximations\n    \"alt+{\" : \"ctrl+up\",\n    \"alt+}\" : \"ctrl+down\"\n}\n";
    write_file("lib/emacskeys/mappings.py", mappings_py);

    /* lib/emacskeys/listener.py */
    const char *listener_py =
      "import keyboard\nimport threading\nimport time\nfrom .util import get_foreground_info\nfrom .config import load_config\nfrom .mappings import DEFAULT_MAPPINGS\nfrom .sender import send_sequence\n\nclass KeyMapper:\n    def __init__(self, config_path=None, registry_hash=None):\n        self.cfg = load_config(config_path=config_path, registry_hash=registry_hash)\n        self.global_mappings = DEFAULT_MAPPINGS.copy()\n        self.global_mappings.update(self.cfg.get(\"mappings\", {}) or {})\n        # per-process maps merge on top of global\n        self.per_process = {}\n        for proc, pm in (self.cfg.get(\"per_process_mappings\") or {}).items():\n            m = self.global_mappings.copy()\n            m.update(pm or {})\n            self.per_process[proc.lower()] = m\n        self.enabled_processes = [p.lower() for p in (self.cfg.get(\"enabled_processes\") or [])]\n        self.use_low_level = bool(self.cfg.get(\"use_low_level_send\", True))\n        self._hotkey_ids = []\n        self._stop = threading.Event()\n        self._install_hotkeys()\n\n    def _is_enabled_for(self, proc):\n        if proc is None:\n            return False\n        if not self.enabled_processes:\n            return True\n        return proc in self.enabled_processes\n\n    def _lookup_map(self, proc):\n        if proc and proc in self.per_process:\n            return self.per_process[proc]\n        return self.global_mappings\n\n    def _install_hotkeys(self):\n        # collect unique keys\n        keys = set(self.global_mappings.keys())\n        for pm in self.per_process.values():\n            keys.update(pm.keys())\n        for key in keys:\n            try:\n                hid = keyboard.add_hotkey(key, lambda k=key: self._handle(k), suppress=True)\n                self._hotkey_ids.append(hid)\n            except Exception:\n                try:\n                    hid = keyboard.add_hotkey(key, lambda k=key: self._handle(k), suppress=False)\n                    self._hotkey_ids.append(hid)\n                except Exception:\n                    pass\n\n    def _handle(self, emacs_key):\n        proc, cls, title = get_foreground_info()\n        if not self._is_enabled_for(proc):\n            # pass-through: re-inject original combo if possible\n            try:\n                keyboard.press_and_release(emacs_key)\n            except Exception:\n                pass\n            return\n        mapping = self._lookup_map(proc)\n        seq = mapping.get(emacs_key)\n        if seq is None:\n            try:\n                keyboard.press_and_release(emacs_key)\n            except Exception:\n                pass\n            return\n        if seq == \"\":\n            # explicit noop\n            return\n        send_sequence(seq, use_low_level=self.use_low_level)\n\n    def start(self):\n        self._stop.clear()\n        t = threading.Thread(target=self._watcher, daemon=True)\n        t.start()\n\n    def stop(self):\n        self._stop.set()\n        try:\n            keyboard.unhook_all_hotkeys()\n        except Exception:\n            pass\n\n    def _watcher(self):\n        while not self._stop.is_set():\n            time.sleep(1)\n";
    write_file("lib/emacskeys/listener.py", listener_py);

    /* lib/emacskeys/gui_tool.py */
    const char *gui_tool_py =
      "\"\"\"\nTkinter GUI to list / view / edit / import / export / delete registry mappings.\nProvides quick apply info (prints hash) — KeyMapper runner accepts --registry-hash.\n\"\"\"\n\nimport tkinter as tk\nfrom tkinter import ttk, filedialog, messagebox\nimport json\nimport winreg\nimport hashlib\nfrom .registry_store import list_all_mappings, store_text_under_hash, delete_hash\n\nREG_BASE = r\"Software\\EmacsKeysRegistry\"\n\ndef compute_hash(text: str) -> str:\n    return hashlib.sha256(text.encode(\"utf-8\")).hexdigest()\n\nclass GuiApp:\n    def __init__(self, root):\n        self.root = root\n        self.root.title(\"EmacsKeys Registry Editor\")\n        self.root.geometry(\"900x600\")\n        self._build_ui()\n        self._refresh()\n\n    def _build_ui(self):\n        p = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)\n        p.pack(fill=\"both\", expand=True)\n        left = ttk.Frame(p, width=320)\n        right = ttk.Frame(p)\n        p.add(left, weight=1)\n        p.add(right, weight=3)\n\n        ttk.Label(left, text=\"Stored mappings\").pack(anchor=\"w\", padx=6, pady=(6,0))\n        self.listbox = tk.Listbox(left)\n        self.listbox.pack(fill=\"both\", expand=True, padx=6, pady=6)\n        self.listbox.bind(\"<<ListboxSelect>>\", self._on_select)\n\n        lfbtn = ttk.Frame(left)\n        lfbtn.pack(fill=\"x\", padx=6, pady=6)\n        ttk.Button(lfbtn, text=\"Refresh\", command=self._refresh).pack(side=\"left\", padx=4)\n        ttk.Button(lfbtn, text=\"Import...\", command=self._import).pack(side=\"left\", padx=4)\n        ttk.Button(lfbtn, text=\"Delete\", command=self._delete).pack(side=\"left\", padx=4)\n        ttk.Button(lfbtn, text=\"Export...\", command=self._export).pack(side=\"left\", padx=4)\n\n        meta = ttk.Frame(right)\n        meta.pack(fill=\"x\", padx=6, pady=6)\n        ttk.Label(meta, text=\"Hash:\").grid(row=0, column=0, sticky=\"w\")\n        self.hash_var = tk.StringVar()\n        ttk.Entry(meta, textvariable=self.hash_var, state=\"readonly\", width=80).grid(row=0, column=1, sticky=\"w\")\n        ttk.Label(meta, text=\"Source:\").grid(row=1, column=0, sticky=\"w\")\n        self.src_var = tk.StringVar()\n        ttk.Entry(meta, textvariable=self.src_var, state=\"readonly\", width=80).grid(row=1, column=1, sticky=\"w\")\n\n        ttk.Label(right, text=\"JSON data\").pack(anchor=\"w\", padx=6)\n        self.text = tk.Text(right, wrap=\"none\")\n        self.text.pack(fill=\"both\", expand=True, padx=6, pady=(0,6))\n        xbar = ttk.Scrollbar(right, orient=\"horizontal\", command=self.text.xview)\n        xbar.pack(side=\"bottom\", fill=\"x\")\n        ybar = ttk.Scrollbar(right, orient=\"vertical\", command=self.text.yview)\n        ybar.pack(side=\"right\", fill=\"y\")\n        self.text.configure(xscrollcommand=xbar.set, yscrollcommand=ybar.set)\n\n        bot = ttk.Frame(right)\n        bot.pack(fill=\"x\", padx=6, pady=6)\n        ttk.Button(bot, text=\"Validate\", command=self._validate).pack(side=\"left\", padx=4)\n        ttk.Button(bot, text=\"Save to registry\", command=self._save).pack(side=\"left\", padx=4)\n        ttk.Button(bot, text=\"Save to file\", command=self._save_file).pack(side=\"left\", padx=4)\n        ttk.Button(bot, text=\"Apply (print hash)\", command=self._apply).pack(side=\"right\", padx=4)\n        ttk.Button(bot, text=\"Close\", command=self.root.quit).pack(side=\"right\", padx=4)\n\n    def _refresh(self):\n        self.listbox.delete(0, tk.END)\n        self.mapdata = list_all_mappings()\n        for hs, info in self.mapdata.items():\n            src = info.get(\"source_path\") or \"\"\n            label = f\"{hs[:8]}...  {src}\"\n            self.listbox.insert(tk.END, label)\n        self.hash_var.set(\"\")\n        self.src_var.set(\"\")\n        self.text.delete(\"1.0\", tk.END)\n\n    def _get_selected_hash(self):\n        sel = self.listbox.curselection()\n        if not sel:\n            return None\n        idx = sel[0]\n        keys = list(self.mapdata.keys())\n        if idx >= len(keys):\n            return None\n        return keys[idx]\n\n    def _on_select(self, ev=None):\n        hs = self._get_selected_hash()\n        if not hs:\n            return\n        info = self.mapdata.get(hs, {})\n        self.hash_var.set(hs)\n        self.src_var.set(info.get(\"source_path\") or \"\")\n        raw = info.get(\"raw\") or \"\"\n        try:\n            parsed = info.get(\"data\")\n            if parsed is not None:\n                pretty = json.dumps(parsed, indent=2, ensure_ascii=False)\n            else:\n                pretty = raw\n        except Exception:\n            pretty = raw\n        self.text.delete(\"1.0\", tk.END)\n        self.text.insert(\"1.0\", pretty)\n\n    def _import(self):\n        path = filedialog.askopenfilename(filetypes=[(\"JSON\",\"*.json\"),(\"All\",\"*.*\")])\n        if not path:\n            return\n        try:\n            with open(path, \"r\", encoding=\"utf-8\") as f:\n                txt = f.read()\n            json.loads(txt)\n        except Exception as e:\n            messagebox.showerror(\"Import failed\", str(e))\n            return\n        hs = store_text_under_hash(txt, source_path=path)\n        messagebox.showinfo(\"Imported\", f\"Stored under hash:\\n{hs}\")\n        self._refresh()\n\n    def _delete(self):\n        hs = self._get_selected_hash()\n        if not hs:\n            messagebox.showwarning(\"No selection\", \"Select an item first.\")\n            return\n        if not messagebox.askyesno(\"Confirm\", f\"Delete mapping {hs}?\"):\n            return\n        ok = delete_hash(hs)\n        if ok:\n            messagebox.showinfo(\"Deleted\", \"Deleted.\")\n            self._refresh()\n        else:\n            messagebox.showerror(\"Failed\", \"Delete failed.\")\n\n    def _export(self):\n        hs = self._get_selected_hash()\n        if not hs:\n            messagebox.showwarning(\"No selection\", \"Select.\")\n            return\n        info = self.mapdata.get(hs, {})\n        raw = info.get(\"raw\") or \"\"\n        dest = filedialog.asksaveasfilename(defaultextension=\".json\", filetypes=[(\"JSON\",\"*.json\")])\n        if not dest:\n            return\n        try:\n            with open(dest, \"w\", encoding=\"utf-8\") as f:\n                f.write(raw)\n            messagebox.showinfo(\"Exported\", dest)\n        except Exception as e:\n            messagebox.showerror(\"Export failed\", str(e))\n\n    def _validate(self):\n        txt = self.text.get(\"1.0\", tk.END).strip()\n        if not txt:\n            messagebox.showwarning(\"Empty\", \"Empty editor.\")\n            return\n        try:\n            json.loads(txt)\n            messagebox.showinfo(\"Valid\", \"JSON valid.\")\n        except Exception as e:\n            messagebox.showerror(\"Invalid\", str(e))\n\n    def _save(self):\n        txt = self.text.get(\"1.0\", tk.END).strip()\n        if not txt:\n            messagebox.showwarning(\"Empty\", \"Empty editor.\")\n            return\n        try:\n            json.loads(txt)\n        except Exception as e:\n            messagebox.showerror(\"Invalid JSON\", str(e))\n            return\n        # Save new entry; if editing existing, new hash will be created. Optionally delete old.\n        hs_new = store_text_under_hash(txt, source_path=self.src_var.get() or \"\")\n        messagebox.showinfo(\"Saved\", f\"Saved under hash:\\n{hs_new}\")\n        self._refresh()\n\n    def _save_file(self):\n        txt = self.text.get(\"1.0\", tk.END).strip()\n        if not txt:\n            messagebox.showwarning(\"Empty\", \"Empty.\")\n            return\n        dest = filedialog.asksaveasfilename(defaultextension=\".json\", filetypes=[(\"JSON\",\"*.json\")])\n        if not dest:\n            return\n        try:\n            json.loads(txt)\n            with open(dest, \"w\", encoding=\"utf-8\") as f:\n                f.write(txt)\n            messagebox.showinfo(\"Saved\", dest)\n        except Exception as e:\n            messagebox.showerror(\"Failed\", str(e))\n\n    def _apply(self):\n        hs = self._get_selected_hash()\n        if not hs:\n            messagebox.showwarning(\"No selection\", \"Select.\")\n            return\n        messagebox.showinfo(\"Apply\", f\"Selected mapping hash:\\n{hs}\\nUse: emacskeys --registry-hash {hs}\")\n\ndef main():\n    root = tk.Tk()\n    app = GuiApp(root)\n    root.mainloop()\n";
    write_file("lib/emacskeys/gui_tool.py", gui_tool_py);

    /* lib/emacskeys/runner.py */
    const char *runner_py =
      "import argparse\nimport sys\nimport time\nfrom .listener import KeyMapper\nfrom .registry_store import store_file_to_registry, list_all_mappings\n\ndef main():\n    parser = argparse.ArgumentParser(description=\"Emacs-like per-app keybindings (registry-backed)\")\n    parser.add_argument(\"--config-file\", \"-f\", help=\"Import JSON mapping file to registry and exit\", default=None)\n    parser.add_argument(\"--registry-hash\", \"-r\", help=\"Load mapping from registry by hash\", default=None)\n    parser.add_argument(\"--list-registry\", action=\"store_true\", help=\"List registry mappings\")\n    args = parser.parse_args()\n\n    if args.config_file:\n        try:\n            hs = store_file_to_registry(args.config_file)\n            print(\"Stored mapping with hash:\", hs)\n        except Exception as e:\n            print(\"Failed to store mapping:\", e)\n        return\n\n    if args.list_registry:\n        regs = list_all_mappings()\n        if not regs:\n            print(\"No registry mappings found.\")\n            return\n        for hs, info in regs.items():\n            sp = info.get(\"source_path\") or \"\"\n            print(hs, sp)\n        return\n\n    mapper = KeyMapper(config_path=None, registry_hash=args.registry_hash)\n    try:\n        print(\"Starting Emacs key mapper. Press Ctrl+C to exit.\")\n        mapper.start()\n        while True:\n            time.sleep(1)\n    except KeyboardInterrupt:\n        print(\"Stopping...\")\n        mapper.stop()\n        sys.exit(0)\n";
    write_file("lib/emacskeys/runner.py", runner_py);

    printf("All files generated.\n");
    return 0;
}
```

以上です。実行後に出力されたファイルを必要に応じて確認・編集し、Python 環境で動作確認してください。
