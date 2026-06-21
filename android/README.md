# Bada Hologram — Android app (APK)

Packages the hologram apps into a downloadable **Android APK**. The apps are
self-contained HTML/canvas (the Bada-computed frames are embedded as JSON), so
they run **offline in a WebView** — no server, no network permission.

Bundled apps (launcher menu = `assets/holograms/index.html`):
- **Spatial Hologram** — Vision-Pro-equivalent passthrough (apps float out of the
  transparent tablet)
- **Hologram Display** — reflection pyramid / free view
- **Float-up Hologram** — video floats up out of the conductive-plastic tablet
  (Jones-polynomial relief + power model)
- **Holographic HHKB** — the Happy Hacking Keyboard floating as a hologram
- **Mirror App** — smartphone mirror over the tablet, aerial display / aerial HHKB
  at the eyeglass-lens focus

## Download the APK
Every push to the app (or a manual run of the **Build Bada Hologram APK**
workflow) builds the APK and publishes it:
- as a **Release** asset — `bada-hologram.apk` under the `hologram-apk` release
  (a stable download link), and
- as a **workflow artifact** (`bada-hologram-apk`) on the Actions run.

Install it on Android (enable *Install unknown apps* for your browser/files app).

## Build it yourself
```
# 1) render the bundled assets from the Bada apps
python3 android/generate_assets.py

# 2) build the APK  (needs JDK 17 + Android SDK; Gradle 8.7)
cd android
gradle assembleDebug          # or open the folder in Android Studio and Run
# -> app/build/outputs/apk/debug/app-debug.apk
```

## Layout
```
android/
  generate_assets.py            renders the hologram HTML into assets/ (from Bada)
  settings.gradle, build.gradle, gradle.properties
  app/
    build.gradle                dependency-free (plain Activity + WebView)
    src/main/AndroidManifest.xml
    src/main/java/com/bada/hologram/MainActivity.java
    src/main/assets/holograms/  the bundled, self-contained app HTML + index menu
    src/main/res/               launcher icon (vector) + strings
```
The CI workflow lives at `.github/workflows/android-apk.yml`.
