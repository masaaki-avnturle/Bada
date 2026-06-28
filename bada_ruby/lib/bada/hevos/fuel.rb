# frozen_string_literal: true

module Bada
  module HEVOS
    # Fuel tank. Tracks liters of gasoline and integrates the engine's
    # instantaneous fuel flow (L/h) over each control cycle.
    class FuelTank
      attr_reader :capacity_l, :level_l, :total_used_l

      def initialize(capacity_l: 43.0, level_l: 40.0)
        @capacity_l = capacity_l.to_f
        @level_l = level_l.to_f.clamp(0.0, @capacity_l)
        @total_used_l = 0.0
      end

      # Burn `lph` liters/hour for `dt_s` seconds. Returns liters actually drawn.
      def consume(lph, dt_s)
        want = lph * dt_s / 3600.0
        drawn = [want, @level_l].min
        @level_l -= drawn
        @total_used_l += drawn
        drawn
      end

      def fraction
        @capacity_l <= 0 ? 0.0 : @level_l / @capacity_l
      end

      def empty?
        @level_l <= 1e-6
      end

      def refuel(liters = nil)
        @level_l = liters.nil? ? @capacity_l : [@level_l + liters, @capacity_l].min
      end
    end
  end
end
