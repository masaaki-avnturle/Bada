# frozen_string_literal: true

module Bada
  module Penrose
    # Roger Penrose's graphical (diagrammatic) notation, as a palette of
    # picture-symbols (絵記号). In Penrose notation a tensor is a shape whose
    # emerging lines are its indices; joining two lines is contraction (an
    # implicit Einstein sum); derivatives are drawn as a ring/hoop around an
    # operand with one extra line (the derivative index); (anti)symmetrisation
    # is a bar across a bundle of lines.
    #
    # Because this is a terminal app, the palette renders each symbol as ASCII
    # art and records the drawing token used on the canvas plus its semantics.
    module Palette
      # key => { glyph:, token:, name:, math:, meaning: }
      GLYPHS = {
        tensor: {
          glyph: ["┌───┐", "│ T │", "└───┘"], token: "[T]",
          name: "テンソル (tensor box)", math: "T^{..}_{..}",
          meaning: "箱から出る線が添字。線の本数 = 階数。"
        },
        wire: {
          glyph: ["─────"], token: "-", name: "添字線 (index wire)",
          math: "index", meaning: "1本の線は1つの添字。"
        },
        contraction: {
          glyph: ["[A]─[B]"], token: "[A]-[B]", name: "縮約 (contraction)",
          math: "A^{.k} B_{k.} = Σ_k", meaning: "2つの線を繋ぐと、その添字で総和（縮約）。"
        },
        metric: {
          glyph: ["┌───┐", "│ g │", "└───┘"], token: "[g]",
          name: "計量 (metric)", math: "g_{μν}", meaning: "添字の上げ下げに使う対称テンソル。"
        },
        cup: {
          glyph: ["╰───╯"], token: "U", name: "カップ (raise index)",
          math: "g^{μν}", meaning: "線を折り返して添字を上げる。"
        },
        cap: {
          glyph: ["╭───╮"], token: "N", name: "キャップ (lower index)",
          math: "g_{μν}", meaning: "線を折り返して添字を下げる。"
        },
        delta: {
          glyph: ["──δ──"], token: "=", name: "クロネッカー δ (identity wire)",
          math: "δ^μ_ν", meaning: "まっすぐな線は恒等（クロネッカーのデルタ）。"
        },
        epsilon: {
          glyph: ["┌───┐", "│ ε │", "└─╲─┘"], token: "[E]",
          name: "レヴィ・チヴィタ ε (antisymmetric)", math: "ε_{μνρ...}",
          meaning: "完全反対称テンソル。"
        },
        nabla: {
          glyph: ["  ╭─∇─╮ ", "  │ ▢ │ ", "  ╰───╯ ", "    │   "], token: "(D X)",
          name: "共変微分 ∇ (covariant derivative ring)",
          math: "∇_μ T", meaning: "オペランドを囲む輪。下に出る1本の線が微分の添字 μ。"
        },
        partial: {
          glyph: ["  ╭─∂─╮ ", "  │ ▢ │ ", "  ╰───╯ ", "    │   "], token: "(d X)",
          name: "偏微分 ∂", math: "∂_μ f", meaning: "輪に ∂ を入れた偏微分。数値は有限差分で計算。"
        },
        integral: {
          glyph: ["⌠      ", "⎮ ▢ dμ ", "⌡      "], token: "(I X dμ)",
          name: "積分 ∫", math: "∫ T dμ", meaning: "オペランドを積分記号で囲む。添字 μ を縮約的に積む。"
        },
        symmetrize: {
          glyph: ["═════", "[ T ]"], token: "S{...}",
          name: "対称化 (symmetriser bar)", math: "T_{(μν)}",
          meaning: "線束を横切る太いバー = 添字の対称化。"
        },
        antisymmetrize: {
          glyph: ["≋≋≋≋≋", "[ T ]"], token: "A{...}",
          name: "反対称化 (antisymmetriser bar)", math: "T_{[μν]}",
          meaning: "波線のバー = 添字の反対称化。"
        }
      }.freeze

      module_function

      def glyphs
        GLYPHS
      end

      # Render the full palette as a printable string.
      def render
        out = []
        out << "╔══════════════════════════════════════════════════════════════╗"
        out << "║  ロジャー・ペンローズ 絵記号パレット  (Penrose graphical)      ║"
        out << "╚══════════════════════════════════════════════════════════════╝"
        GLYPHS.each do |key, g|
          out << ""
          out << "● #{g[:name]}   [#{key}]   描画トークン: #{g[:token].inspect}"
          out << "    #{g[:math]}"
          g[:glyph].each { |line| out << "      #{line}" }
          out << "    → #{g[:meaning]}"
        end
        out << ""
        out << "描画の約束: 行に [A]-[B] と書くと A と B を縮約。両端の小文字/数字は自由添字。"
        out << "  例:  i-[A]-[B]-j   ⇒  A_{i k} B_{k j} → result_{i j}  (行列積)"
        out.join("\n")
      end
    end
  end
end
