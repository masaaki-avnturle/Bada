# frozen_string_literal: true

require_relative "kernel"
require_relative "sensor"
require_relative "battery"
require_relative "powertrain"
require_relative "thermal"
require_relative "charger"
require_relative "range_estimator"
require_relative "diagnostics"
require_relative "recorder"
require_relative "dashboard"

module Bada
  module EVOS
    # Vehicle — the BadaOS-EV facade.
    #
    # Boots all subsystems, wires them into the real-time kernel as periodic
    # tasks (ordered by priority so safety work pre-empts housekeeping), and
    # exposes a small driver/ADAS API (`drive`, `brake`, `plug_in`). The whole
    # electric vehicle runs as one deterministic control loop on top of the
    # Bada operator-algebra framework.
    #
    # Task table (per control cycle):
    #   priority 100  sensors      sample + Bada error-correct the signals
    #   priority  90  powertrain   pedal -> power, integrate road speed
    #   priority  85  bms          coulomb count, self-heat, balance cells
    #   priority  80  charger      CC/CV charge when plugged in
    #   priority  70  thermal      regulate pack/cabin temperature
    #   priority  50  diagnostics  safety limits + Ξ anomaly detection
    #   priority  30  range        consumption + range estimate
    #   priority  10  recorder     telemetry snapshot to Ω::DATABASE
    class Vehicle
      attr_reader :scheduler, :battery, :powertrain, :thermal, :charger,
                  :range, :diagnostics, :recorder, :sensors
      attr_reader :state, :pack_current, :throttle, :dt

      def initialize(capacity_kwh: 60.0, dt: 1.0)
        @dt = dt
        @capacity_kwh = capacity_kwh
        @battery = BatteryPack.new(capacity_kwh: capacity_kwh)
        @powertrain = Powertrain.new
        @thermal = Thermal.new
        @charger = Charger.new
        @range = RangeEstimator.new(capacity_kwh: capacity_kwh)
        @diagnostics = Diagnostics.new
        @recorder = Recorder.new
        @sensors = {
          "speed"   => Sensor.new("speed", unit: "km/h"),
          "current" => Sensor.new("current", unit: "A"),
          "voltage" => Sensor.new("voltage", unit: "V"),
          "celltemp" => Sensor.new("celltemp", unit: "°C")
        }
        @scheduler = Scheduler.new
        @throttle = 0.0
        @pack_current = 0.0
        @state = :off
        build_tasks
      end

      # ---- driver / ADAS API -------------------------------------------------

      def boot
        @state = :ready
        @recorder.log("BadaOS-EV boot: pack #{format('%.0f', @capacity_kwh)}kWh " \
                      "soc #{format('%.0f%%', @battery.soc * 100)}", tags: { kind: :boot })
        self
      end

      # Set the pedal: throttle ∈ [-1,1]. Positive drives, negative regen-brakes.
      def drive(throttle)
        @throttle = throttle.to_f.clamp(-1.0, 1.0)
        @state = :driving if @throttle > 0
        @state = :regen if @throttle < 0
        self
      end

      def brake(strength = 0.5)
        drive(-strength.abs)
      end

      def coast
        @throttle = 0.0
        @state = :ready
        self
      end

      def plug_in(mode = :dc)
        @charger.plug(mode)
        @throttle = 0.0
        @state = :charging
        @recorder.log("charge start mode=#{mode} soc=#{format('%.0f%%', @battery.soc * 100)}",
                      tags: { kind: :charge })
        self
      end

      def unplug
        @charger.unplug
        @state = :ready
        self
      end

      # Advance one control cycle (returns the run-list).
      def step
        @scheduler.step(self)
      end

      # Run `ticks` control cycles, optionally yielding the vehicle each cycle.
      def run(ticks:)
        ticks.times do
          step
          yield self if block_given?
          break if @diagnostics.critical? && @state != :charging
        end
        self
      end

      def dashboard
        Dashboard.render(self)
      end

      private

      # ---- kernel wiring -----------------------------------------------------

      def build_tasks
        @scheduler.every("sensors", period: 1, priority: 100) { |v, tick| v.send(:task_sensors, tick) }
        @scheduler.every("powertrain", period: 1, priority: 90) { |v, _| v.send(:task_powertrain) }
        @scheduler.every("bms", period: 1, priority: 85) { |v, _| v.send(:task_bms) }
        @scheduler.every("charger", period: 1, priority: 80) { |v, _| v.send(:task_charger) }
        @scheduler.every("thermal", period: 2, priority: 70) { |v, _| v.send(:task_thermal) }
        @scheduler.every("diagnostics", period: 2, priority: 50) { |v, tick| v.send(:task_diag, tick) }
        @scheduler.every("range", period: 5, priority: 30) { |v, _| v.send(:task_range) }
        @scheduler.every("recorder", period: 5, priority: 10) { |v, tick| v.send(:task_record, tick) }
      end

      # Sample the physical truth with deterministic sensor noise, then let the
      # Bada error corrector clean it up.
      def task_sensors(tick)
        noise = ->(k) { 1.0 + 0.02 * Math.sin(tick * 0.9 + k) }
        spike = (tick % 17 == 0 ? 1.0 : 0.0) # periodic outlier to exercise EC
        @sensors["speed"].feed(@powertrain.speed_kph * noise[0])
        @sensors["current"].feed(@pack_current * noise[1] + spike * 50.0)
        @sensors["voltage"].feed(@battery.voltage(@pack_current) * noise[2])
        @sensors["celltemp"].feed(@battery.max_temp * noise[3])
      end

      def task_powertrain
        # While plugged in the car is parked: command zero torque and let drag
        # bring it to rest (no traction current is drawn — see task_bms).
        effective = @charger.plugged? ? 0.0 : @throttle
        @powertrain.apply(effective, @dt)
      end

      def task_bms
        traction_kw = @charger.plugged? ? 0.0 : @powertrain.power_kw
        aux_kw = @thermal.aux_load_kw
        load_kw = traction_kw + aux_kw
        @pack_current = @battery.update(load_kw, @dt) unless @charger.plugged?
        @battery.balance!
      end

      def task_charger
        return unless @charger.plugged?
        @charger.charge(@battery, @dt)
        @pack_current = -@charger.power_kw * 1000.0 / [@battery.voltage(0.0), 1.0].max
        if @battery.soc >= 0.999
          @recorder.log("charge complete soc=100%", tags: { kind: :charge })
          unplug
        end
      end

      def task_thermal
        @thermal.regulate(@battery, @dt * 2)
      end

      def task_diag(tick)
        fresh = @diagnostics.evaluate(self, tick)
        fresh.each do |f|
          @recorder.log("FAULT #{f.code} [#{f.severity}] #{f.message}",
                        tags: { kind: :fault, code: f.code })
        end
      end

      def task_range
        dist_km = @powertrain.speed_ms * (@dt * 5) / 1000.0
        energy_kwh = [@powertrain.power_kw, 0.0].max * (@dt * 5) / 3600.0
        @range.update(energy_kwh, dist_km, @battery.soc)
      end

      def task_record(tick)
        @recorder.log(
          format("t=%d v=%.0fkmh soc=%.0f%% Tmax=%.0fC P=%.0fkW rng=%.0fkm health=%.0f%%",
                 tick, @powertrain.speed_kph, @battery.soc * 100, @battery.max_temp,
                 @powertrain.power_kw, @range.range_km, @diagnostics.health * 100),
          tags: { kind: :telemetry }
        )
      end

      public :step
    end
  end
end
