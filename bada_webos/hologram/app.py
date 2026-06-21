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

TABLET_AREA_CM2 = 200.0   # ~10" tablet panel
BATTERY_WH = 40.0         # tablet battery
DEFAULT_BUDGET_W = 5.0    # power budget for the float-up display


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
