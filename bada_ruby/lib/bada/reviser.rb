# frozen_string_literal: true

require_relative "tuplespace"

module Bada
  # The Reviser — @reviser as a grammar-extension transaction.
  #
  # From "Reviser-Extensible Grammars": Bada's @reviser is generalised from a
  # value-level learning loop into a mechanism that extends the language's own
  # grammar *at the level of committed facts*. A production rule is itself a
  # ledger fact:
  #
  #   rule := [ "rule", name, head, pattern, denotation ]
  #
  # where head ∈ {stmt, expr, postfix}, pattern is a token template with holes
  # (_1, _2, …), and denotation is an ordinary Bada expression — typically an
  # engine call. A @reviser block is a transaction that *appends* rules to the
  # rule ledger Omega::DATABASE[grammar]; the parser then consults that ledger.
  #
  # Two disciplines keep this sound and faithful to the engine:
  #   * Monotonicity — rules are appended, never overwritten. A later rule may
  #     shadow an earlier one by higher priority, but the earlier fact remains,
  #     so the grammar's history is auditable (append-only, like evidence).
  #   * Scope — a rule applies only to input that follows its committing
  #     reviser in program order. Syntax a program has not yet "learned" parses
  #     as before.
  module Reviser
    HEADS = %i[stmt expr postfix].freeze

    Rule = Struct.new(:name, :head, :pattern, :denotation, :priority, :seq, keyword_init: true) do
      # The denotation's holes (_1, _2, …) filled from captured fragments.
      def elaborate(captures)
        out = denotation.dup
        captures.each_with_index do |cap, i|
          out = out.gsub("_#{i + 1}", cap.to_s)
        end
        out
      end

      def to_fact
        ["rule", name, head.to_s, pattern, denotation]
      end
    end

    # Omega::DATABASE[grammar] — the append-only rule ledger.
    class RuleLedger
      attr_reader :db

      def initialize(db: TupleSpace.new)
        @db = db
        @rules = []
        @seq = 0
      end

      # Append a rule as a committed fact. Never mutates; later commits shadow
      # earlier ones only by priority at lookup time.
      def commit(name:, head:, pattern:, denotation:, priority: nil)
        head = head.to_sym
        raise ArgumentError, "unknown head #{head}" unless HEADS.include?(head)
        @seq += 1
        rule = Rule.new(
          name: name, head: head, pattern: pattern, denotation: denotation,
          priority: priority || @seq, seq: @seq
        )
        @rules << rule
        @db.push("rule #{name} : #{head} #{pattern.inspect} => #{denotation}",
                 key: "Ω::grammar##{@seq}",
                 tags: { kind: :grammar_rule, head: head, name: name })
        rule
      end

      # Rules for a head, in lookup order: highest priority first (latest commit
      # wins), then ledger order. Only rules committed at or before `up_to_seq`
      # are in scope (program-order scoping).
      def rules_for(head, up_to_seq: Float::INFINITY)
        head = head.to_sym
        @rules.select { |r| r.head == head && r.seq <= up_to_seq }
              .sort_by { |r| [-r.priority, r.seq] }
      end

      def all
        @rules.dup
      end

      def size
        @rules.length
      end

      def current_seq
        @seq
      end
    end

    module_function

    # Parse the body of a @reviser : grammar { … } block into rules and commit
    # them to the ledger. Each non-empty line has the form:
    #
    #   rule "NAME" HEAD [ TOK TOK … ] => DENOTATION
    #
    # where a TOK is either a quoted literal ('H', '(') or a hole keyword
    # (expr). Returns the committed Rule objects.
    RULE_RE = /\A
      rule\s+"(?<name>[^"]+)"\s+
      (?<head>stmt|expr|postfix)\s+
      \[(?<pattern>[^\]]*)\]\s*
      =>\s*(?<den>.+?)\s*
    \z/x.freeze

    def parse_and_commit(body, ledger)
      committed = []
      body.each_line do |raw|
        line = raw.strip.sub(/#.*\z/, "").strip
        next if line.empty?
        m = RULE_RE.match(line)
        raise "reviser: malformed rule: #{line.inspect}" unless m

        pattern = tokenize_pattern(m[:pattern])
        committed << ledger.commit(
          name: m[:name], head: m[:head].to_sym,
          pattern: pattern, denotation: m[:den]
        )
      end
      committed
    end

    # A pattern token is a quoted literal { lit: "H" } (single or double quotes)
    # or a hole { hole: :expr }.
    def tokenize_pattern(text)
      tokens = []
      text.scan(/'([^']*)'|"([^"]*)"|(\w+)/) do |sq, dq, word|
        tokens << if sq || dq
                    { lit: sq || dq }
                  else
                    { hole: word.to_sym }
                  end
      end
      tokens
    end
  end
end
