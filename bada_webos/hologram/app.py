"""HologramApp — project the equation-group videos onto a Hologram Display.

Reuses the equation-group surfaces (eqvideo / transport / slideshow, all
computed in Bada) as the source video, and the hologram light field
(apps/hologram/lib/hologram.bada) as the reflective modulation, then composes
the four-mirror reflection pyramid from the "Hologram Display" report.
"""

from __future__ import annotations

from . import bridge
from .render import html_hologram
from .floatup import html_floatup
from .keyboard import html_keyboard
from .mirror import html_mirror
from .spatial import html_vision
from .glass import html_glass
from .freeform import html_freeform
from .qcache import html_qcache
from .qevolve import html_qevolve
from .jcrypto import html_jcrypto

TABLET_AREA_CM2 = 200.0   # ~10" tablet panel
BATTERY_WH = 40.0         # tablet battery
DEFAULT_BUDGET_W = 5.0    # power budget for the float-up display
GAP_CM = 12.0             # tablet ↔ phone-mirror gap
VMAX = 0.9                # max v/c on the relativity slider


def _grid_mean(g):
    return sum(v for row in g for v in row) / (len(g) * len(g[0]))


class HologramApp:
    def __init__(self, n: int = 14, frames: int = 16, names: list = None):
        self.n = n
        self.frames = frames
        self.names = names

    def boot(self) -> dict:
        from eqvideo import bridge as ev
        from transport import bridge as tr
        from slideshow import bridge as rp
        from eqvideo.render import CATALOG as EV_CAT
        from transport.app import CATALOG as TR_CAT
        from slideshow.app import REPORT_CATALOG as RP_CAT

        ev_names, tr_names, rp_names = ev.names(), tr.names(), rp.names()
        catalog = {**EV_CAT, **TR_CAT, **RP_CAT}
        order = ev_names + tr_names + rp_names
        use = self.names or order

        fb = {}
        for nm in use:
            b = (ev if nm in ev_names else tr if nm in tr_names else rp)
            fb[nm] = b.frames(nm, self.n, self.frames)
        self.frames_by_name = fb
        self.catalog = {nm: catalog[nm] for nm in use}

        # the hologram light field + reflection geometry, from Bada
        self.light_frames = bridge.light_frames("mag", self.n, self.frames)
        self.quads = [{"name": q, "rot": bridge.quad_rot(q)}
                      for q in bridge.quad_names()]

        self.report = {
            "sources": use, "n_sources": len(use),
            "mirrors": [q["name"] for q in self.quads],
            "light": "beta(p,q) complex amplitude (re/im surfaces)",
        }
        return self.report

    def html(self, free: bool = False) -> str:
        return html_hologram(self.frames_by_name, self.light_frames, self.n,
                             self.catalog, self.quads, free)

    def save_html(self, path: str, free: bool = False) -> str:
        with open(path, "w") as f:
            f.write(self.html(free))
        return path

    # --- float-up display: Jones relief + conductive-plastic power ----------
    def _float_data(self):
        """Jones relief frames + per-frame tablet power (all from Bada)."""
        if not hasattr(self, "relief_frames"):
            self.relief_frames = bridge.relief_frames(self.n, self.frames)
            self.jones_poly = bridge.jones_polynomial()
            self.mean_relief, self.power = [], []
            for k in range(self.frames):
                mb = _grid_mean(self.light_frames[k]) / 0.5      # 0..1
                me = _grid_mean(self.relief_frames[k])           # 0..1
                self.mean_relief.append(me)
                self.power.append(
                    bridge.tablet_power(mb, me, TABLET_AREA_CM2))

    def html_float(self, budget: float = DEFAULT_BUDGET_W) -> str:
        self._float_data()
        return html_floatup(self.frames_by_name, self.light_frames,
                            self.relief_frames, self.n, self.catalog,
                            self.jones_poly, self.power, self.mean_relief,
                            budget, BATTERY_WH)

    def save_floatup(self, path: str, budget: float = DEFAULT_BUDGET_W) -> str:
        with open(path, "w") as f:
            f.write(self.html_float(budget))
        return path


