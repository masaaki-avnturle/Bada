package com.bada.morpho.sim

import kotlin.math.roundToInt

/** Simulated manufacturing metrics for one differentiation "batch". */
data class BatchResult(
    val targetType: String,
    val targetCount: Int,
    val totalCells: Int,
    val yieldPct: Double,     // target cells / total
    val purityPct: Double,    // target cells / committed cells
    val viabilityPct: Double, // simulated viability
    val titer: Double,        // simulated functional titer (arb. units)
    val passSpec: Boolean,
    val drugName: String
)

/**
 * DrugBatch — turns a differentiation result into SIMULATED manufacturing
 * numbers (yield, purity, viability, titer, spec pass/fail).
 *
 * ⚠️ These are illustrative simulation outputs from a toy model. They do NOT
 * represent a real bioprocess, real iPS protocol, or any actual medicine.
 */
object DrugBatch {

    // spec thresholds for a "passing" simulated batch
    private const val MIN_PURITY = 75.0
    private const val MIN_VIABILITY = 80.0

    fun evaluate(
        counts: Map<String, Int>,
        targetType: String,
        fieldStrength: Double,
        differentiatedFraction: Double,
        drugName: String
    ): BatchResult {
        val total = counts.values.sum().coerceAtLeast(1)
        val target = counts[targetType] ?: 0
        val committed = counts.filterKeys { it != "iPS細胞" }.values.sum().coerceAtLeast(1)

        val yieldPct = 100.0 * target / total
        val purityPct = 100.0 * target / committed
        // viability nudged by how "settled" the field/diffusion is
        val viabilityPct = (78.0 + 18.0 * differentiatedFraction - 6.0 * (1.0 - fieldStrength))
            .coerceIn(40.0, 99.0)
        val titer = (target * (purityPct / 100.0) * (viabilityPct / 100.0) * 10.0)

        val pass = purityPct >= MIN_PURITY && viabilityPct >= MIN_VIABILITY && target > 0

        return BatchResult(
            targetType = targetType,
            targetCount = target,
            totalCells = total,
            yieldPct = round1(yieldPct),
            purityPct = round1(purityPct),
            viabilityPct = round1(viabilityPct),
            titer = round1(titer),
            passSpec = pass,
            drugName = drugName
        )
    }

    private fun round1(v: Double): Double = (v * 10.0).roundToInt() / 10.0
}
