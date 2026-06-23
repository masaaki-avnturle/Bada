"""Hologram Display: project the equation-group videos onto a four-mirror
reflection pyramid, modulated by the Bada beta(p,q) light field."""

import math
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

from hologram import (HologramApp, HoloKeyboardApp, MirrorApp, VisionApp,
                      GlassApp, FreeformApp, QCacheApp, QEvolveApp, JCryptoApp,
                      html_hologram, html_keyboard)
from hologram import bridge
from hologram.keyboard import code_label


class TestHologramBada(unittest.TestCase):
    """The light field + geometry come out of the Bada library."""

    def test_quads(self):
        self.assertEqual(bridge.quad_names(),
                         ["before", "after", "left", "right"])
        self.assertEqual(bridge.quad_rot("before"), 0)
        self.assertEqual(bridge.quad_rot("after"), 180)
        self.assertEqual(bridge.quad_rot("right"), 90)
        self.assertEqual(bridge.quad_rot("left"), 270)

    def test_light_field_grid(self):
        g = bridge.light_grid("mag", 6, 0.0)
        self.assertEqual(len(g), 6)
        self.assertEqual(len(g[0]), 6)
        # magnitude is a non-negative amplitude bounded by the light_pos peak
        flat = [v for row in g for v in row]
        self.assertTrue(all(0.0 <= v <= 0.51 for v in flat))
        self.assertTrue(max(flat) > 0.1)

    def test_complex_amplitude_consistent(self):
        # |A| == hypot(re, im) at a sample point, both from Bada
        re = bridge.light_grid("re", 5, 0.3)[2][3]
        im = bridge.light_grid("im", 5, 0.3)[2][3]
        mag = bridge.light_grid("mag", 5, 0.3)[2][3]
        self.assertAlmostEqual(mag, math.hypot(re, im), places=6)

    def test_metric_and_mass(self):
        # v/sqrt(1+(v/c)^2) and 8 pi G (p/c^3 + V/S)
        self.assertAlmostEqual(bridge.metric_ds2(3.0, 5.0),
                               3.0 / math.sqrt(1 + (3.0 / 5.0) ** 2), places=6)
        self.assertGreater(bridge.hologram_mass(1.0, 3e8, 1.0, 1.0), 0.0)


class TestHologramApp(unittest.TestCase):
    def test_boot_projects_sources(self):
        app = HologramApp(n=8, frames=4, names=["fermat", "critline"])
        r = app.boot()
        self.assertEqual(r["n_sources"], 2)
        self.assertEqual(r["mirrors"], ["before", "after", "left", "right"])
        self.assertEqual(len(app.light_frames), 4)

    def test_html_pyramid_and_free(self):
        app = HologramApp(n=8, frames=4, names=["fermat", "abelian"])
        app.boot()
        with tempfile.TemporaryDirectory() as d:
            pyr = open(app.save_html(os.path.join(d, "p.html"), False)).read()
            free = open(app.save_html(os.path.join(d, "f.html"), True)).read()
        self.assertIn("FREE=false", pyr)
        self.assertIn("FREE=true", free)
        for h in (pyr, free):
            self.assertIn("HOLOGRAM DISPLAY", h)
            self.assertIn("putImageData", h)         # surface * light render
            for mirror in ("before", "after", "left", "right"):
                self.assertIn(mirror, h)
            self.assertIn("Fermat", h)               # an equation-group title

    def test_render_direct(self):
        frames = {"x": [[[0.0, 1.0], [1.0, 0.0]]]}
        light = [[[0.4, 0.4], [0.4, 0.4]]]
        cat = {"x": ("Holo X", "desc")}
        quads = [{"name": "before", "rot": 0}, {"name": "after", "rot": 180},
                 {"name": "left", "rot": 270}, {"name": "right", "rot": 90}]
        html = html_hologram(frames, light, 2, cat, quads, free=True)
        self.assertIn("Holo X", html)
        self.assertIn("FREE=true", html)


