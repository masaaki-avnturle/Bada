# frozen_string_literal: true

require_relative "circuit"
require_relative "thermal"
require_relative "dopamine"

module Bada
  module Basal
    # Factory + Builder for assembling a basal-ganglia circuit, so callers never
    # name the concrete thermal/dopamine/gate classes directly.
    module CircuitFactory
      module_function

      def build(channels, t0: 1.5, dt: 0.2, diffusion_gain: 0.5,
                gate: :argmax, seed: nil, da_baseline: 0.3, lr: 0.2)
        g = case gate
            when :boltzmann then BoltzmannGate.new(seed: seed)
            else ArgmaxGate.new
            end
        thermal = ThermalField.new(t0: t0, dt: dt, diffusion_gain: diffusion_gain, gate: g)
        dopamine = Dopamine.new(baseline: da_baseline, lr: lr)
        BasalGanglia.new(channels, thermal: thermal, dopamine: dopamine)
      end
    end
  end
end
