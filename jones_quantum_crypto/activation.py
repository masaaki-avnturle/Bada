"""Activation linkage: cryptanalysing the quantum digital signature triggers
the Jones-polynomial quantum cryptography.

    QuantumDigitalSignature.issue(msg, secret_braid, analysis_key)
            │  (signature conceals the braid)
            ▼
    cryptanalyze(signature, analysis_key)   ← decrypt / break the embedded key
            │  ok  → recovered braid
            ▼
    JonesQuantumCipher.from_braid(braid)     ← key = Jones invariant of braid
            │
            ▼  Jones-polynomial quantum cryptography ACTIVATED
    encrypt / decrypt payloads
"""

from __future__ import annotations

from .qcipher import JonesQuantumCipher, describe_braid
from .qsign import QuantumDigitalSignature


class JonesActivation:
    def __init__(self):
        self.cipher: JonesQuantumCipher | None = None
        self.report: dict = {}

    # -- the trigger -------------------------------------------------------
    def activate_from_cryptanalysis(self, sig_obj: dict,
                                    analysis_key: str) -> dict:
        result = QuantumDigitalSignature.cryptanalyze(sig_obj, analysis_key)
        if not result["ok"]:
            self.report = {"activated": False,
                           "reason": "cryptanalysis failed"}
            return self.report
        braid = result["braid"]
        self.cipher = JonesQuantumCipher.from_braid(braid)
        self.report = {
            "activated": True,
            "recovered_braid": braid,
            "jones": describe_braid(braid)["jones"],
            "key_fingerprint": self.cipher.fingerprint(),
        }
        return self.report

    def activate_by_breaking(self, sig_obj: dict, candidates) -> dict:
        result = QuantumDigitalSignature.cryptanalyze_bruteforce(
            sig_obj, candidates)
        if not result["ok"]:
            self.report = {"activated": False, "reason": "key not broken",
                           "tried": result.get("tried")}
            return self.report
        out = self.activate_from_cryptanalysis(sig_obj, result["key"])
        out["broken_key"] = result["key"]
        out["tried"] = result["tried"]
        return out

    # -- use the activated cipher -----------------------------------------
    def encrypt(self, plaintext: bytes) -> bytes:
        if not self.cipher:
            raise RuntimeError("Jones cryptography not activated")
        return self.cipher.encrypt(plaintext)

    def decrypt(self, blob: bytes) -> bytes:
        if not self.cipher:
            raise RuntimeError("Jones cryptography not activated")
        return self.cipher.decrypt(blob)


def demo() -> dict:
    """End-to-end: issue a quantum signature concealing the trefoil braid,
    cryptanalyse it, and use the activated Jones cipher."""
    qds = QuantumDigitalSignature()
    secret_braid = [1, 1, 1]              # the trefoil
    analysis_key = "0042"                 # weak/escrowed PIN by design
    sig = qds.issue(b"launch-authorization", secret_braid, analysis_key)

    out = {"signature_valid": QuantumDigitalSignature.verify(sig)}

    # cryptanalysis by breaking the weak key triggers activation
    act = JonesActivation()
    report = act.activate_by_breaking(sig, (f"{i:04d}" for i in range(1000)))
    out["activation"] = report

    if report["activated"]:
        secret = b"Jones quantum channel open"
        blob = act.encrypt(secret)
        out["roundtrip_ok"] = act.decrypt(blob) == secret
        out["ciphertext_prefix"] = blob[:16].hex()
    return out
