package bada.quantum;

/**
 * The quintic (5次方程式) carrier. Abel–Ruffini denies a radical solution
 * formula; we solve numerically with Durand–Kerner and use the fifth roots of
 * unity (period 2π/5) as a quinary carrier whose phase is non-linearly warped
 * by the pair correlation — period-tuned yet non-linear.
 */
public final class Quintic {
    public static final double TWO_PI = 2.0 * Math.PI;
    public static final double PERIOD = TWO_PI / 5.0;

    /** The five fifth-roots of unity exp(2*pi*i*k/5). */
    public static Complex[] rootsOfUnity() {
        Complex[] r = new Complex[5];
        for (int k = 0; k < 5; k++) {
            r[k] = new Complex(Math.cos(PERIOD * k), Math.sin(PERIOD * k));
        }
        return r;
    }

    /** Evaluate x^5 + c4 x^4 + c3 x^3 + c2 x^2 + c1 x + c0. */
    static Complex poly5(Complex x, Complex[] c) {
        return x.pow(5)
                .add(c[0].mul(x.pow(4)))
                .add(c[1].mul(x.pow(3)))
                .add(c[2].mul(x.pow(2)))
                .add(c[3].mul(x))
                .add(c[4]);
    }

    /** Durand–Kerner solver for a monic quintic given [c4,c3,c2,c1,c0]. */
    public static Complex[] solve(double[] coeffs, int iterations) {
        Complex[] c = new Complex[5];
        for (int i = 0; i < 5; i++) c[i] = Complex.real(coeffs[i]);
        Complex seed = new Complex(0.4, 0.9);
        Complex[] roots = new Complex[5];
        for (int k = 0; k < 5; k++) roots[k] = seed.pow(k);
        for (int it = 0; it < iterations; it++) {
            Complex[] next = roots.clone();
            for (int i = 0; i < 5; i++) {
                Complex num = poly5(roots[i], c);
                Complex den = new Complex(1, 0);
                for (int j = 0; j < 5; j++) if (j != i) den = den.mul(roots[i].sub(roots[j]));
                next[i] = roots[i].sub(num.div(den));
            }
            roots = next;
        }
        return roots;
    }

    public static Complex[] solve(double[] coeffs) { return solve(coeffs, 200); }

    /** Non-linear carrier phase for the k-th quinary symbol at correlation E. */
    public static double carrierPhase(int k, double correlation) {
        double base = PERIOD * (((k % 5) + 5) % 5);
        return base + correlation * Math.sin(base);
    }

    /** The quinary constellation for a given pair correlation. */
    public static Complex[] constellation(double correlation) {
        Complex[] c = new Complex[5];
        for (int k = 0; k < 5; k++) {
            double ph = carrierPhase(k, correlation);
            c[k] = new Complex(Math.cos(ph), Math.sin(ph));
        }
        return c;
    }
}
