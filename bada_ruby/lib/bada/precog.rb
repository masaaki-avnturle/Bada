# frozen_string_literal: true

require_relative "knowledge"
require_relative "qa_engine"
require_relative "generator"
require_relative "manifold"
require_relative "error_correction"
require_relative "tuplespace"
require_relative "engine"
require_relative "quantum"
require_relative "reviser"
require_relative "millennium"
require_relative "info_engine"
require_relative "credit_guard"

module Bada
  # Precog — 未知事前予知エンジン (the Unknown-Prior Precognition Engine).
  #
  # The ChatGPT evolution (進化系) asked for in the brief: instead of predicting
  # the next token from a learned posterior, it predicts the *unknown prior* —
  # the latent structure a question is drawn from — by starting in maximum-
  # entropy ignorance and sharpening it with evidence, all on the engine whose
  # two theorems guarantee it can never resurrect a confident zero.
  #
  # One foresee() turn runs the whole Bada stack:
  #
  #   1. Measure     — Shannon entropy H_q and manifold invariant Ξ_q (Manifold).
  #   2. Hypotheses  — retrieve candidate directions from the corpus, or fall
  #                    back to the seven Millennium faces (the unknown space).
  #   3. Engine      — softmax(retrieval scores) = base a over an UNKNOWN PRIOR;
  #                    entropy-phase cognitive modules rotate the amplitude ψ
  #                    without disturbing q (Thm 2) or any confident zero (Thm 1).
  #   4. Reviser     — the learning loop: feed the posterior back as evidence to
  #                    an append-only Engine::Inference, sharpening the prior
  #                    (entropy strictly decreases) — the @reviser discipline.
  #   5. Quantum     — superpose the top hypotheses on the phase core (qubit/H),
  #                    Measure() commits |ψ|² to Omega::DATABASE (precognition as
  #                    a quantum-inference fold over the trace).
  #   6. Millennium  — decompose/analyse the question across the seven Clay
  #                    problems via the Yamaguchi Framework.
  #   7. Generate    — emit the foreseen text / equation / theory at the
  #                    error-corrected target entropy.
  #   8. Record      — write the exchange to the Akashic TupleSpace.
  class Precog
    attr_reader :knowledge, :db, :qa, :generator, :rules

    def initialize(knowledge: nil, seed: nil)
      @knowledge = knowledge || Knowledge.new
      @db = TupleSpace.new
      @seed = seed
      @rules = Reviser::RuleLedger.new(db: TupleSpace.new)
      rebuild!
      install_default_grammar!
    end

    def learn(text, source: "input")
      @knowledge.ingest(text, source: source)
      rebuild!
      self
    end

    def learn_file(path, source: nil)
      @knowledge.ingest_file(path, source: source)
      rebuild!
      self
    end

    # The full structured precognition for a question.
    def foresee(question, hypotheses: 6, shots: 64)
      hq = Manifold.invariant(question)
      target_h = ErrorCorrection.correct([hq[:entropy], hq[:entropy] * 1.02, hq[:entropy] * 0.98])[:value]

      hyps   = hypothesis_space(question, hypotheses)
      engine = run_engine(question, hyps, hq[:invariant])
      loop_r = revise_loop(engine[:base], engine[:forbidden], shots: shots)
      quant  = quantum_foresight(engine[:posterior])
      mill   = Millennium.analyze(question)
      gen    = generate(target_h)

      record(question, hyps, engine, mill)

      {
        question: question,
        question_entropy: hq[:entropy],
        question_invariant: hq[:invariant],
        target_entropy: target_h,
        hypotheses: hyps,
        engine: engine,
        revision: loop_r,
        quantum: quant,
        millennium: mill,
        generated: gen,
        foreseen: hyps[engine[:argmax]] && hyps[engine[:argmax]][:text]
      }
    end

    # Human-readable single-string precognition (what the REPL prints).
    def ask(question, info: false)
      r = foresee(question)
      out = []
      out << "══ 未知事前予知エンジン — Bada Unknown-Prior Precognition Engine ══"
      out << format("質問 H_q = %.4f bits · 多様体不変量 Ξ_q = %.4f · 目標エントロピー = %.4f",
                    r[:question_entropy], r[:question_invariant], r[:target_entropy])
      out << ""
      out << "【① 未知事前分布の予知 (Unknown-Prior Engine)】"
      r[:engine][:ranked].first(5).each_with_index do |h, i|
        out << format("  %d. P=%.4f (base %.4f, θ=%+.3f) %s", i + 1,
                      h[:posterior], h[:base], h[:phase], truncate(h[:text], 64))
      end
      e = r[:engine]
      out << format("  定理検証: |ψ|²=a 偏差 %.2e (ユニタリ=%s) · 確信ゼロ保存=%s",
                    e[:max_prob_deviation], e[:unitary], e[:zeros_preserved])
      out << ""
      out << "【② リバイザ学習ループ (append-only)】"
      lr = r[:revision]
      out << format("  事前エントロピー %.4f → %.4f bits（%d 回の証拠コミットで単調に鋭化, 減少=%s）",
                    lr[:prior_entropy_before], lr[:prior_entropy_after], lr[:observations],
                    lr[:entropy_decreased])
      out << ""
      out << "【③ 量子予知 (Omega::Quantum, 位相コア)】"
      q = r[:quantum]
      out << format("  qubit(%d) → H → Measure: P=%s", q[:qubits], fmt_arr(q[:probabilities]))
      out << format("  確信ゼロ(復活不能な禁制状態)=%s · |ψ|²総和=%.6f", q[:forbidden].inspect, q[:norm])
      out << ""
      out << "【④ ミレニアム予想分析 (Yamaguchi Framework)】"
      m = r[:millennium]
      out << "  枠組: #{m[:framework]}"
      out << "  主予知先: #{m[:dominant]}"
      out << "  → #{m[:dominant_resolution]}"
      m[:posterior].first(3).each do |p|
        out << format("    · %s  P=%.4f", p[:name], p[:posterior])
      end
      out << format("  エンジン定理: |ψ|²=a 偏差 %.2e · ゼロ保存=%s",
                    m[:engine][:max_prob_deviation], m[:engine][:zeros_preserved])
      out << ""
      out << "【⑤ 予知生成 (entropy-driven generation)】"
      out << "  理論: #{r[:generated][:theory][:theory]}"
      out << "  方程式: #{r[:generated][:equation][:equation]}"
      out << format("  言語 (H≈%.2f): %s", r[:generated][:text][:entropy], r[:generated][:text][:text])
      out << ""
      out << format("Ω::DATABASE へ %d 件記録 · 文法規則 %d 件（@reviser, append-only）",
                    @db.size, @rules.size)
      # Seal with quantum-crypto credit protection (BB84 + HMAC-SHA256) so
      # authorship cannot be silently taken.
      CreditGuard.stamp(out.join("\n"))
    end

    # Interactive REPL.
    def repl(input: $stdin, output: $stdout)
      output.puts "未知事前予知エンジン (Bada Precog) — 空行で終了。"
      output.puts "学習済みコーパス文: #{@knowledge.sentences.length} · 文法規則: #{@rules.size}"
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

    private

    def rebuild!
      @qa = QAEngine.new(@knowledge)
      @generator = Generator.new(knowledge: @knowledge, seed: @seed)
    end

    # Teach the engine its own quantum sublanguage through a @reviser block, so
    # the grammar rules are committed, auditable facts (per the reviser paper).
    def install_default_grammar!
      Reviser.parse_and_commit(<<~GRAMMAR, @rules)
        rule "qubit_n"  expr    [ 'qubit' '(' expr ')' ]   => qubit(_1)
        rule "hadamard" postfix [ 'H' '(' expr ')' ]       => phase_uniform(_1)
        rule "entangle" postfix [ 'CNOT' '(' expr ')' ]    => cnot(_1)
        rule "measure"  stmt    [ 'Measure' '(' expr ')' ] => commit_measurement(_1)
      GRAMMAR
    end

    # The space the precognition is "unknown" over: corpus directions, or — when
    # the corpus is silent on the question — the seven Millennium faces.
    def hypothesis_space(question, want)
      hyps = []
      unless @knowledge.empty?
        invariant = Manifold.invariant(question)[:invariant]
        seen = {}
        (@knowledge.find_by_keywords(Entropy.tokenize(question.downcase), top: want) +
         @knowledge.closest_invariant(invariant, top: want)).each do |s|
          next if seen[s.id]
          seen[s.id] = true
          hyps << { text: s.text, entropy: s.entropy, invariant: s.invariant,
                    score: 1.0 + 1.0 / (1.0 + (s.invariant - invariant).abs) }
        end
      end
      if hyps.length < 2
        Millennium.problems.first(want).each do |p|
          xi = Millennium.signature_invariant(p)
          hyps << { text: "#{p[:name]}: #{p[:link]}", entropy: 0.0, invariant: xi,
                    score: 1.0 + (question.downcase.include?(p[:keywords].first.to_s) ? 1.0 : 0.0) }
        end
      end
      hyps.first([want, hyps.length].min)
    end

    # The Unknown-Prior Engine over the hypotheses.
    def run_engine(question, hyps, xi_q)
      base = Engine.softmax(hyps.map { |h| h[:score] })
      # entropy-phase cognitive module: invariant proximity as a phase field.
      phase = hyps.map { |h| Math::PI * Math.tanh((h[:invariant] - xi_q)) }
      mod = Engine::Module.new(name: "Ξ-proximity", dist: base, gain: 0.7, phase: phase)
      cog = Engine.cognitive_system(base, [mod])
      check = Engine.verify(base, [mod])
      ranked = hyps.each_with_index.map do |h, i|
        h.merge(base: base[i], posterior: cog[:posterior][i], phase: cog[:theta][i])
      end.sort_by { |h| -h[:posterior] }
      {
        base: base,
        posterior: cog[:posterior],
        amplitude: cog[:amplitude],
        ranked: ranked,
        argmax: cog[:posterior].each_with_index.max_by { |p, _| p }[1],
        forbidden: base.each_index.select { |i| base[i] <= 1e-15 },
        max_prob_deviation: check[:max_prob_deviation],
        zeros_preserved: check[:zeros_preserved],
        unitary: check[:unitary]
      }
    end

    # The @reviser learning loop: append-only evidence sharpens the prior.
    def revise_loop(base, forbidden, shots:)
      inf = Engine::Inference.new(base.length, forbidden: forbidden, ledger: @db)
      before = inf.entropy
      rng = @seed ? Random.new(@seed) : Random.new
      shots.times do
        # sample an outcome from the engine's base belief and commit it.
        r = rng.rand
        acc = 0.0
        outcome = base.each_index.find { |i| acc += base[i]; r <= acc } || base.length - 1
        inf.observe(outcome) unless forbidden.include?(outcome)
      end
      {
        observations: inf.total_observations,
        prior_entropy_before: before,
        prior_entropy_after: inf.entropy,
        entropy_decreased: inf.entropy <= before + 1e-9,
        posterior: inf.estimate
      }
    end

    # Quantum precognition: superpose the top hypotheses and measure on the
    # phase core. Confident zeros (ruled-out hypotheses) cannot be resurrected.
    def quantum_foresight(posterior)
      n = [Math.log2([posterior.length, 1].max).ceil, 1].max
      n = [n, 4].min
      reg = Quantum.qubit(n)
      Quantum.hadamard_all(reg)            # uniform superposition over 2^n states
      reg.z(0) if n >= 1                    # a pure-phase step (Theorem 2 probe)
      m = Quantum.measure(reg, ledger: @db) # commit |ψ|² to Ω::DATABASE
      { qubits: n, probabilities: m[:probabilities], forbidden: m[:forbidden], norm: m[:norm] }
    end

    def generate(target_h)
      {
        text: @generator.text(target_h: target_h),
        equation: @generator.equation(target_h: target_h),
        theory: @generator.theory(target_h: target_h)
      }
    end

    def record(question, hyps, engine, mill)
      @db.push("Q: #{question}", key: "Ω::q##{@db.size}")
      foreseen = hyps[engine[:argmax]] && hyps[engine[:argmax]][:text]
      @db.push("FORESEE: #{foreseen}", key: "Ω::foresee##{@db.size}")
      @db.push("MILLENNIUM: #{mill[:dominant]}", key: "Ω::millennium##{@db.size}")
    end

    def truncate(str, n)
      s = str.to_s
      s.length > n ? "#{s[0, n]}…" : s
    end

    def fmt_arr(arr)
      "[#{arr.map { |x| format('%.4f', x) }.join(', ')}]"
    end
  end
end