class HoloKeyboardApp:
    """The Happy Hacking Keyboard floating as a hologram (layout from Bada)."""

    KBD_AREA_CM2 = 120.0   # ~60% keyboard footprint

    def boot(self) -> dict:
        self.keys = bridge.hhkb_keys()
        self.width = bridge.hhkb_width()
        self.rows = bridge.hhkb_rows()
        self.jones = bridge.jones_polynomial()
        # power to light the floating keycaps out of the conductive plastic
        self.power = bridge.tablet_power(0.5, 0.5, self.KBD_AREA_CM2)
        return {"keys": len(self.keys), "width": self.width,
                "rows": self.rows, "power": self.power}

    def _poly_str(self) -> str:
        parts = []
        for e, c in self.jones:
            parts.append(f"{'+' if c >= 0 else '-'} {abs(c)}t^{e}")
        s = " ".join(parts)
        return s[2:] if s.startswith("+ ") else s

    def html(self) -> str:
        return html_keyboard(self.keys, self.width, self.rows,
                             self.power, self._poly_str())

    def save_html(self, path: str) -> str:
        with open(path, "w") as f:
            f.write(self.html())
        return path


class MirrorApp:
    """The smartphone mirror over the tablet: an eyeglass-lens aerial image
    forms in the gap (focal point from the special-relativity Jones polynomial),
    realizing the holographic display and the HHKB keyboard."""

    def __init__(self, n: int = 14, frames: int = 16, display: str = "fermat",
                 nv: int = 10):
        self.n = n
        self.frames = frames
        self.display = display
        self.nv = nv

    def boot(self) -> dict:
        from eqvideo import bridge as ev
        from eqvideo.render import CATALOG as EV_CAT
        from transport import bridge as tr
        from transport.app import CATALOG as TR_CAT

        # source video for the realized display (computed in Bada)
        if self.display in ev.names():
            self.display_frames = ev.frames(self.display, self.n, self.frames)
        else:
            self.display_frames = tr.frames(self.display, self.n, self.frames)
        self.light_frames = bridge.light_frames("mag", self.n, self.frames)

        # the HHKB keyboard layout (computed in Bada)
        self.keys = bridge.hhkb_keys()
        self.kbd_width = bridge.hhkb_width()

        # the eyeglass-lens focal height across velocity (rows) and phase (cols)
        self.focus_table = [
            bridge.focus_frames(GAP_CM, (i / self.nv) * VMAX, 1.0, self.frames)
            for i in range(self.nv + 1)]
        self.jones_poly = bridge.jones_polynomial()

        z_rest = self.focus_table[0][0]
        z_fast = self.focus_table[-1][0]
        return {"gap_cm": GAP_CM, "display": self.display,
                "focus_rest_cm": round(z_rest, 2),
                "focus_fast_cm": round(z_fast, 2),
                "vmax": VMAX, "keys": len(self.keys)}

    def html(self, keyboard: bool = False) -> str:
        return html_mirror(self.display, self.display_frames,
                           self.light_frames, self.n, self.keys,
                           self.kbd_width, self.focus_table, GAP_CM, VMAX,
                           self.jones_poly, keyboard)

    def save_html(self, path: str, keyboard: bool = False) -> str:
        with open(path, "w") as f:
            f.write(self.html(keyboard))
        return path


class VisionApp:
    """Vision-Pro-equivalent: launch the display and the tablet turns
    transparent (passthrough) while its apps float out as spatial windows,
    anchored at the mirror-state lens focus (all geometry computed in Bada)."""

    # the tablet's applications that float out as spatial windows
    APPS = [
        {"title": "Hologram", "kind": "display", "glyph": "🔮"},
        {"title": "Terminal", "kind": "card", "glyph": "▶_"},
        {"title": "Slideshow", "kind": "card", "glyph": "▦"},
        {"title": "Kaleido", "kind": "card", "glyph": "✲"},
        {"title": "Files", "kind": "card", "glyph": "🗀"},
    ]
    RADIUS = 10.0
    SPREAD = 2.0944          # ±60° concave shell
    DISPLAY = "fermat"

    def __init__(self, n: int = 14, frames: int = 16):
        self.n = n
        self.frames = frames

    def boot(self) -> dict:
        from eqvideo import bridge as ev

        self.display_frames = ev.frames(self.DISPLAY, self.n, self.frames)
        self.light_frames = bridge.light_frames("mag", self.n, self.frames)
        self.keys = bridge.hhkb_keys()
        self.kbd_width = bridge.hhkb_width()

        # spatial window layout + tablet passthrough + focal anchor (all Bada)
        self.positions = bridge.window_positions(len(self.APPS),
                                                 self.RADIUS, self.SPREAD)
        self.focus_cm = bridge.focus_z(GAP_CM, 0.3, 1.0, 0.0)
        self.passthrough = bridge.passthrough_alpha(1.0)
        return {"windows": len(self.APPS), "focus_cm": round(self.focus_cm, 2),
                "passthrough_alpha": round(self.passthrough, 2),
                "gap_cm": GAP_CM, "keys": len(self.keys)}

    def html(self) -> str:
        return html_vision(self.APPS, self.positions, self.display_frames,
                          self.light_frames, self.n, self.keys, self.kbd_width,
                          self.focus_cm, GAP_CM)

    def save_html(self, path: str) -> str:
        with open(path, "w") as f:
            f.write(self.html())
        return path


