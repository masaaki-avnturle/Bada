# frozen_string_literal: true

module Bada
  # Shannon entropy and tokenization.
  #
  # This is the "Shannon formula" half of the system:  H = - sum p log2 p.
  # The manifold module then turns H into a global-partial-integral-manifold
  # entropy *invariant*.
  module Entropy
    module_function

    # Tokenizer for mixed Japanese / English / math text. ASCII words stay
    # grouped; each CJK character is its own token (Japanese has no spaces, so
    # per-character tokens give a meaningful Shannon distribution).
    TOKEN_RE = /[A-Za-z0-9_]+|[一-鿿぀-ゟ゠-ヿ]/.freeze

    def tokenize(text)
      s = text.to_s
      s = s.encode("UTF-8", invalid: :replace, undef: :replace, replace: "") unless s.encoding == Encoding::UTF_8
      s.scan(TOKEN_RE)
    end

    # Shannon entropy (bits) of a token list, using in-list relative frequency.
    def shannon(tokens)
      return 0.0 if tokens.nil? || tokens.empty?
      freq = Hash.new(0)
      tokens.each { |t| freq[t] += 1 }
      total = tokens.length.to_f
      h = 0.0
      freq.each_value do |v|
        p = v / total
        h -= p * Math.log2(p)
      end
      h
    end

    # Entropy directly from a string.
    def of(text)
      shannon(tokenize(text))
    end

    # Probability distribution (sorted high->low) over tokens — used as the
    # measure carried onto the manifold.
    def distribution(tokens)
      return [] if tokens.nil? || tokens.empty?
      freq = Hash.new(0)
      tokens.each { |t| freq[t] += 1 }
      total = tokens.length.to_f
      freq.map { |tok, c| [tok, c / total] }.sort_by { |(_, p)| -p }
    end

    # Per-token (normalized) entropy in [0,1]: H / log2(vocab).
    def normalized(tokens)
      return 0.0 if tokens.nil? || tokens.empty?
      vocab = tokens.uniq.length
      return 0.0 if vocab <= 1
      shannon(tokens) / Math.log2(vocab)
    end

    # Cross-entropy of an observed token list against a reference distribution
    # (a Hash token => probability). Used by the generator to steer output.
    def cross_entropy(tokens, ref)
      return 0.0 if tokens.nil? || tokens.empty?
      eps = 1e-12
      total = tokens.length.to_f
      h = 0.0
      counts = Hash.new(0)
      tokens.each { |t| counts[t] += 1 }
      counts.each do |t, c|
        p = c / total
        q = ref.fetch(t, eps)
        h -= p * Math.log2(q)
      end
      h
    end
  end
end
