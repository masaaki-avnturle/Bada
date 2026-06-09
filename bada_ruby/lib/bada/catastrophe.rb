# frozen_string_literal: true

require_relative "entropy"
require_relative "manifold"
require_relative "thurston"

module Bada
  # Thom's catastrophe theory as an *information generation* function.
  #
  # A question's entropy / manifold invariant is loaded as the control
  # parameters of a catastrophe potential V(x). The equilibrium branches are the
  # real critical points V'(x)=0; the bifurcation set (where the number of
  # branches changes — the "branch points of information decomposition") is the
  # discriminant V'=V''=0. Each stable branch seeds a distinct generated output,
  # so one question forks into several information channels.
  module Catastrophe
    module_function

    # The seven elementary catastrophes (codimension ≤ 4), with their potentials.
    CATALOG = [
      { key: :fold,        name: "Fold",              potential: "x³ + a x", controls: 1 },
      { key: :cusp,        name: "Cusp",              potential: "x⁴ + a x² + b x", controls: 2 },
      { key: :swallowtail, name: "Swallowtail",       potential: "x⁵ + a x³ + b x² + c x", controls: 3 },
      { key: :butterfly,   name: "Butterfly",         potential: "x⁶ + a x⁴ + b x³ + c x² + d x", controls: 4 },
      { key: :hyperbolic,  name: "Hyperbolic umbilic", potential: "x³ + y³ + a x y + b x + c y", controls: 3 },
      { key: :elliptic,    name: "Elliptic umbilic",  potential: "x³/3 - x y² + a(x²+y²) + b x + c y", controls: 3 },
      { key: :parabolic,   name: "Parabolic umbilic", potential: "x²y + y⁴ + a x² + b y² + c x + d y", controls: 4 }
    ].freeze

    def catalog
      CATALOG
    end

    # Real roots of the depressed cubic x³ + p x + q = 0 (Cardano /
    # trigonometric). For the cusp these are the equilibrium branches.
    def cubic_real_roots(p, q)
      if p.abs < 1e-12 && q.abs < 1e-12
        return [0.0]
      end
      disc = -(4 * p**3 + 27 * q**2) # >0 : three real roots
      if disc > 1e-12 && p < 0
        m = 2 * Math.sqrt(-p / 3.0)
        theta = Math.acos((3 * q) / (p * m)) / 3.0 rescue 0.0
        (0..2).map { |k| m * Math.cos(theta - 2 * Math::PI * k / 3.0) }.sort
      else
        # one real root via Cardano
        d = (q / 2.0)**2 + (p / 3.0)**3
        sq = Math.sqrt(d)
        u = cbrt(-q / 2.0 + sq)
        v = cbrt(-q / 2.0 - sq)
        [u + v]
      end
    end

    def cbrt(x)
      x.negative? ? -((-x)**(1.0 / 3.0)) : x**(1.0 / 3.0)
    end

    # Cusp catastrophe analysis for control parameters (a, b).
    #   V(x) = x⁴/4 + a x²/2 + b x ,  V'(x) = x³ + a x + b ,
    #   V''(x) = 3x² + a .  Bifurcation set: 4a³ + 27b² = 0.
    def cusp(a, b)
      roots = cubic_real_roots(a, b)
      branches = roots.map do |x|
        v2 = 3 * x * x + a
        { x: x, stable: v2 > 0, second_derivative: v2 }
      end
      disc = 4 * a**3 + 27 * b**2
      {
        controls: [a, b],
        branches: branches,
        stable_branches: branches.select { |br| br[:stable] },
        branch_count: roots.length,
        on_bifurcation: disc.abs < 1e-3,
        discriminant: disc # =0 on the cusp curve (the branch-point set)
      }
    end

    # Information generation: map a question's information (Shannon entropy +
    # manifold invariant) onto the cusp's controls, then return one generation
    # "seed" per stable branch. Each seed carries a target entropy so the
    # downstream generator produces a distinct fragment per branch.
    #
    # Returns { geometry:, controls:, branches: [ {target_h:, weight:, x:} ... ] }.
    def decompose(text, span: 1.5)
      tokens = text.is_a?(String) ? Entropy.tokenize(text) : text
      h = Entropy.shannon(tokens)
      hn = Entropy.normalized(tokens)
      xi = Manifold.invariant(tokens)[:invariant]
      place = Thurston.place_entropy(tokens)

      # Map to cusp controls: a<0 enables multi-branching; b breaks symmetry.
      a = -3.0 * (0.2 + hn) # in roughly [-3.6, -0.6]
      b = (xi - 0.05) * 4.0 # invariant offsets the fold
      cusp_state = cusp(a, b)

      stable = cusp_state[:stable_branches]
      stable = cusp_state[:branches] if stable.empty?
      total = stable.sum { |br| Math.exp(-br[:second_derivative].abs) } + 1e-9

      branches = stable.each_with_index.map do |br, i|
        weight = Math.exp(-br[:second_derivative].abs) / total
        # branch x in roughly [-2,2] -> entropy multiplier
        target_h = [h * (1.0 + span * Math.tanh(br[:x] / 2.0)), 0.3].max
        { index: i, x: br[:x], target_h: target_h, weight: weight }
      end

      {
        entropy: h,
        invariant: xi,
        geometry: place[:geometry],
        perelman_f: place[:perelman_f],
        controls: cusp_state[:controls],
        on_bifurcation: cusp_state[:on_bifurcation],
        discriminant: cusp_state[:discriminant],
        branch_count: branches.length,
        branches: branches
      }
    end
  end
end
