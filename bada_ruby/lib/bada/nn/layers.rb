# frozen_string_literal: true

require_relative "linalg"
require_relative "param"

module Bada
  module NN
    # Layer — the uniform component interface of the network (Composite leaf).
    # Every layer implements forward/backward and exposes its trainable params.
    class Layer
      def forward(_input)
        raise NotImplementedError
      end

      # Given dL/d(output), return dL/d(input) and accumulate param grads.
      def backward(_grad_output)
        raise NotImplementedError
      end

      def params
        []
      end

      def kind
        self.class.name.split("::").last
      end
    end

    # EmbeddingConcat — maps an array of `context` token ids to the
    # concatenation of their embedding rows. First layer of the LM.
    class EmbeddingConcat < Layer
      attr_reader :embedding

      def initialize(vocab_size, dim, context, rng)
        @vocab = vocab_size
        @dim = dim
        @context = context
        @embedding = Param.new(Linalg.randn_matrix(vocab_size, dim, rng))
      end

      def forward(ids)
        @ids = ids
        out = Array.new(@context * @dim)
        ids.each_with_index do |id, c|
          row = @embedding.data[id]
          base = c * @dim
          @dim.times { |d| out[base + d] = row[d] }
        end
        out
      end

      # grad_output length context*dim -> scatter into embedding rows.
      def backward(grad_output)
        @ids.each_with_index do |id, c|
          base = c * @dim
          g = @embedding.grad[id]
          @dim.times { |d| g[d] += grad_output[base + d] }
        end
        nil # discrete input: no gradient flows further back
      end

      def params
        [@embedding]
      end
    end

    # Linear (Dense): y = W x + b.
    class Linear < Layer
      def initialize(in_dim, out_dim, rng)
        @w = Param.new(Linalg.randn_matrix(out_dim, in_dim, rng))
        @b = Param.new(Linalg.zeros(out_dim))
      end

      def forward(x)
        @x = x
        Linalg.add!(Linalg.matvec(@w.data, x), @b.data)
      end

      def backward(grad_output)
        # dW += outer(grad_output, x); db += grad_output
        go = grad_output
        wg = @w.grad
        x = @x
        go.each_index do |o|
          goo = go[o]
          wgo = wg[o]
          x.each_index { |j| wgo[j] += goo * x[j] }
        end
        Linalg.add!(@b.grad, go)
        Linalg.matvec_t(@w.data, go) # dL/dx
      end

      def params
        [@w, @b]
      end
    end

    # Tanh activation (smooth, keeps the rotation-friendly bounded range).
    class Tanh < Layer
      def forward(x)
        @out = x.map { |v| Math.tanh(v) }
        @out
      end

      def backward(grad_output)
        @out.each_index.map { |i| grad_output[i] * (1.0 - @out[i] * @out[i]) }
      end
    end

    # ReLU activation (offered by the factory as an alternative).
    class ReLU < Layer
      def forward(x)
        @x = x
        x.map { |v| v.positive? ? v : 0.0 }
      end

      def backward(grad_output)
        @x.each_index.map { |i| @x[i].positive? ? grad_output[i] : 0.0 }
      end
    end
  end
end
