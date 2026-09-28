"""Contact Machine blueprint generator (apps/contact, Bada) — the Bada maths
is cross-checked against Python, and the OBJ blueprint is validated."""

import math
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
if _PKG not in sys.path:
    sys.path.insert(0, _PKG)

from contact import bridge, ContactApp

GAMMA = 18 * 3600.0


class TestMathKernel(unittest.TestCase):
    def test_gamma_function(self):
        self.assertAlmostEqual(bridge.num("fgamma(0.5)"), math.sqrt(math.pi), places=10)
        self.assertAlmostEqual(bridge.num("fgamma(5.0)"), 24.0, places=9)

    def test_ring_ratio_is_central_binomial(self):
        for k in range(4):
            self.assertAlmostEqual(bridge.num(f"ring_ratio({k})"),
                                   math.comb(2 * k, k) / 4 ** k, places=10)

    def test_trefoil_spins(self):
        # |V(e^{i k pi/2})| for V = t + t^3 - t^4 : 1, 3, 1
        for k, want in ((1, 1.0), (2, 3.0), (3, 1.0)):
            self.assertAlmostEqual(bridge.num(f"ring_spin({k})"), want, places=9)

    def test_atan2(self):
        for y, x in ((1.0, -1.0), (-2.0, 0.5), (-3.0, -4.0), (0.2, 7.0)):
            self.assertAlmostEqual(bridge.num(f"fatan2({y}, {x})"),
                                   math.atan2(y, x), places=10)


class TestRelativity(unittest.TestCase):
    def test_rapidity(self):
        self.assertAlmostEqual(bridge.num(f"rapidity({GAMMA})"), math.acosh(GAMMA), places=9)

    def test_one_minus_beta(self):
        want = 1 / (GAMMA ** 2 * (1 + math.sqrt(1 - 1 / GAMMA ** 2)))
        self.assertAlmostEqual(bridge.num(f"one_minus_beta({GAMMA})") / want, 1.0, places=9)

    def test_boost_invariant(self):
        self.assertAlmostEqual(bridge.num(f"boost_invariant({GAMMA})"), 1.0, places=12)


class TestPortDirectory(unittest.TestCase):
    def test_warp_matched_port(self):
        self.assertEqual(int(bridge.num(f"warp_matched_port({GAMMA})")), 5)

    def test_mirror_warp_matches_paper(self):
        # paper Table 7, row 5: P*_W = e^{4 pi} = 286,751...
        mirror = bridge.call("reflect(port(5))").strip("[]").split(", ")
        self.assertEqual(mirror[0], "4")            # Thurston flip 9 - 5
        self.assertAlmostEqual(float(mirror[4]), math.exp(4 * math.pi), delta=1e-4)

    def test_reflection_involution(self):
        for n in range(1, 11):
            self.assertEqual(bridge.call(f"same_port(reflect(reflect(port({n}))), port({n}))"), "1")


class TestBlueprint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = ContactApp().generate()

    def test_parts(self):
        names = [p["name"] for p in self.app.parts]
        self.assertEqual(names, ["ring_precession", "ring_nutation", "ring_spin",
                                 "pod", "gantry"])

    def test_edges_in_range(self):
        for p in self.app.parts:
            self.assertTrue(p["edges"])
            for a, b in p["edges"]:
                self.assertTrue(0 <= a < len(p["vertices"]))
                self.assertTrue(0 <= b < len(p["vertices"]))

    def test_ring_radii(self):
        hub = 1.7 * 15.0
        for p, want in zip(self.app.parts[:3], (15.0, 7.5, 5.625)):
            for x, y, z in p["vertices"]:
                self.assertAlmostEqual(math.sqrt(x * x + y * y + (z - hub) ** 2), want, places=6)

    def test_obj_roundtrip_at_rest(self):
        obj = bridge.call_text("to_obj(machine([15.0, 1.5, 25.5, 0.3, 11.77, 0.0], 48))")
        parts = bridge.parse_obj(obj)
        self.assertEqual(len(parts), 5)
        self.assertEqual(len(parts[0]["vertices"]), 48)

    def test_ring_normals_at_rest(self):
        # at tau = 0 the three ring planes are mutually orthogonal
        normals = []
        for k in range(3):
            a = eval(bridge.call(f"ring_part(\"r\", 1.0, {k}, 0.0, 0.3, 0.0, 48)[1][0]"))
            b = eval(bridge.call(f"ring_part(\"r\", 1.0, {k}, 0.0, 0.3, 0.0, 48)[1][12]"))
            n = [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
            L = math.sqrt(sum(c * c for c in n))
            normals.append([c / L for c in n])
        for i in range(3):
            for j in range(i + 1, 3):
                self.assertLess(abs(sum(normals[i][k] * normals[j][k] for k in range(3))), 1e-9)

    def test_rings_tumble(self):
        # a gimbal spins about an in-plane axis, so its points actually move
        a = eval(bridge.call("ring_part(\"r\", 1.0, 0, 0.0, 0.0, 0.0, 48)[1][6]"))
        b = eval(bridge.call("ring_part(\"r\", 1.0, 0, 1.0, 0.0, 0.0, 48)[1][6]"))
        self.assertGreater(math.dist(a, b), 0.5)

    def test_report_checks_pass(self):
        self.assertIn("koma invariant OK", self.app.report)
        self.assertIn("port #5 (H2xR)", self.app.report)

    def test_save(self):
        with tempfile.TemporaryDirectory() as d:
            paths = self.app.save(d)
            for path in paths.values():
                self.assertGreater(os.path.getsize(path), 0)
            with open(paths["obj"]) as f:
                self.assertTrue(any(line.startswith("o ring_spin") for line in f))


if __name__ == "__main__":
    unittest.main()


class TestVideoStream(unittest.TestCase):
    def test_parse_stream(self):
        from contact import video
        text = ("CARD|t|x = 1|1\n"
                + bridge.call_text("topology_lines(machine([15.0, 1.5, 25.5, 0.3, 11.77, 0.0], 8))").rstrip() + "\n"
                "FRAME 0 0.0 0 0 0 48 0 | 1 2 3 4 5 6\n")
        d = video.parse_stream(text)
        self.assertEqual(d["cards"][0]["value"], "1")
        self.assertEqual([p["name"] for p in d["parts"]],
                         ["ring_precession", "ring_nutation", "ring_spin", "pod", "gantry"])
        self.assertEqual(d["parts"][0]["n"], 8)
        self.assertEqual(d["frames"][0]["xyz"], [1, 2, 3, 4, 5, 6])

    def test_frame_line_matches_vertices(self):
        line = bridge.call("frame_line(machine([15.0, 1.5, 25.5, 0.3, 11.77, 0.5], 8))")
        n = int(bridge.num("count_vertices(machine([15.0, 1.5, 25.5, 0.3, 11.77, 0.5], 8))"))
        self.assertEqual(len(line.split()), 3 * n)

    def test_r3(self):
        self.assertEqual(bridge.num("r3(-2.42789)"), -2.428)
        self.assertEqual(bridge.num("r3(51.32641)"), 51.326)
