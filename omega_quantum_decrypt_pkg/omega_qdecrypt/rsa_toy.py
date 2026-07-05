"""A toy RSA scheme used to manufacture a decryptable "secret data" target.

This exists so the application has something concrete to break end-to-end -- an
"encrypted USB stick" in the language of secretdata.pdf.  Keys are deliberately
small so that the classical Shor simulation in :mod:`shor` can factor the
modulus in well under a second.  Do not use this for anything real.
"""

from __future__ import annotations

from .shor import _gcd, rsa_transform


# A handful of small primes; pairs give ~20-30 bit moduli that Shor factors
# quickly in simulation while still being genuine RSA.
_SMALL_PRIMES = [
    1009, 1013, 1019, 1021, 3001, 3011, 5003, 5009, 7001, 7013,
    10007, 10009, 12007, 12011, 15013, 15017,
]


def make_keypair(p=None, q=None, e=65537):
    """Return ``(pub, priv)`` = ``((e, N), (d, N))``."""
    if p is None:
        p, q = 10007, 12011
    N = p * q
    phi = (p - 1) * (q - 1)
    if _gcd(e, phi) != 1:
        e = 17
        while _gcd(e, phi) != 1:
            e += 2
    d = pow(e, -1, phi)
    return (e, N), (d, N)


def _bytes_to_blocks(data, N):
    """Pack bytes into integers < N (one byte per block keeps it simple and
    always valid regardless of modulus size)."""
    return list(data)


def _blocks_to_bytes(blocks):
    return bytes(b & 0xFF for b in blocks)


def encrypt(message, pub):
    e, N = pub
    if isinstance(message, str):
        message = message.encode("utf-8")
    return [rsa_transform(m, e, N) for m in _bytes_to_blocks(message, N)]


def decrypt(cipher_blocks, priv):
    d, N = priv
    return _blocks_to_bytes(rsa_transform(c, d, N) for c in cipher_blocks)
