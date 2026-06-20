"""The Jones polynomial implemented in the Bada language, cross-checked
against the reference implementation in jones_quantum_crypto."""

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_PKG)
for p in (_PKG, _ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from qcrypto.bada_jones import bada_bracket, bada_jones_show
from jones_quantum_crypto.jones import jones_str, kauffman_bracket
from bada import run_program

KNOTS = {
    "unknot": [],
    "trefoil": [1, 1, 1],
    "mirror_trefoil": [-1, -1, -1],
    "figure8": [1, -2, 1, -2],
}
LINKS = {"hopf": [1, 1]}


class TestBadaJones(unittest.TestCase):
    def test_bracket_matches_reference(self):
        # the Kauffman bracket is exact integer Laurent — must match for
        # every knot AND link.
        for name, braid in {**KNOTS, **LINKS}.items():
            with self.subTest(name=name):
                self.assertEqual(bada_bracket(braid),
                                 dict(kauffman_bracket(braid).canonical()))

    def test_jones_string_matches_reference_for_knots(self):
        for name, braid in KNOTS.items():
            with self.subTest(name=name):
                self.assertEqual(bada_jones_show(braid), jones_str(braid))

    def test_trefoil_is_the_known_polynomial(self):
        self.assertEqual(bada_jones_show([1, 1, 1]), "+1*t^1 +1*t^3 -1*t^4")

    def test_app_program_runs_on_vm(self):
        path = os.path.join(_PKG, "apps", "quantum_crypto_jones.bada")
        vm = run_program(path)
        # the app records the Jones invariant in the Akashic TupleSpace
        store = vm.tuplespace["jones"]
        self.assertIn("jones-quantum-cryptography-activated", store)
        self.assertTrue(any("t^3" in str(x) for x in store))


if __name__ == "__main__":
    unittest.main()
