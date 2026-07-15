"""Signature database for the scanner.

Three signature kinds, all defensive:

* ``hashes``   -- SHA-256 of known-bad files -> threat name (exact match).
* ``patterns`` -- distinctive byte substrings -> threat name (content match).
* ``jones``    -- Jones structural fingerprints -> threat name (fuzzy match).

The built-in database ships only with the industry-standard **EICAR** test
signature.  EICAR is a deliberately harmless 68-byte string that every real
antivirus is designed to detect; it lets us prove the scanner works without any
actual malware.  Users extend the DB with their own hashes via JSON.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


# SHA-256 of the standard 68-byte EICAR test file.
EICAR_SHA256 = "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f"

# A harmless, distinctive fragment of the EICAR file (its human-readable label).
# This is only the label, not the functional test string.
EICAR_LABEL = b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE"


@dataclass
class SignatureDB:
    hashes: dict = field(default_factory=dict)     # sha256 hex -> name
    patterns: list = field(default_factory=list)   # (name, bytes)
    jones: dict = field(default_factory=dict)      # fingerprint -> name

    @staticmethod
    def default() -> "SignatureDB":
        return SignatureDB(
            hashes={EICAR_SHA256: "EICAR-Test-File"},
            patterns=[("EICAR-Test-File", EICAR_LABEL)],
            jones={},
        )

    # -- persistence ----------------------------------------------------
    def to_json(self) -> str:
        return json.dumps(
            {
                "hashes": self.hashes,
                "patterns": [[n, p.decode("latin1")] for n, p in self.patterns],
                "jones": self.jones,
            },
            indent=2,
        )

    @staticmethod
    def from_json(text: str) -> "SignatureDB":
        d = json.loads(text)
        return SignatureDB(
            hashes=dict(d.get("hashes", {})),
            patterns=[(n, p.encode("latin1")) for n, p in d.get("patterns", [])],
            jones=dict(d.get("jones", {})),
        )

    @staticmethod
    def load(path: str) -> "SignatureDB":
        with open(path, "r", encoding="utf-8") as f:
            return SignatureDB.from_json(f.read())

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    # -- editing --------------------------------------------------------
    def add_hash(self, sha256: str, name: str) -> None:
        self.hashes[sha256.lower()] = name

    def add_jones(self, fingerprint: str, name: str) -> None:
        self.jones[fingerprint] = name

    def merge(self, other: "SignatureDB") -> None:
        self.hashes.update(other.hashes)
        self.patterns.extend(other.patterns)
        self.jones.update(other.jones)

    # -- matching -------------------------------------------------------
    def match_hash(self, sha256: str):
        return self.hashes.get(sha256.lower())

    def match_patterns(self, data: bytes):
        hits = []
        for name, pat in self.patterns:
            if pat and pat in data:
                hits.append(name)
        return hits

    def match_jones(self, fingerprint: str):
        return self.jones.get(fingerprint)
