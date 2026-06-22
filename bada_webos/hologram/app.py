"""HologramApp — project the equation-group videos onto a Hologram Display.

Reuses the equation-group surfaces (eqvideo / transport / slideshow, all
computed in Bada) as the source video, and the hologram light field
(apps/hologram/lib/hologram.bada) as the reflective modulation, then composes
the four-mirror reflection pyramid from the "Hologram Display" report.
"""

from __future__ import annotations

from . import bridge
from .render import html_hologram
from .floatup import html_floatup
from .keyboard import html_keyboard
from .mirror import html_mirror
from .spatial import html_vision
from .glass import html_glass
from .freeform import html_freeform

TABLET_AREA_CM2 = 200.0   # ~10" tablet panel
BATTERY_WH = 40.0         # tablet battery
DEFAULT_BUDGET_W = 5.0    # power budget for the float-up display
GAP_CM = 12.0             # tablet ↔ phone-mirror gap
VMAX = 0.9                # max v/c on the relativity slider


def _grid_mean(g):
    return sum(v for row in g for v in row) / (len(g) * len(g[0]))


class HologramApp:
    def __init__(self, n: int = 14, frames: int = 16, names: list = None):
        self.n = n
        self.frames = frames
        self.names = names

    def boot(self) -> dict:
        from eqvideo import bridge as ev
        from transport import bridge as tr
        from slideshow import bridge as rp
        from eqvideo.render import CATALOG as EV_CAT
        from transport.app import CATALOG as TR_CAT
        from slideshow.app import REPORT_CATALOG as RP_CAT

        ev_names, tr_names, rp_names = ev.names(), tr.names(), rp.names()
        catalog = {**EV_CAT, **TR_CAT, **RP_CAT}
        order = ev_names + tr_names + rp_names
        use = self.names or order

        fb = {}
        for nm in use:
            b = (ev if nm in ev_names else tr if nm in tr_names else rp)
            fb[nm] = b.frames(nm, self.n, self.frames)
        self.frames_by_name = fb
        self.catalog = {nm: catalog[nm] for nm in use}

        # the hologram light field + reflection geometry, from Bada
        self.light_frames = bridge.light_frames("mag", self.n, self.frames)
        self.quads = [{"name": q, "rot": bridge.quad_rot(q)}
                      for q in bridge.quad_names()]

        self.report = {
            "sources": use, "n_sources": len(use),
            "mirrors": [q["name"] for q in self.quads],
            "light": "beta(p,q) complex amplitude (re/im surfaces)",
        }
        return self.report

    def html(self, free: bool = False) -> str:
        return html_hologram(self.frames_by_name, self.light_frames, self.n,
                             self.catalog, self.quads, free)

    def save_html(self, path: str, free: bool = False) -> str:
        with open(path, "w") as f:
            f.write(self.html(free))
        return path

    # --- float-up display: Jones relief + conductive-plastic power ----------
    def _float_data(self):
        """Jones relief frames + per-frame tablet power (all from Bada)."""
        if not hasattr(self, "relief_frames"):
            self.relief_frames = bridge.relief_frames(self.n, self.frames)
            self.jones_poly = bridge.jones_polynomial()
            self.mean_relief, self.power = [], []
            for k in range(self.frames):
                mb = _grid_mean(self.light_frames[k]) / 0.5      # 0..1
                me = _grid_mean(self.relief_frames[k])           # 0..1
                self.mean_relief.append(me)
                self.power.append(
                    bridge.tablet_power(mb, me, TABLET_AREA_CM2))

    def html_float(self, budget: float = DEFAULT_BUDGET_W) -> str:
        self._float_data()
        return html_floatup(self.frames_by_name, self.light_frames,
                            self.relief_frames, self.n, self.catalog,
                            self.jones_poly, self.power, self.mean_relief,
                            budget, BATTERY_WH)

    def save_floatup(self, path: str, budget: float = DEFAULT_BUDGET_W) -> str:
        with open(path, "w") as f:
            f.write(self.html_float(budget))
        return path


class HoloKeyboardApp:
    """The Happy Hacking Keyboard floating as a hologram (layout from Bada)."""

    KBD_AREA_CM2 = 120.0   # ~60% keyboard footprint

    def boot(self) -> dict:
        self.keys = bridge.hhkb_keys()
        self.width = bridge.hhkb_width()
        self.rows = bridge.hhkb_rows()
        self.jones = bridge.jones_polynomial()
        # power to light the floating keycaps out of the conductive plastic
        self.power = bridge.tablet_power(0.5, 0.5, self.KBD_AREA_CM2)
        return {"keys": len(self.keys), "width": self.width,
                "rows": self.rows, "power": self.power}

    def _poly_str(self) -> str:
        parts = []
        for e, c in self.jones:
            parts.append(f"{'+' if c >= 0 else '-'} {abs(c)}t^{e}")
        s = " ".join(parts)
        return s[2:] if s.startswith("+ ") else s

    def html(self) -> str:
        return html_keyboard(self.keys, self.width, self.rows,
                             self.power, self._poly_str())

    def save_html(self, path: str) -> str:
        with open(path, "w") as f:
            f.write(self.html())
        return path


