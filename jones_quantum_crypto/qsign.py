"""Quantum digital signature with an embedded, cryptanalysable secret.

The signature is an Ed25519 signature (the same quantum-era digital signature
used by the ``access_signature`` package) over the message, but it also
*commits to and conceals a secret braid*.  "Cryptanalysing" the signature means
recovering that braid by decrypting the embedded ciphertext — and a successful
cryptanalysis is what activates the Jones-polynomial quantum cryptography
(see :mod:`jones_quantum_crypto.activation`).

The concealment key (``analysis_key``) is intended to be escrowed / weak by
design in this research setting, so that *breaking it* triggers the next stage
— a controlled, authorised "decrypt-to-activate" protocol on one's own data.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
# reuse the pure-Python Ed25519 from the access_signature package
from access_signature import ed25519_pure as ed       # noqa: E402


def _braid_to_bytes(braid: list[int]) -> bytes:
    return (",".join(str(g) for g in braid)).encode()


def _braid_from_bytes(data: bytes) -> list[int]:
    s = data.decode()
    return [int(x) for x in s.split(",")] if s else []


def _keystream(analysis_key: str, salt: bytes, nbytes: int) -> bytes:
    # Moderate scrypt: strong enough to be a real KDF, light enough that a
    # brute-force-the-weak-key demo runs in seconds.
    return hashlib.scrypt(analysis_key.encode(), salt=salt, n=2 ** 12, r=8,
                          p=1, dklen=max(1, nbytes))


class QuantumDigitalSignature:
    def __init__(self, seed: bytes | None = None):
        self.seed = seed or secrets.token_bytes(32)
        self.pub = ed.publickey(self.seed)

    def public_key(self) -> str:
        return self.pub.hex()

    # -- issue a signature that conceals a secret braid -------------------
    def issue(self, message: bytes, braid_secret: list[int],
              analysis_key: str) -> dict:
        sig = ed.sign(message, self.seed, self.pub)
        braid_bytes = _braid_to_bytes(braid_secret)
        salt = os.urandom(16)
        ks = _keystream(analysis_key, salt, len(braid_bytes))
        enc_braid = bytes(b ^ k for b, k in zip(braid_bytes, ks))
        return {
            "message": message.hex(),
            "pub": self.pub.hex(),
            "signature": sig.hex(),
            "enc_braid": enc_braid.hex(),
            "salt": salt.hex(),
            "braid_commit": hashlib.sha256(braid_bytes).hexdigest(),
        }

    # -- ordinary signature verification ----------------------------------
    @staticmethod
    def verify(sig_obj: dict) -> bool:
        return ed.verify(bytes.fromhex(sig_obj["signature"]),
                         bytes.fromhex(sig_obj["message"]),
                         bytes.fromhex(sig_obj["pub"]))

    # -- CRYPTANALYSIS: decrypt the embedded secret -----------------------
    @staticmethod
    def cryptanalyze(sig_obj: dict, analysis_key: str) -> dict:
        """Attempt to recover the concealed braid with ``analysis_key``.

        Returns {"ok": True, "braid": [...]} on success (the commitment
        matches), else {"ok": False}.
        """
        salt = bytes.fromhex(sig_obj["salt"])
        enc = bytes.fromhex(sig_obj["enc_braid"])
        ks = _keystream(analysis_key, salt, len(enc))
        braid_bytes = bytes(c ^ k for c, k in zip(enc, ks))
        if hashlib.sha256(braid_bytes).hexdigest() != sig_obj["braid_commit"]:
            return {"ok": False}
        try:
            braid = _braid_from_bytes(braid_bytes)
        except ValueError:
            return {"ok": False}
        return {"ok": True, "braid": braid}

    @classmethod
    def cryptanalyze_bruteforce(cls, sig_obj: dict, candidates) -> dict:
        """Demonstrate breaking a weak/escrowed analysis key by searching a
        small candidate space (e.g. PINs '0000'..'9999')."""
        tried = 0
        for cand in candidates:
            tried += 1
            res = cls.cryptanalyze(sig_obj, str(cand))
            if res["ok"]:
                res["tried"] = tried
                res["key"] = str(cand)
                return res
        return {"ok": False, "tried": tried}
