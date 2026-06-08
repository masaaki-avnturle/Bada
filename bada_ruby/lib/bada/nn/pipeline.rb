# frozen_string_literal: true

require_relative "../manifold"
require_relative "../error_correction"
require_relative "../tuplespace"
require_relative "../info_engine"
require_relative "generator"
require_relative "sampler"

module Bada
  module NN
    # Akashic — Singleton: one process-wide Omega::DATABASE that every handler
    # writes the conversation into.
    class Akashic
      def self.instance
        @instance ||= Bada::TupleSpace.new
      end

      def self.reset!
        @instance = Bada::TupleSpace.new
      end
    end

    # Handler — Chain of Responsibility node. Each handler enriches the shared
    # context hash and forwards to its successor.
    class Handler
      attr_accessor :successor

      def then(handler)
        @successor = handler
        handler
      end

      def handle(ctx)
        process(ctx)
        @successor ? @successor.handle(ctx) : ctx
      end

      def process(_ctx); end
    end

    # 1. Measure the question: Shannon entropy + manifold invariant.
    class MeasureHandler < Handler
      def process(ctx)
        stats = Bada::Manifold.invariant(ctx[:question])
        ctx[:question_entropy] = stats[:entropy]
        ctx[:question_invariant] = stats[:invariant]
        ctx[:target_h] = stats[:entropy]
        ctx[:xi_target] = stats[:invariant]
      end
    end

    # 2. Retrieve grounding from the corpus (skipped if no QA engine).
    class RetrieveHandler < Handler
      def initialize(qa)
        @qa = qa
      end

      def process(ctx)
        ctx[:retrieval] = @qa ? @qa.answer(ctx[:question]) : nil
      end
    end

    # 3. Neural generation with the unknown-engine sampler.
    class NeuralGenerateHandler < Handler
      def initialize(generator, vocab, seed: nil)
        @generator = generator
        @vocab = vocab
        @seed = seed
      end

      def process(ctx)
        base = EntropyTargetSampler.new(target_h: ctx[:target_h], seed: @seed)
        engine = UnknownEngineSampler.new(base, vocab: @vocab,
                                                xi_target: ctx[:xi_target], seed: @seed)
        out = @generator.generate(prompt: ctx[:question], length: ctx[:length] || 24,
                                  sampler: engine, target_h: ctx[:target_h])
        ctx[:generated] = out
      end
    end

    # 3b. Information generation: place the question's entropy on the Thurston-
    # Perelman manifold, branch it through the catastrophe bifurcation set, and
    # decompose its theory across the seven Clay Millennium problems.
    class InfoGenerateHandler < Handler
      def initialize(info_engine)
        @info = info_engine
      end

      def process(ctx)
        ctx[:info] = @info.generate(ctx[:question], branch_length: 14)
      end
    end

    # 4. Certify the manifold invariant on the integrable rotational body.
    class ErrorCorrectHandler < Handler
      def process(ctx)
        cert = Bada::ErrorCorrection.certify_invariant(ctx[:question])
        ctx[:certified_invariant] = cert[:certified]
        ctx[:invariant_conserved] = cert[:conserved]
      end
    end

    # 5. Record the exchange into the Akashic TupleSpace (Singleton).
    class RecordHandler < Handler
      def process(ctx)
        db = Akashic.instance
        db.push("Q: #{ctx[:question]}", key: "Ω::q##{db.size}")
        db.push("A: #{ctx[:generated][:text]}", key: "Ω::a##{db.size}")
        ctx[:akashic_size] = db.size
      end
    end
  end
end
