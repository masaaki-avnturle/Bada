"""Jones-polynomial quantum cipher.

The key is seeded by a topological quantum invariant: the canonical Kauffman
bracket / Jones polynomial of a secret braid (whose evaluation at a root of
unity is what a quantum computer approximates — AJL).  Encryption is an
HMAC-SHA256 counter-mode keystream over that key (stdlib only).
"""

from __future__ import annotations

import hashlib
import hmac
import os

from .jones import jones_polynomial, jones_str, normalized_bracket


def braid_key(braid: list[int], n: int | None = None) -> bytes:
    """Derive a 32-byte key from the braid's Jones invariant (reproducible)."""
    canon = normalized_bracket(braid, n).canonical()      # exact integer poly
    material = "jones-qkd|" + ";".join(f"{e}:{v}" for e, v in canon)
    return hashlib.sha256(material.encode()).digest()


class JonesQuantumCipher:
    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("key must be 32 bytes")
        self.key = key

    @classmethod
    def from_braid(cls, braid: list[int], n: int | None = None
                   ) -> "JonesQuantumCipher":
        return cls(braid_key(braid, n))

    # -- keystream ---------------------------------------------------------
    def _keystream(self, nbytes: int, nonce: bytes) -> bytes:
        out = bytearray()
        counter = 0
        while len(out) < nbytes:
            block = hmac.new(self.key, nonce + counter.to_bytes(8, "big"),
                             hashlib.sha256).digest()
            out.extend(block)
            counter += 1
        return bytes(out[:nbytes])

    # -- encrypt / decrypt -------------------------------------------------
    def encrypt(self, plaintext: bytes, nonce: bytes | None = None) -> bytes:
        nonce = nonce or os.urandom(16)
        ks = self._keystream(len(plaintext), nonce)
        ct = bytes(p ^ k for p, k in zip(plaintext, ks))
        tag = hmac.new(self.key, b"tag|" + nonce + ct, hashlib.sha256).digest()
        return nonce + tag + ct           # 16 + 32 + len

    def decrypt(self, blob: bytes) -> bytes:
        nonce, tag, ct = blob[:16], blob[16:48], blob[48:]
        expect = hmac.new(self.key, b"tag|" + nonce + ct,
                          hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expect):
            raise ValueError("authentication failed (wrong Jones key?)")
        ks = self._keystream(len(ct), nonce)
        return bytes(c ^ k for c, k in zip(ct, ks))

    def fingerprint(self) -> str:
        return hashlib.sha256(self.key).hexdigest()[:16]


def describe_braid(braid: list[int], n: int | None = None) -> dict:
    return {
        "braid": braid,
        "jones": jones_str(braid, n),
        "jones_terms": jones_polynomial(braid, n),
        "key_fingerprint": JonesQuantumCipher.from_braid(braid, n).fingerprint(),
    }
