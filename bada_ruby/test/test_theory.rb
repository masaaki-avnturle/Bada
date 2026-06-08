# encoding: UTF-8
# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

class TestThurston < Minitest::Test
  def test_eight_geometries
    assert_equal 8, Bada::Thurston.geometries.length
    assert_includes Bada::Thurston.geometries.map { |g| g[:name] }, "S^3"
    assert_includes Bada::Thurston.geometries.map { |g| g[:name] }, "H^1"
  end

  def test_place_entropy_lands_on_a_geometry
    r = Bada::Thurston.place_entropy("ガンマ関数 ゼータ 多様体 エントロピー 不変量")
    assert_includes Bada::Thurston.geometries.map { |g| g[:name] }, r[:geometry]
    assert r[:perelman_f].finite?
    assert r[:entropy] >= 0.0
  end

  def test_spherical_ricci_flow_collapses
    # positive curvature (S^3-like) collapses in finite time
    flow = Bada::Thurston.ricci_flow(1.0, g0: 1.0, dt: 0.05, steps: 100)
    assert flow[:collapsed]
  end

  def test_hyperbolic_ricci_flow_expands
    flow = Bada::Thurston.ricci_flow(-1.0, g0: 1.0, dt: 0.05, steps: 20)
    refute flow[:collapsed]
    assert_operator flow[:final], :>, 1.0
  end
end

class TestCatastrophe < Minitest::Test
  def test_seven_elementary_catastrophes
    assert_equal 7, Bada::Catastrophe.catalog.length
    assert_includes Bada::Catastrophe.catalog.map { |c| c[:key] }, :cusp
  end

  def test_cubic_three_real_roots
    # x^3 - 3x = 0 -> roots -√3, 0, √3
    roots = Bada::Catastrophe.cubic_real_roots(-3.0, 0.0)
    assert_equal 3, roots.length
    assert_in_delta(-Math.sqrt(3), roots[0], 1e-6)
    assert_in_delta 0.0, roots[1], 1e-6
    assert_in_delta Math.sqrt(3), roots[2], 1e-6
  end

  def test_cubic_one_real_root
    # x^3 + x + 1 = 0 has a single real root
    roots = Bada::Catastrophe.cubic_real_roots(1.0, 1.0)
    assert_equal 1, roots.length
    x = roots[0]
    assert_in_delta 0.0, x**3 + x + 1.0, 1e-6
  end

  def test_cusp_bifurcation_on_curve
    # on the cusp curve 4a^3 + 27b^2 = 0 -> on_bifurcation true
    a = -3.0
    b = Math.sqrt(-4 * a**3 / 27.0)
    state = Bada::Catastrophe.cusp(a, b)
    assert state[:on_bifurcation]
  end

  def test_decompose_produces_branches
    d = Bada::Catastrophe.decompose("サーストン ペレルマン 多様体 エントロピー 不変量 ガンマ")
    assert_operator d[:branch_count], :>=, 1
    assert(d[:branches].all? { |b| b[:target_h] > 0 })
  end
end

class TestMillennium < Minitest::Test
  def test_seven_problems
    assert_equal 7, Bada::Millennium.problems.length
  end

  def test_decompose_ranks_poincare_for_thurston_question
    m = Bada::Millennium.decompose_theory("サーストン・ペレルマン多様体のリッチフロー幾何化")
    assert_match(/Poincaré/, m[:dominant])
  end

  def test_decompose_ranks_riemann_for_zeta_question
    m = Bada::Millennium.decompose_theory("リーマン予想 ゼータ関数 素数 ガンマ")
    assert_match(/Riemann/, m[:dominant])
  end

  def test_origin_is_gamma_manifold
    m = Bada::Millennium.decompose_theory("ミレニアム")
    assert_match(/ガンマ関数/, m[:origin])
    assert_equal 7, m[:decomposition].length
  end
end

class TestInfoEngine < Minitest::Test
  def test_generate_structure
    eng = Bada::InfoEngine.new(seed: 1)
    r = eng.generate("クレイ7問とサーストン・ペレルマン多様体のエントロピー", branch_length: 8)
    assert r[:placement][:geometry].is_a?(String)
    assert_operator r[:branches].length, :>=, 1
    assert(r[:branches].all? { |b| b[:text].is_a?(String) })
    assert_equal 7, r[:millennium][:decomposition].length
  end

  def test_render_runs
    eng = Bada::InfoEngine.new(seed: 2)
    s = eng.render("ガンマ関数の大域的部分積分多様体からの理論分解", branch_length: 6)
    assert_match(/サーストン・ペレルマン多様体/, s)
    assert_match(/カタストロフィ/, s)
    assert_match(/ミレニアム/, s)
  end
end
