# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

class TestCoderDetect < Minitest::Test
  C = Bada::Coder

  def test_detect_ruby
    assert_equal "ruby", C.detect("def foo\n  puts 42\nend")[:language]
  end

  def test_detect_python
    assert_equal "python", C.detect("def foo():\n    print(1)\n    return None")[:language]
  end

  def test_detect_javascript
    assert_equal "javascript", C.detect("const f = () => { console.log(1); }")[:language]
  end

  def test_detect_c
    assert_equal "c", C.detect("#include <stdio.h>\nint main(void){ printf(\"x\"); return 0; }")[:language]
  end

  def test_detect_java
    assert_equal "java", C.detect("public class A { public static void main(String[] a){ System.out.println(1); } }")[:language]
  end

  def test_confidence_between_zero_and_one
    d = C.detect("def x; end")
    assert_operator d[:confidence], :>=, 0.0
    assert_operator d[:confidence], :<=, 1.0
  end
end

class TestCoderReserved < Minitest::Test
  C = Bada::Coder

  def test_reserved_words_python
    r = C.reserved_words("for i in range(10):\n    if i: pass", language: "python")
    assert_includes r, "for"
    assert_includes r, "in"
    assert_includes r, "if"
    refute_includes r, "range" # builtin, not a keyword
  end

  def test_annotate_kinds
    ann = C.annotate("def foo; puts x; end", language: "ruby").to_h
    assert_equal :keyword, ann["def"]
    assert_equal :keyword, ann["end"]
    assert_equal :builtin, ann["puts"]
    assert_equal :identifier, ann["foo"]
  end
end

class TestCoderComplete < Minitest::Test
  C = Bada::Coder

  def test_complete_ruby_prefix
    assert_includes C.complete("de", language: "ruby"), "def"
  end

  def test_complete_python_print
    assert_includes C.complete("pr", language: "python"), "print"
  end

  def test_complete_cross_language
    out = C.complete("con") # console, const, continue, ...
    assert(out.any? { |w| w.start_with?("con") })
  end

  def test_complete_empty_prefix_is_empty
    assert_empty C.complete("", language: "ruby")
  end

  def test_completions_all_share_prefix
    C.complete("re", language: "ruby").each { |w| assert w.start_with?("re") }
  end
end

class TestCoderGenerate < Minitest::Test
  C = Bada::Coder

  # ---- the synthesizer generates ORIGINAL programs, not templates ----

  def test_assign_and_print_ruby_runs
    r = C.generate("set greeting to \"hi there\"; print greeting", language: "ruby")
    assert r[:valid]
    assert_equal 2, r[:statements]
    out, = capture_io { eval(r[:code]) } # rubocop:disable Security/Eval
    assert_equal "hi there", out.strip
  end

  def test_composed_sum_loop_runs_and_totals
    r = C.generate("set total to 0; for i from 1 to 5 add i to total; print total", language: "ruby")
    assert r[:valid]
    assert_equal 3, r[:statements]
    out, = capture_io { eval(r[:code]) } # rubocop:disable Security/Eval
    assert_equal "15", out.strip # 1+2+3+4+5
  end

  def test_function_def_and_call_runs
    r = C.generate("function add with a and b returning a + b; print add(2, 3)", language: "ruby")
    assert r[:valid]
    assert_includes r[:code], "def add(a, b)"
    out, = capture_io { eval(r[:code]) } # rubocop:disable Security/Eval
    assert_equal "5", out.strip
  end

  def test_if_then_else_expression_is_parsed
    r = C.generate("set x to 7; if x greater than 5 then print x else print 0", language: "ruby")
    assert r[:valid]
    assert_includes r[:code], "if (x > 5)"
    assert_includes r[:code], "else"
    out, = capture_io { eval(r[:code]) } # rubocop:disable Security/Eval
    assert_equal "7", out.strip
  end

  def test_while_loop_python_structure
    code = C.generate("set x to 3; while x less than 10 set x to x + 2; print x", language: "python")[:code]
    assert_includes code, "while (x < 10):"
    assert_includes code, "x = (x + 2)"
  end

  def test_python_composed_program
    code = C.generate("set total to 0; for i from 1 to 4 add i to total; print total", language: "python")[:code]
    assert_includes code, "for i in range(1, (4) + 1):"
    assert_includes code, "total = (total + i)"
    assert_includes code, "print(total)"
  end

  def test_japanese_variable_program_runs
    r = C.generate("合計 を 0 にする; 1 から 5 まで i を 合計 に i を 足す; 合計 を 表示", language: "ruby")
    assert r[:valid]
    # Japanese variable name is transliterated to an ASCII identifier
    assert_match(/\Av\d+\z/, r[:code][/^(\w+) = 0$/, 1])
    out, = capture_io { eval(r[:code]) } # rubocop:disable Security/Eval
    assert_equal "15", out.strip
  end

  def test_java_infers_types_and_class
    code = C.generate("function square with n returning n * n; set r to square(6); print r", language: "java")[:code]
    assert_includes code, "static int square(int n)"
    assert_includes code, "return (n * n);"
    assert_includes code, "int r = 0;"
  end

  def test_generate_auto_detects_language
    r = C.generate("function greet returning 1")
    assert_includes %w[ruby python javascript c java bada], r[:language]
  end

  def test_precision_bounded
    r = C.generate("print hello", language: "python")
    assert_operator r[:precision], :>=, 0.90
    assert_operator r[:precision], :<=, 0.995
  end

  def test_unparseable_falls_back_to_print
    r = C.generate("", language: "python")
    assert r[:valid]
    assert_includes r[:code], "print("
  end
end

class TestCoderConsole < Minitest::Test
  def setup
    @con = Bada::Coder::Console.new
  end

  def test_lang_command
    assert_match(/language=python/, @con.run(":lang def f():\n    print(1)"))
  end

  def test_complete_command
    assert_match(/\bfunction\b/, @con.run(":complete fun"))
  end

  def test_reserved_command
    out = @con.run(":reserved def foo end")
    assert_match(/def/, out)
    assert_match(/end/, out)
  end

  def test_gen_command_with_lang_prefix
    out = @con.run(":gen python: set x to 5; print x")
    assert_includes out, "x = 5"
    assert_includes out, "print(x)"
  end

  def test_use_sets_language
    @con.run(":use ruby")
    out = @con.run("print hello 2 times loop")
    assert_includes out, "puts"
  end
end

class TestMindBilingual < Minitest::Test
  def test_english_signal_verbalizes_in_english
    r = Bada::Mind::Reader.new.read("light and sound of memory flow like a wave")
    # output should be ASCII words (English), space-joined
    assert(r[:verbalization].match?(/\A[A-Za-z ]+\z/), "expected English output, got #{r[:verbalization]}")
  end

  def test_japanese_signal_verbalizes_in_japanese
    r = Bada::Mind::Reader.new.read("光 と 音 の 記憶 が 波")
    assert(r[:verbalization].each_char.any? { |c| c.match?(/[一-鿿ぁ-んァ-ヶ]/) })
  end
end
