#!/usr/bin/env bash
# Build the Bada Forge APK.
#
# Requirements (one-time):
#   * JDK 17+            (java -version)
#   * Gradle 8+          (gradle -v)            -- installed at /opt/gradle here
#   * Android SDK with:  platform 34, build-tools 34, platform-tools
#       export ANDROID_HOME=/path/to/Android/Sdk
#     Install via Android Studio, or the command-line tools:
#       sdkmanager "platforms;android-34" "build-tools;34.0.0" "platform-tools"
#
# Then:
#   ./build_apk.sh
# produces:  app/build/outputs/apk/debug/app-debug.apk
#
# Refresh the embedded IDE from the Bada source first:
#   (cd .. && ./bada run apps/bada_forge.bada && cp bada_forge.html forge_android/app/src/main/assets/index.html)

set -e
cd "$(dirname "$0")"

if [ -z "$ANDROID_HOME" ] && [ -z "$ANDROID_SDK_ROOT" ]; then
  echo "ERROR: set ANDROID_HOME (or ANDROID_SDK_ROOT) to your Android SDK." >&2
  echo "       The SDK download (dl.google.com) is blocked in the Bada cloud" >&2
  echo "       sandbox, so build this step on a machine with the SDK installed." >&2
  exit 1
fi

echo "sdk.dir=${ANDROID_HOME:-$ANDROID_SDK_ROOT}" > local.properties
gradle assembleDebug --no-daemon
echo
echo "APK: $(pwd)/app/build/outputs/apk/debug/app-debug.apk"
