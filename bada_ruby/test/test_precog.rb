# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

class TestMillenniumAnalysis < Minitest::Test
  def test_analyze_riemann_is_dominant
    r = Bada::Millennium.analyze("リーマン予想 ゼータ関数 素数 zeta riemann prime")
    assert_equal "Riemann Hypothesis", r[:dominant]
    refute_nil r[:dominant_resolution]
    assert_in_delta 1.0, r[:engine][:base_distribution].sum, 1e-9
  end

  def test_analyze_poincare_for_thurston_question
    r = Bada::Millennium.analyze("ポアンカレ予想 サーストン ペレルマン リッチ流 poincare thurston perelman ricci")
    assert_equal "Poincaré Conjecture (解決)", r[:dominant]
  end

  def test_analyze_preserves_engine_theorems
    r = Bada::Millennium.analyze("P vs NP 計算複雑性 entropy")
    assert_operator r[:engine][:max_prob_deviation], :<, 1e-9
    assert r[:engine][:zeros_preserved]
    assert_equal 7, r[:posterior].length
  end
end

class TestPrecog < Minitest::Test
  def setup
    @p = Bada::Precog.new(seed: 42)
    @p.learn(<<~TXT, source: "t")
      ζ(s) = β(p,q)/log x はゼータ関数とベータ関数を結ぶ。
      大域的部分積分多様体 ∬ 1/(x log x)^2 dx_m はガンマ関数に根ざす。
      シャノンエントロピー H = -Σ p log p は情報量である。
    TXT
  end

  def test_foresee_returns_full_structure
    r = @p.foresee("ゼータ関数の素数分布", shots: 16)
    assert_operator r[:question_entropy], :>, 0.0
    assert r[:hypotheses].length.positive?
    # engine theorems hold inside the precognition
    assert_operator r[:engine][:max_prob_deviation], :<, 1e-9
    assert r[:engine][:zeros_preserved]
    assert_equal "Riemann Hypothesis", r[:millennium][:dominant]
  end

  def test_reviser_loop_sharpens_prior
    r = @p.foresee("情報量とエントロピー", shots: 64)
    rl = r[:revision]
    assert_operator rl[:prior_entropy_after], :<=, rl[:prior_entropy_before] + 1e-9
    assert rl[:entropy_decreased]
  end

  def test_quantum_foresight_is_normalised
    r = @p.foresee("量子計算", shots: 8)
    assert_in_delta 1.0, r[:quantum][:norm], 1e-9
  end

  def test_default_grammar_is_installed
    assert_operator @p.rules.size, :>=, 4
  end

  def test_ask_renders_string
    s = @p.ask("リーマン予想")
    assert_includes s, "未知事前予知エンジン"
    assert_includes s, "ミレニアム予想分析"
  end
end
