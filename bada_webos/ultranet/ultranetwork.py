"""The ultranetwork, rebuilt as a BadaWebOS application.

Confirmed core features:

  * **TupleSpace + arrow-syntax evaluator** — runs the ``ultranetwork.bada``
    program on the Bada compiler + VM (the arrows ``<- -< >- >> =>`` and the
    ``Omega::DATABASE`` Akashic TupleSpace).
  * **gravity-port gates** — :class:`GravityPort` from :mod:`ultranet.net`.
  * **neural XOR learning** — :class:`XORNet` from :mod:`ultranet.learn`.
  * **bridge / repeater propagation** — :class:`BridgeRepeaterNet`.

:meth:`UltraNetwork.boot` runs all four and returns a structured report the
Web-OS desktop can display in a window.
"""

from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stdout

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)                                  # repo root
sys.path.insert(0, os.path.join(_ROOT, "bada_silent_vim"))  # the bada package

from bada import run_source                       # noqa: E402
from ultranet.learn import XORNet                  # noqa: E402
from ultranet.net import BridgeRepeaterNet, GravityPort  # noqa: E402

_APP_BADA = os.path.join(_ROOT, "bada_webos", "apps", "ultranetwork.bada")


class UltraNetwork:
    def __init__(self, bada_app: str = _APP_BADA):
        self.bada_app = bada_app
        self.report: dict = {}

    # -- 1. TupleSpace + arrow evaluator (on the Bada VM) ------------------
    def run_tuplespace(self) -> dict:
        with open(self.bada_app) as f:
            src = f.read()
        buf = io.StringIO()
        with redirect_stdout(buf):
            vm = run_source(src)
        return {
            "output": buf.getvalue().splitlines(),
            "tuplespace": vm.tuplespace,
            "stream": vm.stream,
        }

    # -- 2. neural XOR learning -------------------------------------------
    def learn_xor(self, epochs: int = 5000) -> dict:
        net = XORNet()
        loss = net.train(epochs=epochs)
        return {"loss": round(loss, 6),
                "accuracy": net.accuracy(),
                "truth_table": net.truth_table()}

    # -- 3 + 4. gravity ports over bridge/repeater propagation ------------
    def propagate(self) -> dict:
        net = BridgeRepeaterNet(hop_attenuation=0.6)
        for name in ("A", "B", "C", "D", "E"):
            net.add_node(name)
        for a, b in (("A", "B"), ("B", "C"), ("C", "D"), ("D", "E")):
            net.bridge(a, b)
        net.set_repeater("C", gain=2.0)          # repeater boosts downstream
        strengths = net.propagate("A", payload=1.0)

        gate = GravityPort(mass=1.0, threshold=0.3)
        gated = {n: round(gate.gate(s), 4) for n, s in strengths.items()}
        return {
            "strengths": {n: round(v, 4) for n, v in strengths.items()},
            "gravity_gated": gated,
            "reachable": sorted(net.reachable("A")),
        }

    # -- boot all four -----------------------------------------------------
    def boot(self) -> dict:
        self.report = {
            "tuplespace": self.run_tuplespace(),
            "xor": self.learn_xor(),
            "propagation": self.propagate(),
        }
        return self.report

    def render_html(self) -> str:
        r = self.report or self.boot()
        ts = "<br>".join(r["tuplespace"]["output"])
        xor = r["xor"]["truth_table"]
        prop = r["propagation"]["strengths"]
        return (
            '<section class="os-window" data-app="ultranetwork">'
            '<h2>ultranetwork</h2>'
            f'<p><b>TupleSpace</b>: {ts}</p>'
            f'<p><b>XOR learned</b> (acc {r["xor"]["accuracy"]}): {xor}</p>'
            f'<p><b>bridge/repeater</b>: {prop}</p>'
            '</section>')
