# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

class TestBadaLang < Minitest::Test
  def vm(src)
    Bada::Lang::VM.new.load(src)
  end

  def test_arithmetic_and_precedence
    v = vm("def f()\n  return 2 + 3 * 4 - 1\nend")
    assert_in_delta 13.0, v.call("f"), 1e-12
  end

  def test_parentheses
    v = vm("def f()\n  return (2 + 3) * 4\nend")
    assert_in_delta 20.0, v.call("f"), 1e-12
  end

  def test_params_and_call
    v = vm("def add(a, b)\n  return a + b\nend")
    assert_in_delta 7.0, v.call("add", [3.0, 4.0]), 1e-12
  end

  def test_recursion
    v = vm(<<~BADA)
      def fib(n)
        if n < 2
          return n
        end
        return fib(n - 1) + fib(n - 2)
      end
    BADA
    assert_in_delta 55.0, v.call("fib", [10.0]), 1e-12
  end

  def test_while_and_arrays
    v = vm(<<~BADA)
      def total(xs)
        set i = 0
        set acc = 0
        while i < len(xs)
          set acc = acc + xs[i]
          set i = i + 1
        end
        return acc
      end
    BADA
    assert_in_delta 12.0, v.call("total", [[3.0, 4.0, 5.0]]), 1e-12
  end

  def test_if_else
    v = vm(<<~BADA)
      def sgn(x)
        if x > 0
          return 1
        else
          return 0 - 1
        end
      end
    BADA
    assert_in_delta 1.0, v.call("sgn", [5.0]), 1e-12
    assert_in_delta(-1.0, v.call("sgn", [-5.0]), 1e-12)
  end

  def test_builtins_and_array_push_sort
    v = vm(<<~BADA)
      def med(xs)
        set s = sort(xs)
        return s[floor(len(s) / 2)]
      end
      def grow()
        set a = []
        set a = push(a, 3)
        set a = push(a, 1)
        return sort(a)[0]
      end
    BADA
    assert_in_delta 5.0, v.call("med", [[9.0, 1.0, 5.0]]), 1e-12
    assert_in_delta 1.0, v.call("grow"), 1e-12
  end

  def test_beta_via_gamma_builtin
    # β(2,3) = 1!·2!/4! = 1/12
    v = vm("def beta(p, q)\n  return gamma(p) * gamma(q) / gamma(p + q)\nend")
    assert_in_delta 1.0 / 12.0, v.call("beta", [2.0, 3.0]), 1e-9
  end

  # The IQ engine really is the .bada library: its functions are loaded.
  def test_iq_bada_library_loaded
    fns = Bada::IQ.vm.functions.keys
    %w[observe_estimate bayes_mean mirror_pivot band_prob thermal_invariant
       whisper_confidence].each { |f| assert_includes fns, f }
  end
end
