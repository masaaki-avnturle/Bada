"""ζ(s), Hurwitz ζ(s,a), Dirichlet L(s,χ), Riemann–Siegel θ(t), Hardy Z(t).

Standard library only (double precision).  Everything rests on one routine:
the Euler–Maclaurin expansion of the Hurwitz zeta function, valid for all
complex s != 1.
"""

from __future__ import annotations

import cmath
import math
from fractions import Fraction

_M = 12  # Euler–Maclaurin correction terms


def _bernoulli_over_factorial(m: int) -> list[float]:
    """[B_2/2!, B_4/4!, ..., B_2m/(2m)!] computed exactly, then rounded."""
    B = [Fraction(1)]
    for n in range(1, 2 * m + 1):
        acc = Fraction(0)
        for k in range(n):
            acc += math.comb(n + 1, k) * B[k]
        B.append(-acc / (n + 1))
    return [float(B[2 * k] / math.factorial(2 * k)) for k in range(1, m + 1)]


_B2K = _bernoulli_over_factorial(_M)
_LOGS: list[float] = [0.0, 0.0]


def _logs(n: int) -> list[float]:
    while len(_LOGS) <= n:
        _LOGS.append(math.log(len(_LOGS)))
    return _LOGS


def hurwitz_zeta(s: complex, a: float = 1.0) -> complex:
    """ζ(s, a) = Σ_{n>=0} (n+a)^(-s), continued to all s != 1 (0 < a <= 1)."""
    s = complex(s)
    N = int(abs(s)) + 25
    if a == 1.0:
        L = _logs(N)
        total = sum(cmath.exp(-s * L[n]) for n in range(1, N))
        w = float(N)
    else:
        total = sum(cmath.exp(-s * math.log(n + a)) for n in range(N))
        w = N + a
    lw = math.log(w)
    w_s = cmath.exp(-s * lw)
    total += w_s * w / (s - 1) + w_s / 2
    # Σ B_2k/(2k)! · s(s+1)…(s+2k-2) · w^(-s-2k+1)
    poch = s
    power = w_s / w
    for k in range(1, _M + 1):
        total += _B2K[k - 1] * poch * power
        poch *= (s + 2 * k - 1) * (s + 2 * k)
        power /= w * w
    return total


def zeta(s: complex) -> complex:
    return hurwitz_zeta(s, 1.0)


def dirichlet_l(s: complex, chi: list[complex]) -> complex:
    """L(s,χ) for χ given as [χ(0), χ(1), …, χ(q-1)]  (s != 1)."""
    q = len(chi)
    s = complex(s)
    total = 0j
    for a in range(1, q + 1):
        c = chi[a % q]
        if c != 0:
            total += c * hurwitz_zeta(s, a / q)
    return total * cmath.exp(-s * math.log(q))


def loggamma(z: complex) -> complex:
    """log Γ(z) on the continuous branch, Re z > 0."""
    z = complex(z)
    shift = 0j
    while z.real < 15:
        shift += cmath.log(z)
        z += 1
    zi = 1 / z
    z2 = zi * zi
    series = zi * (1 / 12 - z2 * (1 / 360 - z2 * (1 / 1260 - z2 * (1 / 1680 - z2 / 1188))))
    return (z - 0.5) * cmath.log(z) - z + 0.5 * math.log(2 * math.pi) + series - shift


def theta(t: float) -> float:
    """Riemann–Siegel θ(t) = Im log Γ(1/4 + it/2) − (t/2) log π."""
    return loggamma(complex(0.25, t / 2)).imag - t / 2 * math.log(math.pi)


def hardy_z(t: float) -> float:
    """Hardy's Z(t) = e^{iθ(t)} ζ(1/2+it): real, and |Z(t)| = |ζ(1/2+it)|."""
    return (cmath.exp(1j * theta(t)) * zeta(complex(0.5, t))).real
