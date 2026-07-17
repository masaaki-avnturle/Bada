package com.bada.oracle

import android.content.Context
import org.json.JSONObject
import kotlin.math.PI
import kotlin.math.exp
import kotlin.math.ln
import kotlin.math.sin

/**
 * OracleEngine — a PROCEDURAL message generator.
 *
 * It combines poetic fragments using a deterministic hash "shaped" by the
 * gamma function and a Shannon-entropy value. The gamma/entropy terms are the
 * project's "大域的部分積分多様体" motif — here they are ordinary math used to
 * pick fragments and to display telemetry.
 *
 * ⚠️ HONEST NOTE: This does NOT access any "Akashic Record" and does NOT
 * predict the future. Output is generated art for reflection/entertainment.
 * Nothing here should be used to make real-life decisions.
 */
object OracleEngine {

    data class Reading(
        val message: String,
        val gamma: Double,
        val entropy: Double,
        val seedHex: String
    )

    private var openings = listOf<String>()
    private var images = listOf<String>()
    private var guidance = listOf<String>()
    private var closings = listOf<String>()
    private var loaded = false

    fun load(context: Context) {
        if (loaded) return
        val text = context.assets.open("oracle/fragments.json").bufferedReader().use { it.readText() }
        val json = JSONObject(text)
        openings = json.getJSONArray("openings").toStringList()
        images = json.getJSONArray("images").toStringList()
        guidance = json.getJSONArray("guidance").toStringList()
        closings = json.getJSONArray("closings").toStringList()
        loaded = true
    }

    /**
     * Generate a reading. [question] is the user's focus text, [nonce] is
     * user-driven entropy (tap count, elapsed frames) so repeated presses
     * vary — this is procedural variation, not divination.
     */
    fun generate(question: String, nonce: Long): Reading {
        val base = (question.trim().ifEmpty { "∞" }).hashCode().toLong() and 0xffffffffL
        var seed = mix(base xor (nonce * 0x9E3779B97F4A7C15uL.toLong()))

        // entropy of a seed-derived balance, gamma of a seed-derived shape
        val p = ((seed ushr 8) and 0xffff).toDouble() / 0xffff.toDouble()
        val entropy = shannon(p.coerceIn(0.01, 0.99))
        val gShape = 1.0 + 3.0 * (((seed ushr 20) and 0xff).toDouble() / 255.0)
        val gamma = gammaLanczos(gShape)

        // gamma/entropy perturb the picks so the "engine" actually influences output
        val perturb = ((gamma * 1000).toLong() xor (entropy * 1e6).toLong())
        seed = mix(seed xor perturb)

        fun pick(list: List<String>): String {
            seed = mix(seed)
            val idx = ((seed ushr 16) and 0x7fffffff).toInt() % list.size
            return list[idx]
        }

        val message = buildString {
            append(pick(openings))
            append(pick(images))
            append("\n\n")
            append(pick(guidance))
            append("\n")
            append(pick(closings))
        }
        return Reading(message, gamma, entropy, "0x%08X".format(base))
    }

    // --- helpers ---
    private fun mix(v: Long): Long {
        var x = v
        x = x xor (x ushr 33); x *= -0x7ee3623a03d3c9f9L
        x = x xor (x ushr 29); x *= -0x3b314601e57a13adL
        x = x xor (x ushr 32)
        return x and 0x7fffffffffffffffL
    }

    private fun shannon(p: Double): Double = (-p * ln(p) - (1 - p) * ln(1 - p)) / ln(2.0)

    private val LC = doubleArrayOf(
        0.99999999999980993, 676.5203681218851, -1259.1392167224028,
        771.32342877765313, -176.61502916214059, 12.507343278686905,
        -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7
    )

    private fun gammaLanczos(x: Double): Double {
        if (x < 0.5) return PI / (sin(PI * x) * gammaLanczos(1 - x))
        val z = x - 1.0
        var a = LC[0]
        val t = z + 7.0 + 0.5
        for (i in 1 until LC.size) a += LC[i] / (z + i)
        return Math.sqrt(2 * PI) * Math.pow(t, z + 0.5) * exp(-t) * a
    }

    private fun org.json.JSONArray.toStringList(): List<String> =
        (0 until length()).map { getString(it) }
}
