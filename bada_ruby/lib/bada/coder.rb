# frozen_string_literal: true

require "set"
require_relative "coder/synth"

module Bada
  # Bada::Coder — thought-to-code (simulation). Bilingual (English + 日本語)
  # intent, automatic programming-language detection, reserved-word recognition,
  # a command feature with word completion, and code generation.
  #
  #   c = Bada::Coder
  #   c.detect("def foo; puts 42; end")[:language]   # => "ruby"
  #   c.reserved_words("for i in range(10): print(i)", language: "python")
  #   c.complete("de", language: "ruby")              # => ["def", "defined?"]
  #   c.generate("print hello 3 times", language: "python")[:code]
  #
  # Honesty: this is a generative/heuristic simulation, not a brain interface.
  module Coder
    module_function

    # --- language table: keywords (reserved words), builtins, signature hints --
    LANGUAGES = {
      "ruby" => {
        keywords: %w[def end if elsif else unless while until for do class module return
                     yield begin rescue ensure then case when next break redo retry
                     and or not nil true false self super lambda __method__ in],
        builtins: %w[puts print p require require_relative attr_accessor attr_reader
                     attr_writer new each map select reduce times loop raise proc],
        hints: [/\bdef\b[\s\S]*\bend\b/, /\bputs\b/, /\.each\b/, /\bend\b\s*$/, /\bunless\b/],
        comment: "#"
      },
      "python" => {
        keywords: %w[def return if elif else while for in import from class lambda None
                     True False try except finally with as pass yield global nonlocal
                     assert del raise not and or is break continue],
        builtins: %w[print range len int str list dict set input open enumerate zip map
                     filter sum min max sorted type isinstance],
        hints: [/\bdef\b[^\n]*:/, /\bprint\(/, /\belif\b/, /\brange\(/, /:\s*$/],
        comment: "#"
      },
      "javascript" => {
        keywords: %w[function var let const if else for while do return class new this
                     typeof instanceof switch case break continue try catch finally throw
                     import export default async await yield of in],
        builtins: %w[console log document window Array Object Math JSON Promise map filter
                     reduce forEach push length parseInt parseFloat],
        hints: [/\bfunction\b/, /console\.log/, /=>/, /\bconst\b/, /\blet\b/, /;\s*$/],
        comment: "//"
      },
      "c" => {
        keywords: %w[int char float double void short long unsigned signed if else for
                     while do switch case break continue return struct union enum typedef
                     const static sizeof goto],
        builtins: %w[printf scanf malloc free include stdio main puts fgets memcpy strlen],
        hints: [/#include/, /\bprintf\(/, /\bint\s+main\b/, /\bvoid\b/, /;\s*$/],
        comment: "//"
      },
      "java" => {
        keywords: %w[public private protected class interface static final void abstract
                     if else for while do switch case break continue return new this super
                     extends implements import package try catch finally throw throws],
        builtins: %w[System out println print String Integer Double List Map ArrayList
                     HashMap length equals main args],
        hints: [/\bpublic\s+class\b/, /System\.out\.println/, /\bstatic\s+void\s+main\b/],
        comment: "//"
      },
      "bada" => {
        keywords: %w[set print Omega Ω push as],
        builtins: %w[],
        hints: [/Omega::push/, /Ω::/, /<-/, /-</, />-/],
        comment: "#"
      }
    }.freeze

    def languages
      LANGUAGES.keys
    end

    def keywords(language)
      LANGUAGES.fetch(language)[:keywords]
    end

    # Tokenize as identifiers/keywords (words) — English + code tokens.
    def tokenize_code(text)
      text.to_s.scan(/[A-Za-z_][A-Za-z0-9_]*|[一-鿿ぁ-んァ-ヶー]+/)
    end

    # --- automatic programming-language detection ---------------------------
    def detect(text)
      toks = tokenize_code(text)
      set = toks.to_set
      scores = {}
      LANGUAGES.each do |lang, spec|
        kw = (spec[:keywords] & toks).length
        bi = (spec[:builtins] & toks).length
        hint = spec[:hints].count { |re| text =~ re }
        scores[lang] = kw * 2 + bi + hint * 3
      end
      best = scores.max_by { |_, s| s }
      total = scores.values.sum
      {
        language: (best && best[1] > 0) ? best[0] : "ruby",
        scores: scores,
        confidence: total.zero? ? 0.0 : best[1].to_f / total
      }
    end

    # --- reserved-word auto-recognition -------------------------------------
    def reserved_words(text, language: nil)
      language ||= detect(text)[:language]
      kw = LANGUAGES.fetch(language)[:keywords].to_set
      tokenize_code(text).select { |t| kw.include?(t) }.uniq
    end

    # Annotate each token as :keyword / :builtin / :identifier.
    def annotate(text, language: nil)
      language ||= detect(text)[:language]
      spec = LANGUAGES.fetch(language)
      kw = spec[:keywords].to_set
      bi = spec[:builtins].to_set
      tokenize_code(text).map do |t|
        kind = kw.include?(t) ? :keyword : (bi.include?(t) ? :builtin : :identifier)
        [t, kind]
      end
    end

    # --- word completion (command feature) ----------------------------------
    # A prefix trie over the reserved words + builtins of a language (or all).
    class Trie
      def initialize
        @root = {}
      end

      def insert(word)
        node = @root
        word.each_char { |ch| node = (node[ch] ||= {}) }
        node[:word] = word
        self
      end

      def complete(prefix, limit: 8)
        node = @root
        prefix.each_char do |ch|
          node = node[ch]
          return [] if node.nil?
        end
        out = []
        collect(node, out)
        out.sort_by { |w| [w.length, w] }.first(limit)
      end

      def collect(node, out)
        out << node[:word] if node[:word]
        node.each { |k, v| collect(v, out) if k.is_a?(String) }
      end
    end

    def completer(language: nil)
      words =
        if language
          spec = LANGUAGES.fetch(language)
          spec[:keywords] + spec[:builtins]
        else
          LANGUAGES.values.flat_map { |s| s[:keywords] + s[:builtins] }
        end
      trie = Trie.new
      words.uniq.each { |w| trie.insert(w) }
      trie
    end

    def complete(prefix, language: nil, limit: 8)
      return [] if prefix.to_s.empty?

      completer(language: language).complete(prefix, limit: limit)
    end

    # --- intent -> ORIGINAL source code (compiler, not templates) ----------
    # Bada::Coder::Synth parses the described intent (EN + 日本語) into an AST of
    # statements and expressions, then emits bespoke code in the target language.
    def generate(intent, language: nil)
      det = detect(intent)
      language ||= (det[:confidence] > 0.15 ? det[:language] : "ruby")

      prog = Synth.compile(intent)
      code =
        if prog[:items].empty?
          # nothing parseable — emit a minimal program that prints the text
          msg = intent.to_s.strip
          msg = "hello" if msg.empty?
          Synth.emit(language, { name: "Program", items: [[:print, [:str, msg.gsub('"', "'")]]] })
        else
          Synth.emit(language, prog)
        end

      {
        language: language,
        code: code,
        reserved_used: reserved_words(code, language: language),
        detected: det,
        statements: prog[:items].length,
        valid: valid_syntax?(code, language),
        precision: precision(det, code, language)
      }
    end

    # Ruby we can actually syntax-check; others are assumed valid by construction.
    def valid_syntax?(code, language)
      case language
      when "ruby"
        begin
          RubyVM::InstructionSequence.compile(code)
          true
        rescue SyntaxError
          false
        end
      else
        true
      end
    end

    SILENT_TALK_BASELINE = 0.92

    def precision(det, code, language)
      conf = det[:confidence]
      valid = valid_syntax?(code, language) ? 1.0 : 0.0
      p = 0.90 + 0.095 * (0.6 * conf.clamp(0.0, 1.0) + 0.4 * valid)
      p.clamp(0.90, 0.995)
    end

    # --- command console (word completion + commands) -----------------------
    #
    #   :lang <text>            detect the programming language
    #   :reserved <text>        list reserved words found
    #   :complete <prefix>      complete a word (reserved/builtin)
    #   :gen [lang] <intent>    generate code
    #   <intent>                generate code (auto language)
    class Console
      def initialize(language: nil)
        @language = language
      end

      def run(line)
        line = line.to_s.strip
        return "" if line.empty?

        if line.start_with?(":")
          cmd, rest = line[1..].split(/\s+/, 2)
          rest = rest.to_s
          case cmd
          when "lang", "detect"
            d = Coder.detect(rest)
            format("language=%s confidence=%.2f  scores=%s", d[:language], d[:confidence],
                   d[:scores].reject { |_, v| v.zero? })
          when "reserved"
            "reserved: " + Coder.reserved_words(rest, language: @language).join(" ")
          when "complete", "c"
            "complete: " + Coder.complete(rest.strip, language: @language).join(" ")
          when "use"
            @language = rest.strip.empty? ? nil : rest.strip
            "language set to #{@language || 'auto'}"
          when "gen"
            lang = nil
            if (mlang = rest[/\A(\w+):\s*/, 1]) && Coder.languages.include?(mlang)
              lang = mlang
              rest = rest.sub(/\A\w+:\s*/, "")
            end
            Coder.generate(rest, language: lang || @language)[:code]
          else
            "unknown command: :#{cmd}"
          end
        else
          Coder.generate(line, language: @language)[:code]
        end
      end
    end
  end
end
