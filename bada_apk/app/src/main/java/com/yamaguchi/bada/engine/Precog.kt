package com.yamaguchi.bada.engine

import kotlin.math.ceil
import kotlin.math.ln
import kotlin.math.tanh
import kotlin.random.Random

/**
 * Precog — 未知事前予知エンジン (the Unknown-Prior Precognition Engine).
 *
 * The ChatGPT evolution: it predicts the *unknown prior* a question is drawn
 * from, by starting in maximum-entropy ignorance and sharpening it with
 * evidence, on the engine whose two theorems guarantee it can never resurrect a
 * confident zero. Kotlin port of bada_ruby/lib/bada/precog.rb.
 */
class Precog(seed: Long? = 42L) {
    val knowledge = Knowledge()
    val db = TupleSpace()
    val rules = Reviser.RuleLedger()
    private val seedVal = seed

    data class Hypothesis(
        val text: String,
        val invariant: Double,
        val score: Double,
        var base: Double = 0.0,
        var posterior: Double = 0.0,
        var phase: Double = 0.0
    )

    init { installDefaultGrammar() }

    fun learn(text: String, source: String = "input"): Precog {
        knowledge.ingest(text, source)
        return this
    }

    private fun installDefaultGrammar() {
        rules.commit("qubit_n", "expr", "'qubit' '(' expr ')'", "qubit(_1)")
        rules.commit("hadamard", "postfix", "'H' '(' expr ')'", "phase_uniform(_1)")
        rules.commit("entangle", "postfix", "'CNOT' '(' expr ')'", "cnot(_1)")
        rules.commit("measure", "stmt", "'Measure' '(' expr ')'", "commit_measurement(_1)")
    }

    // ---- result structures -------------------------------------------------

    class Revision(
        val observations: Int,
        val priorEntropyBefore: Double,
        val priorEntropyAfter: Double,
        val entropyDecreased: Boolean
    )

    class QuantumForesight(
        val qubits: Int,
        val probabilities: DoubleArray,
        val forbidden: List<Int>,
        val norm: Double
    )

    class Foresight(
        val question: String,
        val questionEntropy: Double,
        val questionInvariant: Double,
        val hypotheses: List<Hypothesis>,
        val rankedHypotheses: List<Hypothesis>,
        val argmaxText: String?,
        val maxProbDeviation: Double,
        val zerosPreserved: Boolean,
        val unitary: Boolean,
        val revision: Revision,
        val quantum: QuantumForesight,
        val millennium: Millennium.Analysis
    )

    // ---- the precognition pipeline ----------------------------------------

    fun foresee(question: String, want: Int = 6, shots: Int = 64): Foresight {
        val stats = Manifold.invariant(question)
        val hyps = hypothesisSpace(question, want)

        val base = Engine.softmax(hyps.map { it.score })
        val phase = DoubleArray(hyps.size) { Math.PI * tanh(hyps[it].invariant - stats.invariant) }
        val mod = Engine.Module("Ξ-proximity", base, 0.7, phase)
        val cog = Engine.cognitiveSystem(base, listOf(mod))
        val check = Engine.verify(base, listOf(mod))

        hyps.forEachIndexed { i, hy ->
            hy.base = base[i]; hy.posterior = cog.posterior[i]; hy.phase = cog.theta[i]
        }
        val ranked = hyps.sortedByDescending { it.posterior }
        var argmax = 0
        for (i in base.indices) if (base[i] > base[argmax]) argmax = i
        val forbidden = base.indices.filter { base[it] <= 1e-15 }

        val revision = reviseLoop(base, forbidden, shots)
        val quantum = quantumForesight(cog.posterior)
        val mill = Millennium.analyze(question)

        record(question, hyps.getOrNull(argmax)?.text, mill.dominant)

        return Foresight(
            question, stats.entropy, stats.invariant, hyps, ranked,
            hyps.getOrNull(argmax)?.text, check.maxProbDeviation, check.zerosPreserved, check.unitary,
            revision, quantum, mill
        )
    }

    private fun hypothesisSpace(question: String, want: Int): List<Hypothesis> {
        val hyps = ArrayList<Hypothesis>()
        if (!knowledge.isEmpty) {
            val xi = Manifold.xi(question)
            val seen = HashSet<Int>()
            val candidates = knowledge.findByKeywords(Entropy.tokenize(question.lowercase()), want) +
                knowledge.closestInvariant(xi, want)
            for (s in candidates) {
                if (!seen.add(s.id)) continue
                hyps.add(Hypothesis(s.text, s.invariant, 1.0 + 1.0 / (1.0 + Math.abs(s.invariant - xi))))
            }
        }
        if (hyps.size < 2) {
            for (p in Millennium.PROBLEMS.take(want)) {
                val xi = Manifold.xi(p.link)
                val hit = if (question.lowercase().contains(p.keywords.first().lowercase())) 1.0 else 0.0
                hyps.add(Hypothesis("${p.name}: ${p.link}", xi, 1.0 + hit))
            }
        }
        return hyps.take(minOf(want, hyps.size))
    }

