"""VM bridge + repeater: migrate the ported Windows VM to the quantum node.

The ported VM image is transported across a small network
``win_vm -> bridge -> repeater -> quantum`` using the ultranetwork's
bridge/repeater propagation (the repeater re-amplifies the signal so the image
reaches the quantum substrate intact).
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
if _PKG not in sys.path:
    sys.path.insert(0, _PKG)

from ultranet.net import BridgeRepeaterNet      # noqa: E402


class VMBridge:
    def __init__(self, hop_attenuation: float = 0.6, repeater_gain: float = 3.0):
        self.net = BridgeRepeaterNet(hop_attenuation=hop_attenuation)
        for node in ("win_vm", "bridge", "repeater", "quantum"):
            self.net.add_node(node)
        self.net.bridge("win_vm", "bridge")
        self.net.bridge("bridge", "repeater")
        self.net.bridge("repeater", "quantum")
        self.net.set_repeater("repeater", repeater_gain)

    def migrate(self, n_features: int, payload: float = 1.0) -> dict:
        strengths = self.net.propagate("win_vm", payload=payload)
        delivered = strengths.get("quantum", 0.0)
        return {
            "path": ["win_vm", "bridge", "repeater", "quantum"],
            "strengths": {k: round(v, 4) for k, v in strengths.items()},
            "delivered": delivered > 0,
            "delivered_strength": round(delivered, 4),
            "features_migrated": n_features if delivered > 0 else 0,
            "reachable": sorted(self.net.reachable("win_vm")),
        }
