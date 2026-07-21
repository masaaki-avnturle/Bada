# frozen_string_literal: true

require_relative "glyph_svg"

module Bada
  module Penrose
    # Roger Penrose's graphical (diagrammatic) notation, as a palette of
    # picture-symbols (絵記号), following his hand-drawn convention:
    #
    #   * a tensor is a SHAPE (box/triangle); a line leaving the TOP is an UPPER
    #     index, a line leaving the BOTTOM is a LOWER index (本数 = 階数);
    #   * joining an upper line to a lower line is contraction (Einstein sum);
    #   * the covariant derivative ∇ is a big HOOP (ring) drawn AROUND the
    #     operand, with the derivative index as an extra leg out of the ring;
    #   * (anti)symmetrisation is a straight / wavy BAR across a bundle of legs;
    #   * a crossing of two lines equals minus the uncrossed pair (antisymmetry).
    #
    # Each symbol carries an ASCII glyph (for the terminal) and, via GlyphSVG, a
    # faithful SVG rendering (for the web app), plus its drawing token/semantics.
    module Palette
      # key => { glyph:, token:, name:, math:, meaning: }
      GLYPHS = {
        tensor: {
          glyph: ["  │   │  ", "┌─┴───┴─┐", "│   T   │", "└─┬───┬─┘", "  │   │  "],
          token: "[T]", name: "テンソル (tensor box)", math: "T^{ab}_{cd}",
          meaning: "図形＝テンソル。上に出る線が上付き添字、下に出る線が下付き添字。線の本数=階数。"
        },
        matrix: {
          glyph: ["  │  ", "┌─┴─┐", "│ M │", "└─┬─┘", "  │  "],
          token: "[M]", name: "行列 (matrix = (1,1)テンソル)", math: "M^a_b",
          meaning: "上付き1本(行)＋下付き1本(列)＝行列。上の脚を次の下の脚へ繋ぐと行列積。"
        },
        matmul: {
          glyph: ["  │  ", "┌─┴─┐", "│ A │", "└─┬─┘", "┌─┴─┐", "│ B │", "└─┬─┘", "  │  "],
          token: "[A][B]", name: "行列積 (matrix product)", math: "(AB)^a_c = A^a_b B^b_c",
          meaning: "A の下の脚と B の上の脚を縦に繋ぐ＝共通添字 b の縮約。上下に残る脚が結果の行・列。"
        },
        vector: {
          glyph: ["  │  ", "┌─┴─┐", "│ v │", "└───┘"],
          token: "[v]", name: "ベクトル (vector)", math: "v^a",
          meaning: "上に1本だけ出る線＝1階反変テンソル（ベクトル）。"
        },
        wire: {
          glyph: ["│", "│", "│"], token: "-", name: "添字線 (index wire)",
          math: "index", meaning: "1本の線は1つの添字。上向き=反変、下向き=共変。"
        },
        contraction: {
          glyph: ["┌─┐   ┌─┐", "│A├─╮ │B│", "└─┘ ╰─┤ │", "     └─┘"],
          token: "[A]-[B]", name: "縮約 (contraction)",
          math: "A^{.k} B_{k.} = Σ_k", meaning: "上付きの線と下付きの線を繋ぐと、その添字で総和（縮約）。"
        },
        metric: {
          glyph: ["┌─────┐", "│  g  │", "└─┬─┬─┘", "  │ │  "],
          token: "[g]", name: "計量 (metric)", math: "g_{ab}",
          meaning: "対称テンソル。下2本＝g_{ab}。カップ/キャップで添字を上げ下げ。"
        },
        cup: {
          glyph: ["╭───╮", "│   │", "▲   ▲"], token: "U", name: "カップ ∪ (添字を上げる)",
          math: "g^{ab}", meaning: "線を上向きに折り返す ∪ ＝ 添字を上げる（反変化）。"
        },
        cap: {
          glyph: ["▼   ▼", "│   │", "╰───╯"], token: "N", name: "キャップ ∩ (添字を下げる)",
          math: "g_{ab}", meaning: "線を下向きに折り返す ∩ ＝ 添字を下げる（共変化）。"
        },
        delta: {
          glyph: ["│", "●", "│"], token: "=", name: "クロネッカー δ (恒等線)",
          math: "δ^a_b", meaning: "上下に真っ直ぐ貫く1本の線＝恒等（クロネッカーのデルタ）。"
        },
        epsilon: {
          glyph: ["  ◹◺  ", " / ε \\ ", "╱──┬──╲", " │ │ │ "], token: "[E]",
          name: "レヴィ・チヴィタ ε", math: "ε_{abc…}",
          meaning: "完全反対称テンソル。三角形の図形で、脚の入れ替えで符号が変わる。"
        },
        nabla: {
          glyph: ["   │   ", " ╭───╮ ", "∇│ T │ ", " ╰───╯╲", "   │   ＼"], token: "(D X)",
          name: "共変微分 ∇ (囲む輪＝フープ)", math: "∇_e T",
          meaning: "オペランドを大きな輪(フープ)で囲む。輪から出る1本の余分な線が微分の添字 e。"
        },
        partial: {
          glyph: ["  │  ", " ╭∂╮ ", " ╰─╯╲", "  │  ＼"], token: "(d X)",
          name: "偏微分 ∂", math: "∂_e f",
          meaning: "輪に ∂ を入れた偏微分。輪から出る1本が微分の添字。数値は有限差分で計算。"
        },
        lie: {
          glyph: ["   │   ", " ╭───╮ ", "£│ T │ ", " ╰───╯ ", "   │   "], token: "(L X)",
          name: "リー微分 £", math: "£_ξ T",
          meaning: "ベクトル場 ξ に沿うリー微分。輪に £ を付す（記号のみ）。"
        },
        integral: {
          glyph: ["⌠  │   ", "⎮ ┌┴┐ dμ", "⌡ │T│  ", "  └┬┘  "], token: "(I X dμ)",
          name: "積分 ∫ … dμ", math: "∫ T dμ",
          meaning: "オペランドを積分記号で囲み、測度 dμ の添字を単位測度で総和（縮約的に積む）。"
        },
        symmetrize: {
          glyph: [" │ │ │ ", "━━━━━━━", "┌─────┐", "│  T  │", "└─────┘"], token: "S{...}",
          name: "対称化 (対称化バー)", math: "T_{(ab)}",
          meaning: "線束を横切る真っ直ぐな太いバー＝添字の対称化。"
        },
        antisymmetrize: {
          glyph: [" │ │ │ ", "≈≈≈≈≈≈≈", "┌─────┐", "│  T  │", "└─────┘"], token: "A{...}",
          name: "反対称化 (反対称化バー)", math: "T_{[ab]}",
          meaning: "線束を横切る波線のバー＝添字の反対称化。"
        },
        swap: {
          glyph: [" ╲ ╱ ", "  ╳   = −  ‖", " ╱ ╲ "], token: "X",
          name: "交差＝反対称 (line swap)", math: "T_{[ab]}: ⤬ = −‖",
          meaning: "2本の線を交差させる＝添字の入れ替え。反対称な対象では 交差 = −(平行) 。"
        },
        riemann: {
          glyph: [" │   │ ", "━┷━━━┷━", "┌─────┐", "│  R  │", "└─────┘", "━┯━━━┯━", " │   │ "],
          token: "[R]", name: "リーマン曲率 R", math: "R_{abc}{}^{d}",
          meaning: "曲率テンソル。反対称な添字対を持つ図形（対にバー）。ビアンキ恒等式に現れる。"
        },
        torsion: {
          glyph: ["  │  ", " /T\\ ", "╱─┬─╲", "━┷━┷━", " │ │ "], token: "[Tor]",
          name: "捩率 (torsion) T", math: "T_{ab}{}^{c}",
          meaning: "下2添字が反対称な三角形テンソル。∇_a∇_b − ∇_b∇_a に現れる。"
        }
      }.freeze

      module_function

      # Attach the faithful SVG to each glyph (used by the web app).
      def glyphs
        GLYPHS.each_with_object({}) do |(key, g), h|
          h[key] = g.merge(svg: GlyphSVG.for(key))
        end
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
