"""Quantum-crypto application for BadaWebOS.

Wraps the repo's :mod:`jones_quantum_crypto` engine as a Web-OS app: it boots
the full "cryptanalyse a quantum digital signature -> activate Jones-polynomial
quantum cryptography" flow and renders it as a desktop window.  The same engine
is reachable from the terminal via the ``qcrypto`` command, and the flow is
narrated in Bada on the VM by ``apps/quantum_crypto.bada``.
"""

from __future__ import annotations

import os
import sys
from html import escape

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)               # bada_webos/
_ROOT = os.path.dirname(_PKG)               # repo root (has jones_quantum_crypto)
for p in (_ROOT, _PKG):
    if p not in sys.path:
        sys.path.insert(0, p)

from jones_quantum_crypto import (JonesActivation, JonesQuantumCipher,  # noqa
                                  QuantumDigitalSignature, describe_braid)


class QuantumCryptoApp:
    def __init__(self, braid: list[int] | None = None, pin: str = "0042"):
        self.braid = braid or [1, 1, 1]      # the trefoil
        self.pin = pin
        self.report: dict = {}

    def boot(self) -> dict:
        qds = QuantumDigitalSignature()
        sig = qds.issue(b"launch-authorization", self.braid, self.pin)
        valid = QuantumDigitalSignature.verify(sig)

        # cryptanalysis: break the weak escrow PIN -> activates Jones crypto
        act = JonesActivation()
        rep = act.activate_by_breaking(
            sig, (f"{i:04d}" for i in range(int(self.pin) + 5)))

        roundtrip = None
        ct_prefix = None
        if rep["activated"]:
            payload = b"Jones quantum channel open"
            blob = act.encrypt(payload)
            roundtrip = act.decrypt(blob) == payload
            ct_prefix = blob[:16].hex()

        # the Jones polynomial computed natively by the Bada library
        try:
            from qcrypto.bada_jones import bada_jones_show
            jones_in_bada = bada_jones_show(self.braid)
        except Exception as exc:                      # pragma: no cover
            jones_in_bada = f"(error: {exc})"

        self.report = {
            "signature_valid": valid,
            "activation": rep,
            "roundtrip_ok": roundtrip,
            "ciphertext_prefix": ct_prefix,
            "jones_in_bada": jones_in_bada,
        }
        return self.report

    def jones(self, braid: list[int] | None = None) -> dict:
        return describe_braid(braid or self.braid)

    # -- rendering ---------------------------------------------------------
    def render_html(self) -> str:
        r = self.report or self.boot()
        act = r["activation"]
        status = ("ACTIVATED" if act["activated"] else "not activated")
        rows = [
            ("signature", "VALID" if r["signature_valid"] else "INVALID"),
            ("cryptanalysis", f"broke key {act.get('broken_key')} "
                              f"in {act.get('tried')} tries"),
            ("recovered braid", str(act.get("recovered_braid"))),
            ("Jones V(t)", act.get("jones", "")),
            ("Jones V(t) in Bada", r.get("jones_in_bada", "")),
            ("Jones cipher key", act.get("key_fingerprint", "")),
            ("encrypt/decrypt", "ok" if r["roundtrip_ok"] else "—"),
        ]
        body = "".join(f"<dt>{escape(k)}</dt><dd>{escape(str(v))}</dd>"
                       for k, v in rows)
        return (
            '<section class="os-window" data-app="qcrypto">'
            f'<h2>Quantum Crypto (Jones) — {escape(status)}</h2>'
            f'<dl class="os-detail">{body}</dl>'
            '<p>cryptanalyse the quantum signature ⟶ Jones-polynomial '
            'quantum cryptography</p></section>')
