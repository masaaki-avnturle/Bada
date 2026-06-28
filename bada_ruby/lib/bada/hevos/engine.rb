# frozen_string_literal: true

require_relative "../special"

module Bada
  module HEVOS
    # Internal-combustion engine (Atkinson-cycle, as in a series-parallel
    # hybrid). Produces mechanical power, burns fuel according to a brake
    # specific fuel consumption (BSFC) map, and supports start/stop.
    #
    # The BSFC / thermal-efficiency map is shaped by the Bada `x log x`
    # (Napier-circle) special function: efficiency rises with load, peaks at
    # high-but-not-full load, and rolls off near wide-open throttle — the
    # classic island-shaped engine map.
    class Engine
      LHV_KWH_PER_L = 8.9 # gasoline lower heating value (kWh per liter)

      attr_reader :on, :power_kw, :rpm, :efficiency, :fuel_lph, :runtime_s

      def initialize(max_power_kw: 73.0, peak_eff: 0.38, idle_rpm: 1000, max_rpm: 5200)
        @max_power = max_power_kw
        @peak_eff = peak_eff
        @idle_rpm = idle_rpm
        @max_rpm = max_rpm
        @on = false
        @power_kw = 0.0
        @rpm = 0
        @efficiency = 0.0
        @fuel_lph = 0.0
        @runtime_s = 0.0
      end

      attr_reader :max_power

      # Thermal efficiency as a function of mechanical output (BSFC map).
      def efficiency_for(power_kw)
        return 0.0 if power_kw <= 0.0
        load = (power_kw / @max_power).clamp(0.01, 1.0)
        # Bada x·log·x rising term (efficiency improves with load)...
        rise = Bada::Special.x_log_x(1.0 + load) / Bada::Special.x_log_x(2.0)
        # ...with a mild high-load roll-off (knock-limited spark retard).
        rolloff = 1.0 - 0.20 * [load - 0.80, 0.0].max / 0.20
        e = @peak_eff * (0.55 + 0.45 * rise) * rolloff
        e.clamp(0.12, @peak_eff)
      end

      # Run the engine at `power_kw` mechanical output for `dt_s`. A request of
      # 0 (or less) shuts it off. Returns fuel flow in L/h.
      def run(power_kw, dt_s)
        if power_kw <= 1e-3
          @on = false
          @power_kw = 0.0
          @rpm = 0
          @efficiency = 0.0
          @fuel_lph = 0.0
          return 0.0
        end
        @on = true
        @power_kw = [power_kw, @max_power].min
        @efficiency = efficiency_for(@power_kw)
        fuel_power_kw = @power_kw / @efficiency # kW of chemical energy
        @fuel_lph = fuel_power_kw / LHV_KWH_PER_L
        load = @power_kw / @max_power
        @rpm = (@idle_rpm + (@max_rpm - @idle_rpm) * Math.sqrt(load)).round
        @runtime_s += dt_s
        @fuel_lph
      end

      def to_s
        @on ? format("ICE %dkW %drpm η%.0f%% %.1fL/h", @power_kw, @rpm, @efficiency * 100, @fuel_lph) : "ICE off"
      end
    end
  end
end
