# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

class TestCodeFix < Minitest::Test
  CF = Bada::CodeFix

  def test_clean_ruby_reports_no_issues
    r = CF.fix("def ok(x)\n  x * 2\nend\n", name: "ok.rb", language: :ruby)
    assert r.ok, "clean source should have a closed orbit"
    assert_empty r.issues
    refute r.changed
  end

  def test_unclosed_paren_is_closed_on_its_line
    r = CF.fix("def greet(name\n  name\nend\n", name: "g.rb", language: :ruby)
    refute r.ok
    assert r.fixed.include?("greet(name)")
    assert_syntax_ok r.fixed
  end

  def test_unterminated_string_is_terminated
    r = CF.fix(%Q{puts "hello\n}, name: "s.rb", language: :ruby)
    assert(r.issues.any? { |i| i.kind == :string })
    assert_syntax_ok r.fixed
  end

  def test_missing_ruby_end_is_appended
    r = CF.fix("def a\n  1\n", name: "e.rb", language: :ruby)
    assert(r.issues.any? { |i| i.kind == :keyword })
    assert_syntax_ok r.fixed
  end

  def test_stray_closer_is_removed
    r = CF.fix("x = (1 + 2))\n", name: "p.rb", language: :ruby)
    assert(r.issues.any? { |i| i.message.include?("stray") })
    assert_syntax_ok r.fixed
  end

  def test_end_inside_string_is_not_counted
    # `end` appearing inside a string must not close a block.
    src = %Q{def a\n  puts "the end"\nend\n}
    r = CF.fix(src, name: "q.rb", language: :ruby)
    assert r.ok, "string content must not affect keyword balance"
  end

  def test_block_brace_language
    r = CF.fix("function f(x) {\n  return [x, x * 2\n}\n", name: "f.js", language: :javascript)
    refute r.ok
    assert r.fixed.include?("[x, x * 2]")
  end

  def test_language_detection_from_name
    assert_equal :python, CF.detect_language("print(1)", name: "a.py")
    assert_equal :ruby, CF.detect_language("puts 1", name: "a.rb")
  end

  def test_confidence_is_bounded_and_conserved_for_small_fix
    r = CF.fix("def greet(name\n  name\nend\n", name: "g.rb", language: :ruby)
    assert_operator r.confidence, :>=, 0.0
    assert_operator r.confidence, :<=, 1.0
    assert_operator r.confidence, :>, 0.9, "an orbit-restoring fix should conserve Ξ"
  end

  # ---- multi-submission board (複数投稿) ----

  def test_repository_accepts_many_submissions
    repo = CF::Repository.new
    repo.submit("def a\n  1\nend\n", name: "one.rb", language: :ruby)
    repo.submit("def b(x\n  x\nend\n", name: "two.rb", language: :ruby)
    repo.submit("print(1)\n", name: "three.py", language: :python)
    assert_equal 3, repo.submissions.length
    assert_equal 2, repo.clean_count # one.rb and three.py close their orbits
    assert_operator repo.total_issues, :>=, 1
    assert_kind_of String, repo.report
    # every submission is written into the Akashic TupleSpace
    assert_equal 3, repo.space.size
  end

  def test_submit_many
    repo = CF::Repository.new
    repo.submit_many([
      { source: "def a\n  1\nend\n", name: "a.rb", language: :ruby },
      { source: "x = [1, 2", name: "b.rb", language: :ruby }
    ])
    assert_equal 2, repo.submissions.length
  end

  private

  def assert_syntax_ok(ruby_source)
    require "tempfile"
    Tempfile.create(["fix", ".rb"]) do |f|
      f.write(ruby_source)
      f.flush
      out = `ruby -c #{f.path} 2>&1`
      assert_match(/Syntax OK/, out, "fixed source should parse:\n#{ruby_source}\n#{out}")
    end
  end
end
