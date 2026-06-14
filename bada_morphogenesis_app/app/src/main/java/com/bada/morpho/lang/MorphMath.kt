package com.bada.morpho.lang

import kotlin.math.acos
import kotlin.math.cos
import kotlin.math.sqrt

/**
 * MorphMath — the mathematical core of the Bada Morphogenesis simulation.
 *
 * Everything here is a real, well-defined model:
 *  - Thom's CUSP catastrophe potential V(x) = x⁴/4 + a·x²/2 + b·x, whose
 *    equilibria (roots of x³ + a·x + b = 0) model a bistable cell-fate
 *    decision: "unbranched" stem state vs. "branched" differentiated states.
 *  - A real cubic root solver (Cardano / trigonometric form).
 *
 * Honest note: this models cell-fate *decisions* as a dynamical system. It is
 * NOT a physical device, not anti-gravity, and does not manufacture anything.
 */
object MorphMath {

    /** Cusp potential V(x; a, b). */
    fun cuspPotential(x: Double, a: Double, b: Double): Double =
        x * x * x * x / 4.0 + a * x * x / 2.0 + b * x

    /** dV/dx = x³ + a·x + b. */
    fun cuspGradient(x: Double, a: Double, b: Double): Double =
        x * x * x + a * x + b

    /**
     * Real roots of the depressed cubic x³ + p·x + q = 0.
     * Returns 1 root (monostable) or 3 roots (bistable / branched region).
     */
    fun cubicRealRoots(p: Double, q: Double): DoubleArray {
        val disc = -4.0 * p * p * p - 27.0 * q * q // > 0 => three real roots
        return if (disc > 0.0 && p < 0.0) {
            // three distinct real roots — trigonometric method
            val m = 2.0 * sqrt(-p / 3.0)
            val theta = acos((3.0 * q) / (p * m)).coerceIn(-1.0, 1.0)
            DoubleArray(3) { k ->
                m * cos(theta / 3.0 - 2.0 * Math.PI * k / 3.0)
            }
        } else {
            // one real root — Cardano
            val u = -q / 2.0
            val v = sqrt(q * q / 4.0 + p * p * p / 27.0)
            val root = cbrt(u + v) + cbrt(u - v)
            doubleArrayOf(root)
        }
    }

    /** True when control point (a,b) lies inside the cusp (bistable) region. */
    fun isBistable(a: Double, b: Double): Boolean =
        a < 0.0 && (4.0 * a * a * a + 27.0 * b * b) < 0.0

    /** Stable equilibria = roots where second derivative 3x²+a > 0. */
    fun stableStates(a: Double, b: Double): DoubleArray =
        cubicRealRoots(a, b).filter { 3.0 * it * it + a > 0.0 }.toDoubleArray()

    private fun cbrt(v: Double): Double =
        if (v < 0) -Math.cbrt(-v) else Math.cbrt(v)
}
