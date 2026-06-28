# frozen_string_literal: true

require_relative "../special"

module Bada
  module EVOS
    # Motor / powertrain controller.
    #
    # Converts a normalised pedal request (throttle ∈ [-1, 1], negative = regen
    # braking) into electrical power drawn from / returned to the pack, and
    # integrates a simple longitudinal vehicle model (tractive force vs. drag +
    # rolling resistance) to produce road speed.
    #
    # The drive efficiency map reuses the Bada `x log x` ("neipa"/Napier circle)
    # special function: motor+inverter efficiency peaks at mid load and rolls
    # off at the extremes, which the smooth `x_log_x` curve captures naturally.
    class Powertrain
      G = 9.81

      attr_reader :speed_ms, :power_kw, :torque, :efficiency

      def initialize(mass_kg: 1850.0, max_power_kw: 150.0, max_regen_kw: 60.0,
                     cd_a: 0.62, crr: 0.011, v_max_kph: 160.0)
        @mass = mass_kg
        @max_power = max_power_kw
        @max_regen = max_regen_kw
        @v_max = v_max_kph / 3.6 # speed governor (m/s)
        @cd_a = cd_a       # drag coefficient × frontal area
        @crr = crr         # rolling resistance coefficient
        @rho = 1.225       # air density
        @speed_ms = 0.0
        @power_kw = 0.0
        @torque = 0.0
        @efficiency = 0.9
      end

      def speed_kph
        @speed_ms * 3.6
      end

      # Drive-line efficiency in [0.78, 0.96] as a function of normalised load,
      # shaped by the Bada x·log·x curve (peaks mid-load).
      def efficiency_for(load)
        l = load.abs.clamp(1e-3, 1.0)
        shape = Bada::Special.x_log_x(1.0 + l) # 0 at l→0, rises smoothly
        0.78 + 0.18 * (shape / Bada::Special.x_log_x(2.0)).clamp(0.0, 1.0)
      end

      # Apply throttle for dt_s seconds. Returns the electrical pack power (kW,
      # positive = discharge, negative = regen back into the pack).
      def apply(throttle, dt_s)
        throttle = throttle.to_f.clamp(-1.0, 1.0)
        v = @speed_ms

        # Speed governor: cut traction (not regen) at the top-speed limit.
        throttle = 0.0 if throttle.positive? && v >= @v_max

        if throttle >= 0
          mech_power = throttle * @max_power * 1000.0           # W to wheels
          @efficiency = efficiency_for(throttle)
          elec_power = mech_power / @efficiency                 # battery supplies more
        else
          mech_power = throttle * @max_regen * 1000.0           # negative (braking)
          @efficiency = efficiency_for(throttle)
          elec_power = mech_power * @efficiency                 # recover less than braked
        end

        # Tractive force (cap at low speed to avoid singularity).
        tractive = mech_power / [v, 1.0].max
        drag = 0.5 * @rho * @cd_a * v * v
        rolling = (v > 0.05 ? @crr * @mass * G : 0.0)
        net = tractive - drag - rolling
        accel = net / @mass

        @speed_ms = [v + accel * dt_s, 0.0].max
        @torque = tractive
        @power_kw = elec_power / 1000.0
        @power_kw
      end

      def to_s
        format("PWR %.1f km/h %.1f kW η=%.0f%%", speed_kph, @power_kw, @efficiency * 100)
      end
    end
  end
end
