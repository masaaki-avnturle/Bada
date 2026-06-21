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

    def _help(self, args, stdin):
        names = " ".join(sorted(self.BUILTINS))
        return ("BadaWebOS terminal — available apps:\n"
                f"  {names}\n"
                "  editors: vim FILE, emacs FILE\n"
                "  run Bada: bada FILE.bada   grammar check: check FILE.bada\n"
                "  quantum crypto: qcrypto [demo|jones N...|badajones N...]\n"
                "  Laevatein AI:   al [boot|grover|cool|mind|robot|gen]\n"
                "  pilot/ATfield:  al [pilot|gamma|atfield]\n"
                "  Windows->QC:    winport [boot|rails|win11|port|bridge]\n")

    BUILTINS = {
        "pwd": _pwd, "cd": _cd, "ls": _ls, "echo": _echo, "cat": _cat,
        "mkdir": _mkdir, "touch": _touch, "rm": _rm, "cp": _cp, "mv": _mv,
        "head": _head, "grep": _grep, "wc": _wc, "env": _env,
        "export": _export, "whoami": _whoami, "clear": _clear,
        "bada": _bada, "check": _check, "vim": _vim, "emacs": _emacs,
        "qcrypto": _qcrypto, "al": _al, "winport": _winport, "help": _help,
    }
