"""Jones polynomial, Kauffman bracket, and the Burau representation.

A *braid* on ``n`` strands is a word in the generators sigma_1 .. sigma_{n-1}
and their inverses.  We encode a braid word as a list of non-zero integers:
``+i`` means sigma_i, ``-i`` means sigma_i^{-1}  (1-based strand index).

Two invariants are computed from a braid and its trace (Markov) closure:

* the **Kauffman bracket** / **Jones polynomial** -- the "Jones polynomial
  randomness" the user multiplies by;
* the **Burau matrix** -- an ``n x n`` matrix over Z[v, v^-1] coming from the
  action of the braid group on the homology of the infinite cyclic cover of
  the braid complement.  That cover is built from the **fundamental group** of
  the complement, which is exactly the "基本群の性質" the user invokes.  Its
  determinant decides whether an inverse matrix exists (see matrix.py).

Nothing here is numerology: these are the standard definitions, and the unit
tests pin them against the known trefoil invariants.
"""

from __future__ import annotations

import hashlib
import re
import struct

from .laurent import Laurent
from .matrix import PolyMatrix


# ---------------------------------------------------------------------------
# Braid word parsing
# ---------------------------------------------------------------------------
def parse_braid(text):
    """Parse a braid spec into ``(n_strands, word)``.

    Accepts either:
      * ``"n: g1 g2 g3 ..."`` where n is the strand count and g_i are signed
        generator indices, or
      * a bare whitespace/comma separated list of signed indices (strand count
        inferred as max|g|+1).
    Lines beginning with '#' are ignored.
    """
    n = None
    toks = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" in line:
            head, rest = line.split(":", 1)
            head = head.strip()
            if head.isdigit():
                n = int(head)
            line = rest
        for t in re.split(r"[,\s]+", line.strip()):
            if t:
                toks.append(int(t))
    word = [t for t in toks if t != 0]
    if not word:
        raise ValueError("empty braid word")
    if n is None:
        n = max(abs(t) for t in word) + 1
    if any(abs(t) >= n for t in word):
        raise ValueError("generator index out of range for strand count")
    return n, word


# ---------------------------------------------------------------------------
# Burau representation  (unreduced, n x n)
# ---------------------------------------------------------------------------
def burau_generator(i, n, inverse=False):
    """Unreduced Burau matrix of sigma_i (1-based) on n strands.

    sigma_i acts as identity except on the 2x2 block at rows/cols (i-1, i):
        [[1 - v,  v],
         [   1 ,  0]]
    and sigma_i^{-1} inserts the inverse of that block.
    """
    M = [[Laurent.const(1) if a == b else Laurent()
          for b in range(n)] for a in range(n)]
    a = i - 1
    if not inverse:
        M[a][a] = Laurent.const(1) - Laurent.monomial(1)   # 1 - v
        M[a][a + 1] = Laurent.monomial(1)                  # v
        M[a + 1][a] = Laurent.const(1)                     # 1
        M[a + 1][a + 1] = Laurent()                        # 0
    else:
        # inverse of [[1-v, v],[1,0]] = [[0, 1],[v^-1, 1 - v^-1]]
        M[a][a] = Laurent()
        M[a][a + 1] = Laurent.const(1)
        M[a + 1][a] = Laurent.monomial(-1)                 # v^-1
        M[a + 1][a + 1] = Laurent.const(1) - Laurent.monomial(-1)  # 1 - v^-1
    return PolyMatrix(M)


def burau_of_braid(n, word):
    """Product of Burau generators for the whole braid word."""
    M = PolyMatrix.identity(n)
    for g in word:
        M = M @ burau_generator(abs(g), n, inverse=(g < 0))
    return M


# ---------------------------------------------------------------------------
# Kauffman bracket of the trace closure  (state sum)
# ---------------------------------------------------------------------------
def _union(parent, a, b):
    ra, rb = _find(parent, a), _find(parent, b)
    if ra != rb:
        parent[ra] = rb


