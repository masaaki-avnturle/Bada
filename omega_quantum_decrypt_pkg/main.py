"""omega_quantum_decrypt -- cross-platform GUI (Windows .exe & Android .apk).

Thin Kivy shell over :mod:`app_controller`.  The same file is the entry point
for both the PyInstaller Windows build and the Buildozer Android build.

Run from source:  python main.py
"""

from __future__ import annotations

import os

import app_controller as ctrl

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

if Window is not None:
    # keep inputs visible above the on-screen keyboard on Android
    Window.softinput_mode = "below_target"


class Root(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", padding=12, spacing=6, **kw)

        self.add_widget(Label(
            text="[b]omega_quantum_decrypt[/b]\nJones x Burau x Shor  +  virus removal",
            markup=True, size_hint_y=None, height=58, halign="center",
        ))

        # --- decrypt controls ---
        self.msg = TextInput(
            hint_text="secret message (blank = default)",
            size_hint_y=None, height=42, multiline=False,
        )
        self.braid = TextInput(
            text="3: 1 1 1", hint_text="braid, e.g. '3: 1 1 1'",
            size_hint_y=None, height=42, multiline=False,
        )
        self.add_widget(self.msg)
        self.add_widget(self.braid)
        row1 = BoxLayout(size_hint_y=None, height=44, spacing=8)
        for text, cb in (("Solve", self.on_solve), ("Jones", self.on_jones)):
            b = Button(text=text)
            b.bind(on_release=cb)
            row1.add_widget(b)
        self.add_widget(row1)

        # --- virus scan controls ---
        self.avpath = TextInput(
            text=self._default_scan_dir(), hint_text="folder to scan",
            size_hint_y=None, height=42, multiline=False,
        )
        self.add_widget(self.avpath)
        row2 = BoxLayout(size_hint_y=None, height=44, spacing=8)
        for text, cb in (
            ("Scan", self.on_scan),
            ("Scan+Quarantine", self.on_disinfect),
            ("Quarantine list", self.on_qlist),
        ):
            b = Button(text=text)
            b.bind(on_release=cb)
            row2.add_widget(b)
        self.add_widget(row2)

        self.out = Label(
            text="Press Solve (decrypt demo) or Scan (virus scan).", markup=False,
            size_hint_y=None, halign="left", valign="top", font_size="13sp",
        )
        self.out.bind(
            width=lambda *_: setattr(self.out, "text_size", (self.out.width, None)),
            texture_size=lambda *_: setattr(self.out, "height", self.out.texture_size[1]),
        )
        sv = ScrollView()
        sv.add_widget(self.out)
        self.add_widget(sv)

    @staticmethod
    def _default_scan_dir():
        # On Android, app storage; on desktop, home.
        for env in ("EXTERNAL_STORAGE", "ANDROID_PRIVATE"):
            if os.environ.get(env):
                return os.environ[env]
        return os.path.expanduser("~")

    def _show(self, text):
        self.out.text = text

    def _run(self, fn, *a):
        try:
            self._show(fn(*a))
        except Exception as exc:  # keep the app alive on bad input
            self._show(f"error: {exc}")

    def on_solve(self, *_):
        self._run(ctrl.demo_solve, self.msg.text, self.braid.text or "3: 1 1 1")

    def on_jones(self, *_):
        self._run(ctrl.jones_report, self.braid.text or "2: 1 1 1")

    def on_scan(self, *_):
        self._run(ctrl.scan_report, self.avpath.text)

    def on_disinfect(self, *_):
        self._run(ctrl.disinfect_report, self.avpath.text)

    def on_qlist(self, *_):
        self._run(ctrl.quarantine_report)


class OmegaQuantumDecryptApp(App):
    title = "omega_quantum_decrypt"

    def build(self):
        return Root()


if __name__ == "__main__":
    OmegaQuantumDecryptApp().run()
