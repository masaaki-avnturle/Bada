"""EqVideo — the equation-group 3D animation dictionary application.

Computes the manifold animation frames (in Bada) and renders them as a
browsable animated-HTML video dictionary.
"""

from __future__ import annotations

from . import bridge
from .render import CATALOG, ascii_animation, html_video


class EqVideoApp:
    def __init__(self, n: int = 16, frames: int = 20):
        self.n = n
        self.frames = frames

    def boot(self) -> dict:
        names = bridge.names()
        self.frames_by_name = {nm: bridge.frames(nm, self.n, self.frames)
                               for nm in names}
        self.report = {
            "entries": names,
            "displacement": {nm: round(bridge.displacement(nm, self.frames), 4)
                             for nm in names},
            "n": self.n,
            "n_frames": self.frames,
        }
        return self.report

    def html(self) -> str:
        return html_video(self.frames_by_name, self.n)

    def save_html(self, path: str) -> str:
        with open(path, "w") as f:
            f.write(self.html())
        return path

    def ascii(self, name: str) -> list:
        return ascii_animation(self.frames_by_name[name])

    @staticmethod
    def catalog() -> dict:
        return CATALOG
