"""SuperposeApp — overlay all the manifold animations into one combined video.

Each of the 10 surfaces (eqvideo + transport, computed in Bada) is normalised to
a common scale, then summed/averaged frame-by-frame into one field. The result
shows what *all the videos superimposed* looks like — a shifting interference
landscape — rendered as a 3D animation and as a top-down kaleidoscope.
"""

from __future__ import annotations

CATALOG = {
    "superpose": ("Superposition of all videos",
                  "the sum/average of all 10 manifold surfaces — the combined "
                  "equation-group interference field"),
}


def _normalize(frames: list) -> list:
    """Map a surface's frames to [-1, 1] using its global min/max."""
    lo = min(v for g in frames for row in g for v in row)
    hi = max(v for g in frames for row in g for v in row)
    span = (hi - lo) or 1.0
    return [[[(v - lo) / span * 2 - 1 for v in row] for row in g]
            for g in frames]


class SuperposeApp:
    def __init__(self, n: int = 14, frames: int = 16, names: list = None,
                 average: bool = True):
        self.n = n
        self.frames = frames
        self.names = names
        self.average = average

    def boot(self) -> dict:
        from eqvideo import bridge as ev
        from transport import bridge as tr

        ev_names = ev.names()
        tr_names = tr.names()
        use = self.names or (ev_names + tr_names)

        norm = []
        for nm in use:
            b = ev if nm in ev_names else tr
            norm.append(_normalize(b.frames(nm, self.n, self.frames)))

        n, T, count = self.n, self.frames, len(norm)
        combined = []
        for k in range(T):
            grid = [[0.0] * n for _ in range(n)]
            for nf in norm:
                g = nf[k]
                for i in range(n):
                    gi, ggi = grid[i], g[i]
                    for j in range(n):
                        gi[j] += ggi[j]
            if self.average:
                grid = [[grid[i][j] / count for j in range(n)]
                        for i in range(n)]
            combined.append(grid)

        self.combined = combined
        # how much the combined centre field moves over the animation
        cz = [combined[k][n // 2][n // 2] for k in range(T)]
        self.report = {
            "sources": use,
            "n_sources": count,
            "n": n,
            "n_frames": T,
            "displacement": round(sum(abs(cz[k] - cz[k - 1])
                                      for k in range(1, T)), 4),
        }
        return self.report

    def frames_by_name(self) -> dict:
        return {"superpose": self.combined}

    def html_3d(self) -> str:
        from eqvideo.render import html_video
        return html_video(self.frames_by_name(), self.n, CATALOG)

    def html_kaleido(self, segments: int = 8) -> str:
        from kaleido.render import html_kaleido
        return html_kaleido(self.frames_by_name(), self.n, CATALOG, segments)

    def save_3d(self, path: str) -> str:
        with open(path, "w") as f:
            f.write(self.html_3d())
        return path

    def save_kaleido(self, path: str, segments: int = 8) -> str:
        with open(path, "w") as f:
            f.write(self.html_kaleido(segments))
        return path