    private fun reviseLoop(base: DoubleArray, forbidden: List<Int>, shots: Int): Revision {
        val inf = Engine.Inference(base.size, forbidden, db)
        val before = inf.entropy()
        val rng = if (seedVal != null) Random(seedVal) else Random.Default
        repeat(shots) {
            val r = rng.nextDouble()
            var acc = 0.0
            var outcome = base.size - 1
            for (i in base.indices) { acc += base[i]; if (r <= acc) { outcome = i; break } }
            if (outcome !in forbidden) inf.observe(outcome)
        }
        return Revision(inf.totalObservations(), before, inf.entropy(), inf.entropy() <= before + 1e-9)
    }

    private fun quantumForesight(posterior: DoubleArray): QuantumForesight {
        var n = maxOf(ceil(ln(maxOf(posterior.size, 1).toDouble()) / ln(2.0)).toInt(), 1)
        n = minOf(n, 4)
        val reg = Quantum.qubit(n)
        Quantum.hadamardAll(reg)
        reg.z(0)
        val m = Quantum.measure(reg, db)
        return QuantumForesight(n, m.probabilities, m.forbidden, m.norm)
    }

    private fun record(question: String, foreseen: String?, dominant: String) {
        db.push("Q: $question", "Ω::q#${db.size}")
        db.push("FORESEE: $foreseen", "Ω::foresee#${db.size}")
        db.push("MILLENNIUM: $dominant", "Ω::millennium#${db.size}")
    }

    // ---- human-readable rendering -----------------------------------------

    fun ask(question: String): String {
        val r = foresee(question)
        val sb = StringBuilder()
        sb.appendLine("══ 未知事前予知エンジン — Bada Unknown-Prior Precognition Engine ══")
        sb.appendLine("質問 H_q = %.4f bits · 多様体不変量 Ξ_q = %.4f".format(r.questionEntropy, r.questionInvariant))
        sb.appendLine()
        sb.appendLine("【① 未知事前分布の予知 (Unknown-Prior Engine)】")
        r.rankedHypotheses.take(5).forEachIndexed { i, hy ->
            sb.appendLine("  %d. P=%.4f (base %.4f, θ=%+.3f) %s".format(i + 1, hy.posterior, hy.base, hy.phase, truncate(hy.text, 60)))
        }
        sb.appendLine("  定理検証: |ψ|²=a 偏差 %.2e (ユニタリ=%s) · 確信ゼロ保存=%s".format(r.maxProbDeviation, r.unitary, r.zerosPreserved))
        sb.appendLine()
        sb.appendLine("【② リバイザ学習ループ (append-only)】")
        sb.appendLine("  事前エントロピー %.4f → %.4f bits（%d 回の証拠コミットで単調に鋭化, 減少=%s）".format(
            r.revision.priorEntropyBefore, r.revision.priorEntropyAfter, r.revision.observations, r.revision.entropyDecreased))
        sb.appendLine()
        sb.appendLine("【③ 量子予知 (Omega::Quantum, 位相コア)】")
        sb.appendLine("  qubit(%d) → H → Measure: P=%s".format(r.quantum.qubits, fmtArr(r.quantum.probabilities)))
        sb.appendLine("  確信ゼロ(復活不能な禁制状態)=%s · |ψ|²総和=%.6f".format(r.quantum.forbidden, r.quantum.norm))
        sb.appendLine()
        sb.appendLine("【④ ミレニアム予想分析 (Yamaguchi Framework)】")
        sb.appendLine("  主予知先: ${r.millennium.dominant}")
        sb.appendLine("  → ${r.millennium.dominantResolution}")
        r.millennium.posterior.take(3).forEach {
            sb.appendLine("    · %s  P=%.4f".format(it.problem.name, it.posterior))
        }
        sb.appendLine("  エンジン定理: |ψ|²=a 偏差 %.2e · ゼロ保存=%s".format(r.millennium.maxProbDeviation, r.millennium.zerosPreserved))
        sb.appendLine()
        sb.appendLine("Ω::DATABASE へ %d 件記録 · 文法規則 %d 件（@reviser, append-only）".format(db.size, rules.size))
        return sb.toString().trimEnd()
    }

    private fun truncate(s: String, n: Int): String = if (s.length > n) s.substring(0, n) + "…" else s
    private fun fmtArr(a: DoubleArray): String = "[" + a.joinToString(", ") { "%.4f".format(it) } + "]"
}
