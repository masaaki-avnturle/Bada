"""Shor 9-qubit quantum error-correcting code on a pure-Python state-vector simulator.

This module implements Peter Shor's [[9,1,3]] code, the concatenation of the
3-qubit phase-flip code with the 3-qubit bit-flip code. It protects one logical
qubit against an arbitrary single-qubit error (any X, Y, or Z, on any of the 9
physical qubits).

It is intended for use by a (simulated) quantum OS kernel: it exposes a small
state-vector class and a `Shor9` wrapper that can encode, inject an error,
measure stabilizer syndromes, correct, decode and report fidelity.

Pure stdlib only (cmath / math / random / itertools). No numpy.
"""

from __future__ import annotations

import cmath
import math
import itertools


# ---------------------------------------------------------------------------
# State-vector simulator
# ---------------------------------------------------------------------------

class StateVector:
    """A dense state-vector simulator for `n_qubits` qubits.

    Amplitudes are stored in a flat list of length 2**n_qubits.  The basis state
    index encodes qubit values with qubit 0 as the MOST significant bit, i.e.
    index bit for qubit q is bit (n_qubits-1-q).  This matches reading a
    bitstring 'b0 b1 ... b_{n-1}' left to right as qubit 0 .. qubit n-1.
    """

    def __init__(self, n_qubits: int) -> None:
        self.n = n_qubits
        self.dim = 1 << n_qubits
        # Initialise to |0...0>.
        self.amps = [0j] * self.dim
        self.amps[0] = 1 + 0j

    # -- internal helpers --------------------------------------------------

    def _bit_mask(self, q: int) -> int:
        """Bit mask in the basis index that selects qubit q (qubit 0 = MSB)."""
        return 1 << (self.n - 1 - q)

    # -- gates -------------------------------------------------------------

    def apply_1q(self, gate2x2, q: int) -> None:
        """Apply a 2x2 single-qubit gate to qubit q.

        gate2x2 is [[a, b], [c, d]] acting on (|0>, |1>) components of qubit q.
        """
        mask = self._bit_mask(q)
        a, b = gate2x2[0]
        c, d = gate2x2[1]
        amps = self.amps
        for i in range(self.dim):
            if i & mask:
                # We only touch each pair once: act when this index has the bit
                # set, pairing it with its partner that has the bit cleared.
                continue
            j = i | mask           # partner with qubit q = 1
            x0 = amps[i]           # amplitude with qubit q = 0
            x1 = amps[j]           # amplitude with qubit q = 1
            amps[i] = a * x0 + b * x1
            amps[j] = c * x0 + d * x1

    def apply_cnot(self, control: int, target: int) -> None:
        """Apply a CNOT gate with the given control and target qubits."""
        cmask = self._bit_mask(control)
        tmask = self._bit_mask(target)
        amps = self.amps
        for i in range(self.dim):
            # Flip target only when control is 1 and target is 0, swapping with
            # its partner (control 1, target 1); each pair handled once.
            if (i & cmask) and not (i & tmask):
                j = i | tmask
                amps[i], amps[j] = amps[j], amps[i]

    # Pauli / Hadamard helpers --------------------------------------------

    _X = [[0 + 0j, 1 + 0j], [1 + 0j, 0 + 0j]]
    _Y = [[0 + 0j, -1j], [1j, 0 + 0j]]
    _Z = [[1 + 0j, 0 + 0j], [0 + 0j, -1 + 0j]]
    _H = [[1 / math.sqrt(2) + 0j, 1 / math.sqrt(2) + 0j],
          [1 / math.sqrt(2) + 0j, -1 / math.sqrt(2) + 0j]]

    def x(self, q: int) -> None:
        self.apply_1q(self._X, q)

    def y(self, q: int) -> None:
        self.apply_1q(self._Y, q)

    def z(self, q: int) -> None:
        self.apply_1q(self._Z, q)

    def h(self, q: int) -> None:
        self.apply_1q(self._H, q)

    # -- measurement / expectation ----------------------------------------

    def expectation_pauli(self, paulistring: str) -> float:
        """Return the real expectation value <psi|P|psi> for a Pauli string.

        `paulistring` has length n_qubits over {'I','X','Y','Z'}, with character
        k acting on qubit k.  For a tensor product of Paulis the result is real.
        """
        if len(paulistring) != self.n:
            raise ValueError("paulistring length must equal n_qubits")

        amps = self.amps
        # Build, for each basis index i, the index P|i> and the accumulated
        # phase.  Each single-qubit Pauli maps a basis state to another basis
        # state (possibly the same) times a phase, so P is a signed/phased
        # permutation; <psi|P|psi> = sum_i conj(amps[P i]) * phase_i * amps[i].
        masks = [self._bit_mask(q) for q in range(self.n)]

        total = 0j
        for i in range(self.dim):
            ai = amps[i]
            if ai == 0:
                continue
            j = i
            phase = 1 + 0j
            for q, p in enumerate(paulistring):
                if p == 'I':
                    continue
                mask = masks[q]
                bit = 1 if (i & mask) else 0
                if p == 'X':
                    j ^= mask
                elif p == 'Z':
                    if bit:
                        phase = -phase
                elif p == 'Y':
                    # Y = i * X * Z ; Y|0> = i|1>, Y|1> = -i|0>
                    j ^= mask
                    if bit:
                        phase = phase * (-1j)
                    else:
                        phase = phase * (1j)
                else:
                    raise ValueError(f"bad Pauli char {p!r}")
            total += (amps[j].conjugate()) * phase * ai
        # Imaginary part should be ~0 for a Hermitian Pauli product.
        return total.real

    def copy(self) -> "StateVector":
        new = StateVector(self.n)
        new.amps = list(self.amps)
        return new


