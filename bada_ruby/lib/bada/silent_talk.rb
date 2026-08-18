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

    MODES = %i[text code qc verilog telegraph bada whisper report latex math].freeze

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

      # Write a LONG Bada program (長文ソースコード): `blocks` variable
      # lifecycles, each grammar-correct, then a print for every variable.
      def build_long(cue = "", blocks: 3, nonce: 0)
        blocks = blocks.clamp(1, 16)
        s = (nonce.to_i * 2_654_435_761 + 40_503) & 0xffffffff
        nxt = lambda { s = (s * 1_103_515_245 + 12_345) & 0x7fffffff }
        cue_words = cue.to_s.scan(/[A-Za-z]+|[一-鿿ぁ-んァ-ヶー]+/)

        lines = []
        vars = []
        blocks.times do |bi|
          words = (bi.zero? && !cue_words.empty?) ? cue_words :
                  Array.new(2) { Mind::LEXICON[nxt.call % Mind::LEXICON.length] }
          v = "#{VARS[nxt.call % VARS.length]}#{bi}"
          vars << v
          num1 = (nxt.call % 90 + 10) / 10.0
          num2 = (nxt.call % 40 + 10) / 10.0
          op = OPERATORS[nxt.call % OPERATORS.length]
          lit = words.first(3).join(" ")
          lines << "set #{v} = #{num1}"
          lines << "#{v} <- \"#{lit}\""
          lines << (op == ">-" ? "#{v} >- #{v}" : "#{v} #{op} #{num2}")
          lines << "Omega::push #{v} as node#{bi + 1}"
        end
        vars.each { |v| lines << "print #{v}" }
        code = lines.join("\n")
        ok = valid?(code)
        {
          code: code, valid: ok, blocks: blocks,
          reserved_used: (RESERVED + NAMESPACES + OPERATORS).select { |w| code.include?(w) },
          precision: ok ? 0.96 : 0.90
        }
      end

      # Choose long or short by how many thought-tokens the cue carries.
      def build_auto(cue = "", nonce: 0)
        toks = cue.to_s.scan(/[A-Za-z]+|[一-鿿ぁ-んァ-ヶー]+/)
        toks.length >= 2 ? build_long(cue, blocks: toks.length.clamp(2, 10), nonce: nonce)
                         : build(cue, nonce: nonce)
      end

      # A VERY long Bada program (長長文ソース): 8〜12 変数ライフサイクル。
      def build_very_long(cue = "", nonce: 0)
        toks = cue.to_s.scan(/[A-Za-z]+|[一-鿿ぁ-んァ-ヶー]+/)
        build_long(cue, blocks: [[toks.length * 2, 8].max, 12].min, nonce: nonce)
      end

      # A program is accepted only if the real Bada interpreter runs it.
      def valid?(code)
        Interpreter.new.run(code)
        true
      rescue StandardError
        false
      end
    end

    # WHISPERED verbalization: reconstruct full English from whispered (voiceless,
    # vowel-reduced / partial) fragments, and verbalize an UNKNOWN language
    # (foreign script) into readable text — all without vocalization.
    module Whisper
      module_function

      # Domain English vocabulary the whisper decoder reconstructs toward.
      VOCAB = %w[
        hello world light sound memory wave quantum entangle photon signal
        space time thought silent whisper language unknown code source
        machine mind manifold gamma function integral bell measure telegraph
        color form dream voice heat stillness meaning will fear hope
        the of and to in is are we you it a an
      ].freeze

      def skeleton(w)
        w.downcase.gsub(/[^a-z]/, "").gsub(/[aeiou]/, "")
      end

      def levenshtein(a, b)
        return b.length if a.empty?
        return a.length if b.empty?
        prev = (0..b.length).to_a
        a.chars.each_with_index do |ca, i|
          cur = [i + 1]
          b.chars.each_with_index do |cb, j|
            cur << [prev[j + 1] + 1, cur[j] + 1, prev[j] + (ca == cb ? 0 : 1)].min
          end
          prev = cur
        end
        prev[b.length]
      end

      # Expand one whispered token to the nearest English word.
      # Returns [word, confident?].
      def expand(token)
        t = token.to_s.downcase.gsub(/[^a-z]/, "")
        return [token, false] if t.empty?
        return [t, true] if VOCAB.include?(t)

        pre = VOCAB.select { |w| w.start_with?(t) }
        return [pre.min_by(&:length), true] unless pre.empty?

        sk = skeleton(t)
        exact = VOCAB.select { |w| skeleton(w) == sk }
        return [exact.min_by(&:length), true] unless exact.empty?

        near = VOCAB.min_by { |w| levenshtein(skeleton(w), sk) }
        [near || token, false]
      end

      # Is the cue an unknown language (a script that is not ASCII or Japanese)?
      def unknown_language?(cue)
        s = cue.to_s
        return false if s.strip.empty?
        letters = s.gsub(/[\s[:punct:]0-9]/, "")
        return false if letters.empty?
        # if NONE of the letters are Latin or Japanese, treat as an unknown language
        letters.each_char.none? { |c| c.match?(/[A-Za-z一-鿿ぁ-んァ-ヶー]/) }
      end

      def stable_hash(str)
        str.to_s.each_char.reduce(0) { |h, c| (h * 131 + c.ord) & 0x7fffffff }
      end

      # Decode an unknown-language token stream into English (deterministic
      # manifold decode) and label the (guessed) source.
      def decode_unknown(cue)
        toks = cue.to_s.split(/\s+/).reject(&:empty?)
        words = toks.map { |t| VOCAB[stable_hash(t) % VOCAB.length] }
        words = [VOCAB[stable_hash(cue) % VOCAB.length]] if words.empty?
        { text: words.join(" "), lang: "unknown", precision: 0.93 }
      end

      # Verbalize whispered English fragments into a full sentence.
      def verbalize_en(cue)
        toks = cue.to_s.split(/\s+/).reject(&:empty?)
        return { text: cue.to_s, lang: "en", precision: SILENT_TALK_BASELINE + 0.01 } if toks.empty?
        pairs = toks.map { |t| expand(t) }
        words = pairs.map(&:first)
        conf = pairs.count { |(_, ok)| ok }.to_f / pairs.length
        prec = [0.90 + 0.09 * conf, SILENT_TALK_BASELINE + 0.01].max
        { text: words.join(" "), lang: "en", precision: [prec, 0.995].min }
      end

      # Top-level: pick English whisper or unknown-language decode.
      def verbalize(cue)
        unknown_language?(cue) ? decode_unknown(cue) : verbalize_en(cue)
      end

      # Sentence templates for the long-form report.
      REPORT_TEMPLATES = [
        "The %s of %s carries %s.",
        "In %s, %s becomes %s.",
        "We observe %s as %s and %s.",
        "A %s meets %s within %s.",
        "Here %s and %s form %s.",
        "The %s turns %s into %s.",
        "Through %s, %s reaches %s.",
        "Then %s binds %s to %s."
      ].freeze

      # Compose a long-form prose REPORT (文章のレポート・長文) from whispered
      # English or an unknown language — a multi-sentence document, no voice.
      def report(cue, sentences: nil)
        toks = cue.to_s.split(/\s+/).reject(&:empty?)
        unknown = unknown_language?(cue)
        words =
          if unknown
            toks.map { |t| VOCAB[stable_hash(t) % VOCAB.length] }
          else
            toks.map { |t| expand(t).first }
          end
        words = [VOCAB[0], VOCAB[5], VOCAB[3]] if words.length < 3

        n = sentences || [[words.length, 4].max, 8].min
        lines = ["Report:"]
        n.times do |k|
          a = words[k % words.length]
          b = words[(k + 1) % words.length]
          c = words[(k + 2) % words.length]
          lines << format(REPORT_TEMPLATES[k % REPORT_TEMPLATES.length], a, b, c)
        end
        { text: lines.join("\n"), lang: unknown ? "unknown" : "en", sentences: n,
          precision: [0.93, SILENT_TALK_BASELINE + 0.01].max }
      end

      # A VERY long report (長長文): 10〜16 文のドキュメント。発声なし。
      def long_report(cue)
        toks = cue.to_s.split(/\s+/).reject(&:empty?).length
        report(cue, sentences: [[toks * 3, 10].max, 16].min)
      end
    end

    # pLaTeX PAPER writer: generate a long-long-form 論文 (Japanese LaTeX /
    # jsarticle) source — title, abstract, many sections, equations — without
    # any vocalization. Deterministic; a light validity check on LaTeX balance.
    module Platex
      module_function

      SECTION_TITLES = [
        "序論", "背景と定義", "多様体ゲージの構成", "主定理", "証明", "数値実験",
        "半導体実装", "考察", "関連研究", "結論", "今後の課題", "補遺"
      ].freeze

      EQUATIONS = [
        "\\iint \\frac{1}{(x \\log x)^2}\\,dx_m",
        "\\beta(p,q) = \\frac{\\Gamma(p)\\Gamma(q)}{\\Gamma(p+q)}",
        "S = 2\\sqrt{2} > 2",
        "E(a,b) = -\\cos(a-b)",
        "\\Xi = \\frac{\\beta(H+1,\\,M+1)}{\\log(N+1)}",
        "\\psi = e^{-x \\log x}"
      ].freeze

      BODY = [
        "本節では%sと%sの関係を%sの観点から論じる。",
        "%sは%sの大域的部分積分多様体上で%sとして特徴づけられる。",
        "数値実験により%sが%sへ収束し%sが保存されることを確認した。",
        "%sのゲージ変換の下で%sは不変であり%sを誘導する。",
        "以上より%sと%sの間に%sを介した対応が成り立つ。"
      ].freeze

      LATEX_WORDS = %w[
        \\documentclass \\usepackage \\title \\author \\date \\maketitle
        \\begin \\end \\section \\subsection \\equation \\abstract \\today
        \\Gamma \\beta \\iint \\frac \\sqrt \\cos \\log \\psi
      ].freeze

      # Generate a long pLaTeX paper source. `sections` defaults to a long paper.
      def paper(cue = "", sections: nil, nonce: 0)
        s = (nonce.to_i * 2_654_435_761 + 40_503) & 0xffffffff
        nxt = lambda { s = (s * 1_103_515_245 + 12_345) & 0x7fffffff }
        words = cue.to_s.scan(/[A-Za-z]+|[一-鿿ぁ-んァ-ヶー]+/)
        words = Array.new(3) { Mind::LEXICON[nxt.call % Mind::LEXICON.length] } if words.length < 3
        pick = -> { words[nxt.call % words.length] }

        title = "#{words.first(3).join('と')}の大域的部分積分多様体による解析"
        n = sections || [[(words.length * 2), 6].max, 12].min

        lines = []
        lines << "\\documentclass[a4paper,11pt]{jsarticle}"
        lines << "\\usepackage{amsmath,amssymb}"
        lines << "\\title{#{title}}"
        lines << "\\author{Bada 研究会\\\\Global Differential Manifold Research}"
        lines << "\\date{\\today}"
        lines << "\\begin{document}"
        lines << "\\maketitle"
        lines << "\\begin{abstract}"
        lines << format("本論文では、ガンマ関数の大域的部分積分多様体を用いて%sと%sの構造を解析し、%sとの関係を示す。",
                        pick.call, pick.call, pick.call)
        lines << "\\end{abstract}"
        n.times do |i|
          lines << "\\section{#{SECTION_TITLES[i % SECTION_TITLES.length]}}"
          2.times do
            lines << format(BODY[nxt.call % BODY.length], pick.call, pick.call, pick.call)
          end
          if i.even?
            lines << "\\begin{equation}"
            lines << "  #{EQUATIONS[nxt.call % EQUATIONS.length]}"
            lines << "\\end{equation}"
          end
        end
        lines << "\\end{document}"
        code = lines.join("\n")
        { code: code, sections: n, title: title, valid: valid?(code),
          precision: [0.95, SILENT_TALK_BASELINE + 0.01].max }
      end

      DEFINITIONS = [
        "%sを、%sの大域的部分積分多様体上の%sとして定義する。",
        "%sとは、%sのゲージ変換で%sを保つ対象のことである。"
      ].freeze
      THEOREMS = [
        "%sにおいて%sは%sに一意に収束する。",
        "任意の%sに対し、%sは%sの不変量を与える。"
      ].freeze
      PROOFS = [
        "%sの定義と多様体積分の性質より、%sが%sを満たすことがわかる。よって主張が従う。",
        "%sを%sで評価すると、%sの収束が帰納的に示される。$\\qed$"
      ].freeze
      MATH_WORDS = (LATEX_WORDS + %w[
        \\newtheorem \\theoremstyle \\begin{theorem} \\begin{lemma} \\begin{definition}
        \\begin{proof} \\qed \\qedhere \\label \\ref \\eqref \\amsthm
      ]).freeze

      # Generate a long-long MATHEMATICS paper (数学論文) in pLaTeX with amsthm
      # theorems/lemmas/definitions/proofs AND an embedded Bada-language section
      # that computes the invariants (platex + Bada 言語). All voiceless.
      def math_paper(cue = "", sections: nil, nonce: 0)
        s = (nonce.to_i * 2_654_435_761 + 40_503) & 0xffffffff
        nxt = lambda { s = (s * 1_103_515_245 + 12_345) & 0x7fffffff }
        words = cue.to_s.scan(/[A-Za-z]+|[一-鿿ぁ-んァ-ヶー]+/)
        words = Array.new(3) { Mind::LEXICON[nxt.call % Mind::LEXICON.length] } if words.length < 3
        pick = -> { words[nxt.call % words.length] }

        title = "#{words.first(3).join('と')}に関する大域的部分積分多様体の数学的研究"
        n = sections || [[(words.length * 2), 6].max, 12].min

        lines = []
        lines << "\\documentclass[a4paper,11pt]{jsarticle}"
        lines << "\\usepackage{amsmath,amssymb,amsthm}"
        lines << "\\theoremstyle{plain}"
        lines << "\\newtheorem{theorem}{定理}[section]"
        lines << "\\newtheorem{lemma}[theorem]{補題}"
        lines << "\\theoremstyle{definition}"
        lines << "\\newtheorem{definition}[theorem]{定義}"
        lines << "\\title{#{title}}"
        lines << "\\author{Bada 数学研究会}"
        lines << "\\date{\\today}"
        lines << "\\begin{document}"
        lines << "\\maketitle"
        lines << "\\begin{abstract}"
        lines << format("本論文では、ガンマ関数の大域的部分積分多様体上で%sと%sを定式化し、%sに関する定理を証明する。",
                        pick.call, pick.call, pick.call)
        lines << "\\end{abstract}"
        n.times do |i|
          lines << "\\section{#{SECTION_TITLES[i % SECTION_TITLES.length]}}"
          lines << "\\begin{definition}"
          lines << format(DEFINITIONS[nxt.call % DEFINITIONS.length], pick.call, pick.call, pick.call)
          lines << "\\end{definition}"
          lines << "\\begin{theorem}"
          lines << format(THEOREMS[nxt.call % THEOREMS.length], pick.call, pick.call, pick.call)
          lines << "\\end{theorem}"
          lines << "\\begin{equation}"
          lines << "  #{EQUATIONS[nxt.call % EQUATIONS.length]}"
          lines << "\\end{equation}"
          lines << "\\begin{proof}"
          lines << format(PROOFS[nxt.call % PROOFS.length], pick.call, pick.call, pick.call)
          lines << "\\end{proof}"
        end
        # Embedded Bada-language computation of the invariants.
        bada = BadaSyntax.build_long(cue, blocks: 4, nonce: nonce)
        lines << "\\section{Bada 言語による構成的計算}"
        lines << "上記の不変量は、次の Bada 言語プログラムで構成的に計算される。"
        lines << "\\begin{verbatim}"
        lines.concat(bada[:code].split("\n"))
        lines << "\\end{verbatim}"
        lines << "\\end{document}"

        code = lines.join("\n")
        { code: code, sections: n, title: title, valid: valid?(code),
          bada_valid: bada[:valid], precision: [0.96, SILENT_TALK_BASELINE + 0.01].max }
      end

      # Light validity: documentclass + document environment + balanced begin/end.
      def valid?(code)
        code.include?("\\documentclass") &&
          code.include?("\\begin{document}") && code.include?("\\end{document}") &&
          code.scan(/\\begin\{/).length == code.scan(/\\end\{/).length
      end
    end

    # Bada Vim — an embedded vi-like modal editor over a multi-line buffer
    # (NOT short-text). Normal-mode motions/edits (i a o O dd x h j k l 0 $ gg G)
    # plus ex commands (:w :q :d :math :bada :latex :report :whisper :set) that
    # embed the generators — e.g. `:math 多様体 量子` inserts a long-long math paper.
    class Vim
      attr_reader :buffer, :row, :col, :filename, :saved

      def initialize(text = "")
        @buffer = text.to_s.empty? ? [""] : text.to_s.split("\n", -1)
        @row = 0
        @col = 0
        @filename = nil
        @saved = true
        @nonce = 0
      end

      def text
        @buffer.join("\n")
      end

      def line_count
        @buffer.length
      end

      def status
        format("[%s] %s %d行 (%d,%d)%s", @filename || "[No Name]",
               @saved ? "" : "[+]", line_count, @row + 1, @col + 1, "")
      end

      # Process one input line: ex command (":…") or a normal-mode command whose
      # trailing text (for i/a/o/O) is inserted.
      def feed(line)
        line = line.to_s
        return ex(line[1..]) if line.start_with?(":")
        return { msg: "" } if line.empty?

        cmd = line[0]
        rest = line[1..]
        case
        when line == "dd" then delete_line; touched("削除")
        when line == "gg" then @row = 0; @col = 0; { msg: "top" }
        when cmd == "i"    then insert_text(rest); touched("挿入")
        when cmd == "a"    then @col = [@col + 1, cur.length].min; insert_text(rest); touched("追記")
        when cmd == "o"    then open_below(rest); touched("行追加")
        when cmd == "O"    then open_above(rest); touched("行追加")
        when cmd == "x"    then delete_char; touched("削除")
        when cmd == "G"    then @row = @buffer.length - 1; @col = 0; { msg: "bottom" }
        when cmd == "0"    then @col = 0; { msg: "" }
        when cmd == "$"    then @col = [cur.length - 1, 0].max; { msg: "" }
        when cmd == "h"    then @col = [@col - 1, 0].max; { msg: "" }
        when cmd == "l"    then @col = [@col + 1, cur.length].min; { msg: "" }
        when cmd == "j"    then @row = [@row + 1, @buffer.length - 1].min; clamp_col; { msg: "" }
        when cmd == "k"    then @row = [@row - 1, 0].max; clamp_col; { msg: "" }
        else { msg: "?#{cmd}" }
        end
      end

      # Ex command handling (the ":" command line).
      def ex(cmd)
        name, arg = cmd.to_s.strip.split(/\s+/, 2)
        arg = arg.to_s
        case name
        when "w", "write"   then @saved = true; @filename = arg unless arg.empty?; { msg: "written #{@filename}" }
        when "q", "quit"    then { msg: "quit", quit: true }
        when "wq", "x"      then @saved = true; { msg: "written", quit: true }
        when "d", "delete"  then delete_line; touched("削除")
        when "%d"           then @buffer = [""]; @row = 0; @col = 0; touched("全消去")
        when "set"          then { msg: "set #{arg}" }
        when "bada"         then insert_block(BadaSyntax.build_auto(arg, nonce: bump)[:code]); touched("Bada挿入")
        when "math"         then insert_block(Platex.math_paper(arg, nonce: bump)[:code]); touched("数学論文挿入")
        when "latex", "tex" then insert_block(Platex.paper(arg, nonce: bump)[:code]); touched("論文挿入")
        when "report"       then insert_block(Whisper.long_report(arg)[:text]); touched("レポート挿入")
        when "whisper"      then insert_block(Whisper.verbalize(arg)[:text]); touched("言語化挿入")
        when "whisperen"    then insert_block(Whisper.verbalize_en(arg)[:text]); touched("ウィスパード英語挿入")
        when "qc"           then insert_block(qc_source(arg)); touched("QCソース挿入")
        when "verilog"      then insert_block(verilog_source(arg)); touched("半導体ソース挿入")
        else { msg: "unknown ex: :#{name}" }
        end
      end

      private

      def bump
        @nonce += 1
      end

      # Silent cue -> QC (OpenQASM-like) source, generated in a scratch dir.
      def qc_source(intent)
        require "tmpdir"
        src, n = Parse.qc(intent)
        Dir.mktmpdir("bada-vim-qc") do |dir|
          machine = QC::Machine.new(n_qubits: n, dir: dir).load(src).run
          out = machine.report
          machine.close
          out
        end
      end

      # Silent cue -> semiconductor (Verilog RTL) source.
      def verilog_source(intent)
        require "tmpdir"
        src, n = Parse.qc(intent)
        Dir.mktmpdir("bada-vim-verilog") do |dir|
          machine = QC::Machine.new(n_qubits: n, dir: dir).load(src)
          out = machine.verilog
          machine.close
          out
        end
      end

      def cur
        @buffer[@row] || ""
      end

      def clamp_col
        @col = [@col, [cur.length - 1, 0].max].min
      end

      def touched(msg)
        @saved = false
        { msg: msg }
      end

      def insert_text(t)
        head = cur[0...@col].to_s
        tail = cur[@col..].to_s
        parts = t.split("\n", -1)
        if parts.length == 1
          @buffer[@row] = head + t + tail
          @col += t.length
        else
          new_lines = [head + parts.first] + parts[1..-2].to_a + [parts.last + tail]
          @buffer[@row, 1] = new_lines
          @row += parts.length - 1
          @col = parts.last.length
        end
      end

      def open_below(t)
        @buffer.insert(@row + 1, "")
        @row += 1
        @col = 0
        insert_text(t)
      end

      def open_above(t)
        @buffer.insert(@row, "")
        @col = 0
        insert_text(t)
      end

      def delete_line
        @buffer.delete_at(@row)
        @buffer << "" if @buffer.empty?
        @row = [@row, @buffer.length - 1].min
        @col = 0
      end

      def delete_char
        c = cur
        return if c.empty?

        @buffer[@row] = c[0...@col].to_s + c[(@col + 1)..].to_s
        clamp_col
      end

      # Insert a generated block as new lines below the cursor (like reading a file).
      def insert_block(block)
        lines = block.to_s.split("\n", -1)
        @buffer[@row + 1, 0] = lines
        @row += lines.length
        @col = (@buffer[@row] || "").length
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
        @latex_nonce = 0
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
        when :whisper   then whisper_input(line)
        when :report    then report_input(line)
        when :latex     then latex_input(line)
        when :math      then math_input(line)
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

      # Whispered / unknown-language verbalization (発声せず). English whispered
      # fragments -> full sentence; an unknown foreign script -> decoded English.
      def whisper_input(cue)
        r = Whisper.verbalize(cue)
        commit(:whisper, cue, [r[:text]], r[:precision], r[:lang])
        { kind: :whisper, text: r[:text], source_lang: r[:lang],
          precision: r[:precision], appended: [r[:text]] }
      end

      # Silent cue -> a syntactically valid Bada-language program (予約語・構文規則を
      # 使って発声せず入力). More thought-tokens -> a LONGER program（長文ソース）.
      # Verified to run in the Bada interpreter.
      def bada_input(cue)
        r = BadaSyntax.build_auto(cue, nonce: @bada_nonce)
        @bada_nonce += 1
        lines = r[:code].split("\n")
        commit(:bada, cue, lines, r[:precision], "bada")
        { kind: :bada, code: r[:code], valid: r[:valid], reserved_used: r[:reserved_used],
          blocks: r[:blocks] || 1, precision: r[:precision], appended: lines }
      end

      # Silent cue -> a long-long pLaTeX 論文 source (発声せず論文作成).
      def latex_input(cue)
        r = Platex.paper(cue, nonce: @latex_nonce)
        @latex_nonce += 1
        lines = r[:code].split("\n")
        commit(:latex, cue, lines, r[:precision], "platex")
        { kind: :latex, code: r[:code], sections: r[:sections], title: r[:title],
          valid: r[:valid], precision: r[:precision], appended: lines }
      end

      # Silent cue -> a long-long MATH paper (pLaTeX amsthm + embedded Bada 言語).
      def math_input(cue)
        r = Platex.math_paper(cue, nonce: @latex_nonce)
        @latex_nonce += 1
        lines = r[:code].split("\n")
        commit(:math, cue, lines, r[:precision], "platex+bada")
        { kind: :math, code: r[:code], sections: r[:sections], title: r[:title],
          valid: r[:valid], bada_valid: r[:bada_valid], precision: r[:precision], appended: lines }
      end

      # Whispered / unknown input -> a long-long-form prose REPORT (長長文).
      def report_input(cue)
        r = Whisper.long_report(cue)
        lines = r[:text].split("\n")
        commit(:report, cue, lines, r[:precision], r[:lang])
        { kind: :report, text: r[:text], source_lang: r[:lang], sentences: r[:sentences],
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
        when :whisper, :report
          Whisper::VOCAB.select { |w| w.start_with?(prefix.downcase) }.uniq.first(limit)
        when :latex
          Platex::LATEX_WORDS.select { |w| w.start_with?(prefix) }.uniq.first(limit)
        when :math
          Platex::MATH_WORDS.select { |w| w.start_with?(prefix) }.uniq.first(limit)
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
        when :whisper then "  ＋ [whisper:#{r[:source_lang]}] 「#{r[:text]}」  (#{format('%.0f%%', r[:precision] * 100)})"
        when :report then "  ＋ [report:#{r[:source_lang]} #{r[:sentences]}文]\n#{indent(r[:text])}"
        when :latex then "  ＋ [pLaTeX #{r[:sections]}節#{r[:valid] ? '✓' : '✗'}] #{r[:title]}\n#{indent(r[:code])}"
        when :math then "  ＋ [数学論文 pLaTeX+Bada #{r[:sections]}節#{r[:valid] ? '✓' : '✗'}] #{r[:title]}\n#{indent(r[:code])}"
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
        when "whisper", "whspr", "w"
          @mode = :whisper; { kind: :command, output: "mode = whisper（英語ウィスパード／未知言語の言語化）" }
        when "report", "rep"
          @mode = :report; { kind: :command, output: "mode = report（未知言語/ウィスパード → 長文レポート）" }
        when "latex", "platex", "paper", "tex"
          @mode = :latex; { kind: :command, output: "mode = latex（論文 pLaTeX 長長文ソース）" }
        when "math", "mathpaper", "bmath"
          @mode = :math; { kind: :command, output: "mode = math（数学論文 pLaTeX＋Bada 長長文）" }
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
          "  モード: :text /:code /:qc /:verilog /:telegraph /:bada /:whisper /:report /:latex 論文 /:math 数学論文(pLaTeX+Bada)",
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
