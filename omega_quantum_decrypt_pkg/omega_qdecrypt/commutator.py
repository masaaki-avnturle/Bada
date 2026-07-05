"""The "difference" operator from secretdata.pdf.

The paper defines

    y = pi(chi, x) <> f(x)  -  f(x) <> pi(chi, x)

which is exactly the **commutator** [pi, f] = pi @ f - f @ pi of two operators
(here, matrices).  The paper further states that the difference Delta

    "assemble from two of pair check with success data decrypted result"

i.e. two Jones-randomized versions of the same data are *differenced*, and the
difference collapsing to zero is the signal that the key matched and the
decryption is consistent.  This module implements both readings:

* :func:`commutator`  -- the matrix commutator [pi, f]  (non-commutativity
  detector; "non commutative equation" in the RSA note of the PDF);
* :func:`difference`  -- E1 - E2 for two Jones-randomized ciphertext vectors;
* :func:`key_match`   -- True iff that difference is (numerically) zero.
"""

from __future__ import annotations

from .matrix import PolyMatrix


def commutator(pi: PolyMatrix, f: PolyMatrix) -> PolyMatrix:
    """[pi, f] = pi @ f - f @ pi.  Zero iff pi and f commute."""
    return (pi @ f) - (f @ pi)


def commutes(pi: PolyMatrix, f: PolyMatrix, t=1.3, tol=1e-9) -> bool:
    """Numerically test whether the commutator vanishes at ``t``."""
    C = commutator(pi, f).eval(t)
    return all(abs(x) <= tol for row in C for x in row)


def difference(e1, e2):
    """Element-wise difference of two Jones-randomized ciphertext vectors."""
    if len(e1) != len(e2):
        raise ValueError("length mismatch")
    return [a - b for a, b in zip(e1, e2)]


def key_match(e1, e2, tol=1e-9):
    """The Delta pair-check: True iff differencing the two randomizations
    collapses to (numerically) zero -- the PDF's "success data decrypted
    result" signal."""
    return all(abs(d) <= tol for d in difference(e1, e2))
