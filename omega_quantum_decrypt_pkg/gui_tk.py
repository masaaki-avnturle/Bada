"""omega_quantum_decrypt -- desktop GUI for the Windows .exe (Tkinter).

Tkinter ships with CPython and needs no OpenGL, so it builds cleanly with
PyInstaller on headless CI runners (unlike Kivy, which requires a GL>=2.0
context).  Android uses the Kivy front-end in ``main.py`` instead; both share
the same logic in :mod:`app_controller`.

Run from source:  python gui_tk.py
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import app_controller as ctrl


class App:
    def __init__(self, root: tk.Tk):
        root.title("omega_quantum_decrypt")
        root.geometry("760x560")
        root.minsize(560, 420)

        pad = {"padx": 8, "pady": 4}
        frm = ttk.Frame(root, padding=10)
        frm.pack(fill="both", expand=True)

        ttk.Label(
            frm, text="omega_quantum_decrypt  —  Jones × Burau × Shor",
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", **pad)

        ttk.Label(frm, text="Secret message:").grid(row=1, column=0, sticky="w", **pad)
        self.msg = ttk.Entry(frm)
        self.msg.grid(row=1, column=1, columnspan=2, sticky="ew", **pad)

        ttk.Label(frm, text="Braid (key):").grid(row=2, column=0, sticky="w", **pad)
        self.braid = ttk.Entry(frm)
        self.braid.insert(0, "3: 1 1 1")
        self.braid.grid(row=2, column=1, columnspan=2, sticky="ew", **pad)

        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=3, sticky="w", **pad)
        ttk.Button(btns, text="Solve (decrypt)", command=self.on_solve).pack(side="left", padx=4)
        ttk.Button(btns, text="Jones info", command=self.on_jones).pack(side="left", padx=4)
        ttk.Button(btns, text="Clear", command=lambda: self._show("")).pack(side="left", padx=4)

        self.out = tk.Text(frm, wrap="word", font=("Consolas", 10), height=20)
        self.out.grid(row=4, column=0, columnspan=3, sticky="nsew", **pad)
        sb = ttk.Scrollbar(frm, command=self.out.yview)
        sb.grid(row=4, column=3, sticky="ns")
        self.out.configure(yscrollcommand=sb.set)

        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(4, weight=1)
        self._show("Enter a secret message and press 'Solve (decrypt)'.")

    def _show(self, text: str):
        self.out.delete("1.0", "end")
        self.out.insert("1.0", text)

    def on_solve(self):
        try:
            self._show(ctrl.demo_solve(self.msg.get(), self.braid.get() or "3: 1 1 1"))
        except Exception as exc:  # keep the window alive on bad input
            self._show(f"error: {exc}")

    def on_jones(self):
        try:
            self._show(ctrl.jones_report(self.braid.get() or "2: 1 1 1"))
        except Exception as exc:
            self._show(f"error: {exc}")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
