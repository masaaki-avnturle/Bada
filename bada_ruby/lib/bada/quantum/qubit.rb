# frozen_string_literal: true

module Bada
  module Quantum
    # Minimal, pure-Ruby two-qubit state-vector simulator.
    #
    # This is the physical substrate the whole space telegraph runs on: an
    # entangled *pair* (Alice's qubit + Bob's qubit) lives here as a length-4
    # complex amplitude vector over the basis |00>, |01>, |10>, |11> with the
    # index convention  i = 2*a + b   (a = Alice qubit, b = Bob qubit).
    #
    # Everything is done with Ruby's built-in Complex — no external deps — so it
    # runs in the same "pure stdlib" spirit as the rest of Bada.
    class Qubit2
      # basis labels for pretty printing
      LABELS = %w[00 01 10 11].freeze

      attr_reader :amp # Array(4) of Complex

      def initialize(amp = nil)
        @amp = amp || [Complex(1, 0), Complex(0, 0), Complex(0, 0), Complex(0, 0)]
      end

      # |00>
      def self.zero
        new
      end

      # The Bell state Phi+ = (|00> + |11>) / sqrt(2) — the shared entangled
      # pair that carries "spooky action at a distance".
      def self.bell_phi_plus
        s = 1.0 / Math.sqrt(2.0)
        new([Complex(s, 0), Complex(0, 0), Complex(0, 0), Complex(s, 0)])
      end

      # Prepare Phi+ from |00> by the actual circuit  H(A) then CNOT(A->B).
      def self.prepare_bell
        zero.h_a.cnot
      end

      # ---- single-/two-qubit gates (return self, mutating) -----------------

      # 4x4 gate application.
      def apply(matrix)
        out = Array.new(4, Complex(0, 0))
        4.times do |i|
          row = matrix[i]
          acc = Complex(0, 0)
          4.times { |j| acc += row[j] * @amp[j] }
          out[i] = acc
        end
        @amp = out
        self
      end

      # Hadamard on Alice's qubit (H ⊗ I).
      def h_a
        apply(GATES[:H_A])
      end

      # CNOT with Alice control, Bob target: |a,b> -> |a, a xor b>.
      def cnot
        # permutation: swap |10> (idx2) and |11> (idx3)
        @amp = [@amp[0], @amp[1], @amp[3], @amp[2]]
        self
      end

      # Pauli gates on Alice's qubit (⊗ I on Bob).
      def x_a; apply(GATES[:X_A]); end
      def y_a; apply(GATES[:Y_A]); end
      def z_a; apply(GATES[:Z_A]); end

      # Superdense-coding encoder: apply the gate named by a 2-bit symbol.
      #   00 -> I, 01 -> X, 10 -> Z, 11 -> ZX   (the four Bell rotations)
      def encode(bit_hi, bit_lo)
        z_a if bit_hi == 1
        x_a if bit_lo == 1
        self
      end

      # Bell measurement decoder: CNOT(A->B) then H(A). On the four encoded
      # Bell states this rotates them back to the computational basis so a plain
      # readout yields exactly the two bits Alice put in.
      def bell_decode
        cnot
        h_a
        self
      end

      # ---- measurement -----------------------------------------------------

      def probabilities
        @amp.map { |c| (c.abs2) }
      end

      # Deterministic readout used after bell_decode in the noiseless case:
      # returns the [a, b] bits of the highest-probability basis state.
      def readout_bits
        i = probabilities.each_with_index.max_by { |p, _| p }[1]
        [i >> 1, i & 1]
      end

      # Sampled readout using a supplied RNG (Born rule).
      def sample(rng)
        probs = probabilities
        r = rng.rand
        acc = 0.0
        probs.each_with_index do |p, i|
          acc += p
          return [i >> 1, i & 1] if r <= acc
        end
        [1, 1]
      end

      # Marginal probability that Bob reads 1 (used for the no-signaling proof).
      def bob_marginal_one
        probabilities[1] + probabilities[3] # |01> + |11|
      end

      def norm
        Math.sqrt(@amp.sum { |c| c.abs2 })
      end

      def to_s
        parts = @amp.each_with_index.filter_map do |c, i|
          next if c.abs < 1e-9
          format("(%.3f%+.3fi)|%s>", c.real, c.imaginary, LABELS[i])
        end
        parts.join(" + ")
      end

      # ---- gate matrices ---------------------------------------------------

      def self.kron(a, b)
        out = Array.new(4) { Array.new(4, Complex(0, 0)) }
        2.times do |i|
          2.times do |j|
            2.times do |k|
              2.times do |l|
                out[2 * i + k][2 * j + l] = a[i][j] * b[k][l]
              end
            end
          end
        end
        out
      end

      I2 = [[Complex(1, 0), Complex(0, 0)], [Complex(0, 0), Complex(1, 0)]].freeze
      X2 = [[Complex(0, 0), Complex(1, 0)], [Complex(1, 0), Complex(0, 0)]].freeze
      Y2 = [[Complex(0, 0), Complex(0, -1)], [Complex(0, 1), Complex(0, 0)]].freeze
      Z2 = [[Complex(1, 0), Complex(0, 0)], [Complex(0, 0), Complex(-1, 0)]].freeze
      H2 = begin
        s = 1.0 / Math.sqrt(2.0)
        [[Complex(s, 0), Complex(s, 0)], [Complex(s, 0), Complex(-s, 0)]]
      end.freeze

      GATES = {
        H_A: kron(H2, I2),
        X_A: kron(X2, I2),
        Y_A: kron(Y2, I2),
        Z_A: kron(Z2, I2)
      }.freeze
    end
  end
end
