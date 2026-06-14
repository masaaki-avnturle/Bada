# frozen_string_literal: true

module Bada
  module Prover
    # Exact univariate polynomial with Rational coefficients.
    # coeffs[i] is the coefficient of x^i. Exactness (Rational) is what makes
    # the identity proofs *sound* rather than numerical.
    class Polynomial
      attr_reader :coeffs

      def initialize(coeffs)
        @coeffs = normalize(coeffs.map { |c| c.is_a?(Rational) ? c : Rational(c) })
      end

      def self.const(c) = new([c])
      def self.x = new([0, 1])
      def self.zero = new([])
      def self.from(arr) = new(arr)

      def degree = @coeffs.empty? ? -1 : @coeffs.length - 1
      def zero? = @coeffs.empty?

      def +(other)
        a = @coeffs
        b = other.coeffs
        n = [a.length, b.length].max
        Polynomial.new(Array.new(n) { |i| (a[i] || 0) + (b[i] || 0) })
      end

      def -(other)
        a = @coeffs
        b = other.coeffs
        n = [a.length, b.length].max
        Polynomial.new(Array.new(n) { |i| (a[i] || 0) - (b[i] || 0) })
      end

      def *(other)
        return Polynomial.zero if zero? || other.zero?
        a = @coeffs
        b = other.coeffs
        out = Array.new(a.length + b.length - 1, Rational(0))
        a.each_index { |i| b.each_index { |j| out[i + j] += a[i] * b[j] } }
        Polynomial.new(out)
      end

      def ==(other) = other.is_a?(Polynomial) && @coeffs == other.coeffs
      alias eql? ==
      def hash = @coeffs.hash

      # Evaluate at an integer/rational (exact).
      def eval(n)
        acc = Rational(0)
        @coeffs.reverse_each { |c| acc = acc * n + c }
        acc
      end

      # Evaluate at an integer returning an Integer (requires integer coeffs).
      def eval_int(n)
        acc = 0
        @coeffs.reverse_each { |c| acc = acc * n + c.to_i }
        acc
      end

      def integer_coeffs? = @coeffs.all? { |c| c.denominator == 1 }

      # Substitute x -> a*x + b (exact), via binomial expansion.
      def compose_linear(a, b)
        a = Rational(a)
        b = Rational(b)
        result = Polynomial.zero
        @coeffs.each_with_index do |c, i|
          next if c.zero?
          # c * (a x + b)^i
          term = binomial_power(a, b, i) * Polynomial.const(c)
          result += term
        end
        result
      end

      def shift(d) = compose_linear(1, d) # x -> x + d

      # Lagrange interpolation through points [[x0,y0],...] (exact).
      def self.interpolate(points)
        result = Polynomial.zero
        points.each_with_index do |(xi, yi), i|
          li = Polynomial.const(Rational(yi))
          points.each_with_index do |(xj, _), j|
            next if i == j
            # (x - xj) / (xi - xj)
            denom = Rational(xi - xj)
            li *= Polynomial.new([Rational(-xj) / denom, Rational(1) / denom])
          end
          result += li
        end
        result
      end

      def to_s(var = "n")
        return "0" if zero?
        terms = []
        @coeffs.each_with_index do |c, i|
          next if c.zero?
          terms << format_term(c, i, var)
        end
        s = terms.reverse.join(" + ")
        s.gsub("+ -", "- ")
      end

      def to_latex(var = "n") = to_s(var).gsub(/\^(\d+)/, '^{\1}')

      private

      def binomial_power(a, b, n)
        # (a x + b)^n
        acc = Polynomial.const(1)
        ax_b = Polynomial.new([b, a])
        n.times { acc *= ax_b }
        acc
      end

      def format_term(c, i, var)
        cs = c.denominator == 1 ? c.numerator.to_s : "#{c.numerator}/#{c.denominator}"
        if i.zero?
          cs
        elsif i == 1
          c == 1 ? var : (c == -1 ? "-#{var}" : "#{cs}#{var}")
        else
          base = "#{var}^#{i}"
          c == 1 ? base : (c == -1 ? "-#{base}" : "#{cs}#{base}")
        end
      end

      def normalize(arr)
        arr = arr.dup
        arr.pop while !arr.empty? && arr.last.zero?
        arr
      end
    end
  end
end
