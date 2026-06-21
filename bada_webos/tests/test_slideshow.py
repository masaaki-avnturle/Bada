"""All equation-group graphs as a PowerPoint-style flash-transition slideshow."""

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

from slideshow import bridge, SlideshowApp, html_slideshow


class TestReportSurfaces(unittest.TestCase):
    def test_new_entries(self):
        self.assertEqual(set(bridge.names()), {"caustic", "dalembert"})

    def test_frame_shape(self):
        fr = bridge.frames("caustic", n=8, T=5)
        self.assertEqual(len(fr), 5)
        self.assertEqual(len(fr[0]), 8)


class TestSlideshow(unittest.TestCase):
    def test_boot_gathers_all_equation_groups(self):
        app = SlideshowApp(n=8, frames=4,
                           names=["fermat", "critline", "caustic",
                                  "dalembert"])
        r = app.boot()
        self.assertEqual(r["n_slides"], 4)
        self.assertIn("caustic", r["slides"])
        self.assertIn("dalembert", r["slides"])
        self.assertIn("flash", r["effects"])

    def test_html_has_flash_transitions(self):
        app = SlideshowApp(n=8, frames=4, names=["fermat", "caustic"])
        app.boot()
        with tempfile.TemporaryDirectory() as d:
            html = open(app.save_html(os.path.join(d, "s.html"))).read()
        # PowerPoint-style transition effects + event handling
        for fx in ("flash", "fade", "wipe", "zoom", "spin", "blinds"):
            self.assertIn(fx, html)
        self.assertIn("keydown", html)         # arrow/space events
        self.assertIn("canvas", html)
        self.assertIn("@keyframes flash", html)
        self.assertIn("Cusp catastrophe", html)

    def test_render_direct(self):
        frames = {"x": [[[0.0, 1.0], [1.0, 0.0]]]}
        cat = {"x": ("Eq X", "desc x")}
        html = html_slideshow(frames, 2, cat)
        self.assertIn("Eq X", html)
        self.assertIn("EFFECTS", html)


if __name__ == "__main__":
    unittest.main()
