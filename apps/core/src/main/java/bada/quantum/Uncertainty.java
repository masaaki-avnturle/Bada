package bada.quantum;

/**
 * Robertson–Schrödinger uncertainty and Born-rule statistics (不確定性理論 ·
 * 確率・統計). For |psi> = cos(θ/2)|0> + e^{iφ} sin(θ/2)|1>, each σ² = I so
 * Var(σ) = 1 - <σ>², and Δσx·Δσz >= |<σy>|.
 */
public final class Uncertainty {
    public static final class Report {
        public double theta, phi, deltaX, deltaZ, product, bound, bornPlus, bornMinus;
        public boolean satisfied;
    }

    static double variance(double m) { return 1.0 - m * m; }

    public static Report report(double theta, double phi) {
        Report r = new Report();
        r.theta = theta; r.phi = phi;
        double ez = Math.cos(theta);
        double ex = Math.sin(theta) * Math.cos(phi);
        double ey = Math.sin(theta) * Math.sin(phi);
        r.deltaX = Math.sqrt(variance(ex));
        r.deltaZ = Math.sqrt(variance(ez));
        r.product = r.deltaX * r.deltaZ;
        r.bound = Math.abs(ey);
        double pUp = Math.pow(Math.cos(theta / 2.0), 2);
        r.bornPlus = pUp;
        r.bornMinus = 1.0 - pUp;
        r.satisfied = r.product >= r.bound - 1e-9;
        return r;
    }
}
