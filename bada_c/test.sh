#!/bin/sh
# test.sh — build and exercise the C implementation of Bada.
set -e
cd "$(dirname "$0")"
fail=0
check() { # check <description> <expected-substring> <actual>
  if printf '%s' "$3" | grep -qF "$2"; then
    echo "ok   - $1"
  else
    echo "FAIL - $1 (expected '$2' in: $3)"; fail=1
  fi
}

echo "== building =="
cc -O2 -std=c11 bada.c -lm -o bada
echo "ok   - compiles"

echo "== interpreter =="
check "recursion+gamma" "fib=55 g=24" "$(./bada eval '
def fib(n) if n<2 return n end return fib(n-1)+fib(n-2) end
print "fib=" + str(fib(10)) + " g=" + str(gamma(5))')"

check "beta identity" "0.0833333" "$(./bada eval 'print str(beta(2,3))')"
check "cons lists" "[2, 3]" "$(./bada eval 'print str(cdr(list(1,2,3)))')"
check "xi trigger" "0.185528" "$(./bada eval 'print str(xi([0.5,0.25,0.25]))')"
check "long-string concat (no overflow)" "len = 5000" "$(./bada eval '
let s = ""
let i = 0
while i < 5000
  s = s + "x"
  i = i + 1
end
print "len = " + str(len(s))')"

echo "== objects (classes/objects are cons-lists) =="
OUT="$(./bada run examples/objects.bada)"
check "object method dispatch" "a.energy = 18" "$OUT"
check "thermal trigger fires" "trigger fired" "$OUT"

echo "== sound prover in Bada =="
OUT="$(./bada run examples/engine.bada)"
check "Fermat proved" "7 | n^7 - n (フェルマー) : 証明完了" "$OUT"
check "disproof n=2" "5 | n^2 - n : 反証 (反例 n=2)" "$OUT"
check "basal selects ch1" "選択チャネル 1" "$OUT"

echo "== compiler: build native executable =="
./bada build examples/engine.bada -o /tmp/bada_engine_bin >/dev/null 2>&1
check "compiled exe runs" "証明完了" "$(/tmp/bada_engine_bin)"

echo "== self-evolution (Bada writes Bada, gated by Xi) =="
./bada run examples/evolve.bada >/dev/null
check "evolved program runs" "evolved_energy(2,3) = 18.1861" "$(./bada run /tmp/bada_evolved.bada)"

echo
if [ $fail -eq 0 ]; then echo "ALL PASS"; else echo "SOME FAILED"; exit 1; fi
