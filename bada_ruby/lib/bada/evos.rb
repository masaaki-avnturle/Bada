# frozen_string_literal: true

# Bada::EVOS — BadaOS-EV, an operating system for an electric vehicle, built
# from scratch on the Bada operator-algebra framework (pure Ruby, no deps).
#
# The OS is a soft-real-time control loop. A priority/period kernel schedules
# every subsystem of the car each control cycle, and the Bada framework's own
# primitives do the heavy lifting:
#
#   Bada::ErrorCorrection  -> sensor fusion (relativistic-top integrable system)
#   Bada::TupleSpace       -> Ω::DATABASE flight recorder / black box
#   Bada::Manifold/Entropy -> Ξ-invariant condition monitoring & anomaly detect
#   Bada::BadaNode (>-)    -> coolant ramp law e^{-x log x}
#   Bada::Special.x_log_x  -> drive-line efficiency map (Napier circle)
#
# Quick start:
#
#   require "bada"
#   ev = Bada::EVOS::Vehicle.new(capacity_kwh: 60.0).boot
#   ev.drive(0.6)
#   ev.run(ticks: 30)
#   puts ev.dashboard
#
# Module map:
#   Bada::EVOS::Scheduler       real-time priority/period kernel
#   Bada::EVOS::Sensor          error-corrected physical sensor
#   Bada::EVOS::BatteryPack     BMS: SOC, voltage, self-heat, cell balancing
#   Bada::EVOS::Powertrain      motor/inverter control + longitudinal model
#   Bada::EVOS::Thermal         battery/cabin thermal management
#   Bada::EVOS::Charger         CC/CV charging controller
#   Bada::EVOS::RangeEstimator  consumption + range prediction
#   Bada::EVOS::Diagnostics     fault manager + Ξ anomaly detection
#   Bada::EVOS::Recorder        Ω::DATABASE black box
#   Bada::EVOS::Dashboard       text HMI / instrument cluster
#   Bada::EVOS::Vehicle         facade tying the whole car together

require_relative "evos/vehicle"

module Bada
  module EVOS
  end
end
