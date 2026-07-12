"""Unit tests pinning the math to known values and the pipeline to a full
decrypt.  Run:  python -m pytest -q   (or)   python tests/test_all.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from omega_qdecrypt import commutator, jones, rsa_toy, shor          # noqa: E402
from omega_qdecrypt.laurent import Laurent                            # noqa: E402
from omega_qdecrypt.matrix import PolyMatrix, inverse_exists          # noqa: E402
from omega_qdecrypt.pipeline import run_pipeline                      # noqa: E402


# ---------------------------------------------------------------- Laurent
def test_laurent_arithmetic():
    a = Laurent({1: 1}) - Laurent({-1: 1})        # v - v^-1
    b = Laurent({1: 1}) + Laurent({-1: 1})        # v + v^-1
    assert (a * b).c == {2: 1, -2: -1}            # v^2 - v^-2
    assert (a * b).eval(2.0) == 4.0 - 0.25


def test_laurent_unit():
    assert Laurent({3: -1}).is_unit_monomial()
    assert not Laurent({3: 2}).is_unit_monomial()
    assert not (Laurent({3: 1}) + Laurent({0: 1})).is_unit_monomial()


# ------------------------------------------------------------------ Jones
def test_unknot_normalized_bracket_is_one():
    # sigma_1 on 2 strands closes to the (1-curl) unknot.  The *raw* bracket
    # carries the Reidemeister-I curl factor (-A^3); the *normalized* bracket,
    # which is the genuine invariant, must be 1.
    n, word = jones.parse_braid("2: 1")
    assert jones.kauffman_bracket(n, word) == Laurent({3: -1})       # -A^3
    assert jones.jones_bracket_normalized(n, word) == Laurent.const(1)


def test_trefoil_jones_value():
    # Right-handed trefoil = closure of sigma_1^3.  Its Jones polynomial is
    # V(t) = -t^-4 + t^-3 + t^-1.  Check numerically at a few points.
    n, word = jones.parse_braid("2: 1 1 1")
    for t in (1.3, 2.0, 0.7):
        expected = -t ** -4 + t ** -3 + t ** -1
        got = jones.jones_value(n, word, t)
        assert abs(got - expected) < 1e-9, (t, got, expected)


def test_burau_is_invertible_for_braid():
    # A pure braid's Burau matrix has unit determinant (a genuine inverse).
    n, word = jones.parse_braid("3: 1 2 1")
    B = jones.burau_of_braid(n, word)
    det = B.determinant()
    assert det.is_unit_monomial(), det


def test_inverse_exists_report():
    n, word = jones.parse_braid("3: 1 1 1")
    B = jones.burau_of_braid(n, word)
    inv = inverse_exists(B - PolyMatrix.identity(n))
    assert "det" in inv and "singular" in inv


# ------------------------------------------------------------ commutator
def test_commutator_nonzero():
    n = 3
    pi = jones.burau_generator(1, n)
    f = jones.burau_generator(2, n)
    assert not commutator.commutes(pi, f, t=1.3)     # braids don't commute


def test_key_match_delta():
    a = jones.jones_key_samples(*jones.parse_braid("3: 1 1 1"))
    assert commutator.key_match(a, list(a))          # identical -> Delta = 0
    b = jones.jones_key_samples(*jones.parse_braid("3: 1 2 1 2"))
    assert not commutator.key_match(a, b)


# ----------------------------------------------------------------- Shor
def test_shor_factor():
    assert sorted(shor.shor_factor(10007 * 12011)) == [10007, 12011]
    assert sorted(shor.shor_factor(15)) == [3, 5]


def test_break_rsa_roundtrip():
    pub, priv = rsa_toy.make_keypair(1009, 1013)
    msg = "HELLO-JONES"
    ct = rsa_toy.encrypt(msg, pub)
    e, N = pub
    d, p, q = shor.break_rsa(N, e)
    assert rsa_toy.decrypt(ct, (d, N)).decode() == msg


# ------------------------------------------------------------- pipeline
def test_full_pipeline_solves():
    pub, _ = rsa_toy.make_keypair(1009, 1013)
    cipher = rsa_toy.encrypt("USB-SECRET", pub)
    braid = jones.parse_braid("3: 1 1 1")
    rep = run_pipeline(braid, {"cipher": cipher, "pub": pub}, true_braid=braid)
    assert rep.success
    assert rep.plaintext.decode() == "USB-SECRET"


def test_pipeline_halts_on_wrong_key():
    pub, _ = rsa_toy.make_keypair(1009, 1013)
    cipher = rsa_toy.encrypt("USB-SECRET", pub)
    candidate = jones.parse_braid("3: 1 1 1")
    wrong_true = jones.parse_braid("3: 1 2 1 2 1")
    rep = run_pipeline(candidate, {"cipher": cipher, "pub": pub}, true_braid=wrong_true)
    assert not rep.success          # Delta != 0 -> halts before Shor


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
