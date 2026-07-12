"""GUI-agnostic controller for the Windows/Android app.

All the real work lives here as pure functions that return plain text, so the
Kivy front-end (main.py) stays a thin shell and the logic is unit-testable
without a display server.
"""

from __future__ import annotations

import os
import sys

# Make ``omega_qdecrypt`` importable whether we run from source, from a
# PyInstaller bundle, or from an Android (buildozer) package.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from omega_qdecrypt import jones, rsa_toy, shor          # noqa: E402
from omega_qdecrypt.matrix import PolyMatrix, inverse_exists  # noqa: E402
from omega_qdecrypt.pipeline import run_pipeline          # noqa: E402


def _fmt_report(rep) -> str:
    lines = []
    for step in rep.steps:
        step = dict(step)
        lines.append(f"=== {step.pop('title')} ===")
        for k, v in step.items():
            lines.append(f"  {k}: {v}")
        lines.append("")
    if rep.success:
        lines.append(f">>> SOLVED: {rep.plaintext.decode('utf-8', 'replace')!r}")
    else:
        lines.append(">>> not solved.")
    return "\n".join(lines)


def demo_solve(message: str = "", braid_spec: str = "3: 1 1 1") -> str:
    """Encrypt a secret into a toy-RSA 'USB stick', then break it end-to-end."""
    secret = message.strip() or "MASAAKI-YAMAGUCHI/JONES-MANIFOLD/USB"
    pub, _ = rsa_toy.make_keypair()
    cipher = rsa_toy.encrypt(secret, pub)
    braid = jones.parse_braid(braid_spec)
    header = (
        f"[+] encrypted target (RSA pub e,N={pub})\n"
        f"    cipher blocks: {cipher[:6]}{'...' if len(cipher) > 6 else ''}\n"
    )
    rep = run_pipeline(braid, {"cipher": cipher, "pub": pub}, true_braid=braid)
    return header + "\n" + _fmt_report(rep)


def jones_report(braid_spec: str = "2: 1 1 1") -> str:
    n, word = jones.parse_braid(braid_spec)
    B = jones.burau_of_braid(n, word)
    inv = inverse_exists(B)
    return (
        f"strands: {n}   word: {word}   writhe: {jones.writhe(word)}\n"
        f"Kauffman bracket <D>(A): {jones.kauffman_bracket(n, word)}\n"
        f"normalized f_L(A)      : {jones.jones_bracket_normalized(n, word)}\n"
        f"Jones V_L(t) at t=1.3  : {jones.jones_value(n, word, 1.3):.6f}\n"
        f"det(B) = {inv['det']}  -> inverse exists: {inv['invertible_ring']}\n"
        f"32-byte key: {jones.derive_key(n, word).hex()}"
    )


def crack_report(N: int, e: int, cipher_csv: str = "") -> str:
    broken = shor.break_rsa(int(N), int(e))
    if broken is None:
        return f"[-] Shor simulation could not factor N={N}."
    d, p, q = broken
    out = [f"[+] Shor factored N={N} = {p} * {q}", f"[+] recovered d = {d}"]
    csv = cipher_csv.strip()
    if csv:
        blocks = [int(x) for x in csv.replace(" ", "").split(",") if x]
        pt = rsa_toy.decrypt(blocks, (d, int(N)))
        out.append(f"[+] plaintext = {pt.decode('utf-8', 'replace')!r}")
    return "\n".join(out)
