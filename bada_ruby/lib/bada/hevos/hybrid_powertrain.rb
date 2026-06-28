# frozen_string_literal: true

require_relative "engine"
require_relative "strategy"

module Bada
  module HEVOS
    # Series-parallel hybrid powertrain with an electronic CVT power split.
    #
    # A planetary gear couples the engine, a generator (MG1) and the traction
    # motor (MG2). At the OS/control level what matters is the *power flow*: the
    # driver's pedal becomes a wheel-power demand, the Energy Management
    # Strategy splits that demand between engine and battery, and the engine can
    # simultaneously drive the wheels and charge the pack through MG1 (the e-CVT
    # lets it sit at its most efficient operating point regardless of road
    # speed). The longitudinal model integrates road speed from the delivered
    # wheel power against aerodynamic drag and rolling resistance.
    class HybridPowertrain
      G = 9.81

      attr_reader :speed_ms, :engine, :strategy, :plan

      def initialize(battery_soc_fn, mass_kg: 1500.0, engine_max_kw: 73.0,
                     motor_max_kw: 60.0, cd_a: 0.58, crr: 0.010, v_max_kph: 180.0)
        @soc_fn = battery_soc_fn
        @mass = mass_kg
        @engine = Engine.new(max_power_kw: engine_max_kw)
        @motor_max = motor_max_kw
        @cd_a = cd_a
        @crr = crr
        @rho = 1.225
        @v_max = v_max_kph / 3.6
        @speed_ms = 0.0
        @strategy = EnergyManagement.new(engine: @engine, motor_max: motor_max_kw)
        @plan = Plan.new(mode: :idle, engine_kw: 0.0, battery_kw: 0.0,
                         motor_wheel_kw: 0.0, friction_kw: 0.0, fuel_lph: 0.0,
                         s_factor: 0.0)
      end

      def speed_kph
        @speed_ms * 3.6
      end

      # Apply the driver pedal (throttle ∈ [-1,1]; negative = braking) for dt_s.
      # Returns the cycle Plan (engine/battery/motor/friction powers).
      def apply(throttle, dt_s)
        throttle = throttle.to_f.clamp(-1.0, 1.0)
        v = @speed_ms
        soc = @soc_fn.call

        if throttle >= 0
          throttle = 0.0 if v >= @v_max # speed governor
          p_total_max = @engine.max_power * 0.95 + @motor_max
          p_demand = throttle * p_total_max
        else
          brake_cap = @motor_max + 80.0 # regen + friction capacity
          p_demand = throttle * brake_cap # negative
        end

        # Energy manager chooses the source split (wheel power is always met).
        @plan = @strategy.decide(p_demand, soc, v)

        # Fire the engine for this cycle and read back true fuel flow.
        @engine.run(@plan.engine_kw, dt_s)
        @plan.fuel_lph = @engine.fuel_lph

        # Longitudinal dynamics from the delivered wheel power (= p_demand).
        mech_power = p_demand * 1000.0
        tractive = mech_power / [v, 1.0].max
        drag = 0.5 * @rho * @cd_a * v * v
        rolling = v > 0.05 ? @crr * @mass * G : 0.0
        net = tractive - drag - (p_demand >= 0 ? rolling : -rolling)
        accel = net / @mass
        @speed_ms = [v + accel * dt_s, 0.0].max
        @plan
      end

      def to_s
        format("HEV %.0f km/h %s", speed_kph, @engine.to_s)
      end
    end
  end
end
