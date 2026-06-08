# frozen_string_literal: true

require_relative "entropy"
require_relative "manifold"
require_relative "tuplespace"

module Bada
  # Knowledge ingestion: turn reports (and web snippets) into a measured corpus.
  #
  # Ports extract_sections.py + entropy_model.py into Ruby: split text into
  # sentences, tag math, compute Shannon entropy AND the global partial integral
  # manifold invariant for each sentence, and load them into a TupleSpace so the
  # QA / generation engines can retrieve by keyword, entropy, or invariant.
  class Knowledge
    Sentence = Struct.new(:id, :para, :text, :math, :tokens, :entropy, :invariant, :source,
                          keyword_init: true)

    MATH_RE = %r{\\\((.+?)\\\)|\$(.+?)\$|\\\[(.+?)\\\]|[∫∬∮∇βζΓπ⊕⊗√∂∞≅⊃⊂]}m.freeze
    SENT_SPLIT = /(?<=。|\.|\?|!|！)\s*/.freeze

    def initialize
      @sentences = []
    end

    attr_reader :sentences

    # Ingest a raw text blob from a named source (a report file, web page, ...).
    def ingest(text, source: "report")
      text = text.to_s.gsub("\r\n", "\n").tr("\r", "\n")
      paras = text.split(/\n\s*\n/).map(&:strip).reject(&:empty?)
      paras.each_with_index do |p, pi|
        p.split(SENT_SPLIT).map(&:strip).reject(&:empty?).each do |s|
          tokens = Entropy.tokenize(s)
          next if tokens.empty?
          @sentences << Sentence.new(
            id: @sentences.length,
            para: pi,
            text: s,
            math: !MATH_RE.match(s).nil?,
            tokens: tokens,
            entropy: Entropy.shannon(tokens),
            invariant: Manifold.invariant(tokens)[:invariant],
            source: source
          )
        end
      end
      self
    end

    def ingest_file(path, source: nil)
      ingest(File.read(path, encoding: "UTF-8"), source: source || File.basename(path))
    end

    # Build a TupleSpace (Omega::DATABASE) from the ingested sentences.
    def to_tuplespace
      db = TupleSpace.new
      @sentences.each do |s|
        db.push(s.text, key: "Ω::#{s.source}##{s.id}",
                        tags: { para: s.para, math: s.math, source: s.source })
      end
      db
    end

    # Retrieval helpers used by the QA engine -------------------------------

    def find_by_keywords(keywords, top: 5)
      kws = keywords.map(&:downcase)
      @sentences.map { |s|
        txt = s.text.downcase
        score = kws.sum { |k| txt.scan(k).length }
        [score, s]
      }.select { |(sc, _)| sc.positive? }
       .sort_by { |(sc, _)| -sc }
       .first(top).map { |(_, s)| s }
    end

    def closest_entropy(target, top: 5)
      @sentences.sort_by { |s| (s.entropy - target).abs }.first(top)
    end

    def closest_invariant(target, top: 5)
      @sentences.sort_by { |s| (s.invariant - target).abs }.first(top)
    end

    def lowest_entropy(top: 5)
      @sentences.sort_by(&:entropy).first(top)
    end

    def highest_entropy(top: 5)
      @sentences.sort_by { |s| -s.entropy }.first(top)
    end

    def median_entropy
      return 0.0 if @sentences.empty?
      hs = @sentences.map(&:entropy).sort
      hs[hs.length / 2]
    end

    def math_sentences
      @sentences.select(&:math)
    end

    def empty?
      @sentences.empty?
    end
  end
end
