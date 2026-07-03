package io.bada.codefix

import java.util.Random
import kotlin.math.abs
import kotlin.math.pow

/**
 * OmegaAgi — the report-driven generative "unknown engine" (未知エンジン / AGI 分派).
 *
 * This is the Yamaguchi / TupleSpace framework's own generative AI: it does NOT
 * call any cloud LLM. Instead it ingests your uploaded reports (source code and
 * PDF text) as a measured corpus, and answers/generates by *correlating* a
 * question with that corpus through the **gamma-function global partial integral
 * manifold** invariant Ξ (Bada::Manifold):
 *
 *   H  = -Σ p·log₂ p                                  (Shannon entropy)
 *   M  = ∬ 1/(x·log x)² dμ                            (global partial integral manifold)
 *   Ξ  = β(H+1, M+1)/log(N+1) = Γ(H+1)Γ(M+1)/Γ(H+M+2) / log(N+1)
 *
 * The signature "独自に相関する" (uniquely-correlating) kernel between a question q
 * and a corpus sentence d is the Euler beta of their entropies — a pure ratio of
 * gamma functions — damped by their manifold-invariant distance:
 *
 *   corr(q,d) = β(H_q+1, H_d+1) · 1/(1+|Ξ_q − Ξ_d|)          (+ keyword overlap)
 *
 * Retrieval + an entropy-steered bigram Markov generator (Bada::Generator) then
 * produce the answer. Faithful port of bada_ruby/lib/bada/{knowledge,qa_engine,
 * generator}.rb.
 */
class OmegaAgi(seed: Long = 42L) {

    data class Sentence(
        val id: Int,
        val source: String,
        val text: String,
        val tokens: List<String>,
        val entropy: Double,
        val invariant: Double
    )

    data class Match(
        val sentence: Sentence,
        val keyword: Int,
        val kernel: Double,     // β(H_q+1, H_d+1) — the gamma-function correlation
        val deltaXi: Double,    // |Ξ_q − Ξ_d|
        val correlation: Double // combined score
    )

    data class Answer(
        val question: String,
        val questionEntropy: Double,
        val questionXi: Double,
        val targetEntropy: Double,
        val matches: List<Match>,
        val generated: String,
        val generatedEntropy: Double,
        val generatedXi: Double,
        val sourcesCount: Int,
        val sentenceCount: Int
    )

    private val sentences = ArrayList<Sentence>()
    private val sources = LinkedHashSet<String>()
    private val bigrams = HashMap<String, HashMap<String, Int>>()
    private val rng = Random(seed)

    private val SENT_SPLIT = Regex("(?<=[。.?!！])\\s*")

    // ---- ingestion (Knowledge) ------------------------------------------

    fun ingest(text: String, source: String): OmegaAgi {
        val norm = text.replace("\r\n", "\n").replace('\r', '\n')
        val paras = norm.split(Regex("\\n\\s*\\n"))
        for (p in paras) {
            val para = p.trim()
            if (para.isEmpty()) continue
            for (raw in para.split(SENT_SPLIT)) {
                val s = raw.trim()
                if (s.isEmpty()) continue
                val toks = Manifold.tokenize(s)
                if (toks.isEmpty()) continue
                val sen = Sentence(
                    id = sentences.size,
                    source = source,
                    text = s,
                    tokens = toks,
                    entropy = Manifold.shannon(toks),
                    invariant = Manifold.invariant(s)
                )
                sentences.add(sen)
                toks.zipWithNext().forEach { (a, b) ->
                    bigrams.getOrPut(a) { HashMap() }.merge(b, 1, Int::plus)
                }
            }
        }
        sources.add(source)
        return this
    }

    fun isEmpty(): Boolean = sentences.isEmpty()
    fun sentenceCount(): Int = sentences.size
    fun sourceCount(): Int = sources.size

    private fun medianEntropy(): Double {
        if (sentences.isEmpty()) return 3.0
        val hs = sentences.map { it.entropy }.sorted()
        return hs[hs.size / 2]
    }

    // ---- the gamma-manifold correlation ---------------------------------

    /** β(H_q+1, H_d+1) = Γ(H_q+1)Γ(H_d+1)/Γ(H_q+H_d+2) — the gamma-function
     *  kernel correlating two manifold points by their entropies. */
    private fun kernel(hq: Double, hd: Double): Double = Manifold.beta(hq + 1.0, hd + 1.0)

