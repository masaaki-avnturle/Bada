"""System-transport equation group (apps/system_transport, Bada): the
verdicts the video shows are recomputed here and cross-checked vs Python."""

import cmath
import math
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
if _PKG not in sys.path:
    sys.path.insert(0, _PKG)

from contact import bridge, st_video            # noqa: E402  (bridge sets sys.path)
from bada import load_program, run_source         # noqa: E402

_LIB = os.path.join(_PKG, "apps", "system_transport", "lib", "components.bada")
_SRC = load_program(_LIB)


def bada(expr):
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_source(_SRC + "\nprint " + expr)
    return buf.getvalue().strip().splitlines()[-1]


def nums(expr):
    return [float(x) for x in bada(expr).strip("[]").split(", ")]


class TestVerified(unittest.TestCase):
    def test_beta(self):
        self.assertLess(nums("check_beta()")[0], 1e-9)

    def test_dgamma_is_minus_euler_gamma(self):
        self.assertAlmostEqual(nums("check_dgamma()")[1], -0.5772156649015329, places=10)

    def test_ricci_extinction(self):
        r = nums("check_ricci(7.0, 11.0, 200)")
        self.assertAlmostEqual(r[1], math.sqrt(49 - 44), places=7)
        self.assertEqual(r[2], 12.25)

    def test_planck(self):
        lp = math.sqrt(1.054571817e-34 * 6.67430e-11 / 299792458.0 ** 3)
        self.assertAlmostEqual(nums("check_planck()")[1] * 1e-35, lp, delta=1e-42)

    def test_mobius_non_orientable(self):
        self.assertAlmostEqual(float(bada("check_mobius()")), -1.0, places=9)

    def test_icosian_group(self):
        self.assertEqual(bada("len(icosian_group())"), "120")
        self.assertEqual(bada("len(icosian_edges(icosian_group()))"), "720")
        self.assertLess(float(bada("check_icosa()")), 1e-12)

    def test_hopf_fibres(self):
        self.assertLess(float(bada("check_seifert()")), 1e-9)
        self.assertEqual(bada("len(fibre_reps(icosian_group()))"), "12")

    def test_heisenberg(self):
        self.assertLess(float(bada("check_heisenberg(0.7, 2.0)")), 1e-6)

    def test_zeta_zeros(self):
        self.assertLess(float(bada("check_zeros()")), 1e-6)
        z = nums("zeta_em([2.0, 0.0])")
        self.assertAlmostEqual(z[0], math.pi ** 2 / 6, places=10)

    def test_gauss(self):
        self.assertAlmostEqual(nums("check_gauss()")[1], math.pi, places=12)


class TestRejected(unittest.TestCase):
    def test_sin_ix_stated_form_fails(self):
        r = [float(bada("check_sin_ix(1.3)[0]")), float(bada("check_sin_ix(1.3)[1]"))]
        self.assertGreater(r[0], 1.0)            # stated (e^-x + e^x)/2i is wrong
        self.assertLess(r[1], 1e-12)             # corrected form holds
        self.assertAlmostEqual(cmath.sin(1.3j).imag, math.sinh(1.3), places=12)

    def test_pi_e_vs_e_pi(self):
        r = nums("check_pie()")
        self.assertAlmostEqual(r[1], math.pi ** math.e, places=9)
        self.assertAlmostEqual(r[2], math.e ** math.pi, places=9)
        self.assertGreater(r[0], 0.5)

    def test_euler_characteristic(self):
        self.assertEqual(bada("euler_char(3)"), "1")
        self.assertEqual(bada("euler_char(2)"), "2")

    def test_xpow_roots(self):
        self.assertEqual(bada("check_xpow()[0]"), "[0.5, 1]")


class TestStream(unittest.TestCase):
    def test_parse(self):
        text = "\n".join([
            "CARD§E01§ST p.9§t§eq§res§VERIFIED§comp",
            "SITE 0 E3 gauss_bell 1.0 2.0",
            "PART tetra 1 6 4 | 0 1 0 2 0 3 1 2 1 3 2 3 ",
            "SV tetra | 0 0 0 1 0 0 0 1 0 0 0 1 ",
            "PART zeta_runner 0 7 1 | ",
            "FH 0 0.0 0 0 0 48 0 0 7 0 0 0.5",
            "FV 0 zeta_runner | 1 2 3 ",
        ])
        d = st_video.parse_stream(text)
        self.assertEqual(d["cards"][0]["verdict"], "VERIFIED")
        self.assertEqual(d["parts"][0]["e"], [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]])
        self.assertEqual(d["frames"][0]["p"]["zeta_runner"], [1, 2, 3])
        self.assertEqual(d["frames"][0]["h"]["zetat"], 0.5)


if __name__ == "__main__":
    unittest.main()
