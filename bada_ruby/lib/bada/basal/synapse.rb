# frozen_string_literal: true

require_relative "../manifold"

module Bada
  module Basal
    # A synapse between two nuclei: a weight and a sign (+1 excitatory,
    # -1 inhibitory). Flyweight-ish value object shared across channels.
    Synapse = Struct.new(:weight, :sign) do
      def transmit(x) = x * weight * sign
    end

    # Thermal conductance between channels, derived from the gamma-function
    # global partial integral manifold line element 1/(x log x)^2: nearby
    # channels (small rank distance) conduct more "heat" (lateral interaction).
    module Conductance
      module_function

      def between(i, j, gain: 1.0)
        return 0.0 if i == j
        x = (i - j).abs + 2.0 # rank distance on the manifold (log x > 0)
        gain * Bada::Manifold.element(x)
      end

      # Symmetric conductance matrix for n channels.
      def matrix(n, gain: 1.0)
        Array.new(n) { |i| Array.new(n) { |j| between(i, j, gain: gain) } }
      end
    end
  end
end
