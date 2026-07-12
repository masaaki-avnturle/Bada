package io.bada.codefix

import kotlin.math.abs
import kotlin.math.exp
import kotlin.math.ln
import kotlin.math.PI
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.math.log2

/**
 * A compact Kotlin port of the Bada Special / Entropy / Manifold stack —
 * enough to compute the Global Partial Integral Manifold entropy invariant Ξ,
 * which CodeFix uses to read off repair confidence (Ξ conservation = the
 * integrable-system guarantee of the complex-rotation koma geometry).
 *
 * Mirrors bada_ruby/lib/bada/{special,entropy,manifold}.rb.
 */
object Manifold {

    // ---- Special: gamma / beta / zeta gauge / x log x --------------------

    private const val LANCZOS_G = 7
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

    fun gamma(x0: Double): Double {
        if (x0 == 0.0) return Double.POSITIVE_INFINITY
        if (x0 < 0.5) {
            return PI / (sin(PI * x0) * gamma(1.0 - x0))
        }
        var x = x0 - 1.0
        var a = LANCZOS_C[0]
        val t = x + LANCZOS_G + 0.5
        for (i in 1 until LANCZOS_G + 2) a += LANCZOS_C[i] / (x + i)
        return sqrt(2 * PI) * Math.pow(t, x + 0.5) * exp(-t) * a
    }

    fun logGamma(x: Double): Double = ln(abs(gamma(x)))

    fun beta(p: Double, q: Double): Double = exp(logGamma(p) + logGamma(q) - logGamma(p + q))

    fun xLogX(x: Double): Double = if (x <= 0.0) 0.0 else x * ln(x)

    fun zetaGauge(p: Double, q: Double, x: Double): Double {
        val lx = ln(x)
        if (abs(lx) < 1e-15) return Double.POSITIVE_INFINITY
        return beta(p, q) / lx
    }

    // ---- Entropy: tokenize + Shannon -------------------------------------

    private val TOKEN_RE =
        Regex("[A-Za-z0-9_]+|[\\u4e00-\\u9fff\\u3040-\\u309f\\u30a0-\\u30ff]")

    fun tokenize(text: String): List<String> = TOKEN_RE.findAll(text).map { it.value }.toList()

    fun shannon(tokens: List<String>): Double {
        if (tokens.isEmpty()) return 0.0
        val freq = HashMap<String, Int>()
        for (t in tokens) freq[t] = (freq[t] ?: 0) + 1
        val total = tokens.size.toDouble()
        var h = 0.0
        for (v in freq.values) {
            val p = v / total
            h -= p * log2(p)
        }
        return h
    }

    private fun distribution(tokens: List<String>): List<Double> {
        if (tokens.isEmpty()) return emptyList()
        val freq = HashMap<String, Int>()
        for (t in tokens) freq[t] = (freq[t] ?: 0) + 1
        val total = tokens.size.toDouble()
        return freq.values.map { it / total }.sortedDescending()
    }

    // ---- Manifold: line element, integral, invariant Ξ -------------------

    private fun element(x: Double): Double {
        if (x <= 1.0) return 1.0
        val xl = xLogX(x)
        if (abs(xl) < 1e-9) return 1.0
        return 1.0 / (xl * xl)
    }

    private fun integral(dist: List<Double>): Double {
        if (dist.isEmpty()) return 0.0
        var acc = 0.0
        dist.forEachIndexed { i, p -> acc += p * element(i + 2.0) }
        return acc
    }

    /** The Global Partial Integral Manifold entropy invariant Ξ of a text. */
    fun invariant(text: String): Double {
        val tokens = tokenize(text)
        val h = shannon(tokens)
        val m = integral(distribution(tokens))
        val n = tokens.size
        return zetaGauge(h + 1.0, m + 1.0, n + 1.0)
    }
}
