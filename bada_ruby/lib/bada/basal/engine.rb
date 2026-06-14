# frozen_string_literal: true

require_relative "factory"
require_relative "../manifold"
require_relative "../prover"

module Bada
  module Basal
    # BodyNeuralSystem — Facade over the basal-ganglia thermal network. It
    # selects one action from a set of candidates [item, salience], with the
    # gamma-manifold conductances and thermal annealing built in, and can learn
    # from reward.
    class BodyNeuralSystem
      attr_reader :circuit

      def initialize(channels:, gate: :boltzmann, seed: nil)
        @circuit = CircuitFactory.build(channels, gate: gate, seed: seed)
      end

      # candidates: Array<[item, salience(Float)]>. Returns the selected item.
      def select(candidates)
        sal = candidates.map { |(_, s)| s.to_f }
        idx = @circuit.select(sal)
        candidates[idx][0]
      end

      def distribution(candidates)
        @circuit.distribution(candidates.map { |(_, s)| s.to_f })
      end

      def reward(r) = @circuit.reward(r)
    end

    # AprioriEngine — the Ruby LLM "unknown a-priori engine" built on the
    # in-body neural system: it imagines candidate conjectures (Bada::Prover),
    # lets the basal ganglia *select which to pursue* by salience (manifold
    # invariant + entropy), proves the selected one soundly, and learns from the
    # outcome (a proof = reward, an open problem = neutral/negative).
    class AprioriEngine
      def initialize(seed: nil)
        @prover = Bada::Prover::Engine.new
        @seed = seed
      end

      def deliberate(question, count: 5, rounds: nil)
        conjectures = @prover.imagine(question, count: count)
        n = conjectures.length
        bg = BodyNeuralSystem.new(channels: n, gate: :boltzmann, seed: @seed)
        base = conjectures.map { |c| salience(c, question) }
        rounds ||= n
        log = []
        chosen = []
        rounds.times do
          break if chosen.length >= n
          # fixed-width salience; already-chosen channels are masked (no Go drive)
          sal = base.each_index.map { |i| chosen.include?(i) ? 0.0 : base[i] }
          idx = bg.circuit.select(sal)
          idx = (0...n).reject { |i| chosen.include?(i) }.max_by { |i| base[i] } if chosen.include?(idx)
          c = conjectures[idx]
          proof = c.prove
          reward = case proof.status
                   when :proved then 1.0
                   when :disproved then 0.5 # still informative
                   else -0.2                # open: no closure
                   end
          bg.reward(reward)
          log << { conjecture: c, proof: proof, reward: reward }
          chosen << idx
        end
        { question: question, order: log, system: bg }
      end

      # Salience of a conjecture = manifold-invariant proximity to the question
      # boosted for soundly-decidable kinds (the basal ganglia prefers closure).
      def salience(conjecture, question)
        xi_q = Bada::Manifold.xi(question)
        xi_c = Bada::Manifold.xi(conjecture.statement)
        prox = 1.0 / (1.0 + (xi_q - xi_c).abs)
        bonus = { sum_identity: 0.6, divisibility: 0.6, open: 0.1 }[conjecture.kind] || 0.3
        prox + bonus
      end

      def render(question, count: 5)
        r = deliberate(question, count: count)
        out = []
        out << "── 未知事前エンジン (体内神経システム / 大脳基底核ゲーティング) ──"
        out << "質問から命題を想像し、大脳基底核の熱ネットワークが取り組む順序を選択する。"
        out << ""
        r[:order].each_with_index do |e, k|
          c = e[:conjecture]; p = e[:proof]
          out << "選択#{k + 1}: 【#{c.title}】  → #{p.symbol}  (報酬 #{e[:reward]})"
          out << "  主張: #{c.statement}"
          out << "  手法: #{p.method}"
        end
        out << ""
        out << format("ドーパミン水準（学習後）: %.3f", r[:system].circuit.dopamine.level)
        out << "※ 証明は健全な手法のみ。未解決は経験的証拠であり証明ではない。"
        out.join("\n")
      end
    end
  end
end
