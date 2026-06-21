"""Top-down kaleidoscope of the equation-group manifold animations."""

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

from kaleido import KaleidoApp, html_kaleido


class TestKaleido(unittest.TestCase):
    def test_boot_subset(self):
        app = KaleidoApp(n=8, frames=4, names=["fermat", "seifert"])
        r = app.boot()
        self.assertEqual(r["entries"], ["fermat", "seifert"])
        self.assertEqual(len(app.frames_by_name["fermat"]), 4)

    def test_html_is_a_kaleidoscope(self):
        app = KaleidoApp(n=8, frames=4, names=["fermat", "critline"])
        app.boot()
        with tempfile.TemporaryDirectory() as d:
            html = open(app.save_html(os.path.join(d, "k.html"), 6)).read()
        # kaleidoscope rendering bits
        self.assertIn("putImageData", html)         # per-pixel top-down render
        self.assertIn("kaleidoscope", html)
        self.assertIn("segments", html)
        self.assertIn("canvas", html)
        # both selected sources present
        self.assertIn("Fermat", html)
        self.assertIn("critical line", html)

    def test_combines_eqvideo_and_transport(self):
        # a default boot pulls from both dictionaries
        app = KaleidoApp(n=6, frames=3,
                         names=["abelian", "kaluza"])   # one from each
        r = app.boot()
        self.assertIn("abelian", r["entries"])          # eqvideo
        self.assertIn("kaluza", r["entries"])           # transport

    def test_render_function_direct(self):
        frames = {"x": [[[0.0, 1.0], [1.0, 0.0]]]}
        cat = {"x": ("Title X", "desc")}
        html = html_kaleido(frames, 2, cat, segments=8)
        self.assertIn("Title X", html)
        self.assertIn("SEG=8", html)


if __name__ == "__main__":
    unittest.main()
