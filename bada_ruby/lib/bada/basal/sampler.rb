# frozen_string_literal: true

require_relative "../nn/sampler"
require_relative "factory"

module Bada
  module Basal
    # BasalGangliaSampler — a Bada::NN decoder Strategy that routes the LLM's
    # logits through the basal-ganglia thermal action-selection network: the
    # top-k tokens become cortical channels, the circuit gates one by selective
    # disinhibition. This makes the LLM choose tokens the way the brain chooses
    # actions (Go/NoGo + thermal annealing) instead of plain softmax.
    class BasalGangliaSampler < Bada::NN::Sampler
      def initialize(k: 8, t0: 0.8, seed: nil)
        super(seed: seed)
        @k = k
        @t0 = t0
        @seed = seed
        @circuit = nil # built once, sized to k, so the gate RNG advances
      end

      def pick(logits, _ctx = {})
        k = [@k, logits.length].min
        @circuit ||= CircuitFactory.build(k, t0: @t0, gate: :boltzmann, seed: @seed)
        # channels are rank-ordered: channel 0 is always the strongest logit.
        top = (0...logits.length).sort_by { |i| -logits[i] }.first(k)
        sal = top.map { |i| logits[i] }
        m = sal.min
        sal = sal.map { |v| v - m } # cortical drive is non-negative
        top[@circuit.select(sal)]
      end
    end
  end
end
