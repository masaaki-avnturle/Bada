import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import hashlib
from .registry_store import list_all_mappings, store_text_under_hash, delete_hash

class GuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EmacsKeys Registry Editor")
        self.root.geometry("900x600")
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        p = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        p.pack(fill="both", expand=True)
        left = ttk.Frame(p, width=320)
        right = ttk.Frame(p)
        p.add(left, weight=1)
        p.add(right, weight=3)

        ttk.Label(left, text="Stored mappings").pack(anchor="w", padx=6, pady=(6,0))
        self.listbox = tk.Listbox(left)
        self.listbox.pack(fill="both", expand=True, padx=6, pady=6)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        lfbtn = ttk.Frame(left)
        lfbtn.pack(fill="x", padx=6, pady=6)
        ttk.Button(lfbtn, text="Refresh", command=self._refresh).pack(side="left", padx=4)
        ttk.Button(lfbtn, text="Import...", command=self._import).pack(side="left", padx=4)
        ttk.Button(lfbtn, text="Delete", command=self._delete).pack(side="left", padx=4)
        ttk.Button(lfbtn, text="Export...", command=self._export).pack(side="left", padx=4)

        meta = ttk.Frame(right)
        meta.pack(fill="x", padx=6, pady=6)
        ttk.Label(meta, text="Hash:").grid(row=0, column=0, sticky="w")
        self.hash_var = tk.StringVar()
        ttk.Entry(meta, textvariable=self.hash_var, state="readonly", width=80).grid(row=0, column=1, sticky="w")
        ttk.Label(meta, text="Source:").grid(row=1, column=0, sticky="w")
        self.src_var = tk.StringVar()
        ttk.Entry(meta, textvariable=self.src_var, state="readonly", width=80).grid(row=1, column=1, sticky="w")

        ttk.Label(right, text="JSON data").pack(anchor="w", padx=6)
        self.text = tk.Text(right, wrap="none")
        self.text.pack(fill="both", expand=True, padx=6, pady=(0,6))
        xbar = ttk.Scrollbar(right, orient="horizontal", command=self.text.xview)
        xbar.pack(side="bottom", fill="x")
        ybar = ttk.Scrollbar(right, orient="vertical", command=self.text.yview)
        ybar.pack(side="right", fill="y")
        self.text.configure(xscrollcommand=xbar.set, yscrollcommand=ybar.set)

        bot = ttk.Frame(right)
        bot.pack(fill="x", padx=6, pady=6)
        ttk.Button(bot, text="Validate", command=self._validate).pack(side="left", padx=4)
        ttk.Button(bot, text="Save to registry", command=self._save).pack(side="left", padx=4)
        ttk.Button(bot, text="Save to file", command=self._save_file).pack(side="left", padx=4)
        ttk.Button(bot, text="Apply (print hash)", command=self._apply).pack(side="right", padx=4)
        ttk.Button(bot, text="Close", command=self.root.quit).pack(side="right", padx=4)

    def _refresh(self):
        self.listbox.delete(0, tk.END)
        self.mapdata = list_all_mappings()
        for hs, info in self.mapdata.items():
            src = info.get("source_path") or ""
            label = f"{hs[:8]}...  {src}"
            self.listbox.insert(tk.END, label)
        self.hash_var.set("")
        self.src_var.set("")
        self.text.delete("1.0", tk.END)

    def _get_selected_hash(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        idx = sel[0]
        keys = list(self.mapdata.keys())
        if idx >= len(keys):
            return None
        return keys[idx]

    def _on_select(self, ev=None):
        hs = self._get_selected_hash()
        if not hs:
            return
        info = self.mapdata.get(hs, {})
        self.hash_var.set(hs)
        self.src_var.set(info.get("source_path") or "")
        raw = info.get("raw") or ""
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

    def _import(self):
        path = filedialog.askopenfilename(filetypes=[("JSON","*.json"),("All","*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                txt = f.read()
            json.loads(txt)
        except Exception as e:
            messagebox.showerror("Import failed", str(e))
            return
        hs = store_text_under_hash(txt, source_path=path)
        messagebox.showinfo("Imported", f"Stored under hash:\n{hs}")
        self._refresh()

    def _delete(self):
        hs = self._get_selected_hash()
        if not hs:
            messagebox.showwarning("No selection", "Select an item first.")
            return
        if not messagebox.askyesno("Confirm", f"Delete mapping {hs}?"):
            return
        ok = delete_hash(hs)
        if ok:
            messagebox.showinfo("Deleted", "Deleted.")
            self._refresh()
        else:
            messagebox.showerror("Failed", "Delete failed.")

    def _export(self):
        hs = self._get_selected_hash()
        if not hs:
            messagebox.showwarning("No selection", "Select.")
            return
        info = self.mapdata.get(hs, {})
        raw = info.get("raw") or ""
        dest = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if not dest:
            return
        try:
            with open(dest, "w", encoding="utf-8") as f:
                f.write(raw)
            messagebox.showinfo("Exported", dest)
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    def _validate(self):
        txt = self.text.get("1.0", tk.END).strip()
        if not txt:
            messagebox.showwarning("Empty", "Empty editor.")
            return
        try:
            json.loads(txt)
            messagebox.showinfo("Valid", "JSON valid.")
        except Exception as e:
            messagebox.showerror("Invalid", str(e))

    def _save(self):
        txt = self.text.get("1.0", tk.END).strip()
        if not txt:
            messagebox.showwarning("Empty", "Empty editor.")
            return
        try:
            json.loads(txt)
        except Exception as e:
            messagebox.showerror("Invalid JSON", str(e))
            return
        hs_new = store_text_under_hash(txt, source_path=self.src_var.get() or "")
        messagebox.showinfo("Saved", f"Saved under hash:\n{hs_new}")
        self._refresh()

    def _save_file(self):
        txt = self.text.get("1.0", tk.END).strip()
        if not txt:
            messagebox.showwarning("Empty", "Empty.")
            return
        dest = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
        if not dest:
            return
        try:
            json.loads(txt)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(txt)
            messagebox.showinfo("Saved", dest)
        except Exception as e:
            messagebox.showerror("Failed", str(e))

    def _apply(self):
        hs = self._get_selected_hash()
        if not hs:
            messagebox.showwarning("No selection", "Select.")
            return
        messagebox.showinfo("Apply", f"Selected mapping hash:\n{hs}\nUse: emacskeys --registry-hash {hs}")

def main():
    root = tk.Tk()
    app = GuiApp(root)
    root.mainloop()
