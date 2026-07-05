# frozen_string_literal: true

module OmegaIQ
  # A Laurent polynomial in one variable, stored as { exponent(Integer) => coeff(Integer) }.
  # Exponents may be negative. Used for the Kauffman bracket (variable A) and,
  # after the A -> t^{-1/4} substitution, for the Jones polynomial (variable t,
  # exponents counted in quarter-units so that half/quarter powers stay exact).
  class Laurent
    attr_reader :terms

    def initialize(terms = {})
      @terms = Hash.new(0)
      terms.each { |e, c| @terms[e] += c }
      prune!
    end

    def self.mono(exp, coeff = 1)
      new(exp => coeff)
    end

    def self.zero
      new
    end

    def +(other)
      Laurent.new(@terms.merge(other.terms) { |_k, a, b| a + b })
    end

    def *(other)
      out = Hash.new(0)
      @terms.each do |e1, c1|
        other.terms.each { |e2, c2| out[e1 + e2] += c1 * c2 }
      end
      Laurent.new(out)
    end

    # Raise to a non-negative integer power.
    def pow(n)
      raise ArgumentError, "negative power" if n.negative?
      result = Laurent.mono(0, 1)
      n.times { result *= self }
      result
    end

    def zero?
      @terms.empty?
    end

    def min_exp
      @terms.keys.min
    end

    def max_exp
      @terms.keys.max
    end

    # Numeric evaluation at a real point (quarter-exponents => x is t^{1/4}-scaled by caller).
    def eval(x)
      @terms.sum { |e, c| c * (x**e) }
    end

    def prune!
      @terms.reject! { |_e, c| c.zero? }
      self
    end
    private :prune!

    # Pretty print in a mathematical variable. Exponents are shown as-is unless a
    # `scale` is given (Jones uses scale=4 so quarter-units render as t powers).
    def to_s(var = "A", scale = 1)
      return "0" if zero?
      @terms.sort_by { |e, _| -e }.map do |e, c|
        exp = Rational(e, scale)
        mag = c.abs
        sign = c.negative? ? "-" : "+"
        body =
          if exp.zero?
            mag.to_s
          else
            base = (mag == 1 ? var : "#{mag}#{var}")
            exp == 1 ? base : "#{base}^#{exp.denominator == 1 ? exp.to_i : exp}"
          end
        "#{sign} #{body}"
      end.join(" ").sub(/\A\+ /, "")
    end
  end

  # Jones polynomial via the Kauffman bracket state sum over the diagram.
  #
  # A crossing is [id, e0, e1, e2, e3, sign] in the KnotTheory X[e0,e1,e2,e3]
  # convention: the four arcs counter-clockwise with e0 the incoming under-arc
  # (so e0,e2 are the under-strand, e1,e3 the over-strand). `sign` is the
  # right-handed writhe sign (+1/-1). With this anchoring:
  #
  #   A-smoothing : join (e0-e1) and (e2-e3)   weight A
  #   B-smoothing : join (e1-e2) and (e3-e0)   weight A^{-1}
  #   loop value  : d = -A^2 - A^{-2}
  module Jones
    module_function

    # Kauffman bracket <D> as a Laurent polynomial in A.
    def bracket(crossings)
      return Laurent.mono(0, 1) if crossings.empty?

      n = crossings.length
      labels = crossings.flat_map { |c| c[1, 4] }.uniq
      loop_val = Laurent.new(2 => -1, -2 => -1) # -A^2 - A^{-2}

      total = Laurent.zero
      (0...(1 << n)).each do |state|
        uf = UnionFind.new(labels)
        a_count = 0
        crossings.each_with_index do |c, i|
          a_smoothing = state[i].zero?
          apply_smoothing(uf, c, a_smoothing)
          a_count += 1 if a_smoothing
        end
        b_count = n - a_count
        loops = uf.component_count
        total += Laurent.mono(a_count - b_count, 1) * loop_val.pow(loops - 1)
      end
      total
    end

    # Union the two arc-pairs for the chosen smoothing of one crossing.
    def apply_smoothing(uf, crossing, a_smoothing)
      _id, e0, e1, e2, e3, _s = crossing
      pairs = a_smoothing ? [[e0, e1], [e2, e3]] : [[e1, e2], [e3, e0]]
      pairs.each { |x, y| uf.union(x, y) }
    end

    def writhe(crossings)
      crossings.sum { |c| c[5] }
    end

    # 真逆 — the mirror image of the diagram. Swapping every over/under strand
    # rotates the anchored arc order by one (e0 <- e1) and negates every sign;
    # this exchanges the A- and B-smoothings, so its Jones polynomial is V(1/t):
    # the exact-opposite (mirror) knot, the knot-theory face of the framework's
    # 真逆 principle (Na<->K, 上がる作用<->下げる作用).
    def mirror(crossings)
      crossings.map { |id, e0, e1, e2, e3, s| [id, e1, e2, e3, e0, -s] }
    end

    # Normalised bracket  f = (-A^3)^{-w} <D>  (a Laurent polynomial in A).
    def normalised(crossings)
      w = writhe(crossings)
      neg_a3 = Laurent.new(3 => -1) # -A^3
      factor =
        if w >= 0
          # (-A^3)^{-w} = ((-A^3)^{-1})^{w}; invert by negating exponent & sign
          inv = Laurent.new(-3 => -1) # (-A^3)^{-1} = -A^{-3}
          inv.pow(w)
        else
          neg_a3.pow(-w)
        end
      factor * bracket(crossings)
    end

    # Jones polynomial V(t). Returned as a Laurent whose exponents are in
    # QUARTER units of t (substitution A = t^{-1/4}, so A^k -> t^{-k/4}, i.e.
    # quarter-exponent = -k). Render with Laurent#to_s("t", 4).
    def polynomial(crossings)
      f = normalised(crossings)
      terms = {}
      f.terms.each { |a_exp, coeff| terms[-a_exp] = (terms[-a_exp] || 0) + coeff }
      Laurent.new(terms)
    end
  end

  # Minimal union-find over arbitrary labels for loop counting.
  class UnionFind
    def initialize(labels)
      @parent = {}
      @rank = Hash.new(0)
      labels.each { |l| @parent[l] = l }
    end

    def find(x)
      return x if @parent[x] == x

      @parent[x] = find(@parent[x]) # recursive path compression
    end

    def union(a, b)
      ra = find(a); rb = find(b)
      return if ra == rb
      if @rank[ra] < @rank[rb]
        @parent[ra] = rb
      elsif @rank[ra] > @rank[rb]
        @parent[rb] = ra
      else
        @parent[rb] = ra; @rank[ra] += 1
      end
    end

    def component_count
      @parent.keys.map { |k| find(k) }.uniq.length
    end
  end
end
