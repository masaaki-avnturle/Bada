# frozen_string_literal: true

require_relative "../evos/kernel"
require_relative "../evos/sensor"
require_relative "../evos/battery"
require_relative "../evos/thermal"
require_relative "../evos/recorder"
require_relative "fuel"
require_relative "hybrid_powertrain"
require_relative "diagnostics"
require_relative "dashboard"

module Bada
  module HEVOS
    # Vehicle — the BadaOS-HEV facade.
    #
    # A full-hybrid (HEV) operating system built on the Bada framework. It
    # reuses the BadaOS-EV real-time kernel, error-corrected sensors, battery
    # management, thermal loop and Ω::DATABASE recorder, and adds the hybrid
    # core: an internal-combustion engine, a fuel system, and an adaptive ECMS
    # energy manager that arbitrates between engine and battery every cycle.
    #
    # Task table (per control cycle, highest priority first):
    #   100 sensors      sample + Bada error-correct the signals
    #    90 powertrain   pedal -> ECMS split -> engine + motor, integrate speed
    #    85 bms          apply battery power (charge/assist/regen) + balance
    #    80 fuel         integrate engine fuel flow out of the tank
    #    70 thermal      regulate pack/cabin temperature
    #    50 diagnostics  safety limits + Ξ anomaly detection (halts on critical)
    #    30 trip         odometer, fuel economy, range estimate
    #    10 recorder     telemetry snapshot to Ω::DATABASE
    class Vehicle
      attr_reader :scheduler, :battery, :powertrain, :thermal, :fuel,
                  :diagnostics, :recorder, :sensors
      attr_reader :state, :pack_current, :throttle, :dt
      attr_reader :odometer_km, :fuel_economy, :total_range_km

      def initialize(battery_kwh: 1.6, fuel_l: 40.0, dt: 1.0)
        @dt = dt
        @battery = Bada::EVOS::BatteryPack.new(capacity_kwh: battery_kwh, soc0: 0.60)
        @fuel = FuelTank.new(level_l: fuel_l)
        @powertrain = HybridPowertrain.new(-> { @battery.soc })
        @thermal = Bada::EVOS::Thermal.new(target_c: 35.0)
        @diagnostics = Diagnostics.new
        @recorder = Bada::EVOS::Recorder.new
        @sensors = {
          "speed"    => Bada::EVOS::Sensor.new("speed", unit: "km/h"),
          "current"  => Bada::EVOS::Sensor.new("current", unit: "A"),
          "rpm"      => Bada::EVOS::Sensor.new("rpm", unit: "rpm"),
          "celltemp" => Bada::EVOS::Sensor.new("celltemp", unit: "°C")
        }
        @scheduler = Bada::EVOS::Scheduler.new
        @throttle = 0.0
        @pack_current = 0.0
        @state = :off
        @odometer_km = 0.0
        @fuel_economy = 0.0
        @total_range_km = 0.0
        build_tasks
      end

      # ---- driver API --------------------------------------------------------

      def boot
        @state = :ready
        @recorder.log("BadaOS-HEV boot: battery #{format('%.1f', @battery.capacity_kwh)}kWh " \
                      "fuel #{format('%.0f', @fuel.level_l)}L soc #{format('%.0f%%', @battery.soc * 100)}",
                      tags: { kind: :boot })
        self
      end

      def drive(throttle)
        @throttle = throttle.to_f.clamp(-1.0, 1.0)
        @state = :driving if @throttle > 0
        @state = :braking if @throttle < 0
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

      def refuel(liters = nil)
        @fuel.refuel(liters)
        @recorder.log("refuel -> #{format('%.0f', @fuel.level_l)}L", tags: { kind: :fuel })
        self
      end

      def step
        @scheduler.step(self)
      end

      def run(ticks:)
        ticks.times do
          step
          yield self if block_given?
          break if @diagnostics.critical?
        end
        self
      end

      def dashboard
        Dashboard.render(self)
      end

      private

      # ---- kernel wiring -----------------------------------------------------

      def build_tasks
        @scheduler.every("sensors", period: 1, priority: 100) { |v, t| v.send(:task_sensors, t) }
        @scheduler.every("powertrain", period: 1, priority: 90) { |v, _| v.send(:task_powertrain) }
        @scheduler.every("bms", period: 1, priority: 85) { |v, _| v.send(:task_bms) }
        @scheduler.every("fuel", period: 1, priority: 80) { |v, _| v.send(:task_fuel) }
        @scheduler.every("thermal", period: 2, priority: 70) { |v, _| v.send(:task_thermal) }
        @scheduler.every("diagnostics", period: 2, priority: 50) { |v, t| v.send(:task_diag, t) }
        @scheduler.every("trip", period: 5, priority: 30) { |v, _| v.send(:task_trip) }
        @scheduler.every("recorder", period: 5, priority: 10) { |v, t| v.send(:task_record, t) }
      end

      def task_sensors(tick)
        # 2% measurement noise; engine start/stop already steps current & rpm,
        # which the Bada error corrector smooths over the sample window.
        noise = ->(k) { 1.0 + 0.02 * Math.sin(tick * 0.9 + k) }
        @sensors["speed"].feed(@powertrain.speed_kph * noise[0])
        @sensors["current"].feed(@pack_current * noise[1])
        @sensors["rpm"].feed(@powertrain.engine.rpm * noise[2])
        @sensors["celltemp"].feed(@battery.max_temp * noise[3])
      end

      def task_powertrain
        @powertrain.apply(@throttle, @dt)
        @state =
          case @powertrain.plan.mode
          when :regen then :braking
          when :idle, :coast then :ready
          else :driving
          end
      end

      def task_bms
        aux_kw = @thermal.aux_load_kw
        load_kw = @powertrain.plan.battery_kw + aux_kw # +discharge / -charge
        @pack_current = @battery.update(load_kw, @dt)
        @battery.balance!
      end

      def task_fuel
        @fuel.consume(@powertrain.engine.fuel_lph, @dt)
      end

      def task_thermal
        @thermal.regulate(@battery, @dt * 2)
      end

      def task_diag(tick)
        @diagnostics.evaluate(self, tick).each do |f|
          @recorder.log("FAULT #{f.code} [#{f.severity}] #{f.message}",
                        tags: { kind: :fault, code: f.code })
        end
      end

      def task_trip
        dist_km = @powertrain.speed_ms * (@dt * 5) / 1000.0
        @odometer_km += dist_km
        used = @fuel.total_used_l
        @fuel_economy = used > 1e-3 ? @odometer_km / used : 0.0
        # Total range = remaining fuel at current economy + a little EV range.
        fuel_range = @fuel_economy.positive? ? @fuel.level_l * @fuel_economy : @fuel.level_l * 18.0
        ev_range = @battery.capacity_kwh * @battery.soc * 6.0
        @total_range_km = fuel_range + ev_range
      end

      def task_record(tick)
        pl = @powertrain.plan
        @recorder.log(
          format("t=%d v=%.0fkmh mode=%s soc=%.0f%% fuel=%.0f%% ice=%.0fkW econ=%.1fkmL health=%.0f%%",
                 tick, @powertrain.speed_kph, pl.mode, @battery.soc * 100, @fuel.fraction * 100,
                 @powertrain.engine.power_kw, @fuel_economy, @diagnostics.health * 100),
          tags: { kind: :telemetry }
        )
      end
    end
  end
end
