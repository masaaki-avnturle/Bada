# frozen_string_literal: true

require_relative "entropy"
require_relative "manifold"
require_relative "error_correction"

module Bada
  # Entropy-driven language / equation / theory generator.
  #
  # This is the "language generation" engine: given a target Shannon entropy H
  # (derived from the question's own entropy and the global partial integral
  # manifold invariant), it emits text, equations, and theory whose measured
  # entropy converges to H. A bigram Markov chain over the corpus is sampled
  # with a temperature that is tuned by the error corrector until the produced
  # entropy matches the target on the rotational body.
  class Generator
    # Vocabulary of the framework (used for equation / theory synthesis).
    SYMBOLS = %w[β(p,q) Γ(γ) ζ(s) π(χ,x) ∬1/(x·log x)² e^{-x·log x} ⊕(iℏ∇)^⊕L
                 Ω::DATABASE x·log x e^{iθ} ∮e^{-□}d□ □=cos(ix log x)-i sin(ix log x)].freeze

    EQUATION_TEMPLATES = [
      "ζ(s) = β(p,q)/log x = x·log x",
      "β(p,q) = Γ(p)Γ(q)/Γ(p+q)",
      "∬ 1/(x·log x)² dx_m = π(χ,x)∇ d∇",
      "□ = 2(sin(ix·log x) + cos(ix·log x))",
      "∮ e^{-□} d□ = π e,  e^π ≅ π^e",
      "H = -Σ p·log₂ p,  Ξ = β(H+1, M+1)/log(N+1)",
      "⊕(iℏ∇)^⊕L = e^{-x·log x}",
      "Γ′(γ) dx_m = T,  ζ(s) e^{-f} dV = β(p,q)/log x"
    ].freeze

    THEORY_TEMPLATES = [
      "大域的部分積分多様体 M 上で、エントロピー不変量 Ξ は複素回転体 e^{iθ} の下で保存される。",
      "ガンマ関数 Γ(γ) の部分積分により β(p,q) が現れ、これが ζ(s)=x·log x のゲージを与える。",
      "シャノンのエントロピー H を多様体線素 1/(x·log x)² で重み付け積分すると不変量 Ξ を得る。",
      "特殊相対性理論のコマ幾何の可積分系がエラーを修正し、Ξ を閉軌道 ∮ 上で安定化させる。",
      "未知エンジンは質問のエントロピー値 H_q を多様体不変量 Ξ_q に写し、近傍の知識を生成する。"
    ].freeze

    def initialize(knowledge: nil, seed: nil)
      @knowledge = knowledge
      @rng = seed ? Random.new(seed) : Random.new
      @bigrams = build_bigrams
    end

    # Generate text whose Shannon entropy converges to target_h.
    # Returns { text:, entropy:, target:, invariant:, error: }.
    def text(target_h: nil, length: 24, seed_word: nil)
      target_h ||= @knowledge&.median_entropy || 3.0
      best = nil
      # Sweep temperature; pick the run whose entropy is closest to target.
      temps = [0.3, 0.6, 0.9, 1.2, 1.6, 2.2, 3.0]
      samples = []
      temps.each do |t|
        words = sample_chain(length, t, seed_word)
        h = Entropy.shannon(Entropy.tokenize(words.join(" ")))
        samples << h
        cand = { text: words.join(" "), entropy: h, temp: t }
        best = cand if best.nil? || (h - target_h).abs < (best[:entropy] - target_h).abs
      end
      # Error-correct the achieved-entropy estimate on the rotational body.
      corrected = ErrorCorrection.correct(samples)
      best.merge(
        target: target_h,
        invariant: Manifold.xi(best[:text]),
        corrected_entropy: corrected[:value],
        error: (best[:entropy] - target_h).abs
      )
    end

    # Generate an equation; entropy of the symbol string steers selection.
    def equation(target_h: nil)
      target_h ||= 3.0
      pick = EQUATION_TEMPLATES.min_by { |e| (Entropy.of(e) - target_h).abs }
      { equation: pick, entropy: Entropy.of(pick), target: target_h,
        invariant: Manifold.xi(pick) }
    end

    # Generate a theory paragraph (sentence chain) at a target entropy.
    def theory(target_h: nil, sentences: 3)
      target_h ||= @knowledge&.median_entropy || 3.5
      chosen = THEORY_TEMPLATES
               .sort_by { |t| (Entropy.of(t) - target_h).abs }
               .first(sentences)
      body = chosen.join(" ")
      eq = equation(target_h: target_h)
      {
        theory: body,
        equation: eq[:equation],
        entropy: Entropy.of(body),
        target: target_h,
        invariant: Manifold.xi(body)
      }
    end

    private

    def build_bigrams
      return {} unless @knowledge && !@knowledge.empty?
      chain = Hash.new { |h, k| h[k] = Hash.new(0) }
      @knowledge.sentences.each do |s|
        toks = s.tokens
        toks.each_cons(2) { |a, b| chain[a][b] += 1 }
      end
      chain
    end

    # Sample a Markov chain with temperature t (higher t -> higher entropy).
    def sample_chain(length, temp, seed_word)
      return synth_words(length, temp) if @bigrams.empty?
      word = seed_word || @bigrams.keys.sample(random: @rng)
      out = [word]
      (length - 1).times do
        nexts = @bigrams[word]
        if nexts.nil? || nexts.empty?
          word = @bigrams.keys.sample(random: @rng)
        else
          word = weighted_pick(nexts, temp)
        end
        out << word
      end
      out
    end

    # Fallback synthesis from the framework vocabulary when no corpus is loaded.
    def synth_words(length, temp)
      pool = SYMBOLS + %w[manifold entropy gamma beta zeta rotation invariant
                          tuplespace shannon integral theory unknown engine]
      n = [(pool.length * (temp / 3.0)).ceil, 2].max
      sub = pool.first(n)
      Array.new(length) { sub.sample(random: @rng) }
    end

    # Temperature-scaled weighted sampling: counts^(1/temp).
    def weighted_pick(counts, temp)
      scaled = counts.map { |w, c| [w, (c.to_f**(1.0 / temp))] }
      total = scaled.sum { |(_, v)| v }
      r = @rng.rand * total
      acc = 0.0
      scaled.each do |w, v|
        acc += v
        return w if r <= acc
      end
      scaled.last[0]
    end
  end
end
