"""Beta-function algorithms in Bada: B(2,2), difference-equation factorization,
and the zeta relations (cross-checked against Python)."""

import math
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_PKG)
for p in (_PKG, _ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from betafn import bridge
from bada import run_program


def py_beta(p, q):
    return math.factorial(p - 1) * math.factorial(q - 1) / math.factorial(
        p + q - 1)


class TestBeta(unittest.TestCase):
    def test_beta_2_2_is_one_sixth(self):
        self.assertAlmostEqual(bridge.beta(2, 2), 1 / 6, places=12)

    def test_beta_matches_reference(self):
        for p in range(2, 5):
            for q in range(2, 5):
                self.assertAlmostEqual(bridge.beta(p, q), py_beta(p, q),
                                       places=10)

    def test_symmetry(self):
        self.assertAlmostEqual(bridge.beta(2, 3), bridge.beta(3, 2), places=12)


class TestDifferenceFactorization(unittest.TestCase):
    def test_pascal_recurrence_holds(self):
        for p in range(2, 5):
            for q in range(2, 5):
                self.assertTrue(bridge.pascal_holds(p, q))


class TestZetaRelations(unittest.TestCase):
    def test_zeta2_exact_link(self):
        # zeta(2) = pi^2 * B(2,2) = pi^2/6
        self.assertAlmostEqual(bridge.zeta2_from_beta(), math.pi ** 2 / 6,
                               places=10)

    def test_zeta3_adaptation(self):
        # report heuristic: B(2,2)/ln(x) == zeta(3)
        z3 = bridge.zeta3(20000)
        self.assertAlmostEqual(z3, sum(1 / k ** 3 for k in range(1, 20001)),
                               places=8)
        x = bridge.adapt_x_for_zeta(z3)
        self.assertAlmostEqual(bridge.beta(2, 2) / bridge.fln(x), z3, places=6)


class TestGenerateRelations(unittest.TestCase):
    def test_family_generated(self):
        rels = bridge.generate_relations()
        got = {(p, q): v for p, q, v in rels}
        self.assertAlmostEqual(got[(2, 2)], 1 / 6, places=10)
        self.assertAlmostEqual(got[(2, 3)], py_beta(2, 3), places=10)
        self.assertAlmostEqual(got[(3, 3)], py_beta(3, 3), places=10)

    def test_app_records_to_tuplespace(self):
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            vm = run_program(os.path.join(_PKG, "apps", "beta",
                                          "beta_app.bada"))
        store = vm.tuplespace["beta"]
        self.assertAlmostEqual(store[0], 1 / 6, places=10)
        self.assertTrue(any("HEURISTIC" in str(x) for x in store))


if __name__ == "__main__":
    unittest.main()
