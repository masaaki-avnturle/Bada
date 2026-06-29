package com.yamaguchi.bada.engine

/**
 * The Global Partial Integral Manifold and its entropy invariant Xi
 * (port of bada_ruby/lib/bada/manifold.rb).
 *
 *   M  = ∬ 1/(x log x)^2 dμ  over the rank coordinates of the token distribution
 *   Xi = zeta_gauge(H+1, M+1, N+1) = beta(H+1, M+1)/log(N+1)
 */
object Manifold {

    data class Stats(
        val entropy: Double,
        val manifoldIntegral: Double,
        val extent: Int,
        val beta: Double,
        val invariant: Double
    )

    fun element(x: Double): Double {
        if (x <= 1.0) return 1.0
        val xl = Special.xLogX(x)
        if (Math.abs(xl) < 1e-9) return 1.0
        return 1.0 / (xl * xl)
    }

    fun integral(dist: List<Pair<String, Double>>): Double {
        if (dist.isEmpty()) return 0.0
        var sum = 0.0
        dist.forEachIndexed { i, (_, p) ->
            val x = i + 2.0
            sum += p * element(x)
        }
        return sum
    }

    fun invariant(tokens: List<String>): Stats {
        val h = Entropy.shannon(tokens)
        val dist = Entropy.distribution(tokens)
        val m = integral(dist)
        val n = tokens.size
        val xi = Special.zetaGauge(h + 1.0, m + 1.0, n + 1.0)
        return Stats(h, m, n, Special.beta(h + 1.0, m + 1.0), xi)
    }

    fun invariant(text: String): Stats = invariant(Entropy.tokenize(text))

    fun xi(text: String): Double = invariant(text).invariant

    fun xi(tokens: List<String>): Double = invariant(tokens).invariant
}