class TestJonesReliefAndPower(unittest.TestCase):
    """The light mounds up via the Jones polynomial; conductive-plastic power."""

    def test_jones_polynomial_is_trefoil(self):
        # V(t) = t + t^3 - t^4 from the Bada Jones-polynomial library
        self.assertEqual(bridge.jones_polynomial(), [[1, 1], [3, 1], [4, -1]])

    def test_relief_grid_normalized(self):
        g = bridge.relief_grid(6, 0.0)
        flat = [v for row in g for v in row]
        self.assertEqual(len(flat), 36)
        self.assertTrue(all(0.0 <= v <= 1.05 for v in flat))   # disk-clamped
        self.assertTrue(max(flat) > 0.3)

    def test_power_model(self):
        half = bridge.tablet_power(0.5, 0.5, 200.0)
        full = bridge.tablet_power(1.0, 1.0, 200.0)
        self.assertAlmostEqual(half, 2.25, places=3)
        self.assertAlmostEqual(full, 6.0, places=3)
        self.assertGreater(full, half)               # more light/relief = more W
        # power budget dims the panel; battery time grows as power falls
        self.assertAlmostEqual(bridge.power_scale(6.0, 3.0), 0.5, places=6)
        self.assertEqual(bridge.power_scale(2.0, 3.0), 1.0)
        self.assertGreater(bridge.battery_minutes(2.0, 40.0),
                           bridge.battery_minutes(4.0, 40.0))

    def test_floatup_html(self):
        app = HologramApp(n=8, frames=4, names=["fermat", "abelian"])
        app.boot()
        with tempfile.TemporaryDirectory() as d:
            h = open(app.save_floatup(os.path.join(d, "f.html"))).read()
        self.assertIn("FLOAT-UP HOLOGRAM", h)
        self.assertIn("Jones V(t)=", h)
        self.assertIn("RELIEF=", h)                  # Jones relief data
        self.assertIn("POWER=", h)                   # per-frame tablet power
        self.assertIn("budget", h)
        self.assertEqual(len(app.power), 4)
        self.assertTrue(all(p > 0 for p in app.power))


class TestHoloKeyboard(unittest.TestCase):
    """The Happy Hacking Keyboard layout in Bada, floating as a hologram."""

    def test_layout_from_bada(self):
        keys = bridge.hhkb_keys()
        self.assertEqual(len(keys), 60)              # HHKB = 60 keys
        self.assertEqual(bridge.hhkb_width(), 15)    # 15U wide (60%)
        self.assertEqual(bridge.hhkb_rows(), 5)
        # rows 0..3 tile to a full 15U
        right = {}
        for x, y, w, c in keys:
            right[y] = max(right.get(y, 0), x + w)
        for y in (0, 1, 2, 3):
            self.assertAlmostEqual(right[y], 15.0, places=3)

    def test_control_left_of_a(self):
        # the signature HHKB trait: Control where Caps Lock sits (left of A)
        keys = bridge.hhkb_keys()
        row2 = sorted((x, int(c)) for x, y, w, c in keys if y == 2)
        self.assertEqual(row2[0][1], 258)            # Ctrl
        self.assertEqual(row2[1][1], 65)             # 'A'

    def test_code_labels(self):
        self.assertEqual(code_label(65), "A")
        self.assertEqual(code_label(258), "ctrl")
        self.assertEqual(code_label(260), "⏎")
        self.assertEqual(code_label(263), "◇")

    def test_keyboard_html(self):
        app = HoloKeyboardApp()
        r = app.boot()
        self.assertEqual(r["keys"], 60)
        self.assertGreater(r["power"], 0)
        with tempfile.TemporaryDirectory() as d:
            h = open(app.save_html(os.path.join(d, "k.html"))).read()
        self.assertIn("HAPPY HACKING KEYBOARD", h)
        self.assertIn("HHKB Professional", h)
        for glyph in ("ctrl", "shift", "esc", "fn"):
            self.assertIn(glyph, h)
        self.assertIn("Jones V(t)=", h)

    def test_render_direct(self):
        keys = [[0, 0, 1.0, 65], [1, 0, 1.5, 258]]
        h = html_keyboard(keys, 15, 5, 1.35, "t + t^3 - t^4")
        self.assertIn('"label": "A"', h)
        self.assertIn('"label": "ctrl"', h)


