"""SlideshowApp — all the equation-group graphs as one PowerPoint-style
slideshow video, with flash transitions between each equation group.
"""

from __future__ import annotations

from .render import html_slideshow

# extra report surfaces (caostics, zeta_dalanversian)
REPORT_CATALOG = {
    "caustic": ("Cusp catastrophe (caustics)",
                "V(x)=x⁴−a·x², control a sweeps the caustic / catastrophe fold"),
    "dalembert": ("d'Alembertian wave  □ψ=0",
                  "standing wave = left- + right-travelling solutions"),
}


class SlideshowApp:
    def __init__(self, n: int = 16, frames: int = 16, names: list = None):
        self.n = n
        self.frames = frames
        self.names = names

    def boot(self) -> dict:
        from eqvideo import bridge as ev
        from transport import bridge as tr
        from . import bridge as rp
        from eqvideo.render import CATALOG as EV_CAT
        from transport.app import CATALOG as TR_CAT

        ev_names, tr_names, rp_names = ev.names(), tr.names(), rp.names()
        catalog = {**EV_CAT, **TR_CAT, **REPORT_CATALOG}
        order = ev_names + tr_names + rp_names
        use = self.names or order

        fb = {}
        for nm in use:
            b = (ev if nm in ev_names else tr if nm in tr_names else rp)
            fb[nm] = b.frames(nm, self.n, self.frames)
        self.frames_by_name = fb
        self.catalog = {nm: catalog[nm] for nm in use}
        self.report = {"slides": use, "n_slides": len(use),
                       "effects": ["flash", "fade", "wipe", "zoom", "spin",
                                   "blinds"]}
        return self.report

    def html(self) -> str:
        return html_slideshow(self.frames_by_name, self.n, self.catalog)

    def save_html(self, path: str) -> str:
        with open(path, "w") as f:
            f.write(self.html())
        return path
