# frozen_string_literal: true

require_relative "knowledge"
require_relative "entropy"

module Bada
  # Entropy-driven question answering over an ingested corpus.
  #
  # Ruby port of qa_engine.py, extended to retrieve by the global partial
  # integral manifold invariant as well as by Shannon entropy and keywords.
  class QAEngine
    def initialize(knowledge)
      @kb = knowledge
    end

    # Answer a single question; returns a String.
    def answer(question)
      q = question.to_s
      ql = q.downcase

      if q.include?("何ができる") || ql.include?("what can be done")
        cands = @kb.find_by_keywords(%w[method approach propose show result 結果 方法 手法 示す propose result])
        return format_list("このレポートから可能なこと（根拠付き）", cands) if cands.any?
        return "明確な methods/results の記述は見つかりませんでした。"
      end

      if q.include?("低エントロピー") || ql.include?("low-entropy")
        return format_entropy("低エントロピー文（要約的/繰り返しが多い）", @kb.lowest_entropy)
      end

      if q.include?("中程度") || ql.include?("medium-entropy")
        return format_entropy("中程度エントロピー文（説明的）", @kb.closest_entropy(@kb.median_entropy))
      end

      if q.include?("高エントロピー") || ql.include?("high-entropy")
        return format_entropy("高エントロピー文（式・新情報多）", @kb.highest_entropy)
      end

      # Manifold invariant target:  Xi=2.5
      if (m = q.match(/(?:Xi|Ξ|invariant|不変量)\s*=\s*([0-9]*\.?[0-9]+)/i))
        target = m[1].to_f
        return format_invariant("指定不変量 Ξ=#{format('%.3f', target)} に近い文", @kb.closest_invariant(target))
      end

      # Entropy target:  H=2.0
      if (m = q.match(/H\s*=\s*([0-9]*\.?[0-9]+)/))
        target = m[1].to_f
        return format_entropy("指定エントロピー H=#{format('%.3f', target)} に近い文", @kb.closest_entropy(target))
      end

      # Fallback: keyword retrieval.
      qtokens = Entropy.tokenize(q)
      cands = @kb.find_by_keywords(qtokens, top: 5)
      return format_list("関連する記述", cands) if cands.any?
      "該当する記述が見つかりませんでした。質問のキーワードを変えてください。"
    end

    private

    def format_list(title, sents)
      lines = ["#{title}:"]
      sents.first(5).each { |s| lines << "- #{trim(s.text)}" }
      lines.join("\n")
    end

    def format_entropy(title, sents)
      lines = ["#{title} 例:"]
      sents.each { |s| lines << format("- H=%.3f: %s", s.entropy, trim(s.text)) }
      lines.join("\n")
    end

    def format_invariant(title, sents)
      lines = ["#{title}:"]
      sents.each { |s| lines << format("- Ξ=%.3f (H=%.2f): %s", s.invariant, s.entropy, trim(s.text)) }
      lines.join("\n")
    end

    def trim(text, n = 300)
      t = text.gsub("\n", " ")
      t.length > n ? "#{t[0, n]}…" : t
    end
  end
end
