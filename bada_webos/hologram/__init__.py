"""Hologram Display — project the equation-group videos onto a four-mirror
reflection pyramid, modulated by the Bada beta(p,q) light field."""

from .app import HologramApp, HoloKeyboardApp, MirrorApp
from .render import html_hologram
from .floatup import html_floatup
from .keyboard import html_keyboard
from .mirror import html_mirror

__all__ = ["HologramApp", "HoloKeyboardApp", "MirrorApp",
           "html_hologram", "html_floatup", "html_keyboard", "html_mirror"]
