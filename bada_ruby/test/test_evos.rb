# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/bada"

class TestEVOSKernel < Minitest::Test
  def test_scheduler_runs_by_priority_and_period
    log = []
    s = Bada::EVOS::Scheduler.new
    s.every("fast", period: 1, priority: 10) { |_, t| log << [:fast, t] }
    s.every("slow", period: 3, priority: 5)  { |_, t| log << [:slow, t] }
    s.run(nil, ticks: 3)
    # fast runs every tick, slow only on tick 0 (period 3)
    assert_equal 3, log.count { |e| e.first == :fast }
    assert_equal 1, log.count { |e| e.first == :slow }
  end

  def test_priority_ordering_within_tick
    order = []
    s = Bada::EVOS::Scheduler.new
    s.every("low", priority: 1)  { |_, _| order << :low }
    s.every("high", priority: 9) { |_, _| order << :high }
    s.step(nil)
    assert_equal %i[high low], order
  end
end

class TestEVOSSensor < Minitest::Test
  def test_error_correction_damps_spike
    s = Bada::EVOS::Sensor.new("current", unit: "A")
    [100.0, 101.0, 99.0, 100.5, 800.0, 100.0, 99.5, 100.2].each { |x| s.feed(x) }
    # the 800 A spike must be damped toward the cluster (~100)
    assert_operator s.value, :<, 200.0
    assert_operator s.value, :>, 50.0
  end

  def test_clean_signal_is_healthy
    s = Bada::EVOS::Sensor.new("v")
    8.times { s.feed(380.0) }
    assert s.healthy?
  end
end

class TestEVOSBattery < Minitest::Test
  def test_discharge_lowers_soc
    b = Bada::EVOS::BatteryPack.new(capacity_kwh: 60.0)
    soc0 = b.soc
    b.update(90.0, 10.0) # 90 kW for 10 s
    assert_operator b.soc, :<, soc0
  end

  def test_charge_raises_soc
    b = Bada::EVOS::BatteryPack.new(capacity_kwh: 60.0)
    soc0 = b.soc
    b.update(-50.0, 10.0) # negative power = charge
    assert_operator b.soc, :>, soc0
  end

  def test_balancing_reduces_imbalance
    b = Bada::EVOS::BatteryPack.new(capacity_kwh: 60.0)
    # drive the pack so cells diverge, then balance repeatedly
    20.times { b.update(120.0, 5.0) }
    before = b.imbalance
    200.times { b.balance! }
    assert_operator b.imbalance, :<=, before
  end

  def test_voltage_in_plausible_range
    b = Bada::EVOS::BatteryPack.new(series: 96)
    assert_operator b.voltage(0.0), :>, 300.0
    assert_operator b.voltage(0.0), :<, 420.0
  end
end

class TestEVOSPowertrain < Minitest::Test
  def test_throttle_accelerates
    p = Bada::EVOS::Powertrain.new
    10.times { p.apply(0.5, 1.0) }
    assert_operator p.speed_kph, :>, 0.0
    assert_operator p.power_kw, :>, 0.0
  end

  def test_regen_returns_power
    p = Bada::EVOS::Powertrain.new
    10.times { p.apply(0.8, 1.0) } # get moving
    p.apply(-0.5, 1.0)             # brake
    assert_operator p.power_kw, :<, 0.0 # negative = energy back to pack
  end

  def test_efficiency_uses_x_log_x_curve
    p = Bada::EVOS::Powertrain.new
    p.apply(0.5, 1.0)
    assert_operator p.efficiency, :>=, 0.78
    assert_operator p.efficiency, :<=, 0.96
  end
end

class TestEVOSCharger < Minitest::Test
  def test_cc_cv_taper
    c = Bada::EVOS::Charger.new
    b = Bada::EVOS::BatteryPack.new(capacity_kwh: 60.0)
    c.plug(:dc)
    p_cc = c.charge(b, 1.0)        # below knee -> full power
    # push past the CV knee
    b.cells.each { |cell| cell.soc = 0.95 }
    p_cv = c.charge(b, 1.0)        # above knee -> tapered
    assert_operator p_cv, :<, p_cc
  end

  def test_unplug_stops_charge
    c = Bada::EVOS::Charger.new
    c.plug(:ac)
    assert c.plugged?
    c.unplug
    refute c.plugged?
    assert_equal 0.0, c.charge(Bada::EVOS::BatteryPack.new, 1.0)
  end
end

class TestEVOSDiagnostics < Minitest::Test
  def test_overtemp_raises_critical_fault
    ev = Bada::EVOS::Vehicle.new.boot
    ev.battery.cells.each { |c| c.temp = 60.0 }
    ev.diagnostics.evaluate(ev, 1)
    assert ev.diagnostics.critical?
    assert_includes ev.diagnostics.active_codes, :PACK_OVERTEMP
  end

  def test_edge_triggered_clear
    ev = Bada::EVOS::Vehicle.new.boot
    ev.battery.cells.each { |c| c.temp = 60.0 }
    ev.diagnostics.evaluate(ev, 1)
    assert ev.diagnostics.critical?
    ev.battery.cells.each { |c| c.temp = 25.0 }
    ev.diagnostics.evaluate(ev, 2)
    refute ev.diagnostics.critical?
  end
end

class TestEVOSRecorder < Minitest::Test
  def test_logs_to_tuplespace
    r = Bada::EVOS::Recorder.new
    r.log("boot sequence complete")
    r.log("charge start dc")
    assert_equal 2, r.size
    assert r.recent_invariant.finite?
    assert_equal 2, r.tail.length
  end
end

class TestEVOSVehicle < Minitest::Test
  def test_boot_and_drive_cycle
    ev = Bada::EVOS::Vehicle.new(capacity_kwh: 60.0).boot
    soc0 = ev.battery.soc
    ev.drive(0.4)
    ev.run(ticks: 20)
    assert_operator ev.powertrain.speed_kph, :>, 0.0
    assert_operator ev.battery.soc, :<, soc0           # consumed energy
    assert_operator ev.recorder.size, :>=, 1           # black box populated
    assert ev.dashboard.include?("BadaOS-EV")
  end

  def test_charge_recovers_soc
    ev = Bada::EVOS::Vehicle.new.boot
    ev.drive(0.6); ev.run(ticks: 25)
    low = ev.battery.soc
    ev.plug_in(:dc); ev.run(ticks: 40)
    assert_operator ev.battery.soc, :>, low
  end

  def test_run_halts_on_critical_fault
    ev = Bada::EVOS::Vehicle.new.boot
    ev.battery.cells.each { |c| c.temp = 70.0 } # force overtemp
    ev.drive(0.5)
    ev.run(ticks: 50)
    # the safety loop must stop the drive well before 50 ticks of damage
    assert_operator ev.scheduler.tick, :<, 50
  end
end
