"""Hologram Display: project the equation-group videos onto a four-mirror
reflection pyramid, modulated by the Bada beta(p,q) light field."""

import math
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

from hologram import HologramApp, html_hologram
from hologram import bridge


class TestHologramBada(unittest.TestCase):
    """The light field + geometry come out of the Bada library."""

    def test_quads(self):
        self.assertEqual(bridge.quad_names(),
                         ["before", "after", "left", "right"])
        self.assertEqual(bridge.quad_rot("before"), 0)
        self.assertEqual(bridge.quad_rot("after"), 180)
        self.assertEqual(bridge.quad_rot("right"), 90)
        self.assertEqual(bridge.quad_rot("left"), 270)

    def test_light_field_grid(self):
        g = bridge.light_grid("mag", 6, 0.0)
        self.assertEqual(len(g), 6)
        self.assertEqual(len(g[0]), 6)
        # magnitude is a non-negative amplitude bounded by the light_pos peak
        flat = [v for row in g for v in row]
        self.assertTrue(all(0.0 <= v <= 0.51 for v in flat))
        self.assertTrue(max(flat) > 0.1)

    def test_complex_amplitude_consistent(self):
        # |A| == hypot(re, im) at a sample point, both from Bada
        re = bridge.light_grid("re", 5, 0.3)[2][3]
        im = bridge.light_grid("im", 5, 0.3)[2][3]
        mag = bridge.light_grid("mag", 5, 0.3)[2][3]
        self.assertAlmostEqual(mag, math.hypot(re, im), places=6)

    def test_metric_and_mass(self):
        # v/sqrt(1+(v/c)^2) and 8 pi G (p/c^3 + V/S)
        self.assertAlmostEqual(bridge.metric_ds2(3.0, 5.0),
                               3.0 / math.sqrt(1 + (3.0 / 5.0) ** 2), places=6)
        self.assertGreater(bridge.hologram_mass(1.0, 3e8, 1.0, 1.0), 0.0)


class TestHologramApp(unittest.TestCase):
    def test_boot_projects_sources(self):
        app = HologramApp(n=8, frames=4, names=["fermat", "critline"])
        r = app.boot()
        self.assertEqual(r["n_sources"], 2)
        self.assertEqual(r["mirrors"], ["before", "after", "left", "right"])
        self.assertEqual(len(app.light_frames), 4)

    def test_html_pyramid_and_free(self):
        app = HologramApp(n=8, frames=4, names=["fermat", "abelian"])
        app.boot()
        with tempfile.TemporaryDirectory() as d:
            pyr = open(app.save_html(os.path.join(d, "p.html"), False)).read()
            free = open(app.save_html(os.path.join(d, "f.html"), True)).read()
        self.assertIn("FREE=false", pyr)
        self.assertIn("FREE=true", free)
        for h in (pyr, free):
            self.assertIn("HOLOGRAM DISPLAY", h)
            self.assertIn("putImageData", h)         # surface * light render
            for mirror in ("before", "after", "left", "right"):
                self.assertIn(mirror, h)
            self.assertIn("Fermat", h)               # an equation-group title

    def test_render_direct(self):
        frames = {"x": [[[0.0, 1.0], [1.0, 0.0]]]}
        light = [[[0.4, 0.4], [0.4, 0.4]]]
        cat = {"x": ("Holo X", "desc")}
        quads = [{"name": "before", "rot": 0}, {"name": "after", "rot": 180},
                 {"name": "left", "rot": 270}, {"name": "right", "rot": 90}]
        html = html_hologram(frames, light, 2, cat, quads, free=True)
        self.assertIn("Holo X", html)
        self.assertIn("FREE=true", html)


if __name__ == "__main__":
    unittest.main()
