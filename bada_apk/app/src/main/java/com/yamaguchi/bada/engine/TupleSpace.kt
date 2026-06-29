package com.yamaguchi.bada.engine

/**
 * Omega::DATABASE — the append-only Akashic Record / TupleSpace
 * (port of bada_ruby/lib/bada/tuplespace.rb).
 */
class TupleSpace {
    data class Tuple(
        val key: String,
        val text: String,
        val stats: Manifold.Stats,
        val tags: Map<String, Any> = emptyMap()
    )

    private val store = ArrayList<Tuple>()

    val size: Int get() = store.size
    fun all(): List<Tuple> = store

    fun push(text: String, key: String? = null, tags: Map<String, Any> = emptyMap()): Tuple {
        val stats = Manifold.invariant(text)
        val k = key ?: "Ω::${store.size}"
        val t = Tuple(k, text, stats, tags)
        store.add(t)
        return t
    }

    fun byInvariant(targetXi: Double, top: Int = 5): List<Tuple> =
        store.sortedBy { Math.abs(it.stats.invariant - targetXi) }.take(top)
}
