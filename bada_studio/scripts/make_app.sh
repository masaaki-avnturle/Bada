#!/usr/bin/env bash
# Bada Studio — macOS .app バンドル + DMG / ZIP パッケージング
# 使い方: bash scripts/make_app.sh [バージョン]   (macOS 上で実行すること)
set -euo pipefail

cd "$(dirname "$0")/.."

VERSION="${1:-0.0.0-dev}"
APP_NAME="Bada Studio"
EXECUTABLE="BadaStudio"
BUNDLE_ID="io.github.masaaki-avnturle.bada-studio"

echo "==> swift build (release, universal)"
if swift build -c release --arch arm64 --arch x86_64; then
  BIN=".build/apple/Products/Release/${EXECUTABLE}"
else
  echo "==> ユニバーサルビルドに失敗。ホストアーキテクチャのみでリトライします"
  swift build -c release
  BIN=".build/release/${EXECUTABLE}"
fi

test -f "$BIN"

DIST="dist"
APP="$DIST/${APP_NAME}.app"
rm -rf "$DIST"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cp "$BIN" "$APP/Contents/MacOS/${EXECUTABLE}"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleDevelopmentRegion</key>
	<string>ja</string>
	<key>CFBundleDisplayName</key>
	<string>${APP_NAME}</string>
	<key>CFBundleExecutable</key>
	<string>${EXECUTABLE}</string>
	<key>CFBundleIdentifier</key>
	<string>${BUNDLE_ID}</string>
	<key>CFBundleInfoDictionaryVersion</key>
	<string>6.0</string>
	<key>CFBundleName</key>
	<string>${APP_NAME}</string>
	<key>CFBundlePackageType</key>
	<string>APPL</string>
	<key>CFBundleShortVersionString</key>
	<string>${VERSION}</string>
	<key>CFBundleVersion</key>
	<string>${VERSION}</string>
	<key>LSApplicationCategoryType</key>
	<string>public.app-category.music</string>
	<key>LSMinimumSystemVersion</key>
	<string>13.0</string>
	<key>NSHighResolutionCapable</key>
	<true/>
	<key>NSHumanReadableCopyright</key>
	<string>masaaki-avnturle / Bada</string>
</dict>
</plist>
PLIST

echo "==> ad-hoc 署名"
codesign --force --deep --sign - "$APP"

echo "==> ZIP 作成"
ditto -c -k --keepParent "$APP" "$DIST/BadaStudio-macOS-${VERSION}.zip"

echo "==> DMG 作成"
hdiutil create -volname "$APP_NAME" -srcfolder "$APP" -ov -format UDZO \
  "$DIST/BadaStudio-macOS-${VERSION}.dmg"

echo "==> 完了"
ls -la "$DIST"
