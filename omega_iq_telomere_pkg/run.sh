#!/bin/sh
# run.sh — build the APK, then launch it on the Bada runtime.
#
# On a BadaOS tablet the package installs and the MeasureActivity reads the IR
# camera + thermometer. Off-device this unpacks dist/bada_iq.apk into a work dir
# and runs app/main.bada through bin/run_iq (the Bada runtime), which falls back
# to the bundled thermal asset when no sensor node is present.
set -e
ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$ROOT"

sh build_apk.sh

WORK="dist/run"
rm -rf "$WORK"
mkdir -p "$WORK"
unzip -q -o dist/bada_iq.apk -d "$WORK"

echo "---- launching Bada IQ activity (app/main.bada) ----"
cd "$WORK"
ruby "$ROOT/bin/run_iq" app/main.bada
