# frozen_string_literal: true

require_relative "conjecture"
require_relative "proof"
require_relative "../manifold"
require_relative "../thurston"
require_relative "../millennium"

module Bada
  module Prover
    # UnknownAprioriEngine (未知事前エンジン): imagine unsolved-style math
    # problems (seeded by the manifold/entropy) and decide them with sound
    # automated reasoning — proving the provable, disproving the false with
    # counterexamples, and honestly flagging genuine open problems with evidence.
    class UnknownAprioriEngine
      def imagine(question, count: 5)
        ConjectureGenerator.imagine(question, count: count)
      end

      def prove(conjecture)
        conjecture.prove
      end

      # Imagine + prove a batch; return structured results.
      def discover(question, count: 5)
        imagine(question, count: count).map do |c|
          { conjecture: c, proof: c.prove }
        end
      end

      # Human-readable rendering of a discovery run.
      def render(question, count: 5)
        results = discover(question, count: count)
        xi = Manifold.xi(question)
        place = Thurston.place_entropy(question)
        out = []
        out << "── 未知事前エンジン (Unknown A-priori Engine) ──"
        out << format("質問から想像（多様体不変量 Ξ=%.4f, 幾何=%s）。健全な自動推論で判定。",
                      xi, place[:geometry])
        out << ""
        proved = disproved = open = 0
        results.each do |r|
          c = r[:conjecture]
          p = r[:proof]
          case p.status
          when :proved then proved += 1
          when :disproved then disproved += 1
          else open += 1
          end
          out << "【命題#{c.id}】#{c.title}"
          out << "  主張: #{c.statement}"
          out << "  判定: #{p.symbol}  （手法: #{p.method}）"
          p.steps.each { |s| out << "    #{s}" }
          out << "    反例: #{p.counterexample.inspect}" if p.counterexample
          out << "    証拠: #{p.evidence.inspect}" if p.evidence
          out << ""
        end
        out << format("要約: 証明 %d 件 / 反証 %d 件 / 未解決 %d 件。", proved, disproved, open)
        out << "※ 未解決は経験的証拠であり証明ではない（健全性のため明示）。"
        out.join("\n")
      end

      # Generate a proof paper (Markdown+LaTeX) for one conjecture.
      def paper(conjecture)
        p = conjecture.prove
        xi = Manifold.invariant(conjecture.statement)
        mil = Millennium.decompose_theory(conjecture.statement)
        verdict = { proved: "定理 (Theorem)", disproved: "反例による反証 (Refutation)",
                    open: "予想 (Conjecture, 未解決)" }[p.status]
        <<~PAPER
          # #{verdict}: #{conjecture.title}

          **生成**: Bada/Ruby 未知事前エンジン · **起点**: #{mil[:origin]}

          ## 主張 (Statement)

          $$#{conjecture.latex}$$

          ## 判定 (Verdict): #{p.symbol}

          手法: **#{p.method}**

          ## 証明 / 検証 (Proof / Verification)

          #{p.steps.map.with_index(1) { |s, i| "#{i}. #{s}" }.join("\n")}
          #{p.counterexample ? "\n**反例**: `#{p.counterexample.inspect}`" : ''}
          #{p.evidence ? "\n**経験的証拠**: `#{p.evidence.inspect}`（証明ではない）" : ''}

          ## 文脈 (Context)

          本命題の多様体不変量は \\(\\Xi = #{format('%.4f', xi[:invariant])}\\)。理論的には
          **#{mil[:dominant]}** に最も近い（ガンマ関数の大域的部分積分多様体を起点とする分解）。

          ## 健全性に関する注記 (Soundness)

          本エンジンは、決定可能なクラス（多項式和の帰納法、剰余系の全数検査、有限領域）に
          ついてのみ「証明完了」と判定する。反例は健全な反証である。決定できない命題は
          「未解決」とし、経験的証拠のみを提示する（証明とは主張しない）。
        PAPER
      end
    end

    # Alias for the conversational name.
    Engine = UnknownAprioriEngine
  end
end
