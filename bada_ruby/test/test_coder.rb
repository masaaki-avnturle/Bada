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

  def test_generate_ruby_is_valid
    r = C.generate("print hello 3 times loop", language: "ruby")
    assert_equal "ruby", r[:language]
    assert r[:valid], "generated Ruby must be syntactically valid"
    assert_includes r[:code], "def"
    assert_includes r[:code], "puts"
  end

  def test_generate_python_structure
    code = C.generate("loop print hi 4 times", language: "python")[:code]
    assert_includes code, "def "
    assert_includes code, "for _ in range(4)"
    assert_includes code, "print("
  end

  def test_generate_japanese_intent
    r = C.generate("メッセージ を 5 回 繰り返し 表示 する", language: "ruby")
    assert r[:valid]
    assert_includes r[:code], "5.times"
    assert_includes r[:code], "メッセージ"
  end

  def test_generate_auto_detects_language
    r = C.generate("function greet console log hello")
    assert_equal "javascript", r[:language]
  end

  def test_precision_exceeds_or_meets_and_bounded
    r = C.generate("print hello", language: "python")
    assert_operator r[:precision], :>=, 0.90
    assert_operator r[:precision], :<=, 0.995
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
    out = @con.run(":gen python: loop print hi 4 times")
    assert_includes out, "range(4)"
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
