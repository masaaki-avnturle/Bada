# frozen_string_literal: true

require_relative "canvas"
require_relative "evaluator"
require_relative "../millennium"
require_relative "../manifold"
require_relative "../thurston"

module Bada
  module Penrose
    # Generate a short research paper (Markdown + LaTeX) from a drawn Penrose
    # diagram and its computation, grounded in the Bada manifold/Millennium
    # theory. This is the "論文作成" output.
    module PaperGenerator
      module_function

      def generate(diagram, question: nil, title: nil)
        eval = Evaluator.evaluate(diagram)
        ascii = Canvas.render(diagram)
        topic = question || eval[:einsum]
        xi = Manifold.invariant(topic)
        place = Thurston.place_entropy(topic)
        mil = Millennium.decompose_theory(topic)
        title ||= "ペンローズ図式 #{eval[:einsum].split('→').last.strip} の縮約と理論的分解"

        latex = einsum_to_latex(eval[:einsum])
        result_str = format_result(eval)

        <<~PAPER
          # #{title}

          **著者**: Bada/Ruby OmegaChat（自動生成） · **起点**: #{mil[:origin]}

          ## 要旨 (Abstract)

          本稿はロジャー・ペンローズの図式記法で描かれたテンソル図
          を自動的に縮約（アインシュタインの総和）し、その結果を山口フレームワークの
          大域的部分積分多様体 \\(\\iint 1/(x\\log x)^2\\) のエントロピー不変量
          \\(\\Xi = #{format('%.4f', xi[:invariant])}\\) の下で解釈する。図式は
          サーストン・ペレルマン多様体 \\(#{place[:geometry]}\\)（曲率 #{format('%.2f', place[:curvature])}）
          に配置され、主たる理論分解先は **#{mil[:dominant]}** である。

          ## 1. 図式 (Penrose diagram)

          ```
          #{ascii}
          ```

          ## 2. 方程式 (Einstein notation)

          $$#{latex}$$

          縮約された添字は図式上で結ばれた線に対応し、自由添字
          \\(#{eval[:output].join(', ')}\\) が結果の脚（出力）となる。

          ## 3. 計算結果 (Result)

          #{result_str}

          ## 4. 理論的分解 (Theory decomposition)

          ガンマ関数 \\(\\Gamma\\) における大域的部分積分多様体を起点として、本図式は
          クレイ・ミレニアム7問へ次のように分解される：

          #{mil[:decomposition].first(3).map { |d| "- **#{d[:name]}**（関連度 #{format('%.3f', d[:score])}）: #{d[:theory]}" }.join("\n")}

          ペレルマンの F-エントロピー汎関数は
          \\(F = \\int (R+|\\nabla f|^2)e^{-f}dV = #{format('%.4f', place[:perelman_f])}\\)
          を与え、リッチ流 \\(\\partial_t g_{ij} = -2R_{ij}\\) の下で
          #{place[:ricci_collapsed] ? '有限時間特異点へ収束（幾何化）する' : '安定に発展する'}。

          ## 5. 結論 (Conclusion)

          描かれたペンローズ図式は機械的に縮約可能であり、その不変量は複素回転体
          （特殊相対性理論のコマ幾何）の可積分系の下で保存される。本手法は図式から
          自動で方程式・数値解・ソースコードを生成する。

          ## 参考 (References)
          - R. Penrose, *Applications of negative dimensional tensors* (1971).
          - G. Perelman, *The entropy formula for the Ricci flow* (2002).
          - C. Shannon, *A Mathematical Theory of Communication* (1948).
          - M. Yamaguchi, *TupleSpace / Global Differential Manifold* (reports).
        PAPER
      end

      def einsum_to_latex(s)
        s.gsub("→", "\\;\\to\\;")
         .gsub(/_\{([^}]*)\}/) { "_{#{$1.split.join('')}}" }
         .gsub("∇", "\\nabla ").gsub("∂", "\\partial ").gsub("∫", "\\int ")
      end

      def format_result(eval)
        if eval[:scalar]
          "スカラー値: \\(#{format('%.6g', eval[:scalar])}\\)"
        elsif eval[:result]
          "テンソル成分:\n\n```\n#{eval[:result].inspect}\n```"
        else
          "（テンソル値が未指定のため記号式のみ。成分を与えると数値解を自動計算します。）\n\n" \
          "記号式: `#{eval[:einsum]}`"
        end
      end
    end
  end
end
