package com.yamaguchi.bada.engine

import kotlin.math.PI
import kotlin.math.exp
import kotlin.math.ln
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Special functions of the Yamaguchi / TupleSpace framework.
 *
 *   beta(p,q) = Gamma(p)Gamma(q)/Gamma(p+q)
 *   zeta(s)   = beta(p,q) / log x          ( = x log x in the report's gauge )
 *
 * Pure-Kotlin port of bada_ruby/lib/bada/special.rb.
 */
object Special {
    private const val G = 7
    private val C = doubleArrayOf(
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

    /** Gamma via the Lanczos approximation with the reflection formula. */
    fun gamma(x0: Double): Double {
        if (x0 == 0.0) return Double.POSITIVE_INFINITY
        if (x0 < 0.5) return PI / (sin(PI * x0) * gamma(1.0 - x0))
        var x = x0 - 1.0
        var a = C[0]
        val t = x + G + 0.5
        for (i in 1 until G + 2) a += C[i] / (x + i)
        return sqrt(2 * PI) * Math.pow(t, x + 0.5) * exp(-t) * a
    }

    fun logGamma(x: Double): Double = ln(Math.abs(gamma(x)))

    /** Euler beta function B(p,q) = Gamma(p)Gamma(q)/Gamma(p+q). */
    fun beta(p: Double, q: Double): Double =
        exp(logGamma(p) + logGamma(q) - logGamma(p + q))

    /** The framework gauge zeta(s) = beta(p,q)/log(x). */
    fun zetaGauge(p: Double, q: Double, x: Double): Double {
        val lx = ln(x)
        if (Math.abs(lx) < 1e-15) return Double.POSITIVE_INFINITY
        return beta(p, q) / lx
    }

    /** x log x — the Napier circle step. */
    fun xLogX(x: Double): Double = if (x <= 0.0) 0.0 else x * ln(x)
}