class TestMirrorAerial(unittest.TestCase):
    """Smartphone mirror + eyeglass lens -> aerial focus from the SR Jones poly."""

    def test_lens_law(self):
        # 1/f = 1/do + 1/di  =>  do=12, f=4 -> di=6
        self.assertAlmostEqual(bridge.lens_image(12.0, 4.0), 6.0, places=4)

    def test_lorentz_factor(self):
        self.assertAlmostEqual(bridge.lorentz(0.0, 1.0), 1.0, places=6)
        self.assertAlmostEqual(bridge.lorentz(0.6, 1.0), 1.25, places=6)
        self.assertGreater(bridge.lorentz(0.9, 1.0), bridge.lorentz(0.6, 1.0))

    def test_focus_in_gap_and_shifts_with_velocity(self):
        d = 12.0
        z_rest = bridge.focus_z(d, 0.0, 1.0, 0.0)
        z_fast = bridge.focus_z(d, 0.9, 1.0, 0.0)
        # the aerial focus stays strictly inside the tablet↔mirror gap
        for z in (z_rest, z_fast):
            self.assertGreater(z, 0.0)
            self.assertLess(z, d)
        # and moves relativistically (different focal height)
        self.assertNotAlmostEqual(z_rest, z_fast, places=2)

    def test_focus_frames_and_mag(self):
        fr = bridge.focus_frames(12.0, 0.3, 1.0, 5)
        self.assertEqual(len(fr), 5)
        self.assertTrue(all(0.0 < z < 12.0 for z in fr))
        self.assertGreater(bridge.focus_mag(12.0, 0.3, 1.0, 0.0), 0.0)

    def test_app_boot_and_html(self):
        app = MirrorApp(n=8, frames=4, display="fermat", nv=5)
        r = app.boot()
        self.assertEqual(r["gap_cm"], 12.0)
        self.assertEqual(r["keys"], 60)
        self.assertNotAlmostEqual(r["focus_rest_cm"], r["focus_fast_cm"],
                                  places=2)
        self.assertEqual(len(app.focus_table), 6)         # nv + 1 rows
        with tempfile.TemporaryDirectory() as d:
            disp = open(app.save_html(os.path.join(d, "m.html"), False)).read()
            kbd = open(app.save_html(os.path.join(d, "k.html"), True)).read()
        self.assertIn("KB=false", disp)
        self.assertIn("KB=true", kbd)
        for h in (disp, kbd):
            self.assertIn("MIRROR APP", h)
            self.assertIn("SMARTPHONE", h)               # phone mirror
            self.assertIn("aerial focus", h)             # the floating image
            self.assertIn("special-relativity Jones", h)
            self.assertIn("FOCUS=", h)                   # Bada focal table


class TestSpatialVision(unittest.TestCase):
    """Vision-Pro-equivalent passthrough: tablet transparent, apps float out."""

    def test_window_arc_is_concave_shell(self):
        pos = bridge.window_positions(5, 10.0, 2.0944)
        self.assertEqual(len(pos), 5)
        zs = [p[2] for p in pos]
        # centre window is deepest, edges wrap toward the viewer
        self.assertGreater(zs[2], zs[0])
        self.assertGreater(zs[2], zs[4])
        self.assertAlmostEqual(zs[0], zs[4], places=3)   # symmetric

    def test_passthrough_and_depth(self):
        # launching makes the tablet transparent
        self.assertAlmostEqual(bridge.passthrough_alpha(0.0), 1.0, places=6)
        self.assertLess(bridge.passthrough_alpha(1.0), 0.2)
        # nearer windows are larger and parallax more
        self.assertGreater(bridge.depth_scale(5.0, 5.0, 10.0),
                           bridge.depth_scale(10.0, 5.0, 10.0))
        self.assertGreater(abs(bridge.parallax(5.0, 0.5, 10.0)),
                           abs(bridge.parallax(10.0, 0.5, 10.0)))

    def test_app_boot_and_html(self):
        app = VisionApp(n=8, frames=4)
        r = app.boot()
        self.assertEqual(r["windows"], len(VisionApp.APPS))
        self.assertEqual(r["keys"], 60)
        self.assertLess(r["passthrough_alpha"], 0.2)     # transparent on launch
        self.assertGreater(r["focus_cm"], 0.0)
        with tempfile.TemporaryDirectory() as d:
            h = open(app.save_html(os.path.join(d, "v.html"))).read()
        self.assertIn("SPATIAL HOLOGRAM", h)
        self.assertIn("passthrough", h)
        self.assertIn("transparent", h)                  # tablet see-through
        self.assertIn("POS=", h)                         # Bada window layout
        self.assertIn("Hologram", h)                     # the display window
        self.assertIn("Terminal", h)                     # a floated tablet app


