# frozen_string_literal: true

require_relative "special"
require_relative "manifold"
require_relative "equivalence"

module Bada
  # Bada 言語の式評価器。
  #
  # 元の Bada は「1 行 = 1 演算子」の言語で、値は演算子で流すだけだった。
  # 物理を書くには算術と関数が要るので、再帰下降パーサでそこを補う。
  #
  #   式    : 数値 / 変数 / 関数呼び出し / + - * / ^ / 単項マイナス / ( )
  #   関数  : 標準ライブラリ（Special, Manifold, Equivalence）を公開
  #
  # 既存の挙動との互換のため、未知の識別子は「裸の語 = 文字列トークン」として
  # そのまま返す（`g <- manifold_node` のような旧来の書き方が動き続ける）。
  module LangExpr
    # Bada から呼べる関数表。値はすべて Float を返す（真偽は 1.0 / 0.0）。
    FUNCTIONS = {
      # --- 数学の基本 ---
      "abs"   => ->(x) { x.abs },
      "sqrt"  => ->(x) { Math.sqrt(x) },
      "exp"   => ->(x) { Math.exp(x) },
      "log"   => ->(x) { Math.log(x) },
      "log2"  => ->(x) { Math.log2(x) },
      "sin"   => ->(x) { Math.sin(x) },
      "cos"   => ->(x) { Math.cos(x) },
      "atan2" => ->(y, x) { Math.atan2(y, x) },
      "floor" => ->(x) { x.floor.to_f },
      "min"   => ->(a, b) { [a, b].min },
      "max"   => ->(a, b) { [a, b].max },
      "pi"    => -> { Math::PI },

      # --- Γ / β / ζ（山口フレームワークの特殊関数） ---
      "gamma"      => ->(x) { Special.gamma(x) },
      "log_gamma"  => ->(x) { Special.log_gamma(x) },
      "beta"       => ->(p, q) { Special.beta(p, q) },
      "x_log_x"    => ->(x) { Special.x_log_x(x) },
      "manifold"   => ->(x) { Manifold.element(x) },

      # Γ(s+1) = s·Γ(s) の破れ（大域的部分積分の不変性）
      "gamma_defect" => ->(s) { Equivalence.gamma_invariance_defect(s) },

      # --- 等価原理 ---
      # 慣性質量と重力質量が等価なら、落下加速度は質量によらない
      "accel"    => ->(g, mg, mi) { Equivalence.acceleration(g, mg, mi) },
      "eotvos"   => ->(a1, a2) { Equivalence.eotvos(a1, a2) },
      "eotvos_ratio" => lambda { |mg1, mi1, mg2, mi2, g = 9.80665|
        Equivalence.eotvos_ratio(mg1, mi1, mg2, mi2, g)
      },
      "fall_x"   => lambda { |g, mg, mi, t|
        Equivalence.free_fall(g, mg, mi, t)[0]
      },
      "fall_v"   => lambda { |g, mg, mi, t|
        Equivalence.free_fall(g, mg, mi, t)[1]
      },
      "redshift" => ->(g, h) { Equivalence.redshift(g, h) },

      # --- 放射性崩壊 / 半減期 ---
      "decay_constant" => ->(t_half) { Equivalence.decay_constant(t_half) },
      "half_life"      => ->(lam) { Equivalence.half_life(lam) },
      "decay"          => ->(n0, t_half, t) { Equivalence.decay(n0, t_half, t) },
      "remaining"      => ->(t_half, t) { Equivalence.remaining_fraction(t_half, t) },
      "activity"       => ->(n0, t_half, t) { Equivalence.activity(n0, t_half, t) },
      # 壊変系列 A→B→C（第3核種は安定）。which は 0/1/2。
      "chain3" => lambda { |ha, hb, n0, t, which|
        Equivalence.decay_chain([ha, hb, nil], n0, t)[which.to_i]
      },
      "secular_ratio" => lambda { |hp, hd|
        Equivalence.secular_equilibrium_ratio(hp, hd)
      },

      # --- トポロジー ---
      "mobius_orientation" => ->(laps) { Equivalence.mobius_orientation(laps).to_f },
      "orientable"  => ->(laps) { Equivalence.orientable_return?(laps) ? 1.0 : 0.0 },
      "euler"       => ->(v, e, f) { Equivalence.euler_characteristic(v, e, f).to_f },
      "genus_euler" => ->(g) { Equivalence.genus_to_euler(g).to_f },
      "mobius_euler" => -> { Equivalence.mobius_euler.to_f },
    }.freeze

    # 式を評価する。env は 名前 => 数値 or BadaNode。
    def self.eval(src, env = {})
      Parser.new(src, env).parse
    end

    # 再帰下降パーサ
    class Parser
      def initialize(src, env)
        @s = src.to_s
        @i = 0
        @env = env
      end

      def parse
        skip_ws
        # 文字列リテラルは式ではなくそのまま返す（旧来の挙動）
        if peek == '"'
          return string_literal
        end

        v = expr
        skip_ws
        # 式として読み切れない場合は「裸の語」として原文を返す（後方互換）
        return @s.strip if @i < @s.length && !v.is_a?(Numeric)

        raise "Bada expression error: #{@s.inspect}" if @i < @s.length

        v
      end

      private

      def peek = @s[@i]
      def skip_ws = (@i += 1 while @s[@i] =~ /\s/)

      def string_literal
        @i += 1
        buf = +""
        buf << @s[@i] and @i += 1 while @i < @s.length && @s[@i] != '"'
        @i += 1 if @s[@i] == '"'
        buf
      end

      # expr := term (('+'|'-') term)*
      def expr
        v = term
        loop do
          skip_ws
          if peek == "+"
            @i += 1
            v = num(v) + num(term)
          elsif peek == "-" && !arrow_ahead?
            @i += 1
            v = num(v) - num(term)
          else
            return v
          end
        end
      end

      # `-<` は多様体積分の演算子なので、引き算と取り違えない
      def arrow_ahead? = @s[@i, 2] == "-<"

      # term := power (('*'|'/') power)*
      def term
        v = power
        loop do
          skip_ws
          if peek == "*"
            @i += 1
            v = num(v) * num(power)
          elsif peek == "/"
            @i += 1
            d = num(power)
            raise "Bada: division by zero" if d.zero?

            v = num(v) / d
          else
            return v
          end
        end
      end

      # power := unary ('^' power)?    右結合
      def power
        v = unary
        skip_ws
        if peek == "^"
          @i += 1
          return num(v)**num(power)
        end
        v
      end

      def unary
        skip_ws
        if peek == "-"
          @i += 1
          return -num(unary)
        end
        primary
      end

      def primary
        skip_ws
        return string_literal if peek == '"'

        if peek == "("
          @i += 1
          v = expr
          skip_ws
          raise "Bada: unbalanced parenthesis in #{@s.inspect}" unless peek == ")"

          @i += 1
          return v
        end

        if @s[@i..] =~ /\A(\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)/
          @i += Regexp.last_match(1).length
          return Regexp.last_match(1).to_f
        end

        if @s[@i..] =~ /\A([A-Za-z_]\w*)/
          name = Regexp.last_match(1)
          @i += name.length
          skip_ws
          if peek == "("
            @i += 1
            args = []
            skip_ws
            unless peek == ")"
              loop do
                args << num(expr)
                skip_ws
                break unless peek == ","

                @i += 1
              end
            end
            raise "Bada: unbalanced call to #{name}" unless peek == ")"

            @i += 1
            return call(name, args)
          end
          return lookup(name)
        end

        raise "Bada expression error at #{@i} in #{@s.inspect}"
      end

      def call(name, args)
        fn = FUNCTIONS[name]
        raise "Bada: unknown function #{name}" unless fn

        arity = fn.arity
        if arity >= 0 && args.size != arity
          raise "Bada: #{name} expects #{arity} argument(s), got #{args.size}"
        end

        fn.call(*args)
      end

      def lookup(name)
        v = @env[name]
        return name if v.nil?          # 未知の識別子は裸の語（後方互換）

        v.respond_to?(:value) ? v.value : v
      end

      def num(v)
        return v.to_f if v.is_a?(Numeric)
        return v.value.to_f if v.respond_to?(:value)

        raise "Bada: #{v.inspect} is not a number"
      end
    end
  end
end
