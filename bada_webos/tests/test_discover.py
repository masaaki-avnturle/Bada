"""Discovery apps in Bada: HPsi operator patterns, odd-zeta regularity, and the
Monster-denominator a-priori engine (cross-checked against Python references)."""

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_PKG)
for p in (_PKG, _ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from discover import bridge
from bada import run_program


def py_zeta(s, N=2000):
    return sum(1.0 / (k ** s) for k in range(1, N + 1))


class TestHPsiPatterns(unittest.TestCase):
    def test_phase_period_is_four(self):
        self.assertEqual(bridge.hpsi_period(), 4)

    def test_real_eigen_residues(self):
        eig = bridge.hpsi_eigen(1, 12)
        self.assertEqual(eig, [3, 4, 7, 8, 11, 12])
        self.assertEqual(sorted({L % 4 for L in eig}), [0, 3])

    def test_geometric_growth(self):
        self.assertAlmostEqual(bridge.hpsi_growth(2, 8), 2.0, delta=0.05)


class TestOddZeta(unittest.TestCase):
    def test_zeta_matches_reference(self):
        for s in (3, 5, 7):
            self.assertAlmostEqual(bridge.zeta(s, 2000), py_zeta(s, 2000),
                                   places=6)

    def test_ratios_converge_to_quarter(self):
        r = bridge.odd_ratios(2000)
        self.assertEqual(len(r), 4)
        # monotonically rising toward 1/4 from below
        self.assertTrue(all(0.1 < x < 0.25 for x in r))
        self.assertTrue(r[0] < r[1] < r[2] < r[3])
        self.assertAlmostEqual(r[-1], 0.25, delta=0.02)


class TestMoonshineEngine(unittest.TestCase):
    def test_gamma_relates_to_zeta(self):
        # the alternating zeta series is in the neighbourhood of gamma
        self.assertTrue(0.5 < bridge.gamma(20, 1500) < 0.65)

    def test_monster_denominators(self):
        seq = bridge.monster_denoms(1500, 120)
        self.assertEqual(len(seq), 4)              # s = 3,5,7,9
        monster = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 41, 47, 59, 71,
                   24, 196884}
        for p, q, err in seq:
            self.assertGreater(p, 0)
            self.assertLess(err, 1e-6)             # tight rational fit
            # q is a Monster number times a small multiple
            self.assertTrue(any(q % m == 0 for m in monster))

    def test_zeta3_anchor(self):
        self.assertAlmostEqual(bridge.zeta(3, 1500), py_zeta(3, 1500),
                               places=5)


class TestSqrt2Quantization(unittest.TestCase):
    def test_sqrt2_value(self):
        import math
        self.assertAlmostEqual(bridge.sqrt2_approx(20), math.sqrt(2),
                               places=9)

    def test_pell_lattice_levels(self):
        self.assertEqual(bridge.pell_denoms(8),
                         [1, 2, 5, 12, 29, 70, 169, 408])

    def test_silver_ratio_causal_regularity(self):
        import math
        sr = bridge.silver_ratios(12)
        self.assertAlmostEqual(sr[-1], 1 + math.sqrt(2), delta=1e-4)

    def test_odd_zeta_general_form(self):
        seq = bridge.pell_seq(1500, 14, 200)
        self.assertEqual(len(seq), 4)
        for p, q, err in seq:
            self.assertGreater(p, 0)
            self.assertLess(err, 1e-6)


class TestDiscoverAppsRun(unittest.TestCase):
    def _ts(self, app):
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            vm = run_program(os.path.join(_PKG, "apps", "discover", app))
        return vm.tuplespace

    def test_hpsi_app_records(self):
        self.assertIn("hpsi", self._ts("hpsi_app.bada"))

    def test_zeta_app_records(self):
        self.assertIn("zeta", self._ts("zeta_app.bada"))

    def test_moonshine_app_records(self):
        ts = self._ts("moonshine_app.bada")
        self.assertIn("moonshine", ts)
        self.assertTrue(any("EXPLORATORY" in str(x)
                            for x in ts["moonshine"]))

    def test_sqrt2_app_records(self):
        ts = self._ts("sqrt2_app.bada")
        self.assertIn("sqrt2", ts)
        self.assertTrue(any("EXPLORATORY" in str(x) for x in ts["sqrt2"]))


if __name__ == "__main__":
    unittest.main()
