"""Hologram Display — project the equation-group videos onto a four-mirror
reflection pyramid, modulated by the Bada beta(p,q) light field."""

from .app import HologramApp
from .render import html_hologram

__all__ = ["HologramApp", "html_hologram"]
