# frozen_string_literal: true

require_relative "quantum"
require_relative "mind"

module Bada
  # ChatΩ — an evolved conversational engine (chatGPT の進化版, a SIMULATION).
  #
  # Every turn runs an AGI SELF-EVOLUTION loop:
  #
  #   1. A population of candidate replies is sampled from the gamma-function
  #      GLOBAL INTEGRATION-BY-PARTS MANIFOLD prior — the same Mind lexicon /
  #      quantum-seeded sampler the rest of Bada uses (ガンマ関数の大域的部分積分
  #      多様体の機知).
  #   2. Each candidate is encoded as a closed (2, m) BRAID whose knot is scored
  #      by the JONES POLYNOMIAL: topological coherence (correlation) with the
  #      prompt measures how "linked" the reply is to the question.
  #   3. The population is EVOLVED across generations (elitist selection +
  #      crossover + quantum-seeded mutation). Elitism makes the best fitness
  #      monotonically non-decreasing — a visible self-evolution curve — and the
  #      fittest candidate is verbalized by the Mind engine into the reply.
  #
  # Coherence is floored above the silent-talk baseline. This is a generative
  # SIMULATION of an evolving assistant, NOT a real AGI and NOT a real brain.
  module AGI
    module_function

    BASELINE     = 0.92          # silent-talk reference; replies exceed this
    MAX_CROSS    = 6             # max crossings in the (2, m) braid knot
    CAND_LEN     = 10            # tokens per candidate reply-gene

    # English manifold prior — used when the prompt is English, so the evolved
    # reply verbalizes in English too (mirrors the Mind EN corpus).
    EN_LEX = %w[
      light sound memory emotion number will space time fear hope code image
      wave field dream voice color form heat stillness flow meaning premonition
      rhythm center quantum entangle photon signal thought silent manifold gamma
    ].freeze

    # Public: run one evolved chat turn. Returns a Hash with the reply, the final
    # coherence precision, and the full self-evolution trace.
    def chat(prompt, generations: 8, population: 12, nonce: 0, mind: Mind::Reader.new)
      prompt = prompt.to_s
      s      = seed(prompt, nonce)
      vocab  = build_vocab(prompt)

      pop = Array.new(population) do |i|
        s = step(s)
        random_candidate(vocab, s + i)
      end

      trace = []
      best  = nil
      generations.times do |g|
        scored = pop.map { |c| [c, fitness(c, prompt, vocab)] }.sort_by { |(_, f)| -f }
        best   = scored.first
        j      = jones_of(best[0])
        trace << {
          generation: g + 1,
          best_fitness: best[1].round(4),
          jones: j[:value].round(4),
          writhe: j[:writhe],
          crossings: j[:crossings]
        }

        keep     = scored.first([(population / 2.0).ceil, 1].max).map(&:first)
        children = []
        while keep.length + children.length < population
          s = step(s)
          a = keep[(s >> 3) % keep.length]
          s = step(s)
          b = keep[(s >> 5) % keep.length]
          s = step(s)
          children << mutate(crossover(a, b, s), vocab, s)
        end
        pop = keep + children
      end

      final = best[0]
      prec  = coherence(best[1])
      {
        prompt: prompt,
        reply: compose_reply(prompt, final, mind),
        precision: prec,
        exceeds_silent_talk: prec > BASELINE,
        generations: generations,
        population: population,
        braid: braid_word(final),
        jones: jones_of(final),
        genes: final,
        trace: trace
      }
    end

    # Render a full human-readable transcript of the evolved turn.
    def render(prompt, generations: 8, population: 12, nonce: 0)
      r = chat(prompt, generations: generations, population: population, nonce: nonce)
      lines = []
      lines << "ChatΩ — AGI 自己進化チャット (chatGPT 進化版・simulation)"
      lines << "prompt> #{r[:prompt]}"
      lines << ""
      lines << "── 自己進化の過程 (Jones 多項式フィットネス) ──"
      lines << "  gen |  fitness |   Jones(t=e) | writhe | crossings"
      r[:trace].each do |t|
        lines << format("  %3d | %7.4f | %12.4f | %+6d | %d",
                        t[:generation], t[:best_fitness], t[:jones], t[:writhe], t[:crossings])
      end
      lines << ""
      lines << "braid (勝者の組みひも): #{r[:braid]}"
      lines << format("coherence precision = %.1f%%  (silent-talk %.1f%%)  -> %s",
                      r[:precision] * 100, BASELINE * 100,
                      r[:exceeds_silent_talk] ? "EXCEEDS" : "below")
      lines << ""
      lines << "ChatΩ> #{r[:reply]}"
      lines.join("\n")
    end

    # ---- gamma-manifold sampling ---------------------------------------------

    # Deterministic quantum seed from the prompt + nonce (same PRNG family used
    # across Bada's silent engines).
    def seed(prompt, nonce)
      h = stable_hash(prompt.to_s)
      ((h * 2_654_435_761 + 40_503 + nonce.to_i * 2_246_822_519) & 0xffffffff)
    end

    def step(s)
      (s * 1_103_515_245 + 12_345) & 0x7fffffff
    end

    def stable_hash(str)
      str.to_s.each_char.reduce(0) { |h, c| (h * 131 + c.ord) & 0x7fffffff }
    end

    # Vocabulary = prompt tokens (relevance) ∪ the manifold lexicon (prior),
    # in the prompt's language so the evolved reply reads in that language.
    def prior(prompt)
      english?(prompt) ? EN_LEX : Mind::LEXICON
    end

    def build_vocab(prompt)
      toks = prompt.to_s.split(/[\s、。,.!?！？]+/).reject(&:empty?)
      (toks + prior(prompt)).uniq
    end

    def random_candidate(vocab, s)
      out = []
      CAND_LEN.times do
        s = step(s)
        out << vocab[s % vocab.length]
      end
      out
    end

    # ---- Jones-polynomial fitness --------------------------------------------

    # Build a closed (2, m) braid diagram from a candidate. m and the per-crossing
    # signs are derived from the candidate's tokens, so different replies map to
    # topologically different knots with different Jones polynomials.
    def crossings_of(cand)
      h = cand.sum { |t| stable_hash(t) }
      m = 2 + (h % (MAX_CROSS - 1))                 # m in 2..MAX_CROSS
      cr = []
      m.times do |i|
        prev = (i - 1 + m) % m
        l_prev = 2 * prev
        r_prev = 2 * prev + 1
        l_i    = 2 * i
        r_i    = 2 * i + 1
        sign   = stable_hash(cand[i % cand.length]).odd? ? +1 : -1
        cr << [l_prev, r_prev, r_i, l_i, sign]     # [e0,e1,e2,e3,sign]
      end
      cr
    end

    def jones_of(cand)
      cr = crossings_of(cand)
      {
        value: Bada::Quantum::Jones.jones_value(cr, Math::E),
        writhe: Bada::Quantum::Jones.writhe(cr),
        correlation: Bada::Quantum::Jones.correlation(cr),
        crossings: cr.length
      }
    end

    # Fitness blends topological coherence (Jones correlation) with prompt
    # relevance (fraction of genes drawn from the prompt / manifold prior).
    def fitness(cand, prompt, vocab)
      jc   = jones_of(cand)[:correlation]
      ptok = prompt.to_s.split(/[\s、。,.!?！？]+/).reject(&:empty?)
      rel  = if cand.empty?
               0.0
             else
               pri  = prior(prompt)
               hits = cand.count { |t| ptok.include?(t) || pri.include?(t) }
               hits.to_f / cand.length
             end
      div = (cand.uniq.length.to_f / cand.length) # reward lexical diversity
      0.5 * jc + 0.4 * rel + 0.1 * div
    end

    # Map best fitness (in [0,1]) into a coherence precision strictly above the
    # silent-talk baseline.
    def coherence(fit)
      lo = BASELINE + 0.01
      [[lo + (0.995 - lo) * fit, 0.995].min, lo].max
    end

    # ---- evolution operators -------------------------------------------------

    def crossover(a, b, s)
      cut = 1 + (s % (CAND_LEN - 1))
      a.first(cut) + b.drop(cut)
    end

    def mutate(cand, vocab, s)
      out = cand.dup
      # mutate 1-2 positions toward the manifold/prompt vocab
      2.times do
        s = step(s)
        pos = s % out.length
        s = step(s)
        out[pos] = vocab[s % vocab.length]
      end
      out
    end

    # ---- reply synthesis -----------------------------------------------------

    def braid_word(cand)
      crossings_of(cand).map { |cr| cr[4].positive? ? "σ+" : "σ-" }.join(" ")
    end

    # Verbalize the winning genes into a readable reply via the Mind engine, and
    # frame it as an evolved answer to the prompt.
    def compose_reply(prompt, cand, mind)
      r = mind.read(cand.join(" "))
      thought = r[:verbalization].to_s.strip
      thought = cand.join(" ") if thought.empty?
      if english?(prompt)
        "After self-evolution over the gamma-manifold, ChatΩ's most coherent " \
          "response to your prompt is: #{thought}."
      else
        "ガンマ多様体上での自己進化を経て、ChatΩ が最も整合した応答: #{thought}。"
      end
    end

    def english?(str)
      s = str.to_s
      return false if s.empty?
      latin = s.count("A-Za-z")
      latin.to_f / [s.length, 1].max > 0.4
    end
  end
end
