package bada.quantum;

import java.util.Random;

/**
 * Two-qubit state-vector simulator over the basis |00>,|01>,|10>,|11| with the
 * index convention i = 2*a + b (a = Alice qubit, b = Bob qubit). This is the
 * entangled pair that carries the telegraph. Pure Java, no dependencies.
 */
public final class Qubit2 {
    public final Complex[] amp;
    private static final double S = 1.0 / Math.sqrt(2.0);

    public Qubit2() {
        amp = new Complex[]{Complex.real(1), Complex.real(0), Complex.real(0), Complex.real(0)};
    }

    public Qubit2(Complex[] a) { amp = a; }

    /** Bell state Phi+ = (|00> + |11>)/sqrt(2), analytic. */
    public static Qubit2 bellPhiPlus() {
        return new Qubit2(new Complex[]{Complex.real(S), Complex.real(0), Complex.real(0), Complex.real(S)});
    }

    /** Prepare Phi+ from |00> with the actual circuit H(A) then CNOT(A->B). */
    public static Qubit2 prepareBell() {
        Qubit2 q = new Qubit2();
        q.hA();
        q.cnot();
        return q;
    }

    /** Hadamard on Alice's qubit (H tensor I). */
    public void hA() {
        Complex n0 = amp[0].add(amp[2]).scale(S);
        Complex n2 = amp[0].sub(amp[2]).scale(S);
        Complex n1 = amp[1].add(amp[3]).scale(S);
        Complex n3 = amp[1].sub(amp[3]).scale(S);
        amp[0] = n0; amp[1] = n1; amp[2] = n2; amp[3] = n3;
    }

    /** CNOT with Alice control, Bob target: swap |10> and |11>. */
    public void cnot() {
        Complex t = amp[2]; amp[2] = amp[3]; amp[3] = t;
    }

    /** Pauli X on Alice: swap (a=0)<->(a=1): (0<->2),(1<->3). */
    public void xA() {
        Complex t0 = amp[0]; amp[0] = amp[2]; amp[2] = t0;
        Complex t1 = amp[1]; amp[1] = amp[3]; amp[3] = t1;
    }

    /** Pauli Z on Alice: phase -1 when a=1. */
    public void zA() {
        amp[2] = amp[2].scale(-1); amp[3] = amp[3].scale(-1);
    }

    /** Pauli Y on Alice: amp'(0,b) = -i amp(1,b), amp'(1,b) = i amp(0,b). */
    public void yA() {
        Complex i = new Complex(0, 1);
        Complex n0 = i.scale(-1).mul(amp[2]);
        Complex n2 = i.mul(amp[0]);
        Complex n1 = i.scale(-1).mul(amp[3]);
        Complex n3 = i.mul(amp[1]);
        amp[0] = n0; amp[1] = n1; amp[2] = n2; amp[3] = n3;
    }

    /** Superdense encoder: 00->I, 01->X, 10->Z, 11->ZX. */
    public void encode(int bitHi, int bitLo) {
        if (bitHi == 1) zA();
        if (bitLo == 1) xA();
    }

    /** Bell measurement decoder: CNOT then H(A). */
    public void bellDecode() { cnot(); hA(); }

    public double[] probabilities() {
        double[] p = new double[4];
        for (int i = 0; i < 4; i++) p[i] = amp[i].abs2();
        return p;
    }

    /** Deterministic readout: bits of the highest-probability basis state. */
    public int[] readoutBits() {
        double[] p = probabilities();
        int best = 0;
        for (int i = 1; i < 4; i++) if (p[i] > p[best]) best = i;
        return new int[]{best >> 1, best & 1};
    }

    /** Marginal probability Bob reads 1 (no-signaling check). */
    public double bobMarginalOne() {
        double[] p = probabilities();
        return p[1] + p[3];
    }

    public double norm() {
        double s = 0;
        for (Complex c : amp) s += c.abs2();
        return Math.sqrt(s);
    }
}
