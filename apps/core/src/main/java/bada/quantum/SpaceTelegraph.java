package bada.quantum;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * SpaceTelegraph — the universal telecommunication application (宇宙での汎用
 * 電信通信機能), native Java port of Bada::Quantum::SpaceTelegraph. It ties the
 * seven ingredients (entangled pair, spooky action, quintic period carrier,
 * Jones correlation, uncertainty/statistics, semiconductor, proof) into one
 * device with a prove() certificate and a transmit() that carries a message.
 */
public final class SpaceTelegraph {
    public final String material;
    public final double tempK;
    public final int redundancy;

    public SpaceTelegraph(String material, double tempK, int redundancy) {
        this.material = material;
        this.tempK = tempK;
        this.redundancy = redundancy;
    }

    public SpaceTelegraph() { this("GaAs", 4.0, 3); }

    public static final class Proof {
        public Map<String, Boolean> certificates = new LinkedHashMap<>();
        public boolean qed;
        public Bell.Result bell;
        public double hopfCorrelation, unlinkCorrelation;
        public Uncertainty.Report uncertainty;
        public Semiconductor.Report semiconductor;
        public Complex[] quinticRoots;
    }

    public Proof prove(long seed) {
        Proof p = new Proof();
        p.bell = Bell.experiment(20_000, seed);

        p.hopfCorrelation = Jones.correlation(Jones.HOPF);
        p.unlinkCorrelation = 0.0;
        boolean jonesOk = p.hopfCorrelation > p.unlinkCorrelation + 0.1;

        boolean noSignaling = true;
        for (int i = 0; i < 4; i++) {
            double m = Qubit2.bellPhiPlus().bobMarginalOne();
            if (Math.abs(m - 0.5) >= 1e-9) noSignaling = false;
        }

        p.uncertainty = Uncertainty.report(Math.PI / 3.0, Math.PI / 4.0);

        p.quinticRoots = Quintic.rootsOfUnity();
        Complex sum = new Complex(0, 0);
        for (Complex r : p.quinticRoots) sum = sum.add(r);
        boolean periodOk = sum.abs() < 1e-6;

        p.semiconductor = Semiconductor.report(material, tempK);

        p.certificates.put("spooky_action", p.bell.violatesLocalRealism && p.bell.spookyActionCertified);
        p.certificates.put("no_signaling", noSignaling);
        p.certificates.put("jones_correlation", jonesOk);
        p.certificates.put("uncertainty", p.uncertainty.satisfied);
        p.certificates.put("quintic_period", periodOk);
        p.certificates.put("semiconductor", p.semiconductor.feasible);

        p.qed = p.certificates.values().stream().allMatch(Boolean::booleanValue);
        return p;
    }

    public Channel.Result transmit(String message, long seed) {
        return Channel.transmit(message, material, tempK, redundancy, seed);
    }

    /** Human-readable end-to-end report (証明 + 送信). */
    public String render(String message, long seed) {
        Proof pf = prove(seed);
        Channel.Result tx = transmit(message, seed);
        double corr = Bell.eQuantum(Bell.A, Bell.B);
        StringBuilder sb = new StringBuilder();
        String line = "============================================================";
        sb.append(line).append("\n");
        sb.append(" Bada 量子もつれ・汎用電信通信機 — Space Telegraph\n");
        sb.append(line).append("\n\n");

        sb.append("① ベルの実験 / 不気味な遠隔作用 (entangled pair · CHSH)\n");
        sb.append(String.format("    S_classical <= 2.000   S_local ~ %.3f   S_quantum = %.3f%n",
                pf.bell.localChsh, pf.bell.quantumChsh));
        sb.append(String.format("    Tsirelson  = %.3f   -> spooky action %s%n%n",
                pf.bell.tsirelson, pf.certificates.get("spooky_action") ? "CERTIFIED" : "no"));

        sb.append("② 5次方程式の解の公式 / 周期に合わせた非線形カリア (quintic)\n");
        sb.append("    fifth roots of unity (period 2π/5):\n");
        Complex[] roots = Quintic.rootsOfUnity();
        for (int k = 0; k < roots.length; k++) {
            sb.append(String.format("      z%d = %+.3f %+.3fi%n", k, roots[k].re, roots[k].im));
        }
        StringBuilder ph = new StringBuilder();
        for (Complex c : Quintic.constellation(corr)) {
            ph.append(String.format("%.2f ", Math.atan2(c.im, c.re)));
        }
        sb.append(String.format("    non-linear carrier phase (corr=%.3f): %s%n%n", corr, ph.toString().trim()));

        sb.append("③ Jones多項式による相関 (topological correlation)\n");
        sb.append(String.format("    <Hopf>  bracket = %s%n", Jones.bracket(Jones.HOPF)));
        sb.append(String.format("    V_Hopf(t=e) correlation = %.4f  (unlink = 0)%n%n", pf.hopfCorrelation));

        sb.append("④ 不確定性理論・確率統計 (Robertson uncertainty)\n");
        sb.append(String.format("    Δσx·Δσz = %.4f  >=  |<σy>| = %.4f  -> %s%n",
                pf.uncertainty.product, pf.uncertainty.bound, pf.uncertainty.satisfied ? "OK" : "VIOLATED"));
        sb.append(String.format("    Born P(+) = %.4f%n%n", pf.uncertainty.bornPlus));

        sb.append("⑤ 半導体で使える原理 (semiconductor feasibility)\n");
        sb.append(String.format("    %s  Eg=%.2f eV  T=%.1f K  flip=%.2e  -> %s%n%n",
                pf.semiconductor.material, pf.semiconductor.bandGapEv, pf.semiconductor.temperatureK,
                pf.semiconductor.bitFlipProb, pf.semiconductor.feasible ? "BUILDABLE" : "too hot"));

        sb.append("⑥ 証明する機能 (proof) -> QED = ").append(pf.qed).append("\n");
        for (Map.Entry<String, Boolean> e : pf.certificates.entrySet()) {
            sb.append(String.format("    [%s] %s%n", e.getValue() ? "✓" : "✗", e.getKey()));
        }
        sb.append("\n");

        sb.append("⑦ 宇宙・汎用電信通信 (superdense transmission)\n");
        sb.append(String.format("    message   : %s%n", tx.message));
        sb.append(String.format("    recovered : %s%n", tx.recovered));
        sb.append(String.format("    pairs=%d  BER=%.4f  fidelity=%.4f  lossless=%s%n",
                tx.pairsUsed, tx.ber, tx.certifiedFidelity, tx.lossless));
        sb.append(line);
        return sb.toString();
    }

    public String render(String message) { return render(message, 7L); }
}
