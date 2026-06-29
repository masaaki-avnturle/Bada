package com.yamaguchi.bada.engine

import kotlin.math.ln

/**
 * Shannon entropy and tokenization (port of bada_ruby/lib/bada/entropy.rb).
 *
 * ASCII words stay grouped; each CJK character is its own token, so mixed
 * Japanese / English / math text yields a meaningful Shannon distribution.
 */
object Entropy {
    private val TOKEN_RE = Regex("[A-Za-z0-9_]+|[\\u4E00-\\u9FFF\\u3040-\\u309F\\u30A0-\\u30FF]")

    fun tokenize(text: String): List<String> =
        TOKEN_RE.findAll(text).map { it.value }.toList()

    private fun log2(x: Double) = ln(x) / ln(2.0)

    /** Shannon entropy (bits) of a token list. */
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

    fun of(text: String): Double = shannon(tokenize(text))

    /** Probability distribution (sorted high->low) over tokens. */
    fun distribution(tokens: List<String>): List<Pair<String, Double>> {
        if (tokens.isEmpty()) return emptyList()
        val freq = HashMap<String, Int>()
        for (t in tokens) freq[t] = (freq[t] ?: 0) + 1
        val total = tokens.size.toDouble()
        return freq.map { (tok, c) -> tok to c / total }.sortedByDescending { it.second }
    }
}
