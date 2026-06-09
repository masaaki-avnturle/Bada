# frozen_string_literal: true

require_relative "thurston"
require_relative "catastrophe"
require_relative "millennium"
require_relative "generator"
require_relative "error_correction"

module Bada
  # InfoEngine — the information-generation function (Facade).
  #
  # Pipeline for a question:
  #   1. Thurston: place the question's Shannon entropy onto the Thurston–
  #      Perelman manifold (which model geometry, and its Perelman F-entropy).
  #   2. Catastrophe: load that information into a cusp potential; its stable
  #      equilibrium branches (separated by bifurcation/branch points) each get a
  #      target entropy. Every branch generates a distinct fragment — this is the
  #      "decomposition / branch-point" information generation.
  #   3. Millennium: decompose the question's theory across the seven Clay
  #      problems, all rooted in the gamma-function global partial integral
  #      manifold.
  #
  # The per-branch target entropies are error-corrected on the complex-rotation
  # integrable system before generation, so the branch set stays stable.
  class InfoEngine
    def initialize(knowledge: nil, seed: nil)
      @generator = Generator.new(knowledge: knowledge, seed: seed)
    end

    def generate(question, branch_length: 16)
      placement = Thurston.place_entropy(question)
      decomp = Catastrophe.decompose(question)
      millennium = Millennium.decompose_theory(question)

      # Stabilise branch targets on the rotational body, then generate per branch.
      targets = decomp[:branches].map { |b| b[:target_h] }
      corrected = ErrorCorrection.correct(targets) unless targets.empty?

      branches = decomp[:branches].map do |b|
        gen = @generator.text(target_h: b[:target_h], length: branch_length)
        {
          index: b[:index],
          equilibrium_x: b[:x],
          weight: b[:weight],
          target_entropy: b[:target_h],
          text: gen[:text],
          entropy: gen[:entropy]
        }
      end

      {
        question: question,
        placement: placement,
        catastrophe: {
          geometry: decomp[:geometry],
          controls: decomp[:controls],
          discriminant: decomp[:discriminant],
          on_bifurcation: decomp[:on_bifurcation],
          branch_count: decomp[:branch_count],
          stabilized_target: corrected && corrected[:value]
        },
        branches: branches,
        millennium: millennium
      }
    end

    # Human-readable rendering of an information-generation result.
    def render(question, branch_length: 16)
      r = generate(question, branch_length: branch_length)
      p = r[:placement]
      out = []
      out << "── 情報生成エンジン (Thurston–Perelman / Catastrophe / Millennium) ──"
      out << format("【サーストン・ペレルマン多様体】幾何=%s (曲率%.2f) · H=%.3f · Perelman F=%.4f · Ricci%s",
                    p[:geometry], p[:curvature], p[:entropy], p[:perelman_f],
                    p[:ricci_collapsed] ? "=有限時間特異点(崩壊)" : format("→%.3f", p[:ricci_final]))
      out << ""
      c = r[:catastrophe]
      out << format("【カタストロフィ分岐（情報分解の分岐点）】カスプ判別式=%.4f%s · 分岐数=%d",
                    c[:discriminant], c[:on_bifurcation] ? " (分岐点上!)" : "", c[:branch_count])
      r[:branches].each do |b|
        out << format("  分岐#%d (x=%.3f, 重み%.2f, 目標H=%.2f): %s",
                      b[:index], b[:equilibrium_x], b[:weight], b[:target_entropy], b[:text])
      end
      out << ""
      m = r[:millennium]
      out << "【ミレニアム7問への理論分解】起点: #{m[:origin]}"
      out << "  主分解先: #{m[:dominant]}"
      m[:decomposition].each { |d| out << "  - #{d[:theory]}" }
      out.join("\n")
    end
  end
end
