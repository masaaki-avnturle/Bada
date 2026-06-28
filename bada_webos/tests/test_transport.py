"""'Integrate of theorem' (system_transport report): binomial equation
generator + manifold video dictionary, in Bada (cross-checked vs Python)."""

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

from transport import bridge, TransportApp, CATALOG
from bada import run_program

ZETA3 = sum(1.0 / k ** 3 for k in range(1, 1501))


class TestBinomialGenerator(unittest.TestCase):
    def test_binom(self):
        self.assertEqual(bridge.binom(4, 2), 6)
        self.assertEqual(bridge.binom(5, 0), 1)

    def test_series_is_one_plus_f_to_n(self):
        # a_k = C(n,r)  =>  sum a_k f^r = (1+f)^n
        self.assertAlmostEqual(bridge.series_binom(4, 0.5), 1.5 ** 4, places=9)
        self.assertAlmostEqual(bridge.series_binom(6, 0.3), 1.3 ** 6, places=9)

    def test_alternating_is_one_minus_f_to_n(self):
        # chi = (-1)^k a_k  =>  sum (-1)^r C(n,r) f^r = (1-f)^n
        self.assertAlmostEqual(bridge.series_alt(4, 0.5), 0.5 ** 4, places=9)

    def test_flow_in_makes_series_equal_zeta(self):
        # (1+f)^2 = zeta(3)  =>  f = sqrt(zeta(3)) - 1
        f, err = bridge.flow_in(3, 2, 1500, 0.0, 1.0, 1000)
        self.assertAlmostEqual(f, math.sqrt(ZETA3) - 1, delta=0.01)
        self.assertLess(err, 0.01)

    def test_P_factor(self):
        # zeta(3) = P^4 * (1.5)^2  =>  P = (zeta(3)/(1.5)^2)^(1/4)
        P = bridge.generate_P(3, 2, 0.5, 1500)
        self.assertAlmostEqual(P, (ZETA3 / 1.5 ** 2) ** 0.25, places=4)

    def test_amgm(self):
        self.assertAlmostEqual(bridge.amgm_gap(1, 4), 0.5, places=9)
        self.assertGreaterEqual(bridge.amgm_gap(3, 7), 0)


class TestManifoldDictionary(unittest.TestCase):
    def test_entries(self):
        self.assertEqual(set(bridge.names()),
                         {"seifert", "kaluza", "critline", "amgm", "binom"})

    def test_all_displace(self):
        for nm in bridge.names():
            self.assertGreater(bridge.displacement(nm, 16), 0.0)

    def test_frame_shape(self):
        fr = bridge.frames("kaluza", n=10, T=6)
        self.assertEqual(len(fr), 6)
        self.assertEqual(len(fr[0]), 10)


class TestApp(unittest.TestCase):
    def test_boot_and_html(self):
        app = TransportApp(n=10, frames=8)
        r = app.boot()
        self.assertEqual(len(r["entries"]), 5)
        self.assertAlmostEqual(r["binom_series_2_half"], 1.5 ** 2, places=6)
        with tempfile.TemporaryDirectory() as d:
            html = open(app.save_html(os.path.join(d, "t.html"))).read()
        self.assertIn("Seifert", html)
        self.assertIn("canvas", html)

    def test_catalog(self):
        self.assertEqual(set(CATALOG), set(bridge.names()))

    def test_bada_app_records(self):
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            vm = run_program(os.path.join(_PKG, "apps", "transport",
                                          "transport_app.bada"))
        self.assertIn("transport", vm.tuplespace)


if __name__ == "__main__":
    unittest.main()
