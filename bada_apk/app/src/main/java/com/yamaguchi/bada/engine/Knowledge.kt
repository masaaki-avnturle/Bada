package com.yamaguchi.bada.engine

/**
 * Knowledge ingestion: turn uploaded files into a measured corpus
 * (port of bada_ruby/lib/bada/knowledge.rb).
 */
class Knowledge {
    data class Sentence(
        val id: Int,
        val text: String,
        val tokens: List<String>,
        val entropy: Double,
        val invariant: Double,
        val source: String
    )

    private val sentences = ArrayList<Sentence>()
    private val sources = LinkedHashSet<String>()

    fun sentences(): List<Sentence> = sentences
    fun sources(): List<String> = sources.toList()
    val isEmpty: Boolean get() = sentences.isEmpty()
    val size: Int get() = sentences.size

    private val sentSplit = Regex("(?<=。|\\.|\\?|!|！)\\s*")

    fun ingest(text: String, source: String = "input"): Knowledge {
        sources.add(source)
        val norm = text.replace("\r\n", "\n").replace('\r', '\n')
        for (para in norm.split(Regex("\\n\\s*\\n"))) {
            for (s0 in para.split(sentSplit)) {
                val s = s0.trim()
                if (s.isEmpty()) continue
                val tokens = Entropy.tokenize(s)
                if (tokens.isEmpty()) continue
                sentences.add(
                    Sentence(
                        sentences.size, s, tokens,
                        Entropy.shannon(tokens),
                        Manifold.invariant(tokens).invariant,
                        source
                    )
                )
            }
        }
        return this
    }

    fun findByKeywords(keywords: List<String>, top: Int = 5): List<Sentence> {
        val kws = keywords.map { it.lowercase() }
        return sentences.map { s ->
            val txt = s.text.lowercase()
            val score = kws.sumOf { k -> Regex(Regex.escape(k)).findAll(txt).count() }
            score to s
        }.filter { it.first > 0 }.sortedByDescending { it.first }.take(top).map { it.second }
    }

    fun closestInvariant(target: Double, top: Int = 5): List<Sentence> =
        sentences.sortedBy { Math.abs(it.invariant - target) }.take(top)
}
