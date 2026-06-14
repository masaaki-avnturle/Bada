# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require "stringio"
require_relative "../lib/bada"

class TestLangBasics < Minitest::Test
  def run_src(src)
    Bada::Lang.run(src, out: StringIO.new)
  end

  def out(src) = run_src(src).output

  def test_arithmetic_precedence
    assert_equal ["7"], out("print 1 + 2 * 3")
    assert_equal ["9"], out("print (1 + 2) * 3")
  end

  def test_string_concat_and_str
    assert_equal ["x=42"], out('print "x=" + str(42)')
  end

  def test_let_and_assignment
    assert_equal ["3"], out("let x = 1\nx = x + 2\nprint x")
  end

  def test_if_elsif_else
    src = <<~BADA
      def grade(n)
        if n > 90
          return "A"
        elsif n > 70
          return "B"
        else
          return "C"
        end
      end
      print grade(95)
      print grade(80)
      print grade(50)
    BADA
    assert_equal %w[A B C], out(src)
  end

  def test_while_loop
    src = <<~BADA
      let i = 0
      let s = 0
      while i < 5
        s = s + i
        i = i + 1
      end
      print s
    BADA
    assert_equal ["10"], out(src)
  end

  def test_recursion
    src = <<~BADA
      def fib(n)
        if n < 2
          return n
        end
        return fib(n - 1) + fib(n - 2)
      end
      print fib(10)
    BADA
    assert_equal ["55"], out(src)
  end

  def test_booleans_and_logic
    assert_equal ["true"], out("print 1 < 2 and 2 < 3")
    assert_equal ["false"], out("print 1 < 2 and 3 < 2")
    assert_equal ["true"], out("print not false")
  end

  def test_lists
    assert_equal ["3"], out("print len([1, 2, 3])")
    assert_equal ["20"], out("print at([10, 20, 30], 1)")
  end
end

class TestLangBadaOps < Minitest::Test
  def out(src) = Bada::Lang.run(src, out: StringIO.new).output

  def test_operators_are_finite_numbers
    # <-  -<  >-  must evaluate to finite numbers
    src = <<~BADA
      print str(2.5 <- "manifold")
      print str(3.0 -< 2.0)
      print str(1.0 >- 1.0)
    BADA
    out(src).each { |line| assert Float(line).finite? }
  end
end

class TestLangModules < Minitest::Test
  def out(src) = Bada::Lang.run(src, out: StringIO.new).output

  def test_native_module_call
    v = out('print str(Manifold.xi("entropy manifold"))')[0]
    assert Float(v).finite?
  end

  def test_user_library_and_sibling_calls
    src = <<~BADA
      library M
        def base(x)
          return x * 2
        end
        def use(x)
          return base(x) + 1
        end
      end
      print M.use(10)
    BADA
    assert_equal ["21"], out(src)
  end
end

class TestLangImportAndApp < Minitest::Test
  def test_import_core_library
    interp = Bada::Lang.run(<<~BADA, out: StringIO.new)
      import "lib/core.bada"
      print Core.rule("テスト")
    BADA
    assert_equal ["──────── テスト ────────"], interp.output
  end

  def test_manifold_library_report
    interp = Bada::Lang.run(<<~BADA, out: StringIO.new)
      import "lib/manifold.bada"
      let xi = Mani.report("ガンマ関数 多様体 エントロピー")
      print "done"
    BADA
    assert_includes interp.output, "done"
    assert(interp.output.any? { |l| l.include?("大域的部分積分多様体") })
  end

  def test_full_app_runs
    app = File.expand_path("../bada/app/unknown_engine.bada", __dir__)
    interp = Bada::Lang.run_file(app, out: StringIO.new)
    joined = interp.output.join("\n")
    assert_match(/Bada 未知事前エンジン/, joined)
    assert_match(/証明完了|反証/, joined)        # the prover ran
    assert_match(/大脳基底核/, joined)            # the basal engine ran
    assert_match(/A_\{i k1\} B_\{k1 j\}/, joined) # penrose computed
  end
end
