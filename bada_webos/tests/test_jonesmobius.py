"""Jones-Mobius causal analyzer in Bada: are the Beta/Zeta equations
Jones-polynomial Mobius equations, and are they causally linked?"""

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_PKG)
for p in (_PKG, _ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from jonesmobius import bridge


class TestMobiusAlgebra(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(bridge.mobius_class([1, 0, 0, 1]), 1)   # identity
        self.assertEqual(bridge.mobius_class([2, 0, 0, 4]), 2)   # scaling
        self.assertEqual(bridge.mobius_class([1, 5, 0, 1]), 3)   # translation
        self.assertEqual(bridge.mobius_class([0, 1, 1, 0]), 4)   # inversion

    def test_inversion_is_involution(self):
        self.assertTrue(bridge.is_involution([0, 1, 1, 0]))      # t -> 1/t
        self.assertFalse(bridge.is_involution([1, 5, 0, 1]))

    def test_inversion_maps_value(self):
        self.assertAlmostEqual(bridge.mobius_apply([0, 1, 1, 0], 4.0),
                               0.25, places=9)


class TestCausalGraph(unittest.TestCase):
    def test_all_equations_are_mobius_and_verified(self):
        graph = bridge.causal_graph()
        self.assertEqual(len(graph), 3)
        kinds = {tuple(e[:2]): e[2] for e in graph}
        self.assertEqual(kinds[("B22", "B23")], 2)        # scaling
        self.assertEqual(kinds[("B22", "zeta2")], 2)      # scaling
        self.assertEqual(kinds[("Jones", "Jones_mirror")], 4)  # inversion
        # every edge verified (the equation really is that Mobius map)
        for src, dst, kind, verified in graph:
            self.assertEqual(verified, 1, f"{src}->{dst} not verified")


if __name__ == "__main__":
    unittest.main()
