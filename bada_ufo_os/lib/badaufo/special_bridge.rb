# frozen_string_literal: true

# SpecialBridge — 山口フレームワークの特殊作用素への橋渡し。
#
# 同一リポジトリの bada_ruby/lib/bada/special.rb（Bada::Special）が読めれば
# それを使う。読めない環境（単体配布時）でも動くよう、反重力に必要な作用素
# ── □_ag(x), □_dal(x), x log x, e^π/π^e ── を純 stdlib で自前実装する。
module BadaUFO
  module SpecialBridge
    module_function

    # bada_ruby が同梱されていれば Bada::Special を優先ロード。
    begin
      root = File.expand_path("../../..", __dir__)
      lib  = File.join(root, "bada_ruby", "lib")
      if File.directory?(lib)
        $LOAD_PATH.unshift(lib) unless $LOAD_PATH.include?(lib)
        require "bada/special"
      end
    rescue LoadError
      # フォールバックへ。
    end

    HAS_BADA = defined?(::Bada::Special)

    def x_log_x(x)
      return 0.0 if x <= 0.0
      x * Math.log(x)
    end

    def cmath_exp(z)
      r = Math.exp(z.real)
      Complex(r * Math.cos(z.imaginary), r * Math.sin(z.imaginary))
    end

    def cmath_sin(z)
      i = Complex(0, 1)
      (cmath_exp(i * z) - cmath_exp(-i * z)) / (2 * i)
    end

    def cmath_cos(z)
      i = Complex(0, 1)
      (cmath_exp(i * z) + cmath_exp(-i * z)) / 2
    end

    # □_ag(x) = 2( sin(i·x log x) + cos(i·x log x) ) = 2·cosh(x log x)
    def box_antigravity(x)
      return ::Bada::Special.box_antigravity(x) if HAS_BADA
      arg = Complex(0, 1) * x_log_x(x)
      2 * (cmath_sin(arg) + cmath_cos(arg))
    end

    # □_dal(x) = cos(i·x log x) − i·sin(i·x log x) = e^{x log x} = x^x
    def box_dalanversian(x)
      return ::Bada::Special.box_dalanversian(x) if HAS_BADA
      arg = Complex(0, 1) * x_log_x(x)
      cmath_cos(arg) - Complex(0, 1) * cmath_sin(arg)
    end

    def gravity_dual
      return ::Bada::Special.gravity_dual if HAS_BADA
      { e_pi: Math.exp(Math::PI), pi_e: Math::PI**Math::E }
    end
  end
end
