# frozen_string_literal: true

module Bada
  module Quantum
    # Heisenberg / Robertson–Schrödinger uncertainty and the Born-rule
    # statistics of a measurement (不確定性理論 · 確率・統計).
    #
    # For a single qubit state on the Bloch sphere
    #   |psi> = cos(θ/2)|0> + e^{iφ} sin(θ/2)|1>
    # the Pauli expectations are
    #   <σz> = cos θ,  <σx> = sinθ cosφ,  <σy> = sinθ sinφ,
    # each σ² = I so Var(σ) = 1 - <σ>². Robertson's relation for the
    # complementary pair (σx, σz) is
    #   Δσx · Δσz  >=  ½ |<[σx,σz]>|  =  |<σy>|,
    # which is our concrete, checkable uncertainty principle.
    module Uncertainty
      module_function

      def expectations(theta, phi)
        {
          z: Math.cos(theta),
          x: Math.sin(theta) * Math.cos(phi),
          y: Math.sin(theta) * Math.sin(phi)
        }
      end

      # Variance of a ±1 Pauli observable with expectation m: 1 - m^2.
      def variance(m)
        1.0 - m * m
      end

      # Born-rule outcome probabilities for a σz measurement.
      def born_probs(theta)
        p_up = Math.cos(theta / 2.0)**2
        { plus: p_up, minus: 1.0 - p_up }
      end

      # Full uncertainty report for the state (θ, φ): the standard deviations of
      # the complementary observables, the Robertson lower bound, and whether the
      # relation holds (it must, to numerical tolerance).
      def report(theta, phi)
        e = expectations(theta, phi)
        dx = Math.sqrt(variance(e[:x]))
        dz = Math.sqrt(variance(e[:z]))
        product = dx * dz
        bound = e[:y].abs
        {
          theta: theta,
          phi: phi,
          delta_x: dx,
          delta_z: dz,
          product: product,
          bound: bound,
          born: born_probs(theta),
          satisfied: product >= bound - 1e-9
        }
      end

      # Sampled Born statistics: draw N σz measurements, return the empirical
      # frequency and its distance from the theoretical probability — the
      # probability/statistics face of the measurement.
      def sample_stats(theta, trials, rng)
        p = born_probs(theta)[:plus]
        ups = 0
        trials.times { ups += 1 if rng.rand < p }
        freq = ups.to_f / trials
        { p_theory: p, p_empirical: freq, error: (freq - p).abs, trials: trials }
      end
    end
  end
end
