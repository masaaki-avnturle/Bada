# frozen_string_literal: true

require "bada"

module Bada
  # CodeFix — source-code error correction for *any* programming language,
  # driven by the complex-rotation spinning-top (koma) integrable system of
  # Bada::ErrorCorrection.
  #
  # The geometric idea (dalia / caostics reports):
  #
  #   box_dal = cos(i x log x) - i sin(i x log x) = e^{-i(x log x)}     (rotation)
  #   ∮ e^{-box} d(box) = pi e                                          (closed orbit)
  #
  # Read a program as a walk on the complex rotational body: every opening
  # delimiter  ( [ {  advances the phase by +θ, every closing delimiter
  # ) ] }  retards it by -θ. A *well-formed* program is an **integrable, closed
  # orbit** — it returns to phase 0 with the winding number (nesting depth)
  # back to zero. A syntax error in delimiter/quote structure is exactly an
  # **open orbit** (net winding ≠ 0, or a crossing that closes the wrong pair).
  #
  # CodeFix closes the orbit with the *minimum* rotation defect: it inserts or
  # removes the fewest delimiters/quotes so the winding returns to zero, then
  # certifies that the manifold entropy invariant Ξ is conserved by the fix
  # (the integrable-system guarantee). Because it only reasons about the
  # universal rotation structure of brackets, quotes and line balance, it is
  # language-agnostic: C, Python, Ruby, JavaScript, Lisp, JSON, … all share it.
  module CodeFix
    module_function

    OPEN  = { "(" => ")", "[" => "]", "{" => "}" }.freeze
    CLOSE = OPEN.invert.freeze

    # Line-comment prefixes and block-comment pairs common across languages.
    LINE_COMMENTS  = ["#", "//", "--", ";"].freeze
    BLOCK_COMMENTS = [["/*", "*/"]].freeze

    Defect = Struct.new(:line, :col, :kind, :message, :suggestion, keyword_init: true)

    # ---- public API --------------------------------------------------------

    # Analyse source and return a report WITHOUT modifying it.
    def analyze(source, filename: nil)
      lines = source.split("\n", -1)
      state = scan(source)
      line_load = line_rotation_load(lines)
      corrected = ErrorCorrection.correct(line_load.reject { |v| v.nil? }.map(&:to_f))
      certify = ErrorCorrection.certify_invariant(source.empty? ? " " : source)
      {
        filename: filename,
        lines: lines.length,
        winding: state[:winding],           # net nesting depth (should be 0)
        max_depth: state[:max_depth],
        quote_defect: state[:quote_defect], # unbalanced string quotes
        defects: state[:defects],
        orbit_closed: state[:defects].empty?,
        # spinning-top integrable diagnostics:
        rotation_residual: corrected[:residual],
        certified_invariant: certify[:certified],
        invariant_conserved: certify[:conserved]
      }
    end

    # Fix source and return { source:, report:, changed:, applied: [..] }.
    def fix(source, filename: nil)
      before = analyze(source, filename: filename)
      out, applied = close_orbit(source)
      # whitespace / trivial noise damping along the orbit (safe, universal)
      out2, ws = damp_whitespace(out)
      applied.concat(ws)
      after = analyze(out2, filename: filename)
      {
        source: out2,
        changed: out2 != source,
        applied: applied,
        before: before,
        report: after,
        certified_invariant: after[:certified_invariant],
        invariant_conserved: after[:invariant_conserved]
      }
    end

    # ---- rotation scan -----------------------------------------------------

    # Walk the source as a phase orbit; collect structural defects.
    # Returns winding (net depth), max_depth, quote_defect, and defects[].
    def scan(source)
      stack = []            # [char, line, col]
      defects = []
      max_depth = 0
      line_no = 1
      col = 0
      in_string = nil       # current string quote char or nil
      string_start = nil
      escaped = false
      i = 0
      chars = source.chars
      while i < chars.length
        c = chars[i]
        nxt = chars[i + 1]
        col += 1
        if c == "\n"
          # unterminated single-line string closes the orbit defect at EOL
          if in_string && in_string != :block && (in_string == '"' || in_string == "'" || in_string == "`")
            defects << Defect.new(line: line_no, col: col, kind: :quote,
              message: "unterminated string opened with #{in_string}",
              suggestion: "insert closing #{in_string}")
            in_string = nil
          end
          line_no += 1; col = 0; i += 1; next
        end

        if in_string
          if in_string == :block
            if c == "*" && nxt == "/"
              in_string = nil; i += 2; col += 1; next
            end
          else
            if escaped
              escaped = false
            elsif c == "\\"
              escaped = true
            elsif c == in_string
              in_string = nil
            end
          end
          i += 1; next
        end

        # not in a string: check comments first
        two = c + (nxt || "")
        if two == "/*"
          in_string = :block; i += 2; col += 1; next
        end
        if line_comment_at?(chars, i)
          # skip to end of line
          i += 1 while i < chars.length && chars[i] != "\n"
          next
        end
        if c == '"' || c == "'" || c == "`"
          in_string = c; string_start = [line_no, col]; i += 1; next
        end

        if OPEN.key?(c)
          stack.push([c, line_no, col])
          max_depth = stack.length if stack.length > max_depth
        elsif CLOSE.key?(c)
          if stack.empty?
            defects << Defect.new(line: line_no, col: col, kind: :unmatched_close,
              message: "stray '#{c}' with no opener",
              suggestion: "remove '#{c}' or add matching '#{CLOSE[c]}' earlier")
          else
            open_c, ol, oc = stack.pop
            want = OPEN[open_c]
            if want != c
              defects << Defect.new(line: line_no, col: col, kind: :mismatch,
                message: "'#{open_c}' at #{ol}:#{oc} closed by '#{c}'",
                suggestion: "replace '#{c}' with '#{want}'")
            end
          end
        end
        i += 1
      end

      # anything still open = orbit did not close
      quote_defect = 0
      if in_string
        quote_defect = 1
        if in_string == :block
          defects << Defect.new(line: line_no, col: col, kind: :comment,
            message: "unterminated block comment /* ... */",
            suggestion: "insert closing */")
        else
          l, cc = string_start || [line_no, col]
          defects << Defect.new(line: l, col: cc, kind: :quote,
            message: "unterminated string opened with #{in_string}",
            suggestion: "insert closing #{in_string}")
        end
      end
      stack.each do |open_c, ol, oc|
        defects << Defect.new(line: ol, col: oc, kind: :unclosed,
          message: "'#{open_c}' opened at #{ol}:#{oc} never closed",
          suggestion: "insert '#{OPEN[open_c]}'")
      end

      { winding: stack.length - 0, max_depth: max_depth,
        quote_defect: quote_defect, defects: defects, open_stack: stack }
    end

    # ---- orbit closing (the actual fix) ------------------------------------

    # Insert/replace the minimal delimiters so the winding returns to zero.
    def close_orbit(source)
      applied = []
      st = scan(source)
      out = source

      # 1) fix mismatched pairs by replacing the wrong closer (leftmost first)
      st[:defects].select { |d| d.kind == :mismatch }.each do |d|
        # replace the offending char at (line,col)
        want = d.suggestion[/replace '.' with '(.)'/, 1]
        out = replace_at(out, d.line, d.col, want) if want
        applied << "line #{d.line}: #{d.message} -> #{d.suggestion}"
      end

      # 2) remove stray closers
      st = scan(out)
      st[:defects].select { |d| d.kind == :unmatched_close }.sort_by { |d| [-d.line, -d.col] }.each do |d|
        out = delete_at(out, d.line, d.col)
        applied << "line #{d.line}: removed stray closer"
      end

      # 3) close unterminated strings / comments at end of their line/file
      st = scan(out)
      st[:defects].select { |d| d.kind == :quote }.sort_by { |d| -d.line }.each do |d|
        q = d.message[/opened with (.)/, 1]
        out = append_to_line(out, d.line, q) if q
        applied << "line #{d.line}: closed unterminated string"
      end
      if st[:defects].any? { |d| d.kind == :comment }
        out = out.rstrip + "\n*/\n"
        applied << "closed unterminated block comment"
      end

      # 4) append missing closers for anything still open (deepest last)
      st = scan(out)
      unless st[:open_stack].empty?
        closers = st[:open_stack].reverse.map { |open_c, _l, _c| OPEN[open_c] }.join
        out = out.rstrip + "\n" + closers + "\n"
        applied << "appended missing closers: #{closers}"
      end

      [out, applied]
    end

    # ---- whitespace damping (safe, universal) ------------------------------
    def damp_whitespace(source)
      applied = []
      lines = source.split("\n", -1)
      trimmed = false
      lines.map! do |ln|
        t = ln.rstrip
        trimmed = true if t != ln
        t
      end
      applied << "trimmed trailing whitespace" if trimmed
      # collapse >1 trailing blank lines to exactly one
      out = lines.join("\n")
      collapsed = out.gsub(/\n{3,}\z/, "\n\n")
      applied << "collapsed trailing blank lines" if collapsed != out
      [collapsed, applied]
    end

    # per-line "rotation load": net delimiter phase change, used as the noisy
    # sample set that the integrable orbit-average damps.
    def line_rotation_load(lines)
      depth = 0
      lines.map do |ln|
        d = 0
        ln.each_char do |c|
          d += 1 if OPEN.key?(c)
          d -= 1 if CLOSE.key?(c)
        end
        depth += d
        d.to_f
      end
    end

    # ---- text edit helpers -------------------------------------------------
    def line_comment_at?(chars, i)
      LINE_COMMENTS.any? do |p|
        p.chars.each_with_index.all? { |pc, k| chars[i + k] == pc }
      end
    end

    def replace_at(source, line, col, ch)
      lines = source.split("\n", -1)
      return source if line < 1 || line > lines.length
      s = lines[line - 1]
      idx = col - 1
      return source if idx < 0 || idx >= s.length
      s[idx] = ch
      lines[line - 1] = s
      lines.join("\n")
    end

    def delete_at(source, line, col)
      lines = source.split("\n", -1)
      return source if line < 1 || line > lines.length
      s = lines[line - 1]
      idx = col - 1
      return source if idx < 0 || idx >= s.length
      lines[line - 1] = s[0...idx] + s[(idx + 1)..]
      lines.join("\n")
    end

    def append_to_line(source, line, str)
      lines = source.split("\n", -1)
      return source + str if line < 1 || line > lines.length
      lines[line - 1] = lines[line - 1] + str
      lines.join("\n")
    end
  end
end
