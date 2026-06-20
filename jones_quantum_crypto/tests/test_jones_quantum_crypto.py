import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from jones_quantum_crypto.jones import (jones_polynomial, jones_str,
                                        kauffman_bracket, normalized_bracket)
from jones_quantum_crypto.qcipher import JonesQuantumCipher, braid_key
from jones_quantum_crypto.qsign import QuantumDigitalSignature
from jones_quantum_crypto.activation import JonesActivation, demo


class TestJonesPolynomial(unittest.TestCase):
    def test_unknot(self):
        self.assertEqual(jones_polynomial([]), {0.0: 1})

    def test_reidemeister_one_reduces_to_unknot(self):
        # a single kink (σ1 on 2 strands) is an unknot: V = 1
        self.assertEqual(jones_polynomial([1], n=2), {0.0: 1})

    def test_right_trefoil(self):
        # known: V = -t^4 + t^3 + t
        self.assertEqual(jones_polynomial([1, 1, 1]),
                         {1.0: 1, 3.0: 1, 4.0: -1})

    def test_left_trefoil_is_mirror(self):
        # known: V = -t^-4 + t^-3 + t^-1
        self.assertEqual(jones_polynomial([-1, -1, -1]),
                         {-1.0: 1, -3.0: 1, -4.0: -1})

    def test_hopf_link(self):
        # known (one chirality): V = -t^{1/2} - t^{5/2}
        self.assertEqual(jones_polynomial([1, 1]),
                         {0.5: -1, 2.5: -1})

    def test_bracket_is_laurent_in_A(self):
        b = kauffman_bracket([1, 1, 1])
        self.assertEqual(b.canonical(), [(-7, 1), (-3, -1), (5, -1)])

    def test_jones_str(self):
        self.assertEqual(jones_str([1, 1, 1]), "+1*t^1 +1*t^3 -1*t^4")


class TestJonesCipher(unittest.TestCase):
    def test_key_deterministic_from_braid(self):
        self.assertEqual(braid_key([1, 1, 1]), braid_key([1, 1, 1]))

    def test_different_braids_different_keys(self):
        self.assertNotEqual(braid_key([1, 1, 1]), braid_key([1, 1]))

    def test_encrypt_decrypt_roundtrip(self):
        c = JonesQuantumCipher.from_braid([1, 1, 1])
        msg = b"the quantum channel is open"
        self.assertEqual(c.decrypt(c.encrypt(msg)), msg)

    def test_wrong_key_fails_auth(self):
        c1 = JonesQuantumCipher.from_braid([1, 1, 1])
        c2 = JonesQuantumCipher.from_braid([1, 1])
        blob = c1.encrypt(b"secret")
        with self.assertRaises(ValueError):
            c2.decrypt(blob)


class TestQuantumDigitalSignature(unittest.TestCase):
    def setUp(self):
        self.qds = QuantumDigitalSignature()
        self.sig = self.qds.issue(b"msg", [1, 1, 1], "secret-key")

    def test_verify_valid(self):
        self.assertTrue(QuantumDigitalSignature.verify(self.sig))

    def test_verify_tampered_message(self):
        bad = dict(self.sig)
        bad["message"] = bad["message"][:-2] + ("00" if bad["message"][-2:]
                                                 != "00" else "11")
        self.assertFalse(QuantumDigitalSignature.verify(bad))

    def test_cryptanalyze_correct_key(self):
        res = QuantumDigitalSignature.cryptanalyze(self.sig, "secret-key")
        self.assertTrue(res["ok"])
        self.assertEqual(res["braid"], [1, 1, 1])

    def test_cryptanalyze_wrong_key(self):
        res = QuantumDigitalSignature.cryptanalyze(self.sig, "wrong")
        self.assertFalse(res["ok"])

    def test_bruteforce_breaks_weak_pin(self):
        sig = self.qds.issue(b"m", [1, 1], "0007")
        res = QuantumDigitalSignature.cryptanalyze_bruteforce(
            sig, (f"{i:04d}" for i in range(20)))
        self.assertTrue(res["ok"])
        self.assertEqual(res["key"], "0007")


class TestActivation(unittest.TestCase):
    def test_cryptanalysis_activates_jones_cipher(self):
        qds = QuantumDigitalSignature()
        sig = qds.issue(b"launch", [1, 1, 1], "pin99")
        act = JonesActivation()
        rep = act.activate_from_cryptanalysis(sig, "pin99")
        self.assertTrue(rep["activated"])
        self.assertEqual(rep["recovered_braid"], [1, 1, 1])
        # the activated cipher works and matches a fresh braid-keyed cipher
        blob = act.encrypt(b"go")
        self.assertEqual(act.decrypt(blob), b"go")
        self.assertEqual(
            rep["key_fingerprint"],
            JonesQuantumCipher.from_braid([1, 1, 1]).fingerprint())

    def test_failed_cryptanalysis_does_not_activate(self):
        qds = QuantumDigitalSignature()
        sig = qds.issue(b"x", [1, 1, 1], "right")
        act = JonesActivation()
        rep = act.activate_from_cryptanalysis(sig, "wrong")
        self.assertFalse(rep["activated"])
        with self.assertRaises(RuntimeError):
            act.encrypt(b"nope")

    def test_demo_end_to_end(self):
        out = demo()
        self.assertTrue(out["signature_valid"])
        self.assertTrue(out["activation"]["activated"])
        self.assertTrue(out["roundtrip_ok"])


if __name__ == "__main__":
    unittest.main()
