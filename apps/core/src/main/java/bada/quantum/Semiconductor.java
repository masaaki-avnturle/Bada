package bada.quantum;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Semiconductor realisability (半導体で使える原理): a GaAs quantum dot emitting
 * a polarization-entangled photon pair. Fermi–Dirac occupation gives the
 * thermal bit-flip probability; WKB tunnelling gives barrier transmission.
 * Energies in eV so kT stays in eV.
 */
public final class Semiconductor {
    public static final double KB_EV = 8.617333262e-5; // eV/K

    public static final Map<String, Double> BAND_GAPS = new LinkedHashMap<>();
    static {
        BAND_GAPS.put("GaAs", 1.42);
        BAND_GAPS.put("InAs", 0.354);
        BAND_GAPS.put("InGaAs", 0.75);
        BAND_GAPS.put("Si", 1.12);
        BAND_GAPS.put("diamond(NV)", 5.47);
    }

    public static double kT(double tempK) { return KB_EV * tempK; }

    public static double fermiDirac(double energyEv, double muEv, double tempK) {
        double x = (energyEv - muEv) / kT(tempK);
        if (x > 700) x = 700;
        if (x < -700) x = -700;
        return 1.0 / (1.0 + Math.exp(x));
    }

    /** Thermal excitation across the gap (mu at mid-gap) = qubit bit-flip prob. */
    public static double thermalFlip(String material, double tempK) {
        double eg = BAND_GAPS.getOrDefault(material, 1.42);
        return fermiDirac(eg, eg / 2.0, tempK);
    }

    /** WKB transmission through barrier height ΔE (eV), width d (nm). */
    public static double tunnelling(double barrierEv, double widthNm) {
        double kappa = 5.123 * Math.sqrt(Math.max(barrierEv, 0.0));
        return Math.exp(-2.0 * kappa * widthNm);
    }

    public static final class Report {
        public String material;
        public double bandGapEv, temperatureK, kTev, bitFlipProb, tunnelling;
        public boolean feasible;
    }

    public static Report report(String material, double tempK, double barrierEv, double widthNm) {
        Report r = new Report();
        r.material = material;
        r.bandGapEv = BAND_GAPS.getOrDefault(material, 1.42);
        r.temperatureK = tempK;
        r.kTev = kT(tempK);
        r.bitFlipProb = thermalFlip(material, tempK);
        r.tunnelling = tunnelling(barrierEv, widthNm);
        r.feasible = r.bitFlipProb < 0.1;
        return r;
    }

    public static Report report(String material, double tempK) {
        return report(material, tempK, 0.3, 5.0);
    }
}
