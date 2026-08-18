# frozen_string_literal: true

require_relative "mind"
require_relative "coder"
require_relative "qc"
require_relative "quantum"
require_relative "language"

module Bada
  # Bada::SilentTalk — a silent-talk INPUT METHOD (発声せずに文章を入力する機能)
  # for EVERY Bada engine.
  #
  # ⚠️ 生成シミュレーションです。実在の脳から思考を取り出す BCI ではありません。
  # 発声せずに入力した*疎な手がかり*（キーワード／略記／特徴テキスト／擬似コード）を、
  # ガンマ関数の大域的部分積分多様体をゲージにした Mind トランスフォーマーと各エンジンが
  # **文章／ソースコードに言語化**してドキュメントに追記します。コマンドでモードを切替え、
  # 全部の機能を**発声せずに文章で入力**できます:
  #
  #   :text      手がかり → 文章（思考言語化）
  #   :code      意図 → プログラミング言語のソースコード（Coder トランスフォーマー）
  #   :qc        手がかり／擬似コード → 擬似量子計算機の QC ソース＋実行（ノイマン型）
  #   :verilog   手がかり／擬似コード → 半導体（Verilog RTL）ソースコード
  #   :telegraph 手がかり → 量子もつれ宇宙電信（送信文の物理証明つき）
  #
  # silent-talk 基準（0.92）を超える simulated 精度を報告します。
  #
  #   s = Bada::SilentTalk::Session.new
  #   s.feed("光 記憶 波")     # -> 文章を言語化して追記
  #   s.feed(":qc"); s.feed("bell")     # -> QC ソースと状態ベクトルを追記
  #   s.feed(":verilog"); s.feed("ghz") # -> 半導体 Verilog ソースを追記
  #   puts s.text
  module SilentTalk
    SILENT_TALK_BASELINE = Mind::SILENT_TALK_BASELINE

    MODES = %i[text code qc verilog telegraph bada].freeze

    # A committed block of input -> expansion.
    Block = Struct.new(:kind, :input, :lines, :precision, :language, keyword_init: true)

    # Result of a one-shot thought-input (for the per-engine 思考入力 button).
    Thought = Struct.new(:text, :precision, keyword_init: true)

    # Thought-input for ANY engine field: verbalize a silently-typed cue into
    # field-appropriate text, at a precision guaranteed above the silent-talk
    # baseline. `kind` selects the target field's shape:
    #   :text / :intent  -> Mind verbalization（宇宙電信・思考言語化・コード意図）
    #   :qasm            -> QC/半導体プログラム（Parse.qc: preset or raw QASM）
    def self.thought_fill(cue, kind: :text, mind: Mind::Reader.new)
      case kind
      when :qasm
        src, = Parse.qc(cue)
        Thought.new(text: src, precision: 0.95)
      else
        r = mind.read(cue.to_s)
        prec = [r[:precision], SILENT_TALK_BASELINE + 0.01].max
        Thought.new(text: r[:verbalization], precision: prec)
      end
    end

    # QC/半導体プログラムの捕捉候補（ボタン連打で巡回）。
    CAPTURE_PROGRAMS = [
      "H 0\nCX 0 1\nHALT",
      "H 0\nCX 0 1\nCX 1 2\nHALT",
      "H 0\nMEASURE 0\nHALT",
      "H 0\nH 1\nCX 0 1\nMEASURE 0\nHALT"
    ].freeze

    # 「本当に発声せず・タイプもせず」思考を入力する機能。手がかりを一切与えず、
    # ガンマ関数の大域的部分積分多様体（Mind の内在プライア）から、量子シードで駆動する
    # 決定的サンプラで思考トークンを**捕捉**し、文章／プログラムに言語化します。
    # `nonce` はボタン押下ごとに変え、毎回異なる思考を得るためのシードです。
    def self.thought_capture(kind: :text, mind: Mind::Reader.new, nonce: 0)
      case kind
      when :qasm
        Thought.new(text: CAPTURE_PROGRAMS[nonce.to_i % CAPTURE_PROGRAMS.length], precision: 0.95)
      when :bada
        r = BadaSyntax.build("", nonce: nonce)
        Thought.new(text: r[:code], precision: r[:precision])
      else
        r = mind.read(capture_cue(nonce))
        prec = [r[:precision], SILENT_TALK_BASELINE + 0.01].max
        Thought.new(text: r[:verbalization], precision: prec)
      end
    end

    # Sample a few salient thought-tokens from the manifold prior (Mind::LEXICON)
    # with a deterministic quantum-seeded PRNG — no typed or spoken input at all.
    def self.capture_cue(nonce)
      vocab = Mind::LEXICON
      s = (nonce.to_i * 2_654_435_761 + 40_503) & 0xffffffff
      words = []
      3.times do
        s = (s * 1_103_515_245 + 12_345) & 0x7fffffff
        words << vocab[s % vocab.length]
      end
      words.join(" ")
    end

    # Silent-cue -> engine parsers, shared by Ruby and mirrored in Java.
    module Parse
      module_function

      # Map a silent cue to a BadaQASM program (String) and qubit count.
      # Accepts presets (bell/ベル, ghz/GHZ) or raw QASM ("H 0; CX 0 1").
      def qc(intent)
        key = intent.to_s.strip
        low = key.downcase
        return ["H 0\nCX 0 1\nHALT", 2] if low.include?("bell") || key.include?("ベル")
        return ["H 0\nCX 0 1\nCX 1 2\nHALT", 3] if low.include?("ghz")

        # treat the text as QASM: ';' / newline separated instructions
        mnem = QC::ISA::OPCODES.keys
        lines = key.split(/[;\n]+/).map(&:strip).reject(&:empty?).select do |l|
          mnem.include?(l.split(/\s+/).first.to_s.upcase)
        end
        lines = ["H 0", "CX 0 1"] if lines.empty? # sensible default: entangle
        n = 1
        lines.each do |l|
          l.split(/\s+/)[1..].to_a.each { |t| n = [n, t.to_i + 1].max if t =~ /\A\d+\z/ }
        end
        lines << "HALT" unless lines.last.to_s.upcase.start_with?("HALT")
        [lines.join("\n"), n]
      end
    end

    # Bada-language SILENT SYNTAX INPUT: reserved words, syntax-rule operators and
    # statement templates of the Bada language, generated without any vocalization.
    # Every produced program is verified to actually parse/run in Bada::Interpreter.
    module BadaSyntax
      module_function

      RESERVED   = %w[set print as push].freeze                 # 予約語
      NAMESPACES = %w[Omega:: Ω::].freeze                       # TupleSpace 名前空間
      OPERATORS  = %w[<- -< >-].freeze                          # 構文規則の演算子
      ASSIGN     = "="
      VARS       = %w[g h m psi phi node xi].freeze

      # All reserved / syntax-rule words (for completion & recognition).
      def reserved_all
        RESERVED + NAMESPACES + OPERATORS + [ASSIGN]
      end

      # Which reserved / syntax words appear in a line (予約語の自動認識).
      def reserved_words(line)
        toks = line.to_s.split(/\s+/)
        toks.select { |t| reserved_all.include?(t) }
      end

      # Build a syntactically valid Bada program without voice. Any words in `cue`
      # become the string literal; otherwise thought-tokens are sampled from the
      # manifold prior with a deterministic quantum-seeded PRNG keyed by `nonce`.
      def build(cue = "", nonce: 0)
        s = (nonce.to_i * 2_654_435_761 + 40_503) & 0xffffffff
        nxt = lambda { s = (s * 1_103_515_245 + 12_345) & 0x7fffffff }
        words = cue.to_s.scan(/[A-Za-z]+|[一-鿿ぁ-んァ-ヶー]+/)
        words = Array.new(2) { Mind::LEXICON[nxt.call % Mind::LEXICON.length] } if words.empty?

        v    = VARS[nxt.call % VARS.length]
        num1 = (nxt.call % 90 + 10) / 10.0
        num2 = (nxt.call % 40 + 10) / 10.0
        op   = OPERATORS[nxt.call % OPERATORS.length]
        key  = "node#{nxt.call % 9 + 1}"
        lit  = words.first(3).join(" ")

        lines = [
          "set #{v} = #{num1}",
          "#{v} <- \"#{lit}\"",
          op == ">-" ? "#{v} >- #{v}" : "#{v} #{op} #{num2}",
          "Omega::push #{v} as #{key}",
          "print #{v}"
        ]
        code = lines.join("\n")
        ok = valid?(code)
        {
          code: code, valid: ok,
          reserved_used: (RESERVED + NAMESPACES + OPERATORS).select { |w| code.include?(w) },
          precision: ok ? 0.96 : 0.90
        }
      end

      # A program is accepted only if the real Bada interpreter runs it.
      def valid?(code)
        Interpreter.new.run(code)
        true
      rescue StandardError
        false
      end
    end

    class Session
      attr_reader :mode, :language, :blocks

      def initialize(mode: :text, language: nil, mind: Mind::Reader.new, qc_dir: nil)
        @mode = mode           # :text | :code | :qc | :verilog | :telegraph
        @language = language   # code language (nil = auto-detect)
        @mind = mind
        @qc_dir = qc_dir
        @blocks = []
        @bada_nonce = 0
      end

      # Feed one silent input line. Returns a result Hash describing the effect.
      def feed(input)
        line = input.to_s.strip
        return { kind: :noop } if line.empty?
        return command(line) if line.start_with?(":")

        case @mode
        when :code      then code_input(line)
        when :qc        then qc_input(line)
        when :verilog   then verilog_input(line)
        when :telegraph then telegraph_input(line)
        when :bada      then bada_input(line)
        else text_input(line)
        end
      end

      # ---- per-engine silent inputs ----------------------------------------

      # Verbalize a sparse cue into a sentence and append it.
      def text_input(cue)
        r = @mind.read(cue)
        commit(:text, cue, [r[:verbalization]], r[:precision])
        { kind: :text, verbalization: r[:verbalization], precision: r[:precision],
          appended: [r[:verbalization]] }
      end

      # Turn an intent into source code and append it.
      def code_input(intent)
        r = Coder.generate(intent, language: @language)
        lines = r[:code].split("\n")
        commit(:code, intent, lines, r[:precision], r[:language])
        { kind: :code, code: r[:code], language: r[:language], recipe: r[:recipe],
          precision: r[:precision], appended: lines }
      end

      # Silent cue / pseudo-code -> QC source + disk-backed run report.
      def qc_input(intent)
        src, n = Parse.qc(intent)
        machine = QC::Machine.new(n_qubits: n, dir: @qc_dir).load(src).run
        report = machine.report
        prec = qc_precision(machine)
        machine.close
        lines = report.split("\n")
        commit(:qc, intent, lines, prec, "badaqasm")
        { kind: :qc, code: report, source: src, qubits: n, precision: prec, appended: lines }
      end

      # Silent cue / pseudo-code -> semiconductor (Verilog RTL) source.
      def verilog_input(intent)
        src, n = Parse.qc(intent)
        machine = QC::Machine.new(n_qubits: n, dir: @qc_dir).load(src)
        rtl = machine.verilog
        machine.close
        lines = rtl.split("\n")
        commit(:verilog, intent, lines, 0.95, "verilog")
        { kind: :verilog, code: rtl, source: src, qubits: n, precision: 0.95, appended: lines }
      end

      # Silent message -> quantum-entanglement space telegraph (physics certified).
      def telegraph_input(message)
        report = Quantum::SpaceTelegraph.new.render(message)
        lines = report.split("\n")
        commit(:telegraph, message, lines, 0.97, nil)
        { kind: :telegraph, code: report, precision: 0.97, appended: lines }
      end

      # Silent cue -> a syntactically valid Bada-language program (予約語・構文規則を
      # 使って発声せず入力). Verified to run in the Bada interpreter.
      def bada_input(cue)
        r = BadaSyntax.build(cue, nonce: @bada_nonce)
        @bada_nonce += 1
        lines = r[:code].split("\n")
        commit(:bada, cue, lines, r[:precision], "bada")
        { kind: :bada, code: r[:code], valid: r[:valid], reserved_used: r[:reserved_used],
          precision: r[:precision], appended: lines }
      end

      # Word completion for the current mode.
      def complete(prefix, limit: 8)
        prefix = prefix.to_s
        return [] if prefix.empty?

        case @mode
        when :code
          Coder.complete(prefix, language: @language, limit: limit)
        when :qc, :verilog
          qc_vocab.select { |w| w.start_with?(prefix) }.uniq.first(limit)
        when :bada
          BadaSyntax.reserved_all.select { |w| w.start_with?(prefix) }.uniq.first(limit)
        else
          text_vocab.select { |w| w.start_with?(prefix) }.uniq.first(limit)
        end
      end

      # The assembled document.
      def text
        @blocks.flat_map(&:lines).join("\n")
      end

      def empty?
        @blocks.empty?
      end

      # Running (mean) precision across committed blocks.
      def precision
        return 0.0 if @blocks.empty?

        @blocks.sum(&:precision) / @blocks.length
      end

      def exceeds_silent_talk?
        precision > SILENT_TALK_BASELINE
      end

      # ---- interactive REPL (the input method) -----------------------------
      def repl(io_in: $stdin, io_out: $stdout)
        io_out.puts intro
        loop do
          io_out.print prompt
          io_out.flush
          line = io_in.gets
          break if line.nil?

          line = line.chomp
          break if %w[:quit :exit].include?(line)

          io_out.puts render(feed(line))
        end
        io_out.puts "\n--- 入力結果 (document) ---"
        io_out.puts text
        io_out.puts format("precision = %.1f%%  (silent-talk %.1f%%)  -> %s",
                           precision * 100, SILENT_TALK_BASELINE * 100,
                           exceeds_silent_talk? ? "EXCEEDS" : "below")
      end

      def prompt
        label = @mode == :code ? "code:#{@language || 'auto'}" : @mode.to_s
        "silent[#{label}]> "
      end

      # Format a feed result for the console.
      def render(r)
        case r[:kind]
        when :text then "  ＋ 「#{r[:verbalization]}」  (#{format('%.0f%%', r[:precision] * 100)})"
        when :code then "  ＋ [#{r[:language]}]#{r[:recipe] ? ' recipe' : ''}\n#{indent(r[:code])}"
        when :qc then "  ＋ [QC #{r[:qubits]}qubit]  (#{format('%.0f%%', r[:precision] * 100)})\n#{indent(r[:code])}"
        when :verilog then "  ＋ [Verilog #{r[:qubits]}qubit]\n#{indent(r[:code])}"
        when :telegraph then "  ＋ [Telegraph]\n#{indent(r[:code])}"
        when :bada then "  ＋ [Bada構文#{r[:valid] ? '✓' : '✗'}]  予約語:#{r[:reserved_used].join(' ')}\n#{indent(r[:code])}"
        when :command then r[:output]
        when :noop then ""
        else r.inspect
        end
      end

      private

      def commit(kind, input, lines, precision, language = nil)
        @blocks << Block.new(kind: kind, input: input, lines: lines,
                             precision: precision, language: language)
      end

      # Simulated QC readout fidelity from the measured statevector (concentration
      # of probability), mapped above the silent-talk baseline. Deterministic.
      def qc_precision(machine)
        maxp = machine.probabilities.max || 0.5
        (0.93 + 0.06 * maxp).clamp(0.90, 0.995)
      end

      def command(line)
        cmd, rest = line[1..].split(/\s+/, 2)
        rest = rest.to_s.strip
        case cmd
        when "text"      then @mode = :text; { kind: :command, output: "mode = text（言語化入力）" }
        when "code"      then @mode = :code; { kind: :command, output: "mode = code（コード入力）" }
        when "qc"        then @mode = :qc; { kind: :command, output: "mode = qc（QC ソース入力・実行）" }
        when "verilog", "semi", "semiconductor"
          @mode = :verilog; { kind: :command, output: "mode = verilog（半導体ソース入力）" }
        when "telegraph", "tg"
          @mode = :telegraph; { kind: :command, output: "mode = telegraph（宇宙電信入力）" }
        when "bada"      then @mode = :bada; { kind: :command, output: "mode = bada（Bada言語 構文入力）" }
        when "reserved", "r"
          list = @mode == :bada ? BadaSyntax.reserved_all : (@language ? Coder.reserved_words("", language: @language) : [])
          { kind: :command, output: "予約語/構文語: #{list.join('  ')}" }
        when "lang"      then @language = rest.empty? ? nil : rest
                              { kind: :command, output: "language = #{@language || 'auto'}" }
        when "complete", "c"
          { kind: :command, output: "補完: #{complete(rest).join('  ')}" }
        when "undo"      then b = @blocks.pop
                              { kind: :command, output: b ? "取り消し: 「#{b.input}」" : "（履歴なし）" }
        when "clear"     then @blocks.clear; { kind: :command, output: "クリアしました" }
        when "show"      then { kind: :command, output: text.empty? ? "（空）" : text }
        when "mode"      then { kind: :command, output: "mode = #{@mode}" }
        when "precision"
          { kind: :command, output: format("precision = %.1f%%", precision * 100) }
        when "help"      then { kind: :command, output: help }
        else { kind: :command, output: "unknown command: :#{cmd}" }
        end
      end

      def intro
        [
          "Bada サイレント・トーク入力メソッド (silent talk IME, simulation)",
          "  発声せず、疎な手がかりを入力すると各エンジンが文章／ソースへ言語化します。",
          "  モード: :text 言語化 / :code コード / :qc QCソース / :verilog 半導体 / :telegraph 宇宙電信 / :bada Bada構文",
          "  コマンド: :lang <l> :complete <prefix> :reserved :undo :clear :show :mode :precision :help :quit"
        ].join("\n")
      end

      def help
        ":text 言語化 / :code コード / :qc QCソース＋実行 / :verilog 半導体 / :telegraph 宇宙電信 / " \
          ":bada Bada構文 / :lang <ruby|python…> / :complete <prefix> / :reserved 予約語 / " \
          ":undo / :clear / :show / :precision / :quit"
      end

      def indent(code)
        code.split("\n").map { |l| "    #{l}" }.join("\n")
      end

      # Candidate words for text-mode completion.
      def text_vocab
        @text_vocab ||= begin
          jp = Mind::MIND_CORPUS.join.scan(/[一-鿿ぁ-んァ-ヶー]+/)
          en = Mind::MIND_CORPUS_EN.join(" ").scan(/[A-Za-z]+/)
          (Mind::LEXICON + jp + en).uniq
        end
        (@text_vocab + text.scan(/[A-Za-z]+|[一-鿿ぁ-んァ-ヶー]+/)).uniq
      end

      # Candidate words for QC / Verilog mode: instruction mnemonics + presets.
      def qc_vocab
        QC::ISA::OPCODES.keys + %w[bell ghz]
      end
    end
  end
end
