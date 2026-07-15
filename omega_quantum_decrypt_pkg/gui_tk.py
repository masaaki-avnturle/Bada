"""omega_quantum_decrypt -- desktop GUI for the Windows .exe (Tkinter).

Two tabs sharing one output pane:
  * Decrypt     -- the Jones x Burau x Shor demo.
  * Virus scan  -- defensive scanner: scan a folder, quarantine (encrypt away)
                   detected files, list/restore/remove quarantine.

Tkinter ships with CPython and needs no OpenGL, so it builds reliably with
PyInstaller on headless CI (unlike Kivy).  Android uses the Kivy front-end in
main.py; both share app_controller.

Run from source:  python gui_tk.py
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, ttk

import app_controller as ctrl


class App:
    def __init__(self, root: tk.Tk):
        root.title("omega_quantum_decrypt")
        root.geometry("820x620")
        root.minsize(620, 460)

        outer = ttk.Frame(root, padding=10)
        outer.pack(fill="both", expand=True)

        ttk.Label(
            outer, text="omega_quantum_decrypt  —  Jones × Burau × Shor  +  Virus removal",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        nb = ttk.Notebook(outer)
        nb.pack(fill="x")
        self._build_decrypt_tab(nb)
        self._build_av_tab(nb)

        self.out = tk.Text(outer, wrap="word", font=("Consolas", 10), height=22)
        self.out.pack(fill="both", expand=True, pady=(10, 0))
        sb = ttk.Scrollbar(outer, command=self.out.yview)
        sb.place(relx=1.0, rely=1.0, anchor="se")
        self.out.configure(yscrollcommand=sb.set)
        self._show("Choose a tab. 'Decrypt' runs the Shor demo; "
                   "'Virus scan' scans a folder and quarantines threats.")

    # -- tabs -----------------------------------------------------------
    def _build_decrypt_tab(self, nb):
        f = ttk.Frame(nb, padding=8)
        nb.add(f, text="Decrypt")
        ttk.Label(f, text="Secret message:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.msg = ttk.Entry(f, width=48)
        self.msg.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        ttk.Label(f, text="Braid (key):").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        self.braid = ttk.Entry(f, width=48)
        self.braid.insert(0, "3: 1 1 1")
        self.braid.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        b = ttk.Frame(f)
        b.grid(row=2, column=0, columnspan=2, sticky="w", padx=4, pady=6)
        ttk.Button(b, text="Solve (decrypt)", command=self.on_solve).pack(side="left", padx=4)
        ttk.Button(b, text="Jones info", command=self.on_jones).pack(side="left", padx=4)
        f.columnconfigure(1, weight=1)

    def _build_av_tab(self, nb):
        f = ttk.Frame(nb, padding=8)
        nb.add(f, text="Virus scan")
        ttk.Label(f, text="Folder / file:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.avpath = ttk.Entry(f, width=44)
        self.avpath.insert(0, os.path.expanduser("~"))
        self.avpath.grid(row=0, column=1, sticky="ew", padx=4, pady=4)
        ttk.Button(f, text="Browse…", command=self._browse).grid(row=0, column=2, padx=4)
        b = ttk.Frame(f)
        b.grid(row=1, column=0, columnspan=3, sticky="w", padx=4, pady=6)
        ttk.Button(b, text="Scan", command=self.on_scan).pack(side="left", padx=4)
        ttk.Button(b, text="Scan + Quarantine", command=self.on_disinfect).pack(side="left", padx=4)
        ttk.Button(b, text="Quarantine list", command=self.on_qlist).pack(side="left", padx=4)
        rr = ttk.Frame(f)
        rr.grid(row=2, column=0, columnspan=3, sticky="w", padx=4, pady=2)
        ttk.Label(rr, text="Quarantine id:").pack(side="left", padx=4)
        self.qid = ttk.Entry(rr, width=20)
        self.qid.pack(side="left", padx=4)
        ttk.Button(rr, text="Restore", command=lambda: self.on_qaction("restore")).pack(side="left", padx=4)
        ttk.Button(rr, text="Remove", command=lambda: self.on_qaction("remove")).pack(side="left", padx=4)
        f.columnconfigure(1, weight=1)

    # -- helpers --------------------------------------------------------
    def _show(self, text):
        self.out.delete("1.0", "end")
        self.out.insert("1.0", text)

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.avpath.get() or os.path.expanduser("~"))
        if d:
            self.avpath.delete(0, "end")
            self.avpath.insert(0, d)

    def _run(self, fn, *a):
        try:
            self._show(fn(*a))
        except Exception as exc:
            self._show(f"error: {exc}")

    # -- decrypt handlers ----------------------------------------------
    def on_solve(self):
        self._run(ctrl.demo_solve, self.msg.get(), self.braid.get() or "3: 1 1 1")

    def on_jones(self):
        self._run(ctrl.jones_report, self.braid.get() or "2: 1 1 1")

    # -- antivirus handlers --------------------------------------------
    def on_scan(self):
        self._run(ctrl.scan_report, self.avpath.get())

    def on_disinfect(self):
        self._run(ctrl.disinfect_report, self.avpath.get())

    def on_qlist(self):
        self._run(ctrl.quarantine_report)

    def on_qaction(self, action):
        self._run(ctrl.quarantine_action, action, self.qid.get().strip())


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
