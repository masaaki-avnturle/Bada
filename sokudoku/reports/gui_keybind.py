以下は、HKCU\Software\EmacsKeysRegistry に保存されたマッピング（SHA256 ハッシュごとの JSON）を一覧表示・閲覧・編集・削除・インポート（ファイル→レジストリ）・エクスポート（レジストリ→ファイル）できるシンプルな GUI ツールの全ソースコードです。Python の標準 GUI ライブラリ tkinter を使っています。既存パッケージ構成に合わせて `bin/` と `lib/emacskeys/` に分けた形で提供します。

注意
- Windows 専用（winreg を使用）。レジストリ変更は HKCU のため通常管理者権限は不要ですが、実行前に内容を確認してください。
- 依存: Python 標準 (tkinter) と標準ライブラリのみ（tkinter が環境にない場合は追加インストールが必要）。
- このツールは入力された JSON を検証しますが、マッピングの内容の正しさは保証しません。編集は自己責任で行ってください。

ファイル一覧
- bin/emacskeys_gui.py
- lib/emacskeys/gui_tool.py

1) bin/emacskeys_gui.py
```python
#!/usr/bin/env python3
from emacskeys.gui_tool import main

if __name__ == "__main__":
    main()
```

2) lib/emacskeys/gui_tool.py
```python
"""
EmacsKeys Registry GUI tool
- Lists registry-stored mapping files under HKCU\Software\EmacsKeysRegistry
- Allows view, edit, delete, import (from file), export (to file)
- Uses tkinter for UI
"""

import json
import hashlib
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import winreg

REG_BASE = r"Software\EmacsKeysRegistry"

def compute_hash_of_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def open_base_key(create=False):
    try:
        if create:
            return winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_BASE)
        return winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_BASE, 0, winreg.KEY_READ)
    except FileNotFoundError:
        if create:
            return winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_BASE)
        raise

def list_mappings():
    """
    Return dict: {hash: {"source_path": str_or_empty, "data": parsed_json_or_none, "raw": text}}
    """
    out = {}
    try:
        base = open_base_key(create=False)
    except FileNotFoundError:
        return out
    i = 0
    try:
        while True:
            sub = winreg.EnumKey(base, i)
            i += 1
            try:
                k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_BASE + "\\" + sub, 0, winreg.KEY_READ)
                raw, _ = winreg.QueryValueEx(k, "data")
                try:
                    src, _ = winreg.QueryValueEx(k, "source_path")
                except Exception:
                    src = ""
                try:
                    parsed = json.loads(raw)
                except Exception:
                    parsed = None
                out[sub] = {"data": parsed, "raw": raw, "source_path": src}
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

def store_text_under_hash(text: str, source_path: str = "") -> str:
    hs = compute_hash_of_text(text)
    keypath = REG_BASE + "\\" + hs
    k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, keypath)
    winreg.SetValueEx(k, "data", 0, winreg.REG_SZ, text)
    winreg.SetValueEx(k, "source_path", 0, winreg.REG_SZ, source_path)
    winreg.CloseKey(k)
    return hs

def delete_hash(hs: str) -> bool:
    try:
        # delete values and key
        keypath = REG_BASE + "\\" + hs
        # open then delete values if exist
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
        # delete subkey
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, keypath)
        return True
    except Exception:
        return False

class GuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EmacsKeys Registry Editor")
        self.root.geometry("900x600")
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        frm = ttk.Frame(self.root)
        frm.pack(fill="both", expand=True)

        left = ttk.Frame(frm, width=300)
        left.pack(side="left", fill="y")
        right = ttk.Frame(frm)
        right.pack(side="right", fill="both", expand=True)

        # Listbox for hashes
        ttk.Label(left, text="Stored mappings:").pack(anchor="w", padx=6, pady=(6,0))
        self.listbox = tk.Listbox(left, width=44, exportselection=False)
        self.listbox.pack(fill="y", expand=True, padx=6, pady=6)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        btnf = ttk.Frame(left)
        btnf.pack(fill="x", padx=6, pady=6)
        ttk.Button(btnf, text="Refresh", command=self._refresh_list).pack(side="left", padx=2)
        ttk.Button(btnf, text="Import file...", command=self._import_file).pack(side="left", padx=2)
        ttk.Button(btnf, text="Delete", command=self._delete_selected).pack(side="left", padx=2)
        ttk.Button(btnf, text="Export...", command=self._export_selected).pack(side="left", padx=2)

        # Right: details and editor
        meta_fr = ttk.Frame(right)
        meta_fr.pack(fill="x", padx=6, pady=6)
        ttk.Label(meta_fr, text="Hash:").grid(row=0, column=0, sticky="w")
        self.hash_var = tk.StringVar()
        ttk.Entry(meta_fr, textvariable=self.hash_var, state="readonly", width=60).grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(meta_fr, text="Source path:").grid(row=1, column=0, sticky="w")
        self.src_var = tk.StringVar()
        ttk.Entry(meta_fr, textvariable=self.src_var, state="readonly", width=60).grid(row=1, column=1, sticky="w", padx=4)

        # Text editor for JSON
        ttk.Label(right, text="JSON data:").pack(anchor="w", padx=6)
        self.text = tk.Text(right, wrap="none", undo=True)
        self.text.pack(fill="both", expand=True, padx=6, pady=(0,6))

        # horizontal & vertical scrollbars
        xscroll = ttk.Scrollbar(right, orient="horizontal", command=self.text.xview)
        xscroll.pack(side="bottom", fill="x")
        yscroll = ttk.Scrollbar(right, orient="vertical", command=self.text.yview)
        yscroll.pack(side="right", fill="y")
        self.text.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)

        # bottom buttons
        bot = ttk.Frame(right)
        bot.pack(fill="x", padx=6, pady=6)
        ttk.Button(bot, text="Validate JSON", command=self._validate_json).pack(side="left", padx=4)
        ttk.Button(bot, text="Save to registry", command=self._save_to_registry).pack(side="left", padx=4)
        ttk.Button(bot, text="Save to file...", command=self._save_to_file).pack(side="left", padx=4)
        ttk.Button(bot, text="Close", command=self.root.quit).pack(side="right", padx=4)

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        self.mappings = list_mappings()
        for hs, info in self.mappings.items():
            label = hs[:8] + "..."  # short
            src = info.get("source_path") or ""
            display = f"{label}  {src}"
            self.listbox.insert(tk.END, display)
        # clear details
        self.hash_var.set("")
        self.src_var.set("")
        self.text.delete("1.0", tk.END)

    def _get_selected_hash(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        index = sel[0]
        keys = list(self.mappings.keys())
        if index >= len(keys):
            return None
        return keys[index]

    def _on_select(self, ev=None):
        hs = self._get_selected_hash()
        if not hs:
            return
        info = self.mappings.get(hs)
        self.hash_var.set(hs)
        self.src_var.set(info.get("source_path") or "")
        raw = info.get("raw") or ""
        # pretty-print JSON if possible
        try:
            parsed = info.get("data")
            if parsed is not None:
                pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
            else:
                pretty = raw
        except Exception:
            pretty = raw
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", pretty)

    def _import_file(self):
        path = filedialog.askopenfilename(title="Select JSON mapping file", filetypes=[("JSON","*.json"),("All","*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                txt = f.read()
            # validate json
            _ = json.loads(txt)
        except Exception as e:
            messagebox.showerror("Import error", f"Failed to read/parse JSON:\n{e}")
            return
        hs = store_text_under_hash(txt, source_path=path)
        messagebox.showinfo("Imported", f"Stored mapping under hash:\n{hs}")
        self._refresh_list()

    def _delete_selected(self):
        hs = self._get_selected_hash()
        if not hs:
            messagebox.showwarning("No selection", "Select an item first.")
            return
        if not messagebox.askyesno("Confirm delete", f"Delete mapping {hs}?"):
            return
        ok = delete_hash(hs)
        if ok:
            messagebox.showinfo("Deleted", f"Mapping {hs} deleted.")
            self._refresh_list()
        else:
            messagebox.showerror("Failed", "Failed to delete mapping. It may not exist or be locked.")

    def _export_selected(self):
        hs = self._get_selected_hash()
        if not hs:
            messagebox.showwarning("No selection", "Select an item first.")
            return
        info = self.mappings.get(hs)
        raw = info.get("raw") or ""
        dest = filedialog.asksaveasfilename(title="Export JSON to file", defaultextension=".json", filetypes=[("JSON","*.json")])
        if not dest:
            return
        try:
            with open(dest, "w", encoding="utf-8") as f:
                f.write(raw)
            messagebox.showinfo("Exported", f"Exported to {dest}")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    def _validate_json(self):
        txt = self.text.get("1.0", tk.END).strip()
        if not txt:
            messagebox.showwarning("Empty", "Editor is empty.")
            return
        try:
            parsed = json.loads(txt)
            messagebox.showinfo("Valid", "JSON is valid.")
        except Exception as e:
            messagebox.showerror("Invalid JSON", str(e))

    def _save_to_registry(self):
        txt = self.text.get("1.0", tk.END).strip()
        if not txt:
            messagebox.showwarning("Empty", "Editor is empty.")
            return
        try:
            parsed = json.loads(txt)
        except Exception as e:
            messagebox.showerror("Invalid JSON", f"Cannot save: {e}")
            return
        # ask whether to overwrite selected or create new
        hs_sel = self._get_selected_hash()
        if hs_sel and messagebox.askyesno("Overwrite", "Overwrite selected registry entry?"):
            # store under same hash? If content changed, hash will differ. We will store under new hash and delete old if user confirms.
            new_hs = store_text_under_hash(txt, source_path=self.mappings.get(hs_sel, {}).get("source_path", ""))
            if new_hs != hs_sel:
                if messagebox.askyesno("Replace old", f"New hash {new_hs} differs from old {hs_sel}. Delete old entry?"):
                    delete_hash(hs_sel)
            messagebox.showinfo("Saved", f"Saved mapping under hash {new_hs}")
        else:
            new_hs = store_text_under_hash(txt, source_path="")
            messagebox.showinfo("Saved", f"Saved mapping under hash {new_hs}")
        self._refresh_list()

    def _save_to_file(self):
        txt = self.text.get("1.0", tk.END).strip()
        if not txt:
            messagebox.showwarning("Empty", "Editor is empty.")
            return
        dest = filedialog.asksaveasfilename(title="Save JSON to file", defaultextension=".json", filetypes=[("JSON","*.json")])
        if not dest:
            return
        try:
            # validate
            _ = json.loads(txt)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(txt)
            messagebox.showinfo("Saved", f"Saved to {dest}")
        except Exception as e:
            messagebox.showerror("Failed", str(e))

def main():
    root = tk.Tk()
    app = GuiApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
```

使い方
- 必要ファイルを配置:
  - bin/emacskeys_gui.py（実行可能ビットまたはダブルクリックで起動）
  - lib/emacskeys/gui_tool.py
- 実行:
  - python bin/emacskeys_gui.py
  - または、インストール済みパッケージであれば `emacskeys_gui` のようにエントリポイントを作ることもできます（ここではエントリポイントは設定していません）。
- 主な操作:
  - Refresh: レジストリ一覧を更新
  - Import file: JSON ファイルを読み、ハッシュ化して HKCU\Software\EmacsKeysRegistry\<sha256> に格納
  - Delete: 選択したハッシュのエントリを削除
  - Export: 選択したエントリをファイルに保存
  - 編集領域で JSON を編集 → Validate JSON → Save to registry（新規または上書き的に登録）

拡張案（必要なら実装可）
- マッピングの「適用中」ハッシュを設定して KeyMapper が指定ハッシュを読み込む仕組み（現在は runner で --registry-hash 指定）。
- JSON 編集の差分プレビュー・競合解決
- GUI で直接 KeyMapper を起動/停止するボタン

必要なら、上記の GUI に「現在選択中のマッピングを即座に KeyMapper に適用する」機能を追加しますか？
