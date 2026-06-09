# frozen_string_literal: true

require_relative "palette"
require_relative "canvas"
require_relative "evaluator"
require_relative "paper"
require_relative "codegen"
require_relative "../info_engine"
require_relative "../millennium"

module Bada
  module Penrose
    # Studio — Facade for the whole Penrose pipeline:
    #   draw (絵記号) -> auto-compute -> ask (auto answer) -> paper -> source code.
    class Studio
      attr_reader :diagram, :drawing

      def initialize(knowledge: nil, seed: nil)
        @info = InfoEngine.new(knowledge: knowledge, seed: seed)
      end

      def palette
        Palette.render
      end

      # Draw a diagram (ASCII picture-symbols), optionally with tensor values.
      def draw(drawing, values: {})
        @drawing = drawing
        @diagram = Canvas.parse(drawing, values: values)
        self
      end

      # Build a diagram programmatically via the DSL.
      def build(&block)
        @diagram = Diagram.build(&block)
        @drawing = Canvas.render(@diagram)
        self
      end

      # Auto-compute the drawn diagram.
      def compute
        Evaluator.evaluate(@diagram)
      end

      # Auto-answer a question about the drawn diagram.
      def ask(question)
        e = compute
        decomp = Millennium.decompose_theory(question.to_s + " " + e[:einsum])
        out = []
        out << "── ペンローズ図式 自動解答 (Bada/Ruby) ──"
        out << "図式: #{@diagram.einsum_string}"
        out << "数値解: #{answer_value(e)}"
        out << "質問: #{question}"
        out << ""
        out << "解答: この図式は #{e[:output].empty? ? 'スカラー' : "自由添字 #{e[:output].join(',')} を持つテンソル"}" \
               "を、結ばれた線（縮約）に沿ったアインシュタイン総和として計算する。"
        out << "主たる理論的背景は #{decomp[:dominant]}（ガンマ関数の大域的部分積分多様体を起点）。"
        e[:notes].each { |n| out << "注: #{n}" }
        out.join("\n")
      end

      def paper(question: nil, title: nil)
        PaperGenerator.generate(@diagram, question: question, title: title)
      end

      def code(standalone: false)
        standalone ? CodeGenerator.standalone_ruby(@diagram) : CodeGenerator.ruby(@diagram, drawing: @drawing)
      end

      # The full bundle: compute + answer + paper + source code.
      def report(question: nil)
        e = compute
        [
          "════════ 入力された絵記号 (Penrose diagram) ════════",
          @drawing,
          "",
          "════════ 自動計算 (auto-compute) ════════",
          Canvas.render(@diagram),
          "einsum: #{e[:einsum]}",
          "結果: #{answer_value(e)}",
          "",
          "════════ 自動解答 (ChatGPT auto-answer) ════════",
          ask(question || "この図式は何を計算しているか？"),
          "",
          "════════ 論文 (auto paper, Markdown+LaTeX) ════════",
          paper(question: question),
          "",
          "════════ 生成ソースコード (Ruby) ════════",
          code
        ].join("\n")
      end

      private

      def answer_value(e)
        if e[:scalar] then format("%.6g (スカラー)", e[:scalar])
        elsif e[:result] then e[:result].inspect
        else "（記号式のみ：成分値を与えると自動で数値解を計算）"
        end
      end
    end
  end
end
