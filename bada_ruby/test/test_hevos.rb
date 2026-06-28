# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

class TestHEVOSFuel < Minitest::Test
  def test_consume_draws_fuel
    t = Bada::HEVOS::FuelTank.new(capacity_l: 40.0, level_l: 40.0)
    t.consume(36.0, 100.0) # 36 L/h for 100 s = 1 L
    assert_in_delta 1.0, t.total_used_l, 1e-6
    assert_in_delta 39.0, t.level_l, 1e-6
  end

  def test_cannot_go_negative
    t = Bada::HEVOS::FuelTank.new(capacity_l: 40.0, level_l: 0.5)
    t.consume(100.0, 3600.0)
    assert t.empty?
    assert_operator t.level_l, :>=, 0.0
  end

  def test_refuel
    t = Bada::HEVOS::FuelTank.new(capacity_l: 40.0, level_l: 5.0)
    t.refuel
    assert_in_delta 40.0, t.level_l, 1e-6
  end
end

class TestHEVOSEngine < Minitest::Test
  def test_off_burns_no_fuel
    e = Bada::HEVOS::Engine.new
    assert_equal 0.0, e.run(0.0, 1.0)
    refute e.on
  end

  def test_running_burns_fuel_and_has_efficiency
    e = Bada::HEVOS::Engine.new
    lph = e.run(40.0, 1.0)
    assert e.on
    assert_operator lph, :>, 0.0
    assert_operator e.efficiency, :>, 0.12
    assert_operator e.efficiency, :<=, 0.38
  end

  def test_efficiency_peaks_mid_high_load
    e = Bada::HEVOS::Engine.new(max_power_kw: 73.0, peak_eff: 0.38)
    low = e.efficiency_for(7.3)    # 10% load
    mid = e.efficiency_for(55.0)   # ~75% load
    assert_operator mid, :>, low   # part-load is less efficient
  end
end

class TestHEVOSStrategy < Minitest::Test
  def setup
    @engine = Bada::HEVOS::Engine.new
    @ems = Bada::HEVOS::EnergyManagement.new(engine: @engine)
  end

  def test_braking_is_regen
    plan = @ems.decide(-30.0, 0.6, 20.0)
    assert_equal :regen, plan.mode
    assert_operator plan.battery_kw, :<, 0.0 # charging
    assert_equal 0.0, plan.engine_kw
  end

  def test_light_load_uses_electric
    plan = @ems.decide(1.0, 0.7, 8.0)
    assert_equal 0.0, plan.engine_kw
    assert_includes %i[ev coast idle], plan.mode
  end

  def test_low_soc_forces_charge
    # at the floor the manager must run the engine and recharge
    plan = @ems.decide(15.0, 0.44, 15.0)
    assert_operator plan.engine_kw, :>, 0.0
    assert_operator plan.battery_kw, :<, 0.0 # net charge
    assert_equal :charge, plan.mode
  end

  def test_high_demand_meets_power
    plan = @ems.decide(120.0, 0.7, 30.0)
    # engine alone can't deliver 120 kW; battery must assist (boost) or it is
    # at least engine-limited — wheel demand is met by engine + battery
    delivered = plan.engine_kw + [plan.motor_wheel_kw, 0.0].max
    assert_operator delivered, :>, @engine.max_power * 0.9
  end

  def test_equivalence_factor_responds_to_soc
    low = @ems.equivalence_factor(0.45)  # low SOC -> discourage discharge
    high = @ems.equivalence_factor(0.78) # high SOC -> cheap electricity
    assert_operator low, :>, high
  end
end

class TestHEVOSPowertrain < Minitest::Test
  def test_accelerates_from_rest
    soc = 0.6
    pt = Bada::HEVOS::HybridPowertrain.new(-> { soc })
    10.times { pt.apply(0.5, 1.0) }
    assert_operator pt.speed_kph, :>, 0.0
  end

  def test_no_chatter_at_charge_sustaining_floor
    soc = 0.6
    pt = Bada::HEVOS::HybridPowertrain.new(-> { soc })
    toggles = 0
    prev_on = false
    60.times do
      plan = pt.apply(0.15, 1.0)
      # drain the battery deterministically toward the floor
      soc = [soc - 0.004, 0.40].max
      on = plan.engine_kw > 0
      toggles += 1 if on != prev_on
      prev_on = on
    end
    # hysteresis must keep engine transitions rare, not once-per-tick
    assert_operator toggles, :<, 10
  end
end

class TestHEVOSVehicle < Minitest::Test
  def test_boot_and_drive
    hev = Bada::HEVOS::Vehicle.new.boot
    hev.drive(0.4)
    hev.run(ticks: 30)
    assert_operator hev.powertrain.speed_kph, :>, 0.0
    assert_operator hev.recorder.size, :>=, 1
    assert hev.dashboard.include?("BadaOS-HEV")
  end

  def test_engine_burns_fuel_over_a_trip
    hev = Bada::HEVOS::Vehicle.new(fuel_l: 40.0).boot
    hev.drive(0.6)
    hev.run(ticks: 60) # demand high enough to require the engine
    assert_operator hev.fuel.total_used_l, :>, 0.0
    assert_operator hev.fuel_economy, :>, 0.0
  end

  def test_regen_recovers_charge
    hev = Bada::HEVOS::Vehicle.new.boot
    hev.drive(0.8); hev.run(ticks: 15)
    low = hev.battery.soc
    hev.brake(0.7); hev.run(ticks: 12)
    assert_operator hev.battery.soc, :>, low
  end

  def test_fuel_empty_raises_critical_and_halts
    hev = Bada::HEVOS::Vehicle.new(fuel_l: 0.05).boot
    hev.drive(0.7)
    hev.run(ticks: 40)
    assert_includes hev.diagnostics.active_codes, :FUEL_EMPTY
    assert_operator hev.scheduler.tick, :<, 40
  end
end
