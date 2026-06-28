# frozen_string_literal: true

module Bada
  module EVOS
    # HMI / instrument-cluster renderer. Pure-text dashboard so BadaOS-EV can
    # draw its state in any terminal.
    module Dashboard
      module_function

      def bar(frac, width: 20)
        frac = frac.clamp(0.0, 1.0)
        filled = (frac * width).round
        "[" + ("█" * filled) + ("·" * (width - filled)) + "]"
      end

      def render(vehicle)
        b = vehicle.battery
        p = vehicle.powertrain
        t = vehicle.thermal
        r = vehicle.range
        d = vehicle.diagnostics

        lines = []
        lines << "╔══════════════════ BadaOS-EV ══════════════════╗"
        lines << format("║ %-46s ║", "tick %d  state: %s" % [vehicle.scheduler.tick, vehicle.state])
        lines << "╠════════════════════════════════════════════════╣"
        lines << format("║ SPEED  %6.1f km/h   PWR %7.1f kW  η %3.0f%%   ║",
                        p.speed_kph, p.power_kw, p.efficiency * 100)
        lines << format("║ SOC    %s %4.0f%%   ║", bar(b.soc), b.soc * 100)
        lines << format("║ RANGE  %6.0f km     %5.0f Wh/km           ║",
                        r.range_km, r.consumption_wh_km)
        lines << format("║ PACK   %6.1f V   I %7.1f A             ║",
                        b.voltage(0.0), vehicle.pack_current)
        lines << format("║ TEMP   max %5.1f°C  cool %.1fkW  cabin %4.1f°C║",
                        b.max_temp, t.coolant_kw, t.cabin_c)
        lines << format("║ BALANCE imbalance %.3f   %s        ║",
                        b.imbalance, vehicle.charger.plugged? ? vehicle.charger.to_s : "         ")
        lines << format("║ HEALTH %s %3.0f%%   ║", bar(d.health), d.health * 100)
        if d.active_codes.any?
          lines << format("║ ⚠ %-44s ║", d.active_codes.first(3).join(" "))
        else
          lines << format("║ %-46s ║", "✓ all systems nominal")
        end
        lines << "╚════════════════════════════════════════════════╝"
        lines.join("\n")
      end
    end
  end
end
