"""KaleidoApp — a top-down kaleidoscope of the equation-group manifold
animations (the eqvideo + transport surfaces, computed in Bada)."""

from __future__ import annotations

from .render import html_kaleido


class KaleidoApp:
    def __init__(self, n: int = 14, frames: int = 16, names: list = None):
        self.n = n
        self.frames = frames
        self.names = names

    def boot(self) -> dict:
        from eqvideo import bridge as ev
        from transport import bridge as tr
        from eqvideo.render import CATALOG as EV_CAT
        from transport.app import CATALOG as TR_CAT

        ev_names = ev.names()
        tr_names = tr.names()
        all_names = ev_names + tr_names
        catalog = {**EV_CAT, **TR_CAT}
        use = self.names or all_names

        fb = {}
        for nm in use:
            b = ev if nm in ev_names else tr
            fb[nm] = b.frames(nm, self.n, self.frames)
        self.frames_by_name = fb
        self.catalog = {nm: catalog[nm] for nm in use}
        self.report = {"entries": use, "n": self.n, "n_frames": self.frames}
        return self.report

    def html(self, segments: int = 8) -> str:
        return html_kaleido(self.frames_by_name, self.n, self.catalog,
                            segments)

    def save_html(self, path: str, segments: int = 8) -> str:
        with open(path, "w") as f:
            f.write(self.html(segments))
        return path
