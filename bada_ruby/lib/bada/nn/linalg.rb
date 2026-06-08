# frozen_string_literal: true

module Bada
  module NN
    # Tiny pure-Ruby linear algebra used by every layer. Vectors are Array of
    # Float; matrices are Array of (Array of Float), shape [out][in].
    module Linalg
      module_function

      # y = W x   (W: out x in, x: in)  ->  out
      def matvec(w, x)
        w.map do |row|
          s = 0.0
          i = 0
          n = row.length
          while i < n
            s += row[i] * x[i]
            i += 1
          end
          s
        end
      end

      # g_in = W^T g   (W: out x in, g: out)  ->  in
      def matvec_t(w, g)
        inn = w[0].length
        out = Array.new(inn, 0.0)
        o = 0
        rows = w.length
        while o < rows
          row = w[o]
          go = g[o]
          j = 0
          while j < inn
            out[j] += row[j] * go
            j += 1
          end
          o += 1
        end
        out
      end

      # outer product a (m) x b (n) -> m x n
      def outer(a, b)
        a.map { |ai| b.map { |bj| ai * bj } }
      end

      def add!(a, b)
        a.each_index { |i| a[i] += b[i] }
        a
      end

      def axpy!(a, scale, b) # a += scale * b
        a.each_index { |i| a[i] += scale * b[i] }
        a
      end

      def zeros(n)
        Array.new(n, 0.0)
      end

      def zeros_like(m)
        if m[0].is_a?(Array)
          m.map { |row| Array.new(row.length, 0.0) }
        else
          Array.new(m.length, 0.0)
        end
      end

      # Xavier/Glorot uniform init for a [rows x cols] matrix.
      def randn_matrix(rows, cols, rng)
        limit = Math.sqrt(6.0 / (rows + cols))
        Array.new(rows) { Array.new(cols) { (rng.rand * 2 - 1) * limit } }
      end

      def softmax(logits)
        m = logits.max
        exps = logits.map { |v| Math.exp(v - m) }
        sum = exps.sum
        exps.map { |e| e / sum }
      end
    end
  end
end
