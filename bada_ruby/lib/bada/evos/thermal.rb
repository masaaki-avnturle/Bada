# frozen_string_literal: true

require_relative "../language"

module Bada
  module EVOS
    # Thermal management — battery cooling/heating loop + cabin climate.
    #
    # A bang-bang-with-proportional cooling controller drives pack temperature
    # toward a target window. The applied cooling power is fed back to the BMS
    # (`BatteryPack#cooling_kw`) where it offsets I²R self-heating.
    #
    # The Bada quantum right-act `>-`  (e^{-x log x}) is used as the coolant
    # ramp law: cooling demand rises sharply as temperature exceeds target and
    # saturates, exactly the decaying-exponential shape produced by the
    # `BadaNode#right_act` operator on the temperature error.
    class Thermal
      attr_reader :target_c, :coolant_kw, :cabin_c, :mode

      def initialize(target_c: 30.0, max_coolant_kw: 8.0, cabin_target_c: 22.0)
        @target_c = target_c
        @max_coolant = max_coolant_kw
        @cabin_target = cabin_target_c
        @cabin_c = 25.0
        @coolant_kw = 0.0
        @mode = :idle
      end

      # Compute and apply cooling for the pack this cycle.
      def regulate(battery, dt_s)
        t = battery.max_temp
        err = t - @target_c

        if err <= 0.0
          @coolant_kw = 0.0
          @mode = (t < @target_c - 8.0 ? :heating : :idle)
        else
          # Bada >- operator: e^{-x log x} maps the error into a (0,1] demand
          # that saturates — strong cooling kicks in fast then plateaus.
          node = Bada::BadaNode.new(err)
          node.right_act           # value = e^{-x log x}, in (0,1]
          demand = 1.0 - node.value.clamp(0.0, 1.0) # invert: big error -> ~1
          @coolant_kw = (demand * @max_coolant).clamp(0.0, @max_coolant)
          @mode = :cooling
        end

        battery.cooling_kw = @coolant_kw

        # Cabin climate relaxes toward its target (uses a little energy).
        @cabin_c += (@cabin_target - @cabin_c) * 0.1
        @coolant_kw
      end

      # Auxiliary electrical load (kW) the climate system draws from the pack.
      def aux_load_kw
        base = 0.3
        base + @coolant_kw * 0.25 + (@mode == :heating ? 1.5 : 0.0)
      end

      def to_s
        format("THERM %s pack→%.1f°C coolant=%.1fkW cabin=%.1f°C",
               @mode, @target_c, @coolant_kw, @cabin_c)
      end
    end
  end
end
