"""有限の高さ T までのリーマン予想の数値検証と、RH と同値な不等式の検査。

論理 (古典的な検証法):
  (A) 臨界線上で Z(t) の符号変化を数える        → 線上の零点の個数の下界
  (B) 偏角の原理で N(T) = θ(T)/π + 1 + S(T) を計算 → 帯領域内の零点の総数
  (A) = (B) なら 0 < Im ρ < T の全零点が Re ρ = 1/2 上にあり、かつ単純。
"""

from __future__ import annotations

import cmath
import math

from .zeta import zeta, theta, hardy_z


def _spacing(t: float) -> float:
    return 2 * math.pi / math.log(max(t, 14.0) / (2 * math.pi))


def scan_sign_changes(T: float, density: int = 6) -> list[tuple[float, float]]:
    """Brackets (a, b) with Z(a)·Z(b) < 0 for 0 < t < T."""
    out = []
    a, za = 1.0, hardy_z(1.0)
    while a < T:
        b = min(a + _spacing(a) / density, T)
        zb = hardy_z(b)
        if za * zb < 0:
            out.append((a, b))
        a, za = b, zb
    return out


def refine_zero(a: float, b: float, iters: int = 60) -> float:
    fa = hardy_z(a)
    for _ in range(iters):
        m = (a + b) / 2
        fm = hardy_z(m)
        if fa * fm <= 0:
            b = m
        else:
            a, fa = m, fm
    return (a + b) / 2


def arg_zeta(T: float) -> float:
    """arg ζ(1/2+iT) by continuous variation along the segment from 4+iT.

    At σ = 4, |ζ − 1| <= ζ(4) − 1 < 0.083, so the principal argument is the
    correct starting value.
    """
    sigma = 4.0
    z = zeta(complex(sigma, T))
    arg = cmath.phase(z)
    step = 0.05
    while sigma > 0.5:
        nxt = max(sigma - step, 0.5)
        z2 = zeta(complex(nxt, T))
        d = cmath.phase(z2 / z)
        if abs(d) > 0.3 and step > 1e-6:
            step /= 2
            continue
        arg += d
        sigma, z = nxt, z2
        step = min(step * 1.5, 0.05)
    return arg


def zero_count(T: float) -> tuple[int, float]:
    """(N(T), residual): zeros with 0 < Im ρ < T, and distance from an integer."""
    n = theta(T) / math.pi + 1 + arg_zeta(T) / math.pi
    return round(n), abs(n - round(n))


def verify_rh_to_height(T: float = 500.0, list_zeros: int = 10) -> dict:
    expected, residual = zero_count(T)
    density, brackets = 6, []
    while density <= 96:
        brackets = scan_sign_changes(T, density)
        if len(brackets) >= expected:
            break
        density *= 2
    found = len(brackets)
    ok = found == expected and residual < 1e-3
    return {
        "claim": f"0 < Im ρ < {T:g} の ζ の非自明零点はすべて Re ρ = 1/2 上にあり単純",
        "height": T,
        "zeros_in_strip_argument_principle": expected,
        "argument_principle_residual": residual,
        "zeros_on_critical_line_sign_changes": found,
        "scan_density": density,
        "first_zeros": [round(refine_zero(a, b), 9) for a, b in brackets[:list_zeros]],
        "status": "verified" if ok else "inconclusive",
    }


def schoenfeld_check(X: int = 10 ** 6) -> dict:
    """Schoenfeld (1976): RH ⇔ |ψ(x) − x| < √x·log²x / (8π) for all x >= 73.2.

    Checked for every real x in [74, X] (the extremes of ψ(x) − x on [n, n+1)
    occur at x = n and x → n+1).
    """
    sieve = bytearray([1]) * (X + 1)
    sieve[0:2] = b"\x00\x00"
    for p in range(2, math.isqrt(X) + 1):
        if sieve[p]:
            sieve[p * p::p] = bytearray(len(range(p * p, X + 1, p)))
    lam = [0.0] * (X + 1)
    for p in range(2, X + 1):
        if sieve[p]:
            lp, q = math.log(p), p
            while q <= X:
                lam[q] = lp
                q *= p
    psi, worst, worst_x, ok = 0.0, 0.0, 0, True
    c = 1 / (8 * math.pi)
    for n in range(1, X):
        psi += lam[n]
        if n < 74:
            continue
        ln = math.log(n)
        bound = c * math.sqrt(n) * ln * ln
        r = max(abs(psi - n), abs(psi - (n + 1))) / bound
        if r > worst:
            worst, worst_x = r, n
        if r >= 1:
            ok = False
    return {
        "claim": f"|ψ(x) − x| < √x·log²x/(8π)  (74 <= x <= {X})",
        "limit": X,
        "max_ratio": worst,
        "max_ratio_at": worst_x,
        "status": "verified" if ok else "disproved",
    }
