"""Small dense matrices whose entries are :class:`Laurent` polynomials.

Used for the Burau representation of braids.  The one non-trivial operation is
the determinant, which we compute by cofactor expansion (the matrices are
tiny -- at most ~6x6 -- so O(n!) is fine and keeps everything exact over
Z[v, v^-1] with no division).

The determinant is the bridge to the user's request: an "inverse-matrix
cipher" has an inverse **iff** the determinant is not the zero polynomial, and
whether that determinant vanishes at the key value governs whether the cipher
is invertible there.  See :func:`inverse_exists`.
"""

from __future__ import annotations

from .laurent import Laurent, _coerce


class PolyMatrix:
    def __init__(self, rows):
        self.rows = [[_coerce(x) for x in row] for row in rows]
        self.n = len(rows)
        self.m = len(rows[0]) if rows else 0
        assert all(len(r) == self.m for r in self.rows), "ragged matrix"

    @staticmethod
    def identity(n):
        return PolyMatrix(
            [[Laurent.const(1) if i == j else Laurent() for j in range(n)]
             for i in range(n)]
        )

    def __matmul__(self, other):
        assert self.m == other.n, "dimension mismatch"
        out = [[Laurent() for _ in range(other.m)] for _ in range(self.n)]
        for i in range(self.n):
            for k in range(self.m):
                a = self.rows[i][k]
                if a.is_zero():
                    continue
                for j in range(other.m):
                    out[i][j] = out[i][j] + a * other.rows[k][j]
        return PolyMatrix(out)

    def __sub__(self, other):
        return PolyMatrix(
            [[self.rows[i][j] - other.rows[i][j] for j in range(self.m)]
             for i in range(self.n)]
        )

    def __add__(self, other):
        return PolyMatrix(
            [[self.rows[i][j] + other.rows[i][j] for j in range(self.m)]
             for i in range(self.n)]
        )

    def determinant(self) -> Laurent:
        """Cofactor (Laplace) expansion.  Exact over Z[v, v^-1]."""
        assert self.n == self.m, "determinant needs a square matrix"
        return _det(self.rows)

    def eval(self, v):
        """Evaluate every entry numerically -> list-of-lists of numbers."""
        return [[e.eval(v) for e in row] for row in self.rows]

    def __repr__(self):
        return "PolyMatrix[\n  " + "\n  ".join(
            "[" + ", ".join(str(e) for e in row) + "]" for row in self.rows
        ) + "\n]"


def _det(rows):
    n = len(rows)
    if n == 1:
        return rows[0][0]
    if n == 2:
        return rows[0][0] * rows[1][1] - rows[0][1] * rows[1][0]
    total = Laurent()
    for j in range(n):
        a = rows[0][j]
        if a.is_zero():
            continue
        minor = [r[:j] + r[j + 1:] for r in rows[1:]]
        sign = 1 if j % 2 == 0 else -1
        total = total + (a * _det(minor)) * sign
    return total


def inverse_exists(mat: PolyMatrix):
    """Decide whether ``mat`` is invertible, in two senses.

    Returns a dict:
      * ``det``            -- the determinant as a Laurent polynomial
      * ``invertible_ring``-- True iff det is a unit +/- v^k  (invertible over
                              Z[v, v^-1], i.e. a genuine inverse matrix exists)
      * ``singular``       -- True iff det is the zero polynomial (never
                              invertible)

    This is the concrete meaning of the user's phrase
    "その暗号に逆行列が存在していると分かる" -- we can *decide*, from the
    Burau (fundamental-group) matrix, whether the inverse exists.
    """
    det = mat.determinant()
    return {
        "det": det,
        "invertible_ring": det.is_unit_monomial(),
        "singular": det.is_zero(),
    }
