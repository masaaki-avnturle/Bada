# frozen_string_literal: true

require "set"

module Bada
  module Coder
    # Synth — a small natural-language → program compiler. It parses a described
    # intent (English or 日本語) into an AST of statements and expressions, then
    # emits *original* source code in the target language. This is a rule-based
    # intent compiler (not an LLM): it understands a bounded grammar of
    # assignments, arithmetic/comparison expressions, print, return, functions,
    # for/while loops and if/else — and composes them into a bespoke program.
    #
    # Statements are separated by ";", a newline, "then", "。" or "そして".
    # Operands are ASCII names / numbers / "quoted strings".
    #
    #   Synth.emit("python", Synth.compile(
    #     'set total to 0; for i from 1 to 5 add i to total; print total'))
    #
    # AST:
    #   expr : [:num,n] [:str,s] [:var,v] [:bin,op,l,r] [:neg,e] [:call,name,[args]]
    #   stmt : [:assign,v,e] [:print,e] [:return,e] [:call,name,[args]] [:expr,e]
    #          [:for,v,from,to,[body]] [:while,cond,[body]] [:if,cond,[then],[else]]
    #          [:func,name,[params],[body]]
    module Synth
      module_function

      # A name is an ASCII identifier or a kanji/katakana run (Japanese variable).
      IDENT = '[A-Za-z_]\w*|[一-鿿ァ-ヶー]+'
      # Statement-body verbs — used to find where a loop/if body begins.
      BODY_VERB = '(?:print|puts|show|output|display|echo|log|say|set|let|assign|return|add|increment|increase|call|if|while|for|repeat)\b'

      # ---- public: compile intent text -> program ---------------------------
      def compile(intent)
        text = intent.to_s
        items = []
        split_segments(text).each do |seg|
          st = parse_statement(seg.strip)
          items << st if st
        end
        prog = { name: program_name(text), items: items }
        resolve!(prog)
        asciify_names!(prog)
        prog
      end

      def program_name(text)
        m = text[/\b(?:function|func|def|program|class)\s+([A-Za-z_]\w*)/, 1]
        (m || "program").sub(/\A[a-z]/, &:upcase)
      end

      # ---- statement segmentation ------------------------------------------
      # Split on top-level separators only (never inside parentheses).
      def split_segments(text)
        text = text.gsub(/\r\n?/, "\n")
        # unify word separators to ';'
        # note: bare "then" is NOT a separator — it delimits an if…then…else.
        text = text.gsub(/\band then\b/i, ";")
                   .gsub("そして", ";").gsub("。", ";").gsub("\n", ";")
        out = []
        depth = 0
        buf = +""
        text.each_char do |ch|
          case ch
          when "(" then depth += 1; buf << ch
          when ")" then depth -= 1; buf << ch
          when ";"
            if depth <= 0 then out << buf; buf = +"" else buf << ch end
          else buf << ch
          end
        end
        out << buf
        out.reject { |s| s.strip.empty? }
      end

      # ---- statement parsing (tried in order) ------------------------------
      def parse_statement(seg)
        return nil if seg.empty?

        # FUNCTION:  function NAME (with|taking|of)? PARAMS (that)? returns EXPR
        if (m = seg.match(/\A(?:define\s+|create\s+)?(?:a\s+)?(?:function|func|method)\s+([A-Za-z_]\w*)\s*(?:\((.*?)\)|(?:with|taking|of)\s+(.+?))?\s+(?:that\s+)?(?:returns?|returning)\s+(.+)\z/i))
          name = m[1]
          params = parse_params(m[2] || m[3] || "")
          body = [[:return, parse_expr(m[4])]]
          return [:func, name, params, body]
        end
        # JP function:  NAME 関数 (引数 PARAMS)? EXPR を返す
        if (m = seg.match(/\A(#{IDENT})\s*(?:という)?関数\s*(?:\((.*?)\)|(?:引数)?\s*(.+?))?\s*[はがを]?\s*(.+?)\s*を返す\z/o))
          name = m[1]
          params = parse_params(m[2] || m[3] || "")
          return [:func, name, params, [[:return, parse_expr(m[4])]]]
        end

        # FOR:  for VAR from A to B [do|:] STMT   |  repeat N times STMT
        if (m = seg.match(/\Afor\s+([A-Za-z_]\w*)\s+from\s+(.+?)\s+to\s+(.+?)(?:\s*[:,]|\s+do\b|\s+)(.+)\z/i))
          return [:for, m[1], parse_expr(m[2]), parse_expr(m[3]), [parse_statement(m[4].strip)].compact]
        end
        if (m = seg.match(/\Arepeat\s+(.+?)\s+times?\s+(.+)\z/i))
          return [:for, "_i", [:num, 1], parse_expr(m[1]), [parse_statement(m[2].strip)].compact]
        end
        # JP for:  A から B まで VAR (を)? STMT (繰り返す)?  |  STMT を N 回 繰り返す
        if (m = seg.match(/\A(.+?)\s*から\s*(.+?)\s*まで\s*(#{IDENT})\s*を?\s*(.+?)(?:を?\s*繰り返す)?\z/o))
          return [:for, m[3], parse_expr(m[1]), parse_expr(m[2]), [parse_statement(m[4].strip)].compact]
        end
        if (m = seg.match(/\A(.+?)\s*を\s*(.+?)\s*回\s*繰り返す\z/))
          return [:for, "_i", [:num, 1], parse_expr(m[2]), [parse_statement(m[1].strip)].compact]
        end

        # WHILE:  while COND do|: STMT   |   while COND <verb…>
        if (m = seg.match(/\Awhile\s+(.+?)(?:\s*[:,]|\s+do\b)\s*(.+)\z/i))
          return [:while, parse_expr(m[1]), [parse_statement(m[2].strip)].compact]
        end
        if (m = seg.match(/\Awhile\s+(.+?)\s+(#{BODY_VERB}.+)\z/io))
          return [:while, parse_expr(m[1]), [parse_statement(m[2].strip)].compact]
        end
        if (m = seg.match(/\A(.+?)\s*の?\s*間\s*(.+?)(?:を?\s*繰り返す)?\z/)) && seg.include?("間")
          return [:while, parse_expr(m[1]), [parse_statement(m[2].strip)].compact]
        end

        # IF:  if COND then STMT [else STMT]   (then is required to delimit)
        if (m = seg.match(/\Aif\s+(.+?)\s+then\s+(.+?)(?:\s+else\s+(.+))?\z/i))
          cond, thn, els = m[1], m[2], m[3]
          return [:if, parse_expr(cond), [parse_statement(thn.strip)].compact,
                  els ? [parse_statement(els.strip)].compact : []]
        end
        # JP if:  もし COND なら STMT (でなければ STMT)
        if (m = seg.match(/\Aもし\s*(.+?)\s*なら\s*(.+?)(?:\s*でなければ\s*(.+))?\z/))
          return [:if, parse_expr(m[1]), [parse_statement(m[2].strip)].compact,
                  m[3] ? [parse_statement(m[3].strip)].compact : []]
        end

        # RETURN
        if (m = seg.match(/\Areturn\s+(.+)\z/i))
          return [:return, parse_expr(m[1])]
        end
        if (m = seg.match(/\A(.+?)\s*を返す\z/))
          return [:return, parse_expr(m[1])]
        end

        # PRINT / SHOW / OUTPUT
        if (m = seg.match(/\A(?:print|puts|show|output|display|echo|log|say)\s+(.+)\z/i))
          return [:print, parse_expr(m[1])]
        end
        if (m = seg.match(/\A(.+?)\s*を\s*(?:表示|出力|印刷|プリント)(?:する)?\z/))
          return [:print, parse_expr(m[1])]
        end

        # COMPOUND ADD:  add EXPR to VAR  |  VAR に EXPR を足す/加える
        if (m = seg.match(/\Aadd\s+(.+?)\s+to\s+([A-Za-z_]\w*)\z/i))
          v = m[2]
          return [:assign, v, [:bin, "+", [:var, v], parse_expr(m[1])]]
        end
        if (m = seg.match(/\A(#{IDENT})\s*に\s*(.+?)\s*を\s*(?:足す|加える|加算(?:する)?)\z/o))
          v = m[1]
          return [:assign, v, [:bin, "+", [:var, v], parse_expr(m[2])]]
        end
        if (m = seg.match(/\A(?:increment|increase)\s+([A-Za-z_]\w*)(?:\s+by\s+(.+))?\z/i))
          v = m[1]
          return [:assign, v, [:bin, "+", [:var, v], m[2] ? parse_expr(m[2]) : [:num, 1]]]
        end

        # ASSIGN:  set VAR to EXPR | let VAR = EXPR | VAR = EXPR | assign EXPR to VAR
        if (m = seg.match(/\A(?:set|let)\s+([A-Za-z_]\w*)\s+(?:to|be|=)\s+(.+)\z/i))
          return [:assign, m[1], parse_expr(m[2])]
        end
        if (m = seg.match(/\Aassign\s+(.+?)\s+to\s+([A-Za-z_]\w*)\z/i))
          return [:assign, m[2], parse_expr(m[1])]
        end
        if (m = seg.match(/\A([A-Za-z_]\w*)\s*=\s*(.+)\z/))
          return [:assign, m[1], parse_expr(m[2])]
        end
        # JP assign:  VAR を EXPR にする | VAR に EXPR を代入 | VAR は EXPR
        if (m = seg.match(/\A(#{IDENT})\s*を\s*(.+?)\s*に(?:する|セット)\z/o))
          return [:assign, m[1], parse_expr(m[2])]
        end
        if (m = seg.match(/\A(#{IDENT})\s*に\s*(.+?)\s*を\s*代入(?:する)?\z/o))
          return [:assign, m[1], parse_expr(m[2])]
        end
        if (m = seg.match(/\A(#{IDENT})\s*は\s*(.+)\z/o))
          return [:assign, m[1], parse_expr(m[2])]
        end

        # CALL / bare expression
        if (m = seg.match(/\Acall\s+(.+)\z/i))
          return [:expr, parse_expr(m[1])]
        end
        e = parse_expr(seg)
        e ? [:expr, e] : nil
      end

      def parse_params(str)
        str.to_s.gsub(/\band\b/i, ",").split(/[,\s]+/).map(&:strip)
           .reject(&:empty?).select { |p| p.match?(/\A[A-Za-z_]\w*\z/) }
      end

      # ---- expression parsing (recursive descent) --------------------------
      def parse_expr(str)
        toks = ExprLexer.new(normalize_ops(str)).tokens
        p = ExprParser.new(toks)
        ast = p.parse
        ast
      rescue StandardError
        nil
      end

      # Map English/Japanese word operators to symbols before lexing.
      def normalize_ops(s)
        s = " #{s} "
        subs = [
          [/\bis\s+greater\s+than\s+or\s+equal\s+to\b/i, " >= "], [/\bat\s+least\b/i, " >= "], [/以上/, " >= "],
          [/\bis\s+less\s+than\s+or\s+equal\s+to\b/i, " <= "], [/\bat\s+most\b/i, " <= "], [/以下/, " <= "],
          [/\bis\s+greater\s+than\b/i, " > "], [/\bgreater\s+than\b/i, " > "], [/より大きい|を超える|超える/, " > "],
          [/\bis\s+less\s+than\b/i, " < "], [/\bless\s+than\b/i, " < "], [/より小さい|未満/, " < "],
          [/\bis\s+not\s+equal\s+to\b/i, " != "], [/\bnot\s+equal\s+to\b/i, " != "],
          [/\bis\s+equal\s+to\b/i, " == "], [/\bequal\s+to\b/i, " == "], [/\bequals\b/i, " == "], [/等しい/, " == "],
          [/\bplus\b/i, " + "], [/\bминус\b/i, " - "], [/\bminus\b/i, " - "],
          [/\btimes\b/i, " * "], [/\bmultiplied\s+by\b/i, " * "],
          [/\bdivided\s+by\b/i, " / "], [/\bmodulo\b/i, " % "], [/\bmod\b/i, " % "],
          [/足す|プラス|加える/, " + "], [/引く|マイナス/, " - "], [/掛ける|かける/, " * "],
          [/割る|わる/, " / "]
        ]
        subs.each { |re, rep| s = s.gsub(re, rep) }
        s
      end

      # Resolve unknown bare identifiers (never assigned, not a function) to
      # string literals — so "print hello" prints the word "hello".
      def resolve!(prog)
        funcs = prog[:items].select { |i| i[0] == :func }.map { |i| i[1] }.to_set
        declared = Set.new
        prog[:items].each { |it| resolve_item(it, declared, funcs) }
        prog
      end

      def resolve_item(it, declared, funcs)
        case it[0]
        when :func
          local = declared.dup
          it[2].each { |p| local << p }
          it[3].each { |s| resolve_item(s, local, funcs) }
        when :assign
          it[2] = resolve_expr(it[2], declared, funcs)
          declared << it[1]
        when :arrdecl
          it[2] = it[2].map { |x| resolve_expr(x, declared, funcs) }
          declared << it[1]
        when :idxset
          it[2] = resolve_expr(it[2], declared, funcs)
          it[3] = resolve_expr(it[3], declared, funcs)
        when :print, :return, :expr
          it[1] = resolve_expr(it[1], declared, funcs)
        when :for
          it[2] = resolve_expr(it[2], declared, funcs)
          it[3] = resolve_expr(it[3], declared, funcs)
          local = declared.dup << it[1]
          it[4].each { |s| resolve_item(s, local, funcs) }
        when :while
          it[1] = resolve_expr(it[1], declared, funcs)
          it[2].each { |s| resolve_item(s, declared, funcs) }
        when :if
          it[1] = resolve_expr(it[1], declared, funcs)
          it[2].each { |s| resolve_item(s, declared, funcs) }
          it[3].each { |s| resolve_item(s, declared, funcs) }
        end
      end

      def resolve_expr(e, declared, funcs)
        return e if e.nil?

        case e[0]
        when :var
          declared.include?(e[1]) ? e : [:str, e[1]]
        when :bin
          [:bin, e[1], resolve_expr(e[2], declared, funcs), resolve_expr(e[3], declared, funcs)]
        when :neg
          [:neg, resolve_expr(e[1], declared, funcs)]
        when :call
          [:call, e[1], e[2].map { |a| resolve_expr(a, declared, funcs) }]
        when :idx
          [:idx, e[1], resolve_expr(e[2], declared, funcs)]
        when :arr
          [:arr, e[1].map { |x| resolve_expr(x, declared, funcs) }]
        else e
        end
      end

      # Transliterate non-ASCII (Japanese) identifiers to stable ASCII names so
      # the emitted code is valid in every target language (C/Java need ASCII).
      def asciify_names!(prog)
        map = {}
        counter = [0]
        prog[:items].each { |it| asciify_item(it, map, counter) }
        prog[:name] = ascii_name(prog[:name], map, counter) if prog[:name]
        prog
      end

      def ascii_name(name, map, counter)
        return name if name.nil? || name.match?(/\A[A-Za-z_]\w*\z/)

        map[name] ||= "v#{counter[0] += 1}"
      end

      def asciify_item(it, map, counter)
        case it[0]
        when :func
          it[1] = ascii_name(it[1], map, counter)
          it[2] = it[2].map { |p| ascii_name(p, map, counter) }
          it[3].each { |s| asciify_item(s, map, counter) }
        when :assign
          it[1] = ascii_name(it[1], map, counter)
          it[2] = asciify_expr(it[2], map, counter)
        when :arrdecl
          it[1] = ascii_name(it[1], map, counter)
          it[2] = it[2].map { |x| asciify_expr(x, map, counter) }
        when :idxset
          it[1] = ascii_name(it[1], map, counter)
          it[2] = asciify_expr(it[2], map, counter)
          it[3] = asciify_expr(it[3], map, counter)
        when :print, :return, :expr
          it[1] = asciify_expr(it[1], map, counter)
        when :for
          it[1] = ascii_name(it[1], map, counter)
          it[2] = asciify_expr(it[2], map, counter)
          it[3] = asciify_expr(it[3], map, counter)
          it[4].each { |s| asciify_item(s, map, counter) }
        when :while
          it[1] = asciify_expr(it[1], map, counter)
          it[2].each { |s| asciify_item(s, map, counter) }
        when :if
          it[1] = asciify_expr(it[1], map, counter)
          it[2].each { |s| asciify_item(s, map, counter) }
          it[3].each { |s| asciify_item(s, map, counter) }
        end
      end

      def asciify_expr(e, map, counter)
        return e if e.nil?

        case e[0]
        when :var then [:var, ascii_name(e[1], map, counter)]
        when :call then [:call, ascii_name(e[1], map, counter), e[2].map { |a| asciify_expr(a, map, counter) }]
        when :bin then [:bin, e[1], asciify_expr(e[2], map, counter), asciify_expr(e[3], map, counter)]
        when :neg then [:neg, asciify_expr(e[1], map, counter)]
        when :idx then [:idx, ascii_name(e[1], map, counter), asciify_expr(e[2], map, counter)]
        when :arr then [:arr, e[1].map { |x| asciify_expr(x, map, counter) }]
        else e
        end
      end

      # ==== expression lexer ================================================
      class ExprLexer
        def initialize(str)
          @s = str.to_s
        end

        def tokens
          toks = []
          i = 0
          n = @s.length
          while i < n
            ch = @s[i]
            if ch =~ /\s/
              i += 1
            elsif (m = @s[i..].match(/\A\d+(?:\.\d+)?/))
              toks << [:num, m[0]]; i += m[0].length
            elsif ch == '"' || ch == "'"
              j = @s.index(ch, i + 1) || (n - 1)
              toks << [:str, @s[(i + 1)...j]]; i = j + 1
            elsif (m = @s[i..].match(/\A[A-Za-z_]\w*/))
              toks << [:ident, m[0]]; i += m[0].length
            elsif (m = @s[i..].match(/\A[一-鿿ァ-ヶー]+/)) # Japanese identifier (kanji/katakana)
              toks << [:ident, m[0]]; i += m[0].length
            elsif (m = @s[i..].match(%r{\A(>=|<=|==|!=|&&|\|\||[-+*/%()<>,])}))
              toks << [:op, m[0]]; i += m[0].length
            else
              i += 1 # skip anything else (stray punctuation / non-ASCII)
            end
          end
          toks
        end
      end

      # ==== recursive-descent parser ========================================
      class ExprParser
        def initialize(tokens)
          @t = tokens
          @i = 0
        end

        def parse
          e = comparison
          e
        end

        private

        def peek = @t[@i]

        def accept_op(*ops)
          t = peek
          return nil unless t && t[0] == :op && ops.include?(t[1])

          @i += 1
          t[1]
        end

        def comparison
          left = additive
          if (op = accept_op(">", "<", ">=", "<=", "==", "!=", "&&", "||"))
            right = additive
            return [:bin, op, left, right]
          end
          left
        end

        def additive
          node = term
          while (op = accept_op("+", "-"))
            node = [:bin, op, node, term]
          end
          node
        end

        def term
          node = unary
          while (op = accept_op("*", "/", "%"))
            node = [:bin, op, node, unary]
          end
          node
        end

        def unary
          if accept_op("-")
            return [:neg, unary]
          end

          primary
        end

        def primary
          t = peek
          return [:num, 0] if t.nil?

          if t[0] == :num
            @i += 1
            return [:num, t[1].include?(".") ? t[1].to_f : t[1].to_i]
          elsif t[0] == :str
            @i += 1
            return [:str, t[1]]
          elsif t[0] == :ident
            @i += 1
            name = t[1]
            if peek && peek[0] == :op && peek[1] == "("
              @i += 1
              args = []
              unless peek && peek[0] == :op && peek[1] == ")"
                args << comparison
                while peek && peek[0] == :op && peek[1] == ","
                  @i += 1
                  args << comparison
                end
              end
              accept_op(")")
              return [:call, name, args]
            end
            return [:var, name]
          elsif t[0] == :op && t[1] == "("
            @i += 1
            e = comparison
            accept_op(")")
            return e
          end
          @i += 1
          [:num, 0]
        end
      end

      # ==== type inference (for C / Java) ===================================
      def infer_types(prog)
        types = {}
        prog[:items].each { |it| infer_item(it, types) }
        types
      end

      def infer_item(it, types)
        case it[0]
        when :assign
          types[it[1]] ||= infer_expr(it[2], types)
        when :arrdecl
          types[it[1]] = :array
        when :for
          # the loop variable is declared by the for-statement itself, so it is
          # intentionally NOT added to the surrounding declaration block.
          it[4].each { |s| infer_item(s, types) }
        when :while then it[2].each { |s| infer_item(s, types) }
        when :if
          it[2].each { |s| infer_item(s, types) }
          it[3].each { |s| infer_item(s, types) }
        end
      end

      def infer_expr(e, types)
        case e && e[0]
        when :num then e[1].is_a?(Float) ? :double : :int
        when :str then :string
        when :var then types[e[1]] || :int
        when :idx then :int
        when :arr then :array
        when :neg then infer_expr(e[1], types)
        when :bin
          return :int if %w[> < >= <= == != && ||].include?(e[1])
          lt = infer_expr(e[2], types)
          rt = infer_expr(e[3], types)
          return :string if e[1] == "+" && (lt == :string || rt == :string)
          return :double if e[1] == "/" || lt == :double || rt == :double

          :int
        else :int
        end
      end

      # ==== emitters ========================================================
      def emit(language, prog)
        case language
        when "python" then Emit.python(prog)
        when "javascript" then Emit.javascript(prog)
        when "c" then Emit.c(prog, infer_types(prog))
        when "java" then Emit.java(prog, infer_types(prog))
        when "bada" then Emit.bada(prog)
        else Emit.ruby(prog)
        end
      end

      # Expression rendering (shared — arithmetic/comparison syntax is common).
      def expr_str(e, lang = :default)
        case e && e[0]
        when :num then e[1].to_s
        when :str then "\"#{e[1]}\""
        when :var then e[1]
        when :neg then "-#{expr_str(e[1], lang)}"
        when :call then "#{e[1]}(#{e[2].map { |a| expr_str(a, lang) }.join(', ')})"
        when :idx then "#{e[1]}[#{expr_str(e[2], lang)}]"
        when :arr then "[#{e[1].map { |x| expr_str(x, lang) }.join(', ')}]"
        when :bin
          "(#{expr_str(e[2], lang)} #{e[1]} #{expr_str(e[3], lang)})"
        else "0"
        end
      end

      module Emit
        module_function

        S = Synth

        def indent(n) = "  " * n

        # ---- Ruby ----
        def ruby(prog)
          lines = []
          prog[:items].select { |i| i[0] == :func }.each { |f| lines.concat(ruby_func(f)) }
          prog[:items].reject { |i| i[0] == :func }.each { |s| lines.concat(ruby_stmt(s, 0)) }
          lines.join("\n") + "\n"
        end

        def ruby_func(f)
          out = ["def #{f[1]}(#{f[2].join(', ')})"]
          f[3].each { |s| out.concat(ruby_stmt(s, 1)) }
          out << "end" << ""
          out
        end

        def ruby_stmt(s, d)
          i = "  " * d
          case s[0]
          when :assign then ["#{i}#{s[1]} = #{S.expr_str(s[2])}"]
          when :arrdecl then ["#{i}#{s[1]} = [#{s[2].map { |x| S.expr_str(x) }.join(', ')}]"]
          when :idxset then ["#{i}#{s[1]}[#{S.expr_str(s[2])}] = #{S.expr_str(s[3])}"]
          when :print then ["#{i}puts #{S.expr_str(s[1])}"]
          when :return then ["#{i}return #{S.expr_str(s[1])}"]
          when :expr then ["#{i}#{S.expr_str(s[1])}"]
          when :for
            ["#{i}(#{S.expr_str(s[2])}..#{S.expr_str(s[3])}).each do |#{s[1]}|"] +
              s[4].flat_map { |b| ruby_stmt(b, d + 1) } + ["#{i}end"]
          when :while
            ["#{i}while #{S.expr_str(s[1])}"] + s[2].flat_map { |b| ruby_stmt(b, d + 1) } + ["#{i}end"]
          when :if
            out = ["#{i}if #{S.expr_str(s[1])}"] + s[2].flat_map { |b| ruby_stmt(b, d + 1) }
            out += ["#{i}else"] + s[3].flat_map { |b| ruby_stmt(b, d + 1) } unless s[3].empty?
            out + ["#{i}end"]
          else []
          end
        end

        # ---- Python ----
        def python(prog)
          lines = []
          prog[:items].select { |i| i[0] == :func }.each { |f| lines.concat(py_func(f)) }
          prog[:items].reject { |i| i[0] == :func }.each { |s| lines.concat(py_stmt(s, 0)) }
          lines.join("\n") + "\n"
        end

        def py_func(f)
          out = ["def #{f[1]}(#{f[2].join(', ')}):"]
          body = f[3].flat_map { |s| py_stmt(s, 1) }
          out.concat(body.empty? ? ["    pass"] : body)
          out << ""
          out
        end

        def py_stmt(s, d)
          i = "    " * d
          case s[0]
          when :assign then ["#{i}#{s[1]} = #{S.expr_str(s[2])}"]
          when :arrdecl then ["#{i}#{s[1]} = [#{s[2].map { |x| S.expr_str(x) }.join(', ')}]"]
          when :idxset then ["#{i}#{s[1]}[#{S.expr_str(s[2])}] = #{S.expr_str(s[3])}"]
          when :print then ["#{i}print(#{S.expr_str(s[1])})"]
          when :return then ["#{i}return #{S.expr_str(s[1])}"]
          when :expr then ["#{i}#{S.expr_str(s[1])}"]
          when :for
            ["#{i}for #{s[1]} in range(#{S.expr_str(s[2])}, (#{S.expr_str(s[3])}) + 1):"] +
              body_or_pass(s[4].flat_map { |b| py_stmt(b, d + 1) }, d + 1)
          when :while
            ["#{i}while #{S.expr_str(s[1])}:"] + body_or_pass(s[2].flat_map { |b| py_stmt(b, d + 1) }, d + 1)
          when :if
            out = ["#{i}if #{S.expr_str(s[1])}:"] + body_or_pass(s[2].flat_map { |b| py_stmt(b, d + 1) }, d + 1)
            out += ["#{i}else:"] + body_or_pass(s[3].flat_map { |b| py_stmt(b, d + 1) }, d + 1) unless s[3].empty?
            out
          else []
          end
        end

        def body_or_pass(lines, d)
          lines.empty? ? ["#{'    ' * d}pass"] : lines
        end

        # ---- JavaScript ----
        def javascript(prog)
          lines = []
          declared = Set.new
          prog[:items].select { |i| i[0] == :func }.each { |f| lines.concat(js_func(f)) }
          prog[:items].reject { |i| i[0] == :func }.each { |s| lines.concat(js_stmt(s, 0, declared)) }
          lines.join("\n") + "\n"
        end

        def js_func(f)
          out = ["function #{f[1]}(#{f[2].join(', ')}) {"]
          local = Set.new(f[2])
          f[3].each { |s| out.concat(js_stmt(s, 1, local)) }
          out << "}" << ""
          out
        end

        def js_stmt(s, d, declared)
          i = "  " * d
          case s[0]
          when :assign
            if declared.include?(s[1])
              ["#{i}#{s[1]} = #{S.expr_str(s[2])};"]
            else
              declared << s[1]
              ["#{i}let #{s[1]} = #{S.expr_str(s[2])};"]
            end
          when :arrdecl
            declared << s[1]
            ["#{i}let #{s[1]} = [#{s[2].map { |x| S.expr_str(x) }.join(', ')}];"]
          when :idxset then ["#{i}#{s[1]}[#{S.expr_str(s[2])}] = #{S.expr_str(s[3])};"]
          when :print then ["#{i}console.log(#{S.expr_str(s[1])});"]
          when :return then ["#{i}return #{S.expr_str(s[1])};"]
          when :expr then ["#{i}#{S.expr_str(s[1])};"]
          when :for
            declared << s[1]
            ["#{i}for (let #{s[1]} = #{S.expr_str(s[2])}; #{s[1]} <= #{S.expr_str(s[3])}; #{s[1]}++) {"] +
              s[4].flat_map { |b| js_stmt(b, d + 1, declared) } + ["#{i}}"]
          when :while
            ["#{i}while (#{S.expr_str(s[1])}) {"] + s[2].flat_map { |b| js_stmt(b, d + 1, declared) } + ["#{i}}"]
          when :if
            out = ["#{i}if (#{S.expr_str(s[1])}) {"] + s[2].flat_map { |b| js_stmt(b, d + 1, declared) } + ["#{i}}"]
            unless s[3].empty?
              out[-1] = "#{i}} else {"
              out += s[3].flat_map { |b| js_stmt(b, d + 1, declared) } + ["#{i}}"]
            end
            out
          else []
          end
        end

        # ---- C ----
        TYPE_C = { int: "int", double: "double", string: "const char*", void: "void" }.freeze

        def c(prog, types)
          funcs = prog[:items].select { |i| i[0] == :func }
          top = prog[:items].reject { |i| i[0] == :func }
          out = ["#include <stdio.h>", ""]
          funcs.each { |f| out.concat(c_func(f, types)); out << "" }
          out << "int main(void) {"
          types.each do |v, t|
            next if t == :array

            out << "  #{TYPE_C[t] || 'int'} #{v} = #{t == :string ? '""' : '0'};"
          end
          top.each { |s| out.concat(c_stmt(s, 1, types)) }
          out << "  return 0;" << "}"
          out.join("\n") + "\n"
        end

        def c_func(f, types)
          rt = TYPE_C[func_ret(f, types)] || "int"
          params = f[2].map { |p| "int #{p}" }.join(", ")
          local = local_types(f[2], f[3])
          merged = types.merge(local)
          out = ["#{rt} #{f[1]}(#{params.empty? ? 'void' : params}) {"]
          local.each do |v, t|
            next if t == :array

            out << "  #{TYPE_C[t] || 'int'} #{v} = #{t == :string ? '""' : '0'};"
          end
          f[3].each { |s| out.concat(c_stmt(s, 1, merged)) }
          out << "}"
          out
        end

        # Types of a function's local variables (assigns/arrdecls in its body),
        # excluding parameters and loop variables. Needed for C/Java declarations.
        def local_types(params, body)
          t = {}
          body.each { |s| S.infer_item(s, t) }
          params.each { |p| t.delete(p) }
          t
        end

        def c_stmt(s, d, types)
          i = "  " * d
          case s[0]
          when :assign then ["#{i}#{s[1]} = #{S.expr_str(s[2])};"]
          when :arrdecl then ["#{i}int #{s[1]}[] = {#{s[2].map { |x| S.expr_str(x) }.join(', ')}};"]
          when :idxset then ["#{i}#{s[1]}[#{S.expr_str(s[2])}] = #{S.expr_str(s[3])};"]
          when :print
            t = S.infer_expr(s[1], types)
            fmt = t == :string ? "%s" : (t == :double ? "%f" : "%d")
            ["#{i}printf(\"#{fmt}\\n\", #{S.expr_str(s[1])});"]
          when :return then ["#{i}return #{S.expr_str(s[1])};"]
          when :expr then ["#{i}#{S.expr_str(s[1])};"]
          when :for
            ["#{i}for (int #{s[1]} = #{S.expr_str(s[2])}; #{s[1]} <= #{S.expr_str(s[3])}; #{s[1]}++) {"] +
              s[4].flat_map { |b| c_stmt(b, d + 1, types) } + ["#{i}}"]
          when :while
            ["#{i}while (#{S.expr_str(s[1])}) {"] + s[2].flat_map { |b| c_stmt(b, d + 1, types) } + ["#{i}}"]
          when :if
            out = ["#{i}if (#{S.expr_str(s[1])}) {"] + s[2].flat_map { |b| c_stmt(b, d + 1, types) } + ["#{i}}"]
            unless s[3].empty?
              out[-1] = "#{i}} else {"
              out += s[3].flat_map { |b| c_stmt(b, d + 1, types) } + ["#{i}}"]
            end
            out
          else []
          end
        end

        # ---- Java ----
        TYPE_J = { int: "int", double: "double", string: "String", void: "void" }.freeze

        def java(prog, types)
          funcs = prog[:items].select { |i| i[0] == :func }
          top = prog[:items].reject { |i| i[0] == :func }
          cls = prog[:name] || "Program"
          out = ["public class #{cls} {"]
          funcs.each { |f| out.concat(java_func(f, types).map { |l| "  #{l}" }); out << "" }
          out << "  public static void main(String[] args) {"
          types.each do |v, t|
            next if t == :array

            out << "    #{TYPE_J[t] || 'int'} #{v} = #{t == :string ? '""' : '0'};"
          end
          top.each { |s| out.concat(java_stmt(s, 2, types)) }
          out << "  }" << "}"
          out.join("\n") + "\n"
        end

        def java_func(f, types)
          rt = TYPE_J[func_ret(f, types)] || "int"
          params = f[2].map { |p| "int #{p}" }.join(", ")
          local = local_types(f[2], f[3])
          merged = types.merge(local)
          out = ["static #{rt} #{f[1]}(#{params}) {"]
          local.each do |v, t|
            next if t == :array

            out << "  #{TYPE_J[t] || 'int'} #{v} = #{t == :string ? '""' : '0'};"
          end
          f[3].each { |s| out.concat(java_stmt(s, 1, merged)) }
          out << "}"
          out
        end

        def java_stmt(s, d, types)
          i = "  " * d
          case s[0]
          when :assign then ["#{i}#{s[1]} = #{S.expr_str(s[2])};"]
          when :arrdecl then ["#{i}int[] #{s[1]} = {#{s[2].map { |x| S.expr_str(x) }.join(', ')}};"]
          when :idxset then ["#{i}#{s[1]}[#{S.expr_str(s[2])}] = #{S.expr_str(s[3])};"]
          when :print then ["#{i}System.out.println(#{S.expr_str(s[1])});"]
          when :return then ["#{i}return #{S.expr_str(s[1])};"]
          when :expr then ["#{i}#{S.expr_str(s[1])};"]
          when :for
            ["#{i}for (int #{s[1]} = #{S.expr_str(s[2])}; #{s[1]} <= #{S.expr_str(s[3])}; #{s[1]}++) {"] +
              s[4].flat_map { |b| java_stmt(b, d + 1, types) } + ["#{i}}"]
          when :while
            ["#{i}while (#{S.expr_str(s[1])}) {"] + s[2].flat_map { |b| java_stmt(b, d + 1, types) } + ["#{i}}"]
          when :if
            out = ["#{i}if (#{S.expr_str(s[1])}) {"] + s[2].flat_map { |b| java_stmt(b, d + 1, types) } + ["#{i}}"]
            unless s[3].empty?
              out[-1] = "#{i}} else {"
              out += s[3].flat_map { |b| java_stmt(b, d + 1, types) } + ["#{i}}"]
            end
            out
          else []
          end
        end

        def func_ret(f, types)
          ret = f[3].find { |s| s[0] == :return }
          ret ? S.infer_expr(ret[1], types) : :void
        end

        # ---- Bada (best effort) ----
        def bada(prog)
          out = ["# generated Bada program"]
          n = 0
          prog[:items].each do |s|
            case s[0]
            when :assign
              val = s[2][0] == :num ? s[2][1] : 0
              out << "set #{s[1]} = #{val}"
            when :print
              out << (s[1][0] == :var ? "print #{s[1][1]}" : "print #{S.expr_str(s[1])}")
              out << "Omega::push #{s[1][0] == :var ? s[1][1] : 'result'} as node#{n}"
              n += 1
            end
          end
          out.join("\n") + "\n"
        end
      end
    end
  end
end
