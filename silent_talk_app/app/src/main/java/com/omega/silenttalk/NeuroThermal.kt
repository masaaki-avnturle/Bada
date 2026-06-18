package com.omega.silenttalk

import kotlin.math.cos
import kotlin.math.exp
import kotlin.math.floor
import kotlin.math.ln
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.math.tan
import kotlin.math.tanh
import kotlin.random.Random

/**
 * NeuroThermal — Kotlin port of the omega_neurothermal C core.
 *
 * 中核方程式 (山口フレームワーク, explorerfiles l.148, l.334):
 *      T' = ∫ Γ(γ)' dx_m
 *      E  = m c² − ½ m v² = ‖ds²‖ = ∫ Γ(γ)' dx_m
 *
 * 教育・可視化のための数値モデル。実医療・診断用途ではない。
 */
object NeuroThermal {

    // Lanczos g=7, n=9
    private const val G = 7.0
    private val C = doubleArrayOf(
        0.99999999999980993, 676.5203681218851, -1259.1392167224028,
        771.32342877765313, -176.61502916214059, 12.507343278686905,
        -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7
    )

    fun lgamma(x: Double): Double {
        if (x < 0.5) return ln(Math.PI / Math.abs(sin(Math.PI * x))) - lgamma(1.0 - x)
        val z = x - 1.0
        var a = C[0]
        val t = z + G + 0.5
        for (i in 1 until 9) a += C[i] / (z + i)
        return 0.5 * ln(2.0 * Math.PI) + (z + 0.5) * ln(t) - t + ln(a)
    }

    fun gamma(x: Double): Double =
        if (x < 0.5) Math.PI / (sin(Math.PI * x) * gamma(1.0 - x)) else exp(lgamma(x))

    fun digamma(xIn: Double): Double {
        var x = xIn
        var result = 0.0
        if (x <= 0.0 && x == floor(x)) return Double.NaN
        if (x < 0.0) return digamma(1.0 - x) - Math.PI / tan(Math.PI * x)
        while (x < 6.0) { result -= 1.0 / x; x += 1.0 }
        val inv = 1.0 / x
        val inv2 = inv * inv
        result += ln(x) - 0.5 * inv -
            inv2 * (1.0 / 12.0 - inv2 * (1.0 / 120.0 - inv2 * (1.0 / 252.0)))
        return result
    }

    fun gammaPrime(x: Double): Double = gamma(x) * digamma(x)

    /** T' = ∫ Γ'(γ) dx_m  (composite Simpson). */
    fun thermalEnergy(lo: Double, hi: Double, stepsIn: Int): Double {
        var steps = if (stepsIn < 2) 2 else stepsIn
        if (steps % 2 != 0) steps += 1
        val h = (hi - lo) / steps
        var sum = gammaPrime(lo) + gammaPrime(hi)
        for (i in 1 until steps) {
            val x = lo + i * h
            sum += (if (i % 2 == 0) 2.0 else 4.0) * gammaPrime(x)
        }
        return (h / 3.0) * sum
    }

    fun toCelsius(energy: Double, baseline: Double, scale: Double): Double {
        val s = if (scale <= 0.0) 1.0 else scale
        return baseline + s * tanh(energy / s)
    }

    // ---- sensors (IR + thermometer) ----
    private fun gauss(rng: Random) =
        sqrt(-2.0 * ln(rng.nextDouble() + 1e-12)) * cos(2.0 * Math.PI * rng.nextDouble())

    private const val SIGMA = 5.670374419e-8

    fun irSensor(objectC: Double, emissivity: Double, ambientC: Double,
                 noise: Double, rng: Random): Double {
        val eps = if (emissivity <= 0.0) 0.95 else emissivity
        val t = objectC + 273.15
        val ta = ambientC + 273.15
        val m = eps * SIGMA * t * t * t * t + (1 - eps) * SIGMA * ta * ta * ta * ta
        var c = Math.pow(m / SIGMA, 0.25) - 273.15
        if (noise > 0.0) c += noise * gauss(rng)
        return c
    }

    fun thermometer(trueC: Double, prev: Double, tau: Double,
                    noise: Double, rng: Random): Double {
        val ta = tau.coerceIn(0.0, 1.0)
        var y = (1.0 - ta) * trueC + ta * prev
        if (noise > 0.0) y += noise * gauss(rng)
        return y
    }

    fun fuse(irC: Double, irVar: Double, thC: Double, thVar: Double): Pair<Double, Double> {
        val wi = 1.0 / (if (irVar <= 0.0) 1e-6 else irVar)
        val wt = 1.0 / (if (thVar <= 0.0) 1e-6 else thVar)
        val f = (wi * irC + wt * thC) / (wi + wt)
        return f to 1.0 / (wi + wt)
    }

    /** A live snapshot used by the persistent sensor bar (IR + thermometer attached). */
    data class Snapshot(
        val energy: Double, val core: Double,
        val ir: Double, val thermo: Double, val fused: Double, val sd: Double
    )

    fun snapshot(rng: Random = Random.Default): Snapshot {
        val energy = thermalEnergy(1.0, 5.0, 4000)
        val core = toCelsius(energy, 37.0, 1.5)
        val ir = irSensor(core, 0.97, 25.0, 0.1, rng)
        val th = thermometer(core, core, 0.3, 0.05, rng)
        val (f, v) = fuse(ir, 0.01, th, 0.0025)
        return Snapshot(energy, core, ir, th, f, sqrt(v))
    }
}
