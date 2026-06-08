package com.bada.biofeedback.lang

import kotlin.math.PI
import kotlin.math.exp
import kotlin.math.ln
import kotlin.math.sin

/**
 * BadaMath — the mathematical core referenced by the Bada language.
 *
 * Honest note: these are real, well-defined functions (Lanczos gamma,
 * the Euler-Mascheroni constant, a Shannon-style entropy envelope). They
 * are used here to *shape sound and animation envelopes* in a reproducible,
 * aesthetically pleasing way — inspired by the project's "gamma function /
 * global partial-integration manifold / thermal entropy" motif. They do
 * NOT measure any physical quantity of the human body.
 */
object BadaMath {

    /** Euler-Mascheroni constant γ. */
    const val EULER_GAMMA = 0.5772156649015329

    private val LANCZOS_G = 7.0
    private val LANCZOS_C = doubleArrayOf(
        0.99999999999980993,
        676.5203681218851,
        -1259.1392167224028,
        771.32342877765313,
        -176.61502916214059,
        12.507343278686905,
        -0.13857109526572012,
        9.9843695780195716e-6,
        1.5056327351493116e-7
    )

    /** Gamma function Γ(x) via the Lanczos approximation. */
    fun gamma(x: Double): Double {
        if (x < 0.5) {
            // Reflection formula for x < 0.5
            return PI / (sin(PI * x) * gamma(1.0 - x))
        }
        val z = x - 1.0
        var a = LANCZOS_C[0]
        val t = z + LANCZOS_G + 0.5
        for (i in 1 until LANCZOS_C.size) {
            a += LANCZOS_C[i] / (z + i)
        }
        return Math.sqrt(2.0 * PI) * Math.pow(t, z + 0.5) * exp(-t) * a
    }

    /**
     * A normalised Gamma-distribution probability density, used as the
     * "global partial-integration manifold" envelope over a session.
     * shape k > 0, scale θ > 0. Returns f(t) for t >= 0.
     */
    fun gammaEnvelope(t: Double, k: Double, theta: Double): Double {
        if (t <= 0.0) return 0.0
        val num = Math.pow(t, k - 1.0) * exp(-t / theta)
        val den = gamma(k) * Math.pow(theta, k)
        return num / den
    }

    /**
     * Shannon-style "thermal entropy" of a two-state relaxation balance
     * p ∈ (0,1): S(p) = -p ln p - (1-p) ln(1-p), scaled by the Euler
     * constant so the curve's peak reads near 1.0. Used to drive the
     * brightness/warmth of the soundscape and the topomap glow.
     */
    fun thermalEntropy(p: Double): Double {
        val q = p.coerceIn(1e-6, 1.0 - 1e-6)
        val s = -q * ln(q) - (1.0 - q) * ln(1.0 - q)
        return s / ln(2.0) // in bits, peak = 1.0 at p = 0.5
    }

    /**
     * Session amplitude envelope at time t (seconds), combining the gamma
     * manifold with a slow entropy breathing term. Output clamped to [0,1].
     */
    fun sessionEnvelope(tSeconds: Double, durationSeconds: Double): Double {
        val u = (tSeconds / durationSeconds).coerceIn(0.0, 1.0)
        // map u into the body of a Gamma(k=2, θ=0.25) curve then renormalise
        val g = gammaEnvelope(u * 4.0 + 1e-3, 2.0, 0.6)
        val gNorm = (g / 0.42).coerceIn(0.0, 1.0) // 0.42 ≈ peak of this gamma
        // slow breathing from entropy of a sine-driven balance
        val breath = thermalEntropy(0.5 + 0.45 * sin(2.0 * PI * tSeconds / 12.0))
        return (0.6 * gNorm + 0.4 * breath).coerceIn(0.0, 1.0)
    }
}
