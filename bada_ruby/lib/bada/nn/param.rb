# frozen_string_literal: true

require_relative "linalg"

module Bada
  module NN
    # A trainable parameter: its data and a gradient accumulator of identical
    # shape. Supports 1-D (bias / embedding row stream) and 2-D (weight matrix)
    # tensors. Optimizers read .grad and update .data.
    class Param
      attr_accessor :data, :grad

      def initialize(data)
        @data = data
        @grad = Linalg.zeros_like(data)
      end

      def zero_grad!
        @grad = Linalg.zeros_like(@data)
      end

      def two_d?
        @data[0].is_a?(Array)
      end

      # Save / restore as plain nested arrays (used by the Memento).
      def to_a
        @data
      end

      def self.from_a(arr)
        new(arr)
      end
    end
  end
end