class MirrorApp:
    """The smartphone mirror over the tablet: an eyeglass-lens aerial image
    forms in the gap (focal point from the special-relativity Jones polynomial),
    realizing the holographic display and the HHKB keyboard."""

    def __init__(self, n: int = 14, frames: int = 16, display: str = "fermat",
                 nv: int = 10):
        self.n = n
        self.frames = frames
        self.display = display
        self.nv = nv

    def boot(self) -> dict:
        from eqvideo import bridge as ev
        from eqvideo.render import CATALOG as EV_CAT
        from transport import bridge as tr
        from transport.app import CATALOG as TR_CAT

        # source video for the realized display (computed in Bada)
        if self.display in ev.names():
            self.display_frames = ev.frames(self.display, self.n, self.frames)
        else:
            self.display_frames = tr.frames(self.display, self.n, self.frames)
        self.light_frames = bridge.light_frames("mag", self.n, self.frames)

        # the HHKB keyboard layout (computed in Bada)
        self.keys = bridge.hhkb_keys()
        self.kbd_width = bridge.hhkb_width()

        # the eyeglass-lens focal height across velocity (rows) and phase (cols)
        self.focus_table = [
            bridge.focus_frames(GAP_CM, (i / self.nv) * VMAX, 1.0, self.frames)
            for i in range(self.nv + 1)]
        self.jones_poly = bridge.jones_polynomial()

        z_rest = self.focus_table[0][0]
        z_fast = self.focus_table[-1][0]
        return {"gap_cm": GAP_CM, "display": self.display,
                "focus_rest_cm": round(z_rest, 2),
                "focus_fast_cm": round(z_fast, 2),
                "vmax": VMAX, "keys": len(self.keys)}

    def html(self, keyboard: bool = False) -> str:
        return html_mirror(self.display, self.display_frames,
                           self.light_frames, self.n, self.keys,
                           self.kbd_width, self.focus_table, GAP_CM, VMAX,
                           self.jones_poly, keyboard)

    def save_html(self, path: str, keyboard: bool = False) -> str:
        with open(path, "w") as f:
            f.write(self.html(keyboard))
        return path


class VisionApp:
    """Vision-Pro-equivalent: launch the display and the tablet turns
    transparent (passthrough) while its apps float out as spatial windows,
    anchored at the mirror-state lens focus (all geometry computed in Bada)."""

    # the tablet's applications that float out as spatial windows
    APPS = [
        {"title": "Hologram", "kind": "display", "glyph": "🔮"},
        {"title": "Terminal", "kind": "card", "glyph": "▶_"},
        {"title": "Slideshow", "kind": "card", "glyph": "▦"},
        {"title": "Kaleido", "kind": "card", "glyph": "✲"},
        {"title": "Files", "kind": "card", "glyph": "🗀"},
    ]
    RADIUS = 10.0
    SPREAD = 2.0944          # ±60° concave shell
    DISPLAY = "fermat"

    def __init__(self, n: int = 14, frames: int = 16):
        self.n = n
        self.frames = frames

    def boot(self) -> dict:
        from eqvideo import bridge as ev

        self.display_frames = ev.frames(self.DISPLAY, self.n, self.frames)
        self.light_frames = bridge.light_frames("mag", self.n, self.frames)
        self.keys = bridge.hhkb_keys()
        self.kbd_width = bridge.hhkb_width()

        # spatial window layout + tablet passthrough + focal anchor (all Bada)
        self.positions = bridge.window_positions(len(self.APPS),
                                                 self.RADIUS, self.SPREAD)
        self.focus_cm = bridge.focus_z(GAP_CM, 0.3, 1.0, 0.0)
        self.passthrough = bridge.passthrough_alpha(1.0)
        return {"windows": len(self.APPS), "focus_cm": round(self.focus_cm, 2),
                "passthrough_alpha": round(self.passthrough, 2),
                "gap_cm": GAP_CM, "keys": len(self.keys)}

    def html(self) -> str:
        return html_vision(self.APPS, self.positions, self.display_frames,
                          self.light_frames, self.n, self.keys, self.kbd_width,
                          self.focus_cm, GAP_CM)

    def save_html(self, path: str) -> str:
        with open(path, "w") as f:
            f.write(self.html())
        return path


class GlassApp:
    """Fully transparent holographic display + Japanese HHKB over a camera
    passthrough: no video, everything see-through to the world behind the
    tablet.  Romaji->kana from the Bada conversion table."""

    def boot(self) -> dict:
        self.keys = bridge.hhkb_keys()
        self.kbd_width = bridge.hhkb_width()
        self.kana = bridge.kana_table()
        return {"keys": len(self.keys), "kana_entries": len(self.kana),
                "input": "romaji->kana (hiragana/katakana)",
                "background": "camera passthrough (see-through)"}

    def html(self) -> str:
        return html_glass(self.keys, self.kbd_width, self.kana)

    def save_html(self, path: str) -> str:
        with open(path, "w") as f:
            f.write(self.html())
        return path


class FreeformApp:
    """A Samsung-Freeform-style multi-window desktop: the tablet's apps open in
    draggable/resizable freeform windows with close/minimize/maximize buttons
    and a Play-Store-style taskbar (Start button + tasks + clock).  The window
    geometry and app catalog come from Bada (apps/hologram/lib/freeform.bada)."""

    def boot(self) -> dict:
        self.catalog = bridge.wm_catalog()
        self.tb = bridge.tb_height()
        return {"apps": len(self.catalog), "taskbar_h": self.tb,
                "features": "freeform windows · close/min/max · split-snap · "
                            "Start button · taskbar"}

    def html(self) -> str:
        return html_freeform(self.catalog, self.tb)

    def save_html(self, path: str) -> str:
        with open(path, "w") as f:
            f.write(self.html())
        return path
