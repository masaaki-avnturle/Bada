# frozen_string_literal: true

# Bada::HEVOS — BadaOS-HEV, an operating system for a (full / series-parallel)
# hybrid electric vehicle, built on the Bada operator-algebra framework in pure
# Ruby. It reuses the BadaOS-EV kernel and subsystems and adds the hybrid core:
# an internal-combustion engine, a fuel system, an e-CVT power split, and an
# adaptive ECMS energy manager.
#
# The Bada framework does the hard control-theory work:
#
#   Bada::ErrorCorrection  -> stabilises the ECMS equivalence factor s
#   Bada::Manifold/Entropy -> Ξ drive-pattern classification + anomaly detect
#   Bada::TupleSpace       -> Ω::DATABASE flight recorder / black box
#   Bada::Special.x_log_x  -> engine BSFC / thermal-efficiency map
#
# Quick start:
#
#   require "bada"
#   hev = Bada::HEVOS::Vehicle.new.boot
#   hev.drive(0.5); hev.run(ticks: 40)
#   puts hev.dashboard
#
# Module map:
#   Bada::HEVOS::Engine             internal-combustion engine + BSFC map
#   Bada::HEVOS::FuelTank           gasoline tank + fuel-flow integration
#   Bada::HEVOS::EnergyManagement   adaptive ECMS energy manager (the brain)
#   Bada::HEVOS::HybridPowertrain   engine + motor + e-CVT power split + dynamics
#   Bada::HEVOS::Diagnostics        fault manager (fuel/engine/SOC + Ξ anomaly)
#   Bada::HEVOS::Dashboard          text HMI with live energy-flow display
#   Bada::HEVOS::Vehicle            facade tying the whole hybrid together
#
# (Battery management, thermal, sensors, kernel and the recorder are reused
#  from Bada::EVOS.)

require_relative "evos"
require_relative "hevos/vehicle"

module Bada
  module HEVOS
  end
end
