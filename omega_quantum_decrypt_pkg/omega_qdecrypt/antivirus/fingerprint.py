"""File fingerprints and heuristics used by the scanner.

Everything here is defensive: it *characterises* a file so the scanner can
decide whether it looks known-bad or suspicious.  Nothing here creates,
modifies, or executes anything.

Signals
-------
* SHA-256          -- exact content hash for signature matching.
* Shannon entropy  -- high entropy hints at packing/encryption (a classic AV
                      heuristic; benign compressed files also score high, so it
                      is only ever "suspicious", never "malicious").
* Jones fingerprint-- a short, deterministic structural hash built from the
                      file's byte-transition histogram via the project's own
                      Kauffman-bracket / Jones machinery.  It gives a fuzzy
                      structural signature that survives trivial byte changes.
"""

from __future__ import annotations

import hashlib
import math

from .. import jones


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_of_file(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def shannon_entropy(data: bytes) -> float:
    """Entropy in bits per byte (0..8)."""
    if not data:
        return 0.0
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    n = len(data)
    ent = 0.0
    for c in counts:
        if c:
            p = c / n
            ent -= p * math.log2(p)
    return ent


def jones_fingerprint(data: bytes) -> str:
    """Deterministic structural fingerprint of ``data``.

    We fold the byte stream into a small braid on 4 strands: consecutive bytes
    pick a generator index (1..3) and a sign, so the file's local byte
    transitions become crossings.  The Jones value of that braid's closure,
    evaluated at a fixed point, is hashed to a short hex tag.  Same structure
    -> same tag; small edits change it only locally.
    """
    if not data:
        return "0" * 12
    n_strands = 4
    word = []
    # Sample up to 4096 transitions to keep it fast on large files.
    step = max(1, len(data) // 4096)
    prev = data[0]
    for i in range(step, len(data), step):
        b = data[i]
        gen = 1 + (b % (n_strands - 1))        # 1..3
        sign = 1 if ((b ^ prev) & 1) == 0 else -1
        word.append(sign * gen)
        prev = b
    if not word:
        word = [1]
    # Cap the crossing count so the 2^c Kauffman state sum stays cheap.
    word = word[:18]
    try:
        val = jones.jones_value(n_strands, word, 1.3)
        real = float(getattr(val, "real", val))
        imag = float(getattr(val, "imag", 0.0))
    except Exception:
        real, imag = 0.0, 0.0
    payload = f"{len(data)}:{real:.6e}:{imag:.6e}".encode()
    return hashlib.sha256(payload).hexdigest()[:12]


# --- lightweight heuristic content rules (benign indicators only) ----------
# These are *indicators* often seen in obfuscated scripts.  Matching them marks
# a file "suspicious" for the user to review -- never a confirmed threat.
_SUSPICIOUS_TOKENS = [
    (b"powershell", b"-enc"),          # base64-encoded PowerShell command
    (b"powershell", b"-w hidden"),
    (b"FromBase64String", b"IEX"),
    (b"WScript.Shell", b"Run"),
    (b"cmd.exe", b"/c "),
    (b"eval(", b"base64_decode"),      # obfuscated PHP/JS
    (b"document.write(unescape", b""),
]


def heuristic_flags(data: bytes) -> list[str]:
    reasons = []
    low = data.lower()
    for a, b in _SUSPICIOUS_TOKENS:
        if a.lower() in low and (not b or b.lower() in low):
            label = a.decode("latin1") + ("+" + b.decode("latin1") if b else "")
            reasons.append(f"suspicious-token[{label}]")
    ent = shannon_entropy(data[: 1 << 20])
    if ent >= 7.5 and len(data) >= 2048:
        reasons.append(f"high-entropy[{ent:.2f}b/byte]")
    return reasons
