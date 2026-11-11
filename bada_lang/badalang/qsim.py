"""Native multi-qubit quantum simulator for Bada — the "hardware" the Bada
Quantum OS runs on.

A register of n qubits is the state vector of 2**n complex amplitudes.  Gates
are unitary operators applied by Schrodinger evolution |psi> -> U|psi>; the
report's Hamiltonian evolution H|Psi> = (+)(i hbar grad)^(+)L is realised as
the composition of these unitary "ticks".  Uses Python's built-in complex.
"""

import cmath
import math
import random


# --- single-qubit 2x2 gate matrices ----------------------------------------

_S2 = 1.0 / math.sqrt(2.0)
GATES = {
    "I": (1, 0, 0, 1),
    "H": (_S2, _S2, _S2, -_S2),
    "X": (0, 1, 1, 0),
    "Y": (0, complex(0, -1), complex(0, 1), 0),
    "Z": (1, 0, 0, -1),
    "S": (1, 0, 0, complex(0, 1)),
    "T": (1, 0, 0, cmath.exp(complex(0, math.pi / 4))),
}


def _rot(name, theta):
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    if name == "RX":
        return (c, complex(0, -s), complex(0, -s), c)
    if name == "RY":
        return (c, -s, s, c)
    if name == "RZ":
        return (cmath.exp(complex(0, -theta / 2)), 0, 0, cmath.exp(complex(0, theta / 2)))
    if name == "PHASE":
        return (1, 0, 0, cmath.exp(complex(0, theta)))
    raise ValueError("unknown rotation " + name)


class QReg:
    def __init__(self, n):
        self.n = int(n)
        self.size = 1 << self.n
        self.amps = [0j] * self.size
        self.amps[0] = 1 + 0j

    # apply a 2x2 gate to qubit `t` (qubit 0 = least significant bit)
    def apply1(self, m, t):
        m00, m01, m10, m11 = m
        bit = 1 << t
        a = self.amps
        for i in range(self.size):
            if i & bit:
                continue
            j = i | bit
            x0 = a[i]
            x1 = a[j]
            a[i] = m00 * x0 + m01 * x1
            a[j] = m10 * x0 + m11 * x1

    # controlled 2x2 gate: apply to `t` only where `control` bit is 1
    def applyc(self, m, control, t):
        m00, m01, m10, m11 = m
        cb = 1 << control
        tb = 1 << t
        a = self.amps
        for i in range(self.size):
            if (i & tb) or not (i & cb):
                continue
            j = i | tb
            x0 = a[i]
            x1 = a[j]
            a[i] = m00 * x0 + m01 * x1
            a[j] = m10 * x0 + m11 * x1

    # flip the phase of a single computational basis state (oracle marking)
    def phase_flip(self, index):
        if 0 <= index < self.size:
            self.amps[index] = -self.amps[index]

    def probs(self):
        return [abs(z) ** 2 for z in self.amps]

    def measure(self, seed=None):
        rng = random.Random(seed) if seed is not None else random
        r = rng.random()
        acc = 0.0
        ps = self.probs()
        for i, p in enumerate(ps):
            acc += p
            if r <= acc:
                # collapse
                self.amps = [0j] * self.size
                self.amps[i] = 1 + 0j
                return i
        return self.size - 1

    def normalize(self):
        nrm = math.sqrt(sum(abs(z) ** 2 for z in self.amps))
        if nrm > 0:
            self.amps = [z / nrm for z in self.amps]

    def state_str(self, limit=8):
        out = []
        for i, z in enumerate(self.amps):
            if abs(z) ** 2 < 1e-9:
                continue
            ket = format(i, "0" + str(self.n) + "b")
            out.append(f"({z.real:.3f}{'+' if z.imag>=0 else '-'}{abs(z.imag):.3f}i)|{ket}>")
            if len(out) >= limit:
                out.append("...")
                break
        return " + ".join(out)

    def __repr__(self):
        return f"<qreg {self.n} qubits>"


# --- module-level helpers used by the builtins ------------------------------

def gate_matrix(name):
    return GATES[name]
