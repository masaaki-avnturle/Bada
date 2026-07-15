"""The scanner: walk a path, characterise each file, report detections.

Read-only.  The scanner never modifies files -- removal/neutralisation is a
separate, explicit step handled by :mod:`quarantine`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from . import fingerprint
from .signatures import SignatureDB


@dataclass
class Detection:
    path: str
    threat: str
    kind: str            # "signature" | "pattern" | "jones" | "heuristic"
    severity: str        # "malicious" | "suspicious"
    sha256: str = ""
    reasons: list = field(default_factory=list)

    def line(self) -> str:
        tag = "!!" if self.severity == "malicious" else "??"
        extra = f"  ({', '.join(self.reasons)})" if self.reasons else ""
        return f"[{tag}] {self.severity:9} {self.threat:20} {self.path}{extra}"


# Skip anything bigger than this (avoid reading huge media/VM files fully).
DEFAULT_MAX_BYTES = 64 * 1024 * 1024


def scan_file(path: str, db: SignatureDB, max_bytes: int = DEFAULT_MAX_BYTES):
    """Return a Detection for ``path`` or None if it looks clean."""
    try:
        if not os.path.isfile(path) or os.path.islink(path):
            return None
        size = os.path.getsize(path)
        if size > max_bytes:
            return None
        with open(path, "rb") as f:
            data = f.read()
    except (OSError, PermissionError):
        return None

    sha = fingerprint.sha256_of_bytes(data)

    # 1) exact known-bad hash
    name = db.match_hash(sha)
    if name:
        return Detection(path, name, "signature", "malicious", sha)

    # 2) content pattern (e.g. EICAR label)
    pats = db.match_patterns(data)
    if pats:
        return Detection(path, pats[0], "pattern", "malicious", sha)

    # 3) fuzzy structural (Jones) fingerprint
    fp = fingerprint.jones_fingerprint(data)
    jname = db.match_jones(fp)
    if jname:
        return Detection(path, jname, "jones", "malicious", sha, [f"jones-fp={fp}"])

    # 4) heuristics -> suspicious (needs human review, not a confirmed threat)
    flags = fingerprint.heuristic_flags(data)
    if flags:
        return Detection(path, "Heuristic.Suspicious", "heuristic", "suspicious", sha, flags)

    return None


def scan_path(path: str, db: SignatureDB, recursive: bool = True,
              max_bytes: int = DEFAULT_MAX_BYTES):
    """Scan a file or directory. Returns (detections, files_scanned)."""
    detections = []
    scanned = 0
    if os.path.isfile(path):
        scanned = 1
        d = scan_file(path, db, max_bytes)
        return ([d] if d else [], scanned)

    for root, dirs, files in os.walk(path):
        # don't descend into a quarantine store if it sits under the scan root
        dirs[:] = [d for d in dirs if d != "_omega_quarantine"]
        for fn in files:
            fp = os.path.join(root, fn)
            scanned += 1
            d = scan_file(fp, db, max_bytes)
            if d:
                detections.append(d)
        if not recursive:
            break
    return (detections, scanned)
