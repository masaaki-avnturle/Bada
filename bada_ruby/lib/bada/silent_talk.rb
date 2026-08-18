# frozen_string_literal: true

require_relative "mind"
require_relative "coder"

module Bada
  # Bada::SilentTalk — a silent-talk INPUT METHOD (発声せずに文章を入力する機能).
  #
  # ⚠️ 生成シミュレーションです。実在の脳から思考を取り出す BCI ではありません。
  # 発声せずに入力した*疎な手がかり*（キーワード／略記／特徴テキスト）を、ガンマ関数の
  # 大域的部分積分多様体をゲージにした Mind トランスフォーマーが**文章に言語化**して
  # ドキュメントに追記します。コマンド機能でモード切替・補完・取り消しができ、コード
  # モードではプログラミング言語トランスフォーマー（Bada::Coder）で**ソースコードを入力**
  # できます。silent-talk 基準（0.92）を超える simulated 精度を報告します。
  #
  #   s = Bada::SilentTalk::Session.new
  #   s.feed("光 記憶 波")     # -> 文章を言語化して追記
  #   s.feed(":code")          # コードモードへ
  #   s.feed("fibonacci 10")   # -> プログラムを生成して追記
  #   puts s.text              # 組み上がったドキュメント
  module SilentTalk
    SILENT_TALK_BASELINE = Mind::SILENT_TALK_BASELINE

    # A committed block of input -> expansion.
    Block = Struct.new(:kind, :input, :lines, :precision, :language, keyword_init: true)

    class Session
      attr_reader :mode, :language, :blocks

      def initialize(mode: :text, language: nil, mind: Mind::Reader.new)
        @mode = mode           # :text | :code
        @language = language   # code language (nil = auto-detect)
        @mind = mind
        @blocks = []
      end

      # Feed one silent input line. Returns a result Hash describing the effect.
      def feed(input)
        line = input.to_s.strip
        return { kind: :noop } if line.empty?
        return command(line) if line.start_with?(":")

        @mode == :code ? code_input(line) : text_input(line)
      end

      # Verbalize a sparse cue into a sentence and append it.
      def text_input(cue)
        r = @mind.read(cue)
        block = Block.new(kind: :text, input: cue, lines: [r[:verbalization]],
                          precision: r[:precision])
        @blocks << block
        { kind: :text, verbalization: r[:verbalization], precision: r[:precision],
          appended: block.lines }
      end

      # Turn an intent into source code and append it.
      def code_input(intent)
        r = Coder.generate(intent, language: @language)
        lines = r[:code].split("\n")
        block = Block.new(kind: :code, input: intent, lines: lines,
                          precision: r[:precision], language: r[:language])
        @blocks << block
        { kind: :code, code: r[:code], language: r[:language], recipe: r[:recipe],
          precision: r[:precision], appended: lines }
      end

      # Word completion for the current mode.
      def complete(prefix, limit: 8)
        prefix = prefix.to_s
        return [] if prefix.empty?

        if @mode == :code
          Coder.complete(prefix, language: @language, limit: limit)
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
          io_out.print(@mode == :code ? "silent[code:#{@language || 'auto'}]> " : "silent[text]> ")
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

      # Format a feed result for the console.
      def render(r)
        case r[:kind]
        when :text then "  ＋ 「#{r[:verbalization]}」  (#{format('%.0f%%', r[:precision] * 100)})"
        when :code then "  ＋ [#{r[:language]}]#{r[:recipe] ? ' recipe' : ''}\n#{indent(r[:code])}"
        when :command then r[:output]
        when :noop then ""
        else r.inspect
        end
      end

      private

      def command(line)
        cmd, rest = line[1..].split(/\s+/, 2)
        rest = rest.to_s.strip
        case cmd
        when "text"     then @mode = :text; { kind: :command, output: "mode = text（言語化入力）" }
        when "code"     then @mode = :code; { kind: :command, output: "mode = code（コード入力）" }
        when "lang"     then @language = rest.empty? ? nil : rest
                             { kind: :command, output: "language = #{@language || 'auto'}" }
        when "complete", "c"
          { kind: :command, output: "補完: #{complete(rest).join('  ')}" }
        when "undo"     then b = @blocks.pop
                             { kind: :command, output: b ? "取り消し: 「#{b.input}」" : "（履歴なし）" }
        when "clear"    then @blocks.clear; { kind: :command, output: "クリアしました" }
        when "show"     then { kind: :command, output: text.empty? ? "（空）" : text }
        when "precision"
          { kind: :command, output: format("precision = %.1f%%", precision * 100) }
        when "help"     then { kind: :command, output: help }
        else { kind: :command, output: "unknown command: :#{cmd}" }
        end
      end

      def intro
        [
          "Bada サイレント・トーク入力メソッド (silent talk IME, simulation)",
          "  発声せず、疎な手がかりを入力すると文章に言語化します。",
          "  コマンド: :text :code :lang <l> :complete <prefix> :undo :clear :show :precision :help :quit"
        ].join("\n")
      end

      def help
        ":text 言語化入力 / :code コード入力 / :lang <ruby|python…> / " \
          ":complete <prefix> 補完 / :undo 取消 / :clear / :show / :precision / :quit"
      end

      def indent(code)
        code.split("\n").map { |l| "    #{l}" }.join("\n")
      end

      # Candidate words for text-mode completion: the mind lexicon, the built-in
      # priors' words, and words already present in the document.
      def text_vocab
        @text_vocab ||= begin
          jp = Mind::MIND_CORPUS.join.scan(/[一-鿿ぁ-んァ-ヶー]+/)
          en = Mind::MIND_CORPUS_EN.join(" ").scan(/[A-Za-z]+/)
          (Mind::LEXICON + jp + en).uniq
        end
        (@text_vocab + text.scan(/[A-Za-z]+|[一-鿿ぁ-んァ-ヶー]+/)).uniq
      end
    end
  end
end
