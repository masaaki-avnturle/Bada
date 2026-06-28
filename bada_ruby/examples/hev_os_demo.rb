# frozen_string_literal: true

# hev_os_demo.rb — drive BadaOS-HEV through a full scenario.
#
#   ruby -Ilib examples/hev_os_demo.rb
#
# Boots the hybrid-vehicle OS and runs a mixed drive cycle so every operating
# mode of the ECMS energy manager shows up: EV launch, engine cruise, battery
# boost, charge-sustaining, and regenerative braking — printing the instrument
# cluster (with the live energy-flow display) and the Ω::DATABASE black box.

$LOAD_PATH.unshift(File.expand_path("../lib", __dir__))
require "bada"

def phase(title, hev)
  puts "\n#### #{title}"
  puts hev.dashboard
end

hev = Bada::HEVOS::Vehicle.new(battery_kwh: 1.6, fuel_l: 40.0).boot
puts "BadaOS-HEV booted — #{format('%.1f', hev.battery.capacity_kwh)} kWh battery + " \
     "#{format('%.0f', hev.fuel.level_l)} L fuel"

# 1) Gentle city start — the manager runs on battery (engine off).
hev.drive(0.10); hev.run(ticks: 25)
phase("City — EV / charge-sustaining", hev)

# 2) Highway merge — hard demand pulls in the engine, battery boosts.
hev.drive(0.85); hev.run(ticks: 10)
phase("Highway merge — engine + boost", hev)

# 3) Steady highway cruise — engine at an efficient point.
hev.drive(0.18); hev.run(ticks: 30)
phase("Highway cruise", hev)

# 4) Off-ramp braking — regenerate into the pack.
hev.brake(0.6); hev.run(ticks: 15)
phase("Braking — regen", hev)

# 5) Black-box readout from Ω::DATABASE.
puts "\n#### Ω::DATABASE flight recorder (last 8 events)"
puts hev.recorder.tail(n: 8)
puts format("\nodometer %.1f km · fuel used %.2f L · economy %.1f km/L · final SOC %.0f%%",
            hev.odometer_km, hev.fuel.total_used_l, hev.fuel_economy, hev.battery.soc * 100)
