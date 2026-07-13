# frozen_string_literal: true

module Bada
  module Quantum
    # Bell's experiment: the CHSH inequality and its quantum violation — the
    # certificate of "spooky action at a distance" (不気味な遠隔作用) between an
    # entangled *pair*.
    #
    #   * A local hidden-variable (classical) world obeys  |S| <= 2.
    #   * Quantum mechanics for a singlet pair predicts  E(a,b) = -cos(a-b),
    #     which reaches the Tsirelson bound  |S| = 2*sqrt(2) ~= 2.828.
    #
    # The gap between the two is not solved by any radical/algebraic completion
    # of a local model — it is genuinely non-local. We expose both the exact
    # quantum prediction and a Monte-Carlo run of a local model, so the
    # violation is shown *statistically* (確率・統計).
    module Bell
      module_function

      # Standard optimal CHSH settings (radians).
      A  = 0.0
      A2 = Math::PI / 2.0
      B  = Math::PI / 4.0
      B2 = 3.0 * Math::PI / 4.0

      TSIRELSON = 2.0 * Math.sqrt(2.0)

      # Quantum correlation of the singlet pair at analyzer angles a, b.
      def e_quantum(a, b)
        -Math.cos(a - b)
      end

      # CHSH combination  S = E(a,b) - E(a,b') + E(a',b) + E(a',b').
      def chsh_quantum(a = A, a2 = A2, b = B, b2 = B2)
        e_quantum(a, b) - e_quantum(a, b2) + e_quantum(a2, b) + e_quantum(a2, b2)
      end

      # One shared-hidden-variable trial of a *local* model. A common lambda is
      # drawn; each side answers with only its own analyzer angle and lambda —
      # no communication. This is the best deterministic local strategy and it
      # cannot beat |S| <= 2.
      def local_outcome(angle, lambda)
        Math.cos(angle - lambda) >= 0 ? +1 : -1
      end

      # Monte-Carlo estimate of a local correlation E(a,b) over N trials.
      def e_local(a, b, trials, rng)
        sum = 0
        trials.times do
          lam = rng.rand * 2 * Math::PI
          sum += local_outcome(a, lam) * local_outcome(b, lam)
        end
        sum.to_f / trials
      end

      def chsh_local(trials: 20_000, rng: Random.new(1))
        eab  = e_local(A,  B,  trials, rng)
        eab2 = e_local(A,  B2, trials, rng)
        ea2b = e_local(A2, B,  trials, rng)
        ea2b2 = e_local(A2, B2, trials, rng)
        eab - eab2 + ea2b + ea2b2
      end

      # The full experiment result: the classical bound, the sampled local S,
      # the exact quantum S, the Tsirelson ceiling, and whether spooky action is
      # certified (quantum S beats the classical bound by more than the sampled
      # local model's spread).
      def experiment(trials: 20_000, seed: 1)
        rng = Random.new(seed)
        s_local = chsh_local(trials: trials, rng: rng)
        s_quantum = chsh_quantum
        {
          classical_bound: 2.0,
          local_chsh: s_local,
          quantum_chsh: s_quantum,
          tsirelson: TSIRELSON,
          violates_local_realism: s_quantum.abs > 2.0 + 1e-9,
          spooky_action_certified: s_quantum.abs > s_local.abs + 0.2,
          margin: s_quantum.abs - 2.0
        }
      end
    end
  end
end
