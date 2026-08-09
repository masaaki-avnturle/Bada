#!/bin/sh
# roundtrip.sh — end-to-end test of encrypt/decrypt with the example knots.
# Usage: sh tests/roundtrip.sh [path-to-binary]
set -e
BIN="${1:-./build/omega_quantum_decrypted}"
DIR="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

msg="$DIR/examples/message.txt"
[ -f "$msg" ] || { printf 'The quick brown fox.\n' > "$TMP/msg.txt"; msg="$TMP/msg.txt"; }

fail() { echo "FAIL: $1" >&2; exit 1; }

echo "[roundtrip] encrypt with trefoil key"
"$BIN" encrypt "$DIR/examples/trefoil.knot" "$msg" "$TMP/a.oqd" >/dev/null

echo "[roundtrip] decrypt with trefoil key"
"$BIN" decrypt "$DIR/examples/trefoil.knot" "$TMP/a.oqd" "$TMP/a.out" >/dev/null
cmp -s "$msg" "$TMP/a.out" || fail "trefoil round-trip mismatch"

echo "[roundtrip] wrong knot key must be rejected"
if "$BIN" decrypt "$DIR/examples/figure8.knot" "$TMP/a.oqd" "$TMP/a.bad" >/dev/null 2>&1; then
    fail "figure-8 key wrongly accepted"
fi

echo "[roundtrip] passphrase binding"
"$BIN" encrypt "$DIR/examples/trefoil.knot" "$msg" "$TMP/b.oqd" -p secret >/dev/null
"$BIN" decrypt "$DIR/examples/trefoil.knot" "$TMP/b.oqd" "$TMP/b.out" -p secret >/dev/null
cmp -s "$msg" "$TMP/b.out" || fail "passphrase round-trip mismatch"
if "$BIN" decrypt "$DIR/examples/trefoil.knot" "$TMP/b.oqd" "$TMP/b.bad" -p nope >/dev/null 2>&1; then
    fail "wrong passphrase wrongly accepted"
fi

echo "[roundtrip] tamper detection"
"$BIN" encrypt "$DIR/examples/trefoil.knot" "$msg" "$TMP/c.oqd" >/dev/null
# flip a byte in the ciphertext region (offset 60)
dd if="$TMP/c.oqd" of="$TMP/c.head" bs=1 count=60 2>/dev/null
printf '\xff' > "$TMP/c.flip"
tail -c +62 "$TMP/c.oqd" > "$TMP/c.tail"
cat "$TMP/c.head" "$TMP/c.flip" "$TMP/c.tail" > "$TMP/c.oqd"
if "$BIN" decrypt "$DIR/examples/trefoil.knot" "$TMP/c.oqd" "$TMP/c.bad" >/dev/null 2>&1; then
    fail "tampered ciphertext wrongly accepted"
fi

echo "[roundtrip] ALL PASS"
