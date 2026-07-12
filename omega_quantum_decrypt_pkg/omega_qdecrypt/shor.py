"""Shor's algorithm -- the quantum-cryptanalysis engine.

secretdata.pdf explicitly names "Rsa secret data and non commutative equation".
The genuine, well-established link between quantum computing and *decrypting*
a cipher is **Shor's algorithm**, which factors an RSA modulus in polynomial
time on a quantum computer and thereby recovers the private key.

Here we run the quantum step -- *order finding* -- as a classical simulation.
The quantum period-finding subroutine is what a real quantum computer would do
via the quantum Fourier transform; simulating it classically costs, in the
worst case, exponential time, which is precisely why this only breaks **toy**
RSA sizes.  That honesty matters: this module does NOT break real 2048-bit RSA,
and nothing in this repository does.  It is a faithful, runnable demonstration
of *how* the attack works.

References: Shor 1994; Nielsen & Chuang, ch. 5.
"""

from __future__ import annotations

import math


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def multiplicative_order(a, N):
    """Order-finding: smallest r > 0 with a^r == 1 (mod N).

    This is the subroutine a quantum computer solves with the QFT in
    O(poly(log N)); classically we search, so it is only tractable for small N.
    Returns None if a and N are not coprime.
    """
    if _gcd(a, N) != 1:
        return None
    r = 1
    x = a % N
    while x != 1:
        x = (x * a) % N
        r += 1
        if r > N:  # safety; should never trigger for coprime a
            return None
    return r


def shor_factor(N, max_bases=200):
    """Factor a composite ``N`` via order finding (Shor).

    Returns ``(p, q)`` with ``p * q == N`` (non-trivial) or ``None`` on
    failure.  Deterministic base sweep (2,3,5,...) so runs are reproducible.
    """
    if N % 2 == 0:
        return 2, N // 2
    # Rule out perfect powers a^b (Shor's classical pre-check).
    for b in range(2, int(math.log2(N)) + 1):
        root = round(N ** (1.0 / b))
        for cand in (root - 1, root, root + 1):
            if cand > 1 and cand ** b == N:
                return cand, N // cand

    a = 2
    tried = 0
    while a < N and tried < max_bases:
        g = _gcd(a, N)
        if g > 1:                       # got lucky: a shares a factor
            return g, N // g
        r = multiplicative_order(a, N)
        if r is not None and r % 2 == 0:
            y = pow(a, r // 2, N)
            if y != N - 1:              # y == -1 mod N gives only trivial factors
                for cand in (_gcd(y - 1, N), _gcd(y + 1, N)):
                    if 1 < cand < N:
                        return cand, N // cand
        a += 1
        tried += 1
    return None


def break_rsa(N, e):
    """Recover the RSA private exponent d by factoring N with Shor.

    Returns ``(d, p, q)`` or ``None``.
    """
    fac = shor_factor(N)
    if fac is None:
        return None
    p, q = fac
    phi = (p - 1) * (q - 1)
    try:
        d = pow(e, -1, phi)            # modular inverse (Python 3.8+)
    except ValueError:
        return None
    return d, p, q


def rsa_transform(m, exp, N):
    """RSA primitive: m^exp mod N (encryption with e, decryption with d)."""
    return pow(m, exp, N)
