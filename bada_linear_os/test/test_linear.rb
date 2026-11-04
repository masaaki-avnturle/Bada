# frozen_string_literal: true
# ruby -Ilib test/test_linear.rb
require "minitest/autorun"
require "badalinear"

class TestGuideway < Minitest::Test
  G = BadaLinear::Guideway

  def test_levitates_at_rest_without_superconductors
    assert G.lift_ratio > 1.0, "揚力比 L>1（速度に依らず浮上）"
    assert G.levitation_force > G::TRAIN[:mass] * 9.80665
  end

  def test_drag_is_effectively_zero_under_envelope
    v = 1000.0 / 3.6
    assert G.base_drag(v) > 1e4, "底空間の空気抵抗は大きい"
    assert G.effective_drag(v, 4.0) < 10.0, "包絡後の残存抗力は実質ゼロ"
    assert G.drag_suppression(4.0) < 1e-4
    assert G.drag_suppression(5.0) < G.drag_suppression(4.0), "x_env で単調に抑制"
  end

  def test_travel_time_matches_l0_schedule
    # 品川–名古屋 285.6km を 500km/h：無停車台形モデルで約37分
    # （実運行計画の40分は途中停車・速度制限込み）
    t = G.travel_time_s(285.6, 500.0) / 60
    assert_in_delta 40.0, t, 5.0
    assert G.travel_time_s(285.6, 1000.0) < G.travel_time_s(285.6, 500.0)
  end

  def test_compare_reports_both_routes
    c = G.compare
    assert_equal 2, c.length
    assert c[0][:bada_drag_mwh] < c[0][:sc_drag_mwh] * 1e-3
  end

  def test_timetable_ends_at_shin_osaka
    rows = G.timetable(1000.0)
    assert_equal "新大阪", rows.last[1]
  end
end

class TestOS < Minitest::Test
  def setup; @os = BadaLinear::OS.new; @os.boot; end

  def test_boot_and_physics
    assert_match(/反重力リニア/, @os.boot)
    assert_match(/補空間包絡/, @os.command("physics"))
  end

  def test_depart_advances_to_next_station
    out = @os.command("depart 1000")
    assert_match(/神奈川県/, out)
    assert_match(/車掌AI/, out)
    assert @os.pos_km > 0
  end

  def test_compare_and_route
    assert_match(/L0/, @os.command("compare"))
    assert_match(/新大阪/, @os.command("route 1000"))
  end

  def test_ask_records_to_akashic
    @os.command("ask 浮上の原理は？")
    assert_match(/Ω::DATABASE/, @os.command("akashic ask"))
  end

  def test_envelope_setting
    assert_match(/σ=/, @os.command("envelope 3"))
  end
end
