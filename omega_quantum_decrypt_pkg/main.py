"""omega_quantum_decrypt -- cross-platform GUI (Windows .exe & Android .apk).

Thin Kivy shell over :mod:`app_controller`.  The same file is the entry point
for both the PyInstaller Windows build and the Buildozer Android build.

Run from source:  python main.py
"""

from __future__ import annotations

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
        super().__init__(orientation="vertical", padding=12, spacing=8, **kw)

        self.add_widget(Label(
            text="[b]omega_quantum_decrypt[/b]\nJones x Burau x Shor",
            markup=True, size_hint_y=None, height=64, halign="center",
        ))

        self.msg = TextInput(
            hint_text="secret message (blank = default)",
            size_hint_y=None, height=44, multiline=False,
        )
        self.braid = TextInput(
            text="3: 1 1 1", hint_text="braid, e.g. '3: 1 1 1'",
            size_hint_y=None, height=44, multiline=False,
        )
        self.add_widget(self.msg)
        self.add_widget(self.braid)

        buttons = BoxLayout(size_hint_y=None, height=48, spacing=8)
        for text, cb in (
            ("Solve", self.on_solve),
            ("Jones", self.on_jones),
        ):
            b = Button(text=text)
            b.bind(on_release=cb)
            buttons.add_widget(b)
        self.add_widget(buttons)

        self.out = Label(
            text="Enter a secret and press Solve.", markup=False,
            size_hint_y=None, halign="left", valign="top", font_size="13sp",
        )
        self.out.bind(
            width=lambda *_: setattr(self.out, "text_size", (self.out.width, None)),
            texture_size=lambda *_: setattr(self.out, "height", self.out.texture_size[1]),
        )
        sv = ScrollView()
        sv.add_widget(self.out)
        self.add_widget(sv)

    def _show(self, text):
        self.out.text = text

    def on_solve(self, *_):
        try:
            self._show(ctrl.demo_solve(self.msg.text, self.braid.text or "3: 1 1 1"))
        except Exception as exc:  # keep the app alive on bad input
            self._show(f"error: {exc}")

    def on_jones(self, *_):
        try:
            self._show(ctrl.jones_report(self.braid.text or "2: 1 1 1"))
        except Exception as exc:
            self._show(f"error: {exc}")


class OmegaQuantumDecryptApp(App):
    title = "omega_quantum_decrypt"

    def build(self):
        return Root()


if __name__ == "__main__":
    OmegaQuantumDecryptApp().run()
