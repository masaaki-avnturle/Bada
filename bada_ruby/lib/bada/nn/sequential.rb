# frozen_string_literal: true

require_relative "layers"
require_relative "linalg"

module Bada
  module NN
    # Sequential — Composite that treats a stack of layers as one layer.
    # forward threads the input through; backward threads the gradient back.
    class Sequential < Layer
      attr_reader :layers, :meta

      def initialize(layers = [], meta: {})
        @layers = layers
        @meta = meta # vocab_size, dim, context, hidden, etc.
      end

      def add(layer)
        @layers << layer
        self
      end

      def forward(input)
        @layers.reduce(input) { |acc, layer| layer.forward(acc) }
      end

      def backward(grad)
        @layers.reverse_each do |layer|
          grad = layer.backward(grad)
          break if grad.nil?
        end
        grad
      end

      def params
        @layers.flat_map(&:params)
      end

      def zero_grad!
        params.each(&:zero_grad!)
      end

      # --- Memento -------------------------------------------------------
      # Capture the full trainable state as a plain Hash (JSON-serialisable),
      # and restore it without exposing layer internals to the caller.
      def to_memento
        { meta: @meta, weights: params.map(&:to_a) }
      end

      def load_memento(memento)
        ps = params
        memento["weights"].each_with_index do |w, i|
          ps[i].data = w
          ps[i].zero_grad!
        end
        self
      end
    end

    # CrossEntropySoftmax — fused softmax + negative-log-likelihood loss.
    # Returns the loss and caches probs so backward yields dL/dlogits cheaply.
    class CrossEntropySoftmax
      def forward(logits, target)
        @probs = Linalg.softmax(logits)
        @target = target
        p = @probs[target]
        -Math.log(p < 1e-12 ? 1e-12 : p)
      end

      # dL/dlogits = softmax - onehot(target)
      def backward
        g = @probs.dup
        g[@target] -= 1.0
        g
      end

      attr_reader :probs
    end
  end
end
