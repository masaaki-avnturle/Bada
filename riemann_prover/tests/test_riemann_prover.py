import copy
import math
import unittest

from riemann_prover import (zeta, hardy_z, dirichlet_l, verify_rh_to_height,
                            schoenfeld_check, drh_evidence, CHARACTERS,
                            build_certificate, seal, check_seal)


class TestZeta(unittest.TestCase):
    def test_known_values(self):
        self.assertAlmostEqual(zeta(2).real, math.pi ** 2 / 6, places=12)
        self.assertAlmostEqual(zeta(0.5).real, -1.4603545088095868, places=11)
        self.assertAlmostEqual(zeta(-1).real, -1 / 12, places=12)
        self.assertLess(abs(zeta(complex(0.5, 14.134725141734693))), 1e-12)

    def test_dirichlet_l(self):
        chi4 = CHARACTERS["chi_-4"]
        self.assertAlmostEqual(dirichlet_l(1, chi4).real, math.pi / 4, places=12)
        self.assertAlmostEqual(dirichlet_l(2, chi4).real, 0.915965594177219, places=12)  # Catalan

    def test_hardy_z_is_modulus(self):
        self.assertAlmostEqual(abs(hardy_z(20.0)), abs(zeta(complex(0.5, 20.0))), places=12)


class TestVerification(unittest.TestCase):
    def test_rh_to_height_100(self):
        r = verify_rh_to_height(100.0, list_zeros=3)
        self.assertEqual(r["status"], "verified")
        self.assertEqual(r["zeros_in_strip_argument_principle"], 29)
        self.assertEqual(r["zeros_on_critical_line_sign_changes"], 29)
        for got, want in zip(r["first_zeros"], (14.134725142, 21.022039639, 25.010857580)):
            self.assertAlmostEqual(got, want, places=8)

    def test_schoenfeld(self):
        r = schoenfeld_check(10 ** 5)
        self.assertEqual(r["status"], "verified")
        self.assertLess(r["max_ratio"], 1)

    def test_drh_sqrt2(self):
        d = drh_evidence("chi_-4", 0.0, 10 ** 5)
        self.assertEqual(d["status"], "open")           # evidence, never a proof
        last = d["table"][-1]
        self.assertLess(last["rel_error_vs_DRH_limit"], 0.1)
        self.assertGreater(last["rel_error_vs_plain_L"], 0.3)


class TestCertificate(unittest.TestCase):
    def test_seal_and_tamper(self):
        cert = seal(build_certificate(verify_rh_to_height(50.0), schoenfeld_check(10 ** 4),
                                      [drh_evidence("chi_-3", 0.0, 10 ** 3)]), [1, 1, 1])
        self.assertEqual(cert["verdicts"]["riemann_hypothesis"], "open")
        self.assertEqual(cert["verdicts"]["deep_riemann_hypothesis"], "open")
        self.assertTrue(check_seal(cert))
        self.assertFalse(check_seal(cert, [1, 1]))      # wrong braid (Hopf link)
        forged = copy.deepcopy(cert)
        forged["verdicts"]["riemann_hypothesis"] = "proved"
        self.assertFalse(check_seal(forged))


if __name__ == "__main__":
    unittest.main()
