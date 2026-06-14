package com.bada.morpho.sim

/**
 * Gray-Scott reaction-diffusion on a square grid, masked to a circle (the
 * "circular container"). Produces Turing-type morphogenetic patterns.
 *
 *   ∂u/∂t = Du·∇²u − u·v² + f·(1 − u)
 *   ∂v/∂t = Dv·∇²v + u·v² − (f + k)·v
 *
 * The "field" controls (fieldX, fieldY, fieldStrength) add a gentle advection
 * bias — an ABSTRACT stand-in for the requested electromagnetic/anti-gravity
 * "field". It is a simulation parameter only, not a physical apparatus.
 */
class ReactionDiffusion(val n: Int = 96) {
    var u = FloatArray(n * n) { 1f }
    var v = FloatArray(n * n) { 0f }
    private var u2 = FloatArray(n * n)
    private var v2 = FloatArray(n * n)
    private val inside = BooleanArray(n * n)

    var feed = 0.037f
    var kill = 0.060f
    var du = 0.16f
    var dv = 0.08f
    var fieldX = 0f
    var fieldY = 0f
    var fieldStrength = 0f

    init { reset() }

    fun reset() {
        val r = n / 2f
        for (y in 0 until n) for (x in 0 until n) {
            val i = y * n + x
            val dx = x - r; val dy = y - r
            inside[i] = (dx * dx + dy * dy) <= (r - 1) * (r - 1)
            u[i] = 1f; v[i] = 0f
        }
        // seed a central cluster of v (the differentiating focus)
        val c = n / 2
        for (y in c - 4 until c + 4) for (x in c - 4 until c + 4) {
            val i = y * n + x
            if (i in 0 until n * n) { u[i] = 0.5f; v[i] = 0.25f }
        }
    }

    /** Advance the simulation by [steps] Euler steps. */
    fun step(steps: Int = 8) {
        repeat(steps) {
            for (y in 1 until n - 1) for (x in 1 until n - 1) {
                val i = y * n + x
                if (!inside[i]) { u2[i] = 1f; v2[i] = 0f; continue }
                val lu = laplacian(u, x, y)
                val lv = laplacian(v, x, y)
                val uvv = u[i] * v[i] * v[i]
                // field advection bias (abstract)
                val bias = fieldStrength * 0.02f
                val adU = bias * (fieldX * (u[i + 1] - u[i - 1]) + fieldY * (u[i + n] - u[i - n]))
                val adV = bias * (fieldX * (v[i + 1] - v[i - 1]) + fieldY * (v[i + n] - v[i - n]))
                u2[i] = (u[i] + du * lu - uvv + feed * (1f - u[i]) - adU).coerceIn(0f, 1f)
                v2[i] = (v[i] + dv * lv + uvv - (feed + kill) * v[i] - adV).coerceIn(0f, 1f)
            }
            val tu = u; u = u2; u2 = tu
            val tv = v; v = v2; v2 = tv
        }
    }

    private fun laplacian(g: FloatArray, x: Int, y: Int): Float {
        val i = y * n + x
        return g[i - 1] + g[i + 1] + g[i - n] + g[i + n] - 4f * g[i]
    }

    fun isInside(x: Int, y: Int) = inside[y * n + x]

    /** Fraction of the container that has differentiated (v above threshold). */
    fun differentiatedFraction(threshold: Float = 0.2f): Float {
        var hit = 0; var tot = 0
        for (i in 0 until n * n) if (inside[i]) {
            tot++
            if (v[i] > threshold) hit++
        }
        return if (tot == 0) 0f else hit.toFloat() / tot
    }
}
