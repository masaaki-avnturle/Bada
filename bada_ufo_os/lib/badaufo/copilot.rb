# frozen_string_literal: true

module BadaUFO
  # ============================================================================
  # Copilot — 生成AI操縦士（UFOの機体知性）
  # ----------------------------------------------------------------------------
  # 量子コンピュータ上の生成AI操縦士。山口フレームワークの Bada::Generator
  # （エントロピー駆動の生成エンジン）を機体知性として用い、応答を
  # Ω::DATABASE（アカシックレコード / Bada::TupleSpace）へ記録する。
  #
  # bada_ruby が同梱されていれば本物の生成エンジンを、無ければ純 stdlib の
  # 小型エントロピー生成器をフォールバックとして使う（単体配布でも動作）。
  # ============================================================================
  class Copilot
    def initialize(seed: 42)
      @seed = seed
      @akashic = nil
      @generator = nil
      @entropy = nil
      @manifold = nil
      boot_engine
    end

    def engine_name
      @generator ? "Bada::Generator (量子生成AI)" : "MicroGen (stdlib fallback)"
    end

    # 質問に生成応答を返す。{ text:, entropy:, invariant: }。
    def respond(question, context: {})
      seed_word = pick_seed(question)
      if @generator
        h_q = @entropy ? @entropy.shannon(@entropy.tokenize(question)) : 3.0
        r = @generator.text(target_h: h_q, length: 18, seed_word: seed_word)
        text = flavor(r[:text], context)
        { text: text,
          entropy: r[:entropy],
          invariant: r[:invariant] || xi(text) }
      else
        text = flavor(micro_generate(question, seed_word), context)
        { text: text, entropy: micro_entropy(text), invariant: xi(text) }
      end
    end

    def akashic_push(text)
      if @akashic
        @akashic.push(text.to_s)
      else
        (@fallback_log ||= []) << text.to_s
      end
    end

    def akashic_search(query)
      if @akashic
        q = query.to_s
        res = @akashic.respond_to?(:scan) ? @akashic.scan(q) : nil
        return res.map { |t| t.is_a?(String) ? t : t.text } if res && !res.empty?
        collect = []
        @akashic.each { |t| collect << (t.is_a?(String) ? t : t.text) } if @akashic.respond_to?(:each)
        query.to_s.empty? ? collect : collect.select { |s| s.include?(query.to_s) }
      else
        log = @fallback_log || []
        query.to_s.empty? ? log : log.select { |s| s.include?(query.to_s) }
      end
    end

    private

    def boot_engine
      root = File.expand_path("../../..", __dir__)
      lib  = File.join(root, "bada_ruby", "lib")
      return unless File.directory?(lib)
      $LOAD_PATH.unshift(lib) unless $LOAD_PATH.include?(lib)
      require "bada/entropy"
      require "bada/manifold"
      require "bada/tuplespace"
      require "bada/knowledge"
      require "bada/generator"
      @entropy  = ::Bada::Entropy
      @manifold = ::Bada::Manifold
      @akashic  = ::Bada::TupleSpace.new
      knowledge = build_knowledge(root)
      @generator = ::Bada::Generator.new(knowledge: knowledge, seed: @seed)
    rescue LoadError, StandardError
      @generator = nil        # フォールバックへ
    end

    # 反重力コーパスを学習させて機体知性の語彙を作る。
    def build_knowledge(root)
      corpus = File.join(root, "bada_ruby", "corpus")
      texts = []
      if File.directory?(corpus)
        Dir[File.join(corpus, "*.txt")].sort.first(4).each do |f|
          texts << File.read(f) rescue nil
        end
      end
      texts << ufo_seed_corpus
      k = ::Bada::Knowledge.new rescue nil
      if k
        texts.compact.each { |t| k.ingest(t) rescue (k.learn(t) rescue nil) }
      end
      k
    end

    # 生成AIの基礎語彙（反重力・真空・補空間の理論文）。
    def ufo_seed_corpus
      <<~TXT
        反重力場は重力方程式の補空間に住むエネルギーである。無尽蔵の真空
        エネルギー体が機体を支える。特殊相対性理論の補空間 mc² 引く 二分の一 mv²
        が抽出可能なエネルギーを与える。ネイピア円上で x log x が回転し、
        コホモロジーの切断が反重力を生む。アカシックレコードに航跡を記録する。
        揚力比が一を超えると機体は上昇する。量子作用素が生成AIを駆動する。
      TXT
    end

    def pick_seed(question)
      toks = question.to_s.split(/[^\p{Word}]+/).reject(&:empty?)
      toks.max_by(&:length)
    end

    # 文脈（高度・揚力比）を応答に織り込む。
    def flavor(text, context)
      alt = context[:altitude]
      lr  = context[:lift_ratio]
      tail = []
      tail << format("高度%.0fm", alt) if alt && alt > 0
      tail << format("揚力比L=%.2f", lr) if lr
      base = text.to_s.strip
      base = "反重力回転を確認" if base.empty?
      tail.empty? ? base : "#{base}〔#{tail.join(' ')}〕"
    end

    def xi(text)
      return @manifold.xi(text) if @manifold
      # 簡易 Ξ: 正規化した文字エントロピー。
      micro_entropy(text) / 8.0
    end

    # ---- フォールバック生成器（bada_ruby 非同梱時） ----
    FALLBACK_VOCAB = %w[
      反重力 補空間 真空 エネルギー 揚力 多様体 コホモロジー 切断
      ネイピア円 量子作用素 アカシック 上昇 回転 無尽蔵 相対論 重力方程式
    ].freeze

    def micro_generate(question, seed_word)
      rng = Random.new(@seed ^ question.to_s.bytes.sum)
      n = 6 + rng.rand(6)
      words = []
      words << seed_word if seed_word
      n.times { words << FALLBACK_VOCAB[rng.rand(FALLBACK_VOCAB.length)] }
      words.join("・") + "を演算した"
    end

    def micro_entropy(text)
      chars = text.to_s.chars
      return 0.0 if chars.empty?
      freq = Hash.new(0)
      chars.each { |c| freq[c] += 1 }
      n = chars.length.to_f
      -freq.values.sum { |c| p = c / n; p * Math.log2(p) }
    end
  end
end