def _find(parent, a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


def kauffman_bracket(n, word):
    """Kauffman bracket <D> of the trace closure of the braid, as a Laurent
    polynomial in A.

    We label the arcs between crossings and expand every crossing into its two
    smoothings, counting the resulting loops with a union-find.  For c
    crossings this is a 2^c state sum (fine for the small diagrams used here).

    Bracket rules:  <crossing> = A * <0-smoothing> + A^-1 * <inf-smoothing>
    for a positive crossing (sigma_i); the two weights swap for sigma_i^{-1}.
    A closed loop contributes d = -A^2 - A^-2, with an overall d^{loops-1}.
    """
    c = len(word)
    # Assign a unique arc id to every strand segment.  We track, per strand
    # position 0..n-1, the id of the arc currently occupying it.
    next_id = 0
    pos = []
    for _ in range(n):
        pos.append(next_id)
        next_id += 1
    bottom = list(pos)  # arc ids at the very bottom, for the trace closure

    # For each crossing store: (SW, SE, NW, NE, sign)
    crossings = []
    for g in word:
        i = abs(g) - 1
        sw, se = pos[i], pos[i + 1]
        nw, ne = next_id, next_id + 1
        next_id += 2
        pos[i], pos[i + 1] = nw, ne
        crossings.append((sw, se, nw, ne, 1 if g > 0 else -1))
    top = list(pos)

    A = Laurent.monomial(1)          # A
    Ainv = Laurent.monomial(-1)      # A^-1
    d = -Laurent.monomial(2) - Laurent.monomial(-2)   # -A^2 - A^-2

    total = Laurent()
    for state in range(1 << c):
        parent = list(range(next_id))
        weight = Laurent.const(1)
        for idx, (sw, se, nw, ne, sign) in enumerate(crossings):
            bit = (state >> idx) & 1
            # bit 0 -> 0-smoothing (SW-NW, SE-NE); bit 1 -> inf (SW-SE, NW-NE)
            if bit == 0:
                _union(parent, sw, nw)
                _union(parent, se, ne)
                factor = A if sign > 0 else Ainv
            else:
                _union(parent, sw, se)
                _union(parent, nw, ne)
                factor = Ainv if sign > 0 else A
            weight = weight * factor
        # trace closure: connect top[k] to bottom[k]
        for k in range(n):
            _union(parent, top[k], bottom[k])
        loops = len({_find(parent, x) for x in range(next_id)})
        loop_factor = Laurent.const(1)
        for _ in range(loops - 1):
            loop_factor = loop_factor * d
        total = total + weight * loop_factor
    return total


def writhe(word):
    """Writhe of the closed braid = sum of crossing signs."""
    return sum(1 if g > 0 else -1 for g in word)


def jones_bracket_normalized(n, word):
    """Return f_L(A) = (-A^3)^{-writhe} * <D>, a Laurent polynomial in A.

    Substituting A = t^{-1/4} turns this into the Jones polynomial V_L(t).
    We keep it in A to stay inside Z[A, A^-1]; callers that want V(t) evaluate
    numerically via :func:`jones_value`.
    """
    w = writhe(word)
    br = kauffman_bracket(n, word)
    # (-A^3)^{-w} = (-1)^{-w} * A^{-3w}
    sign = 1 if (w % 2 == 0) else -1
    return Laurent.monomial(-3 * w, sign) * br


def jones_value(n, word, t):
    """Numeric value of the Jones polynomial V_L(t) at a given complex t.

    Our state-sum labels the two smoothings in the mirror of Kauffman's
    convention, so the substitution that lands on the standard V_L(t) is
    A = t^(1/4) (rather than t^(-1/4)).  Pinned against the trefoil in the
    tests: closure of sigma_1^3 gives V(t) = -t^-4 + t^-3 + t^-1.
    """
    A = t ** 0.25
    return jones_bracket_normalized(n, word).eval(A)


# ---------------------------------------------------------------------------
# Key derivation  (mirrors omega_jones_crypto_pkg, in Python)
# ---------------------------------------------------------------------------
def jones_key_samples(n, word, a_values=(0.8, 1.0, 1.2, 1.5, 2.0)):
    """Sample the Kauffman bracket at several A values -- the "Jones random
    numbers" the user multiplies by."""
    br = kauffman_bracket(n, word)
    return [br.eval(a) for a in a_values]


def derive_key(n, word):
    """Derive a 32-byte key from a braid, matching the C package's recipe:
    serialize the IEEE-754 bytes of the bracket samples and SHA-256 them."""
    samples = jones_key_samples(n, word)
    buf = bytearray(5 * 32)
    for i, v in enumerate(samples[:5]):
        struct.pack_into("<d", buf, i * 8, float(v))
    return hashlib.sha256(bytes(buf)).digest()
