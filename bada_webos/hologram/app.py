"""HologramApp — project the equation-group videos onto a Hologram Display.

Reuses the equation-group surfaces (eqvideo / transport / slideshow, all
computed in Bada) as the source video, and the hologram light field
(apps/hologram/lib/hologram.bada) as the reflective modulation, then composes
the four-mirror reflection pyramid from the "Hologram Display" report.
"""

from __future__ import annotations

from . import bridge
from .render import html_hologram


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
