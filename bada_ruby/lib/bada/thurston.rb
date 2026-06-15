# frozen_string_literal: true

require_relative "special"
require_relative "entropy"
require_relative "manifold"

module Bada
  # Thurston–Perelman manifold (geometrization), and placing a question's
  # Shannon entropy onto it.
  #
  # The Bada1 report enumerates the eight model geometries
  #   S^3, H^1×E^1, E^1, S^1×E^1, S^2×E^1, H^1×S^1, H^1, S^2×E
  # and gives the Ricci flow  d/dt g_ij = -2 R_ij  together with Perelman's
  # second-variation / adjoint-heat operator.
  #
  # We implement:
  #   * the eight geometries with their curvature sign,
  #   * Perelman's F-entropy functional driven by the Shannon measure
  #         F(g,f) = ∫ (R + |∇f|²) e^{-f} dV ,   f = -log p  (so e^{-f}=p),
  #   * a scalar Ricci-flow step (geometrization smoothing),
  #   * place_entropy: map a question's entropy H onto one of the eight
  #     geometries and return its Perelman F value (Shannon "lifted" onto the
  #     Thurston–Perelman manifold).
  module Thurston
    module_function

    # The eight model geometries, in the report's order, with a curvature value.
    GEOMETRIES = [
      { name: "S^3",      curvature: 1.0,  kind: :spherical },
      { name: "H^1×E^1",  curvature: -0.5, kind: :mixed },
      { name: "E^1",      curvature: 0.0,  kind: :flat },
      { name: "S^1×E^1",  curvature: 0.3,  kind: :mixed },
      { name: "S^2×E^1",  curvature: 0.6,  kind: :mixed },
      { name: "H^1×S^1",  curvature: -0.3, kind: :mixed },
      { name: "H^1",      curvature: -1.0, kind: :hyperbolic },
      { name: "S^2×E",    curvature: 0.5,  kind: :mixed }
    ].freeze

    def geometries
      GEOMETRIES
    end

    # Perelman F-entropy functional, discretized over a token distribution.
    #   f_i = -ln p_i ,  e^{-f_i} = p_i ,
    #   |∇f|²_i ≈ (f_{i+1} - f_i)² along the rank coordinate,
    #   dV_i  = manifold line element 1/(x log x)² at rank x,
    #   F = Σ_i (R + |∇f|²_i) p_i dV_i .
    def perelman_f(dist, curvature)
      return 0.0 if dist.nil? || dist.empty?
      ps = dist.map { |(_, p)| p }
      fs = ps.map { |p| -Math.log(p) }
      f = 0.0
      ps.each_index do |i|
        gradf2 = i < ps.length - 1 ? (fs[i + 1] - fs[i])**2 : 0.0
        x = i + 2.0
        dv = Manifold.element(x)
        f += (curvature + gradf2) * ps[i] * dv
      end
      f
    end

    # Perelman W-entropy (a scale-aware refinement), τ = diffusion scale.
    def perelman_w(dist, curvature, tau: 1.0)
      return 0.0 if dist.nil? || dist.empty?
      ps = dist.map { |(_, p)| p }
      fs = ps.map { |p| -Math.log(p) }
      n = ps.length.to_f
      w = 0.0
      ps.each_index do |i|
        gradf2 = i < ps.length - 1 ? (fs[i + 1] - fs[i])**2 : 0.0
        w += (tau * (curvature + gradf2) + fs[i] - n) * ps[i]
      end
      w
    end

    # Scalar Ricci flow: a constant-curvature model where R(g) = k/g, so
    #   dg/dt = -2 R(g) = -2k/g  ->  g(t)² = g0² - 4 k t.
    # Spherical (k>0) collapses in finite time (the geometrization singularity);
    # hyperbolic (k<0) expands. Returns the trajectory of the metric scale.
    def ricci_flow(curvature, g0: 1.0, dt: 0.05, steps: 20)
      g = g0
      traj = [g]
      steps.times do
        r = g.abs < 1e-9 ? 0.0 : curvature / g
        g -= 2.0 * r * dt
        break if g <= 0.0 # finite-time singularity (round-point collapse)
        traj << g
      end
      { trajectory: traj, final: traj.last, collapsed: g <= 0.0 }
    end

    # Place a question's Shannon entropy onto the Thurston–Perelman manifold.
    # Returns the geometry it lands in plus the Perelman entropy carried there.
    def place_entropy(text)
      tokens = text.is_a?(String) ? Entropy.tokenize(text) : text
      h = Entropy.shannon(tokens)
      dist = Entropy.distribution(tokens)
      stats = Manifold.invariant(tokens)
      h_norm = Entropy.normalized(tokens) # in [0,1]
      idx = (h_norm * GEOMETRIES.length).floor.clamp(0, GEOMETRIES.length - 1)
      geo = GEOMETRIES[idx]
      f = perelman_f(dist, geo[:curvature])
      w = perelman_w(dist, geo[:curvature])
      flow = ricci_flow(geo[:curvature])
      {
        entropy: h,
        entropy_normalized: h_norm,
        invariant: stats[:invariant],
        geometry: geo[:name],
        curvature: geo[:curvature],
        kind: geo[:kind],
        perelman_f: f,        # Shannon entropy lifted onto the manifold
        perelman_w: w,
        ricci_final: flow[:final],
        ricci_collapsed: flow[:collapsed]
      }
    end
  end
end
