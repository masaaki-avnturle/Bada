"""TopDownApp — each equation group's domain as a flat 2D top-down video,
with an optional kaleidoscope fold (based on the 3D kaleidoscope)."""

from __future__ import annotations

from .render import html_topdown


class TopDownApp:
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
        self.report = {"domains": use, "n_domains": len(use)}
        return self.report

    def html(self, fold: bool = False) -> str:
        return html_topdown(self.frames_by_name, self.n, self.catalog, fold)

    def save_html(self, path: str, fold: bool = False) -> str:
        with open(path, "w") as f:
            f.write(self.html(fold))
        return path
