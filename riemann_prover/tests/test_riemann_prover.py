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
        self.assertAlmostEqual(dirichlet_l(3, chi4).real, math.pi ** 3 / 32, places=12)
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


class TestPatchGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cert = seal(build_certificate(verify_rh_to_height(50.0), schoenfeld_check(10 ** 4),
                                          [drh_evidence("chi_-3", 0.0, 10 ** 3)]), [1, 1, 1])

    def test_honest_certificate_accepted(self):
        from riemann_prover.patchguard import check
        rep = check([self.cert], recompute=True)
        self.assertEqual(rep["verdict"], "ACCEPT")
        self.assertEqual(rep["tuples"][-1][-1], "ACCEPT")

    def test_claiming_a_proof_is_rejected(self):
        from riemann_prover.patchguard import check
        forged = copy.deepcopy(self.cert)
        forged["verdicts"]["riemann_hypothesis"] = "proved"
        rep = check([self.cert, seal(forged, [1, 1, 1])])   # even when re-sealed
        self.assertEqual(rep["verdict"], "REJECT")
        self.assertIn("RG01", [f["id"] for f in rep["findings"]])

    def test_forged_zero_count_caught_by_recompute(self):
        from riemann_prover.patchguard import check
        forged = copy.deepcopy(self.cert)
        forged["rh_bounded"]["zeros_in_strip_argument_principle"] += 1
        forged["rh_bounded"]["zeros_on_critical_line_sign_changes"] += 1
        rep = check([self.cert, seal(forged, [1, 1, 1])], recompute=True)
        self.assertIn("RG03", [f["id"] for f in rep["findings"]])
        self.assertEqual(rep["verdict"], "REJECT")

    def test_fold_cancels_reverted_stage(self):
        from riemann_prover.patchguard import check
        bad = copy.deepcopy(self.cert)
        bad["drh_evidence"][0]["status"] = "proved"
        rep = check([self.cert, bad, self.cert])
        self.assertEqual(rep["verdict"], "ACCEPT")
        self.assertEqual(rep["net_patch"], {})
        self.assertTrue(rep["cancelled"])

    def test_shrinking_height_needs_review(self):
        from riemann_prover.patchguard import check
        small = seal(build_certificate(verify_rh_to_height(30.0), schoenfeld_check(10 ** 4),
                                       [drh_evidence("chi_-3", 0.0, 10 ** 3)]), [1, 1, 1])
        self.assertEqual(check([self.cert, small])["verdict"], "REVIEW")


class TestQuantumSearch(unittest.TestCase):
    def test_grover_finds_single_marked_state(self):
        from riemann_prover.qsim import grover_search
        marked = [False] * 256
        marked[173] = True
        g = grover_search(marked)
        self.assertGreater(g["success_probability"], 0.99)
        self.assertEqual(g["measured"], 173)

    def test_false_statement_is_disproved(self):
        from riemann_prover.qsim import quantum_search
        for qubits in (6, 10):          # sparse and dense counterexample sets
            self.assertEqual(quantum_search("euler_polynomial", qubits)["status"], "disproved")
        q = quantum_search("euler_polynomial", 6)
        self.assertFalse(all((q["counterexample"] ** 2 + q["counterexample"] + 41) % d
                             for d in range(2, 200)))

    def test_open_problems_stay_open(self):
        from riemann_prover.qsim import quantum_search
        for name in ("riemann_lagarias", "goldbach", "collatz", "legendre"):
            q = quantum_search(name, 8)
            self.assertEqual((q["status"], q["bounded_status"], q["marked"]), ("open", "verified", 0))

    def test_gate_rejects_quantum_proof_claim(self):
        from riemann_prover.patchguard import check
        from riemann_prover.qsim import quantum_search_all
        cert = seal(build_certificate(verify_rh_to_height(50.0), schoenfeld_check(10 ** 4),
                                      [drh_evidence("chi_-3", 0.0, 10 ** 3)],
                                      quantum_search_all(6)), [1, 1, 1])
        self.assertEqual(check([cert])["verdict"], "ACCEPT")
        forged = copy.deepcopy(cert)
        forged["quantum_search"][0]["status"] = "proved"
        fake = copy.deepcopy(cert)
        fake["quantum_search"][1].update(status="disproved", counterexample=10)
        for bad in (forged, fake):
            rep = check([cert, seal(bad, [1, 1, 1])])
            self.assertEqual(rep["verdict"], "REJECT")
            self.assertIn("RG10", [f["id"] for f in rep["findings"]])


if __name__ == "__main__":
    unittest.main()
