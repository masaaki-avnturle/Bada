# frozen_string_literal: true

module Bada
  module EVOS
    # Range / energy estimator.
    #
    # Tracks a moving average of energy consumption (Wh/km) from the powertrain
    # and turns the remaining usable energy into an estimated range. The moving
    # average is an exponential filter so a sudden hill or headwind does not
    # whip the prediction around.
    class RangeEstimator
      attr_reader :consumption_wh_km, :range_km, :odometer_km

      def initialize(capacity_kwh: 60.0, usable: 0.95, baseline_wh_km: 160.0)
        @usable_kwh = capacity_kwh * usable
        @consumption_wh_km = baseline_wh_km
        @range_km = 0.0
        @odometer_km = 0.0
        @alpha = 0.1
      end

      # Update with the energy used (kWh) and distance covered (km) this window.
      def update(energy_kwh, distance_km, soc)
        @odometer_km += distance_km
        if distance_km > 1e-4
          inst = (energy_kwh * 1000.0) / distance_km # Wh/km
          inst = inst.clamp(40.0, 600.0)
          @consumption_wh_km = (1 - @alpha) * @consumption_wh_km + @alpha * inst
        end
        remaining_kwh = @usable_kwh * soc
        @range_km = (remaining_kwh * 1000.0) / @consumption_wh_km
        @range_km
      end

      def to_s
        format("RANGE %.0f km @ %.0f Wh/km (odo %.1f km)",
               @range_km, @consumption_wh_km, @odometer_km)
      end
    end
  end
end
