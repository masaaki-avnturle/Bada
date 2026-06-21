"""All equation-group graphs as a PowerPoint-style flash-transition slideshow."""

from . import bridge
from .app import SlideshowApp, REPORT_CATALOG
from .render import html_slideshow

__all__ = ["bridge", "SlideshowApp", "REPORT_CATALOG", "html_slideshow"]
