import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_PKG)
for p in (_PKG, _ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from quantum.shor9 import Shor9, demo_correct
from wm.w9wm import W9wm, NUM_SCREENS
from railsbridge.rails_to_os import RailsField, RailsResource, RailsToOS
from cloud.settings_bridge import (Bridge, CloudStore, HardwareProfile,
                                    Repeater, SettingsPanel)
from ultranet import BridgeRepeaterNet, GravityPort, UltraNetwork, XORNet
from android.installer import (Android12Installer, AndroidManifest,
                               InstallError)
from kernel.kernel import QuantumKernel
from webos import BadaWebOS


class TestShor9QEC(unittest.TestCase):
    def test_all_single_qubit_errors_corrected(self):
        for kind in ("X", "Y", "Z"):
            for q in range(9):
                d = demo_correct(kind, q)
                self.assertGreater(d["fidelity_after"], 0.999,
                                   f"{kind}@{q} not corrected")

    def test_no_error_is_identity(self):
        code = Shor9()
        code.encode(0.6, 0.8)
        self.assertEqual(code.syndrome(), tuple([0] * 8))


class TestW9wm(unittest.TestCase):
    def test_eight_virtual_screens(self):
        self.assertEqual(NUM_SCREENS, 8)
        wm = W9wm()
        self.assertEqual(wm.screens, 8)

    def test_new_focus_hide_unhide(self):
        wm = W9wm()
        a = wm.new_window("a")
        b = wm.new_window("b")
        self.assertEqual(wm.focused, b.wid)
        wm.hide(b.wid)
        self.assertEqual(wm.focused, a.wid)
        self.assertIn(b, wm.hidden_windows())
        wm.unhide(b.wid)
        self.assertEqual(wm.focused, b.wid)

    def test_screen_switch_isolates_windows(self):
        wm = W9wm()
        wm.new_window("s0")
        wm.switch_screen(3)
        wm.new_window("s3")
        self.assertEqual([w.name for w in wm.windows_on(3)], ["s3"])
        self.assertEqual([w.name for w in wm.windows_on(0)], ["s0"])

    def test_root_menu_has_fixed_then_screens(self):
        menu = W9wm().root_menu()
        self.assertEqual(menu[:5], ["New", "Reshape", "Move", "Delete",
                                    "Hide"])
        self.assertEqual(sum(1 for m in menu if m.startswith("Screen")), 8)


class TestRailsToOS(unittest.TestCase):
    def test_transpile_maps_mvc(self):
        res = RailsResource("article", [RailsField("title"),
                                        RailsField("body", "text")])
        app = RailsToOS().transpile(res)
        self.assertEqual(app.object_schema, {"title": "string",
                                             "body": "text"})
        self.assertIn("article.index()", app.methods)
        self.assertIn("os-window", app.windows["index"])
        self.assertIn("/dev/soft/articles", app.driver)


class TestCloudBridge(unittest.TestCase):
    def test_set_propagates_to_cloud_via_repeater(self):
        cloud = CloudStore()
        bridge = Bridge(cloud, Repeater(hops=2))
        panel = SettingsPanel(bridge)
        panel.set("theme", "dark")
        self.assertEqual(cloud.get("theme"), "dark")
        self.assertGreater(bridge.repeater.relayed, 0)

    def test_adapt_to_hardware(self):
        cloud = CloudStore()
        panel = SettingsPanel(Bridge(cloud))
        panel.adapt_to_hardware(HardwareProfile(screen_w=600, dpi=192,
                                                has_touch=True))
        self.assertEqual(panel.settings["layout"], "handheld")
        self.assertEqual(panel.settings["font_scale"], 2.0)
        self.assertEqual(panel.settings["hit_target"], 44)
        self.assertEqual(cloud.get("layout"), "handheld")


class TestUltranet(unittest.TestCase):
    def test_xor_learns(self):
        net = XORNet()
        net.train(epochs=4000)
        self.assertEqual(net.accuracy(), 1.0)

    def test_repeater_boosts_downstream(self):
        net = BridgeRepeaterNet(hop_attenuation=0.6)
        for n in "ABCDE":
            net.add_node(n)
        for a, b in (("A", "B"), ("B", "C"), ("C", "D"), ("D", "E")):
            net.bridge(a, b)
        base = net.propagate("A")["E"]
        net.set_repeater("C", 2.0)
        boosted = net.propagate("A")["E"]
        self.assertGreater(boosted, base)

    def test_gravity_port_traps_weak(self):
        gate = GravityPort(mass=1.0, threshold=0.5)
        self.assertEqual(gate.gate(0.1), 0)
        self.assertGreater(gate.gate(1.0), 0)

    def test_tuplespace_app_runs(self):
        r = UltraNetwork().boot()
        self.assertIn("ultranetwork online", r["tuplespace"]["output"])
        self.assertEqual(r["xor"]["accuracy"], 1.0)


class TestAndroidInstaller(unittest.TestCase):
    def test_install_and_launch(self):
        inst = Android12Installer()
        m = AndroidManifest("com.x.app", "App", target_sdk=31,
                            permissions=["android.permission.CAMERA"])
        inst.install(m)
        self.assertIn("com.x.app", inst.registry)
        self.assertIn("App", inst.launch("com.x.app"))

    def test_reject_future_sdk(self):
        inst = Android12Installer()
        with self.assertRaises(InstallError):
            inst.install(AndroidManifest("com.x.y", "Y", target_sdk=34))


class TestKernel(unittest.TestCase):
    def test_boot_corrects_kernel_register(self):
        k = QuantumKernel()
        rep = k.boot("X", 2)
        self.assertTrue(rep["ok"])

    def test_run_bada_app(self):
        k = QuantumKernel()
        proc = k.run_app("hello", 'say "hi"\nprint 21 * 2')
        self.assertEqual(proc.state, "exited")
        self.assertEqual(proc.output, ["hi", "42"])


class TestFullBoot(unittest.TestCase):
    def test_boot_and_render(self):
        os_ = BadaWebOS()
        r = os_.boot()
        self.assertTrue(r["qec"]["ok"])
        self.assertEqual(r["objects"], ["article"])
        self.assertEqual(r["android"], ["com.bada.notes"])
        self.assertEqual(r["ultranetwork"]["xor"]["accuracy"], 1.0)
        self.assertTrue(r["quantum_crypto"]["activated"])
        self.assertTrue(r["al"]["online"])
        self.assertEqual(len(r["windows"]), 8)
        with tempfile.TemporaryDirectory() as d:
            p = os_.save_html(os.path.join(d, "desktop.html"))
            with open(p) as fh:
                html = fh.read()
        self.assertIn("BadaWebOS", html)
        self.assertIn("w9wm", html)
        self.assertIn("Shor-9 QEC", html)


if __name__ == "__main__":
    unittest.main()
