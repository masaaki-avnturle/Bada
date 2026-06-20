"""AL — the Laevatein AI/machine OS, all libraries written in Bada."""

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_PKG)
for p in (_PKG, _ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from al import bridge, AlOS
from bada import run_program


class TestQuantumAlgorithm(unittest.TestCase):
    def test_grover_finds_marked(self):
        for nq, marked in [(3, 5), (4, 11), (4, 0), (5, 17)]:
            with self.subTest(nq=nq, marked=marked):
                self.assertEqual(bridge.grover(nq, marked), marked)


class TestLambdaCooling(unittest.TestCase):
    def test_nominal_load_no_meltdown(self):
        maxt, finalt, meltdown = bridge.cooling_sim(120, 220, 0.8)
        self.assertEqual(meltdown, 0)
        self.assertLess(maxt, 500)

    def test_overload_melts_down(self):
        _, _, meltdown = bridge.cooling_sim(120, 2000, 0.8)
        self.assertEqual(meltdown, 1)


class TestConsciousness(unittest.TestCase):
    def test_within_bounds(self):
        phi = bridge.consciousness(8, 60, 1005)
        self.assertGreaterEqual(phi, 0)
        self.assertLessEqual(phi, 8)

    def test_evolution_reaches_high_ignition(self):
        # hill-climbing should ignite most of the network
        self.assertGreaterEqual(bridge.consciousness(8, 80, 4242), 4)


class TestRobotFPGA(unittest.TestCase):
    def test_clear_path_goes_straight(self):
        self.assertEqual(bridge.robot_fpga([0, 0, 0]), [1, 1])

    def test_obstacle_ahead_left_open_turns_left(self):
        # front=1,left=0,right=1 -> stop left motor, run right -> turn
        self.assertEqual(bridge.robot_fpga([1, 0, 1]), [0, 1])


class TestAprioriEngine(unittest.TestCase):
    def test_generates_code(self):
        code = bridge.apriori(77, 3)
        self.assertIn("def", code)
        self.assertEqual(code.count("def "), 3)

    def test_deterministic(self):
        self.assertEqual(bridge.apriori(5, 4), bridge.apriori(5, 4))


class TestAlOS(unittest.TestCase):
    def test_boot_report(self):
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            r = AlOS().boot()
        self.assertTrue(r["online"])
        self.assertEqual(r["resonance_mode"], 11)
        self.assertFalse(r["meltdown"])
        self.assertGreaterEqual(r["consciousness"], 0)

    def test_app_records_to_tuplespace(self):
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            vm = run_program(bridge.APP)
        self.assertIn("AL-online", vm.tuplespace["al"])


if __name__ == "__main__":
    unittest.main()
