# frozen_string_literal: true

require_relative "sampler"

module Bada
  module NN
    # NeuralGenerator: runs the trained Sequential model autoregressively,
    # delegating token choice to a Sampler (Strategy). The sampler receives the
    # generated-so-far context so decorators (the unknown engine) can steer.
    class NeuralGenerator
      def initialize(model, vocab, context:)
        @model = model
        @vocab = vocab
        @context = context
      end

      # prompt: String or Array<token>. Returns { tokens:, text:, entropy: }.
      def generate(prompt: nil, length: 24, sampler: GreedySampler.new, target_h: nil)
        ids = seed_ids(prompt)
        generated = []
        length.times do
          ctx = ids.last(@context)
          ctx = pad(ctx)
          logits = @model.forward(ctx)
          next_id = sampler.pick(logits, generated: generated, target_h: target_h)
          tok = @vocab.token(next_id)
          generated << tok
          ids << next_id
        end
        text = generated.join(" ")
        { tokens: generated, text: text, entropy: Bada::Entropy.shannon(generated) }
      end

      private

      def seed_ids(prompt)
        toks =
          case prompt
          when nil then []
          when String then Bada::Entropy.tokenize(prompt)
          when Array then prompt
          end
        ([@vocab.bos_id] + @vocab.encode(toks))
      end

      def pad(ctx)
        return ctx if ctx.length == @context
        Array.new(@context - ctx.length, @vocab.bos_id) + ctx
      end
    end
  end
end
