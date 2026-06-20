"""AlOS — the Laevatein AI / machine OS as a BadaWebOS application.

Boots the AL Bada program (``apps/al/al_laevatein.bada``) on the VM and exposes
its result as a desktop window: Grover resonance mode, Lambda Driver cooling
status, evolved machine consciousness, the a-priori engine's generated code,
and the robot FPGA command.
"""

from __future__ import annotations

import os
import sys
from html import escape

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_PKG)
for p in (_ROOT, _PKG, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from bada import run_program                          # noqa: E402
from al.bridge import APP, PILOT_APP                  # noqa: E402


class AlOS:
    def boot(self) -> dict:
        vm = run_program(APP)
        self.output = vm.output
        store = vm.tuplespace.get("al", [])
        mode_phi = store[0] if store else [None, None]
        cooling = store[1] if len(store) > 1 else [None, None, None]
        self.report = {
            "resonance_mode": mode_phi[0],
            "consciousness": mode_phi[1],
            "cooling_maxT": cooling[0],
            "cooling_finalT": cooling[1],
            "meltdown": bool(cooling[2]) if cooling[2] is not None else None,
            "online": "AL-online" in store,
            "generated_code": self._generated_code(),
        }
        self.report.update(self._boot_pilot())
        return self.report

    def _boot_pilot(self) -> dict:
        """Run the pilot resonance link: gamma waves -> AT field + anti-gravity."""
        vm = run_program(PILOT_APP)
        p = vm.tuplespace.get("pilot", [])
        region_gp = p[0] if p else [None, None]
        bf = p[1] if len(p) > 1 else [None, None, None]
        ld = p[2] if len(p) > 2 else [None, None]
        return {
            "pilot_region": region_gp[0],
            "gamma_power": region_gp[1],
            "resonance": bf[0],
            "haloperidol": bf[1],
            "eff_gamma": bf[2],
            "at_field": ld[0],
            "anti_gravity": ld[1],
            "atfield_online": "AT-field-online" in p,
        }

    def _generated_code(self) -> list:
        code = []
        grab = False
        for line in self.output:
            if line.startswith("[E]"):
                grab = True
                continue
            if grab:
                if line.startswith("[R]") or line.startswith("AL online"):
                    break
                if line.strip():
                    code.append(line)
        return code

    def render_html(self) -> str:
        r = self.report
        melt = "MELTDOWN" if r["meltdown"] else "nominal"
        rows = [
            ("status", "ONLINE" if r["online"] else "offline"),
            ("Grover resonance mode", r["resonance_mode"]),
            ("machine consciousness", f"{r['consciousness']} ignited neurons"),
            ("Lambda Driver cooling",
             f"maxT {r['cooling_maxT']:.1f} / final "
             f"{r['cooling_finalT']:.1f} — {melt}"),
            ("pilot gamma power", f"{r['gamma_power']:.3f} "
             f"(region {r['pilot_region']})"),
            ("haloperidol biofeedback",
             f"{r['haloperidol']:.2f} → resonance {r['resonance']:.3f}"),
            ("Lambda Driver output",
             f"AT-field {r['at_field']:.2f}, anti-gravity "
             f"{r['anti_gravity']:.2f}"),
        ]
        body = "".join(f"<dt>{escape(k)}</dt><dd>{escape(str(v))}</dd>"
                       for k, v in rows)
        code = "<br>".join(escape(c) for c in r["generated_code"])
        return (
            '<section class="os-window" data-app="al">'
            '<h2>AL — Laevatein AI / Machine OS</h2>'
            f'<dl class="os-detail">{body}</dl>'
            f'<p><b>a-priori engine output:</b><br>'
            f'<code>{code}</code></p>'
            '<p>palladium reactor neural · supercooled anti-gravity coolant · '
            'robot FPGA</p></section>')
