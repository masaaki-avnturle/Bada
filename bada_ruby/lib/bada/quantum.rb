# frozen_string_literal: true

require_relative "engine"
require_relative "tuplespace"

module Bada
  # Omega::Quantum — a Q#-style quantum sublanguage realised directly on the
  # Unknown-Prior Engine's phase core, exactly as in "Reviser-Extensible
  # Grammars: a Q#-targeted quantum front end".
  #
  # The engine's native phase amplitude  ψ_i = √a_i · exp(iθ_i)  *is* a quantum
  # amplitude  α_i = √p_i · e^{iφ_i}. So:
  #
  #   p_i  ↔  a_i = |ψ_i|²        (basis-state probability)
  #   φ_i  ↔  θ_i                 (phase)
  #   H, S, T, Rz                 (gates that are pure phase or uniform-amplitude)
  #   CNOT                        (a conditional index permutation)
  #   Measure                     (a ledger commit that sharpens a max-ent prior)
  #
  # and the engine's two theorems become the quantum semantics one wants:
  #
  #   Theorem 2 (|ψ|²=a)        → pure-phase gates are unitary.
  #   Theorem 1 (zero-preserve) → a forbidden basis state (zero amplitude)
  #                               cannot be resurrected by a phase step.
  #
  # No new numeric kernel is introduced: a register is an engine distribution
  # of size a power of two, plus its phase.
  module Quantum
    module_function

    SQRT1_2 = 1.0 / Math.sqrt(2.0)

    # A quantum register over n qubits: V = 2^n complex amplitudes ψ.
    # The pair (a = |ψ|², θ = arg ψ) is exactly the engine's phase core.
    class Register
      attr_reader :n, :v, :psi

      def initialize(n)
        @n = n
        @v = 1 << n
        @psi = Array.new(@v, Complex(0.0, 0.0))
        @psi[0] = Complex(1.0, 0.0) # |0…0>
      end

      # Engine view: the base distribution a_i = |ψ_i|².
      def probabilities
        @psi.map(&:abs2)
      end
      alias a probabilities

      # Engine view: the phase field θ_i = arg ψ_i.
      def theta
        @psi.map { |c| c.abs2 > 1e-30 ? Math.atan2(c.imaginary, c.real) : 0.0 }
      end

      def bit?(index, qubit)
        ((index >> qubit) & 1) == 1
      end

      # ---- single-qubit gates ---------------------------------------------

      # Hadamard: creates uniform superposition. On |0> of one qubit this gives
      # a = [0.5, 0.5] — the paper's "uniform a + one phase module".
      def h(q)
        apply1(q) { |a0, a1| [(a0 + a1) * SQRT1_2, (a0 - a1) * SQRT1_2] }
      end

      # Pauli-X (NOT): basis flip on the qubit.
      def x(q)
        apply1(q) { |a0, a1| [a1, a0] }
      end

      # Pauli-Z: pure phase (a untouched) — unitary by Theorem 2.
      def z(q)
        apply1(q) { |a0, a1| [a0, -a1] }
      end

      # Phase gate S: |1> ↦ i|1>. Pure phase.
      def s(q)
        apply1(q) { |a0, a1| [a0, Complex(0, 1) * a1] }
      end

      # T gate: |1> ↦ e^{iπ/4}|1>. Pure phase.
      def t(q)
        ph = Complex(Math.cos(Math::PI / 4), Math.sin(Math::PI / 4))
        apply1(q) { |a0, a1| [a0, ph * a1] }
      end

      # Rz(λ): a parameterised pure-phase rotation about Z. Pure phase.
      def rz(lambda, q)
        em = Complex(Math.cos(-lambda / 2), Math.sin(-lambda / 2))
        ep = Complex(Math.cos(lambda / 2), Math.sin(lambda / 2))
        apply1(q) { |a0, a1| [em * a0, ep * a1] }
      end

      # ---- two-qubit gate --------------------------------------------------

      # CNOT: a conditional index permutation (entangles). On (a, θ) it is an
      # index remap performed structurally — the engine's core never sees it as
      # arithmetic, exactly as the paper describes.
      def cnot(control, target)
        seen = Array.new(@v, false)
        @v.times do |i|
          next if seen[i]
          if bit?(i, control)
            j = i ^ (1 << target)
            @psi[i], @psi[j] = @psi[j], @psi[i]
            seen[i] = seen[j] = true
          else
            seen[i] = true
          end
        end
        self
      end

      # ---- measurement -----------------------------------------------------

      # Measurement *distribution* a = |ψ|² (no collapse) — the value Measure
      # commits to the ledger.
      def measure_distribution
        probabilities
      end

      # Sample one basis outcome ~ |ψ|² using a deterministic-if-seeded RNG.
      def sample(rng = Random.new)
        r = rng.rand
        acc = 0.0
        probs = probabilities
        probs.each_with_index do |p, i|
          acc += p
          return i if r <= acc
        end
        probs.length - 1
      end

      # Apply a 2x2 amplitude map to the |…0…> / |…1…> pair of qubit q.
      def apply1(q)
        seen = Array.new(@v, false)
        @v.times do |i|
          next if seen[i] || bit?(i, q)
          j = i | (1 << q)
          a0 = @psi[i]
          a1 = @psi[j]
          n0, n1 = yield(a0, a1)
          @psi[i] = n0
          @psi[j] = n1
          seen[i] = seen[j] = true
        end
        self
      end
    end

    # ---- the surface: qubit / gates / Measure on the ledger ----------------

    # qubit(n) — reviser-introduced name for an engine distribution of size 2^n.
    def qubit(n = 1)
      Register.new(n)
    end

    # H(reg) — uniform superposition (applies Hadamard to every qubit).
    def hadamard_all(reg)
      reg.n.times { |q| reg.h(q) }
      reg
    end

    # Measure(reg) on a ledger: commit |ψ|² as a fact and report the outcome
    # distribution. This is where quantum computation meets unknown-prior
    # inference — a measurement is an append-only commit.
    def measure(reg, ledger: TupleSpace.new)
      dist = reg.measure_distribution
      ledger.push("Measure: P=#{dist.map { |p| format('%.5f', p) }.join(',')}",
                  key: "Ω::measure##{ledger.size}",
                  tags: { kind: :measurement, distribution: dist })
      {
        probabilities: dist,
        # |ψ|² == a to machine precision (Theorem 2 / unitarity probe):
        norm: dist.sum,
        forbidden: dist.each_index.select { |i| dist[i] <= 1e-15 }, # no-resurrection
        committed: 1
      }
    end

    # ---- Omega::Quantum: ledger-native quantum inference -------------------
    #
    # Tomography of an unknown state begins from the maximum-entropy prior — the
    # engine's honest ignorance — and sharpens monotonically with each measuring
    # commit. The full measurement record is the ledger trace; re-deriving an
    # estimate is a fold over committed facts.
    class Inference
      attr_reader :engine, :ledger

      def initialize(n, ledger: TupleSpace.new, seed: nil)
        @n = n
        @v = 1 << n
        @ledger = ledger
        @rng = seed ? Random.new(seed) : Random.new
        @engine = nil
      end

      # prepare_unknown(n): a 2^n maximum-entropy prior over basis outcomes.
      def prepare_unknown(forbidden: [])
        @engine = Engine::Inference.new(@v, forbidden: forbidden, ledger: @ledger)
        self
      end

      # observe(reg): a measuring commit that samples |ψ|² and updates the prior.
      def observe(reg)
        prepare_unknown if @engine.nil?
        outcome = reg.sample(@rng)
        @engine.observe(outcome)
        outcome
      end

      # Repeatedly measure a register and accumulate the trace.
      def observe_many(reg, shots: 100)
        shots.times { observe(reg) }
        self
      end

      # estimate(): a fold over the committed trace — the sharpened posterior.
      def estimate
        @engine.estimate
      end

      # forbidden(): basis states certified impossible (a measured selection
      # rule grounded in the ledger).
      def forbidden
        @engine.forbidden
      end

      def entropy
        @engine.entropy
      end
    end
  end
end
