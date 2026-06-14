"""
omega_qkd.py — Jones / Kauffman knot-theory key derivation.

This is a faithful pure-Python port of ``omega_jones_crypto_pkg/lib/jones_key.c``
so that a 32-byte master key derived here from a knot diagram is byte-for-byte
identical to the one produced by the original "quantum cryptography" C tool.

The diagram file IS the shared secret: two parties can only establish a session
if they both possess the same knot diagram (shared out-of-band). Without it the
session handshake's mutual authentication fails — this is the cryptographic
consent gate of the collaboration system.
"""
from __future__ import annotations

import hashlib
import hmac
import struct
from typing import List, Tuple


# ---------------------------------------------------------------------------
#  Diagram parsing
# ---------------------------------------------------------------------------
class Crossing:
    __slots__ = ("id", "e", "sign")

    def __init__(self, cid: int, e: Tuple[int, int, int, int], sign: int):
        self.id = cid
        self.e = e
        self.sign = 1 if sign >= 0 else -1


def load_diagram(path: str) -> List[Crossing]:
    """Parse a knot diagram: lines of `id e0 e1 e2 e3 sign`, `#` = comment."""
    out: List[Crossing] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            parts = s.split()
            if len(parts) < 6:
                continue
            cid, a0, a1, a2, a3, sg = (int(x) for x in parts[:6])
            out.append(Crossing(cid, (a0, a1, a2, a3), sg))
    return out


# ---------------------------------------------------------------------------
#  Kauffman bracket (union-find loop counting), matching the C implementation
# ---------------------------------------------------------------------------
class _UF:
    def __init__(self, n: int):
        self.p = [-1] * max(n, 1)

    def find(self, a: int) -> int:
        while self.p[a] >= 0:
            # path halving
            if self.p[self.p[a]] >= 0:
                self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a: int, b: int) -> None:
        a, b = self.find(a), self.find(b)
        if a == b:
            return
        if self.p[a] < self.p[b]:
            self.p[a] += self.p[b]
            self.p[b] = a
        else:
            self.p[b] += self.p[a]
            self.p[a] = b


def compute_kauffman_bracket(cross: List[Crossing], A: float) -> float:
    n = len(cross)
    if n == 0:
        return 1.0
    maxlbl = 0
    for c in cross:
        maxlbl = max(maxlbl, *c.e)
    U = maxlbl + 1
    d = -(A * A) - 1.0 / (A * A)
    total = 0.0
    for s in range(1 << n):
        uf = _UF(U)
        a_cnt = b_cnt = 0
        for i, c in enumerate(cross):
            if (s >> i) & 1 == 0:
                uf.union(c.e[0], c.e[1])
                uf.union(c.e[2], c.e[3])
                a_cnt += 1
            else:
                uf.union(c.e[1], c.e[2])
                uf.union(c.e[3], c.e[0])
                b_cnt += 1
        seen = [False] * U
        loops = 0
        for lbl in range(U):
            r = uf.find(lbl)
            if not seen[r]:
                seen[r] = True
                loops += 1
        exp = a_cnt - b_cnt
        weight = A ** exp
        loops_factor = d ** (loops - 1 if loops > 0 else 0)
        total += weight * loops_factor
    return total


def derive_key_from_diagram(path: str) -> bytes:
    """Return the 32-byte master key for a knot diagram (== the C tool's key)."""
    cs = load_diagram(path)
    a_values = (0.8, 1.0, 1.2, 1.5, 2.0)
    samples = [compute_kauffman_bracket(cs, a) for a in a_values]
    # Replicate C: 160-byte buffer, IEEE754 little-endian doubles at offset i*8.
    buf = bytearray(5 * 32)
    for i, v in enumerate(samples):
        struct.pack_into("<d", buf, i * 8, v)
    return hashlib.sha256(bytes(buf)).digest()


# ---------------------------------------------------------------------------
#  HKDF-SHA256 (RFC 5869) — session key schedule
# ---------------------------------------------------------------------------
def hkdf(ikm: bytes, salt: bytes, info: bytes, length: int) -> bytes:
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    okm = b""
    t = b""
    counter = 1
    while len(okm) < length:
        t = hmac.new(prk, t + info + bytes([counter]), hashlib.sha256).digest()
        okm += t
        counter += 1
    return okm[:length]


def fingerprint(key: bytes) -> str:
    """Short human-verifiable fingerprint of a key (for out-of-band check)."""
    h = hashlib.sha256(key).hexdigest()[:16].upper()
    return "-".join(h[i:i + 4] for i in range(0, 16, 4))


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("usage: python omega_qkd.py <diagram.knot>")
        raise SystemExit(2)
    k = derive_key_from_diagram(sys.argv[1])
    print("master key :", k.hex())
    print("fingerprint:", fingerprint(k))
