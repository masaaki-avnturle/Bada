# frozen_string_literal: true

require_relative "special"

module Bada
  # Bada::Lang — the Bada language, grown from the line-oriented operator
  # interpreter (Bada::Interpreter) into a small but real expression / function
  # language with a tree-walking VM.
  #
  # It exists so the IQ / thermal engine can be *authored in the Bada language*
  # (see lib/bada_src/*.bada) and executed both by the Ruby CLI and — via the
  # Kotlin port (android/.../BadaVM.kt) — by the Android APK.
  #
  # Grammar (line + block oriented, `end`-terminated):
  #
  #   def name(a, b)         if cond          while cond        return expr
  #     ...                    ...              ...             print expr
  #     return expr          else             end              set x = expr
  #   end                      ...                              x = expr
  #                          end                                <expr>
  #
  # Expressions: numbers, strings, identifiers, arrays [a, b], indexing a[i],
  # calls f(x, y), arithmetic + - * / %, comparisons == != < > <= >=, and/or/not.
  # Values are Float / String / Array / boolean. Host builtins provide the
  # transcendental primitives (gamma, erf, ln, exp, ...) so the .bada libraries
  # can define beta, the manifold gauge, the four IQ stages, and so on.
  module Lang
    module_function

    class BadaError < StandardError; end

    # ── Builtins: the Bada standard primitives (a small "libc") ───────────────
    def default_builtins
      {
        "gamma"  => ->(a) { Special.gamma(a[0]) },
        "erf"    => ->(a) { Special.erf(a[0]) },
        "ln"     => ->(a) { Math.log(a[0]) },
        "exp"    => ->(a) { Math.exp(a[0]) },
        "sqrt"   => ->(a) { Math.sqrt(a[0]) },
        "abs"    => ->(a) { a[0].abs },
        "pow"    => ->(a) { a[0]**a[1] },
        "floor"  => ->(a) { a[0].floor.to_f },
        "min"    => ->(a) { [a[0], a[1]].min },
        "max"    => ->(a) { [a[0], a[1]].max },
        "pi"     => ->(_a) { Math::PI },
        "inf"    => ->(_a) { Float::INFINITY },
        "len"    => ->(a) { a[0].length.to_f },
        "push"   => ->(a) { a[0] + [a[1]] },
        "sort"   => ->(a) { a[0].sort },
        "sum"    => ->(a) { a[0].sum(0.0) }
      }
    end

    # ── VM ────────────────────────────────────────────────────────────────────
    class VM
      attr_reader :functions

      def initialize(builtins: Lang.default_builtins)
        @builtins = builtins
        @functions = {}
      end

      # Load Bada source: registers all `def`s (and runs any top-level code).
      def load(source)
        stmts = Parser.new(source).parse_program
        stmts.each { |s| exec_stmt(s, {}) }
        self
      end

      # Call a defined Bada function by name with numeric/array arguments.
      def call(name, args = [])
        fn = @functions[name] or raise BadaError, "no such Bada function: #{name}"
        invoke(fn, args)
      end

      private

      def invoke(fn, args)
        env = {}
        fn[:params].each_with_index { |p, i| env[p] = args[i] }
        catch(:return) do
          fn[:body].each { |s| exec_stmt(s, env) }
          nil
        end
      end

      def exec_stmt(node, env)
        case node[0]
        when :def
          @functions[node[1]] = { params: node[2], body: node[3] }
        when :assign
          env[node[1]] = eval_expr(node[2], env)
        when :print
          puts fmt(eval_expr(node[1], env))
        when :return
          throw(:return, node[1].nil? ? nil : eval_expr(node[1], env))
        when :if
          if truthy(eval_expr(node[1], env))
            node[2].each { |s| exec_stmt(s, env) }
          else
            node[3].each { |s| exec_stmt(s, env) }
          end
        when :while
          loop_guard = 0
          while truthy(eval_expr(node[1], env))
            node[2].each { |s| exec_stmt(s, env) }
            loop_guard += 1
            raise BadaError, "while loop exceeded 1e7 iterations" if loop_guard > 10_000_000
          end
        when :expr
          eval_expr(node[1], env)
        else
          raise BadaError, "unknown statement: #{node[0]}"
        end
      end

      def eval_expr(node, env)
        case node[0]
        when :num then node[1]
        when :str then node[1]
        when :arr then node[1].map { |e| eval_expr(e, env) }
        when :var
          raise BadaError, "undefined variable: #{node[1]}" unless env.key?(node[1])
          env[node[1]]
        when :index
          base = eval_expr(node[1], env)
          idx = eval_expr(node[2], env).to_i
          base[idx]
        when :unary
          v = eval_expr(node[2], env)
          node[1] == "-" ? -v : (truthy(v) ? false : true)
        when :binop
          apply_binop(node[1], node[2], node[3], env)
        when :call
          call_fn(node[1], node[2].map { |e| eval_expr(e, env) })
        else
          raise BadaError, "unknown expression: #{node[0]}"
        end
      end

      def apply_binop(op, an, bn, env)
        # short-circuit boolean ops
        if op == "&&"
          return truthy(eval_expr(an, env)) ? truthy(eval_expr(bn, env)) : false
        elsif op == "||"
          return truthy(eval_expr(an, env)) ? true : truthy(eval_expr(bn, env))
        end
        a = eval_expr(an, env)
        b = eval_expr(bn, env)
        case op
        when "+" then a + b
        when "-" then a - b
        when "*" then a * b
        when "/" then a / b
        when "%" then a % b
        when "<" then a < b
        when ">" then a > b
        when "<=" then a <= b
        when ">=" then a >= b
        when "==" then a == b
        when "!=" then a != b
        else raise BadaError, "unknown operator: #{op}"
        end
      end

      def call_fn(name, args)
        if @functions.key?(name)
          invoke(@functions[name], args)
        elsif @builtins.key?(name)
          @builtins[name].call(args)
        else
          raise BadaError, "call to undefined function: #{name}"
        end
      end

      def truthy(v)
        return v != 0.0 if v.is_a?(Numeric)
        return v unless v.nil?
        false
      end

      def fmt(v)
        v.is_a?(Float) ? v.to_s : v.inspect
      end
    end

    # ── Tokenizer ──────────────────────────────────────────────────────────────
    class Lexer
      OPS = %w[== != <= >= && || + - * / % ( ) [ ] , < > = !].freeze

      def self.tokenize(line)
        toks = []
        i = 0
        s = line
        n = s.length
        while i < n
          c = s[i]
          if c =~ /\s/
            i += 1
          elsif c == '"'
            j = i + 1
            j += 1 while j < n && s[j] != '"'
            toks << [:str, s[(i + 1)...j]]
            i = j + 1
          elsif c =~ /[0-9]/ || (c == "." && i + 1 < n && s[i + 1] =~ /[0-9]/)
            j = i
            j += 1 while j < n && s[j] =~ /[0-9.]/
            toks << [:num, s[i...j].to_f]
            i = j
          elsif c =~ /[A-Za-z_]/
            j = i
            j += 1 while j < n && s[j] =~ /[A-Za-z0-9_]/
            toks << [:id, s[i...j]]
            i = j
          else
            two = s[i, 2]
            if OPS.include?(two)
              toks << [:op, two]
              i += 2
            elsif OPS.include?(c)
              toks << [:op, c]
              i += 1
            else
              raise BadaError, "unexpected character #{c.inspect} in: #{line}"
            end
          end
        end
        toks
      end
    end

    # ── Parser (line-oriented statements, recursive-descent expressions) ───────
    class Parser
      KEYWORDS = %w[def end if else while return set print].freeze

      def initialize(source)
        src = source.to_s
        src = src.encode("UTF-8") unless src.encoding == Encoding::UTF_8
        @lines = src.each_line.map do |raw|
          raw.sub(/#.*/, "").rstrip
        end.reject { |l| l.strip.empty? }
        @pos = 0
      end

      def parse_program
        stmts = []
        stmts << parse_stmt while @pos < @lines.length
        stmts
      end

      private

      def peek_line = @lines[@pos]
      def next_line = @lines[@pos].tap { @pos += 1 }
      def first_word(line) = line.strip.split(/[\s(]/, 2).first

      def parse_block(terminators)
        stmts = []
        until @pos >= @lines.length || terminators.include?(first_word(peek_line))
          stmts << parse_stmt
        end
        stmts
      end

      def parse_stmt
        line = peek_line
        kw = first_word(line)
        case kw
        when "def"    then parse_def
        when "if"     then parse_if
        when "while"  then parse_while
        when "return" then parse_return
        when "set"    then parse_set
        when "print"  then parse_print
        else parse_bare
        end
      end

      def parse_def
        header = next_line.strip
        m = header.match(/\Adef\s+([A-Za-z_]\w*)\s*\((.*)\)\s*\z/) or
          raise BadaError, "bad def: #{header}"
        name = m[1]
        params = m[2].strip.empty? ? [] : m[2].split(",").map(&:strip)
        body = parse_block(%w[end])
        raise BadaError, "def #{name} missing end" if @pos >= @lines.length
        next_line # consume end
        [:def, name, params, body]
      end

      def parse_if
        cond_src = next_line.strip.sub(/\Aif\b/, "")
        cond = parse_expr_str(cond_src)
        then_body = parse_block(%w[else end])
        else_body = []
        if @pos < @lines.length && first_word(peek_line) == "else"
          next_line
          else_body = parse_block(%w[end])
        end
        raise BadaError, "if missing end" if @pos >= @lines.length
        next_line # consume end
        [:if, cond, then_body, else_body]
      end

      def parse_while
        cond_src = next_line.strip.sub(/\Awhile\b/, "")
        cond = parse_expr_str(cond_src)
        body = parse_block(%w[end])
        raise BadaError, "while missing end" if @pos >= @lines.length
        next_line # consume end
        [:while, cond, body]
      end

      def parse_return
        src = next_line.strip.sub(/\Areturn\b/, "").strip
        [:return, src.empty? ? nil : parse_expr_str(src)]
      end

      def parse_set
        src = next_line.strip.sub(/\Aset\b/, "").strip
        name, rest = src.split("=", 2)
        [:assign, name.strip, parse_expr_str(rest)]
      end

      def parse_print
        src = next_line.strip.sub(/\Aprint\b/, "").strip
        [:print, parse_expr_str(src)]
      end

      def parse_bare
        src = next_line.strip
        # assignment without `set`:  NAME = expr
        if src =~ /\A([A-Za-z_]\w*)\s*=(?!=)\s*(.+)\z/
          [:assign, $1, parse_expr_str($2)]
        else
          [:expr, parse_expr_str(src)]
        end
      end

      # Expression sub-parser over one line's tokens.
      def parse_expr_str(src)
        toks = Lexer.tokenize(src)
        ep = ExprParser.new(toks)
        node = ep.parse
        raise BadaError, "trailing tokens in: #{src}" unless ep.done?
        node
      end
    end

    # Recursive-descent / precedence-climbing expression parser.
    class ExprParser
      def initialize(toks)
        @toks = toks
        @i = 0
      end

      def parse = parse_or
      def done? = @i >= @toks.length

      private

      def peek = @toks[@i]
      def advance = @toks[@i].tap { @i += 1 }
      def op?(v) = peek && peek[0] == :op && peek[1] == v

      def eat_op(v)
        raise BadaError, "expected #{v}" unless op?(v)
        advance
      end

      def parse_or
        node = parse_and
        while op?("||")
          advance
          node = [:binop, "||", node, parse_and]
        end
        node
      end

      def parse_and
        node = parse_equality
        while op?("&&")
          advance
          node = [:binop, "&&", node, parse_equality]
        end
        node
      end

      def parse_equality
        node = parse_compare
        while op?("==") || op?("!=")
          o = advance[1]
          node = [:binop, o, node, parse_compare]
        end
        node
      end

      def parse_compare
        node = parse_add
        while op?("<") || op?(">") || op?("<=") || op?(">=")
          o = advance[1]
          node = [:binop, o, node, parse_add]
        end
        node
      end

      def parse_add
        node = parse_mul
        while op?("+") || op?("-")
          o = advance[1]
          node = [:binop, o, node, parse_mul]
        end
        node
      end

      def parse_mul
        node = parse_unary
        while op?("*") || op?("/") || op?("%")
          o = advance[1]
          node = [:binop, o, node, parse_unary]
        end
        node
      end

      def parse_unary
        if op?("-")
          advance
          [:unary, "-", parse_unary]
        elsif op?("!")
          advance
          [:unary, "!", parse_unary]
        else
          parse_postfix
        end
      end

      def parse_postfix
        node = parse_primary
        while op?("[")
          advance
          idx = parse_or
          eat_op("]")
          node = [:index, node, idx]
        end
        node
      end

      def parse_primary
        t = peek
        raise BadaError, "unexpected end of expression" unless t
        if t[0] == :num
          advance
          [:num, t[1]]
        elsif t[0] == :str
          advance
          [:str, t[1]]
        elsif op?("(")
          advance
          node = parse_or
          eat_op(")")
          node
        elsif op?("[")
          advance
          elems = []
          unless op?("]")
            elems << parse_or
            while op?(",")
              advance
              elems << parse_or
            end
          end
          eat_op("]")
          [:arr, elems]
        elsif t[0] == :id
          name = advance[1]
          return [:num, Float::INFINITY] if name == "inf_literal"
          if op?("(") # function call
            advance
            args = []
            unless op?(")")
              args << parse_or
              while op?(",")
                advance
                args << parse_or
              end
            end
            eat_op(")")
            [:call, name, args]
          elsif %w[true false].include?(name)
            [:num, name == "true" ? 1.0 : 0.0]
          else
            [:var, name]
          end
        else
          raise BadaError, "unexpected token: #{t.inspect}"
        end
      end
    end
  end
end
