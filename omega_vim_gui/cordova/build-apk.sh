#!/usr/bin/env bash
# build-apk.sh — reproducibly build the Ω-Vim Android APK from www/ + config.xml.
#
# This is the exact, pinned recipe the CI workflow uses. Run it on any machine
# (or CI runner) that can reach the Android SDK repository (dl.google.com).
#
# Requirements auto-checked/installed where possible:
#   - JDK 17            (cordova-android 12 requires exactly 17)
#   - Node 18+ / npm
#   - Android SDK       (platform-tools, platforms;android-33, build-tools;33.0.2)
#   - cordova 12.0.0    (pinned)   + cordova-android 12.0.1 (pinned)
#
# Output: dist/omega-vim-debug.apk
#
# Usage:
#   bash cordova/build-apk.sh                 # debug APK (sideloadable)
#   ANDROID_SDK_ROOT=/path bash cordova/build-apk.sh
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"     # omega_vim_gui/
WWW="$HERE/www"
CONFIG="$HERE/cordova/config.xml"
OUT="$HERE/dist"
WORK="${WORK:-$HERE/.apk-build}"

CORDOVA_VERSION="${CORDOVA_VERSION:-12.0.0}"
CORDOVA_ANDROID="${CORDOVA_ANDROID:-12.0.1}"
ANDROID_PLATFORM="${ANDROID_PLATFORM:-android-33}"
ANDROID_BUILDTOOLS="${ANDROID_BUILDTOOLS:-33.0.2}"

echo "==> Ω-Vim APK build"
command -v node >/dev/null || { echo "node is required"; exit 1; }

# --- JDK 17 ---------------------------------------------------------------
if [ -z "${JAVA_HOME:-}" ] || ! "$JAVA_HOME/bin/java" -version 2>&1 | grep -q '"17'; then
  for j in /usr/lib/jvm/java-17-openjdk-amd64 /usr/lib/jvm/temurin-17-jdk-amd64 \
           /Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home; do
    [ -x "$j/bin/java" ] && export JAVA_HOME="$j" && break
  done
fi
echo "    JAVA_HOME=${JAVA_HOME:-<unset>}"
"$JAVA_HOME/bin/java" -version 2>&1 | head -1 || { echo "JDK 17 not found — install it first"; exit 1; }
export PATH="$JAVA_HOME/bin:$PATH"

# --- Android SDK ----------------------------------------------------------
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-$HOME/android-sdk}}"
export ANDROID_HOME="$ANDROID_SDK_ROOT"
SDKMANAGER="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager"
if [ ! -x "$SDKMANAGER" ]; then
  echo "    installing Android command-line tools into $ANDROID_SDK_ROOT"
  mkdir -p "$ANDROID_SDK_ROOT/cmdline-tools"
  TMPZIP="$(mktemp -u).zip"
  curl -fsSL -o "$TMPZIP" "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
  unzip -q "$TMPZIP" -d "$ANDROID_SDK_ROOT/cmdline-tools"
  mv "$ANDROID_SDK_ROOT/cmdline-tools/cmdline-tools" "$ANDROID_SDK_ROOT/cmdline-tools/latest"
  rm -f "$TMPZIP"
fi
yes | "$SDKMANAGER" --licenses >/dev/null 2>&1 || true
"$SDKMANAGER" "platform-tools" "platforms;$ANDROID_PLATFORM" "build-tools;$ANDROID_BUILDTOOLS"

# --- cordova --------------------------------------------------------------
if ! command -v cordova >/dev/null || [ "$(cordova --version 2>/dev/null | cut -d. -f1)" != "12" ]; then
  echo "    installing cordova@$CORDOVA_VERSION"
  npm install -g "cordova@$CORDOVA_VERSION"
fi

# --- assemble & build -----------------------------------------------------
rm -rf "$WORK"
cordova create "$WORK" io.github.masaaki_avnturle.omega_vim OmegaVim
rm -rf "$WORK/www"
cp -r "$WWW" "$WORK/www"
cp "$CONFIG" "$WORK/config.xml"

pushd "$WORK" >/dev/null
cordova platform add "android@$CORDOVA_ANDROID"
cordova build android --verbose
popd >/dev/null

mkdir -p "$OUT"
APK="$(find "$WORK/platforms/android/app/build/outputs/apk/debug" -name '*.apk' | head -1)"
cp "$APK" "$OUT/omega-vim-debug.apk"
echo "==> APK ready: $OUT/omega-vim-debug.apk"
ls -la "$OUT/omega-vim-debug.apk"
