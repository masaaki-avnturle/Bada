package bada.quantum;

import java.util.Random;

/**
 * Bell's experiment: CHSH inequality and its quantum violation — the
 * certificate of spooky action at a distance (不気味な遠隔作用) between a pair.
 * Classical local hidden-variable worlds obey |S| <= 2; the singlet reaches the
 * Tsirelson bound |S| = 2*sqrt(2).
 */
public final class Bell {
    public static final double A  = 0.0;
    public static final double A2 = Math.PI / 2.0;
    public static final double B  = Math.PI / 4.0;
    public static final double B2 = 3.0 * Math.PI / 4.0;
    public static final double TSIRELSON = 2.0 * Math.sqrt(2.0);

    public static double eQuantum(double a, double b) { return -Math.cos(a - b); }

    public static double chshQuantum() {
        return eQuantum(A, B) - eQuantum(A, B2) + eQuantum(A2, B) + eQuantum(A2, B2);
    }

    static int localOutcome(double angle, double lambda) {
        return Math.cos(angle - lambda) >= 0 ? 1 : -1;
    }

    static double eLocal(double a, double b, int trials, Random rng) {
        long sum = 0;
        for (int i = 0; i < trials; i++) {
            double lam = rng.nextDouble() * 2 * Math.PI;
            sum += (long) localOutcome(a, lam) * localOutcome(b, lam);
        }
        return (double) sum / trials;
    }

    public static double chshLocal(int trials, Random rng) {
        double eab  = eLocal(A,  B,  trials, rng);
        double eab2 = eLocal(A,  B2, trials, rng);
        double ea2b = eLocal(A2, B,  trials, rng);
        double ea2b2 = eLocal(A2, B2, trials, rng);
        return eab - eab2 + ea2b + ea2b2;
    }

    /** Result of the Bell experiment. */
    public static final class Result {
        public final double classicalBound = 2.0;
        public double localChsh, quantumChsh, tsirelson = TSIRELSON, margin;
        public boolean violatesLocalRealism, spookyActionCertified;
    }

    public static Result experiment(int trials, long seed) {
        Random rng = new Random(seed);
        Result r = new Result();
        r.localChsh = chshLocal(trials, rng);
        r.quantumChsh = chshQuantum();
        r.violatesLocalRealism = Math.abs(r.quantumChsh) > 2.0 + 1e-9;
        r.spookyActionCertified = Math.abs(r.quantumChsh) > Math.abs(r.localChsh) + 0.2;
        r.margin = Math.abs(r.quantumChsh) - 2.0;
        return r;
    }
}
