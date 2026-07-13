# frozen_string_literal: true

module Bada
  module Quantum
    # Jones polynomial correlation of an entangled pair.
    #
    # The topological signature of "are these two strands linked?" is the Jones
    # polynomial, computed from the Kauffman bracket state sum (a pure-Ruby port
    # of omega_jones_crypto_pkg/lib/jones_key.c). We use it as the *correlation
    # invariant* of a pair:
    #
    #   * two entangled qubits  <->  the Hopf link (linked) -> non-trivial Jones
    #   * two separable qubits  <->  the 2-component unlink   -> trivial factor
    #
    # so a topological polynomial certifies whether the pair carries the
    # correlation the telegraph needs (Jones多項式に基づく相関関係).
    module Jones
      # A crossing is [e0, e1, e2, e3, sign], edges labelled by integers.
      # Diagrams below match the C example set.
      HOPF = [
        [0, 1, 2, 3, +1],
        [2, 3, 0, 1, +1]
      ].freeze

      TREFOIL = [
        [0, 1, 5, 4, +1],
        [1, 2, 3, 5, +1],
        [3, 4, 0, 2, +1]
      ].freeze

      # A tiny Laurent polynomial in A (Hash: exponent => coefficient).
      class Laurent
        attr_reader :terms

        def initialize(terms = {})
          @terms = Hash.new(0.0)
          terms.each { |e, c| @terms[e] += c }
          prune!
        end

        def self.mono(coeff, exp)
          new(exp => coeff)
        end

        def +(other)
          t = @terms.dup
          other.terms.each { |e, c| t[e] = (t[e] || 0.0) + c }
          Laurent.new(t)
        end

        def *(other)
          t = Hash.new(0.0)
          @terms.each do |e1, c1|
            other.terms.each { |e2, c2| t[e1 + e2] += c1 * c2 }
          end
          Laurent.new(t)
        end

        def prune!
          @terms.delete_if { |_, c| c.abs < 1e-9 }
          @terms[0] = 0.0 if @terms.empty?
          self
        end

        # Evaluate at a numeric A.
        def eval(a)
          @terms.sum { |e, c| c * (a**e) }
        end

        def zero?
          @terms.all? { |_, c| c.abs < 1e-9 }
        end

        def ==(other)
          (self + other * Laurent.mono(-1.0, 0)).zero? if other.is_a?(Laurent)
        end

        def to_s
          return "0" if zero?
          @terms.sort_by { |e, _| -e }
                .map { |e, c| format("%+.3g*A^%d", c, e) }
                .join(" ")
        end
      end

      module_function

      # Kauffman bracket <L> as a Laurent polynomial in A, via the 2^n state sum
      # with union-find loop counting — the exact algorithm from jones_key.c.
      def bracket(crossings)
        n = crossings.length
        return Laurent.mono(1.0, 0) if n.zero?

        max_lbl = crossings.flat_map { |cr| cr[0, 4] }.max
        u = max_lbl + 1
        d = Laurent.new(2 => -1.0, -2 => -1.0) # d = -A^2 - A^-2
        total = Laurent.new

        (0...(1 << n)).each do |s|
          parent = Array.new(u, -1)
          a_cnt = 0
          b_cnt = 0
          n.times do |i|
            cr = crossings[i]
            if (s >> i) & 1 == 0
              uf_union(parent, cr[0], cr[1]); uf_union(parent, cr[2], cr[3]); a_cnt += 1
            else
              uf_union(parent, cr[1], cr[2]); uf_union(parent, cr[3], cr[0]); b_cnt += 1
            end
          end
          loops = (0...u).map { |l| uf_find(parent, l) }.uniq.length
          weight = Laurent.mono(1.0, a_cnt - b_cnt)
          dpow = Laurent.mono(1.0, 0)
          (loops - 1).times { dpow *= d } if loops > 1
          total += weight * dpow
        end
        total
      end

      # Writhe = sum of crossing signs.
      def writhe(crossings)
        crossings.sum { |cr| cr[4] }
      end

      # Jones f_L = (-A^3)^(-writhe) * <L>, still a Laurent polynomial in A
      # (the standard  A = t^{-1/4}  substitution can be applied numerically via
      # jones_value).
      def polynomial(crossings)
        w = writhe(crossings)
        norm = Laurent.mono((-1.0)**(-w), -3 * w) # (-A^3)^(-w) = (-1)^w A^{-3w}
        norm * bracket(crossings)
      end

      # Numeric Jones value at variable t (A = t^{-1/4}).
      def jones_value(crossings, t)
        a = t**(-0.25)
        polynomial(crossings).eval(a)
      end

      # Correlation strength of a pair, in [0,1]: how far the pair's Jones value
      # sits from the trivial (unlinked) value 1 at the framework gauge t = e.
      # Entangled/Hopf -> large; separable/unlink -> ~0.
      def correlation(crossings, t: Math::E)
        v = jones_value(crossings, t)
        d = (v - 1.0).abs
        d / (1.0 + d)
      end

      # union-find helpers (port of the C code)
      def uf_find(parent, a)
        a = parent[a] while parent[a] >= 0
        a
      end

      def uf_union(parent, a, b)
        a = uf_find(parent, a)
        b = uf_find(parent, b)
        return if a == b
        if parent[a] < parent[b]
          parent[a] += parent[b]; parent[b] = a
        else
          parent[b] += parent[a]; parent[a] = b
        end
      end
    end
  end
end
