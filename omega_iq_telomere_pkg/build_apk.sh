#!/bin/sh
# build_apk.sh — assemble the Bada IQ app into an APK-format package.
#
# The .apk is a ZIP (the Android package format) laid out the standard way:
#   AndroidManifest.xml, bada_apk.json, app/, lib/, assets/, res/, META-INF/
# It carries the Bada runtime (lib/omega_iq + app/main.bada) instead of a
# compiled Dalvik classes.dex, so it runs on the BadaOS runtime / desktop via
# `bin/run_iq` (see run.sh). A SHA-256 manifest is written to META-INF.
set -e
ROOT=$(cd "$(dirname "$0")" && pwd)
cd "$ROOT"

APK="dist/bada_iq.apk"
mkdir -p dist META-INF

# 1. checksum manifest (a lightweight stand-in for APK signing)
: > META-INF/MANIFEST.MF
echo "Manifest-Version: 1.0" >> META-INF/MANIFEST.MF
echo "Created-By: bada build_apk.sh" >> META-INF/MANIFEST.MF
echo "" >> META-INF/MANIFEST.MF
find AndroidManifest.xml bada_apk.json app lib assets res -type f | sort | while read -r f; do
  sum=$(sha256sum "$f" | cut -d' ' -f1)
  echo "Name: $f" >> META-INF/MANIFEST.MF
  echo "SHA-256-Digest: $sum" >> META-INF/MANIFEST.MF
  echo "" >> META-INF/MANIFEST.MF
done

# 2. zip everything into the .apk (exclude build output and caches)
rm -f "$APK"
zip -q -r -X "$APK" \
  AndroidManifest.xml bada_apk.json \
  app lib assets res META-INF/MANIFEST.MF \
  -x '*.pyc' -x '*/__pycache__/*' -x 'dist/*'

echo "built $APK"
unzip -l "$APK" | tail -n +2 | head -n 40
