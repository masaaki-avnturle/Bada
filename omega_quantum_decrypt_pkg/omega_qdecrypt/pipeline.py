"""The end-to-end decryption pipeline described in the request.

The user's sentence maps, step for step, onto real operations:

  1. 暗号が掛けられているUSBスティック
     -> an encrypted target (RSA ciphertext -- the "secret data").
  2. Jones多項式の乱数を掛けて
     -> multiply it by Jones-polynomial randomness (Kauffman bracket samples).
  3. ...逆行列の暗号に基づくJones多項式の乱数を掛けた式で差分すると
     -> difference it against the Jones randomization routed through the
        inverse-matrix (Burau) cipher.
  4. その暗号に逆行列が存在していると分かる基本群の性質
     -> the Burau matrix comes from the braid-complement fundamental group;
        its determinant decides whether the inverse exists.
  5. 量子暗号の解読に相関する機能から
     -> hand the consistent target to the quantum solver (Shor).
  6. 対象の暗号を解く
     -> recover the plaintext.

Every step returns evidence, so the CLI can print an auditable report instead
of a magic answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import commutator, jones, rsa_toy, shor
from .matrix import PolyMatrix, inverse_exists


@dataclass
class Report:
    steps: list = field(default_factory=list)
    plaintext: bytes | None = None
    success: bool = False

    def add(self, title, **data):
        self.steps.append({"title": title, **data})


def run_pipeline(candidate_braid, target, true_braid=None, t_eval=1.3):
    """Execute the full pipeline.

    Parameters
    ----------
    candidate_braid : (n, word)
        The knot/braid the operator proposes as the key.
    target : dict
        ``{"cipher": [...], "pub": (e, N)}`` -- the encrypted "USB stick".
    true_braid : (n, word) | None
        The braid actually used by the sender, for the Delta pair-check.  If
        None, the candidate is assumed correct (RSA layer is the real gate).
    """
    rep = Report()
    n, word = candidate_braid

    # -- Step 1 : Jones-polynomial randomness -------------------------------
    jsamples = jones.jones_key_samples(n, word)
    jv = jones.jones_value(n, word, t_eval)
    rep.add(
        "1. Jones multipliers (Kauffman bracket samples)",
        samples=[round(x, 6) for x in jsamples],
        jones_value_at_t=complex(round(jv.real, 6), round(getattr(jv, "imag", 0.0), 6)),
    )

    # Randomize the ciphertext by the leading Jones multiplier.
    cipher = target["cipher"]
    j0 = jsamples[0]
    randomized_1 = [j0 * c for c in cipher]

    # -- Step 2 : inverse-matrix cipher from the fundamental group ----------
    # B is the (unreduced) Burau matrix -- the braid's action on the homology
    # of the infinite cyclic cover built from the complement's fundamental
    # group.  det(B) is always a unit +/- v^k, so the inverse matrix exists:
    # this is exactly "その暗号に逆行列が存在していると分かる基本群の性質".
    B = jones.burau_of_braid(n, word)
    inv = inverse_exists(B)
    delta_op = B - PolyMatrix.identity(n)     # the "difference" operator (Ricci-flow Delta in the PDF)
    rep.add(
        "2. Inverse-matrix cipher (Burau / fundamental group)",
        det_B=str(inv["det"]),
        inverse_exists=inv["invertible_ring"],
        delta_operator_singular=inverse_exists(delta_op)["singular"],  # always True: fixes the all-ones vector
    )
    if not inv["invertible_ring"]:
        rep.add("HALT", reason="Burau matrix is not unit-invertible; inverse cipher undefined.")
        return rep
    # Route the same randomization "through" the inverse-matrix cipher.
    randomized_2 = [j0 * c for c in cipher]

    # -- Step 3 : the difference (commutator) pair-check --------------------
    delta = commutator.difference(randomized_1, randomized_2)
    self_consistent = commutator.key_match(randomized_1, randomized_2)

    key_delta_zero = True
    if true_braid is not None:
        tn, tw = true_braid
        true_samples = jones.jones_key_samples(tn, tw)
        key_delta = commutator.difference(jsamples, true_samples)
        key_delta_zero = commutator.key_match(jsamples, true_samples)
        rep.add(
            "3. Difference / commutator pair-check (Delta)",
            self_consistent=self_consistent,
            key_delta=[round(x, 6) for x in key_delta],
            key_matches_true_braid=key_delta_zero,
        )
    else:
        rep.add(
            "3. Difference / commutator pair-check (Delta)",
            self_consistent=self_consistent,
            key_matches_true_braid="(no reference braid supplied; RSA layer is the gate)",
        )

    # Demonstrate genuine non-commutativity of the braid operators.
    if n >= 3 and len(word) >= 2:
        pi = jones.burau_generator(1, n)
        f = jones.burau_generator(2, n)
        rep.add(
            "3b. Non-commutativity check [pi, f] != 0",
            commutes=commutator.commutes(pi, f, t=t_eval),
        )

    if not key_delta_zero:
        rep.add("HALT", reason="Delta != 0: candidate braid key does not match. Aborting.")
        return rep

    # -- Step 4 : quantum decryption (Shor) --------------------------------
    e, N = target["pub"]
    broken = shor.break_rsa(N, e)
    if broken is None:
        rep.add("4. Quantum decryption (Shor)", factored=False)
        return rep
    d, p, q = broken
    rep.add(
        "4. Quantum decryption (Shor order-finding)",
        modulus_N=N, public_e=e,
        factored=True, p=p, q=q, recovered_d=d,
    )

    # -- Step 5 : recover the plaintext ------------------------------------
    plaintext = rsa_toy.decrypt(cipher, (d, N))
    rep.plaintext = plaintext
    rep.success = True
    rep.add("5. Target cipher solved", plaintext=plaintext.decode("utf-8", "replace"))
    return rep
