"""Superposition of all the manifold animations into one combined video."""

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

from superpose import SuperposeApp
from superpose.app import _normalize


class TestNormalize(unittest.TestCase):
    def test_maps_to_unit_range(self):
        frames = [[[0.0, 10.0], [5.0, -10.0]]]
        nf = _normalize(frames)
        flat = [v for row in nf[0] for v in row]
        self.assertAlmostEqual(min(flat), -1.0, places=9)
        self.assertAlmostEqual(max(flat), 1.0, places=9)


class TestSuperpose(unittest.TestCase):
    def test_boot_combines_sources(self):
        app = SuperposeApp(n=8, frames=6,
                           names=["fermat", "abelian", "seifert"])
        r = app.boot()
        self.assertEqual(r["n_sources"], 3)
        self.assertEqual(len(app.combined), 6)
        self.assertEqual(len(app.combined[0]), 8)
        # averaged normalised field stays within [-1, 1]
        for g in app.combined:
            for row in g:
                for v in row:
                    self.assertLessEqual(abs(v), 1.0 + 1e-9)

    def test_combined_is_the_average(self):
        # with one source, the combined field equals that source normalised
        app = SuperposeApp(n=6, frames=4, names=["fermat"])
        app.boot()
        from eqvideo import bridge as ev
        nf = _normalize(ev.frames("fermat", 6, 4))
        self.assertAlmostEqual(app.combined[2][3][3], nf[2][3][3], places=9)

    def test_html_outputs(self):
        app = SuperposeApp(n=8, frames=4, names=["fermat", "critline"])
        app.boot()
        with tempfile.TemporaryDirectory() as d:
            h3d = open(app.save_3d(os.path.join(d, "s.html"))).read()
            hk = open(app.save_kaleido(os.path.join(d, "k.html"), 6)).read()
        self.assertIn("Superposition of all videos", h3d)
        self.assertIn("canvas", h3d)
        self.assertIn("putImageData", hk)         # kaleidoscope render
        self.assertIn("Superposition", hk)

    def test_displacement_nonzero(self):
        app = SuperposeApp(n=8, frames=8,
                           names=["covariant", "kaluza", "abelian"])
        r = app.boot()
        self.assertGreater(r["displacement"], 0.0)


if __name__ == "__main__":
    unittest.main()