class GlassApp:
    """Fully transparent holographic display + Japanese HHKB over a camera
    passthrough: no video, everything see-through to the world behind the
    tablet.  Romaji->kana from the Bada conversion table."""

    def boot(self) -> dict:
        self.keys = bridge.hhkb_keys()
        self.kbd_width = bridge.hhkb_width()
        self.kana = bridge.kana_table()
        return {"keys": len(self.keys), "kana_entries": len(self.kana),
                "input": "romaji->kana (hiragana/katakana)",
                "background": "camera passthrough (see-through)"}

    def html(self) -> str:
        return html_glass(self.keys, self.kbd_width, self.kana)

    def save_html(self, path: str) -> str:
        with open(path, "w") as f:
            f.write(self.html())
        return path


class FreeformApp:
    """A Samsung-Freeform-style multi-window desktop: the tablet's apps open in
    draggable/resizable freeform windows with close/minimize/maximize buttons
    and a Play-Store-style taskbar (Start button + tasks + clock).  The window
    geometry and app catalog come from Bada (apps/hologram/lib/freeform.bada)."""

    def boot(self) -> dict:
        self.catalog = bridge.wm_catalog()
        self.tb = bridge.tb_height()
        self.sections = bridge.start_sections()
        self.sizes = bridge.size_presets()
        return {"apps": len(self.catalog), "taskbar_h": self.tb,
                "sections": self.sections,
                "sizes": [s["label"] for s in self.sizes],
                "features": "freeform windows · close/min/max · split-snap · "
                            "size presets (携帯型/中/大) · Start button "
                            "(installed + Bada apps) · taskbar"}

    def html(self) -> str:
        return html_freeform(self.catalog, self.tb, self.sections, self.sizes)

    def save_html(self, path: str) -> str:
        with open(path, "w") as f:
            f.write(self.html())
        return path


class QCacheApp:
    """The Quantum Cache Disk: the hard disk's bit patterns become a quantum
    state, the Reviser rewrites von-Neumann cache ops to quantum gates, a Grover
    a-priori engine predicts the DNA-telomere thought pattern, with the Jones
    thermal network, the Gamma integration-by-parts manifold and the
    semiconductor uncertainty bound — all computed in Bada."""

    NBITS = 4
    NQ = 4                              # 2^4 = 16 blocks
    L0 = 20                             # initial telomere length
    STEPS = 8                           # telomere division steps
    HBAR = 1.054571817e-34
    PATTERNS = [3, 12, 7, 1, 15, 9, 6, 10, 5, 0, 14, 11, 8, 2, 13, 4]
    OPS = ["READ", "WRITE", "FETCH", "SEARCH", "EVICT"]

    def boot(self) -> dict:
        self.amps = bridge.disk_state(self.PATTERNS, self.NBITS)
        self.reviser = bridge.revise_program(self.OPS)
        self.predicted = bridge.predict_blocks(self.NQ, self.L0, self.STEPS)
        self.curve = bridge.predict_curve(self.NQ, self.L0, self.STEPS)
        self.thermal = [[round(b, 2), bridge.jones_thermal(b)]
                        for b in [i * 0.4 for i in range(8)]]
        self.gamma = [[z, bridge.gamma_int(z), bridge.gamma_ibp(z)]
                      for z in range(1, 8)]
        self.bound = bridge.uncertainty_bound(0.5, self.HBAR)
        return {
            "blocks": len(self.PATTERNS), "qubits": self.NQ,
            "reviser": self.reviser,
            "predicted_first": self.predicted[0],
            "hit_prob": round(self.curve[0], 4),
            "gamma_ibp_ok": self.gamma[4][1] * 5 == self.gamma[5][1],
        }

    def data(self) -> dict:
        if not hasattr(self, "amps"):
            self.boot()
        return {
            "nbits": self.NBITS, "patterns": self.PATTERNS, "amps": self.amps,
            "reviser": [list(r) for r in self.reviser],
            "predicted": self.predicted, "curve": self.curve,
            "teloMax": self.L0, "thermal": self.thermal, "gamma": self.gamma,
            "unc": {"d_addr": 0.5, "hbar": self.HBAR, "bound": self.bound},
        }

    def html(self) -> str:
        return html_qcache(self.data())

    def save_html(self, path: str) -> str:
        with open(path, "w") as f:
            f.write(self.html())
        return path


