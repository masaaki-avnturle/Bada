# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require "stringio"
require_relative "../lib/bada"

# These tests prove the pure-Bada standard library (bada/std/*.bada) computes
# correctly — i.e. the algorithms are genuinely implemented in the Bada language.
class TestBadaStdLib < Minitest::Test
  # Run Bada source, return the printed lines.
  def out(src)
    Bada::Lang.run(src, out: StringIO.new).output
  end

  def num(src)
    out("print str(#{src})").first.to_f
  end

  def with(import, expr)
    out(%(import "#{import}"\nprint str(#{expr}))).first
  end

  def test_special_gamma_beta
    assert_in_delta 24.0, with("std/special.bada", "Special.gamma(5)").to_f, 1e-4
    # str() prints 6 significant figures, so compare at display precision
    assert_in_delta Math::PI, with("std/special.bada", "Special.gamma(0.5) * Special.gamma(0.5)").to_f, 1e-4
    assert_in_delta 1.0 / 12.0, with("std/special.bada", "Special.beta(2, 3)").to_f, 1e-6
  end

  def test_entropy_uniform
    # uniform over 4 -> H = 2 bits
    v = with("std/entropy.bada", "Entropy.shannon([0.25, 0.25, 0.25, 0.25])").to_f
    assert_in_delta 2.0, v, 1e-9
  end

  def test_manifold_invariant_finite
    v = with("std/manifold.bada", "Mani.invariant([0.5, 0.25, 0.25])").to_f
    assert v.finite?
    assert_operator v, :>, 0.0
  end

  def test_catastrophe_cubic_roots
    # x^3 - 3x = 0 -> roots {-√3, 0, √3}
    s = with("std/catastrophe.bada", "Cat.roots(-3, 0)")
    roots = s.gsub(/[\[\]]/, "").split(",").map(&:to_f).sort
    assert_in_delta(-Math.sqrt(3), roots[0], 1e-6)
    assert_in_delta 0.0, roots[1], 1e-6
    assert_in_delta Math.sqrt(3), roots[2], 1e-6
  end

  def test_polynomial_eval
    # E = x^3 - x at n=4 -> 60
    v = with("std/polynomial.bada", "Poly.eval([0, -1, 0, 1], 4)").to_f
    assert_in_delta 60.0, v, 1e-9
  end

  def test_prover_fermat_proved
    src = <<~BADA
      import "std/prover.bada"
      import "std/polynomial.bada"
      print str(Prove.divides_all(Poly.power_minus_x(7), 7))
    BADA
    assert_equal(-1, out(src).first.to_i) # -1 == proved for all n
  end

  def test_prover_disproof_counterexample
    src = <<~BADA
      import "std/prover.bada"
      print str(Prove.divides_all([0, -1, 1], 5))
    BADA
    # 5 | n^2 - n is false; least residue counterexample is 2
    assert_equal 2, out(src).first.to_i
  end

  def test_prover_six_divides_n_cubed_minus_n
    src = <<~BADA
      import "std/prover.bada"
      import "std/polynomial.bada"
      print str(Prove.divides_all(Poly.power_minus_x(3), 6))
    BADA
    assert_equal(-1, out(src).first.to_i)
  end

  def test_basal_selects_highest_salience
    v = with("std/basal.bada", "BG.select([0.2, 0.9, 0.5, 0.1])").to_i
    assert_equal 1, v
  end

  def test_flow_mapreduce_directive
    # Σ k^2 (k=1..5) via branch (-<) then merge (>-) = 55
    src = <<~BADA
      import "std/flow.bada"
      print str(Flow.mapreduce([1, 2, 3, 4, 5],
        def(x) return x * x end,
        def(a, b) return a + b end))
    BADA
    assert_equal ["55"], out(src)
  end

  def test_flow_zip_parallel_lanes
    # dot product via parallel lane combine (zip) then merge (sum) = 32
    src = <<~BADA
      import "std/flow.bada"
      print str(Flow.zipreduce([1, 2, 3], [4, 5, 6],
        def(a, b) return a * b end,
        def(a, b) return a + b end))
    BADA
    assert_equal ["32"], out(src)
  end

  def test_gamma_still_exact_after_flow_lanczos
    assert_in_delta 24.0, with("std/special.bada", "Special.gamma(5)").to_f, 1e-4
    assert_in_delta 1.0 / 12.0, with("std/special.bada", "Special.beta(2, 3)").to_f, 1e-6
  end

  def test_std_entropy_uses_directives
    # the directive-rewritten Entropy still computes H correctly
    v = with("std/entropy.bada", "Entropy.shannon([0.25, 0.25, 0.25, 0.25])").to_f
    assert_in_delta 2.0, v, 1e-9
  end

  def test_full_native_engine_app
    app = File.expand_path("../bada/app/native_engine.bada", __dir__)
    joined = Bada::Lang.run_file(app, out: StringIO.new).output.join("\n")
    assert_match(/Γ\(5\)\s+= 24/, joined)
    assert_match(/証明完了/, joined)
    assert_match(/反証 \(反例 n=2\)/, joined)
    assert_match(/選択チャネル 1/, joined)
    assert_match(/Σ k\^2 \(k=1\.\.5\) を分岐→合流で = 55/, joined)
  end
end
