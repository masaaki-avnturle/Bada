"""Signature authority — the owner's Ed25519 key pair (pure-Python).

Real asymmetric digital signatures: only the holder of the private seed (the
repository owner) can *issue* a valid credential, and anyone can *verify* one
with the public key.  This is what lets us hand an approved person a
"digital-signature password" that proves the owner authorised them, without
sharing any secret.

The private seed is stored owner-readable only; if
``ACCESS_SIGNATURE_KEY_PASSPHRASE`` is set it is additionally encrypted at rest
with an scrypt-derived keystream.
"""

from __future__ import annotations

import hashlib
import os
import secrets

from . import ed25519_pure as ed

_PASS_ENV = "ACCESS_SIGNATURE_KEY_PASSPHRASE"


def _maybe_encrypt(seed: bytes) -> str:
    passphrase = os.environ.get(_PASS_ENV)
    if not passphrase:
        return "raw:" + seed.hex()
    salt = secrets.token_bytes(16)
    keystream = hashlib.scrypt(passphrase.encode(), salt=salt, n=2 ** 14,
                               r=8, p=1, dklen=len(seed))
    enc = bytes(a ^ b for a, b in zip(seed, keystream))
    return "enc:" + salt.hex() + ":" + enc.hex()


def _maybe_decrypt(blob: str) -> bytes:
    kind, _, rest = blob.partition(":")
    if kind == "raw":
        return bytes.fromhex(rest)
    salt_hex, _, enc_hex = rest.partition(":")
    passphrase = os.environ.get(_PASS_ENV)
    if not passphrase:
        raise ValueError(f"{_PASS_ENV} required to decrypt the private key")
    salt = bytes.fromhex(salt_hex)
    enc = bytes.fromhex(enc_hex)
    keystream = hashlib.scrypt(passphrase.encode(), salt=salt, n=2 ** 14,
                               r=8, p=1, dklen=len(enc))
    return bytes(a ^ b for a, b in zip(enc, keystream))


class SignatureAuthority:
    def __init__(self, seed: bytes):
        self._seed = seed
        self._pub = ed.publickey(seed)

    # -- creation / loading ------------------------------------------------
    @classmethod
    def generate(cls) -> "SignatureAuthority":
        return cls(secrets.token_bytes(32))

    @classmethod
    def load(cls, key_path: str) -> "SignatureAuthority":
        with open(key_path) as f:
            return cls(_maybe_decrypt(f.read().strip()))

    def save(self, key_path: str):
        fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(_maybe_encrypt(self._seed))

    # -- key material ------------------------------------------------------
    def public_pem(self) -> str:
        """Public key as hex (the verifier's material)."""
        return self._pub.hex()

    # -- sign --------------------------------------------------------------
    def sign(self, message: str) -> str:
        return ed.sign(message.encode(), self._seed, self._pub).hex()


def verify(public_hex: str, message: str, signature_hex: str) -> bool:
    """Verify a signature with a public key. Safe (never raises)."""
    if not public_hex:
        return False
    try:
        return ed.verify(bytes.fromhex(signature_hex), message.encode(),
                         bytes.fromhex(public_hex))
    except (ValueError, TypeError):
        return False
