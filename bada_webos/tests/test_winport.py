"""WinPort: Rails-in-Bada, Win10/11 reviser, symlink/hardlink control panel,
quantum porting, and the VM bridge + repeater."""

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

from winport import WinPortApp, WindowsReviser, VMBridge
from winport import control_panel
from winport.quantum_port import WIN10_FEATURES, port_all
from winport.rails_bada import generate_rails


class TestRailsInBada(unittest.TestCase):
    def test_generates_functioning_rails(self):
        code = generate_rails("Article", ["title", "body"])
        self.assertIn("class Article < ApplicationRecord", code)
        self.assertIn("class ArticlesController < ApplicationController", code)
        self.assertIn("def index", code)
        self.assertIn("resources :Articles", code)
        self.assertIn("create_table :Articles", code)


class TestWindowsReviser(unittest.TestCase):
    def test_win10_to_win11(self):
        rev = WindowsReviser()
        out = rev.to_win11("Windows10 ControlPanel Cortana DirectX11")
        self.assertEqual(out, "Windows11 Settings Copilot DirectX12")

    def test_win_to_quantum(self):
        rev = WindowsReviser()
        out = rev.to_quantum("CPU thread register cache RAM")
        self.assertEqual(out, "QPU qubit qregister entangled_cache QRAM")

    def test_preserves_unmapped_words(self):
        rev = WindowsReviser()
        self.assertEqual(rev.to_win11("hello world"), "hello world")


class TestControlPanel(unittest.TestCase):
    def test_symlinks_and_hardlinks(self):
        with tempfile.TemporaryDirectory() as d:
            panel = control_panel.build_control_panel(d)
            info = control_panel.inspect(panel)
            self.assertTrue(info["symlinks_ok"])
            self.assertTrue(info["hardlinks_share_inode"])
            self.assertEqual(info["symlinks"], len(control_panel.DEVICES))
            # one symlink really is a symlink resolving to the device file
            any_link = next(iter(panel["symlinks"].values()))
            self.assertTrue(os.path.islink(any_link))
            self.assertTrue(os.path.exists(os.path.realpath(any_link)))
            # shared config inode is shared by all hardlinks + the original
            self.assertEqual(info["shared_link_count"],
                             len(control_panel.DEVICES) + 1)


class TestQuantumPort(unittest.TestCase):
    def test_all_features_ported_and_protected(self):
        ported = port_all()
        self.assertEqual(len(ported), len(WIN10_FEATURES))
        for p in ported:
            self.assertTrue(p["qec_ok"])
            self.assertNotIn("CPU", p["quantum"])      # CPU -> QPU
            self.assertNotIn("Windows10", p["quantum"])  # -> Windows11

    def test_kernel_port_tokens(self):
        kernel = next(p for p in port_all() if p["feature"] == "kernel")
        self.assertIn("QPU", kernel["quantum"])
        self.assertIn("qubit", kernel["quantum"])


class TestVMBridge(unittest.TestCase):
    def test_migrates_to_quantum_node(self):
        b = VMBridge().migrate(4)
        self.assertTrue(b["delivered"])
        self.assertGreater(b["delivered_strength"], 0)
        self.assertIn("quantum", b["reachable"])
        self.assertEqual(b["features_migrated"], 4)

    def test_repeater_boosts_delivery(self):
        weak = VMBridge(repeater_gain=1.0).migrate(4)["delivered_strength"]
        strong = VMBridge(repeater_gain=3.0).migrate(4)["delivered_strength"]
        self.assertGreater(strong, weak)


class TestWinPortApp(unittest.TestCase):
    def test_boot_report(self):
        r = WinPortApp().boot()
        self.assertTrue(r["rails_ok"])
        self.assertGreater(r["win11_changes"], 0)
        self.assertTrue(r["control_panel"]["symlinks_ok"])
        self.assertTrue(r["control_panel"]["hardlinks_share_inode"])
        self.assertTrue(r["qec_ok"])
        self.assertTrue(r["vm_bridge"]["delivered"])

    def test_render_html(self):
        app = WinPortApp()
        app.boot()
        html = app.render_html()
        self.assertIn("WinPort", html)
        self.assertIn("class Article", html)


if __name__ == "__main__":
    unittest.main()
