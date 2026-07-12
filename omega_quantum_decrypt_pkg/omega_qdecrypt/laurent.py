"""Laurent polynomials in a single variable over the integers.

A Laurent polynomial is a finite sum  sum_k c_k * v^k  where k may be any
integer (positive, zero, or negative).  We store it as {exponent: coefficient}
with all zero coefficients pruned, so equality is structural.

This is the numeric backbone for the Jones / Kauffman-bracket polynomials and
for the Burau matrices, whose entries all live in Z[v, v^-1].
"""

from __future__ import annotations


class Laurent:
    __slots__ = ("c",)

    def __init__(self, coeffs=None):
        # coeffs: dict {int exponent -> int coefficient} or an int
        c = {}
        if coeffs is None:
            pass
        elif isinstance(coeffs, int):
            if coeffs != 0:
                c[0] = coeffs
        elif isinstance(coeffs, Laurent):
            c = dict(coeffs.c)
        else:
            for e, k in coeffs.items():
                if k:
                    c[int(e)] = c.get(int(e), 0) + int(k)
        self.c = {e: k for e, k in c.items() if k}

    # -- constructors ---------------------------------------------------
    @staticmethod
    def const(k):
        return Laurent({0: k})

    @staticmethod
    def monomial(exp, coeff=1):
        return Laurent({exp: coeff})

    # -- arithmetic -----------------------------------------------------
    def __add__(self, other):
        other = _coerce(other)
        out = dict(self.c)
        for e, k in other.c.items():
            out[e] = out.get(e, 0) + k
        return Laurent(out)

    __radd__ = __add__

    def __neg__(self):
        return Laurent({e: -k for e, k in self.c.items()})

    def __sub__(self, other):
        return self + (-_coerce(other))

    def __rsub__(self, other):
        return _coerce(other) + (-self)

    def __mul__(self, other):
        other = _coerce(other)
        out = {}
        for e1, k1 in self.c.items():
            for e2, k2 in other.c.items():
                e = e1 + e2
                out[e] = out.get(e, 0) + k1 * k2
        return Laurent(out)

    __rmul__ = __mul__

    def __eq__(self, other):
        return self.c == _coerce(other).c

    def __hash__(self):
        return hash(tuple(sorted(self.c.items())))

    def __bool__(self):
        return bool(self.c)

    def is_zero(self):
        return not self.c

    def is_unit_monomial(self):
        """True for +/- v^k : the units of Z[v, v^-1]."""
        return len(self.c) == 1 and abs(next(iter(self.c.values()))) == 1

    # -- evaluation -----------------------------------------------------
    def eval(self, v):
        """Numerically evaluate at v (float or complex)."""
        return sum(k * (v ** e) for e, k in self.c.items())

    # -- display --------------------------------------------------------
    def __repr__(self):
        if not self.c:
            return "0"
        parts = []
        for e in sorted(self.c, reverse=True):
            k = self.c[e]
            if e == 0:
                parts.append(f"{k:+d}")
            elif e == 1:
                parts.append(f"{k:+d}*v")
            else:
                parts.append(f"{k:+d}*v^{e}")
        s = " ".join(parts)
        return s[1:] if s.startswith("+") else s


def _coerce(x):
    if isinstance(x, Laurent):
        return x
    if isinstance(x, int):
        return Laurent.const(x)
    raise TypeError(f"cannot combine Laurent with {type(x)}")
