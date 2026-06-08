# frozen_string_literal: true

require_relative "manifold"

module Bada
  # Omega::DATABASE — the Akashic Record / TupleSpace.
  #
  # From "Library of akashic recode" and the Bada1 report:
  #
  #   Omega::DATABASE[tuplespace] { Z ⊃ C ⊕ ∇R+ ... }
  #   import Omega::Tuplespace < DATABASE { ... w <- value ... w.pop => tuplespace.value }
  #
  # It is a content-addressable store of "tuples" (manifold points). Each entry
  # carries its text, its manifold entropy invariant, and arbitrary tags, so the
  # space can be searched by keyword *or* by entropy / invariant proximity.
  class TupleSpace
    Tuple = Struct.new(:key, :text, :stats, :tags, keyword_init: true)

    def initialize
      @store = []
    end

    attr_reader :store

    # push(key, text)  — register a manifold point (Akashic write).
    def push(text, key: nil, tags: {})
      stats = Manifold.invariant(text)
      key ||= "Ω::#{@store.length}"
      tuple = Tuple.new(key: key, text: text, stats: stats, tags: tags)
      @store << tuple
      tuple
    end
    alias add push

    def pop
      @store.pop
    end

    def size
      @store.length
    end

    # Find tuples whose text contains a substring (the report's w.scan).
    def find(&block)
      @store.select(&block)
    end

    def scan(substr)
      @store.select { |t| t.text.include?(substr) }
    end

    # Search by keyword overlap, returning [score, tuple] best first.
    def search(query, top: 5)
      qtokens = Entropy.tokenize(query.downcase)
      scored = @store.map do |t|
        ttoks = Entropy.tokenize(t.text.downcase)
        overlap = (qtokens & ttoks).length
        [overlap, t]
      end
      scored.select { |(s, _)| s.positive? }
            .sort_by { |(s, _)| -s }
            .first(top)
            .map { |(_, t)| t }
    end

    # Search by entropy invariant proximity — retrieve tuples whose global
    # partial integral manifold invariant is closest to a target Xi.
    def by_invariant(target_xi, top: 5)
      @store.sort_by { |t| (t.stats[:invariant] - target_xi).abs }.first(top)
    end

    # Search by Shannon entropy proximity.
    def by_entropy(target_h, top: 5)
      @store.sort_by { |t| (t.stats[:entropy] - target_h).abs }.first(top)
    end

    def each(&block)
      @store.each(&block)
    end
    include Enumerable
  end
end
