# frozen_string_literal: true

require_relative "knowledge"
require_relative "qa_engine"
require_relative "generator"
require_relative "manifold"
require_relative "error_correction"
require_relative "tuplespace"

module Bada
  # OmegaChat — the ChatGPT branch (分派) built from Ruby on the Bada stack.
  #
  # Pipeline for every user turn:
  #
  #   1. Measure the question: Shannon entropy H_q and the global partial
  #      integral manifold entropy invariant Ξ_q.
  #   2. Error-correct H_q / Ξ_q on the complex rotational body (special
  #      relativity spinning-top integrable system).
  #   3. Retrieve from the corpus (report + web) by keyword AND by Ξ_q.
  #   4. Generate an answer at the question's own target entropy — text,
  #      equation, and theory — using the corrected target.
  #   5. Record the exchange into Omega::DATABASE (the Akashic TupleSpace).
  #
  # This is the "unknown engine": it obtains new information by mapping the
  # question's entropy onto the manifold invariant and generating in its
  # neighbourhood, rather than by retrieval alone.
  class OmegaChat
    attr_reader :knowledge, :db, :qa, :generator

    def initialize(knowledge: nil, seed: nil)
      @knowledge = knowledge || Knowledge.new
      @db = TupleSpace.new
      @qa = QAEngine.new(@knowledge)
      @generator = Generator.new(knowledge: @knowledge, seed: seed)
      @info = InfoEngine.new(knowledge: @knowledge, seed: seed)
    end

    # Ingest reference material (reports, web snippets) into the engine.
    def learn(text, source: "input")
      @knowledge.ingest(text, source: source)
      @qa = QAEngine.new(@knowledge)
      @generator = Generator.new(knowledge: @knowledge)
      @info = InfoEngine.new(knowledge: @knowledge)
      self
    end

    def learn_file(path, source: nil)
      @knowledge.ingest_file(path, source: source)
      @qa = QAEngine.new(@knowledge)
      @generator = Generator.new(knowledge: @knowledge)
      @info = InfoEngine.new(knowledge: @knowledge)
      self
    end

    # Full structured reply for a question.
    def reply(question, mode: :auto)
      stats = Manifold.invariant(question)
      hq = stats[:entropy]
      xiq = stats[:invariant]

      # Error-correct the question's measurements on the rotational body.
      cert = ErrorCorrection.certify_invariant(question)
      target_h = ErrorCorrection.correct([hq, hq * 1.02, hq * 0.98])[:value]

      retrieved = @knowledge.empty? ? [] : @qa.answer(question)
      gen_text   = @generator.text(target_h: target_h)
      gen_eq     = @generator.equation(target_h: target_h)
      gen_theory = @generator.theory(target_h: target_h)

      @db.push("Q: #{question}", key: "Ω::q##{@db.size}")
      @db.push("A: #{gen_theory[:theory]}", key: "Ω::a##{@db.size}")

      {
        question: question,
        question_entropy: hq,
        question_invariant: xiq,
        certified_invariant: cert[:certified],
        invariant_conserved: cert[:conserved],
        target_entropy: target_h,
        retrieval: retrieved,
        generated_text: gen_text,
        equation: gen_eq,
        theory: gen_theory
      }
    end

    # Information generation across Thurston-Perelman / catastrophe / millennium.
    def info(question, branch_length: 16)
      @info.render(question, branch_length: branch_length)
    end

    # Penrose graphical notation: draw picture-symbols, auto-compute, and get an
    # auto-answer + paper + source code. `drawing` is the ASCII diagram; `values`
    # maps tensor names to nested arrays.
    def penrose(drawing, values: {}, question: nil)
      studio = Penrose::Studio.new(knowledge: @knowledge)
      studio.draw(drawing, values: values)
      studio.report(question: question)
    end

    def penrose_palette
      Penrose::Palette.render
    end

    # Human-readable single-string answer (what the REPL prints).
    # info: append the Thurston/catastrophe/millennium information-generation block.
    def ask(question, info: true)
      r = reply(question)
      out = []
      out << "── OmegaChat (Bada/Ruby 分派) ──"
      out << format("質問エントロピー H_q = %.4f  ·  多様体不変量 Ξ_q = %.4f",
                    r[:question_entropy], r[:question_invariant])
      out << format("可積分エラー修正後 Ξ = %.4f  (保存=%s)  ·  目標エントロピー = %.4f",
                    r[:certified_invariant], r[:invariant_conserved], r[:target_entropy])
      out << ""
      if r[:retrieval].is_a?(String) && !r[:retrieval].empty?
        out << "【レポート/Web検索（エントロピー・不変量近傍）】"
        out << r[:retrieval]
        out << ""
      end
      out << "【理論生成】"
      out << r[:theory][:theory]
      out << ""
      out << "【方程式生成】"
      out << r[:equation][:equation]
      out << ""
      out << format("【言語生成 (H≈%.2f / 目標%.2f)】", r[:generated_text][:entropy], r[:target_entropy])
      out << r[:generated_text][:text]
      if info
        out << ""
        out << @info.render(question)
      end
      out.join("\n")
    end

    # Interactive REPL.
    def repl(input: $stdin, output: $stdout)
      output.puts "OmegaChat — Bada/Ruby 分派。空行で終了。"
      loop do
        output.print "\nあなた> "
        line = input.gets
        break if line.nil?
        q = line.dup.force_encoding("UTF-8").strip
        break if q.empty?
        output.puts
        output.puts ask(q)
      end
      output.puts "\nΩ::DATABASE に #{@db.size} 件のタプルを記録しました。さようなら。"
    end
  end
end
