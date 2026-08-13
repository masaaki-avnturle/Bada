# frozen_string_literal: true

require "bada/code_fix"

module Bada
  # Grammar — a language-aware layer on top of Bada::CodeFix that adds:
  #
  #   * a grammar checker      (check)       — delimiter/quote/comment defects
  #                                            plus block-keyword balance
  #   * a parser completion    (complete)    — from the current parse state,
  #                                            the token(s) the parser expects
  #                                            next (closers, block terminators)
  #   * indent completion      (reindent /   — depth-driven re-indentation and
  #                             indent_for_new_line) auto-indent for new lines
  #
  # It reuses the spinning-top "orbit" idea: the open-token stack IS the winding
  # of the rotation orbit, and completion/indentation are read straight off it.
  # Strings and comments are masked out first so their contents never count as
  # structure. The rules are per-language but the machinery is shared, so the
  # feature works for C, JavaScript, Python, Ruby, shell and Lisp alike.
  module Grammar
    module_function

    # ---- language specifications ------------------------------------------
    BRACKETS = { "(" => ")", "[" => "]", "{" => "}" }.freeze

    SPEC = {
      c:      { style: :brace, indent: 4, line_comments: ["//"], block: [["/*", "*/"]] },
      js:     { style: :brace, indent: 2, line_comments: ["//"], block: [["/*", "*/"]] },
      json:   { style: :brace, indent: 2, line_comments: [], block: [] },
      python: { style: :colon, indent: 4, line_comments: ["#"], block: [],
                dedent: /\A(else|elif|except|finally|case)\b|\A(return|pass|break|continue|raise)\b/ },
      ruby:   { style: :keyword, indent: 2, line_comments: ["#"], block: [],
                open_kw: /\A(def|class|module|do|if|unless|while|until|case|begin|for)\b/,
                close_kw: /\A(end)\b/,
                mid_kw:  /\A(else|elsif|when|rescue|ensure|in)\b/,
                trailing_do: /\bdo(\s*\|[^|]*\|)?\s*\z/ },
      shell:  { style: :keyword, indent: 2, line_comments: ["#"], block: [],
                pairs: { "if" => "fi", "case" => "esac" },
                do_done: true },
      lisp:   { style: :paren, indent: 1, line_comments: [";"], block: [] },
      text:   { style: :brace, indent: 2, line_comments: ["#", "//"], block: [["/*", "*/"]] }
    }.freeze

    EXT = {
      ".c" => :c, ".h" => :c, ".cc" => :c, ".cpp" => :c, ".hpp" => :c, ".java" => :c,
      ".go" => :c, ".rs" => :c, ".js" => :js, ".mjs" => :js, ".ts" => :js, ".jsx" => :js,
      ".json" => :json, ".py" => :python, ".rb" => :ruby, ".gemspec" => :ruby,
      ".sh" => :shell, ".bash" => :shell, ".zsh" => :shell,
      ".lisp" => :lisp, ".lsp" => :lisp, ".el" => :lisp, ".clj" => :lisp, ".scm" => :lisp
    }.freeze

    def for_filename(name)
      return :text if name.nil?
      ext = File.extname(name.to_s).downcase
      EXT[ext] || :text
    end

    def spec(lang)
      SPEC[lang] || SPEC[:text]
    end

    def indent_width(lang)
      spec(lang)[:indent]
    end

    # ---- masking: blank out string / comment contents ---------------------
    # Returns a copy of `source` where every character inside a string literal,
    # a line comment or a block comment is replaced by a space (newlines kept),
    # so structural scanning never trips on punctuation inside them.
    def mask(source, lang)
      sp = spec(lang)
      line_comments = sp[:line_comments] || []
      blocks = sp[:block] || []
      out = source.dup
      chars = source.chars
      i = 0
      state = nil          # nil | quote-char | :block
      block_close = nil
      while i < chars.length
        c = chars[i]
        if state == :block
          if block_close && chars[i, block_close.length].join == block_close
            block_close.length.times { |k| out[i + k] = " " unless chars[i + k] == "\n" }
            i += block_close.length; state = nil; block_close = nil; next
          end
          out[i] = " " unless c == "\n"
          i += 1; next
        elsif state # inside a string
          if c == "\\"
            out[i] = " "; out[i + 1] = " " if chars[i + 1] && chars[i + 1] != "\n"
            i += 2; next
          elsif c == state
            state = nil   # keep the closing quote visible (harmless)
            i += 1; next
          else
            out[i] = " " unless c == "\n"
            i += 1; next
          end
        else
          # not in string/comment
          bc = blocks.find { |o, _| chars[i, o.length].join == o }
          if bc
            state = :block; block_close = bc[1]
            i += bc[0].length; next
          end
          lc = line_comments.find { |p| chars[i, p.length].join == p }
          if lc
            j = i
            j += 1 while j < chars.length && chars[j] != "\n"
            (i...j).each { |k| out[k] = " " }
            i = j; next
          end
          if c == '"' || c == "'" || c == "`"
            state = c; i += 1; next
          end
          i += 1
        end
      end
      out
    end

    # ---- the open-token stack (the "winding" of the parse) ----------------
    # Walk the masked source and return the stack of tokens still expected to
    # close, innermost last. Each entry is { close:, kind:, line:, col:, open: }.
    def open_stack(source, lang)
      sp = spec(lang)
      masked = mask(source, lang)
      stack = []
      lineno = 1
      col = 0
      masked.each_line do |mline|
        stripped = mline.strip
        # brackets, char by char
        mline.chars.each_with_index do |ch, idx|
          col = idx + 1
          if BRACKETS.key?(ch)
            stack.push(close: BRACKETS[ch], kind: :bracket, line: lineno, col: col, open: ch)
          elsif BRACKETS.values.include?(ch)
            top = stack.last
            if top && top[:kind] == :bracket && top[:close] == ch
              stack.pop
            elsif top && top[:kind] == :bracket
              stack.pop # mismatched; treat as closing the innermost bracket
            end
          end
        end
        # keyword blocks (leading-token heuristic on the masked, stripped line)
        case sp[:style]
        when :keyword
          if sp[:open_kw] # ruby
            if stripped =~ sp[:close_kw]
              pop_kw(stack)
            elsif stripped =~ sp[:mid_kw]
              # mid keyword: no stack change
            elsif stripped =~ sp[:open_kw]
              # 'if'/'unless'/'while'/'until' used as trailing modifier don't open
              unless trailing_modifier?(stripped, sp)
                stack.push(close: "end", kind: :keyword, line: lineno, col: 1, open: $1)
              end
            elsif stripped =~ sp[:trailing_do]
              stack.push(close: "end", kind: :keyword, line: lineno, col: 1, open: "do")
            end
          elsif sp[:pairs] # shell
            first = stripped[/\A\w+/]
            if first == "fi" || first == "esac"
              pop_kw(stack)
            elsif sp[:pairs].key?(first)
              stack.push(close: sp[:pairs][first], kind: :keyword, line: lineno, col: 1, open: first)
            elsif sp[:do_done]
              if stripped =~ /\bdo\b\s*\z/
                stack.push(close: "done", kind: :keyword, line: lineno, col: 1, open: "do")
              elsif first == "done"
                pop_kw(stack)
              end
            end
          end
        end
        lineno += 1
      end
      stack
    end

    def pop_kw(stack)
      idx = stack.rindex { |e| e[:kind] == :keyword }
      stack.delete_at(idx) if idx
    end

    def trailing_modifier?(stripped, _sp)
      # a bare 'if'/'unless'/... at start is a block opener; as a modifier it
      # appears after code: "foo if bar". Leading match => opener, so only skip
      # when the keyword is clearly a one-line modifier (has code before it).
      false
    end

    # ---- grammar check ----------------------------------------------------
    def check(source, lang: :text, filename: nil)
      lang = for_filename(filename) if filename && lang == :text
      base = CodeFix.analyze(source, filename: filename)
      diags = base[:defects].map do |d|
        { line: d.line, col: d.col, kind: d.kind, message: d.message, suggestion: d.suggestion }
      end
      # keyword-block balance (ruby/shell): report unclosed blocks by line
      st = open_stack(source, lang).select { |e| e[:kind] == :keyword }
      st.each do |e|
        diags << { line: e[:line], col: e[:col], kind: :unclosed_block,
                   message: "block '#{e[:open]}' opened at line #{e[:line]} needs '#{e[:close]}'",
                   suggestion: "insert '#{e[:close]}'" }
      end
      diags.sort_by! { |d| [d[:line], d[:col]] }
      {
        filename: filename, lang: lang,
        ok: diags.empty?,
        winding: base[:winding],
        diagnostics: diags,
        certified_invariant: base[:certified_invariant],
        invariant_conserved: base[:invariant_conserved]
      }
    end

    # ---- parser completion ------------------------------------------------
    # Given the source BEFORE the cursor, return what the parser expects next.
    #   { candidates: ["]", "}", "end"], suggestion: {type:, text:, newline:} }
    # candidates are innermost-first; suggestion is the top pick ready to insert.
    def complete(source_before_cursor, lang: :text, filename: nil, width: nil)
      lang = for_filename(filename) if filename && lang == :text
      width ||= indent_width(lang)
      stack = open_stack(source_before_cursor, lang)
      candidates = stack.reverse.map { |e| e[:close] }
      top = stack.last
      suggestion =
        if top.nil?
          # nothing open: if the last non-blank line opens a colon-block, expect
          # an indented body line.
          last = source_before_cursor.split("\n").reverse.find { |l| !l.strip.empty? }
          if last && spec(lang)[:style] == :colon && mask(last, lang).rstrip.end_with?(":")
            { type: :indent, text: (leading_ws(last) + " " * width), newline: true }
          end
        elsif top[:kind] == :bracket
          { type: :bracket, text: top[:close], newline: false }
        else
          { type: :keyword, text: top[:close], newline: true,
            indent: keyword_indent(source_before_cursor, top, lang, width) }
        end
      { candidates: candidates, suggestion: suggestion, stack_depth: stack.length }
    end

    # indent for a block terminator keyword: align with its opener line
    def keyword_indent(source, top, lang, _width)
      lines = source.split("\n")
      opener_line = lines[top[:line] - 1] || ""
      leading_ws(opener_line)
    end

    # ---- indent completion ------------------------------------------------
    # The indentation string a NEW line inserted after `row` should get.
    def indent_for_new_line(lines, row, lang: :text, filename: nil, width: nil)
      lang = for_filename(filename) if filename && lang == :text
      width ||= indent_width(lang)
      cur = lines[row] || ""
      base = leading_ws(cur)
      masked = mask(cur, lang).strip
      opens_block =
        case spec(lang)[:style]
        when :brace, :text then masked.end_with?("{", "(", "[")
        when :colon        then masked.end_with?(":")
        when :paren        then net_paren(mask(cur, lang)) > 0
        when :keyword      then opens_keyword?(masked, lang)
        else false
        end
      opens_block ? base + " " * width : base
    end

    def opens_keyword?(stripped, lang)
      sp = spec(lang)
      if sp[:open_kw]
        return false if stripped =~ sp[:close_kw]
        return true if stripped =~ sp[:open_kw] && !(stripped =~ /\bend\b\s*\z/)
        return true if stripped =~ sp[:trailing_do]
        false
      elsif sp[:pairs]
        first = stripped[/\A\w+/]
        return true if sp[:pairs].key?(first)
        return true if sp[:do_done] && stripped =~ /\bdo\b\s*\z/
        false
      else
        false
      end
    end

    # Re-indent the whole source using the depth machine. Supports brace,
    # paren, keyword and shell styles fully; for colon-significant Python it
    # only trims trailing whitespace (indentation there is semantic).
    def reindent(source, lang: :text, filename: nil, width: nil)
      lang = for_filename(filename) if filename && lang == :text
      width ||= indent_width(lang)
      style = spec(lang)[:style]
      return trim_trailing(source) if style == :colon

      raw = source.split("\n", -1)
      masked = mask(source, lang).split("\n", -1)
      out = []
      depth = 0
      raw.each_with_index do |line, i|
        ml = masked[i] || ""
        s = ml.strip
        content = line.strip
        dedent = leading_dedent(s, lang)
        level = [depth - dedent, 0].max
        out << (content.empty? ? "" : (" " * (width * level)) + content)
        depth += net_units(ml, lang)
        depth = 0 if depth < 0
      end
      out.join("\n")
    end

    # ---- low-level counters ----------------------------------------------
    def net_units(masked_line, lang)
      sp = spec(lang)
      n = net_paren(masked_line)
      if sp[:style] == :keyword
        st = masked_line.strip
        if sp[:open_kw]
          if st =~ sp[:close_kw] then n -= 1
          elsif st =~ sp[:mid_kw] then n += 0
          elsif st =~ sp[:open_kw] then n += 1
          elsif st =~ sp[:trailing_do] then n += 1
          end
        elsif sp[:pairs]
          first = st[/\A\w+/]
          if first == "fi" || first == "esac" || first == "done" then n -= 1
          elsif sp[:pairs].key?(first) then n += 1
          elsif sp[:do_done] && st =~ /\bdo\b\s*\z/ then n += 1
          end
        end
      end
      n
    end

    def leading_dedent(stripped, lang)
      sp = spec(lang)
      d = 0
      # leading closing brackets
      stripped.each_char do |ch|
        if BRACKETS.values.include?(ch) then d += 1
        elsif ch == " " || ch == "\t" then next
        else break
        end
      end
      if sp[:style] == :keyword
        if sp[:open_kw] && (stripped =~ sp[:close_kw] || stripped =~ sp[:mid_kw]) then d += 1
        elsif sp[:pairs]
          first = stripped[/\A\w+/]
          d += 1 if first == "fi" || first == "esac" || first == "done" || first == "else" || first == "elif"
        end
      end
      d
    end

    def net_paren(masked_line)
      o = masked_line.count("([{")
      c = masked_line.count(")]}")
      o - c
    end

    def leading_ws(line)
      line[/\A[ \t]*/] || ""
    end

    def trim_trailing(source)
      source.split("\n", -1).map(&:rstrip).join("\n")
    end
  end
end
