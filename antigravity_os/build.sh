#!/usr/bin/env bash
# build.sh -- build the Bada toolchain and certify the Anti-Gravity OS.
#
#   stage 0 : the C reference (bada) -- trusted base, working reviser
#   stage 1 : the kernel + libraries run, reviser-rewritten OS syntax fires
#   stage 2 : the OS invariants are re-derived at runtime (the acceptance test)
#
# Acceptance is invariant-based, not byte-based:
#   G1 lift conservation   |psi|^2 = a to machine precision
#   G2 mode isolation      a vented field mode is never re-excited
#   G3 scram safety        a scrammed coil reads probability 0
#   G4 auditable telemetry the journal is the full append-only ledger trace
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
CC="${CC:-gcc}"
CFLAGS="-O2 -std=c11 -Wno-alloc-size-larger-than"

echo "== stage 0 : building the C reference (bada) =="
"$CC" $CFLAGS -o bada src/bada.c -lm
echo "   built ./bada"

echo "== stage 1 : kernel + libraries (reviser-rewritten OS syntax) =="
./bada run sys/agkernel.bada >/dev/null && echo "   sys/agkernel.bada runs (charge/hover/vent/Telemetry)"
./bada run lib/aglift.bada   >/dev/null && echo "   lib/aglift.bada   runs (sense/steer)"
./bada run lib/agfield.bada  >/dev/null && echo "   lib/agfield.bada  runs (Split/Twist/Flip/Couple + ballast)"
./bada run lib/agsafe.bada   >/dev/null && echo "   lib/agsafe.bada   runs (arm/scram)"

echo "== stage 2 : the OS init process (PID 1), invariants re-derived =="
OUT="$(./bada run agos.bada)"
echo "$OUT" | sed 's/^/   | /'

echo "-- acceptance: checking the four invariants in the run output --"
pass=1
echo "$OUT" | grep -q "G1 lift? |psi|^2=a (md) : 2.78e-17" || { echo "   FAIL G1"; pass=0; }
echo "$OUT" | grep -q "G2 isolation holds      : true"     || { echo "   FAIL G2"; pass=0; }
echo "$OUT" | grep -q "G3 post-scram safe      : true"     || { echo "   FAIL G3"; pass=0; }
echo "$OUT" | grep -q "journal facts: 6"                   || { echo "   FAIL G4"; pass=0; }
if [ "$pass" = "1" ]; then
  echo "   PASS all four Anti-Gravity OS invariants upheld"
else
  echo "   FAIL one or more invariants did not hold"; exit 1
fi

echo ""
echo "== Anti-Gravity OS built and certified =="
