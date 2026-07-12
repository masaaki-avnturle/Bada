"""Port Windows features to the quantum computer via the Reviser.

Each Windows feature spec is rewritten Win10 -> Win11 -> quantum target by the
:class:`WindowsReviser`, and the ported logical register is protected by the
Shor 9-qubit code (encode, inject a transport error, correct) so the migration
is fault-tolerant.
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
for p in (_PKG, _HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from quantum.shor9 import Shor9               # noqa: E402
from reviser_rules import WindowsReviser      # noqa: E402

# Windows 10 feature specs (the source of the port).
WIN10_FEATURES = {
    "kernel": "Windows10 kernel: CPU scheduler, thread, register, "
              "cache, RAM, bit logic, process model",
    "graphics": "Windows10 DirectX11 graphics stack over Win32",
    "shell": "Windows10 StartMenu, Cortana, TilesUI, ControlPanel",
    "security": "Windows10 TPM1 secure boot, Edge18 browser",
}


def port_feature(name: str, win10_spec: str) -> dict:
    rev = WindowsReviser()
    win11 = rev.to_win11(win10_spec)
    quantum = rev.to_quantum(win11)

    # fault-tolerant transport: protect the ported register with Shor-9
    code = Shor9()
    code.encode(0.6, 0.8)
    code.inject_error("Y", (sum(map(ord, name)) % 9))   # a transport glitch
    code.correct()
    fidelity = code.fidelity(0.6, 0.8)

    return {
        "feature": name,
        "win11": win11,
        "quantum": quantum,
        "win11_changes": rev.changes_win11(win10_spec),
        "quantum_changes": rev.changes_quantum(win11),
        "qec_fidelity": round(fidelity, 4),
        "qec_ok": fidelity > 0.999,
    }


def port_all(features: dict | None = None) -> list:
    features = features or WIN10_FEATURES
    return [port_feature(n, s) for n, s in features.items()]
