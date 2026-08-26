# frozen_string_literal: true

require_relative "special"
require_relative "manifold"
require_relative "tuplespace"
require_relative "lang_expr"

module Bada
  # The Bada language, rebuilt from scratch on top of Ruby.
  #
  # Bada is an operator-algebra language: programs are sequences of manifold
  # operators acting on values that live in Omega::DATABASE (a TupleSpace).
  # The three core operators come straight from the README / Bada1 report:
  #
  #   <-   left non-commutative act     π(χ,x) = [iπ, f(x)]
  #   -<   manifold integral            ∬ 1/(x log x)^2 dx_m
  #   >-   quantum right act            ⊕(iℏ∇)^⊕L = e^{-x log x}
  #   Ω::  / Omega::                    TupleSpace (Akashic) namespace
  #
  # A BadaNode is the runtime value the operators act on; Interpreter is a small
  # line-oriented evaluator for Bada source.
  class BadaNode
    attr_accessor :value, :history

    def initialize(value = 0.0)
      @value = value
      @history = []
    end

    # <-  left non-commutative act:  π(χ,x) = [iπ(χ,x), f(x)]
    # Implemented as the commutator magnitude of the imaginary generator iπ·χ
    # with f(x)=log x. For a string input χ is its entropy invariant.
    def left_act(input)
      chi = coerce(input)
      x = (@value.abs < 1e-9 ? 1.0 : @value.abs) + 1.0
      pi_chi = Complex(0, Math::PI) * chi
      commutator = (pi_chi * Math.log(x) - Math.log(x) * pi_chi) # = 0 for scalars...
      # non-commutative content carried by the rotation phase:
      result = (pi_chi * Math.log(x)).abs
      @history << [:left_act, input, result]
      @value = result
      self
    end

    # -<  manifold integral on the current state.
    def manifold_integral(state = nil)
      s = state.nil? ? @value : coerce(state)
      x = s.abs + 2.0
      result = Special.x_log_x(x) * Manifold.element(x) + Manifold.element(x)
      @history << [:manifold_integral, state, result]
      @value = result
      self
    end

    # >-  quantum right act:  e^{-x log x}.
    def right_act(output = nil)
      o = output.nil? ? @value : coerce(output)
      x = o.abs + 1e-6
      result = Math.exp(-Special.x_log_x(x))
      @history << [:right_act, output, result]
      @value = result
      self
    end

    def coerce(v)
      case v
      when Numeric then v.to_f
      when String  then Manifold.xi(v)
      when BadaNode then v.value
      else 0.0
      end
    end

    def to_s
      "#<BadaNode value=#{@value}>"
    end
  end

  # Line-oriented interpreter for Bada source.
  #
  #   set g = 3.5            # bind a value
  #   g <- "hello world"     # left act with a string (its manifold invariant)
  #   g -< 2.0               # manifold integral
  #   g >- g                 # quantum right act
  #   Omega::push g as node1 # write to the Akashic TupleSpace
  #   print g                # print a value
  #
  # Comments start with '#'. Strings use double quotes.
  class Interpreter
    attr_reader :env, :db, :output

    def initialize(db: TupleSpace.new)
      @env = {}
      @db = db
      @output = []
    end

    def run(source)
      # .bada は UTF-8 で書かれる。ロケールが ASCII の環境で File.read された
      # ソースが渡されても落ちないよう、ここで明示的に付け直す。
      src = source.to_s
      src = src.dup.force_encoding(Encoding::UTF_8) unless src.encoding == Encoding::UTF_8
      lines = src.each_line.map { |raw| raw.strip.sub(/#.*\z/, "").strip }
      exec_block(lines, 0, lines.length)
      @output
    end

    private

    # lines[from...to] を順に実行する。repeat ブロックはここで畳む。
    def exec_block(lines, from, to)
      i = from
      while i < to
        line = lines[i]
        if line.empty?
          i += 1
          next
        end

        if line =~ /\Arepeat\s+(.+?)\s+as\s+(\w+)\z/
          count = num_of(eval_expr(Regexp.last_match(1))).to_i
          var = Regexp.last_match(2)
          body_end = matching_end(lines, i + 1, to)
          count.times do |k|
            @env[var] = k.to_f
            exec_block(lines, i + 1, body_end)
          end
          i = body_end + 1
          next
        end

        raise "Bada: 'end' without a matching block" if line == "end"

        exec_line(line)
        i += 1
      end
    end

    # 対応する end の位置を返す（ネスト対応）。
    def matching_end(lines, from, to)
      depth = 0
      (from...to).each do |j|
        l = lines[j]
        depth += 1 if l =~ /\Arepeat\s+.+\s+as\s+\w+\z/
        if l == "end"
          return j if depth.zero?

          depth -= 1
        end
      end
      raise "Bada: missing 'end' for repeat block"
    end

    def exec_line(line)
      case line
      when /\Aset\s+(\w+)\s*=\s*(.+)\z/
        @env[$1] = node_for(eval_expr($2))
      when /\A(\w+)\s*<-\s*(.+)\z/
        nodef($1).left_act(eval_expr($2))
      when /\A(\w+)\s*-<\s*(.+)\z/
        nodef($1).manifold_integral(eval_expr($2))
      when /\A(\w+)\s*>-\s*(.+)\z/
        nodef($1).right_act(eval_expr($2))
      when /\Alet\s+(\w+)\s*=\s*(.+)\z/
        # 数値変数（BadaNode を作らずスカラーのまま保持する）
        @env[$1] = num_of(eval_expr($2))
      when /\A(?:Omega|Ω)::push\s+(\w+)(?:\s+as\s+(\w+))?\z/
        n = nodef($1)
        key = $2
        t = @db.push(n.value.to_s, key: key)
        @output << "Ω::push #{key || t.key} (Xi=#{format('%.4f', n.value)})"
      when /\Aprint\s+(.+)\z/
        @output << render_print($1)
      else
        raise "Bada syntax error: #{line.inspect}"
      end
    end

    def nodef(name)
      @env[name] ||= BadaNode.new
    end

    def node_for(v)
      v.is_a?(BadaNode) ? v : BadaNode.new(v.is_a?(Numeric) ? v.to_f : Manifold.xi(v.to_s))
    end

    # 式評価器。数値・文字列リテラル・変数に加え、算術と関数呼び出しを扱う。
    # 読み切れない語は「裸の語 = 文字列トークン」として返す（後方互換）。
    def eval_expr(src)
      s = src.strip
      return $1 if s =~ /\A"(.*)"\z/
      return @env[s] if @env.key?(s)

      LangExpr.eval(s, @env)
    end

    # print の引数を描画する。カンマ区切りで文字列と式を混ぜられる。
    #   print "eta = ", eotvos(a1, a2)
    def render_print(src)
      split_args(src).map { |part|
        v = eval_expr(part)
        v = v.value if v.is_a?(BadaNode)
        v.is_a?(Float) ? format_number(v) : v.to_s
      }.join
    end

    # 括弧と文字列の内側のカンマでは区切らない。
    def split_args(src)
      parts = []
      buf = +""
      depth = 0
      in_str = false
      src.each_char do |ch|
        if in_str
          buf << ch
          in_str = false if ch == '"'
          next
        end
        case ch
        when '"' then in_str = true; buf << ch
        when "(" then depth += 1; buf << ch
        when ")" then depth -= 1; buf << ch
        when ","
          if depth.zero?
            parts << buf
            buf = +""
          else
            buf << ch
          end
        else buf << ch
        end
      end
      parts << buf
      parts.map(&:strip).reject(&:empty?)
    end

    # 整数は整数らしく、極端に小さい/大きい値は指数表記で出す。
    def format_number(v)
      return v.to_i.to_s if v.finite? && v == v.to_i && v.abs < 1e15
      return format("%.6e", v) if v != 0 && (v.abs < 1e-4 || v.abs >= 1e7)

      format("%.6f", v).sub(/0+\z/, "").sub(/\.\z/, "")
    end

    def num_of(v)
      return v.to_f if v.is_a?(Numeric)
      return v.value.to_f if v.is_a?(BadaNode)

      raise "Bada: #{v.inspect} is not a number"
    end
  end
end
