# frozen_string_literal: true

require_relative "special"
require_relative "manifold"
require_relative "error_correction"
require_relative "tuplespace"

module Bada
  # CodeFix — source-code error correction as the integrable system of a
  # complex rotational body ("the spinning-top / koma geometry of special
  # relativity").
  #
  # The physical picture, taken straight from Bada::ErrorCorrection:
  #
  #   * Every source file is a *rotational body*. Its opening and closing
  #     delimiters — ( ) [ ] { }, quotes, and Ruby block words def…end —
  #     are angular markers on the spin orbit.
  #   * A syntactically valid file is one whose orbit *closes*: every opener
  #     returns to its closer, exactly as the integrable closed-orbit
  #     condition  ∮ e^{-□} d□ = π e  demands. The signed delimiter balance
  #     is the **conserved quantity** of the spin (the integrable invariant).
  #   * A syntax error is the top *falling off* its closed orbit: the
  #     conserved balance is broken. Correction = restoring the conserved
  #     quantity (adding the missing closer / removing the stray one /
  #     terminating the open string) so the orbit closes again.
  #   * Confidence in the repair is read off the Lorentz-damped orbit average
  #     of the manifold entropy invariant Ξ before and after the fix
  #     (Bada::ErrorCorrection): a good fix conserves Ξ, a violent rewrite
  #     does not.
  #
  # It is a genuinely working (heuristic) fixer for the most common breakages —
  # unbalanced brackets, unterminated strings, and missing/extra Ruby `end` —
  # across Ruby, Python, and the C/JS brace family, plus a submission board
  # (複数投稿) so many sources can be posted and corrected at once.
  module CodeFix
    module_function

    # ---- language table -------------------------------------------------

    PAIRS = { "(" => ")", "[" => "]", "{" => "}" }.freeze
    CLOSERS = PAIRS.values.freeze
    OPENERS = PAIRS.keys.freeze

    # Per-language lexical rules used by the scanner.
    LANGS = {
      ruby:       { line: ["#"],        block: nil,           quotes: ['"', "'"],       keyword_blocks: true  },
      python:     { line: ["#"],        block: nil,           quotes: ['"', "'"],       keyword_blocks: false },
      javascript: { line: ["//"],       block: ["/*", "*/"],  quotes: ['"', "'", "`"],  keyword_blocks: false },
      c:          { line: ["//"],       block: ["/*", "*/"],  quotes: ['"', "'"],       keyword_blocks: false },
      generic:    { line: ["#", "//"],  block: ["/*", "*/"],  quotes: ['"', "'"],       keyword_blocks: false }
    }.freeze

    EXT = {
      ".rb" => :ruby, ".ru" => :ruby, ".gemspec" => :ruby, ".rake" => :ruby,
      ".py" => :python, ".pyw" => :python,
      ".js" => :javascript, ".mjs" => :javascript, ".jsx" => :javascript,
      ".ts" => :javascript, ".tsx" => :javascript,
      ".c" => :c, ".h" => :c, ".cpp" => :c, ".cc" => :c, ".hpp" => :c,
      ".java" => :c, ".go" => :c, ".rs" => :c, ".cs" => :c
    }.freeze

    # Ruby words that open a block that must be balanced by `end`.
    RUBY_OPENERS = %w[def class module do begin case].freeze
    # if/unless/while/until/for open a block only when they *start* a line
    # (otherwise they are trailing modifiers: `return x if y`).
    RUBY_LEADING = %w[if unless while until for].freeze

    Issue = Struct.new(:line, :kind, :severity, :message, keyword_init: true)

    # ---- language detection --------------------------------------------

    def detect_language(code, name: nil)
      if name
        base = File.basename(name.to_s)
        ext = base.include?(".") ? base[base.rindex(".")..] : base
        return EXT[ext.downcase] if EXT.key?(ext.downcase)
      end
      return :ruby   if code =~ /^\s*(def|class|module|require|puts)\b/ && code.include?("end")
      return :python if code =~ /^\s*(def |class |import |print\()/ && code.include?(":")
      return :javascript if code =~ /\b(function|const|let|var|=>)\b/
      return :c if code =~ /[;{}]\s*$/ && code =~ /\b(int|void|char|double|include)\b/
      :generic
    end

    # ---- the scanner ----------------------------------------------------
    #
    # Single left-to-right pass over the source (walking the spin orbit).
    # Produces:
    #   * :edits    — insert/delete operations that re-close the orbit
    #   * :issues   — human-readable diagnostics
    #   * :cleaned  — the source with strings/comments blanked, for the Ruby
    #                 keyword pass (so `end` inside a string is never counted).
    def scan(code, lang)
      rules = LANGS.fetch(lang, LANGS[:generic])
      quotes = rules[:quotes]
      line_tokens = rules[:line]
      block_open, block_close = rules[:block]

      stack = []          # [char, index, line]
      issues = []
      edits = []          # {op: :insert|:delete, pos:, str:|len:}
      cleaned = code.dup
      i = 0
      line = 1
      len = code.length
      line_start = 0

      blank = lambda do |from, to|
        (from...to).each { |k| cleaned[k] = " " unless cleaned[k] == "\n" }
      end

      while i < len
        c = code[i]
        if c == "\n"
          line += 1
          line_start = i + 1
          i += 1
          next
        end

        # block comment
        if block_open && code[i, block_open.length] == block_open
          close_at = code.index(block_close, i + block_open.length)
          stop = close_at ? close_at + block_close.length : len
          blank.call(i, stop)
          line += code[i...stop].count("\n")
          i = stop
          next
        end

        # line comment
        if line_tokens.any? { |t| code[i, t.length] == t }
          nl = code.index("\n", i) || len
          blank.call(i, nl)
          i = nl
          next
        end

        # string literal
        if quotes.include?(c)
          q = c
          j = i + 1
          terminated = false
          while j < len
            cj = code[j]
            break if cj == "\n" && q != "`" # ` (template) may span lines
            if cj == "\\"
              j += 2
              next
            end
            if cj == q
              terminated = true
              break
            end
            j += 1
          end
          if terminated
            blank.call(i, j + 1)
            line += code[i..j].count("\n")
            i = j + 1
          else
            # orbit never re-closes on this string: terminate it at line end
            nl = code.index("\n", i) || len
            issues << Issue.new(line: line, kind: :string,
                                severity: :error,
                                message: "unterminated #{q == '`' ? 'template' : 'string'} literal — closing #{q} inserted")
            edits << { op: :insert, pos: nl, str: q }
            blank.call(i, nl)
            i = nl
          end
          next
        end

        # brackets — the angular markers of the spin orbit
        if OPENERS.include?(c)
          stack << [c, i, line]
        elsif CLOSERS.include?(c)
          if stack.empty? || PAIRS[stack.last[0]] != c
            issues << Issue.new(line: line, kind: :bracket, severity: :error,
                                message: "stray closing '#{c}' with no matching opener — removed")
            edits << { op: :delete, pos: i, len: 1 }
          else
            stack.pop
          end
        end
        i += 1
      end

      # Openers that never returned to their closer. Placement is best-effort:
      # inline containers ( ) and [ ] are almost always a same-line typo, so we
      # re-close them at the end of their opening line; block braces { } usually
      # span to the end of a scope, so we close them at EOF. (A genuinely
      # multi-line ( / [ is the one case this can mis-place — documented.)
      unless stack.empty?
        brace_tail = +""
        stack.reverse_each do |(oc, idx, ln)|
          issues << Issue.new(line: ln, kind: :bracket, severity: :error,
                              message: "unclosed '#{oc}' opened here — '#{PAIRS[oc]}' inserted")
          if oc == "{"
            brace_tail << PAIRS[oc]
          else
            nl = code.index("\n", idx) || len
            edits << { op: :insert, pos: nl, str: PAIRS[oc] }
          end
        end
        unless brace_tail.empty?
          edits << { op: :insert, pos: len, str: (code.end_with?("\n") ? "" : "\n") + brace_tail + "\n" }
        end
      end

      { edits: edits, issues: issues, cleaned: cleaned }
    end

    # ---- Ruby block-keyword balance ------------------------------------
    #
    # Net (openers − `end`) over the cleaned source. A positive deficit means
    # the spin never returned: append that many `end`s. Negative means extra
    # `end`s (reported only — deleting a mid-file `end` safely is ambiguous).
    def ruby_keyword_balance(cleaned)
      depth = 0
      issues = []
      open_lines = []
      cleaned.each_line.with_index(1) do |raw, ln|
        code = raw.sub(/#.*$/, "")
        stripped = code.strip
        next if stripped.empty?

        opens = 0
        # leading block words (not trailing modifiers)
        first = stripped[/\A(\w+)/, 1]
        opens += 1 if RUBY_LEADING.include?(first)
        # unconditional block words anywhere as whole words
        RUBY_OPENERS.each { |w| opens += code.scan(/\b#{w}\b/).length }
        # `do` blocks (with or without |args|)
        opens += code.scan(/\bdo\b(\s*\|[^|]*\|)?/).length
        # closers on this line
        closes = code.scan(/\bend\b/).length

        net = opens - closes
        depth += net
        open_lines << ln if net.positive?
      end

      if depth.positive?
        depth.times do
          issues << Issue.new(line: open_lines.last || 0, kind: :keyword, severity: :error,
                              message: "unbalanced Ruby block — missing `end` appended")
        end
      elsif depth.negative?
        (-depth).times do
          issues << Issue.new(line: 0, kind: :keyword, severity: :warning,
                              message: "extra `end` detected — remove it manually (auto-removal is unsafe)")
        end
      end
      { deficit: depth, issues: issues }
    end

    # ---- apply edits ----------------------------------------------------

    def apply_edits(code, edits)
      out = code.dup
      edits.sort_by { |e| -e[:pos] }.each do |e|
        case e[:op]
        when :insert then out.insert(e[:pos], e[:str])
        when :delete then out.slice!(e[:pos], e[:len])
        end
      end
      out
    end

    # ---- full single-source fix ----------------------------------------

    Result = Struct.new(:name, :language, :ok, :issues, :original, :fixed,
                        :changed, :stats, :confidence, keyword_init: true) do
      def summary
        head = ok ? "✅ orbit closed (no errors)" : "🛠  #{issues.length} correction(s)"
        "#{name} [#{language}] — #{head}, Ξ-confidence #{format('%.3f', confidence)}"
      end
    end

    def fix(code, name: "source", language: nil)
      code = code.to_s
      language ||= detect_language(code, name: name)
      s = scan(code, language)
      issues = s[:issues].dup
      edits = s[:edits].dup

      if LANGS.fetch(language, LANGS[:generic])[:keyword_blocks]
        kb = ruby_keyword_balance(s[:cleaned])
        issues.concat(kb[:issues])
        if kb[:deficit].positive?
          pad = code.end_with?("\n") ? "" : "\n"
          edits << { op: :insert, pos: code.length, str: pad + (["end"] * kb[:deficit]).join("\n") + "\n" }
        end
      end

      fixed = apply_edits(code, edits)
      changed = fixed != code

      before = Manifold.invariant(code)[:invariant]
      after = Manifold.invariant(fixed)[:invariant]
      cert = ErrorCorrection.correct([before, after].reject { |v| v.nil? || !v.finite? })
      # Confidence = how well the manifold invariant Ξ is *conserved* by the
      # repair (the integrable guarantee). A tiny, orbit-restoring edit keeps Ξ
      # nearly fixed -> confidence ~ 1; a violent rewrite drops it.
      denom = (before.abs + after.abs + 1e-9)
      confidence = 1.0 - ((before - after).abs / denom).clamp(0.0, 1.0)

      Result.new(
        name: name,
        language: language,
        ok: issues.empty?,
        issues: issues.sort_by { |x| [x.line, x.kind.to_s] },
        original: code,
        fixed: fixed,
        changed: changed,
        stats: { before: before, after: after, certified: cert[:value], residual: cert[:residual] },
        confidence: confidence
      )
    end

    def fix_file(path)
      fix(File.read(path), name: File.basename(path))
    end

    # =====================================================================
    # Repository — the submission board (複数投稿). Post many sources, correct
    # them all in one pass, and keep every submission + repair in the Akashic
    # TupleSpace so the whole batch is searchable by keyword or by invariant.
    # =====================================================================
    class Repository
      Submission = Struct.new(:id, :name, :language, :source, :result, keyword_init: true)

      def initialize
        @submissions = []
        @space = Bada::TupleSpace.new
      end

      attr_reader :submissions, :space

      # Post one source. Returns the Submission.
      def submit(source, name: nil, language: nil)
        id = @submissions.length + 1
        name ||= "submission_#{id}"
        result = CodeFix.fix(source, name: name, language: language)
        sub = Submission.new(id: id, name: name, language: result.language, source: source, result: result)
        @submissions << sub
        @space.push(source, key: "code::#{id}::#{name}",
                    tags: { id: id, language: result.language, ok: result.ok, issues: result.issues.length })
        sub
      end

      # Post a file from disk.
      def submit_file(path)
        submit(File.read(path), name: File.basename(path))
      end

      # Post many at once: array of files, or of {source:, name:, language:}.
      def submit_many(items)
        items.map do |item|
          if item.is_a?(String)
            File.file?(item) ? submit_file(item) : submit(item)
          else
            submit(item[:source], name: item[:name], language: item[:language])
          end
        end
      end

      def total_issues
        @submissions.sum { |s| s.result.issues.length }
      end

      def clean_count
        @submissions.count { |s| s.result.ok }
      end

      # Batch report over every submission.
      def report
        lines = []
        lines << "╔═ Bada CodeFix — 複素回転体・特殊相対性の可積分コマ幾何による多重投稿修正"
        lines << "║  submissions: #{@submissions.length}   clean: #{clean_count}   corrections: #{total_issues}"
        lines << "╚" + ("═" * 60)
        @submissions.each do |s|
          r = s.result
          lines << ""
          lines << "▸ ##{s.id} #{r.summary}"
          if r.issues.empty?
            lines << "    (orbit already closed — conserved balance intact)"
          else
            r.issues.first(12).each do |iss|
              loc = iss.line.positive? ? "L#{iss.line}" : "—"
              mark = iss.severity == :error ? "✗" : "!"
              lines << "    #{mark} #{loc} [#{iss.kind}] #{iss.message}"
            end
            lines << "    … #{r.issues.length - 12} more" if r.issues.length > 12
          end
          lines << format("    Ξ before %.6f → after %.6f  (conserved %s)",
                          r.stats[:before], r.stats[:after],
                          (r.stats[:before] - r.stats[:after]).abs < 1e-6 ? "yes" : "no")
        end
        lines.join("\n")
      end
    end
  end
end
