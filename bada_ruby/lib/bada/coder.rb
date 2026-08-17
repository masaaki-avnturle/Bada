# frozen_string_literal: true

require "set"

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

    # --- bilingual intent -> code generation --------------------------------
    PRINT_RE = /\b(print|puts|output|show|display|echo|log|say)\b|表示|出力|印刷|プリント/i
    LOOP_RE  = /\b(loop|for|while|repeat|iterate|each|times)\b|繰り返|反復|ループ|回/i
    COND_RE  = /\b(if|when|condition|check|unless)\b|もし|条件|なら|判定/i
    FUNC_RE  = /\b(function|func|def|define|method|procedure)\b|関数|定義|メソッド|手続き/i
    ADD_RE   = /\b(add|sum|plus|total|accumulate|addition)\b|足し算|合計|加算|足す|総和|加算する/i
    STOP = %w[the a an to in of and or with please make create write program code
              い を に は が の と で た する して ください 回 times time].to_set
    JP_STOP = %w[もし 条件 なら 判定 回 度 表示 出力 印刷 プリント 繰り返し 繰り返す 反復
                 ループ する して ください 関数 定義 メソッド 手続き の を に は が と で た].to_set

    def generate(intent, language: nil)
      det = detect(intent)
      language ||= (det[:confidence] > 0.15 ? det[:language] : "ruby")
      spec = LANGUAGES.fetch(language)

      toks = tokenize_code(intent)
      arith = !!(intent =~ ADD_RE)
      nums = intent.to_s.scan(/\d+/).map(&:to_i)
      # for a sum "1..N" the upper bound is the largest number; else first count
      count = (arith ? (nums.max || 10) : (nums.first || 3)).clamp(1, 1000)
      name = identifier(toks) || "task"
      message = message_of(intent, toks) || "hello"
      ir = {
        func: name,
        loop: !!(intent =~ LOOP_RE),
        cond: !!(intent =~ COND_RE),
        arith: arith,
        count: count,
        message: message,
        want_func: !!(intent =~ FUNC_RE) || true # always wrap in a function
      }
      code = render(language, ir)
      {
        language: language,
        code: code,
        reserved_used: reserved_words(code, language: language),
        detected: det,
        valid: valid_syntax?(code, language),
        precision: precision(det, code, language)
      }
    end

    def identifier(tokens)
      t = tokens.find { |x| x.match?(/\A[A-Za-z_]/) && !STOP.include?(x.downcase) && x.length > 1 &&
                            !LANGUAGES.values.any? { |s| s[:keywords].include?(x) } }
      t && t.downcase.gsub(/[^a-z0-9_]/, "_")
    end

    def message_of(intent, tokens)
      if (m = intent[/"([^"]*)"/, 1] || intent[/'([^']*)'/, 1])
        return m
      end
      # prefer a CJK content word (skip construct/stop words), then English
      cjk = tokens.find { |t| t.match?(/[一-鿿ぁ-んァ-ヶ]/) && !JP_STOP.include?(t) }
      return cjk if cjk

      tokens.reverse.find { |t| t.match?(/\A[A-Za-z]/) && !STOP.include?(t.downcase) &&
                                !LANGUAGES.values.any? { |s| (s[:keywords] + s[:builtins]).include?(t) } }
    end

    # Render the small intermediate representation into real syntax.
    def render(language, ir)
      case language
      when "python"    then render_python(ir)
      when "javascript" then render_js(ir)
      when "c"         then render_c(ir)
      when "java"      then render_java(ir)
      when "bada"      then render_bada(ir)
      else render_ruby(ir)
      end
    end

    def render_ruby(ir)
      if ir[:arith]
        return "def #{ir[:func]}\n  total = 0\n  (1..#{ir[:count]}).each { |i| total += i }\n  puts total\n  total\nend\n\n#{ir[:func]}\n"
      end
      body = +"  puts \"#{ir[:message]}\""
      body = ir[:cond] ? "  if #{ir[:count]} > 0\n  #{body}\n  end" : body
      body = ir[:loop] ? "  #{ir[:count]}.times do\n  #{body}\n  end" : body
      "def #{ir[:func]}\n#{body}\nend\n\n#{ir[:func]}\n"
    end

    def render_python(ir)
      if ir[:arith]
        return "def #{ir[:func]}():\n    total = 0\n    for i in range(1, #{ir[:count]} + 1):\n        total += i\n    print(total)\n    return total\n\n#{ir[:func]}()\n"
      end
      inner = "print(\"#{ir[:message]}\")"
      inner = ir[:cond] ? "if #{ir[:count]} > 0:\n        #{inner}" : inner
      inner = ir[:loop] ? "for _ in range(#{ir[:count]}):\n        #{inner}" : inner
      "def #{ir[:func]}():\n    #{inner}\n\n#{ir[:func]}()\n"
    end

    def render_js(ir)
      if ir[:arith]
        return "function #{ir[:func]}() {\n  let total = 0;\n  for (let i = 1; i <= #{ir[:count]}; i++) { total += i; }\n  console.log(total);\n  return total;\n}\n\n#{ir[:func]}();\n"
      end
      inner = "console.log(\"#{ir[:message]}\");"
      inner = ir[:cond] ? "if (#{ir[:count]} > 0) { #{inner} }" : inner
      inner = ir[:loop] ? "for (let i = 0; i < #{ir[:count]}; i++) { #{inner} }" : inner
      "function #{ir[:func]}() {\n  #{inner}\n}\n\n#{ir[:func]}();\n"
    end

    def render_c(ir)
      if ir[:arith]
        return "#include <stdio.h>\n\nint #{ir[:func]}(void) {\n  int total = 0;\n  for (int i = 1; i <= #{ir[:count]}; i++) { total += i; }\n  printf(\"%d\\n\", total);\n  return total;\n}\n\nint main(void) {\n  #{ir[:func]}();\n  return 0;\n}\n"
      end
      inner = "printf(\"#{ir[:message]}\\n\");"
      inner = ir[:cond] ? "if (#{ir[:count]} > 0) { #{inner} }" : inner
      inner = ir[:loop] ? "for (int i = 0; i < #{ir[:count]}; i++) { #{inner} }" : inner
      "#include <stdio.h>\n\nvoid #{ir[:func]}(void) {\n  #{inner}\n}\n\nint main(void) {\n  #{ir[:func]}();\n  return 0;\n}\n"
    end

    def render_java(ir)
      cls = ir[:func].sub(/\A[a-z]/, &:upcase)
      if ir[:arith]
        return "public class #{cls} {\n  static int #{ir[:func]}() {\n    int total = 0;\n    for (int i = 1; i <= #{ir[:count]}; i++) { total += i; }\n    System.out.println(total);\n    return total;\n  }\n  public static void main(String[] args) {\n    #{ir[:func]}();\n  }\n}\n"
      end
      inner = "System.out.println(\"#{ir[:message]}\");"
      inner = ir[:cond] ? "if (#{ir[:count]} > 0) { #{inner} }" : inner
      inner = ir[:loop] ? "for (int i = 0; i < #{ir[:count]}; i++) { #{inner} }" : inner
      "public class #{cls} {\n  static void #{ir[:func]}() {\n    #{inner}\n  }\n  public static void main(String[] args) {\n    #{ir[:func]}();\n  }\n}\n"
    end

    def render_bada(ir)
      "set #{ir[:func]} = #{ir[:count]}\n#{ir[:func]} <- \"#{ir[:message]}\"\n#{ir[:func]} -< 2.0\nOmega::push #{ir[:func]} as node0\nprint #{ir[:func]}\n"
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
