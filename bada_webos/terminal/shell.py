"""A small bash-like shell for the BadaWebOS terminal.

Implements a useful set of POSIX-ish builtins over the :class:`VFS`, plus
pipelines (``|``) and output redirection (``>`` / ``>>``).  Two commands are
"launchers": ``vim`` and ``emacs`` hand a request back to the Terminal, and
``bada`` runs a Bada program on the VM.
"""

from __future__ import annotations

import io
import os
import shlex
import sys
from contextlib import redirect_stdout

from .vfs import VFS, VFSError

# the Bada VM (application language)
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_WEBOS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # bada_webos/
for _p in (_ROOT, _WEBOS, os.path.join(_ROOT, "bada_silent_vim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from bada import run_source  # noqa: E402


class LaunchRequest:
    """Returned to the Terminal when the user runs vim/emacs."""

    def __init__(self, program: str, filename: str | None):
        self.program = program
        self.filename = filename


class Shell:
    def __init__(self, vfs: VFS | None = None):
        self.vfs = vfs or VFS()
        self.env = {"USER": "bada", "HOME": "/home/bada",
                    "SHELL": "/bin/bash", "TERM": "w9wm-256color"}
        self.launch_request: LaunchRequest | None = None

    # -- entry point -------------------------------------------------------
    def run(self, line: str) -> str:
        line = line.strip()
        if not line or line.startswith("#"):
            return ""
        self.launch_request = None
        # pipeline
        stages = [s.strip() for s in line.split("|")]
        stdin = ""
        out = ""
        for stage in stages:
            out = self._run_stage(stage, stdin)
            stdin = out
            if self.launch_request is not None:
                break
        return out

    # -- one command (with redirection) ------------------------------------
    def _run_stage(self, stage: str, stdin: str) -> str:
        try:
            tokens = shlex.split(stage)
        except ValueError as e:
            return f"bash: {e}"
        if not tokens:
            return ""

        redirect = None
        append = False
        clean: list[str] = []
        i = 0
        while i < len(tokens):
            t = tokens[i]
            if t in (">", ">>"):
                append = t == ">>"
                if i + 1 >= len(tokens):
                    return "bash: syntax error near redirection"
                redirect = tokens[i + 1]
                i += 2
                continue
            clean.append(t)
            i += 1

        cmd, args = clean[0], clean[1:]
        fn = self.BUILTINS.get(cmd)
        if fn is None:
            return f"bash: {cmd}: command not found"
        try:
            out = fn(self, args, stdin)
        except VFSError as e:
            return str(e)

        if redirect is not None:
            existing = ""
            if append and self.vfs.is_file(redirect):
                existing = self.vfs.read(redirect)
            self.vfs.write(redirect, existing + out)
            return ""
        return out

    # ====================================================================
    # builtins
    # ====================================================================
    def _pwd(self, args, stdin):
        return self.vfs.cwd + "\n"

    def _cd(self, args, stdin):
        self.vfs.chdir(args[0] if args else self.env["HOME"])
        return ""

    def _ls(self, args, stdin):
        path = args[-1] if args and not args[-1].startswith("-") else None
        long = "-l" in args
        names = self.vfs.listdir(path)
        if long:
            return "\n".join(
                ("d " if n.endswith("/") else "- ") + n for n in names
            ) + ("\n" if names else "")
        return ("  ".join(names) + "\n") if names else ""

    def _echo(self, args, stdin):
        # expand $VAR
        words = [self.env.get(a[1:], "") if a.startswith("$") else a
                 for a in args]
        return " ".join(words) + "\n"

    def _cat(self, args, stdin):
        if not args:
            return stdin
        return "".join(self.vfs.read(a) for a in args)

    def _mkdir(self, args, stdin):
        for a in args:
            if a == "-p":
                continue
            self.vfs.mkdir(a)
        return ""

    def _touch(self, args, stdin):
        for a in args:
            if not self.vfs.is_file(a):
                self.vfs.write(a, "")
        return ""

    def _rm(self, args, stdin):
        for a in args:
            if a.startswith("-"):
                continue
            self.vfs.remove(a)
        return ""

    def _cp(self, args, stdin):
        src, dst = args[0], args[1]
        self.vfs.write(dst, self.vfs.read(src))
        return ""

    def _mv(self, args, stdin):
        src, dst = args[0], args[1]
        self.vfs.write(dst, self.vfs.read(src))
        self.vfs.remove(src)
        return ""

    def _head(self, args, stdin):
        n = 10
        files = []
        i = 0
        while i < len(args):
            if args[i] == "-n":
                n = int(args[i + 1])
                i += 2
            else:
                files.append(args[i])
                i += 1
        text = "".join(self.vfs.read(f) for f in files) if files else stdin
        return "\n".join(text.splitlines()[:n]) + "\n"

    def _grep(self, args, stdin):
        pattern = args[0]
        text = ("".join(self.vfs.read(f) for f in args[1:])
                if len(args) > 1 else stdin)
        return "\n".join(l for l in text.splitlines() if pattern in l) + "\n"

    def _wc(self, args, stdin):
        text = ("".join(self.vfs.read(f) for f in args)
                if args else stdin)
        lines = text.count("\n")
        words = len(text.split())
        chars = len(text)
        return f"{lines} {words} {chars}\n"

    def _env(self, args, stdin):
        return "".join(f"{k}={v}\n" for k, v in sorted(self.env.items()))

    def _export(self, args, stdin):
        for a in args:
            if "=" in a:
                k, _, v = a.partition("=")
                self.env[k] = v
        return ""

    def _whoami(self, args, stdin):
        return self.env["USER"] + "\n"

    def _clear(self, args, stdin):
        return "\x0c"          # form-feed: Terminal clears its transcript

    def _bada(self, args, stdin):
        if not args:
            return "bada: usage: bada FILE.bada\n"
        src = self.vfs.read(args[0])
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                run_source(src)
        except Exception as e:
            return f"{type(e).__name__}: {e}\n"
        return buf.getvalue()

    def _check(self, args, stdin):
        # Bada grammar checker over a VFS file.
        from bada import lint
        if not args:
            return "check: usage: check FILE.bada\n"
        ds = lint(self.vfs.read(args[0]))
        if not ds:
            return f"{args[0]}: OK (no syntax errors)\n"
        return "".join(f"{args[0]}:{d}\n" for d in ds)

    def _vim(self, args, stdin):
        self.launch_request = LaunchRequest("vim", args[0] if args else None)
        return ""

    def _emacs(self, args, stdin):
        self.launch_request = LaunchRequest("emacs", args[0] if args else None)
        return ""

    def _qcrypto(self, args, stdin):
        # Jones-polynomial quantum cryptography app, runnable from the terminal.
        from qcrypto.app import QuantumCryptoApp
        sub = args[0] if args else "demo"
        if sub == "jones":
            braid = [int(x) for x in args[1:]] or [1, 1, 1]
            d = QuantumCryptoApp(braid=braid).jones(braid)
            return (f"braid {d['braid']}\nJones V(t) = {d['jones']}\n"
                    f"key {d['key_fingerprint']}\n")
        if sub == "badajones":
            # the Jones polynomial computed natively by the Bada library
            from qcrypto.bada_jones import bada_jones_show
            braid = [int(x) for x in args[1:]] or [1, 1, 1]
            return f"V(t) = {bada_jones_show(braid)}  (computed in Bada)\n"
        # default: full activation demo
        r = QuantumCryptoApp().boot()
        act = r["activation"]
        return ("quantum signature: "
                + ("VALID\n" if r["signature_valid"] else "INVALID\n")
                + f"cryptanalysis: broke key {act.get('broken_key')} "
                  f"in {act.get('tried')} tries\n"
                + f"recovered braid: {act.get('recovered_braid')}\n"
                + f"Jones V(t) = {act.get('jones')}\n"
                + "Jones-polynomial quantum cryptography ACTIVATED\n")

    def _al(self, args, stdin):
        # AL — the Laevatein AI/machine OS (libraries written in Bada).
        from al import bridge
        sub = args[0] if args else "boot"
        if sub == "grover":
            nq = int(args[1]) if len(args) > 1 else 4
            mk = int(args[2]) if len(args) > 2 else 11
            return f"Grover resonance mode = {bridge.grover(nq, mk)}\n"
        if sub == "cool":
            steps = int(args[1]) if len(args) > 1 else 120
            q = float(args[2]) if len(args) > 2 else 220
            sc = float(args[3]) if len(args) > 3 else 0.8
            r = bridge.cooling_sim(steps, q, sc)
            return (f"Lambda Driver cooling: maxT={r[0]:.1f} finalT={r[1]:.1f} "
                    f"meltdown={'YES' if r[2] else 'no'}\n")
        if sub == "mind":
            k = int(args[1]) if len(args) > 1 else 8
            g = int(args[2]) if len(args) > 2 else 60
            s = int(args[3]) if len(args) > 3 else 1234
            return f"machine consciousness = {bridge.consciousness(k, g, s)} ignited neurons\n"
        if sub == "robot":
            sensors = [int(x) for x in args[1:4]] or [1, 0, 1]
            return f"robot FPGA motors [L,R] = {bridge.robot_fpga(sensors)}\n"
        if sub == "gen":
            seed = int(args[1]) if len(args) > 1 else 77
            lines = int(args[2]) if len(args) > 2 else 3
            return bridge.apriori(seed, lines) + "\n"
        if sub == "gamma":
            amp = float(args[1]) if len(args) > 1 else 1.5
            return f"pilot gamma power = {bridge.gamma_power(amp):.4f}\n"
        if sub == "atfield":
            eff = float(args[1]) if len(args) > 1 else 1.2
            res = float(args[2]) if len(args) > 2 else 0.25
            sc = float(args[3]) if len(args) > 3 else 0.8
            ld = bridge.lambda_driver(eff, res, sc)
            return f"Lambda Driver: AT-field={ld[0]:.2f} anti-gravity={ld[1]:.2f}\n"
        if sub == "pilot":
            from al import AlOS
            import io as _io
            from contextlib import redirect_stdout as _rs
            buf = _io.StringIO()
            with _rs(buf):
                r = AlOS().boot()
            return ("AL :: pilot resonance link  "
                    f"[{'AT-FIELD ONLINE' if r['atfield_online'] else 'down'}]\n"
                    f"  gamma topography : region {r['pilot_region']}, "
                    f"power {r['gamma_power']:.3f}\n"
                    f"  haloperidol bio  : {r['haloperidol']:.2f} -> "
                    f"resonance {r['resonance']:.3f}\n"
                    f"  Lambda Driver    : AT-field {r['at_field']:.2f}, "
                    f"anti-gravity {r['anti_gravity']:.2f}\n")
        # default: concise boot summary
        from al import AlOS
        import io as _io
        from contextlib import redirect_stdout as _rs
        buf = _io.StringIO()
        with _rs(buf):
            r = AlOS().boot()
        return (f"AL :: Laevatein AI OS  [{'ONLINE' if r['online'] else 'down'}]\n"
                f"  Grover mode      : {r['resonance_mode']}\n"
                f"  consciousness    : {r['consciousness']} ignited neurons\n"
                f"  Lambda cooling   : maxT {r['cooling_maxT']:.1f}, "
                f"meltdown {'YES' if r['meltdown'] else 'no'}\n")

    def _winport(self, args, stdin):
        # WinPort: Rails-in-Bada, Win10/11 reviser port to quantum, VM bridge.
        sub = args[0] if args else "boot"
        if sub == "rails":
            from winport.rails_bada import generate_rails
            name = args[1] if len(args) > 1 else "Article"
            return generate_rails(name, args[2:] or ["title", "body"])
        if sub == "win11":
            from winport.reviser_rules import WindowsReviser
            from winport.quantum_port import WIN10_FEATURES
            rev = WindowsReviser()
            out = ""
            for n, s in WIN10_FEATURES.items():
                out += f"{n}: {rev.to_win11(s)}\n"
            return out
        if sub == "port":
            from winport.quantum_port import port_all
            out = ""
            for p in port_all():
                out += (f"{p['feature']}: {p['quantum']}  "
                        f"[Shor-9 {'ok' if p['qec_ok'] else 'FAIL'}]\n")
            return out
        if sub == "bridge":
            from winport.vm_bridge import VMBridge
            b = VMBridge().migrate(4)
            return (f"VM bridge {b['path']}\n"
                    f"delivered to quantum: {b['delivered']} "
                    f"(strength {b['delivered_strength']})\n")
        # default: boot summary
        from winport import WinPortApp
        import io as _io
        from contextlib import redirect_stdout as _rs
        buf = _io.StringIO()
        with _rs(buf):
            r = WinPortApp().boot()
        cp = r["control_panel"]
        return ("WinPort :: Windows -> quantum\n"
                f"  Rails (Bada)   : {r['rails_lines']} lines "
                f"({'ok' if r['rails_ok'] else 'FAIL'})\n"
                f"  Win10->Win11   : {r['win11_changes']} tokens rewritten\n"
                f"  control panel  : {cp['symlinks']} symlinks, "
                f"{cp['hardlinks']} hardlinks (inode shared "
                f"{cp['hardlinks_share_inode']})\n"
                f"  quantum port   : Shor-9 {'ok' if r['qec_ok'] else 'FAIL'}\n"
                f"  VM bridge      : delivered "
                f"{r['vm_bridge']['delivered']}\n")

    def _discover(self, args, stdin):
        # Math-discovery apps written in Bada (HPsi / odd-zeta / moonshine).
        import os as _os
        from bada import run_program
        import io as _io
        from contextlib import redirect_stdout as _rs
        sub = args[0] if args else "zeta"
        app = {"hpsi": "hpsi_app.bada", "zeta": "zeta_app.bada",
               "moonshine": "moonshine_app.bada",
               "sqrt2": "sqrt2_app.bada"}.get(sub)
        if app is None:
            return "discover: usage: discover [hpsi|zeta|moonshine|sqrt2]\n"
        path = _os.path.join(_WEBOS, "apps", "discover", app)
        buf = _io.StringIO()
        with _rs(buf):
            run_program(path)
        return buf.getvalue()

    def _topdown(self, args, stdin):
        # each equation group's domain as a flat 2D top-down video.
        from topdown import TopDownApp
        sub = args[0] if args else "list"
        app = TopDownApp()
        if sub == "list":
            r = app.boot()
            return (f"2D top-down domains of {r['n_domains']} equation "
                    f"groups:\n  {r['domains']}\n")
        if sub == "html":
            app.boot()
            path = args[1] if len(args) > 1 else "topdown.html"
            fold = len(args) > 2 and args[2] == "fold"
            app.save_html(path, fold)
            return (f"wrote 2D top-down domain video to {path}"
                    f"{' (kaleidoscope fold)' if fold else ''}\n")
        return "topdown: usage: topdown [list|html PATH [fold]]\n"

    def _hologram(self, args, stdin):
        # project the equation-group videos onto a Hologram Display
        # (four-mirror reflection pyramid + Bada beta(p,q) light field).
        from hologram import HologramApp
        sub = args[0] if args else "list"
        app = HologramApp()
        if sub == "list":
            r = app.boot()
            return ("Hologram Display:\n"
                    f"  projecting {r['n_sources']} equation-group videos\n"
                    f"  {r['sources']}\n"
                    f"  mirrors: {r['mirrors']}\n"
                    f"  light field: {r['light']}\n")
        if sub == "html":
            app.boot()
            path = args[1] if len(args) > 1 else "hologram.html"
            mode = args[2] if len(args) > 2 else ""
            if mode == "float":
                app.save_floatup(path)
                return (f"wrote float-up hologram to {path} "
                        "(Jones relief, conductive-plastic power)\n")
            free = mode == "free"
            app.save_html(path, free)
            return (f"wrote hologram display to {path}"
                    f"{' (free view)' if free else ' (reflection pyramid)'}\n")
        return "hologram: usage: hologram [list|html PATH [free|float]]\n"

    def _holokbd(self, args, stdin):
        # the Happy Hacking Keyboard floating as a hologram (layout from Bada).
        from hologram import HoloKeyboardApp
        sub = args[0] if args else "list"
        app = HoloKeyboardApp()
        r = app.boot()
        if sub == "list":
            return ("Holographic Happy Hacking Keyboard:\n"
                    f"  layout: HHKB Professional (US), {r['keys']} keys, "
                    f"{r['width']}U x {r['rows']} rows (computed in Bada)\n"
                    f"  power: {r['power']:.2f} W (conductive-plastic float-up)\n")
        if sub == "html":
            path = args[1] if len(args) > 1 else "holokbd.html"
            app.save_html(path)
            return f"wrote holographic HHKB keyboard to {path}\n"
        return "holokbd: usage: holokbd [list|html PATH]\n"

    def _holomirror(self, args, stdin):
        # smartphone mirror over the tablet: an eyeglass-lens aerial image forms
        # in the gap (focus from the special-relativity Jones polynomial).
        from hologram import MirrorApp
        sub = args[0] if args else "list"
        app = MirrorApp()
        r = app.boot()
        if sub == "list":
            return ("Mirror App — aerial hologram between tablet & phone:\n"
                    f"  gap: {r['gap_cm']} cm · eyeglass-lens focal point\n"
                    f"  focus z: {r['focus_rest_cm']} cm at rest -> "
                    f"{r['focus_fast_cm']} cm near {r['vmax']}c "
                    "(special-relativity Jones polynomial)\n"
                    f"  realizes: holographic display + HHKB ({r['keys']} keys)\n")
        if sub == "html":
            path = args[1] if len(args) > 1 else "holomirror.html"
            kbd = len(args) > 2 and args[2] == "keyboard"
            app.save_html(path, kbd)
            return (f"wrote mirror-app aerial hologram to {path}"
                    f"{' (HHKB keyboard)' if kbd else ' (display)'}\n")
        return "holomirror: usage: holomirror [list|html PATH [keyboard]]\n"

    def _holovision(self, args, stdin):
        # Vision-Pro-equivalent: launch the display, the tablet turns
        # transparent and its apps float out as spatial windows.
        from hologram import VisionApp
        sub = args[0] if args else "list"
        app = VisionApp()
        r = app.boot()
        if sub == "list":
            return ("Spatial Hologram (Vision-Pro-equivalent):\n"
                    f"  launch -> tablet transparent (passthrough alpha "
                    f"{r['passthrough_alpha']})\n"
                    f"  {r['windows']} app windows float out on a concave shell\n"
                    f"  anchored at the mirror-lens focus z={r['focus_cm']} cm "
                    f"(gap {r['gap_cm']} cm)\n"
                    f"  spatial HHKB input ({r['keys']} keys)\n")
        if sub == "html":
            path = args[1] if len(args) > 1 else "holovision.html"
            app.save_html(path)
            return f"wrote spatial passthrough hologram to {path}\n"
        return "holovision: usage: holovision [list|html PATH]\n"

    def _hologlass(self, args, stdin):
        # fully transparent display + Japanese HHKB over camera passthrough.
        from hologram import GlassApp
        sub = args[0] if args else "list"
        app = GlassApp()
        r = app.boot()
        if sub == "list":
            return ("Transparent Hologram (see-through):\n"
                    f"  display + HHKB rendered as glass over camera passthrough\n"
                    f"  no video — the world behind the tablet shows through\n"
                    f"  Japanese input: {r['input']} "
                    f"({r['kana_entries']} kana, from Bada)\n")
        if sub == "html":
            path = args[1] if len(args) > 1 else "hologlass.html"
            app.save_html(path)
            return f"wrote transparent JP-keyboard hologram to {path}\n"
        return "hologlass: usage: hologlass [list|html PATH]\n"

    def _freeform(self, args, stdin):
        # Samsung-Freeform-style multi-window desktop + Play-Store taskbar.
        from hologram import FreeformApp
        sub = args[0] if args else "list"
        app = FreeformApp()
        r = app.boot()
        if sub == "list":
            return ("Freeform multi-window desktop:\n"
                    f"  {r['apps']} apps · taskbar {r['taskbar_h']}px\n"
                    f"  {r['features']}\n")
        if sub == "html":
            path = args[1] if len(args) > 1 else "freeform.html"
            app.save_html(path)
            return f"wrote freeform multi-window desktop to {path}\n"
        return "freeform: usage: freeform [list|html PATH]\n"

    def _qcache(self, args, stdin):
        # the Quantum Cache Disk: hard disk -> quantum cache (all computed in Bada).
        from hologram import QCacheApp
        sub = args[0] if args else "list"
        app = QCacheApp()
        r = app.boot()
        if sub == "list":
            return ("Quantum Cache Disk:\n"
                    f"  {r['blocks']} disk blocks -> {r['qubits']}-qubit state\n"
                    f"  Reviser von-Neumann->quantum: {r['reviser']}\n"
                    f"  telomere thought prediction: block #{r['predicted_first']}"
                    f" @ hit {r['hit_prob']*100:.1f}% (Grover)\n"
                    f"  Gamma integration-by-parts manifold: "
                    f"{'OK' if r['gamma_ibp_ok'] else 'FAIL'}\n")
        if sub == "html":
            path = args[1] if len(args) > 1 else "qcache.html"
            app.save_html(path)
            return f"wrote quantum cache disk to {path}\n"
        return "qcache: usage: qcache [list|html PATH]\n"

    def _slideshow(self, args, stdin):
        # all equation-group graphs as a PowerPoint-style flash slideshow.
        from slideshow import SlideshowApp
        sub = args[0] if args else "list"
        app = SlideshowApp()
        if sub == "list":
            r = app.boot()
            return (f"slideshow of {r['n_slides']} equation-group graphs:\n"
                    f"  {r['slides']}\n"
                    f"  flash effects: {r['effects']}\n")
        if sub == "html":
            app.boot()
            path = args[1] if len(args) > 1 else "slideshow.html"
            app.save_html(path)
            return f"wrote equation-group slideshow to {path}\n"
        return "slideshow: usage: slideshow [list|html PATH]\n"

    def _superpose(self, args, stdin):
        # overlay all the manifold animations into one combined video.
        from superpose import SuperposeApp
        sub = args[0] if args else "stats"
        app = SuperposeApp()
        if sub == "stats":
            r = app.boot()
            return (f"superposition of {r['n_sources']} videos: "
                    f"{r['sources']}\n"
                    f"combined-field displacement: {r['displacement']}\n")
        if sub == "html":
            app.boot()
            path = args[1] if len(args) > 1 else "superpose.html"
            app.save_3d(path)
            return f"wrote 3D superposition video to {path}\n"
        if sub == "kaleido":
            app.boot()
            path = args[1] if len(args) > 1 else "superpose_kaleido.html"
            app.save_kaleido(path, 8)
            return f"wrote superposition kaleidoscope to {path}\n"
        return "superpose: usage: superpose [stats|html PATH|kaleido PATH]\n"

    def _kaleido(self, args, stdin):
        # top-down kaleidoscope of the equation-group manifold animations.
        from kaleido import KaleidoApp
        from eqvideo.render import CATALOG as EVC
        from transport.app import CATALOG as TRC
        sub = args[0] if args else "list"
        if sub == "list":
            out = "kaleidoscope sources (top-down manifold animations):\n"
            for nm, (title, _) in {**EVC, **TRC}.items():
                out += f"  {nm:9} {title}\n"
            return out
        if sub == "html":
            path = args[1] if len(args) > 1 else "kaleido.html"
            seg = int(args[2]) if len(args) > 2 else 8
            app = KaleidoApp()
            app.boot()
            app.save_html(path, seg)
            return f"wrote kaleidoscope to {path} ({seg} segments)\n"
        return "kaleido: usage: kaleido [list|html PATH [segments]]\n"

    def _transport(self, args, stdin):
        # Integrate-of-theorem: binomial equation generator + manifold video.
        from transport import TransportApp, CATALOG
        sub = args[0] if args else "gen"
        if sub == "gen":
            import os as _os
            import io as _io
            from contextlib import redirect_stdout as _rs
            from bada import run_program
            buf = _io.StringIO()
            with _rs(buf):
                run_program(_os.path.join(_WEBOS, "apps", "transport",
                                          "transport_app.bada"))
            return buf.getvalue()
        if sub == "list":
            out = "Integrate-of-theorem manifold dictionary:\n"
            for nm, (title, desc) in CATALOG.items():
                out += f"  {nm:9} {title} -- {desc}\n"
            return out
        if sub == "view":
            name = args[1] if len(args) > 1 else "seifert"
            app = TransportApp(n=12, frames=8)
            app.boot()
            fr = app.ascii(name)
            out = f"== {name} ({CATALOG[name][0]}) ==\n"
            for idx in (0, len(fr) // 2, len(fr) - 1):
                out += f"-- frame {idx} --\n" + fr[idx] + "\n"
            return out
        if sub == "html":
            path = args[1] if len(args) > 1 else "transport.html"
            app = TransportApp()
            app.boot()
            app.save_html(path)
            return f"wrote transport video dictionary to {path}\n"
        return "transport: usage: transport [gen|list|view NAME|html PATH]\n"

    def _eqvideo(self, args, stdin):
        # equation-group 3D animation video dictionary (Bada manifolds).
        from eqvideo import EqVideoApp, CATALOG
        sub = args[0] if args else "list"
        if sub == "list":
            out = "equation-group 3D animation dictionary:\n"
            for nm, (title, desc) in CATALOG.items():
                out += f"  {nm:10} {title} -- {desc}\n"
            return out
        if sub == "view":
            name = args[1] if len(args) > 1 else "fermat"
            app = EqVideoApp(n=12, frames=8)
            app.boot()
            frames = app.ascii(name)
            # a compact flip-book: a few frames
            out = f"== {name} ({CATALOG[name][0]}) ==\n"
            for idx in (0, len(frames) // 2, len(frames) - 1):
                out += f"-- frame {idx} --\n" + frames[idx] + "\n"
            return out
        if sub == "html":
            path = args[1] if len(args) > 1 else "eqvideo.html"
            app = EqVideoApp()
            app.boot()
            app.save_html(path)
            return f"wrote animated video dictionary to {path}\n"
        return "eqvideo: usage: eqvideo [list|view NAME|html PATH]\n"

    def _eqgen(self, args, stdin):
        # generate the equation group from Euler zeta & beta (Bada).
        import os as _os
        import io as _io
        from contextlib import redirect_stdout as _rs
        from bada import run_program
        buf = _io.StringIO()
        with _rs(buf):
            run_program(_os.path.join(_WEBOS, "apps", "eqgen",
                                      "eqgen_app.bada"))
        return buf.getvalue()

    def _mobius(self, args, stdin):
        # Jones-Mobius causal analyzer (Bada): are the equations Mobius eqs?
        import os as _os
        import io as _io
        from contextlib import redirect_stdout as _rs
        from bada import run_program
        buf = _io.StringIO()
        with _rs(buf):
            run_program(_os.path.join(_WEBOS, "apps", "jonesmobius",
                                      "jonesmobius_app.bada"))
        return buf.getvalue()

    def _beta(self, args, stdin):
        # Beta-function difference-equation factorization + zeta links (Bada).
        import os as _os
        import io as _io
        from contextlib import redirect_stdout as _rs
        from bada import run_program
        buf = _io.StringIO()
        with _rs(buf):
            run_program(_os.path.join(_WEBOS, "apps", "beta", "beta_app.bada"))
        return buf.getvalue()

    def _help(self, args, stdin):
        names = " ".join(sorted(self.BUILTINS))
        return ("BadaWebOS terminal — available apps:\n"
                f"  {names}\n"
                "  editors: vim FILE, emacs FILE\n"
                "  run Bada: bada FILE.bada   grammar check: check FILE.bada\n"
                "  quantum crypto: qcrypto [demo|jones N...|badajones N...]\n"
                "  Laevatein AI:   al [boot|grover|cool|mind|robot|gen]\n"
                "  pilot/ATfield:  al [pilot|gamma|atfield]\n"
                "  Windows->QC:    winport [boot|rails|win11|port|bridge]\n"
                "  discovery:      discover [hpsi|zeta|moonshine|sqrt2]\n"
                "  beta:           beta  (Beta factorization + zeta links)\n"
                "  causal:         mobius  (Jones-Mobius causal analyzer)\n"
                "  equation gen:   eqgen  (generate equations from zeta&beta)\n"
                "  video dict:     eqvideo [list|view NAME|html PATH]\n"
                "  transport:      transport [gen|list|view NAME|html PATH]\n"
                "  kaleidoscope:   kaleido [list|html PATH [segments]]\n"
                "  superpose all:  superpose [stats|html PATH|kaleido PATH]\n"
                "  slideshow:      slideshow [list|html PATH]\n"
                "  2D top-down:    topdown [list|html PATH [fold]]\n"
                "  hologram:       hologram [list|html PATH [free|float]]\n"
                "  holo keyboard:  holokbd [list|html PATH]\n"
                "  mirror app:     holomirror [list|html PATH [keyboard]]\n"
                "  spatial (VP):   holovision [list|html PATH]\n"
                "  transparent JP: hologlass [list|html PATH]\n"
                "  freeform WM:    freeform [list|html PATH]\n"
                "  quantum cache:  qcache [list|html PATH]\n")

    BUILTINS = {
        "pwd": _pwd, "cd": _cd, "ls": _ls, "echo": _echo, "cat": _cat,
        "mkdir": _mkdir, "touch": _touch, "rm": _rm, "cp": _cp, "mv": _mv,
        "head": _head, "grep": _grep, "wc": _wc, "env": _env,
        "export": _export, "whoami": _whoami, "clear": _clear,
        "bada": _bada, "check": _check, "vim": _vim, "emacs": _emacs,
        "qcrypto": _qcrypto, "al": _al, "winport": _winport,
        "discover": _discover, "beta": _beta, "mobius": _mobius,
        "eqgen": _eqgen, "eqvideo": _eqvideo, "transport": _transport,
        "kaleido": _kaleido, "superpose": _superpose,
        "slideshow": _slideshow, "topdown": _topdown,
        "hologram": _hologram, "holokbd": _holokbd,
        "holomirror": _holomirror, "holovision": _holovision,
        "hologlass": _hologlass, "freeform": _freeform,
        "qcache": _qcache, "help": _help,
    }
