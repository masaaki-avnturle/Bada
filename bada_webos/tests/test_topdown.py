"""Each equation group's domain as a flat 2D top-down video (kaleido-based)."""

import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_PKG)
for p in (_PKG, _ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from topdown import TopDownApp, html_topdown


class TestTopDown(unittest.TestCase):
    def test_boot_gathers_domains(self):
        app = TopDownApp(n=8, frames=4,
                         names=["fermat", "critline", "caustic"])
        r = app.boot()
        self.assertEqual(r["n_domains"], 3)
        self.assertIn("caustic", r["domains"])

    def test_html_plain_and_fold(self):
        app = TopDownApp(n=8, frames=4, names=["fermat", "abelian"])
        app.boot()
        with tempfile.TemporaryDirectory() as d:
            plain = open(app.save_html(os.path.join(d, "p.html"), False)).read()
            fold = open(app.save_html(os.path.join(d, "f.html"), True)).read()
        self.assertIn("FOLD=false", plain)
        self.assertIn("FOLD=true", fold)
        # 2D top-down render (per-pixel heatmap) + kaleidoscope-fold toggle
        for h in (plain, fold):
            self.assertIn("putImageData", h)
            self.assertIn("kaleidoscope fold", h)
            self.assertIn("top-down", h)
            self.assertIn("Fermat", h)

    def test_render_direct(self):
        frames = {"x": [[[0.0, 1.0], [1.0, 0.0]]]}
        cat = {"x": ("Dom X", "desc")}
        html = html_topdown(frames, 2, cat, fold=True)
        self.assertIn("Dom X", html)
        self.assertIn("FOLD=true", html)


if __name__ == "__main__":
    unittest.main()