class TestTransparentJapanese(unittest.TestCase):
    """Transparent glass display + Japanese (romaji->kana) HHKB, no video."""

    def test_romaji_to_kana(self):
        cases = {
            "konnichiwa": "こんにちわ", "arigatou": "ありがとう",
            "nippon": "にっぽん", "sensei": "せんせい",
            "kya": "きゃ", "matte": "まって", "nihongo": "にほんご",
        }
        for r, expect in cases.items():
            self.assertEqual(bridge.romaji_to_kana(r), expect, r)

    def test_kana_table(self):
        t = bridge.kana_table()
        self.assertGreater(len(t), 100)
        self.assertEqual(t["ka"], "か")
        self.assertEqual(t["shi"], "し")
        self.assertEqual(t["kya"], "きゃ")

    def test_glass_app_html(self):
        app = GlassApp()
        r = app.boot()
        self.assertEqual(r["keys"], 60)
        self.assertGreater(r["kana_entries"], 100)
        with tempfile.TemporaryDirectory() as d:
            h = open(app.save_html(os.path.join(d, "g.html"))).read()
        # transparent (glass) + camera passthrough + no embedded video frames
        self.assertIn("getUserMedia", h)                 # see the world behind
        self.assertIn("透過", h)                          # transparent
        self.assertNotIn("putImageData", h)              # no video heatmap
        # Japanese input wired in, table embedded (unescaped unicode)
        self.assertIn("toHira", h)
        self.assertIn("か", h)
        self.assertIn("きゃ", h)
        self.assertIn("Happy Hacking Keyboard", h)


class TestFreeformWM(unittest.TestCase):
    """Samsung-Freeform-style multi-window manager + taskbar (geometry in Bada)."""

    def test_wm_geometry(self):
        self.assertEqual(bridge.tb_height(), 56)
        # maximize sits above the taskbar
        self.assertEqual(bridge.maximize_rect(1200, 800), [0, 0, 1200, 744])
        # split-snap: left + right halves tile the width
        l = bridge.snap_rect(0, 1200, 800)
        r = bridge.snap_rect(1, 1200, 800)
        self.assertEqual(l, [0, 0, 600, 744])
        self.assertEqual(r, [600, 0, 600, 744])
        self.assertEqual(l[2] + r[2], 1200)
        # cascade offsets successive windows
        c = bridge.cascade(3, 1200, 800)
        self.assertEqual(len(c), 3)
        self.assertLess(c[0][0], c[1][0])
        self.assertLess(c[1][1], c[2][1])
        # clamp keeps an off-screen window reachable
        cl = bridge.clamp_rect(2000, 900, 480, 340, 1200, 800)
        self.assertLessEqual(cl[0], 1200 - 80)

    def test_catalog(self):
        cat = bridge.wm_catalog()
        self.assertGreaterEqual(len(cat), 5)
        files = [a["file"] for a in cat]
        self.assertIn("hologlass.html", files)       # the transparent JP app
        self.assertIn("holovision.html", files)
        self.assertTrue(all(a["title"] and a["glyph"] for a in cat))

    def test_start_sections(self):
        secs = bridge.start_sections()
        self.assertEqual(len(secs), 2)
        self.assertIn("インストール済みアプリ", secs)   # installed device apps

    def test_size_presets(self):
        ps = bridge.size_presets()
        self.assertEqual([p["key"] for p in ps], ["mobile", "medium", "large"])
        self.assertEqual([p["label"] for p in ps], ["携帯型", "中", "大"])
        mob = bridge.window_size("mobile", 1200, 800)
        med = bridge.window_size("medium", 1200, 800)
        lar = bridge.window_size("large", 1200, 800)
        self.assertLess(mob[0], mob[1])              # 携帯型: tall & narrow
        self.assertGreater(lar[0], med[0])           # 大 > 中 (width)
        self.assertGreater(lar[1], med[1])           # 大 > 中 (height)
        self.assertLessEqual(lar[1], 800 - 56)       # fits above the taskbar

    def test_freeform_html(self):
        app = FreeformApp()
        r = app.boot()
        self.assertEqual(r["apps"], len(bridge.wm_catalog()))
        with tempfile.TemporaryDirectory() as d:
            h = open(app.save_html(os.path.join(d, "f.html"))).read()
        self.assertIn("Bada Freeform", h)
        self.assertIn('id="start"', h)              # Start button
        self.assertIn('id="taskbar"', h)            # taskbar
        self.assertIn("b cls", h)                   # window close button
        self.assertIn("function snap", h)           # split-snap
        self.assertIn("<iframe src=", h)            # windows host the real apps
        self.assertIn("hologlass.html", h)
        # the Start menu lists the device's installed apps via the native bridge
        self.assertIn("AndroidApps", h)
        self.assertIn("listApps", h)
        self.assertIn("launchApp", h)
        self.assertIn("インストール済みアプリ", h)
        # launch-size selector (携帯型 / 中 / 大)
        self.assertIn("sizeFor", h)
        self.assertIn("launchSize", h)
        self.assertIn("携帯型", h)


