# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require "stringio"
require_relative "../lib/bada"

class TestDialectReviser < Minitest::Test
  def out(src, dialect:)
    Bada::Lang.run(src, out: StringIO.new, dialect: dialect).output
  end

  def test_japanese_keyword_variant
    ja = Bada::Lang.fork(name: "t-ja") do
      rename :def, "関数"
      rename :end, "終"
      rename :print, "表示"
      rename :return, "返す"
    end
    src = <<~BADA
      関数 sq(x)
        返す x * x
      終
      表示 str(sq(6))
    BADA
    assert_equal ["36"], out(src, dialect: ja)
  end

  def test_alias_keeps_original
    # alias adds a surface word without removing the original
    d = Bada::Lang.fork(name: "t-alias") { keyword "func", :def }
    src = "func a()\n  return 1\nend\nprint str(a())"
    assert_equal ["1"], out(src, dialect: d)
    # original 'def' still works too
    assert_equal ["2"], out("def b()\n return 2\nend\nprint str(b())", dialect: d)
  end

  def test_builtin_overlay
    d = Bada::Lang.fork(name: "t-bi") { builtin("twice") { |x| x * 2 } }
    assert_equal ["10"], out("print str(twice(5))", dialect: d)
  end

  def test_prelude_runs_first
    d = Bada::Lang.fork(name: "t-pre") do
      prelude "def greet(n)\n  return \"hi \" + n\nend"
    end
    assert_equal ["hi bada"], out('print greet("bada")', dialect: d)
  end

  def test_branch_genealogy_tree
    root = Bada::Lang::Dialect.new(name: "r")
    a = Bada::Lang::Reviser.fork(name: "a", parent: root)
    b = Bada::Lang::Reviser.fork(name: "b", parent: a)
    assert_equal %w[r a b], b.lineage.map(&:name)
    assert_includes root.descendants, b
    tree = root.render_tree
    assert_match(/● r/, tree)
    assert_match(/● b/, tree)
  end

  def test_child_inherits_parent_revisions
    parent = Bada::Lang.fork(name: "p-inh") { builtin("base") { |x| x } }
    child = Bada::Lang.fork(name: "c-inh", parent: parent) { builtin("extra") { |x| x + 1 } }
    # child has both base (inherited) and extra
    assert_equal ["7"], out("print str(base(7))", dialect: child)
    assert_equal ["8"], out("print str(extra(7))", dialect: child)
    # diff shows only the child's own change
    assert(child.diff_from_parent.any? { |r| r.include?("extra") })
    refute(child.diff_from_parent.any? { |r| r.include?("base") })
  end

  def test_each_variant_has_manifold_invariant_and_signature
    a = Bada::Lang.fork(name: "inv-a") { rename :print, "表示" }
    b = Bada::Lang.fork(name: "inv-b") { rename :print, "出力" }
    # the manifold invariant is the branch's real-valued identity "trigger"
    assert a.invariant.finite?
    assert_operator a.invariant, :>, 0.0
    assert b.invariant.finite?
    # signatures are the structural (exact) identity and must differ
    refute_equal a.signature, b.signature
  end

  def python?
    system("python3", "--version", out: File::NULL, err: File::NULL)
  end

  def test_dialect_bakes_in_ruby_library
    d = Bada::Lang.fork(name: "sci-rb") { ruby "Math", as: "M" }
    # program needs no import; the library is pre-loaded by the dialect
    assert_equal ["3"], out("print str(M.sqrt(9))", dialect: d)
  end

  def test_dialect_foreign_recorded_and_inherited
    parent = Bada::Lang.fork(name: "p-frn") { ruby "Math", as: "RM" }
    child = Bada::Lang.fork(name: "c-frn", parent: parent) { ruby "Comparable", as: "Cmp" }
    assert_includes parent.foreign, %w[ruby Math RM]
    # child inherits parent's foreign + its own
    assert_includes child.foreign, %w[ruby Math RM]
    assert_includes child.foreign, %w[ruby Comparable Cmp]
    assert_equal ["4"], out("print str(RM.sqrt(16))", dialect: child) # inherited lib works
  end

  def test_dialect_generic_foreign_spec
    d = Bada::Lang.fork(name: "gen-frn") { foreign "ruby:Math as MM" }
    assert_equal ["5"], out("print str(MM.hypot(3, 4))", dialect: d)
  end

  def test_dialect_bakes_in_python_library
    skip "python3 not available" unless python?
    d = Bada::Lang.fork(name: "sci-py") { python "statistics", as: "S" }
    assert_equal ["20"], out("print str(S.mean([10, 20, 30]))", dialect: d)
  end

  def test_foreign_changes_dialect_signature
    a = Bada::Lang.fork(name: "siga") { ruby "Math", as: "M" }
    b = Bada::Lang.fork(name: "sigb") { ruby "Comparable", as: "M" }
    refute_equal a.signature, b.signature
  end

  def test_base_dialect_unaffected_by_forks
    Bada::Lang.fork(name: "throwaway") { rename :def, "関数" }
    # base still uses 'def'
    assert_equal ["3"], out("def f()\n return 3\nend\nprint str(f())", dialect: Bada::Lang::Dialect.base)
  end
end
