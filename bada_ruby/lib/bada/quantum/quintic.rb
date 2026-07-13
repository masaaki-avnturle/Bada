# frozen_string_literal: true

module Bada
  module Quantum
    # The quintic (5次方程式) carrier.
    #
    # Abel–Ruffini says the general quintic has no *radical* solution formula;
    # its roots are given instead by a genuinely non-linear "solution formula"
    # (Hermite's elliptic / Bring-radical form). We do not need the elliptic
    # machinery here — we need its two structural gifts:
    #
    #   1. a **period**: the reduced quintic  z^5 = 1  has its five roots equally
    #      spaced by  2*pi/5  on the unit circle (the fifth roots of unity). That
    #      spacing is the natural period of a 5-symbol (quinary) telegraph.
    #   2. a **non-linear modulation**: because the map is not solvable by
    #      radicals, the phase advance per symbol is a non-linear function of the
    #      pair's entanglement correlation, not a plain linear ramp.
    #
    # We solve arbitrary quintics numerically (Durand–Kerner / Weierstrass) to
    # keep the "solution formula" honest and testable, and use the roots as the
    # carrier constellation for the space telegraph.
    module Quintic
      module_function

      TWO_PI = 2.0 * Math::PI
      PERIOD = TWO_PI / 5.0 # spacing of the fifth roots of unity

      # The five fifth-roots of unity  exp(2*pi*i*k/5), k = 0..4.
      def roots_of_unity
        (0...5).map { |k| Complex(Math.cos(PERIOD * k), Math.sin(PERIOD * k)) }
      end

      # Durand–Kerner solver for a monic quintic given its lower coefficients
      # [c4, c3, c2, c1, c0] of  x^5 + c4 x^4 + ... + c0.  Returns 5 complex roots.
      def solve(coeffs, iterations: 200)
        c = coeffs.map { |v| Complex(v, 0) }
        # initial guesses on a circle (classic Durand–Kerner seed 0.4+0.9i)
        seed = Complex(0.4, 0.9)
        roots = (0...5).map { |k| seed**k }
        iterations.times do
          new_roots = roots.dup
          5.times do |i|
            num = poly5(roots[i], c)
            den = Complex(1, 0)
            5.times { |j| den *= (roots[i] - roots[j]) if j != i }
            new_roots[i] = roots[i] - num / den
          end
          roots = new_roots
        end
        roots
      end

      # Evaluate  x^5 + c4 x^4 + c3 x^3 + c2 x^2 + c1 x + c0.
      def poly5(x, c)
        x**5 + c[0] * x**4 + c[1] * x**3 + c[2] * x**2 + c[3] * x + c[4]
      end

      # Bring–Jerrard style principal quintic  x^5 + p*x + q  (the form Hermite
      # solved with elliptic functions). Its discriminant governs how many real
      # roots exist, i.e. the "period" of sign changes along the real axis.
      def bring_jerrard(p, q)
        solve([0.0, 0.0, 0.0, p, q])
      end

      # Non-linear phase for the k-th quinary symbol given the entanglement
      # correlation E in [-1,1]. The base advance is the periodic k*2*pi/5; the
      # correlation warps it non-linearly (sin of the base phase), so the carrier
      # is *tuned to the equation's period* yet non-linear — exactly the
      # "方程式の周期に合わせた非線形の性質".
      def carrier_phase(k, correlation)
        base = PERIOD * (k % 5)
        base + correlation * Math.sin(base)
      end

      # The full quinary carrier constellation for a given pair correlation.
      def constellation(correlation)
        (0...5).map do |k|
          ph = carrier_phase(k, correlation)
          Complex(Math.cos(ph), Math.sin(ph))
        end
      end
    end
  end
end
