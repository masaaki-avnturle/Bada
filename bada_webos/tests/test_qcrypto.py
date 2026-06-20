import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_PKG)
for p in (_PKG, _ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from qcrypto import QuantumCryptoApp
from terminal import Terminal


class TestQuantumCryptoApp(unittest.TestCase):
    def test_boot_activates_jones_crypto(self):
        r = QuantumCryptoApp().boot()
        self.assertTrue(r["signature_valid"])
        self.assertTrue(r["activation"]["activated"])
        self.assertEqual(r["activation"]["recovered_braid"], [1, 1, 1])
        self.assertTrue(r["roundtrip_ok"])

    def test_jones_of_trefoil(self):
        d = QuantumCryptoApp().jones([1, 1, 1])
        self.assertEqual(d["jones"], "+1*t^1 +1*t^3 -1*t^4")

    def test_render_html(self):
        html = QuantumCryptoApp().render_html()
        self.assertIn("Quantum Crypto (Jones)", html)
        self.assertIn("ACTIVATED", html)


class TestTerminalQcrypto(unittest.TestCase):
    def test_qcrypto_jones_command(self):
        out = Terminal().bash("qcrypto jones 1 1 1")
        self.assertIn("t^3", out)

    def test_qcrypto_demo_command(self):
        out = Terminal().bash("qcrypto")
        self.assertIn("ACTIVATED", out)

    def test_help_lists_qcrypto(self):
        self.assertIn("qcrypto", Terminal().bash("help"))


if __name__ == "__main__":
    unittest.main()
