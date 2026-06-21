"""WinPort — Rails-in-Bada, Win10/11 reviser, symlink control panel, and a
VM bridge/repeater that ports Windows features to the quantum computer.
"""

from __future__ import annotations

import os
import sys
import tempfile
from html import escape

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
for p in (_PKG, _HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from winport.rails_bada import generate_rails        # noqa: E402
from winport.reviser_rules import WindowsReviser      # noqa: E402
from winport.quantum_port import WIN10_FEATURES, port_all  # noqa: E402
from winport.vm_bridge import VMBridge                # noqa: E402
from winport import control_panel                     # noqa: E402


class WinPortApp:
    def boot(self) -> dict:
        # 1. Rails functioning source, generated in Bada
        rails = generate_rails("Article", ["title", "body", "published"])

        # 2. Win10 -> Win11 rewrite via the reviser
        rev = WindowsReviser()
        win11 = {n: rev.to_win11(s) for n, s in WIN10_FEATURES.items()}
        win11_changes = sum(rev.changes_win11(s)
                            for s in WIN10_FEATURES.values())

        # 3. hardware control panel via symlinks + hardlinks (sandboxed)
        tmp = tempfile.mkdtemp(prefix="winport_")
        panel = control_panel.build_control_panel(tmp)
        panel_info = control_panel.inspect(panel)

        # 4. port every Windows feature to the quantum computer (reviser+Shor9)
        ported = port_all()
        qec_ok = all(p["qec_ok"] for p in ported)

        # 5. migrate the VM to the quantum node via bridge + repeater
        bridge = VMBridge().migrate(len(ported))

        self.report = {
            "rails_lines": len(rails.splitlines()),
            "rails_ok": "class Article < ApplicationRecord" in rails
                        and "resources :Articles" in rails,
            "win11_features": list(win11),
            "win11_changes": win11_changes,
            "control_panel": panel_info,
            "ported": ported,
            "qec_ok": qec_ok,
            "vm_bridge": bridge,
            "rails": rails,
        }
        return self.report

    def render_html(self) -> str:
        r = self.report
        cp = r["control_panel"]
        b = r["vm_bridge"]
        rows = [
            ("Rails (in Bada)", f"{r['rails_lines']} lines, "
             f"{'ok' if r['rails_ok'] else 'FAIL'}"),
            ("Win10 → Win11 reviser", f"{r['win11_changes']} tokens rewritten "
             f"across {len(r['win11_features'])} features"),
            ("control panel", f"{cp['symlinks']} symlinks "
             f"({'ok' if cp['symlinks_ok'] else 'bad'}), "
             f"{cp['hardlinks']} hardlinks "
             f"(inode shared: {cp['hardlinks_share_inode']})"),
            ("quantum port", f"{len(r['ported'])} features ported, "
             f"Shor-9 {'ok' if r['qec_ok'] else 'FAIL'}"),
            ("VM bridge+repeater", f"delivered to quantum: {b['delivered']} "
             f"(strength {b['delivered_strength']})"),
        ]
        body = "".join(f"<dt>{escape(k)}</dt><dd>{escape(str(v))}</dd>"
                       for k, v in rows)
        sample = "<br>".join(escape(line) for line in
                             r["rails"].splitlines()[:6])
        return (
            '<section class="os-window" data-app="winport">'
            '<h2>WinPort — VM Bridge → Quantum</h2>'
            f'<dl class="os-detail">{body}</dl>'
            f'<p><b>Rails source (Bada-generated):</b><br>'
            f'<code>{sample}</code></p>'
            '<p>symlink/hardlink control panel · reviser port · '
            'bridge+repeater</p></section>')
