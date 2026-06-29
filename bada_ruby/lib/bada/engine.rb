# frozen_string_literal: true

require_relative "special"
require_relative "entropy"
require_relative "tuplespace"

module Bada
  # The Unknown-Prior Engine — the runtime of the Bada language.
  #
  # Formalised from M. Yamaguchi, "The Unknown-Prior Engine" and
  # "Reviser-Extensible Grammars". Three ideas meet here:
  #
  #   1. An append-only tuple ledger (Omega::DATABASE) — no fact is overwritten.
  #   2. A maximum-entropy prior — the engine begins in honest ignorance
  #      (the uniform distribution) and *earns* structure by appending evidence.
  #   3. An entropy-phase cognitive core — auxiliary modules reweight a softmax
  #      base distribution by a *unit-modulus* complex factor exp(iθ), so that:
  #
  #        a_i = softmax(z)_i                          (base distribution)
  #        θ_i = Σ_m β_m · H_m · φ_m^(i)               (accumulated phase)
  #        ψ_i = √a_i · exp(i·θ_i)                      (native phase amplitude)
  #        q_i = |ψ_i|² / Σ_j |ψ_j|²  =  a_i           (posterior; |e^{iθ}|=1)
  #
  #   Theorem 1 (zero-preservation):  a_i = 0  ⇒  q_i = 0.
  #     A confident zero can never be resurrected by any phase setting.
  #   Theorem 2 (|ψ|² = a):  the phase step changes no probability.
  #     The cognitive core is unitary on the probability simplex.
  #
  # These two provable properties are what make the engine safe: modules can
  # only *rotate* belief, never invent mass where the base model is certain
  # there is none. The quantum sublanguage (Bada::Quantum) is literally this
  # core read as a state-vector amplitude.
  module Engine
    module_function

    # ---- base distribution -------------------------------------------------

    # Numerically-stable softmax over an array of logits z.
    def softmax(z)
      return [] if z.nil? || z.empty?
      m = z.max
      exps = z.map { |zi| Math.exp(zi - m) }
      s = exps.sum
      s = 1.0 if s.zero?
      exps.map { |e| e / s }
    end

    # The maximum-entropy prior over V outcomes — the engine's honest
    # ignorance, the uniform distribution. This is the "unknown prior".
    def unknown_prior(v)
      raise ArgumentError, "V must be positive" unless v.positive?
      Array.new(v, 1.0 / v)
    end

    # Shannon entropy (bits) of a probability vector.
    def entropy_of(dist)
      dist.reduce(0.0) { |h, p| p > 0.0 ? h - p * Math.log2(p) : h }
    end

    # ---- the entropy-phase cognitive core ---------------------------------

    # A cognitive module supplies a distribution `dist` (its own belief, used
    # for the per-module entropy H_m and the phase field φ_m^(i)) and a gain β.
    # If `phase` is given it is used directly as φ_m; otherwise φ_m^(i) is
    # derived from the module's own surprisal, -log q_i, which is the honest
    # "where this module has something to say" field.
    Module = Struct.new(:name, :dist, :gain, :phase, keyword_init: true) do
      def entropy
        Engine.entropy_of(dist)
      end

      # φ_m^(i): the module's phase field over outcomes. Default: normalised
      # surprisal mapped into (-π, π], so a confident module pushes a large
      # phase and a maximally-uncertain one a flat (cancelling) phase.
      def phase_field(v)
        return phase if phase
        Array.new(v) do |i|
          p = dist[i] || 0.0
          s = p > 0.0 ? -Math.log2(p) : 0.0
          # squash surprisal into (-π, π]
          Math::PI * Math.tanh(s / 4.0)
        end
      end
    end

    # The cognitive system: combine a base distribution with modules through
    # multiplicative, unit-modulus entropy-phase coupling.
    #
    #   base:    Array<Float>   — the softmax base distribution a (sums to 1)
    #   modules: Array<Module>  — auxiliary cognitive modules
    #
    # Returns a hash with the amplitude ψ, the accumulated phase θ, and the
    # posterior q. By construction q == base (Theorem 2); the value is in the
    # *phase* ψ, which the quantum layer and the precognition layer read.
    def cognitive_system(base, modules = [])
      v = base.length
      theta = Array.new(v, 0.0)
      modules.each do |mod|
        hm = mod.entropy
        beta = mod.gain || 1.0
        field = mod.phase_field(v)
        v.times { |i| theta[i] += beta * hm * field[i] }
      end

      psi = Array.new(v) do |i|
        amp = Math.sqrt([base[i], 0.0].max)
        Complex(amp * Math.cos(theta[i]), amp * Math.sin(theta[i]))
      end

      norm = psi.reduce(0.0) { |s, c| s + c.abs2 }
      norm = 1.0 if norm.zero?
      q = psi.map { |c| c.abs2 / norm }

      { amplitude: psi, theta: theta, posterior: q, base: base }
    end

    # Verify the two engine theorems on a given (base, modules) configuration.
    # Returns the maximum |q_i − a_i| deviation and whether every confident
    # zero of the base survived into the posterior.
    def verify(base, modules = [])
      r = cognitive_system(base, modules)
      maxdiff = base.each_index.map { |i| (r[:posterior][i] - base[i]).abs }.max || 0.0
      zeros_preserved = base.each_index.all? do |i|
        base[i] <= 0.0 ? r[:posterior][i].abs <= 1e-15 : true
      end
      {
        max_prob_deviation: maxdiff,       # Theorem 2: should be ~machine-ε
        zeros_preserved: zeros_preserved,  # Theorem 1: confident zeros survive
        unitary: maxdiff < 1e-9
      }
    end

    # ---- the append-only inference loop ------------------------------------

    # A running engine instance: an unknown prior over V outcomes, sharpened by
    # evidence committed to an append-only ledger. Forbidden outcomes (a base
    # zero) are never given prior mass — the zero-aware estimator.
    class Inference
      attr_reader :v, :ledger, :prior

      # `forbidden`: indices that are confident zeros (ruled out a-priori).
      def initialize(v, forbidden: [], ledger: TupleSpace.new, concentration: 1.0)
        @v = v
        @forbidden = forbidden.to_a
        @ledger = ledger
        @alpha0 = concentration.to_f
        @counts = Array.new(v, 0.0)
        @prior = max_entropy_prior
      end

      # The maximum-entropy prior, with forbidden outcomes held at exactly zero.
      def max_entropy_prior
        live = (0...@v).reject { |i| @forbidden.include?(i) }
        p = Array.new(@v, 0.0)
        share = live.empty? ? 0.0 : 1.0 / live.length
        live.each { |i| p[i] = share }
        p
      end

      # Commit one observed outcome as an append-only fact and sharpen the prior
      # toward the empirical frequencies (a ledger-native Dirichlet update).
      def observe(outcome)
        raise "outcome #{outcome} is forbidden (confident zero)" if @forbidden.include?(outcome)
        @counts[outcome] += 1.0
        @ledger.push("observe ##{@ledger.size}: outcome=#{outcome}",
                     key: "Ω::obs##{@ledger.size}",
                     tags: { kind: :observation, outcome: outcome })
        @prior = estimate
        outcome
      end

      # estimate(): a fold over the committed trace — the zero-aware posterior.
      # Dirichlet-smoothed empirical frequency over live outcomes only.
      def estimate
        live = (0...@v).reject { |i| @forbidden.include?(i) }
        denom = @counts.sum + @alpha0
        denom = 1.0 if denom.zero?
        p = Array.new(@v, 0.0)
        live.each { |i| p[i] = (@counts[i] + @alpha0 / live.length) / denom }
        # renormalise (forbidden stay exactly zero)
        s = p.sum
        s = 1.0 if s.zero?
        p.map { |x| x / s }
      end

      # forbidden(): the basis states certified impossible — never wasted on.
      def forbidden
        @forbidden.dup
      end

      def entropy
        Engine.entropy_of(@prior)
      end

      def total_observations
        @counts.sum.to_i
      end
    end
  end
end
