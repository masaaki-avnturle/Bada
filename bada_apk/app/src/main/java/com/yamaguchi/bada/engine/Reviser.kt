package com.yamaguchi.bada.engine

/**
 * The Reviser — @reviser as a grammar-extension transaction
 * (port of bada_ruby/lib/bada/reviser.rb).
 *
 * A production rule is a ledger fact:
 *   rule := [ "rule", name, head, pattern, denotation ]
 * committed append-only to Omega::DATABASE[grammar]. Rules are appended, never
 * overwritten (monotone); a later rule may shadow an earlier one only by higher
 * priority at lookup time, and the earlier fact remains (auditable history).
 */
object Reviser {
    val HEADS = listOf("stmt", "expr", "postfix")

    data class Rule(
        val name: String,
        val head: String,
        val pattern: String,
        val denotation: String,
        val priority: Int,
        val seq: Int
    ) {
        /** Fill the denotation's holes (_1, _2, …) from captured fragments. */
        fun elaborate(captures: List<String>): String {
            var out = denotation
            captures.forEachIndexed { i, cap -> out = out.replace("_${i + 1}", cap) }
            return out
        }
    }

    /** Omega::DATABASE[grammar] — the append-only rule ledger. */
    class RuleLedger(val db: TupleSpace = TupleSpace()) {
        private val rules = ArrayList<Rule>()
        private var seq = 0

        val size: Int get() = rules.size
        fun all(): List<Rule> = rules

        fun commit(name: String, head: String, pattern: String, denotation: String, priority: Int? = null): Rule {
            require(head in HEADS) { "unknown head $head" }
            seq += 1
            val rule = Rule(name, head, pattern, denotation, priority ?: seq, seq)
            rules.add(rule)
            db.push("rule $name : $head [$pattern] => $denotation", "Ω::grammar#$seq")
            return rule
        }

        /** Rules for a head: highest priority first (latest commit wins), then ledger order. */
        fun rulesFor(head: String): List<Rule> =
            rules.filter { it.head == head }.sortedWith(compareByDescending<Rule> { it.priority }.thenBy { it.seq })
    }
}
