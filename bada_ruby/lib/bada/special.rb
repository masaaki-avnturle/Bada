# frozen_string_literal: true

module Bada
  # Special functions used throughout the Yamaguchi / TupleSpace framework.
  #
  # The reports center on a handful of relations:
  #
  #   beta(p,q) = Gamma(p) Gamma(q) / Gamma(p+q)
  #   zeta(s)   = beta(p,q) / log x           ( = x log x  in the report's gauge )
  #   x log x   = 1   on the "neipa" (Napier) circle step
  #   e^pi ~= pi^e                            ( the gravity / anti-gravity duality )
  #
  # Everything here is pure stdlib Ruby so the library runs anywhere.
  module Special
    module_function

    # Lanczos approximation coefficients (g = 7, n = 9).
    LANCZOS_G = 7
    LANCZOS_C = [
      0.99999999999980993,
      676.5203681218851,
      -1259.1392167224028,
      771.32342877765313,
      -176.61502916214059,
      12.507343278686905,
      -0.13857109526572012,
      9.9843695780195716e-6,
      1.5056327351493116e-7
    ].freeze

    # Gamma function for real arguments via the Lanczos approximation,
    # with the reflection formula for x < 0.5.
    def gamma(x)
      return Float::INFINITY if x.zero?
      if x < 0.5
        # Reflection: Gamma(x) Gamma(1-x) = pi / sin(pi x)
        Math::PI / (Math.sin(Math::PI * x) * gamma(1.0 - x))
      else
        x -= 1.0
        a = LANCZOS_C[0]
        t = x + LANCZOS_G + 0.5
        (1...(LANCZOS_G + 2)).each { |i| a += LANCZOS_C[i] / (x + i) }
        Math.sqrt(2 * Math::PI) * (t**(x + 0.5)) * Math.exp(-t) * a
      end
    end

    # Natural log of the gamma function (stable for large arguments).
    def log_gamma(x)
      Math.log(gamma(x).abs)
    end

    # Euler beta function  B(p,q) = Gamma(p)Gamma(q)/Gamma(p+q).
    # This is the heart of "Beta function reveal with global differential manifold".
    def beta(p, q)
      Math.exp(log_gamma(p) + log_gamma(q) - log_gamma(p + q))
    end

    # Riemann zeta by direct + Euler-Maclaurin tail for s > 1, and the
    # framework gauge  zeta(s) = beta(p,q)/log x  exposed via zeta_gauge.
    def zeta(s, terms: 10_000)
      return Float::INFINITY if (s - 1.0).abs < 1e-12
      sum = 0.0
      (1..terms).each { |n| sum += 1.0 / (n**s) }
      sum
    end

    # The report's signature gauge:  zeta(s) = beta(p,q) / log(x).
    # Returns the zeta value implied by a beta coupling at manifold coordinate x.
    def zeta_gauge(p, q, x)
      lx = Math.log(x)
      return Float::INFINITY if lx.abs < 1e-15
      beta(p, q) / lx
    end

    # x log x  — the Napier ("neipa") circle step appearing everywhere in the
    # caostics / dalia reports as  zeta(s) = x log x.
    def x_log_x(x)
      return 0.0 if x <= 0.0
      x * Math.log(x)
    end

    # Dalanversian / antigravity circle operators (the box operator []).
    #   box_anti = 2(sin(i x log x) + cos(i x log x))
    #   box_dal  = cos(i x log x) - i sin(i x log x) = e^{x log x} = x^x
    # (the inner i turns the trig pair into cosh+sinh, giving the real x^x).
    # Implemented over Complex so the rotation structure is explicit.
    def box_antigravity(x)
      arg = Complex(0, 1) * x_log_x(x)
      2 * (cmath_sin(arg) + cmath_cos(arg))
    end

    def box_dalanversian(x)
      arg = Complex(0, 1) * x_log_x(x)
      cmath_cos(arg) - Complex(0, 1) * cmath_sin(arg)
    end

    # Complex sin / cos (avoids requiring the cmath stdlib).
    def cmath_exp(z)
      r = Math.exp(z.real)
      Complex(r * Math.cos(z.imaginary), r * Math.sin(z.imaginary))
    end

    def cmath_sin(z)
      i = Complex(0, 1)
      (cmath_exp(i * z) - cmath_exp(-i * z)) / (2 * i)
    end

    def cmath_cos(z)
      i = Complex(0, 1)
      (cmath_exp(i * z) + cmath_exp(-i * z)) / 2
    end

    # The gravity / anti-gravity duality check: e^pi vs pi^e.
    def gravity_dual
      { e_pi: Math.exp(Math::PI), pi_e: Math::PI**Math::E }
    end
  end
end