class QEvolveApp:
    """Self-evolving quantum-algorithm source-code prototype: a genetic
    algorithm (in Bada) evolves a real-amplitude quantum program toward Grover
    amplification, then writes the evolved algorithm back out as Bada source
    code — self-validated by re-running the emitted source."""

    NQ = 4
    MARKED = 10
    L = 8                   # gene length (gate slots)
    POP = 16
    GENS = 18
    SEED = 5

    def boot(self) -> dict:
        self.prog = bridge.evolve_best(self.NQ, self.MARKED, self.L,
                                       self.POP, self.GENS, self.SEED)
        self.curve = bridge.evolve_curve(self.NQ, self.MARKED, self.L,
                                         self.POP, self.GENS, self.SEED)
        self.fitness = bridge.fitness(self.NQ, self.MARKED, self.prog)
        self.source = bridge.emit_source(self.NQ, self.MARKED, self.prog)
        self.verified = bridge.verify_emitted(self.NQ, self.MARKED, self.prog)
        return {
            "gene": self.prog,
            "gates": [bridge.GATE_NAMES[g] for g in self.prog],
            "start": round(self.curve[0], 4),
            "final": round(self.curve[-1], 4),
            "fitness": round(self.fitness, 4),
            "verified": round(self.verified, 4),
            "evolved": self.curve[-1] > self.curve[0],
            "source_ok": abs(self.verified - self.fitness) < 1e-9,
        }

    def data(self) -> dict:
        if not hasattr(self, "prog"):
            self.boot()
        return {"nq": self.NQ, "marked": self.MARKED, "prog": self.prog,
                "curve": self.curve, "fitness": self.fitness,
                "verified": self.verified, "source": self.source}

    def html(self) -> str:
        return html_qevolve(self.data())

    def save_html(self, path: str) -> str:
        with open(path, "w") as f:
            f.write(self.html())
        return path


class JCryptoApp:
    """Quantum cryptography solved by the Jones polynomial: encryption f(s),
    Jones π(χ,x), the cipher solved by f(s)/π(χ,x)−f(s), decryptable only under
    the necessary condition (matching Jones key), with the plaintext pulled from
    Omega::DATABASE — all computed in Bada."""

    CHI = [1, 1, 1]         # trefoil braid (sigma_1^3)
    N = 2                   # strands
    X = 0.5                 # Jones evaluation point (the key)
    WX = 0.7                # a wrong key (different evaluation point)
    PLAINTEXT = "BADA QC!"

    def boot(self) -> dict:
        self.msg = [ord(c) for c in self.PLAINTEXT]
        key = (self.CHI, self.N, self.X)
        wrong = (self.CHI, self.N, self.WX)
        self.pi = bridge.jones_pi(*key)
        self.cipher = bridge.encrypt_msg(self.msg, *key)
        self.solved = bridge.solve_msg(self.cipher, *key)
        self.wrong = bridge.solve_msg(self.cipher, *wrong)
        self.nc_ok = bridge.necessary_condition(*key, *key)
        self.nc_bad = bridge.necessary_condition(*key, *wrong)
        self.pull_ok = bridge.pull_decrypt(self.msg, *key, *key)
        self.pull_bad = bridge.pull_decrypt(self.msg, *key, *wrong)
        return {
            "plaintext": self.PLAINTEXT, "pi": round(self.pi, 4),
            "recovered": "".join(chr(round(v)) for v in self.solved),
            "necessary_ok": self.nc_ok, "necessary_bad": self.nc_bad,
            "pulled": self.pull_ok, "pulled_wrong": self.pull_bad,
            "solved_ok": [round(v) for v in self.solved] == self.msg,
        }

    def data(self) -> dict:
        if not hasattr(self, "msg"):
            self.boot()
        return {"chi": self.CHI, "x": self.X, "wx": self.WX, "pi": self.pi,
                "msg": self.msg, "cipher": self.cipher, "solved": self.solved,
                "wrong": self.wrong, "nc_ok": self.nc_ok, "nc_bad": self.nc_bad,
                "pull_ok": self.pull_ok, "pull_bad": self.pull_bad}

    def html(self) -> str:
        return html_jcrypto(self.data())

    def save_html(self, path: str) -> str:
        with open(path, "w") as f:
            f.write(self.html())
        return path
