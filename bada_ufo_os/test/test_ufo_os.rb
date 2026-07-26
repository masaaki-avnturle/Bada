# frozen_string_literal: true

# BadaUFO-OS テスト:  ruby -Ilib test/test_ufo_os.rb
require "minitest/autorun"
require "badaufo"

class TestAntigravity < Minitest::Test
  include BadaUFO

  def test_gravity_energy_positive
    u = Antigravity.gravity_energy(5.972e24, 12_000.0, 6.371e6)
    assert u > 0, "重力エネルギーは正"
  end

  def test_antigravity_coupling_ge_one
    # α_ag(x) = cosh(x log x) >= 1 for x >= 1
    assert Antigravity.antigravity_coupling(1.0) >= 0.99
    assert Antigravity.antigravity_coupling(3.0) > Antigravity.antigravity_coupling(2.0),
           "反重力結合は多様体座標で単調増加"
  end

  def test_complementary_gravity_beats_gravity
    # 重力方程式の補空間（反重力場）は束縛重力を上回りうる
    big, m, r = 5.972e24, 12_000.0, 6.371e6
    e_ag = Antigravity.complementary_gravity_energy(big, m, r)
    u    = Antigravity.gravity_energy(big, m, r)
    assert e_ag >= u, "補空間エネルギー E_ag >= U_grav"
  end

  def test_relativity_complement_equals_formula
    m, v = 3.0, 100.0
    got = Antigravity.complementary_relativity_energy(m, v)
    want = m * Antigravity::C**2 - 0.5 * m * v**2
    assert_in_delta want, got, 1e-3, "E_⊥ = mc² − ½mv²"
  end

  def test_vacuum_energy_grows_inexhaustible
    # 真空エネルギー x^x は座標とともに増大（無尽蔵）
    assert Antigravity.vacuum_energy(3.0) > Antigravity.vacuum_energy(2.0)
  end

  def test_duality_gap_small
    d = Antigravity.duality
    assert d[:gap] < 1.0, "e^π ≈ π^e の双対ギャップは小さい (#{d[:gap]})"
  end
end

class TestVacuumReservoir < Minitest::Test
  def test_draw_never_depletes
    r = BadaUFO::VacuumReservoir.new(manifold_x: 3.0)
    before = r.level
    10.times { r.draw(before * 5) }        # 残量の5倍を10回引く
    assert r.level >= before * 0.999, "無尽蔵：引いても枯渇しない"
    assert r.drawn_total > 0
  end
end

class TestDrive < Minitest::Test
  def test_ascends_over_steps
    d = BadaUFO::AntigravityDrive.new
    start = d.altitude
    12.times { d.step(throttle: 1.0) }
    assert d.altitude > start, "反重力上昇で高度が増える"
    assert d.lift_ratio > 1.0, "揚力比 L>1"
  end
end

class TestOS < Minitest::Test
  def setup
    @os = BadaUFO::OS.new
    @banner = @os.boot
  end

  def test_boot_banner
    assert_match(/BadaUFO-OS/, @banner)
    assert_match(/e\^π/, @banner)
  end

  def test_physics_report
    out = @os.command("physics")
    assert_match(/補空間 反重力場/, out)
    assert_match(/相対論補空間/, out)
  end

  def test_ascend_changes_altitude
    @os.command("ascend 8")
    st = @os.command("status")
    assert_match(/高度/, st)
  end

  def test_ask_generates_and_records
    out = @os.command("ask 反重力とは？")
    assert_match(/操縦士AI/, out)
    ak = @os.command("akashic ask")
    assert_match(/アカシック|Ω::DATABASE/, ak)
  end

  def test_help
    assert_match(/status/, @os.command("help"))
  end
end
