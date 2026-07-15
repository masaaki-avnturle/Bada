"""omega_qdecrypt.antivirus -- defensive malware scanner + quarantine.

A demo-grade, signature+heuristic scanner that detects known-bad files and
neutralises them by encrypting them into quarantine (restore = decrypt).  It is
NOT a replacement for a real antivirus and only detects what its signature DB
and heuristics cover.  It never creates, modifies, or executes malware.
"""

from . import fingerprint, quarantine, scanner, signatures  # noqa: F401
from .scanner import Detection, scan_file, scan_path  # noqa: F401
from .signatures import SignatureDB  # noqa: F401
from .quarantine import Quarantine, QuarantineItem  # noqa: F401

__all__ = [
    "fingerprint", "quarantine", "scanner", "signatures",
    "Detection", "scan_file", "scan_path",
    "SignatureDB", "Quarantine", "QuarantineItem",
]
