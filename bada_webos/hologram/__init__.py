"""Hologram Display — project the equation-group videos onto a four-mirror
reflection pyramid, modulated by the Bada beta(p,q) light field."""

from .app import HologramApp, HoloKeyboardApp
from .render import html_hologram
from .floatup import html_floatup
from .keyboard import html_keyboard

__all__ = ["HologramApp", "HoloKeyboardApp",
           "html_hologram", "html_floatup", "html_keyboard"]
