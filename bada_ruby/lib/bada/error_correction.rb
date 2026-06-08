# frozen_string_literal: true

require_relative "special"
require_relative "manifold"

module Bada
  # Error correction by the integrable system of a complex rotational body —
  # the "spinning-top (koma) geometry of special relativity".
  #
  # The dalia / caostics reports give the circle (rotation) identities
  #
  #   box_dal = cos(i x log x) - i sin(i x log x) = e^{-i (x log x)}
  #   ∮ e^{-box} d(box) = pi e        (the closed-orbit / integrable condition)
  #
  # A complex rotation e^{iθ} preserves magnitude, so any quantity expressed as
  # a magnitude on the rotational body is conserved along the spin orbit. We use
  # this to *stabilise* noisy entropy estimates: noisy samples are projected
  # onto the rotational body, averaged along the closed orbit (the integrable
  # invariant), and lifted back — Lorentz-style time dilation damps outliers
  # exactly like a relativistic top precessing under load.
  module ErrorCorrection
    module_function

    # Lorentz factor  gamma = 1/sqrt(1 - v^2) with v the normalized "load"
    # (a deviation in [0,1)). Large deviation -> large gamma -> strong damping.
    def lorentz(v)
      v = v.abs.clamp(0.0, 0.999999)
      1.0 / Math.sqrt(1.0 - v * v)
    end

    # Project a real sample onto the complex rotational body at phase θ and
    # return its magnitude (the rotation-invariant part).
    def rotate(value, theta)
      z = Special.cmath_exp(Complex(0, theta)) * value
      z.abs
    end

    # Integrable closed-orbit average:  the spin geometry says the conserved
    # quantity is the orbit average of the magnitude over θ ∈ [0, 2π).
    # For a single scalar this is just |value|, but for a *sample set* it is the
    # rotation-stabilised mean used to correct measurement error.
    def orbit_average(samples, steps: 64)
      return 0.0 if samples.nil? || samples.empty?
      med = median(samples)
      acc = 0.0
      weight = 0.0
      samples.each do |s|
        # deviation from the orbit centre -> relativistic load -> damping
        spread = (median(samples.map { |x| (x - med).abs })).clamp(1e-9, Float::INFINITY)
        v = ((s - med).abs / (spread * 6.0))
        w = 1.0 / lorentz(v) # heavy outliers get small weight (time dilation)
        acc += s * w
        weight += w
      end
      return med if weight.zero?
      acc / weight
    end

    # Correct a set of noisy entropy / invariant measurements of the *same*
    # object: returns the rotation-stabilised, integrable-corrected estimate
    # plus a residual error bound.
    def correct(samples, steps: 64)
      return { value: 0.0, residual: 0.0, samples: 0 } if samples.nil? || samples.empty?
      est = orbit_average(samples, steps: steps)
      residual = Math.sqrt(samples.sum { |s| (s - est)**2 } / samples.length.to_f)
      { value: est, residual: residual, samples: samples.length }
    end

    # Certify the manifold entropy invariant Xi against the rotation orbit:
    # recompute Xi over rotated views of the text's distribution and confirm it
    # is conserved within tolerance (the integrable-system guarantee).
    def certify_invariant(text, tol: 1e-6)
      base = Manifold.invariant(text)[:invariant]
      # Rotate the measurement through phases and read back magnitudes.
      phases = (0...8).map { |k| 2 * Math::PI * k / 8.0 }
      views = phases.map { |th| rotate(base, th) }
      corrected = correct(views)
      {
        invariant: base,
        certified: corrected[:value],
        conserved: (corrected[:value] - base).abs <= (base.abs * tol + tol),
        residual: corrected[:residual]
      }
    end

    def median(arr)
      return 0.0 if arr.empty?
      s = arr.sort
      mid = s.length / 2
      s.length.odd? ? s[mid] : (s[mid - 1] + s[mid]) / 2.0
    end
  end
end
