# frozen_string_literal: true

module Bada
  module Transformer
    # Minimal pure-Ruby tensor helpers (matrices as Array<Array<Float>>).
    # Everything the manifold-gauge transformer needs, no external deps.
    module Tensor
      module_function

      def zeros(rows, cols)
        Array.new(rows) { Array.new(cols, 0.0) }
      end

      # Deterministic weight matrix in [-scale, scale] from a seeded xorshift PRNG.
      def randmat(rows, cols, rng, scale: 0.5)
        Array.new(rows) { Array.new(cols) { (rng.next_float * 2.0 - 1.0) * scale } }
      end

      # A x B  (a: m x k, b: k x n) -> m x n
      def matmul(a, b)
        m = a.length
        k = b.length
        n = b[0].length
        out = Array.new(m) { Array.new(n, 0.0) }
        i = 0
        while i < m
          ai = a[i]
          oi = out[i]
          t = 0
          while t < k
            aval = ai[t]
            if aval != 0.0
              bt = b[t]
              j = 0
              while j < n
                oi[j] += aval * bt[j]
                j += 1
              end
            end
            t += 1
          end
          i += 1
        end
        out
      end

      def transpose(a)
        a[0].each_index.map { |j| a.map { |row| row[j] } }
      end

      # row-wise add of a bias vector
      def add_bias(a, bias)
        a.map { |row| row.each_index.map { |j| row[j] + bias[j] } }
      end

      def add(a, b)
        a.each_index.map { |i| a[i].each_index.map { |j| a[i][j] + b[i][j] } }
      end

      def scale(a, s)
        a.map { |row| row.map { |v| v * s } }
      end

      # numerically stable softmax over a row vector
      def softmax(vec)
        mx = vec.max
        exps = vec.map { |v| Math.exp(v - mx) }
        sum = exps.sum
        sum = 1e-12 if sum.zero?
        exps.map { |e| e / sum }
      end

      # layer normalization of a row vector
      def layernorm(vec, gamma: nil, beta: nil, eps: 1e-5)
        mean = vec.sum / vec.length
        var = vec.sum { |v| (v - mean)**2 } / vec.length
        inv = 1.0 / Math.sqrt(var + eps)
        vec.each_index.map do |i|
          y = (vec[i] - mean) * inv
          g = gamma ? gamma[i] : 1.0
          b = beta ? beta[i] : 0.0
          y * g + b
        end
      end

      def gelu(x)
        0.5 * x * (1.0 + Math.tanh(Math.sqrt(2.0 / Math::PI) * (x + 0.044715 * x**3)))
      end

      def gelu_mat(a)
        a.map { |row| row.map { |v| gelu(v) } }
      end

      def cosine(u, v)
        dot = 0.0
        nu = 0.0
        nv = 0.0
        u.each_index do |i|
          dot += u[i] * v[i]
          nu += u[i]**2
          nv += v[i]**2
        end
        d = Math.sqrt(nu) * Math.sqrt(nv)
        d.zero? ? 0.0 : dot / d
      end

      # A tiny, seedable xorshift64 PRNG (deterministic, no Kernel#rand global).
      class PRNG
        def initialize(seed)
          @s = (seed.to_i & 0xFFFFFFFFFFFFFFFF)
          @s = 0x9E3779B97F4A7C15 if @s.zero?
        end

        def next_u64
          x = @s
          x ^= (x << 13) & 0xFFFFFFFFFFFFFFFF
          x ^= (x >> 7)
          x ^= (x << 17) & 0xFFFFFFFFFFFFFFFF
          @s = x & 0xFFFFFFFFFFFFFFFF
          @s
        end

        # float in [0,1)
        def next_float
          (next_u64 >> 11) / (1 << 53).to_f
        end
      end
    end
  end
end
