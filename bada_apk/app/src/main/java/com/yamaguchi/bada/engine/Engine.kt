package com.yamaguchi.bada.engine

import kotlin.math.exp
import kotlin.math.ln
import kotlin.math.tanh

/**
 * The Unknown-Prior Engine — the runtime of the Bada language
 * (port of bada_ruby/lib/bada/engine.rb).
 *
 *   a_i = softmax(z)_i
 *   θ_i = Σ_m β_m · H_m · φ_m^(i)
 *   ψ_i = √a_i · exp(i·θ_i)
 *   q_i = |ψ_i|² / Σ_j |ψ_j|²  =  a_i        ( |e^{iθ}| = 1 )
 *
 *   Theorem 1 (zero-preservation):  a_i = 0  ⇒  q_i = 0
 *   Theorem 2 (|ψ|² = a):  the phase step changes no probability.
 */
object Engine {

    private fun log2(x: Double) = ln(x) / ln(2.0)

    fun softmax(z: List<Double>): DoubleArray {
        if (z.isEmpty()) return DoubleArray(0)
        val m = z.max()
        val exps = DoubleArray(z.size) { exp(z[it] - m) }
        var s = exps.sum()
        if (s == 0.0) s = 1.0
        return DoubleArray(z.size) { exps[it] / s }
    }

    /** The maximum-entropy prior over V outcomes (the "unknown prior"). */
    fun unknownPrior(v: Int): DoubleArray {
        require(v > 0)
        return DoubleArray(v) { 1.0 / v }
    }

    fun entropyOf(dist: DoubleArray): Double {
        var h = 0.0
        for (p in dist) if (p > 0.0) h -= p * log2(p)
        return h
    }

    /**
     * A cognitive module: a distribution (its own belief, used for the
     * per-module entropy H_m and phase field), a gain β, and an optional
     * explicit phase field.
     */
    class Module(
        val name: String,
        val dist: DoubleArray,
        val gain: Double = 1.0,
        val phase: DoubleArray? = null
    ) {
        fun entropy(): Double = entropyOf(dist)

        fun phaseField(v: Int): DoubleArray {
            phase?.let { return it }
            return DoubleArray(v) { i ->
                val p = if (i < dist.size) dist[i] else 0.0
                val s = if (p > 0.0) -log2(p) else 0.0
                Math.PI * tanh(s / 4.0)
            }
        }
    }

    class Result(
        val theta: DoubleArray,
        val posterior: DoubleArray,
        val base: DoubleArray
    )

    /** The entropy-phase cognitive system. */
    fun cognitiveSystem(base: DoubleArray, modules: List<Module> = emptyList()): Result {
        val v = base.size
        val theta = DoubleArray(v)
        for (mod in modules) {
            val hm = mod.entropy()
            val beta = mod.gain
            val field = mod.phaseField(v)
            for (i in 0 until v) theta[i] += beta * hm * field[i]
        }
        // ψ_i = √a_i · exp(iθ_i) ; |ψ_i|² = a_i since |exp(iθ)| = 1
        val abs2 = DoubleArray(v) { i -> base[i].coerceAtLeast(0.0) }
        var norm = abs2.sum()
        if (norm == 0.0) norm = 1.0
        val q = DoubleArray(v) { abs2[it] / norm }
        return Result(theta, q, base)
    }

    class Check(
        val maxProbDeviation: Double,
        val zerosPreserved: Boolean,
        val unitary: Boolean
    )

    /** Verify the two theorems on a (base, modules) configuration. */
    fun verify(base: DoubleArray, modules: List<Module> = emptyList()): Check {
        val r = cognitiveSystem(base, modules)
        var maxdiff = 0.0
        for (i in base.indices) maxdiff = maxOf(maxdiff, Math.abs(r.posterior[i] - base[i]))
        var zeros = true
        for (i in base.indices) if (base[i] <= 0.0 && Math.abs(r.posterior[i]) > 1e-15) zeros = false
        return Check(maxdiff, zeros, maxdiff < 1e-9)
    }

    /**
     * A running engine instance: an unknown prior sharpened by append-only
     * evidence. Forbidden outcomes (confident zeros) never get prior mass.
     */
    class Inference(
        private val v: Int,
        private val forbidden: List<Int> = emptyList(),
        val ledger: TupleSpace = TupleSpace(),
        private val alpha0: Double = 1.0
    ) {
        private val counts = DoubleArray(v)
        var prior: DoubleArray = maxEntropyPrior(); private set

        private fun live(): List<Int> = (0 until v).filter { it !in forbidden }

        fun maxEntropyPrior(): DoubleArray {
            val live = live()
            val p = DoubleArray(v)
            val share = if (live.isEmpty()) 0.0 else 1.0 / live.size
            for (i in live) p[i] = share
            return p
        }

        fun observe(outcome: Int): Int {
            require(outcome !in forbidden) { "outcome $outcome is forbidden (confident zero)" }
            counts[outcome] += 1.0
            ledger.push("observe #${ledger.size}: outcome=$outcome", "Ω::obs#${ledger.size}")
            prior = estimate()
            return outcome
        }

        fun estimate(): DoubleArray {
            val live = live()
            var denom = counts.sum() + alpha0
            if (denom == 0.0) denom = 1.0
            val p = DoubleArray(v)
            for (i in live) p[i] = (counts[i] + alpha0 / live.size) / denom
            var s = p.sum()
            if (s == 0.0) s = 1.0
            return DoubleArray(v) { p[it] / s }
        }

        fun forbidden(): List<Int> = forbidden.toList()
        fun entropy(): Double = entropyOf(prior)
        fun totalObservations(): Int = counts.sum().toInt()
    }
}
