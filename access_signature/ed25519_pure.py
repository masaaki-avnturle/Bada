"""Pure-Python Ed25519 (RFC 8032) — stdlib only.

A self-contained implementation of the Ed25519 signature scheme so the
gatekeeper has real asymmetric digital signatures without any third-party
package (the environment's ``cryptography`` wheel is unavailable).  Based on
the public-domain reference implementation by Daniel J. Bernstein et al.

Public API:
    publickey(seed32) -> pub32
    sign(message, seed32, pub32) -> sig64
    verify(sig64, message, pub32) -> bool
"""

from __future__ import annotations

import hashlib

b = 256
q = 2 ** 255 - 19
ell = 2 ** 252 + 27742317777372353535851937790883648493


def _H(m: bytes) -> bytes:
    return hashlib.sha512(m).digest()


def _inv(x: int) -> int:
    return pow(x, q - 2, q)


d = (-121665 * _inv(121666)) % q
I = pow(2, (q - 1) // 4, q)


def _xrecover(y: int) -> int:
    xx = (y * y - 1) * _inv(d * y * y + 1)
    x = pow(xx, (q + 3) // 8, q)
    if (x * x - xx) % q != 0:
        x = (x * I) % q
    if x % 2 != 0:
        x = q - x
    return x


By = (4 * _inv(5)) % q
Bx = _xrecover(By)
B = [Bx % q, By % q]


def _edwards(P, Q):
    x1, y1 = P
    x2, y2 = Q
    x3 = (x1 * y2 + x2 * y1) * _inv(1 + d * x1 * x2 * y1 * y2)
    y3 = (y1 * y2 + x1 * x2) * _inv(1 - d * x1 * x2 * y1 * y2)
    return [x3 % q, y3 % q]


def _scalarmult(P, e: int):
    # iterative double-and-add (avoids deep recursion)
    Q = [0, 1]            # neutral element
    while e > 0:
        if e & 1:
            Q = _edwards(Q, P)
        P = _edwards(P, P)
        e >>= 1
    return Q


def _bit(h: bytes, i: int) -> int:
    return (h[i // 8] >> (i % 8)) & 1


def _encodeint(y: int) -> bytes:
    return bytes((y >> (8 * i)) & 0xFF for i in range(b // 8))


def _encodepoint(P) -> bytes:
    x, y = P
    bits = [(y >> i) & 1 for i in range(b - 1)] + [x & 1]
    return bytes(sum(bits[i * 8 + j] << j for j in range(8))
                 for i in range(b // 8))


def _decodeint(s: bytes) -> int:
    return sum(2 ** i * _bit(s, i) for i in range(b))


def _isoncurve(P) -> bool:
    x, y = P
    return (-x * x + y * y - 1 - d * x * x * y * y) % q == 0


def _decodepoint(s: bytes):
    y = sum(2 ** i * _bit(s, i) for i in range(b - 1))
    x = _xrecover(y)
    if x & 1 != _bit(s, b - 1):
        x = q - x
    P = [x, y]
    if not _isoncurve(P):
        raise ValueError("decoding point that is not on curve")
    return P


def _secret_scalar(seed: bytes):
    h = _H(seed)
    a = 2 ** (b - 2) + sum(2 ** i * _bit(h, i) for i in range(3, b - 2))
    return a, h


def publickey(seed: bytes) -> bytes:
    a, _ = _secret_scalar(seed)
    return _encodepoint(_scalarmult(B, a))


def _Hint(m: bytes) -> int:
    h = _H(m)
    return sum(2 ** i * _bit(h, i) for i in range(2 * b))


def sign(message: bytes, seed: bytes, pub: bytes) -> bytes:
    a, h = _secret_scalar(seed)
    r = _Hint(h[b // 8:b // 4] + message)
    R = _scalarmult(B, r)
    S = (r + _Hint(_encodepoint(R) + pub + message) * a) % ell
    return _encodepoint(R) + _encodeint(S)


def verify(signature: bytes, message: bytes, pub: bytes) -> bool:
    try:
        if len(signature) != b // 4 or len(pub) != b // 8:
            return False
        R = _decodepoint(signature[:b // 8])
        A = _decodepoint(pub)
        S = _decodeint(signature[b // 8:b // 4])
        h = _Hint(_encodepoint(R) + pub + message)
        return _scalarmult(B, S) == _edwards(R, _scalarmult(A, h))
    except (ValueError, IndexError):
        return False
