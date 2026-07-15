"""Quarantine: neutralise a detected file by locking (encrypting) it away.

This is where the "quantum decryption app" and the "virus removal app" meet:
quarantining a threat *encrypts* it so it can no longer execute, and restoring
it *decrypts* it back.  Removal permanently deletes the locked copy.

Crypto note (honest): neutralisation uses a keyed SHA-256 counter-mode
keystream XOR plus an HMAC-SHA256 integrity tag -- all from the Python standard
library, so it works unchanged inside the Windows .exe and the Android .apk
with no native dependencies.  The goal is to render a quarantined file inert
and losslessly restorable, not to provide AES-grade confidentiality; the random
per-file key is stored in the manifest because the user must always be able to
restore.  (The separate omega_jones_crypto_pkg provides real AES-256-GCM for
callers who want it on desktop.)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass


def _keystream(key: bytes, n: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < n:
        out += hashlib.sha256(key + counter.to_bytes(8, "big")).digest()
        counter += 1
    return bytes(out[:n])


def _xor(key: bytes, data: bytes) -> bytes:
    ks = _keystream(key, len(data))
    return bytes(a ^ b for a, b in zip(data, ks))


def _tag(key: bytes, data: bytes) -> str:
    return hmac.new(key, data, hashlib.sha256).hexdigest()


@dataclass
class QuarantineItem:
    qid: str
    original_path: str
    threat: str
    severity: str
    sha256: str
    key_hex: str
    hmac_hex: str
    size: int


class Quarantine:
    def __init__(self, store_dir: str):
        self.dir = os.path.abspath(store_dir)
        os.makedirs(self.dir, exist_ok=True)
        self.manifest_path = os.path.join(self.dir, "manifest.json")

    # -- manifest -------------------------------------------------------
    def _load(self) -> list:
        if not os.path.exists(self.manifest_path):
            return []
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, items: list) -> None:
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)

    def list_items(self) -> list:
        return [QuarantineItem(**it) for it in self._load()]

    # -- quarantine (lock away) ----------------------------------------
    def quarantine(self, detection) -> QuarantineItem:
        """Encrypt the detected file into the store and remove the original."""
        path = detection.path
        with open(path, "rb") as f:
            data = f.read()
        key = secrets.token_bytes(32)
        blob = _xor(key, data)
        qid = secrets.token_hex(8)
        with open(os.path.join(self.dir, qid + ".bin"), "wb") as f:
            f.write(blob)

        item = QuarantineItem(
            qid=qid,
            original_path=os.path.abspath(path),
            threat=detection.threat,
            severity=detection.severity,
            sha256=detection.sha256,
            key_hex=key.hex(),
            hmac_hex=_tag(key, data),
            size=len(data),
        )
        items = self._load()
        items.append(item.__dict__)
        self._save(items)

        # Neutralise the original: overwrite then unlink so it cannot run.
        try:
            with open(path, "r+b") as f:
                f.write(b"\x00" * len(data))
                f.flush()
                os.fsync(f.fileno())
        except OSError:
            pass
        os.remove(path)
        return item

    # -- restore (unlock / decrypt) ------------------------------------
    def restore(self, qid: str, dest: str = None) -> str:
        items = self._load()
        rec = next((it for it in items if it["qid"] == qid), None)
        if rec is None:
            raise KeyError(f"no quarantine item {qid}")
        blob_path = os.path.join(self.dir, qid + ".bin")
        with open(blob_path, "rb") as f:
            blob = f.read()
        key = bytes.fromhex(rec["key_hex"])
        data = _xor(key, blob)
        if not hmac.compare_digest(_tag(key, data), rec["hmac_hex"]):
            raise ValueError("integrity check failed; refusing to restore")
        target = dest or rec["original_path"]
        os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
        with open(target, "wb") as f:
            f.write(data)
        os.remove(blob_path)
        self._save([it for it in items if it["qid"] != qid])
        return target

    # -- remove (delete permanently) -----------------------------------
    def remove(self, qid: str) -> None:
        items = self._load()
        if not any(it["qid"] == qid for it in items):
            raise KeyError(f"no quarantine item {qid}")
        blob_path = os.path.join(self.dir, qid + ".bin")
        if os.path.exists(blob_path):
            os.remove(blob_path)
        self._save([it for it in items if it["qid"] != qid])
