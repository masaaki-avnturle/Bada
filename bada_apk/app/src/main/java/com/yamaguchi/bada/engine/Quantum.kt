package com.yamaguchi.bada.engine

import kotlin.math.atan2
import kotlin.math.sqrt
import kotlin.random.Random

/**
 * Omega::Quantum — a Q#-style quantum sublanguage on the engine's phase core
 * (port of bada_ruby/lib/bada/quantum.rb). The native phase amplitude
 * ψ_i = √a_i·exp(iθ_i) *is* a quantum amplitude, so no new numeric kernel is
 * introduced. A complex amplitude is kept as a (re, im) pair.
 */
object Quantum {
    private val SQRT1_2 = 1.0 / sqrt(2.0)

    class Register(val n: Int) {
        val v: Int = 1 shl n
        val re = DoubleArray(v)
        val im = DoubleArray(v)

        init { re[0] = 1.0 } // |0…0>

        fun probabilities(): DoubleArray = DoubleArray(v) { re[it] * re[it] + im[it] * im[it] }

        fun theta(): DoubleArray = DoubleArray(v) {
            if (re[it] * re[it] + im[it] * im[it] > 1e-30) atan2(im[it], re[it]) else 0.0
        }

        private fun bit(index: Int, qubit: Int) = (index shr qubit) and 1 == 1

        private fun apply1(q: Int, f: (Double, Double, Double, Double) -> DoubleArray) {
            val seen = BooleanArray(v)
            for (i in 0 until v) {
                if (seen[i] || bit(i, q)) continue
                val j = i or (1 shl q)
                val out = f(re[i], im[i], re[j], im[j]) // returns [r0,i0,r1,i1]
                re[i] = out[0]; im[i] = out[1]; re[j] = out[2]; im[j] = out[3]
                seen[i] = true; seen[j] = true
            }
        }

        /** Hadamard: uniform superposition on qubit q. */
        fun h(q: Int): Register {
            apply1(q) { r0, i0, r1, i1 ->
                doubleArrayOf((r0 + r1) * SQRT1_2, (i0 + i1) * SQRT1_2, (r0 - r1) * SQRT1_2, (i0 - i1) * SQRT1_2)
            }
            return this
        }

        /** Pauli-X (NOT). */
        fun x(q: Int): Register {
            apply1(q) { r0, i0, r1, i1 -> doubleArrayOf(r1, i1, r0, i0) }
            return this
        }

        /** Pauli-Z: pure phase (probabilities untouched — Theorem 2). */
        fun z(q: Int): Register {
            apply1(q) { r0, i0, r1, i1 -> doubleArrayOf(r0, i0, -r1, -i1) }
            return this
        }

        /** S gate: |1> ↦ i|1>. Pure phase. */
        fun s(q: Int): Register {
            apply1(q) { r0, i0, r1, i1 -> doubleArrayOf(r0, i0, -i1, r1) }
            return this
        }

        /** CNOT: a conditional index permutation (entangles). */
        fun cnot(control: Int, target: Int): Register {
            val seen = BooleanArray(v)
            for (i in 0 until v) {
                if (seen[i]) continue
                if (bit(i, control)) {
                    val j = i xor (1 shl target)
                    val tr = re[i]; val ti = im[i]
                    re[i] = re[j]; im[i] = im[j]; re[j] = tr; im[j] = ti
                    seen[i] = true; seen[j] = true
                } else seen[i] = true
            }
            return this
        }

        fun sample(rng: Random): Int {
            val r = rng.nextDouble()
            var acc = 0.0
            val p = probabilities()
            for (i in p.indices) { acc += p[i]; if (r <= acc) return i }
            return p.size - 1
        }
    }

    fun qubit(n: Int = 1): Register = Register(n)

    fun hadamardAll(reg: Register): Register {
        for (q in 0 until reg.n) reg.h(q)
        return reg
    }

    class Measurement(
        val probabilities: DoubleArray,
        val norm: Double,
        val forbidden: List<Int>,
        val committed: Int
    )

    /** Measure(reg) on a ledger: commit |ψ|² as a fact. */
    fun measure(reg: Register, ledger: TupleSpace = TupleSpace()): Measurement {
        val dist = reg.probabilities()
        ledger.push("Measure: P=${dist.joinToString(",") { "%.5f".format(it) }}", "Ω::measure#${ledger.size}")
        val forbidden = dist.indices.filter { dist[it] <= 1e-15 }
        return Measurement(dist, dist.sum(), forbidden, 1)
    }

    /** Omega::Quantum: ledger-native quantum inference (tomography). */
    class Inference(private val n: Int, val ledger: TupleSpace = TupleSpace(), seed: Long? = null) {
        private val v = 1 shl n
        private val rng = if (seed != null) Random(seed) else Random.Default
        private var engine: Engine.Inference? = null

        fun prepareUnknown(forbidden: List<Int> = emptyList()): Inference {
            engine = Engine.Inference(v, forbidden, ledger)
            return this
        }

        fun observe(reg: Register): Int {
            if (engine == null) prepareUnknown()
            val outcome = reg.sample(rng)
            engine!!.observe(outcome)
            return outcome
        }

        fun observeMany(reg: Register, shots: Int = 100): Inference {
            repeat(shots) { observe(reg) }
            return this
        }

        fun estimate(): DoubleArray = engine!!.estimate()
        fun forbidden(): List<Int> = engine!!.forbidden()
        fun entropy(): Double = engine!!.entropy()
    }
}
