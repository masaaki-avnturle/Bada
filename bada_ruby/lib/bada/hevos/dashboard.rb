# frozen_string_literal: true

module Bada
  module HEVOS
    # HMI / instrument cluster for the hybrid, with a live energy-flow display
    # showing how power moves between the engine, battery and wheels each cycle.
    module Dashboard
      module_function

      def bar(frac, width: 18)
        frac = frac.clamp(0.0, 1.0)
        filled = (frac * width).round
        "[" + ("█" * filled) + ("·" * (width - filled)) + "]"
      end

      # A one-line schematic of the current power flow.
      def flow(plan)
        eng = plan.engine_kw
        batt = plan.battery_kw
        case plan.mode
        when :ev      then "ENGINE·off   BATT──#{'%.0f' % batt.abs}kW──▶ WHEELS"
        when :boost   then "ENGINE──#{'%.0f' % eng}kW──▶ WHEELS ◀──#{'%.0f' % batt.abs}kW──BATT"
        when :charge  then "ENGINE──#{'%.0f' % eng}kW──▶ WHEELS+BATT(◀#{'%.0f' % batt.abs}kW chg)"
        when :engine  then "ENGINE──#{'%.0f' % eng}kW──▶ WHEELS   BATT·idle"
        when :regen   then "WHEELS──#{'%.0f' % batt.abs}kW──▶ BATT (regen)   ENGINE·off"
        else               "ENGINE·off   BATT·idle   (coast)"
        end
      end

      def render(vehicle)
        b = vehicle.battery
        p = vehicle.powertrain
        e = p.engine
        f = vehicle.fuel
        d = vehicle.diagnostics
        pl = p.plan

        lines = []
        lines << "╔═══════════════════ BadaOS-HEV ═══════════════════╗"
        lines << format("║ %-48s ║", "tick %d  mode: %s" % [vehicle.scheduler.tick, pl.mode.to_s.upcase])
        lines << "╠══════════════════════════════════════════════════╣"
        lines << format("║ SPEED %6.1f km/h     %-26s ║", p.speed_kph, vehicle.state)
        lines << format("║ ICE   %-42s ║", e.on ? ("%dkW %drpm η%.0f%% %.1fL/h" % [e.power_kw, e.rpm, e.efficiency * 100, e.fuel_lph]) : "off")
        lines << format("║ BATT  %s %3.0f%% %+6.1fkW ║", bar(b.soc), b.soc * 100, pl.battery_kw)
        lines << format("║ FUEL  %s %3.0f%% %5.1fL ║", bar(f.fraction), f.fraction * 100, f.level_l)
        lines << format("║ ECON  %5.1f km/L   ECMS s=%.2f  Ξ=%.2f       ║",
                        vehicle.fuel_economy, pl.s_factor, p.strategy.drive_xi)
        lines << format("║ TEMP  pack %4.1f°C   range ~%4.0f km          ║",
                        b.max_temp, vehicle.total_range_km)
        lines << "╟──────────────────────────────────────────────────╢"
        lines << format("║ %-48s ║", flow(pl))
        lines << "╟──────────────────────────────────────────────────╢"
        lines << format("║ HEALTH %s %3.0f%%        ║", bar(d.health), d.health * 100)
        if d.active_codes.any?
          lines << format("║ ⚠ %-46s ║", d.active_codes.first(3).join(" "))
        else
          lines << format("║ %-48s ║", "✓ all systems nominal")
        end
        lines << "╚══════════════════════════════════════════════════╝"
        lines.join("\n")
      end
    end
  end
end
