# frozen_string_literal: true

require "json"
require_relative "factory"
require_relative "vocab"
require_relative "trainer"
require_relative "optimizer"
require_relative "observer"
require_relative "generator"
require_relative "sampler"
require_relative "pipeline"
require_relative "../knowledge"
require_relative "../qa_engine"

module Bada
  module NN
    # NeuralOmegaChat — Facade over the whole neural stack: build vocab + model
    # (Builder/Factory), train (Template Method + Observer + Strategy), and
    # answer through the Chain-of-Responsibility pipeline whose generation step
    # uses the unknown-engine Decorator. Model state is portable via the Memento.
    class NeuralOmegaChat
      attr_reader :model, :vocab, :knowledge, :adapter

      def initialize(dim: 16, context: 2, hidden: 32, max_vocab: 300, seed: 42)
        @dim = dim
        @context = context
        @hidden = hidden
        @max_vocab = max_vocab
        @seed = seed
        @knowledge = Bada::Knowledge.new
      end

      # Ingest reference material.
      def learn(text, source: "input")
        @knowledge.ingest(text, source: source)
        self
      end

      def learn_file(path, source: nil)
        @knowledge.ingest_file(path, source: source)
        self
      end

      # Build the vocab + model from the learned corpus and train the network.
      # optimizer: :adam (default, stable) or :sgd. Adam normalises per-parameter
      # so the per-sample updates converge cleanly on small noisy corpora.
      def train!(epochs: 8, lr: 0.01, optimizer: :adam, momentum: 0.9, log: true, max_samples: nil)
        @adapter = CorpusAdapter.new(@knowledge, context: @context, max_vocab: @max_vocab)
        @vocab = @adapter.vocab
        @model = LanguageModelBuilder.mlp_lm(
          vocab: @vocab.size, dim: @dim, context: @context, hidden: @hidden, seed: @seed
        )
        samples = @adapter.sample_array
        samples = samples.first(max_samples) if max_samples
        opt = optimizer == :sgd ? SGD.new(lr: lr, momentum: momentum) : Adam.new(lr: lr)
        trainer = Trainer.new(@model, optimizer: opt, seed: @seed)
        @logger = LossLogger.new(io: $stdout)
        @ckpt = Checkpointer.new
        trainer.subscribe(@logger) if log
        trainer.subscribe(@ckpt)
        trainer.train(samples, epochs: epochs)
        self
      end

      def trained?
        !@model.nil?
      end

      # Answer a question through the full pipeline.
      def reply(question, length: 24)
        raise "call train! first" unless trained?
        ctx = { question: question, length: length }
        gen = NeuralGenerator.new(@model, @vocab, context: @context)
        qa = Bada::QAEngine.new(@knowledge)
        info = Bada::InfoEngine.new(knowledge: @knowledge, seed: @seed)

        chain = MeasureHandler.new
        chain.then(RetrieveHandler.new(qa))
             .then(NeuralGenerateHandler.new(gen, @vocab, seed: @seed))
             .then(InfoGenerateHandler.new(info))
             .then(ErrorCorrectHandler.new)
             .then(RecordHandler.new)
        chain.handle(ctx)
        ctx
      end

      # Human-readable answer string.
      def ask(question, length: 24)
        r = reply(question, length: length)
        out = []
        out << "── Neural OmegaChat (Bada/Ruby 未知エンジン) ──"
        out << format("質問 H_q=%.4f · Ξ_q=%.4f · 可積分修正後 Ξ=%.4f (保存=%s)",
                      r[:question_entropy], r[:question_invariant],
                      r[:certified_invariant], r[:invariant_conserved])
        out << ""
        if r[:retrieval].is_a?(String) && !r[:retrieval].empty?
          out << "【検索（エントロピー・不変量近傍）】"
          out << r[:retrieval]
          out << ""
        end
        out << format("【ニューラル言語生成 (H≈%.2f / 目標%.2f)】",
                      r[:generated][:entropy], r[:target_h])
        out << r[:generated][:text]
        if (info = r[:info])
          out << ""
          out << render_info(info)
        end
        out.join("\n")
      end

      # Render the Thurston / catastrophe / millennium information block.
      def render_info(info)
        p = info[:placement]
        c = info[:catastrophe]
        m = info[:millennium]
        lines = []
        lines << format("【サーストン・ペレルマン多様体】幾何=%s (曲率%.2f) · Perelman F=%.4f · Ricci%s",
                        p[:geometry], p[:curvature], p[:perelman_f],
                        p[:ricci_collapsed] ? "=有限時間特異点" : format("→%.3f", p[:ricci_final]))
        lines << format("【カタストロフィ分岐（情報分解の分岐点）】判別式=%.4f%s · 分岐数=%d",
                        c[:discriminant], c[:on_bifurcation] ? " (分岐点上!)" : "", c[:branch_count])
        info[:branches].each do |b|
          lines << format("  分岐#%d (x=%.2f,目標H=%.2f): %s", b[:index], b[:equilibrium_x], b[:target_entropy], b[:text])
        end
        lines << "【ミレニアム7問への理論分解】起点: #{m[:origin]} / 主分解先: #{m[:dominant]}"
        m[:decomposition].first(3).each { |d| lines << "  - #{d[:theory]}" }
        lines.join("\n")
      end

      def repl(input: $stdin, output: $stdout)
        output.puts "Neural OmegaChat — Bada/Ruby 未知エンジン。空行で終了。"
        loop do
          output.print "\nあなた> "
          line = input.gets
          break if line.nil?
          q = line.dup.force_encoding("UTF-8").strip
          break if q.empty?
          output.puts
          output.puts ask(q)
        end
        output.puts "\nΩ::DATABASE に #{Akashic.instance.size} 件記録。さようなら。"
      end

      # --- Memento persistence ------------------------------------------
      def save(path)
        File.write(path, JSON.pretty_generate(
                           "vocab" => @vocab.to_h,
                           "config" => { "dim" => @dim, "context" => @context, "hidden" => @hidden },
                           "model" => @model.to_memento
                         ))
        path
      end

      def self.load(path, knowledge: nil)
        data = JSON.parse(File.read(path))
        cfg = data["config"]
        chat = new(dim: cfg["dim"], context: cfg["context"], hidden: cfg["hidden"])
        chat.instance_variable_set(:@knowledge, knowledge || Bada::Knowledge.new)
        vocab = Vocab.from_h(data["vocab"])
        model = LanguageModelBuilder.mlp_lm(
          vocab: vocab.size, dim: cfg["dim"], context: cfg["context"], hidden: cfg["hidden"]
        )
        model.load_memento(data["model"])
        chat.instance_variable_set(:@vocab, vocab)
        chat.instance_variable_set(:@model, model)
        chat
      end
    end
  end
end
