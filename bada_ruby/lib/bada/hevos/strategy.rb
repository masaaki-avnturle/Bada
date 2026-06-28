# frozen_string_literal: true

require_relative "../error_correction"
require_relative "../manifold"

module Bada
  module HEVOS
    # The torque-split plan produced by the energy manager for one cycle.
    #   engine_kw       mechanical output asked of the ICE (0 = engine off)
    #   battery_kw      electrical pack power (+discharge / -charge)
    #   motor_wheel_kw  mechanical motor power at the wheels (+drive / -regen)
    #   friction_kw     mechanical brake power dissipated as heat
    Plan = Struct.new(:mode, :engine_kw, :battery_kw, :motor_wheel_kw,
                      :friction_kw, :fuel_lph, :s_factor, keyword_init: true)

    # Energy Management Strategy — the hybrid "brain" of BadaOS-HEV.
    #
    # Implements an adaptive ECMS (Equivalent Consumption Minimization
    # Strategy): every cycle it picks the engine/battery split that minimises a
    # single cost  J = fuel_power + s · battery_power, where the equivalence
    # factor `s` converts stored electricity into "equivalent fuel". The
    # framework's Bada layer does two jobs here:
    #
    #   * `Bada::ErrorCorrection` stabilises the SOC-adaptive `s` (the
    #     relativistic-top integrable system damps noisy SOC feedback so the
    #     strategy never chatters between charge and assist).
    #   * `Bada::Manifold` measures the entropy invariant Ξ of the recent power
    #     demand: a high-Ξ (busy / aggressive) drive pattern biases the manager
    #     toward keeping the engine lit and the battery ready to boost.
    class EnergyManagement
      def initialize(engine:, soc_target: 0.60, soc_min: 0.45, soc_max: 0.78,
                     s0: 2.6, motor_eff: 0.90, motor_max: 60.0, charge_max: 25.0,
                     regen_max: 50.0, engine_min: 6.0)
        @engine = engine
        @soc_target = soc_target
        @soc_min = soc_min
        @soc_max = soc_max
        @s0 = s0
        @motor_eff = motor_eff
        @motor_max = motor_max
        @charge_max = charge_max
        @regen_max = regen_max
        @engine_min = engine_min
        @cs_band = 0.06 # charge-sustaining recovery band (hysteresis)
        @cs_charging = false
        @s_hist = [s0]
        @demand_hist = []
        @s_factor = s0
        @drive_xi = 0.0
      end

      attr_reader :s_factor, :drive_xi

      # SOC-adaptive equivalence factor, stabilised by Bada error correction.
      def equivalence_factor(soc)
        raw = @s0 * (1.0 + 3.0 * (@soc_target - soc))
        # aggressive driving (high Ξ) slightly cheapens electricity -> more boost
        raw *= (1.0 - 0.10 * @drive_xi.clamp(0.0, 1.0))
        @s_hist << raw
        @s_hist.shift while @s_hist.length > 8
        @s_factor = Bada::ErrorCorrection.correct(@s_hist)[:value].clamp(0.5, 8.0)
      end

      # Classify the recent drive pattern via the manifold entropy invariant Ξ.
      def observe(p_demand_kw)
        @demand_hist << p_demand_kw.round.to_s
        @demand_hist.shift while @demand_hist.length > 16
        @drive_xi = Bada::Manifold.xi(@demand_hist.join(" ")) if @demand_hist.length >= 4
      end

      # Decide the split. `p_demand_kw` is the mechanical wheel power required
      # (negative = braking). Returns a Plan; the wheel power is always met.
      def decide(p_demand_kw, soc, speed_ms)
        observe(p_demand_kw)

        # --- braking: blend regenerative + friction braking -------------------
        if p_demand_kw < -1e-6
          regen_avail = soc < @soc_max ? @regen_max : 0.0
          regen = [-p_demand_kw, regen_avail].min
          friction = (-p_demand_kw) - regen
          return Plan.new(mode: :regen, engine_kw: 0.0, battery_kw: -regen * @motor_eff,
                          motor_wheel_kw: -regen, friction_kw: friction, fuel_lph: 0.0,
                          s_factor: @s_factor)
        end

        # --- light load with charge in hand: pure-electric / coast -----------
        if p_demand_kw < 1.5 && soc > @soc_min
          batt = p_demand_kw.positive? ? p_demand_kw / @motor_eff : 0.0
          mode = speed_ms < 0.1 ? :idle : (p_demand_kw.positive? ? :ev : :coast)
          return Plan.new(mode: mode, engine_kw: 0.0, battery_kw: batt,
                          motor_wheel_kw: p_demand_kw, friction_kw: 0.0,
                          fuel_lph: 0.0, s_factor: @s_factor)
        end

        s = equivalence_factor(soc)

        # Charge-sustaining hysteresis: once SOC hits the floor, latch into
        # recharge until it recovers a band above the floor. Without this the
        # engine bang-bangs on/off in a limit cycle at the floor.
        @cs_charging = true if soc <= @soc_min
        @cs_charging = false if soc >= @soc_min + @cs_band
        disch_max = (soc > @soc_min && !@cs_charging) ? @motor_max : 0.0
        chg_max   = soc < @soc_max ? @charge_max : 0.0
        # Clamp demand to what the driveline can actually deliver right now so
        # the search always has a feasible split (engine-limited limp at floor).
        p_demand_kw = [p_demand_kw, @engine.max_power + disch_max].min

        # Forced recharge while latched: run the engine above the road load at
        # an efficient point so the surplus refills the pack (as a real
        # charge-sustaining controller does), instead of merely holding SOC.
        if @cs_charging
          charge_rate = [chg_max, @engine.max_power - p_demand_kw, 18.0].min
          charge_rate = [charge_rate, 0.0].max
          p_eng = [p_demand_kw + charge_rate, @engine.max_power].min
          pb = p_demand_kw - p_eng # <= 0 (charging)
          return Plan.new(mode: (pb < -0.5 ? :charge : :engine), engine_kw: p_eng,
                          battery_kw: pb * @motor_eff, motor_wheel_kw: pb,
                          friction_kw: 0.0, fuel_lph: 0.0, s_factor: @s_factor)
        end

        # --- ECMS minimisation over battery mechanical power pb ---------------
        lo = -chg_max
        hi = [disch_max, p_demand_kw].min

        candidates = []
        n = 24
        (0..n).each { |i| candidates << lo + (hi - lo) * i / n.to_f }
        candidates.concat([0.0, p_demand_kw, -chg_max, hi])

        best = nil
        candidates.uniq.each do |pb|
          next if pb > hi + 1e-9 || pb < lo - 1e-9
          p_eng = p_demand_kw - pb
          next if p_eng < -1e-9 || p_eng > @engine.max_power + 1e-9
          p_eng = [p_eng, 0.0].max

          fuel_kw = p_eng > 1e-3 ? p_eng / @engine.efficiency_for(p_eng) : 0.0
          batt_elec = pb >= 0 ? pb / @motor_eff : pb * @motor_eff
          j = fuel_kw + s * batt_elec
          j += 6.0 if p_eng > 1e-3 && p_eng < @engine_min # avoid inefficient idling-on

          if best.nil? || j < best[:j]
            best = { j: j, pb: pb, p_eng: p_eng, batt: batt_elec }
          end
        end

        # Fallback (should be unreachable after the demand clamp): engine-only.
        best ||= begin
          p_eng = [p_demand_kw, @engine.max_power].min
          { j: 0.0, pb: 0.0, p_eng: p_eng, batt: 0.0 }
        end

        pb = best[:pb]
        p_eng = best[:p_eng]
        mode =
          if p_eng <= 1e-3 then :ev
          elsif pb > 0.5 then :boost
          elsif pb < -0.5 then :charge
          else :engine
          end

        Plan.new(mode: mode, engine_kw: p_eng, battery_kw: best[:batt],
                 motor_wheel_kw: pb, friction_kw: 0.0, fuel_lph: 0.0,
                 s_factor: @s_factor)
      end
    end
  end
end
