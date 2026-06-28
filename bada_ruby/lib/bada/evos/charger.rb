# frozen_string_literal: true

module Bada
  module EVOS
    # Charging controller — CC/CV (constant-current / constant-voltage).
    #
    # While plugged in, charge at constant power up to the CV knee (default
    # 80% SOC), then taper linearly toward full to protect the cells. Charging
    # delivers *negative* power to the BatteryPack (the BMS treats negative
    # power as charge).
    class Charger
      MODES = %i[off ac dc].freeze

      attr_reader :mode, :power_kw, :delivered_kw

      def initialize
        @mode = :off
        @ac_power = 11.0   # kW (home AC)
        @dc_power = 120.0  # kW (DC fast)
        @cv_knee = 0.80
        @power_kw = 0.0
        @delivered_kw = 0.0
      end

      def plug(mode)
        @mode = MODES.include?(mode) ? mode : :off
      end

      def unplug
        @mode = :off
        @power_kw = 0.0
      end

      def plugged?
        @mode != :off
      end

      # Run one charge cycle against the battery. Returns delivered power (kW).
      def charge(battery, dt_s)
        return 0.0 unless plugged?

        rated = @mode == :dc ? @dc_power : @ac_power
        soc = battery.soc

        @power_kw =
          if soc >= 0.999
            unplug
            0.0
          elsif soc < @cv_knee
            rated # constant current/power phase
          else
            # CV taper: power falls to ~5% of rated at full.
            frac = (1.0 - soc) / (1.0 - @cv_knee)
            rated * (0.05 + 0.95 * frac)
          end

        battery.update(-@power_kw, dt_s) if @power_kw.positive? # negative = charge
        @delivered_kw = @power_kw
        @power_kw
      end

      def to_s
        plugged? ? format("CHG %s %.1fkW", @mode, @power_kw) : "CHG off"
      end
    end
  end
end
