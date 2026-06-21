"""Equation-group 3D animation video dictionary (manifolds in Bada)."""

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

from eqvideo import bridge, EqVideoApp, CATALOG
from bada import run_program


class TestManifoldBridge(unittest.TestCase):
    def test_dictionary_entries(self):
        self.assertEqual(set(bridge.names()),
                         {"eqgen", "fermat", "covariant", "trigbeta",
                          "abelian"})

    def test_frame_shape(self):
        fr = bridge.frames("fermat", n=10, T=6)
        self.assertEqual(len(fr), 6)
        self.assertEqual(len(fr[0]), 10)
        self.assertEqual(len(fr[0][0]), 10)

    def test_surface_displaces(self):
        # every manifold moves over the animation (non-zero displacement)
        for nm in bridge.names():
            self.assertGreater(bridge.displacement(nm, 16), 0.0,
                               f"{nm} does not displace")

    def test_fermat_known_value(self):
        # z(0.5,0.5; t=0) with n=2 is 1 - 0.25 - 0.25 = 0.5; grid centre-ish
        fr = bridge.frames("fermat", n=3, T=1)[0]
        self.assertAlmostEqual(fr[1][1], 1.0, places=6)   # centre (0,0) -> 1


class TestApp(unittest.TestCase):
    def test_boot_and_html(self):
        app = EqVideoApp(n=10, frames=8)
        r = app.boot()
        self.assertEqual(len(r["entries"]), 5)
        self.assertTrue(all(v > 0 for v in r["displacement"].values()))
        with tempfile.TemporaryDirectory() as d:
            html = open(app.save_html(os.path.join(d, "v.html"))).read()
        self.assertIn("video dictionary", html)
        self.assertIn("Fermat", html)
        self.assertIn("canvas", html)

    def test_ascii_animation(self):
        app = EqVideoApp(n=8, frames=6)
        app.boot()
        frames = app.ascii("abelian")
        self.assertEqual(len(frames), 6)
        # the animation is not static (the surface displaces over frames)
        self.assertGreater(len(set(frames)), 1)

    def test_catalog_has_all(self):
        self.assertEqual(set(CATALOG), set(bridge.names()))


class TestAppRecords(unittest.TestCase):
    def test_bada_app_records(self):
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            vm = run_program(os.path.join(_PKG, "apps", "eqvideo",
                                          "eqvideo_app.bada"))
        self.assertIn("eqvideo", vm.tuplespace)


if __name__ == "__main__":
    unittest.main()
