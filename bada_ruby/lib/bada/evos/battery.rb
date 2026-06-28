# frozen_string_literal: true

module Bada
  module EVOS
    # A single lithium cell — the atom of the battery pack.
    #
    # OCV (open-circuit voltage) is a smooth function of state-of-charge; the
    # terminal voltage drops under load by the internal resistance. Each cell
    # keeps its own SOC, temperature and capacity factor so the pack can drift
    # out of balance (weaker cells drain faster) and the BMS has real work to do.
    class Cell
      attr_accessor :soc, :temp, :cap_factor, :soh
      attr_reader :resistance

      def initialize(soc: 0.85, temp: 25.0, cap_factor: 1.0, resistance: 0.018, soh: 1.0)
        @soc = soc
        @temp = temp
        @cap_factor = cap_factor # >1 = healthier (drains slower), <1 = weaker
        @resistance = resistance
        @soh = soh
      end

      # Open-circuit voltage from SOC (linear 3.40 V .. 4.14 V map).
      def ocv
        3.40 + 0.74 * @soc.clamp(0.0, 1.0)
      end

      # Terminal voltage under a per-cell current (A, discharge positive).
      def voltage(current_a)
        ocv - current_a * @resistance
      end
    end

    # Battery Management System (BMS) + pack model.
    #
    # The BMS is the most safety-critical subsystem of an EV. This one does
    # coulomb-counting SOC estimation, computes pack voltage/current, models
    # I²R self-heating against an externally-supplied cooling power, and runs
    # passive cell balancing to keep the string within a voltage spread.
    class BatteryPack
      AMBIENT = 25.0

      attr_reader :cells, :series, :parallel, :capacity_kwh
      attr_accessor :cooling_kw

      def initialize(series: 96, parallel: 4, capacity_kwh: 60.0, seed_spread: true)
        @series = series
        @parallel = [parallel.to_i, 1].max
        @capacity_kwh = capacity_kwh.to_f
        @cooling_kw = 0.0
        @cells = Array.new(series) do |i|
          # Deterministic small spread so balancing has something to correct.
          if seed_spread
            soc = 0.85 + 0.01 * Math.sin(i * 0.7)
            cap = 1.0 + 0.03 * Math.cos(i * 0.9)
            Cell.new(soc: soc, cap_factor: cap)
          else
            Cell.new
          end
        end
      end

      # Pack state-of-charge — mean cell SOC (0..1).
      def soc
        @cells.sum(&:soc) / @cells.length
      end

      # Per-cell SOC spread (max-min) — the balancing target.
      def imbalance
        socs = @cells.map(&:soc)
        socs.max - socs.min
      end

      # Pack open-circuit and terminal voltage.
      def ocv
        @cells.sum(&:ocv)
      end

      def voltage(current_a = 0.0)
        @cells.sum { |c| c.voltage(current_a) }
      end

      # Hottest cell — what thermal management and diagnostics watch.
      def max_temp
        @cells.map(&:temp).max
      end

      def mean_temp
        @cells.sum(&:temp) / @cells.length
      end

      # Apply `power_kw` of load for `dt_s` seconds.
      #   power_kw > 0  -> discharge (driving)
      #   power_kw < 0  -> charge (regen / plug)
      # Returns the pack current drawn (A, discharge positive).
      def update(power_kw, dt_s)
        v = [voltage(0.0), 1.0].max
        current = power_kw * 1000.0 / v
        e_kwh = power_kw * dt_s / 3600.0
        # Coulomb counting per cell, weighted by capacity factor.
        @cells.each do |c|
          dsoc = (e_kwh / @capacity_kwh) / c.cap_factor
          c.soc = (c.soc - dsoc).clamp(0.0, 1.0)
          # I²R self-heating minus cooling. Pack current splits across the
          # parallel strings, so each cell only carries current/parallel.
          cell_current = current / @parallel
          heat_w = cell_current * cell_current * c.resistance
          cool_w = (@cooling_kw * 1000.0) / @cells.length
          c.temp += (heat_w - cool_w) * dt_s / 900.0 # 900 J/K lumped cell mass
          c.temp = c.temp.clamp(-20.0, 120.0)
        end
        current
      end

      # Passive cell balancing: bleed cells above (min + threshold) down toward
      # the floor. Called by the BMS task each cycle.
      def balance!(threshold: 0.005, bleed: 0.0008)
        floor = @cells.map(&:soc).min
        bled = 0
        @cells.each do |c|
          if c.soc > floor + threshold
            c.soc -= bleed
            bled += 1
          end
        end
        bled
      end

      def to_s
        format("BMS soc=%.1f%% V=%.1f Tmax=%.1f°C imbalance=%.3f",
               soc * 100, voltage(0.0), max_temp, imbalance)
      end
    end
  end
end
