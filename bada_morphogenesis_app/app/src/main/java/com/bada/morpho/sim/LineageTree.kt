package com.bada.morpho.sim

import com.bada.morpho.lang.MorphMath
import kotlin.random.Random

/** A node in the differentiation lineage tree. */
data class CellNode(
    val id: Int,
    val parent: Int,
    val depth: Int,
    val fate: String,
    val x: Float,   // normalised layout position 0..1
    val y: Float,
    val terminal: Boolean
)

/**
 * Stochastic branching model of iPS-cell differentiation.
 *
 * A single induced pluripotent stem cell sits in the "unbranched" state. At
 * each generation the cusp catastrophe decides whether a cell stays
 * unbranched (monostable) or BRANCHES into committed fates (bistable region,
 * controlled by cusp_a/cusp_b and branch_prob). Leaves are terminal cell
 * types. Output type counts feed the drug-manufacturing simulation.
 *
 * This is a mathematical simulation — not a laboratory protocol.
 */
class LineageTree(
    private val cuspA: Double,
    private val cuspB: Double,
    private val branchProb: Double,
    private val maxDepth: Int = 5,
    seed: Long = 42L
) {
    private val rng = Random(seed)
    val nodes = mutableListOf<CellNode>()

    // a small fate hierarchy: iPS -> germ layers -> terminal cell types
    private val germLayers = listOf("外胚葉", "中胚葉", "内胚葉")
    private val terminalByLayer = mapOf(
        "外胚葉" to listOf("神経細胞", "表皮細胞", "網膜細胞"),
        "中胚葉" to listOf("心筋細胞", "血球細胞", "骨格筋細胞"),
        "内胚葉" to listOf("肝細胞", "膵β細胞", "肺胞細胞")
    )

    fun generate(): List<CellNode> {
        nodes.clear()
        val root = CellNode(0, -1, 0, "iPS細胞", 0.5f, 0f, false)
        nodes.add(root)
        grow(root, 0f, 1f)
        return nodes
    }

    private fun grow(node: CellNode, xLo: Float, xHi: Float) {
        if (node.depth >= maxDepth) return

        // does this cell branch? bistability widens the branch probability.
        val bistable = MorphMath.isBistable(cuspA, cuspB)
        val effProb = if (bistable) branchProb else branchProb * 0.35
        val branches = when {
            node.depth == 0 -> 3                        // iPS -> three germ layers
            rng.nextDouble() < effProb -> 2             // commit & split
            else -> 1                                   // stay on lineage
        }

        val span = xHi - xLo
        for (b in 0 until branches) {
            val childLo = xLo + span * b / branches
            val childHi = xLo + span * (b + 1) / branches
            val cx = (childLo + childHi) / 2f
            val cd = node.depth + 1
            val fate = nextFate(node, b)
            val terminal = cd >= maxDepth || terminalByLayer.values.flatten().contains(fate)
            val child = CellNode(nodes.size, node.id, cd, fate, cx, cd / maxDepth.toFloat(), terminal)
            nodes.add(child)
            if (!terminal) grow(child, childLo, childHi)
        }
    }

    private fun nextFate(parent: CellNode, branchIndex: Int): String = when (parent.depth) {
        0 -> germLayers[branchIndex % germLayers.size]
        1 -> terminalByLayer[parent.fate]?.get(branchIndex % 3) ?: "前駆細胞"
        else -> {
            // deeper: pick a terminal type consistent with ancestor layer if known
            val pool = terminalByLayer[parent.fate] ?: terminalByLayer.values.flatten()
            if (parent.terminal) parent.fate else pool[rng.nextInt(pool.size)]
        }
    }

    /** Terminal cell-type counts from the (small) visualization tree. */
    fun terminalCounts(): Map<String, Int> =
        nodes.filter { it.terminal }
            .groupingBy { it.fate }
            .eachCount()

    /**
     * Proliferation population model used for the manufacturing simulation.
     *
     * The protocol's branch_prob (and whether the cusp is bistable) "steers"
     * differentiation: a higher value concentrates the population into the
     * target cell type. Remaining cells are spread across the other terminal
     * types. Returns integer counts over [totalCells]. Transparent toy model.
     */
    fun population(target: String, totalCells: Int = 1000): Map<String, Int> {
        val allTypes = terminalByLayer.values.flatten()
        val bistable = MorphMath.isBistable(cuspA, cuspB)
        val boost = (branchProb + if (bistable) 0.15 else 0.0).coerceIn(0.0, 1.0)
        val targetFrac = (0.35 + 0.55 * boost).coerceIn(0.0, 0.95)

        val result = LinkedHashMap<String, Int>()
        val targetCount = (totalCells * targetFrac).toInt()
        result[target] = targetCount

        val others = allTypes.filter { it != target }
        var remaining = totalCells - targetCount
        val per = remaining / others.size
        for ((idx, t) in others.withIndex()) {
            val give = if (idx == others.size - 1) remaining else per
            result[t] = give
            remaining -= give
        }
        return result
    }
}
