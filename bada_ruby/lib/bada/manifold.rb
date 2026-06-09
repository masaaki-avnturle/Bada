# frozen_string_literal: true

require_relative "special"
require_relative "entropy"

module Bada
  # The Global Partial Integral Manifold and its entropy invariant.
  #
  # From "Beta function reveal with global differential manifold":
  #
  #   d/df F(x,y) = ∬ 1/(x log x)^2 dx_m + ∬ 1/(y log y)^2 dy_m
  #
  # and from the caostics / quantum reports the *global partial* differential
  # is "integrate of cut in cohomology", i.e. a measure-weighted sum of the
  # manifold element  1/(x log x)^2  carried by the token distribution.
  #
  # We turn a probability measure (the Shannon distribution of a text) into a
  # point of this manifold, integrate the manifold element against it, and
  # couple the result to the Shannon entropy through the beta/zeta gauge to
  # obtain an *invariant* Xi that survives the complex-rotation error
  # correction (see Bada::ErrorCorrection).
  module Manifold
    module_function

    # Manifold line element  dμ(x) = 1 / (x log x)^2  with a safe value at the
    # Napier circle step x -> 1 (where x log x -> 0).
    def element(x)
      return 1.0 if x <= 1.0
      xl = Special.x_log_x(x)
      return 1.0 if xl.abs < 1e-9
      1.0 / (xl * xl)
    end

    # ∬ 1/(x log x)^2 dμ  approximated as the measure-weighted manifold
    # integral over the rank coordinates of a token distribution.
    #
    # dist: array of [token, probability] sorted high->low (Entropy.distribution).
    def integral(dist)
      return 0.0 if dist.nil? || dist.empty?
      dist.each_with_index.sum do |(_, p), i|
        x = i + 2.0 # rank coordinate, start at 2 so log x > 0
        p * element(x)
      end
    end

    # The Global Partial Integral Manifold entropy invariant Xi.
    #
    #   H  = Shannon entropy of the measure              (information content)
    #   M  = global partial integral of the manifold     (geometry / curvature)
    #   Xi = zeta_gauge(p=H+1, q=M+1, x=N+1)
    #      = beta(H+1, M+1) / log(N+1)        ( the report's  zeta = beta/log x )
    #
    # The +1 shifts keep beta well defined; N is the token count (manifold
    # extent). Xi is the quantity the error corrector certifies as conserved.
    def invariant(text_or_tokens)
      tokens = text_or_tokens.is_a?(String) ? Entropy.tokenize(text_or_tokens) : text_or_tokens
      h = Entropy.shannon(tokens)
      dist = Entropy.distribution(tokens)
      m = integral(dist)
      n = tokens.length
      xi = Special.zeta_gauge(h + 1.0, m + 1.0, n + 1.0)
      {
        entropy: h,                 # Shannon H
        manifold_integral: m,       # ∬ 1/(x log x)^2 dμ
        extent: n,                  # token count
        beta: Special.beta(h + 1.0, m + 1.0),
        invariant: xi               # Xi  (global partial integral manifold entropy invariant)
      }
    end

    # Convenience: just the scalar invariant.
    def xi(text)
      invariant(text)[:invariant]
    end
  end
end
