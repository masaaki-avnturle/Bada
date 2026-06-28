# frozen_string_literal: true

require_relative "../manifold"

module Bada
  module EVOS
    # A single diagnostic trouble code.
    Fault = Struct.new(:code, :severity, :message, :tick, keyword_init: true)

    # Diagnostics / fault manager — the watchdog of BadaOS.
    #
    # Two complementary detectors:
    #
    #   1. Rule-based safety limits (temperature, SOC, voltage, sensor health)
    #      — hard guarantees the vehicle must honour.
    #   2. Information-theoretic anomaly detection — the manifold entropy
    #      invariant Ξ of the recent event stream is tracked; an abrupt jump in
    #      Ξ (the system "behaving unusually") raises a soft anomaly even when
    #      no single limit is breached. This is the Bada framework's own
    #      `Bada::Manifold` / `Bada::ErrorCorrection` layer doing condition
    #      monitoring.
    class Diagnostics
      SEVERITY = { info: 0, warn: 1, critical: 2 }.freeze

      attr_reader :faults, :last_invariant, :health

      def initialize
        @faults = []
        @active = {}
        @last_invariant = nil
        @health = 1.0
      end

      # Evaluate the whole vehicle state for this control cycle.
      # Returns the list of *newly* raised faults.
      def evaluate(vehicle, tick)
        fresh = []
        b = vehicle.battery

        fresh.concat(check(:PACK_OVERTEMP, :critical, b.max_temp > 55.0, tick,
                           "cell over-temperature %.1f°C" % b.max_temp))
        fresh.concat(check(:PACK_HOT, :warn, b.max_temp > 45.0, tick,
                           "pack temperature high %.1f°C" % b.max_temp))
        fresh.concat(check(:SOC_LOW, :warn, b.soc < 0.10, tick,
                           "state of charge low %.0f%%" % (b.soc * 100)))
        fresh.concat(check(:SOC_CRITICAL, :critical, b.soc < 0.03, tick,
                           "state of charge critical %.0f%%" % (b.soc * 100)))
        fresh.concat(check(:CELL_IMBALANCE, :warn, b.imbalance > 0.05, tick,
                           "cell imbalance %.3f" % b.imbalance))
        fresh.concat(check(:OVERSPEED, :warn, vehicle.powertrain.speed_kph > 180.0, tick,
                           "overspeed %.0f km/h" % vehicle.powertrain.speed_kph))

        vehicle.sensors.each_value do |s|
          fresh.concat(check(:"SENSOR_#{s.name.upcase}", :warn, !s.healthy?, tick,
                             "sensor %s noisy (residual %.3f)" % [s.name, s.residual]))
        end

        # Information-theoretic anomaly: large swing in the event-stream Ξ.
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

      # Edge-triggered fault tracking: a fault fires once when it becomes
      # active and clears when the condition goes away.
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
        penalty = @active.values.sum { |f| SEVERITY[f.severity] + 1 }
        (1.0 - penalty * 0.12).clamp(0.0, 1.0)
      end
    end
  end
end
