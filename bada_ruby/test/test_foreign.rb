# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require "stringio"
require_relative "../lib/bada"

class TestForeignImport < Minitest::Test
  def out(src) = Bada::Lang.run(src, out: StringIO.new).output

  # --- Ruby ---
  def test_import_ruby_math
    assert_equal ["3"], out('import "ruby:Math as M"' + "\nprint str(M.sqrt(9))")
  end

  def test_import_ruby_json_requires_gem
    v = out('import "ruby:JSON as J"' + "\nprint J.generate([1, 2, 3])")
    assert_equal ["[1,2,3]"], v
  end

  def test_ruby_eval_builtin_module
    assert_equal ["55"], out('print str(Ruby.eval("(1..10).sum"))')
  end

  def test_default_alias
    # no "as": default alias = capitalized last segment ("Math")
    assert_equal ["2"], out('import "ruby:Math"' + "\nprint str(Math.cbrt(8))")
  end

  # --- Python (skips if python3 missing) ---
  def python?
    system("python3", "--version", out: File::NULL, err: File::NULL)
  end

  def test_import_python_math
    skip "python3 not available" unless python?
    assert_equal ["4"], out('import "python:math as P"' + "\nprint str(P.gcd(12, 8))")
  end

  def test_import_python_statistics
    skip "python3 not available" unless python?
    assert_equal ["5"], out('import "python:statistics as S"' + "\nprint str(S.mean([2, 4, 6, 8]))")
  end

  # --- C (skips if fiddle/libm missing) ---
  def fiddle?
    require "fiddle"
    Fiddle.dlopen("libm.so.6")
    true
  rescue StandardError, LoadError
    false
  end

  def test_import_c_libm
    skip "fiddle/libm not available" unless fiddle?
    out_lines = out('import "c:m as LibM"' + "\nprint str(LibM.pow(2, 10))")
    assert_equal ["1024"], out_lines
  end

  def test_import_c_cos
    skip "fiddle/libm not available" unless fiddle?
    v = out('import "c:m as LibM"' + "\nprint str(LibM.cos(0))").first.to_f
    assert_in_delta 1.0, v, 1e-9
  end

  # --- coercion ---
  def test_value_coercion_roundtrip
    # Ruby Array -> Bada list -> back
    assert_equal ["[1, 2, 3]"], out('import "ruby:Array as A"' + "\nprint str(Ruby.eval(\"[1,2,3]\"))")
  end
end
