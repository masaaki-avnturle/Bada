#!/usr/bin/env bash
# build_apk.sh — package the Bada XP PWA (mobile/www) into an installable
# Android APK using the WebView wrapper in mobile/android.
#
# Requirements:
#   - JDK 17+         (java -version)
#   - Gradle 8.7+     (gradle -v)   — or run via Android Studio
#   - Android SDK     (ANDROID_HOME / ANDROID_SDK_ROOT set, platform 34 + build-tools)
#
# Usage:  bash mobile/build_apk.sh   ->   mobile/android/app/build/outputs/apk/debug/app-debug.apk
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
www="$here/www"
android="$here/android"
assets="$android/app/src/main/assets/www"

echo "→ bundling PWA  $www  →  assets/www"
rm -rf "$assets"
mkdir -p "$assets"
cp -R "$www/." "$assets/"

if [ -z "${ANDROID_HOME:-}${ANDROID_SDK_ROOT:-}" ]; then
  cat >&2 <<'EOF'

⚠  Android SDK not found (ANDROID_HOME / ANDROID_SDK_ROOT unset).
   The web assets are bundled, but compiling the APK needs the Android SDK.
   Either:
     • open  mobile/android  in Android Studio and press Run, or
     • install the SDK (platform-34 + build-tools), set ANDROID_HOME, then re-run.
EOF
  exit 2
fi

echo "→ gradle assembleDebug"
cd "$android"
if [ -x ./gradlew ]; then ./gradlew assembleDebug; else gradle assembleDebug; fi

apk="$android/app/build/outputs/apk/debug/app-debug.apk"
echo
if [ -f "$apk" ]; then
  echo "✓ APK ready: $apk"
  echo "  install on a device:  adb install -r \"$apk\""
else
  echo "✗ build finished but APK not found at $apk" >&2
  exit 1
fi
