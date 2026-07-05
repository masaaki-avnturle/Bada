# frozen_string_literal: true

# Tests for the Bada IQ / telomere-Jones engine.
# Run: ruby test/test_iq.rb   (no external gems)
Encoding.default_external = Encoding::UTF_8
$LOAD_PATH.unshift File.expand_path("../lib", __dir__)
require "omega_iq"

include OmegaIQ

$failures = 0
def check(name)
  ok = yield
  puts "#{ok ? 'ok  ' : 'FAIL'}  #{name}"
  $failures += 1 unless ok
end

# --- Laurent polynomial algebra ---
check("Laurent multiply") do
  p = Laurent.new(1 => 1, 0 => 1)          # A + 1
  (p * p).terms == { 2 => 1, 1 => 2, 0 => 1 } # A^2 + 2A + 1
end

check("Laurent pow(0) is 1") { Laurent.new(3 => 5).pow(0).terms == { 0 => 1 } }

# --- Jones engine: known knots ---
check("unknot V(t) == 1") { Jones.polynomial([]).terms == { 0 => 1 } }

# The bundled drawing (pentagram) is the cinquefoil 5_1. Its Jones polynomial is
# one of the two chiralities of  -t^-7 + t^-6 - t^-5 + t^-4 + t^-2.
DIAGRAM = File.expand_path("../assets/diagram_arrows.txt", __dir__)
cross = Drawing.load(DIAGRAM).analyse.crossings

check("drawing yields 5 crossings") { cross.length == 5 }

def poly_hash(laurent, scale = 4)
  laurent.terms.transform_keys { |e| Rational(e, scale) }
end

cinquefoil = { Rational(-7) => -1, Rational(-6) => 1, Rational(-5) => -1,
               Rational(-4) => 1, Rational(-2) => 1 }

check("cinquefoil Jones (mirror matches 5_1)") do
  poly_hash(Jones.polynomial(Jones.mirror(cross))) == cinquefoil
end

check("V and 真逆 are mirror pair V(t) <-> V(1/t)") do
  fwd = poly_hash(Jones.polynomial(cross))
  rev = poly_hash(Jones.polynomial(Jones.mirror(cross)))
  fwd == rev.transform_keys(&:-@)
end

check("integer t-powers (knot, not link)") do
  Jones.polynomial(cross).terms.keys.all? { |e| (e % 4).zero? }
end

# --- Telomere splitting ---
tel = Telomere.new(cross).divide
check("Hayflick limit == crossing number") { tel.hayflick_limit == 5 }
check("division reaches senescence") { tel.generations.last[:senescent] }
check("split entropy positive") { tel.entropy > 0 }

# --- Thermal sensor ---
th = Thermal.read(File.expand_path("../assets/thermal_frame.pgm", __dir__))
check("thermal mean in physiological band") { th.mean_c > 20 && th.mean_c < 45 }
check("thermal coherence in [0,1]") { th.coherence >= 0 && th.coherence <= 1 }
check("t_eval in (0,1)") { th.t_eval > 0 && th.t_eval < 1 }

# --- IQ measurement (forward + 真逆) ---
m = IQ.new(cross, t_eval: th.t_eval, coherence: th.coherence).measure
check("IQ is a finite number") { m[:iq].is_a?(Numeric) && m[:iq].finite? }
check("mirror IQ present") { m[:mirror_iq].is_a?(Numeric) }
check("divergence >= 0") { m[:divergence] >= 0 }
check("components normalised to [0,1]") do
  m[:forward][:components].values.all? { |v| v >= 0 && v <= 1 }
end

# --- Bada runtime executes the app ---
out = BadaRuntime.new(base_dir: File.expand_path("..", __dir__)).run(
  File.read(File.expand_path("../app/main.bada", __dir__), encoding: "UTF-8")
)
check("bada app emits Jones line") { out.any? { |l| l.include?("V(t)") } }
check("bada app emits IQ line") { out.any? { |l| l.include?("IQ") } }

puts($failures.zero? ? "\nALL PASS" : "\n#{$failures} FAILURE(S)")
exit($failures.zero? ? 0 : 1)
