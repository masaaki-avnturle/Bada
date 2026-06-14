package com.bada.silenttalk;

/**
 * Signal-fusion model for Silent Talk.
 *
 * <p>Conceptually this implements the "global integration-by-parts manifold of the
 * gamma function" referenced in the design: the body/ambient <b>thermal network</b>
 * (温度計) and the infrared proximity channel (赤外線センサー) are fused with the
 * gaze/expression signal quality through a Γ-function kernel to produce a single
 * confidence value. That confidence modulates how long the user must hold a gaze
 * (the dwell time) before a command is "spoken" silently.
 *
 * <p>NOTE: this does not read thoughts. A thermometer cannot recover cognition.
 * The thermal term is a real, observable context signal that stabilises selection
 * (e.g. a covered/near IR sensor and a steady thermal reading raise confidence).
 */
final class ThermalManifold {

    private ThermalManifold() {}

    /** Lanczos approximation of the gamma function Γ(x). */
    static double gamma(double x) {
        double[] g = {
                0.99999999999980993, 676.5203681218851, -1259.1392167224028,
                771.32342877765313, -176.61502916214059, 12.507343278686905,
                -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7
        };
        if (x < 0.5) {
            return Math.PI / (Math.sin(Math.PI * x) * gamma(1 - x));
        }
        x -= 1;
        double a = g[0];
        double t = x + 7.5;
        for (int i = 1; i < g.length; i++) a += g[i] / (x + i);
        return Math.sqrt(2 * Math.PI) * Math.pow(t, x + 0.5) * Math.exp(-t) * a;
    }

    /**
     * A Γ-shaped kernel over the body's thermal energy. Peaks for a comfortable,
     * steady thermal reading and decays away from it. Returns ~1.0 when no
     * temperature sensor is present (neutral), so the app still works everywhere.
     *
     * @param tempC ambient/skin temperature in Celsius, or NaN if unavailable.
     */
    static double thermalKernel(double tempC) {
        if (Double.isNaN(tempC)) return 1.0;
        // Map temperature to a Γ(k,θ) density with mode near 30°C and normalise to its peak.
        final double k = 6.0, theta = 5.0;          // shape / scale
        double x = Math.max(0.1, tempC);            // gamma support x > 0
        double mode = (k - 1) * theta;              // = 25; peak of the density
        double density = Math.pow(x, k - 1) * Math.exp(-x / theta)
                / (gamma(k) * Math.pow(theta, k));
        double peak = Math.pow(mode, k - 1) * Math.exp(-mode / theta)
                / (gamma(k) * Math.pow(theta, k));
        return clamp01(density / peak);
    }

    /**
     * Fuse the channels into an overall confidence in [0,1].
     *
     * @param signalQuality 0..1 from the gaze/expression tracker (face stability)
     * @param proximityNear true when the IR proximity sensor is covered/near
     * @param tempC         thermal reading, NaN if none
     */
    static double confidence(double signalQuality, boolean proximityNear, double tempC) {
        double thermal = thermalKernel(tempC);
        double ir = proximityNear ? 1.0 : 0.85;          // IR engagement bonus
        return clamp01(signalQuality * thermal * ir);
    }

    /** Higher confidence => shorter dwell needed to confirm a command. */
    static long dwellMillis(double confidence) {
        double base = 1200, min = 450;
        return (long) (min + (base - min) * (1.0 - clamp01(confidence)));
    }

    private static double clamp01(double v) {
        return v < 0 ? 0 : (v > 1 ? 1 : v);
    }
}
