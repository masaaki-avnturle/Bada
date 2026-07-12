"""Equation generator in Bada: generate the equation group from Euler's zeta
and beta via O(x)=zeta(s)/sum a_k f^k (cross-checked against Python)."""

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_PKG)
for p in (_PKG, _ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from eqgen import bridge
from bada import run_program

ZETA3 = sum(1.0 / k ** 3 for k in range(1, 2001))
ONES = [1, 1, 1, 1, 1, 1, 1, 1]


class TestPowerSeries(unittest.TestCase):
    def test_geometric(self):
        # 1+f+...+f^7
        self.assertAlmostEqual(bridge.power_series(ONES, 0.5),
                               sum(0.5 ** k for k in range(8)), places=9)


class TestGenerator(unittest.TestCase):
    def test_o_from_zeta_and_inverse(self):
        o = bridge.o_from_zeta(ZETA3, ONES, 0.5)
        self.assertAlmostEqual(o, ZETA3 / sum(0.5 ** k for k in range(8)),
                               places=9)
        # O * series regenerates zeta(3)
        self.assertAlmostEqual(bridge.zeta_from_series(o, ONES, 0.5), ZETA3,
                               places=9)

    def test_generate_equation_group(self):
        eqs = bridge.generate_equations(ZETA3, ONES, [0.1, 0.3, 0.5, 0.7])
        self.assertEqual(len(eqs), 4)
        for f, o in eqs:
            self.assertAlmostEqual(o, ZETA3 / sum(f ** k for k in range(8)),
                                   places=8)


class TestFlowIn(unittest.TestCase):
    def test_flow_in_finds_geometric_root(self):
        # O = 1  <=>  zeta(3) = sum f^k ~ 1/(1-f)  =>  f ~ 1 - 1/zeta(3)
        f, o, err = bridge.flow_in(ZETA3, ONES, 0.0, 0.9, 900, 1)
        self.assertAlmostEqual(f, 1 - 1 / ZETA3, delta=0.01)
        self.assertAlmostEqual(o, 1.0, delta=0.01)


class TestEulerCF(unittest.TestCase):
    def test_simple_cf(self):
        # 1 + 1/(1 + 1/(1+0)) = 1.5
        self.assertAlmostEqual(bridge.euler_cf(1, [1, 1], [1, 1]), 1.5,
                               places=9)


class TestApp(unittest.TestCase):
    def test_records_tuplespace(self):
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            vm = run_program(os.path.join(_PKG, "apps", "eqgen",
                                          "eqgen_app.bada"))
        store = vm.tuplespace["eqgen"]
        self.assertTrue(any("generates the equation group" in str(x)
                            for x in store))


if __name__ == "__main__":
    unittest.main()