# ---------------------------------------------------------------------------
# Shor 9-qubit code
# ---------------------------------------------------------------------------

# The 8 stabilizer generators of the Shor code.
# 6 Z-type generators detect bit flips (within each block of 3):
#   Z0Z1, Z1Z2, Z3Z4, Z4Z5, Z6Z7, Z7Z8
# 2 X-type generators detect phase flips (across blocks):
#   X0X1X2X3X4X5, X3X4X5X6X7X8
_STABILIZERS = [
    "ZZIIIIIII",  # Z0 Z1
    "IZZIIIIII",  # Z1 Z2
    "IIIZZIIII",  # Z3 Z4
    "IIIIZZIII",  # Z4 Z5
    "IIIIIIZZI",  # Z6 Z7
    "IIIIIIIZZ",  # Z7 Z8
    "XXXXXXIII",  # X0..X5
    "IIIXXXXXX",  # X3..X8
]


class Shor9:
    """Shor's 9-qubit code with a state-vector backend and lookup-table decoder."""

    def __init__(self) -> None:
        self.sv = StateVector(9)
        # Recovery lookup table: syndrome (8-tuple) -> recovery description.
        self._table = self._build_table()

    # -- encoding ----------------------------------------------------------

    @staticmethod
    def _encode_into(sv: StateVector) -> None:
        """Apply the standard Shor encoding circuit to `sv`.

        Assumes the logical information already lives on qubit 0 (qubits 1..8
        are |0>).  After this, qubit 0's state is spread into the codeword.
        """
        # Phase-flip (outer) code: spread qubit 0 onto block heads 3 and 6,
        # then Hadamard each block head.
        sv.apply_cnot(0, 3)
        sv.apply_cnot(0, 6)
        sv.h(0)
        sv.h(3)
        sv.h(6)
        # Bit-flip (inner) code: within each block copy the head to its two
        # partners.
        for head in (0, 3, 6):
            sv.apply_cnot(head, head + 1)
            sv.apply_cnot(head, head + 2)

    @staticmethod
    def _decode_into(sv: StateVector) -> None:
        """Apply the inverse of `_encode_into` to `sv` (gates are self-inverse,
        so we just reverse their order)."""
        for head in (0, 3, 6):
            sv.apply_cnot(head, head + 2)
            sv.apply_cnot(head, head + 1)
        sv.h(0)
        sv.h(3)
        sv.h(6)
        sv.apply_cnot(0, 6)
        sv.apply_cnot(0, 3)

    def encode(self, alpha: complex, beta: complex) -> None:
        """Prepare the logical state alpha|0_L> + beta|1_L>.

        (alpha, beta) need not be normalized; it is normalized internally.
        """
        alpha = complex(alpha)
        beta = complex(beta)
        norm = math.sqrt(abs(alpha) ** 2 + abs(beta) ** 2)
        if norm == 0:
            raise ValueError("alpha and beta cannot both be zero")
        alpha /= norm
        beta /= norm

        # Start fresh, place (alpha, beta) on qubit 0 (others |0>), then encode.
        self.sv = StateVector(9)
        # |0...0> has amplitude 1 at index 0.  Put beta on the state where
        # qubit 0 = 1 (others 0): that's index 1<<8 = 256.
        self.sv.amps[0] = alpha
        self.sv.amps[1 << 8] = beta
        self._encode_into(self.sv)

    # -- error injection ---------------------------------------------------

    def inject_error(self, kind: str, qubit: int) -> None:
        """Apply a single-qubit Pauli error of `kind` in {'X','Y','Z'}."""
        if not (0 <= qubit <= 8):
            raise ValueError("qubit must be in 0..8")
        kind = kind.upper()
        if kind == 'X':
            self.sv.x(qubit)
        elif kind == 'Y':
            self.sv.y(qubit)
        elif kind == 'Z':
            self.sv.z(qubit)
        else:
            raise ValueError("kind must be X, Y, or Z")

    # -- syndrome ----------------------------------------------------------

    def syndrome(self) -> tuple:
        """Measure the 8 stabilizer generators via expectation values.

        Each generator has eigenvalue +-1 exactly for code states / single
        errors.  Returns an 8-tuple of bits, bit=0 for eigenvalue +1
        (expectation > 0) else 1.
        """
        bits = []
        for stab in _STABILIZERS:
            ev = self.sv.expectation_pauli(stab)
            bits.append(0 if ev > 0 else 1)
        return tuple(bits)

    # -- recovery lookup table ---------------------------------------------

    def _build_table(self) -> dict:
        """Build syndrome -> recovery lookup table.

        Simulate every single-qubit X, Y, Z error on a reference codeword,
        record its syndrome, and store the recovery (the same Pauli, which is
        self-inverse).  The identity (no error) maps the all-zero syndrome to
        'I'.
        """
        table = {}

        # Reference codeword: encode |0_L> (alpha=1, beta=0).  Any code state
        # produces identical syndromes for a given error, so |0_L> suffices.
        ref = StateVector(9)
        ref.amps[0] = 1 + 0j
        self._encode_into(ref)

        # No-error case.
        clean_syndrome = self._syndrome_of(ref)
        table[clean_syndrome] = ('I', None)

        # Single-qubit errors.  We record each (kind, qubit) -> syndrome.  For
        # the Shor code, X and Y errors on certain qubits can share syndromes
        # with combinations, but every distinct single-qubit error yields a
        # syndrome that uniquely identifies a valid recovery (up to stabilizer
        # equivalence).  We choose the first error producing each syndrome; the
        # recovery is that error's Pauli (self-inverse).
        for qubit in range(9):
            for kind in ('X', 'Z', 'Y'):
                test = ref.copy()
                if kind == 'X':
                    test.x(qubit)
                elif kind == 'Z':
                    test.z(qubit)
                else:
                    test.y(qubit)
                syn = self._syndrome_of(test)
                if syn not in table:
                    table[syn] = (kind, qubit)
        return table

    @staticmethod
    def _syndrome_of(sv: StateVector) -> tuple:
        bits = []
        for stab in _STABILIZERS:
            ev = sv.expectation_pauli(stab)
            bits.append(0 if ev > 0 else 1)
        return tuple(bits)

    # -- correction --------------------------------------------------------

    def correct(self) -> str:
        """Apply the recovery indicated by the current syndrome, in place.

        Returns a short string describing the applied recovery, e.g. 'X@4' or
        'I'.
        """
        syn = self.syndrome()
        entry = self._table.get(syn)
        if entry is None:
            # Unknown syndrome (e.g. a multi-qubit error): nothing safe to do.
            return '?'
        kind, qubit = entry
        if kind == 'I':
            return 'I'
        if kind == 'X':
            self.sv.x(qubit)
        elif kind == 'Z':
            self.sv.z(qubit)
        elif kind == 'Y':
            self.sv.y(qubit)
        return f"{kind}@{qubit}"

    # -- decoding ----------------------------------------------------------

    def decode(self) -> tuple:
        """Apply the inverse encoding circuit and return (alpha, beta).

        After inverse encoding a valid codeword, qubits 1..8 return to |0> and
        the logical amplitudes live on qubit 0.  We read alpha from the
        all-zero basis state and beta from the state with only qubit 0 set.
        """
        self._decode_into(self.sv)
        alpha = self.sv.amps[0]            # qubit0=0, rest 0
        beta = self.sv.amps[1 << 8]        # qubit0=1, rest 0
        return (alpha, beta)

    # -- fidelity ----------------------------------------------------------

    def fidelity(self, alpha: complex, beta: complex) -> float:
        """Return |<phi|psi_decoded>| comparing the decoded logical qubit to
        the original (alpha, beta).  Both are normalized; result in [0, 1].
        """
        a, b = self.decode_state()
        # Normalize reference.
        alpha = complex(alpha)
        beta = complex(beta)
        rn = math.sqrt(abs(alpha) ** 2 + abs(beta) ** 2)
        if rn == 0:
            raise ValueError("reference state cannot be zero")
        alpha /= rn
        beta /= rn
        # Normalize decoded.
        dn = math.sqrt(abs(a) ** 2 + abs(b) ** 2)
        if dn == 0:
            return 0.0
        a /= dn
        b /= dn
        overlap = alpha.conjugate() * a + beta.conjugate() * b
        return abs(overlap)

    def decode_state(self) -> tuple:
        """Read the decoded (alpha, beta) WITHOUT mutating the state vector.

        Used by `fidelity` so it can be called independently of `decode`.
        """
        tmp = self.sv.copy()
        self._decode_into(tmp)
        return (tmp.amps[0], tmp.amps[1 << 8])


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo_correct(kind: str, qubit: int,
                 alpha: complex = 0.6, beta: complex = 0.8) -> dict:
    """Run a full encode / error / syndrome / correct / decode cycle.

    Returns a dict with keys: 'kind', 'qubit', 'syndrome', 'recovery',
    'fidelity_before', 'fidelity_after'.
    """
    code = Shor9()
    code.encode(alpha, beta)

    code.inject_error(kind, qubit)
    # Fidelity before correction (decoded state vs. original, no mutation).
    fidelity_before = code.fidelity(alpha, beta)

    syn = code.syndrome()
    recovery = code.correct()

    fidelity_after = code.fidelity(alpha, beta)

    return {
        'kind': kind,
        'qubit': qubit,
        'syndrome': syn,
        'recovery': recovery,
        'fidelity_before': fidelity_before,
        'fidelity_after': fidelity_after,
    }


if __name__ == "__main__":
    print("Shor 9-qubit code: single-qubit error correction test")
    print("=" * 60)
    header = f"{'kind':<5}{'qubit':<7}{'recovery':<10}" \
             f"{'fid_before':<12}{'fid_after':<12}{'result':<6}"
    print(header)
    print("-" * 60)

    all_pass = True
    n_cases = 0
    for kind in ('X', 'Y', 'Z'):
        for qubit in range(9):
            res = demo_correct(kind, qubit)
            n_cases += 1
            ok = res['fidelity_after'] > 0.999
            all_pass = all_pass and ok
            status = "PASS" if ok else "FAIL"
            print(f"{res['kind']:<5}{res['qubit']:<7}{res['recovery']:<10}"
                  f"{res['fidelity_before']:<12.4f}"
                  f"{res['fidelity_after']:<12.4f}{status:<6}")
            assert ok, (f"FAILED: {kind} error on qubit {qubit}, "
                        f"fidelity_after={res['fidelity_after']}")

    print("-" * 60)
    print(f"{n_cases} cases tested.  "
          f"{'ALL PASS' if all_pass else 'SOME FAILED'}")
