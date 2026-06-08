# frozen_string_literal: true

module Bada
  module NN
    # Optimizer — Strategy: the training loop calls #step(params) without
    # knowing which update rule is in use.
    class Optimizer
      def step(_params)
        raise NotImplementedError
      end
    end

    # SGD with optional momentum.
    class SGD < Optimizer
      def initialize(lr: 0.1, momentum: 0.0, clip: 5.0)
        @lr = lr
        @momentum = momentum
        @clip = clip
        @velocity = {}
      end

      def step(params)
        params.each do |p|
          v = (@velocity[p.object_id] ||= zeros_like(p.grad))
          update(p.data, p.grad, v)
        end
      end

      private

      def update(data, grad, vel)
        if data[0].is_a?(Array)
          data.each_index do |i|
            di = data[i]; gi = grad[i]; vi = vel[i]
            di.each_index do |j|
              g = clip(gi[j])
              vi[j] = @momentum * vi[j] - @lr * g
              di[j] += vi[j]
            end
          end
        else
          data.each_index do |i|
            g = clip(grad[i])
            vel[i] = @momentum * vel[i] - @lr * g
            data[i] += vel[i]
          end
        end
      end

      def clip(g)
        return @clip if g > @clip
        return -@clip if g < -@clip
        g
      end

      def zeros_like(m)
        if m[0].is_a?(Array)
          m.map { |row| Array.new(row.length, 0.0) }
        else
          Array.new(m.length, 0.0)
        end
      end
    end

    # Adam — adaptive moment estimation (alternative Strategy).
    class Adam < Optimizer
      def initialize(lr: 0.01, b1: 0.9, b2: 0.999, eps: 1e-8)
        @lr = lr; @b1 = b1; @b2 = b2; @eps = eps
        @m = {}; @v = {}; @t = 0
      end

      def step(params)
        @t += 1
        params.each do |p|
          m = (@m[p.object_id] ||= zeros_like(p.grad))
          v = (@v[p.object_id] ||= zeros_like(p.grad))
          update(p.data, p.grad, m, v)
        end
      end

      private

      def update(data, grad, m, v)
        bc1 = 1 - @b1**@t
        bc2 = 1 - @b2**@t
        if data[0].is_a?(Array)
          data.each_index do |i|
            data[i].each_index { |j| data[i][j] += step_one(grad[i][j], m[i], v[i], j, bc1, bc2) }
          end
        else
          data.each_index { |i| data[i] += step_one(grad[i], m, v, i, bc1, bc2) }
        end
      end

      def step_one(g, m, v, idx, bc1, bc2)
        m[idx] = @b1 * m[idx] + (1 - @b1) * g
        v[idx] = @b2 * v[idx] + (1 - @b2) * g * g
        mh = m[idx] / bc1
        vh = v[idx] / bc2
        -@lr * mh / (Math.sqrt(vh) + @eps)
      end

      def zeros_like(m)
        if m[0].is_a?(Array)
          m.map { |row| Array.new(row.length, 0.0) }
        else
          Array.new(m.length, 0.0)
        end
      end
    end
  end
end
