"""Jones polynomial via the Kauffman bracket state sum on braid closures.

The security report links RSA / quantum signatures to the Jones polynomial and
the non-commutative operator π(χ,x)=[iπ(χ,x), f(x)].  This module computes the
genuine topological invariant: given a braid word, it forms the braid closure,
runs the Kauffman-bracket state sum (resolving every crossing into its A- and
B-smoothings and counting loops with union-find), normalises by the writhe, and
returns the Jones polynomial V(t).

Approximating V(t) at a root of unity is BQP-complete (the Aharonov–Jones–Landau
algorithm) — that is the "quantum" in this quantum cryptography: the key is
seeded by a quantum-topological invariant.

Braid words: a list of non-zero ints; ``+i`` = generator σ_i, ``-i`` = σ_i⁻¹
(positions are 1-indexed; strand count n defaults to max|gen|+1).
"""

from __future__ import annotations

import cmath
import math

# ---------------------------------------------------------------------------
# Laurent polynomials in A (exponent -> integer coefficient)
# ---------------------------------------------------------------------------
class Laurent:
    __slots__ = ("c",)

    def __init__(self, coeffs: dict | None = None):
        self.c = {e: v for e, v in (coeffs or {}).items() if v != 0}

    @classmethod
    def mono(cls, exp: int, coeff: int = 1) -> "Laurent":
        return cls({exp: coeff})

    def __add__(self, other: "Laurent") -> "Laurent":
        out = dict(self.c)
        for e, v in other.c.items():
            out[e] = out.get(e, 0) + v
        return Laurent(out)

    def __mul__(self, other: "Laurent") -> "Laurent":
        out: dict = {}
        for e1, v1 in self.c.items():
            for e2, v2 in other.c.items():
                out[e1 + e2] = out.get(e1 + e2, 0) + v1 * v2
        return Laurent(out)

    def scale(self, k: int) -> "Laurent":
        return Laurent({e: v * k for e, v in self.c.items()})

    def pow(self, n: int) -> "Laurent":
        result = Laurent({0: 1})
        base = self
        if n < 0:
            raise ValueError("negative powers unsupported here")
        while n:
            if n & 1:
                result = result * base
            base = base * base
            n >>= 1
        return result

    def __eq__(self, other) -> bool:
        return isinstance(other, Laurent) and self.c == other.c

    def canonical(self) -> list:
        return sorted(self.c.items())

    def __repr__(self) -> str:
        if not self.c:
            return "0"
        parts = []
        for e, v in sorted(self.c.items()):
            parts.append(f"{v:+d}*A^{e}")
        return " ".join(parts)


# d = -A^2 - A^-2  (loop value)
_D = Laurent({2: -1, -2: -1})


# ---------------------------------------------------------------------------
# union-find
# ---------------------------------------------------------------------------
class _UF:
    def __init__(self):
        self.parent: dict[int, int] = {}
        self._n = 0

    def fresh(self) -> int:
        i = self._n
        self._n += 1
        self.parent[i] = i
        return i

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb

    def num_components(self) -> int:
        return len({self.find(x) for x in self.parent})


# ---------------------------------------------------------------------------
# Kauffman bracket of a braid closure
# ---------------------------------------------------------------------------
def n_strands(braid: list[int]) -> int:
    return (max(abs(g) for g in braid) + 1) if braid else 1


def kauffman_bracket(braid: list[int], n: int | None = None) -> Laurent:
    n = n or n_strands(braid)
    c = len(braid)
    total = Laurent()

    for state in range(1 << c):
        uf = _UF()
        bottom = [uf.fresh() for _ in range(n)]
        cur = list(bottom)
        a_exp = 0
        for k, g in enumerate(braid):
            pos = abs(g)                 # 1-indexed crossing position
            a, b = pos - 1, pos          # strands it acts on (0-indexed)
            choice = (state >> k) & 1    # 0 -> A-smoothing, 1 -> B-smoothing
            positive = g > 0
            # A-smoothing weight +1, B-smoothing weight -1
            a_exp += 1 if choice == 0 else -1
            # which smoothing is the e_i (cup-cap)?
            #   positive crossing: B-smoothing is e_i
            #   negative crossing: A-smoothing is e_i
            is_e = (choice == 1) if positive else (choice == 0)
            if is_e:
                uf.union(cur[a], cur[b])
                na, nb = uf.fresh(), uf.fresh()
                uf.union(na, nb)
                cur[a], cur[b] = na, nb
            # else identity smoothing: strands pass straight (no change)
        # close the braid
        for i in range(n):
            uf.union(cur[i], bottom[i])
        loops = uf.num_components()
        term = Laurent.mono(a_exp, 1) * _D.pow(loops - 1)
        total = total + term
    return total


def writhe(braid: list[int]) -> int:
    return sum(1 if g > 0 else -1 for g in braid)


def normalized_bracket(braid: list[int], n: int | None = None) -> Laurent:
    """X(A) = (-A^3)^{-w} <L>  — invariant under all Reidemeister moves."""
    br = kauffman_bracket(braid, n)
    w = writhe(braid)
    factor = Laurent.mono(3 * (-w), (-1) ** (-w if (-w) >= 0 else w))
    # (-A^3)^{-w} = (-1)^{-w} A^{-3w}
    factor = Laurent.mono(-3 * w, (-1) ** ((-w) % 2))
    return factor * br


def jones_polynomial(braid: list[int], n: int | None = None) -> dict:
    """Return the Jones polynomial V(t) as {t-exponent(Fraction-as-float): coeff}.

    Substitution A = t^{-1/4}, so A^k -> t^{-k/4}; exponents are stored as the
    rational -k/4 (float).  For a knot these are integers.
    """
    X = normalized_bracket(braid, n)
    V: dict = {}
    for e, v in X.c.items():
        texp = -e / 4.0
        V[texp] = V.get(texp, 0) + v
    return {k: v for k, v in V.items() if v != 0}


def jones_str(braid: list[int], n: int | None = None) -> str:
    V = jones_polynomial(braid, n)
    if not V:
        return "0"
    out = []
    for e in sorted(V):
        coeff = V[e]
        exp = int(e) if float(e).is_integer() else e
        out.append(f"{coeff:+d}*t^{exp}")
    return " ".join(out)


def evaluate_at_root_of_unity(braid: list[int], r: int = 5,
                              n: int | None = None) -> complex:
    """Evaluate the normalized bracket X(A) at A = e^{iπ/(2r)} — the
    Aharonov–Jones–Landau evaluation point (a quantum invariant)."""
    X = normalized_bracket(braid, n)
    A = cmath.exp(1j * math.pi / (2 * r))
    return sum(v * (A ** e) for e, v in X.c.items())
