# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

include Bada::Prover

class TestPolynomial < Minitest::Test
  def test_arithmetic
    a = Polynomial.from([1, 2]) # 1 + 2x
    b = Polynomial.from([0, 1]) # x
    assert_equal Polynomial.from([1, 3]), a + b
    assert_equal Polynomial.from([0, 1, 2]), a * b # x + 2x^2
  end

  def test_eval_exact
    p = Polynomial.from([0, Rational(1, 2), Rational(1, 2)]) # n/2 + n^2/2
    assert_equal Rational(3), p.eval(2) # 1 + 2 = 3
  end

  def test_interpolation_exact
    # points of x^2: (0,0),(1,1),(2,4)
    p = Polynomial.interpolate([[0, 0], [1, 1], [2, 4]])
    assert_equal Polynomial.from([0, 0, 1]), p
  end

  def test_shift
    p = Polynomial.from([0, 0, 1]) # x^2
    assert_equal Polynomial.from([1, -2, 1]), p.shift(-1) # (x-1)^2
  end
end

class TestSummation < Minitest::Test
  def test_sum_of_k
    f = Polynomial.from([0, 1]) # k
    c, ok, step = Summation.closed_form(f)
    assert ok
    assert step.zero?
    assert_equal Polynomial.from([0, Rational(1, 2), Rational(1, 2)]), c # n(n+1)/2
  end

  def test_sum_of_k_squared
    f = Polynomial.from([0, 0, 1]) # k^2
    c, ok, = Summation.closed_form(f)
    assert ok
    # n(n+1)(2n+1)/6 = 1/3 n^3 + 1/2 n^2 + 1/6 n
    assert_equal Polynomial.from([0, Rational(1, 6), Rational(1, 2), Rational(1, 3)]), c
  end
end

class TestIdentityProver < Minitest::Test
  def test_proves_true_identity
    f = Polynomial.from([0, 1]) # k
    rhs = Polynomial.from([0, Rational(1, 2), Rational(1, 2)]) # n(n+1)/2
    proof = IdentityProver.prove(f, rhs)
    assert proof.proved?
    assert_match(/帰納法/, proof.method)
  end

  def test_disproves_false_identity_with_counterexample
    f = Polynomial.from([0, 1])                      # k
    rhs = Polynomial.from([0, Rational(1, 2), 1])    # wrong
    proof = IdentityProver.prove(f, rhs)
    assert proof.disproved?
    refute_nil proof.counterexample
    # verify the counterexample is real
    n = proof.counterexample[:n]
    lhs = (1..n).sum { |k| f.eval(k) }
    refute_equal lhs, rhs.eval(n)
  end
end

class TestDivisibilityProver < Minitest::Test
  def test_proves_six_divides_n_cubed_minus_n
    e = Polynomial.from([0, -1, 0, 1]) # n^3 - n
    proof = DivisibilityProver.prove(e, 6)
    assert proof.proved?
    # spot check
    (1..20).each { |n| assert_equal 0, e.eval_int(n) % 6 }
  end

  def test_proves_fermat_little_theorem
    # p | n^p - n for prime p
    [2, 3, 5, 7].each do |p|
      e = Polynomial.from(Array.new(p + 1) { |i| i == p ? 1 : (i == 1 ? -1 : 0) })
      assert DivisibilityProver.prove(e, p).proved?, "Fermat failed for p=#{p}"
    end
  end

  def test_disproves_with_counterexample
    e = Polynomial.from([0, -1, 1]) # n^2 - n
    proof = DivisibilityProver.prove(e, 5)
    assert proof.disproved?
    r = proof.counterexample[:n]
    refute_equal 0, e.eval_int(r) % 5
  end
end

class TestEmpirical < Minitest::Test
  def test_collatz_open_not_proved
    proof = EmpiricalTester.test((1..50), description: "collatz") { |k| NT.collatz_reaches_one?(k) }
    assert proof.open? # honest: evidence, not proof
    refute proof.proved?
  end

  def test_empirical_finds_real_counterexample
    # "all n are even" is false at n=1
    proof = EmpiricalTester.test((0..10), description: "even") { |n| n.even? }
    assert proof.disproved?
    assert_equal 1, proof.counterexample[:x]
  end

  def test_finite_case_prover
    proof = FiniteCaseProver.prove((1..10), description: "n<100") { |n| n < 100 }
    assert proof.proved?
  end
end

class TestNT < Minitest::Test
  def test_prime
    assert NT.prime?(7)
    refute NT.prime?(9)
  end

  def test_goldbach_small
    primes = NT.primes_upto(100).to_set
    (4..100).step(2) { |e| assert NT.goldbach_holds?(e, primes), "Goldbach fails at #{e}" }
  end
end

class TestEngine < Minitest::Test
  def test_discover_spans_statuses
    eng = UnknownAprioriEngine.new
    results = eng.discover("未解決問題を想像して証明して", count: 5)
    assert_equal 5, results.length
    statuses = results.map { |r| r[:proof].status }.uniq
    assert_includes statuses, :proved
    assert_includes statuses, :disproved
  end

  def test_render_contains_soundness_note
    s = UnknownAprioriEngine.new.render("ガンマ関数の未解決問題", count: 5)
    assert_match(/証明完了|反証|未解決/, s)
    assert_match(/証拠であり証明ではない/, s)
  end

  def test_no_open_is_ever_marked_proved
    eng = UnknownAprioriEngine.new
    eng.discover(" random seed text", count: 5).each do |r|
      c = r[:conjecture]
      next unless c.kind == :open
      refute r[:proof].proved?, "an open problem was wrongly marked proved"
    end
  end

  def test_paper_generation
    eng = UnknownAprioriEngine.new
    c = eng.imagine("テスト", count: 5).first
    paper = eng.paper(c)
    assert_match(/健全性/, paper)
    assert_match(/\$\$/, paper)
  end

  def test_chat_discover_integration
    out = Bada::OmegaChat.new.discover("未解決問題を想像して", count: 5)
    assert_match(/未知事前エンジン/, out)
  end
end
