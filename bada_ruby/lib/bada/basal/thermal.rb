# frozen_string_literal: true

require_relative "synapse"

module Bada
  module Basal
    # Gating strategies (Strategy pattern): how a salience vector becomes a choice.
    class ArgmaxGate
      def select(s, _t) = s.each_index.max_by { |i| s[i] }
      def distribution(s, _t)
        i = select(s, nil)
        d = Array.new(s.length, 0.0); d[i] = 1.0; d
      end
    end

    class BoltzmannGate
      def initialize(seed: nil) = (@rng = seed ? Random.new(seed) : Random.new)
      def distribution(s, t)
        t = [t, 1e-6].max
        m = s.max
        ex = s.map { |v| Math.exp((v - m) / t) }
        z = ex.sum
        ex.map { |e| e / z }
      end

      def select(s, t)
        p = distribution(s, t)
        r = @rng.rand; acc = 0.0
        p.each_index { |i| acc += p[i]; return i if r <= acc }
        p.length - 1
      end
    end

    # ThermalField: the simulated in-body thermal network. It (1) diffuses
    # "heat" (salience) laterally across channels via gamma-manifold
    # conductances, and (2) supplies a cooling temperature for the gate
    # (simulated annealing). Body temperature falls as deliberation proceeds.
    class ThermalField
      attr_reader :t0, :step

      def initialize(t0: 1.5, dt: 0.2, diffusion_gain: 0.5, gate: nil)
        @t0 = t0
        @dt = dt
        @gain = diffusion_gain
        @gate = gate || ArgmaxGate.new
        @step = 0
      end

      # One heat-diffusion sweep:  v_i += dt * Σ_j G_ij (v_j - v_i).
      def diffuse(v)
        n = v.length
        g = Conductance.matrix(n, gain: @gain)
        out = v.dup
        n.times do |i|
          flux = 0.0
          n.times { |j| flux += g[i][j] * (v[j] - v[i]) }
          out[i] = v[i] + @dt * flux
        end
        out
      end

      # Annealing temperature: T(step) = T0 / log(step + e), cools over time.
      def temperature
        @t0 / Math.log(@step + Math::E)
      end

      def gate(salience)
        @step += 1
        @gate.select(salience, temperature)
      end

      def distribution(salience)
        @gate.distribution(salience, temperature)
      end
    end
  end
end
