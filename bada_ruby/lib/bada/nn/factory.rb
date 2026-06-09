# frozen_string_literal: true

require_relative "layers"
require_relative "sequential"

module Bada
  module NN
    # LayerFactory — Factory Method: build a layer from a symbol + spec, so the
    # Builder and Memento loader never name concrete classes directly.
    module LayerFactory
      module_function

      def build(kind, spec, rng)
        case kind
        when :embedding
          EmbeddingConcat.new(spec[:vocab], spec[:dim], spec[:context], rng)
        when :linear, :dense
          Linear.new(spec[:in], spec[:out], rng)
        when :tanh
          Tanh.new
        when :relu
          ReLU.new
        else
          raise ArgumentError, "unknown layer kind: #{kind}"
        end
      end
    end

    # LanguageModelBuilder — Builder: fluent assembly of a neural n-gram
    # language model (Bengio-style MLP LM). Tracks the running feature width so
    # dense layers can be specified by output size only.
    class LanguageModelBuilder
      def initialize(seed: 42)
        @rng = Random.new(seed)
        @layers = []
        @width = nil
        @meta = {}
      end

      def embedding(vocab:, dim:, context:)
        @meta.merge!(vocab: vocab, dim: dim, context: context)
        @layers << LayerFactory.build(:embedding, { vocab: vocab, dim: dim, context: context }, @rng)
        @width = dim * context
        self
      end

      def dense(out)
        raise "embedding must come first" if @width.nil?
        @layers << LayerFactory.build(:dense, { in: @width, out: out }, @rng)
        @width = out
        self
      end

      def activation(kind)
        @layers << LayerFactory.build(kind, {}, @rng)
        self
      end

      # Project to vocabulary logits.
      def project_to_vocab
        dense(@meta[:vocab])
      end

      def build
        @meta[:hidden] ||= nil
        Sequential.new(@layers, meta: @meta)
      end

      # Convenience preset: emb -> dense(hidden) -> tanh -> dense(vocab).
      def self.mlp_lm(vocab:, dim: 16, context: 2, hidden: 32, seed: 42)
        b = new(seed: seed)
        b.embedding(vocab: vocab, dim: dim, context: context)
        b.dense(hidden)
        b.activation(:tanh)
        b.project_to_vocab
        model = b.build
        model.meta[:hidden] = hidden
        model
      end
    end
  end
end