class TestQuantumCacheDisk(unittest.TestCase):
    """Hard disk -> quantum cache: Reviser, Grover prediction, Γ-IBP, Jones."""

    def test_gamma_integration_by_parts(self):
        # the IBP identity Gamma(z+1) = z*Gamma(z), computed in Bada
        for z in range(1, 8):
            self.assertEqual(bridge.gamma_ibp(z), bridge.gamma_int(z + 1))

    def test_disk_state_is_normalized(self):
        amps = bridge.disk_state([3, 7, 1, 15], 4)
        self.assertAlmostEqual(sum(a * a for a in amps), 1.0, places=6)

    def test_reviser_von_neumann_to_quantum(self):
        rev = dict(bridge.revise_program(
            ["READ", "WRITE", "FETCH", "EVICT", "SEARCH"]))
        self.assertEqual(rev["READ"], "MEASURE")
        self.assertEqual(rev["FETCH"], "HADAMARD")
        self.assertEqual(rev["SEARCH"], "GROVER")

    def test_grover_prediction_amplifies(self):
        # the a-priori engine amplifies the telomere thought pattern well past
        # the uniform 1/N probability
        p = bridge.predict_curve(4, 20, 4)
        self.assertTrue(all(x > 0.5 for x in p))     # >> 1/16
        blocks = bridge.predict_blocks(4, 20, 4)
        self.assertEqual(len(blocks), 4)
        self.assertTrue(all(0 <= b < 16 for b in blocks))

    def test_uncertainty_bound(self):
        # Delta(addr)*Delta(data) >= hbar/2 ; at d_addr=0.5 the bound is hbar
        hbar = 1.054571817e-34
        self.assertAlmostEqual(bridge.uncertainty_bound(0.5, hbar) / hbar,
                               1.0, places=3)

    def test_app_html(self):
        app = QCacheApp()
        r = app.boot()
        self.assertEqual(r["blocks"], 16)
        self.assertTrue(r["gamma_ibp_ok"])
        self.assertGreater(r["hit_prob"], 0.5)
        with tempfile.TemporaryDirectory() as d:
            h = open(app.save_html(os.path.join(d, "q.html"))).read()
        self.assertIn("QUANTUM CACHE DISK", h)
        self.assertIn("HADAMARD", h)                 # Reviser output
        self.assertIn("GROVER", h)
        self.assertIn("大域的部分積分", h)           # Gamma IBP manifold
        self.assertIn("不確定性原理", h)             # uncertainty principle

    def test_in_freeform_catalog(self):
        files = [a["file"] for a in bridge.wm_catalog()]
        self.assertIn("qcache.html", files)          # opens in a freeform window


