"""TransportApp — 'Integrate of theorem' equation generator + manifold video
dictionary (the report's Seifert / Kaluza-Klein / critical-line / AM-GM /
binomial surfaces), computed in Bada and rendered with the eqvideo renderer.
"""

from __future__ import annotations

from . import bridge
from eqvideo.render import ascii_animation, html_video

# this report's dictionary: name -> (title, description)
CATALOG = {
    "seifert": ("Seifert manifold",
                "Seifert fibered space — rotating concentric fibres"),
    "kaluza": ("Kaluza-Klein 5th dimension",
               "two compactified circle modes of the 5D tower"),
    "critline": ("zeta critical line Re=1/2",
                 "|Σ n^{-(1/2+is)}| — Riemann zeros appear as valleys"),
    "amgm": ("AM-GM inequality manifold",
             "(a+b)/2 − √(ab) ≥ 0, the valley along a=b"),
    "binom": ("binomial equation surface",
              "Σ C(n,r) gʳ = (1+g)ⁿ — the report's a_k = ΣₙCᵣ"),
}


class TransportApp:
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
            # the binomial generator for zeta(3): a_k = C(2,r), P^4 factor
            "binom_series_2_half": bridge.series_binom(2, 0.5),
            "flow_in_zeta3": bridge.flow_in(3, 2),
            "P_zeta3": bridge.generate_P(3, 2, 0.5),
        }
        return self.report

    def html(self) -> str:
        return html_video(self.frames_by_name, self.n, CATALOG)

    def save_html(self, path: str) -> str:
        with open(path, "w") as f:
            f.write(self.html())
        return path

    def ascii(self, name: str) -> list:
        return ascii_animation(self.frames_by_name[name])

    @staticmethod
    def catalog() -> dict:
        return CATALOG