    // ---- ask (QAEngine + Generator) -------------------------------------

    fun ask(question: String, topK: Int = 5, length: Int = 26): Answer {
        val qTokens = Manifold.tokenize(question)
        val hq = Manifold.shannon(qTokens)
        val xiq = Manifold.invariant(question)
        val qlower = qTokens.map { it.lowercase() }.toSet()

        // target entropy: an explicit "H=…" request, else the corpus median.
        val hTarget = Regex("H\\s*=\\s*([0-9]*\\.?[0-9]+)")
            .find(question)?.groupValues?.get(1)?.toDoubleOrNull() ?: medianEntropy()

        val matches = sentences.map { s ->
            val overlap = s.tokens.count { qlower.contains(it.lowercase()) }
            val k = kernel(hq, s.entropy)
            val dXi = abs(xiq - s.invariant)
            val manifoldProx = 1.0 / (1.0 + dXi)
            // combined "独自の相関": gamma kernel × manifold proximity, lifted by
            // keyword overlap so on-topic sentences rank first.
            val corr = k * manifoldProx * (1.0 + overlap)
            Match(s, overlap, k, dXi, corr)
        }.sortedByDescending { it.correlation }.take(topK)

        val generated = generate(length, hTarget, matches.firstOrNull()?.sentence?.tokens?.firstOrNull())
        val gTokens = Manifold.tokenize(generated)

        return Answer(
            question = question,
            questionEntropy = hq,
            questionXi = xiq,
            targetEntropy = hTarget,
            matches = matches,
            generated = generated,
            generatedEntropy = Manifold.shannon(gTokens),
            generatedXi = Manifold.invariant(generated),
            sourcesCount = sources.size,
            sentenceCount = sentences.size
        )
    }

    // ---- entropy-steered bigram generation (Generator) ------------------

    private fun generate(length: Int, targetH: Double, seedWord: String?): String {
        if (bigrams.isEmpty()) return synth(length, targetH)
        val temps = doubleArrayOf(0.3, 0.6, 0.9, 1.2, 1.6, 2.2, 3.0)
        var best: String? = null
        var bestErr = Double.MAX_VALUE
        for (t in temps) {
            val words = sampleChain(length, t, seedWord)
            val h = Manifold.shannon(Manifold.tokenize(words.joinToString(" ")))
            val err = abs(h - targetH)
            if (err < bestErr) { bestErr = err; best = words.joinToString(" ") }
        }
        return best ?: ""
    }

    private fun sampleChain(length: Int, temp: Double, seedWord: String?): List<String> {
        val keys = bigrams.keys.toList()
        if (keys.isEmpty()) return emptyList()
        var word = seedWord?.takeIf { bigrams.containsKey(it) } ?: keys[rng.nextInt(keys.size)]
        val out = ArrayList<String>()
        out.add(word)
        repeat(length - 1) {
            val nexts = bigrams[word]
            word = if (nexts.isNullOrEmpty()) keys[rng.nextInt(keys.size)]
            else weightedPick(nexts, temp)
            out.add(word)
        }
        return out
    }

    private fun weightedPick(counts: Map<String, Int>, temp: Double): String {
        val scaled = counts.map { (w, c) -> w to c.toDouble().pow(1.0 / temp) }
        val total = scaled.sumOf { it.second }
        var r = rng.nextDouble() * total
        for ((w, v) in scaled) {
            r -= v
            if (r <= 0.0) return w
        }
        return scaled.last().first
    }

    private val SYMBOLS = listOf(
        "β(p,q)", "Γ(γ)", "ζ(s)", "π(χ,x)", "∬1/(x·log x)²", "e^{-x·log x}",
        "Ω::DATABASE", "x·log x", "e^{iθ}", "∮e^{-□}d□",
        "manifold", "entropy", "gamma", "beta", "zeta", "rotation",
        "invariant", "tuplespace", "shannon", "integral", "theory", "unknown", "engine"
    )

    private fun synth(length: Int, temp: Double): String {
        val n = maxOf((SYMBOLS.size * (temp / 3.0)).toInt(), 4)
        val sub = SYMBOLS.take(n)
        return (0 until length).joinToString(" ") { sub[rng.nextInt(sub.size)] }
    }
}
