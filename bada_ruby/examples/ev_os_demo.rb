# frozen_string_literal: true

# ev_os_demo.rb — drive BadaOS-EV through a full scenario.
#
#   ruby -Ilib examples/ev_os_demo.rb
#
# Boots the electric-vehicle OS, runs a drive cycle (launch -> cruise -> regen
# braking), fast-charges, and prints the instrument cluster plus the Ω::DATABASE
# black-box tail at each phase.

$LOAD_PATH.unshift(File.expand_path("../lib", __dir__))
require "bada"

def phase(title, ev)
  puts "\n#### #{title}"
  puts ev.dashboard
end

ev = Bada::EVOS::Vehicle.new(capacity_kwh: 60.0, dt: 1.0).boot
puts "BadaOS-EV booted — 60 kWh pack, #{ev.battery.series}s#{ev.battery.parallel}p"

# 1) Launch hard, then settle into a cruise.
ev.drive(0.9); ev.run(ticks: 6)
ev.drive(0.12); ev.run(ticks: 25)
phase("Cruise", ev)

# 2) Regenerative braking down to low speed.
ev.brake(0.6); ev.run(ticks: 15)
phase("Regen braking", ev)

# 3) Park & DC fast-charge.
ev.plug_in(:dc); ev.run(ticks: 50)
phase("DC fast charging", ev)

# 4) Black-box readout from Ω::DATABASE.
puts "\n#### Ω::DATABASE flight recorder (last 8 events)"
puts ev.recorder.tail(n: 8)
puts format("\nrecorded events: %d   event-stream Ξ: %.4f   final SOC: %.1f%%",
            ev.recorder.size, ev.recorder.recent_invariant, ev.battery.soc * 100)