class TestSelfEvolvingQuantum(unittest.TestCase):
    """A GA evolves a quantum algorithm and emits it as Bada source (qevolve)."""

    def test_gates_grover(self):
        # the hand-built Grover gene amplifies; identity-only stays at 1/N
        amp = bridge.fitness(4, 10, [1, 2, 1, 2, 1, 2])
        self.assertGreater(amp, 0.9)
        self.assertAlmostEqual(bridge.fitness(4, 10, [0, 0, 0, 0, 0, 0]),
                               1.0 / 16, places=6)

    def test_evolution_improves(self):
        curve = bridge.evolve_curve(4, 10, 8, 16, 18, 5)
        # best-so-far is non-decreasing and strictly rises (self-evolution)
        for i in range(len(curve) - 1):
            self.assertGreaterEqual(curve[i + 1], curve[i])
        self.assertGreater(curve[-1], curve[0])
        self.assertGreater(curve[-1], 0.5)           # well past uniform 1/16

    def test_emitted_source_self_validates(self):
        prog = bridge.evolve_best(4, 10, 8, 16, 18, 5)
        src = bridge.emit_source(4, 10, prog)
        self.assertIn("def evolved_amp()", src)      # it is Bada source code
        self.assertIn("apply_oracle", src)
        # re-running the emitted source reproduces the evolved fitness
        self.assertAlmostEqual(bridge.verify_emitted(4, 10, prog),
                               bridge.fitness(4, 10, prog), places=9)

    def test_app_html(self):
        app = QEvolveApp()
        r = app.boot()
        self.assertTrue(r["evolved"])
        self.assertTrue(r["source_ok"])
        with tempfile.TemporaryDirectory() as d:
            h = open(app.save_html(os.path.join(d, "qe.html"))).read()
        self.assertIn("SELF-EVOLVING QUANTUM ALGORITHM", h)
        self.assertIn("evolved_amp", h)              # the emitted source
        self.assertIn("自己検証", h)                 # self-validation
        files = [a["file"] for a in bridge.wm_catalog()]
        self.assertIn("qevolve.html", files)


class TestQuantumCryptoJones(unittest.TestCase):
    """Cipher f(s) solved by f(s)/π(χ,x)−f(s); pull + necessary condition."""

    KEY = ([1, 1, 1], 2, 0.5)
    WRONG = ([1, 1, 1], 2, 0.7)

    def test_solver_inverts_with_correct_key(self):
        # f(s)/π−f(s) exactly recovers the plaintext m under the right key
        msg = [72, 73, 33]
        cipher = bridge.encrypt_msg(msg, *self.KEY)
        solved = [round(v) for v in bridge.solve_msg(cipher, *self.KEY)]
        self.assertEqual(solved, msg)

    def test_wrong_key_does_not_break(self):
        msg = [72, 73, 33]
        cipher = bridge.encrypt_msg(msg, *self.KEY)
        wrong = [round(v) for v in bridge.solve_msg(cipher, *self.WRONG)]
        self.assertNotEqual(wrong, msg)              # cipher not broken

    def test_necessary_condition(self):
        self.assertTrue(bridge.necessary_condition(*self.KEY, *self.KEY))
        self.assertFalse(bridge.necessary_condition(*self.KEY, *self.WRONG))

    def test_pull_from_tuplespace(self):
        msg = [66, 65, 68, 65]                       # "BADA"
        # correct key -> plaintext pulled from Omega::DATABASE
        self.assertEqual(bridge.pull_decrypt(msg, *self.KEY, *self.KEY), msg)
        # wrong key -> necessary condition fails -> nothing pulled
        self.assertEqual(bridge.pull_decrypt(msg, *self.KEY, *self.WRONG), [])

    def test_app_html(self):
        app = JCryptoApp()
        r = app.boot()
        self.assertTrue(r["solved_ok"])
        self.assertEqual(r["recovered"], app.PLAINTEXT)
        self.assertTrue(r["necessary_ok"])
        self.assertFalse(r["necessary_bad"])
        self.assertEqual(r["pulled_wrong"], [])
        with tempfile.TemporaryDirectory() as d:
            h = open(app.save_html(os.path.join(d, "jc.html"))).read()
        self.assertIn("QUANTUM CRYPTO", h)
        self.assertIn("f(s)/π(χ,x)", h)              # the solver formula
        self.assertIn("Omega::DATABASE", h)          # pull
        self.assertIn("必要条件", h)                 # necessary condition
        files = [a["file"] for a in bridge.wm_catalog()]
        self.assertIn("jcrypto.html", files)


if __name__ == "__main__":
    unittest.main()
