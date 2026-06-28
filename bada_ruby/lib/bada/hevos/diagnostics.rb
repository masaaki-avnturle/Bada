# frozen_string_literal: true

require_relative "../evos/diagnostics"

module Bada
  module HEVOS
    # Diagnostics / fault manager for the hybrid. Reuses the EV OS fault model
    # (rule-based safety limits + Ξ-invariant anomaly detection) and adds the
    # hybrid-specific checks: fuel level, engine over-speed, and the HEV battery
    # operating window (SOC must stay inside the charge-sustaining band).
    Fault = Bada::EVOS::Fault

    class Diagnostics
      attr_reader :faults, :last_invariant, :health

      def initialize
        @faults = []
        @active = {}
        @last_invariant = nil
        @health = 1.0
      end

      def evaluate(vehicle, tick)
        fresh = []
        b = vehicle.battery
        e = vehicle.powertrain.engine
        f = vehicle.fuel

        fresh.concat(check(:PACK_OVERTEMP, :critical, b.max_temp > 55.0, tick,
                           "cell over-temperature %.1f°C" % b.max_temp))
        fresh.concat(check(:SOC_OUT_OF_BAND, :warn, b.soc < 0.35 || b.soc > 0.85, tick,
                           "HEV SOC out of band %.0f%%" % (b.soc * 100)))
        fresh.concat(check(:FUEL_LOW, :warn, f.fraction < 0.10 && !f.empty?, tick,
                           "fuel low %.0f%%" % (f.fraction * 100)))
        fresh.concat(check(:FUEL_EMPTY, :critical, f.empty?, tick,
                           "fuel tank empty"))
        fresh.concat(check(:ENGINE_OVERSPEED, :warn, e.rpm > 5400, tick,
                           "engine over-speed %d rpm" % e.rpm))
        fresh.concat(check(:OVERSPEED, :warn, vehicle.powertrain.speed_kph > 185.0, tick,
                           "overspeed %.0f km/h" % vehicle.powertrain.speed_kph))

        vehicle.sensors.each_value do |s|
          # Engine start/stop makes current & rpm step sharply, so the HEV uses
          # a looser sensor-health tolerance than the EV.
          fresh.concat(check(:"SENSOR_#{s.name.upcase}", :warn, !s.healthy?(tol: 0.45), tick,
                             "sensor %s noisy (residual %.3f)" % [s.name, s.residual]))
        end

        xi = vehicle.recorder.recent_invariant(n: 12)
        if @last_invariant && @last_invariant > 1e-9
          jump = (xi - @last_invariant).abs / @last_invariant
          fresh.concat(check(:INFO_ANOMALY, :warn, jump > 0.75, tick,
                             "event-stream Ξ anomaly Δ=%.2f" % jump))
        end
        @last_invariant = xi

        @health = compute_health
        @faults.concat(fresh)
        fresh
      end

      def critical?
        @active.values.any? { |f| f.severity == :critical }
      end

      def active_codes
        @active.keys
      end

      private

      def check(code, severity, condition, tick, message)
        if condition
          unless @active.key?(code)
            f = Fault.new(code: code, severity: severity, message: message, tick: tick)
            @active[code] = f
            return [f]
          end
        else
          @active.delete(code)
        end
        []
      end

      def compute_health
        return 1.0 if @active.empty?
        sev = { info: 0, warn: 1, critical: 2 }
        penalty = @active.values.sum { |f| sev[f.severity] + 1 }
        (1.0 - penalty * 0.12).clamp(0.0, 1.0)
      end
    end
  end
end
