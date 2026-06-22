"""Hologram Display — project the equation-group videos onto a four-mirror
reflection pyramid, modulated by the Bada beta(p,q) light field."""

from .app import (HologramApp, HoloKeyboardApp, MirrorApp, VisionApp,
                  GlassApp, FreeformApp)
from .render import html_hologram
from .floatup import html_floatup
from .keyboard import html_keyboard
from .mirror import html_mirror
from .spatial import html_vision
from .glass import html_glass
from .freeform import html_freeform

__all__ = ["HologramApp", "HoloKeyboardApp", "MirrorApp", "VisionApp",
           "GlassApp", "FreeformApp", "html_hologram", "html_floatup",
           "html_keyboard", "html_mirror", "html_vision", "html_glass",
           "html_freeform"]
