# frozen_string_literal: true

require_relative "linalg"
require_relative "../entropy"
require_relative "../manifold"
require_relative "../error_correction"

module Bada
  module NN
    # Sampler — Strategy: given the model's output logits (and optional context)
    # decide the next token id. Decoders are interchangeable at runtime.
    class Sampler
      def initialize(seed: nil)
        @rng = seed ? Random.new(seed) : Random.new
      end

      def pick(_logits, _ctx = {})
        raise NotImplementedError
      end

      # Shannon entropy (bits) of a probability vector.
      def self.dist_entropy(probs)
        h = 0.0
        probs.each { |p| h -= p * Math.log2(p) if p > 1e-12 }
        h
      end

      protected

      def sample_from(probs)
        r = @rng.rand
        acc = 0.0
        probs.each_index do |i|
          acc += probs[i]
          return i if r <= acc
        end
        probs.length - 1
      end
    end

    # Greedy: always the most likely token.
    class GreedySampler < Sampler
      def pick(logits, _ctx = {})
        logits.each_with_index.max_by { |(v, _)| v }[1]
      end
    end

    # Temperature sampling.
    class TemperatureSampler < Sampler
      def initialize(temp: 1.0, seed: nil)
        super(seed: seed)
        @temp = temp
      end

      def pick(logits, _ctx = {})
        sample_from(Linalg.softmax(logits.map { |v| v / @temp }))
      end
    end

    # Top-k sampling at a temperature.
    class TopKSampler < Sampler
      def initialize(k: 8, temp: 1.0, seed: nil)
        super(seed: seed)
        @k = k
        @temp = temp
      end

      def pick(logits, _ctx = {})
        scaled = logits.map { |v| v / @temp }
        idx = (0...scaled.length).sort_by { |i| -scaled[i] }.first(@k)
        sub = idx.map { |i| scaled[i] }
        probs = Linalg.softmax(sub)
        idx[sample_from(probs)]
      end
    end

    # EntropyTargetSampler: choose the temperature so the output distribution's
    # Shannon entropy matches a target H (binary search — entropy is monotone in
    # temperature), then sample. This is the bridge to the report's Shannon /
    # manifold machinery.
    class EntropyTargetSampler < Sampler
      def initialize(target_h: 3.0, seed: nil)
        super(seed: seed)
        @target = target_h
      end

      def pick(logits, ctx = {})
        target = ctx[:target_h] || @target
        temp = temperature_for(logits, target)
        sample_from(Linalg.softmax(logits.map { |v| v / temp }))
      end

      def temperature_for(logits, target_h)
        lo = 1e-2
        hi = 50.0
        20.times do
          mid = Math.sqrt(lo * hi)
          h = Sampler.dist_entropy(Linalg.softmax(logits.map { |v| v / mid }))
          if h < target_h then lo = mid else hi = mid end
        end
        Math.sqrt(lo * hi)
      end
    end

    # UnknownEngineSampler — Decorator: wraps any base sampler and adds the
    # "unknown engine" behaviour. Before each pick it
    #   1. measures the global partial integral manifold entropy invariant Ξ of
    #      the text generated so far,
    #   2. error-corrects the target entropy on the complex-rotation /
    #      special-relativity integrable system (so the trajectory is stable),
    #   3. nudges the logits along the manifold so tokens that move Ξ toward the
    #      question's Ξ_target are favoured,
    # then delegates the actual choice to the wrapped sampler.
    class UnknownEngineSampler < Sampler
      def initialize(base, vocab:, xi_target: nil, gain: 0.6, seed: nil)
        super(seed: seed)
        @base = base
        @vocab = vocab
        @xi_target = xi_target
        @gain = gain
      end

      def pick(logits, ctx = {})
        generated = ctx[:generated] || []
        text = generated.join(" ")

        # 2. error-correct the target entropy on the rotational body.
        base_target = ctx[:target_h] || 3.0
        cur_h = Bada::Entropy.shannon(generated)
        corrected = Bada::ErrorCorrection.correct([base_target, cur_h, (base_target + cur_h) / 2.0])
        eff_target = corrected[:value]

        # 1 & 3. manifold-modulate logits toward the target invariant.
        modulated = modulate(logits, text)

        @base.pick(modulated, ctx.merge(target_h: eff_target))
      end

      private

      # Add a small bias that rewards each candidate token by how much it pulls
      # the running manifold invariant toward the target (a cheap one-step
      # lookahead on the highest-scoring candidates only).
      def modulate(logits, text)
        return logits if @xi_target.nil? || text.empty?
        out = logits.dup
        # only probe the top candidates to keep it O(k)
        top = (0...logits.length).sort_by { |i| -logits[i] }.first(12)
        top.each do |i|
          cand = "#{text} #{@vocab.token(i)}"
          xi = Bada::Manifold.xi(cand)
          # closer to target -> positive bias
          out[i] += @gain * (-(xi - @xi_target).abs)
        end
        out
      end
    end
  end
end
