"""深リーマン予想 (Deep Riemann Hypothesis, 黒川・木村・小山) の数値的証拠。

DRH: 非自明な Dirichlet 指標 χ と Re s = 1/2 (L(s,χ) != 0) に対し

    lim_{x→∞} Π_{p<=x} (1 − χ(p) p^{-s})^{-1} = L(s,χ) · c,
    c = √2  (s = 1/2 かつ χ² = 1),   c = 1  (それ以外)。

オイラー積は Re s > 1 でしか絶対収束しないので、臨界線上での収束は RH より
強い主張である。ここでは有限の x までの部分積を極限値と比較する。
"""

from __future__ import annotations

import cmath
import math

from .zeta import dirichlet_l

CHARACTERS: dict[str, list[complex]] = {
    "chi_-4": [0, 1, 0, -1],
    "chi_-3": [0, 1, -1],
    "chi_5": [0, 1, -1, -1, 1],
    "chi_5_complex": [0, 1, 1j, -1j, -1],
}


def primes_upto(n: int) -> list[int]:
    sieve = bytearray([1]) * (n + 1)
    sieve[0:2] = b"\x00\x00"
    for p in range(2, math.isqrt(n) + 1):
        if sieve[p]:
            sieve[p * p::p] = bytearray(len(range(p * p, n + 1, p)))
    return [i for i in range(2, n + 1) if sieve[i]]


def drh_evidence(name: str = "chi_-4", t: float = 0.0, X: int = 10 ** 6) -> dict:
    chi = CHARACTERS[name]
    q = len(chi)
    s = complex(0.5, t)
    is_real = all(complex(c).imag == 0 for c in chi)
    factor = math.sqrt(2) if (t == 0 and is_real) else 1.0
    L = dirichlet_l(s, chi)
    target = L * factor
    checkpoints = [10 ** k for k in range(2, 10) if 10 ** k <= X]
    if not checkpoints or checkpoints[-1] != X:
        checkpoints.append(X)
    rows, log_prod, i = [], 0j, 0
    primes = primes_upto(X)
    for x in checkpoints:
        while i < len(primes) and primes[i] <= x:
            p = primes[i]
            c = chi[p % q]
            if c != 0:
                log_prod -= cmath.log(1 - c * cmath.exp(-s * math.log(p)))
            i += 1
        prod = cmath.exp(log_prod)
        rows.append({
            "x": x,
            "partial_product": [prod.real, prod.imag],
            "rel_error_vs_DRH_limit": abs(prod - target) / abs(target),
            "rel_error_vs_plain_L": abs(prod - L) / abs(L),
        })
    return {
        "claim": f"Π_(p<=x)(1−χ(p)p^(−s))^(−1) → {'√2·' if factor != 1 else ''}L(s,χ),  χ={name}, s=1/2+{t:g}i",
        "character": name,
        "s": [0.5, t],
        "L": [L.real, L.imag],
        "sqrt2_factor": factor != 1.0,
        "drh_limit": [target.real, target.imag],
        "table": rows,
        "status": "open",
    }
