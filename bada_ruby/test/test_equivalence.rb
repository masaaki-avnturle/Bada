# frozen_string_literal: true
# encoding: utf-8

require "minitest/autorun"
require "bada/equivalence"
require "bada/language"

# Bada::Equivalence（等価原理・半減期・トポロジー）と、
# Bada 言語の拡張（算術式・関数呼び出し・repeat ブロック）のテスト。
class TestEquivalence < Minitest::Test
  E = Bada::Equivalence

  # ---- 等価原理 ------------------------------------------------------------

  def test_acceleration_is_g_when_masses_are_equivalent
    # m_g/m_i = 1 なら落下加速度は g そのもの
    assert_in_delta 9.80665, E.acceleration(9.80665, 1.0, 1.0), 1e-12
    assert_in_delta 9.80665, E.acceleration(9.80665, 7.0, 7.0), 1e-12
  end

  def test_acceleration_rejects_zero_inertial_mass
    assert_raises(ArgumentError) { E.acceleration(9.8, 1.0, 0.0) }
  end

  def test_eotvos_is_zero_under_the_equivalence_principle
    a1 = E.acceleration(9.80665, 1.0, 1.0)
    a2 = E.acceleration(9.80665, 7.0, 7.0)
    assert_in_delta 0.0, E.eotvos(a1, a2), 1e-15
    assert_in_delta 0.0, E.eotvos_ratio(1.0, 1.0, 2.0, 2.0), 1e-15
  end

  def test_eotvos_recovers_the_size_of_a_violation
    # m_g/m_i を 1e-3 ずらすと eta も 1e-3 のオーダーで出る
    eta = E.eotvos_ratio(1.0, 1.0, 1.001, 1.0)
    assert_in_delta(-1.0e-3, eta, 1e-6)
  end

  def test_free_fall_trajectory_is_mass_independent
    x1, v1 = E.free_fall(9.80665, 1.0, 1.0, 3.0)
    x2, v2 = E.free_fall(9.80665, 7.0, 7.0, 3.0)
    assert_in_delta x1, x2, 1e-12
    assert_in_delta v1, v2, 1e-12
    # x = 1/2 g t^2
    assert_in_delta 0.5 * 9.80665 * 9.0, x1, 1e-9
  end

  def test_redshift_matches_gh_over_c_squared
    c = 299_792_458.0
    assert_in_delta 9.80665 * 100 / (c * c), E.redshift(9.80665, 100), 1e-24
  end

  # ---- 半減期 --------------------------------------------------------------

  def test_decay_constant_and_half_life_are_inverses
    [1.0, 5.0, 10.0, 1234.5].each do |th|
      assert_in_delta th, E.half_life(E.decay_constant(th)), 1e-9
    end
    assert_in_delta Math.log(2) / 10.0, E.decay_constant(10.0), 1e-12
  end

  def test_decay_constant_rejects_nonpositive_half_life
    assert_raises(ArgumentError) { E.decay_constant(0.0) }
    assert_raises(ArgumentError) { E.half_life(-1.0) }
  end

  def test_remaining_fraction_halves_every_half_life
    (0..6).each do |k|
      assert_in_delta 2.0**(-k), E.remaining_fraction(10.0, 10.0 * k), 1e-12
    end
  end

  def test_decay_matches_the_exponential_law
    assert_in_delta 500.0, E.decay(1000.0, 10.0, 10.0), 1e-9
    assert_in_delta 250.0, E.decay(1000.0, 10.0, 20.0), 1e-9
  end

  def test_activity_is_lambda_times_n
    n = E.decay(1000.0, 10.0, 7.0)
    assert_in_delta E.decay_constant(10.0) * n, E.activity(1000.0, 10.0, 7.0), 1e-9
  end

  def test_decay_chain_conserves_total_mass
    [0.0, 1.0, 5.0, 25.0, 200.0].each do |t|
      out = E.decay_chain([5.0, 15.0, nil], 1000.0, t)
      assert_in_delta 1000.0, out.sum, 1e-6, "total not conserved at t=#{t}"
      out.each { |v| assert_operator v, :>=, -1e-9 }
    end
  end

  def test_decay_chain_starts_with_all_parent
    out = E.decay_chain([5.0, 15.0, nil], 1000.0, 0.0)
    assert_in_delta 1000.0, out[0], 1e-9
    assert_in_delta 0.0, out[1], 1e-9
    assert_in_delta 0.0, out[2], 1e-9
  end

  def test_decay_chain_parent_follows_simple_exponential
    # 親は娘の存在に関係なく単純な指数崩壊
    out = E.decay_chain([5.0, 15.0, nil], 1000.0, 5.0)
    assert_in_delta 500.0, out[0], 1e-6
  end

  def test_daughter_peaks_at_the_analytic_time
    # A→B の娘が最大になるのは t = ln(λA/λB)/(λA−λB)
    la = E.decay_constant(5.0)
    lb = E.decay_constant(15.0)
    t_peak = Math.log(la / lb) / (la - lb)
    peak = E.decay_chain([5.0, 15.0, nil], 1000.0, t_peak)[1]
    [-1.0, 1.0].each do |d|
      other = E.decay_chain([5.0, 15.0, nil], 1000.0, t_peak + d)[1]
      assert_operator peak, :>, other
    end
  end

  def test_secular_equilibrium_ratio
    assert_in_delta 0.001, E.secular_equilibrium_ratio(10_000.0, 10.0), 1e-12
  end

  # ---- トポロジー ----------------------------------------------------------

  def test_mobius_double_cover
    assert_equal(-1, E.mobius_orientation(1))
    assert_equal 1, E.mobius_orientation(2)
    refute E.orientable_return?(3)
    assert E.orientable_return?(4)
  end

  def test_platonic_solids_all_have_euler_characteristic_two
    # 球面と同相なので、どれも chi = 2（位相不変量）
    assert_equal 2, E.euler_characteristic(4, 6, 4)     # 正四面体
    assert_equal 2, E.euler_characteristic(8, 12, 6)    # 立方体
    assert_equal 2, E.euler_characteristic(6, 12, 8)    # 正八面体
    assert_equal 2, E.euler_characteristic(20, 30, 12)  # 正十二面体
    assert_equal 2, E.euler_characteristic(12, 30, 20)  # 正二十面体
  end

  def test_genus_to_euler
    assert_equal 2, E.genus_to_euler(0)   # 球面
    assert_equal 0, E.genus_to_euler(1)   # トーラス
    assert_equal(-2, E.genus_to_euler(2))
  end

  def test_mobius_band_is_not_a_disk
    assert_equal 0, E.mobius_euler
    refute_equal E.mobius_euler, E.euler_characteristic(1, 1, 1)
  end

  def test_winding_number
    # 2 周ぶんの角度列 → 巻き数 2
    angles = (0..64).map { |i| 2 * Math::PI * i / 64.0 * 2 }
    assert_in_delta 2.0, E.winding_number(angles), 1e-9
    # 逆回りは -1
    back = (0..32).map { |i| -2 * Math::PI * i / 32.0 }
    assert_in_delta(-1.0, E.winding_number(back), 1e-9)
  end

  # ---- Γ 多様体との対応 ----------------------------------------------------

  def test_gamma_invariance_holds_to_machine_precision
    [1.5, 2.5, 3.7, 5.0].each do |s|
      assert_operator E.gamma_invariance_defect(s), :<, 1e-12
    end
  end

  # ---- Bada 言語の拡張 -----------------------------------------------------

  def run_bada(src)
    Bada::Interpreter.new.run(src).join("\n")
  end

  def test_language_arithmetic
    assert_equal "7", run_bada("print 1 + 2 * 3")
    assert_equal "9", run_bada("print (1 + 2) * 3")
    assert_equal "8", run_bada("print 2 ^ 3")
    assert_equal "-5", run_bada("print -5")
    assert_equal "0.5", run_bada("print 1 / 2")
  end

  def test_language_let_and_variables
    assert_equal "12", run_bada("let a = 3\nlet b = 4\nprint a * b")
  end

  def test_language_function_calls
    assert_equal "24", run_bada("print gamma(5)")
    assert_equal "4", run_bada("print sqrt(16)")
    assert_equal "0", run_bada("print eotvos(accel(9.8, 1, 1), accel(9.8, 5, 5))")
  end

  def test_language_repeat_block
    out = Bada::Interpreter.new.run("repeat 3 as k\n  print k\nend")
    assert_equal %w[0 1 2], out
  end

  def test_language_nested_repeat
    out = Bada::Interpreter.new.run(
      "repeat 2 as i\n  repeat 2 as j\n    print i * 10 + j\n  end\nend"
    )
    assert_equal %w[0 1 10 11], out
  end

  def test_language_print_with_mixed_parts
    assert_equal "eta = 0", run_bada('print "eta = ", eotvos(1.0, 1.0)')
  end

  def test_language_division_by_zero_is_reported
    err = assert_raises(RuntimeError) { run_bada("print 1 / 0") }
    assert_match(/division by zero/, err.message)
  end

  def test_language_unknown_function_is_reported
    err = assert_raises(RuntimeError) { run_bada("print nope(1)") }
    assert_match(/unknown function/, err.message)
  end

  def test_language_missing_end_is_reported
    err = assert_raises(RuntimeError) { run_bada("repeat 2 as k\n  print k") }
    assert_match(/missing 'end'/, err.message)
  end

  # 旧来の書き方が壊れていないこと（後方互換）
  def test_language_backward_compatibility
    out = Bada::Interpreter.new.run(<<~BADA)
      set g = 2.5
      g <- "global differential manifold entropy"
      print g
      g -< 3.0
      g >- g
      Omega::push g as manifold_node
    BADA
    assert_equal 2, out.length
    assert_match(/\AΩ::push manifold_node/, out.last)
  end

  # ---- .bada スクリプトが最後まで走ること --------------------------------

  def test_example_scripts_run
    root = File.expand_path("..", __dir__)
    %w[equivalence.bada halflife.bada topology.bada].each do |name|
      src = File.read(File.join(root, "examples", name))
      out = Bada::Interpreter.new.run(src)
      refute_empty out, "#{name} produced no output"
    end
  end
end
