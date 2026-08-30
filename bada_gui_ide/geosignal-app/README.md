# GeoSignal (地球の伝達使用地点シアター) — ネイティブ アプリ (APK / Windows / Ubuntu)

電磁波・重力チャネルが実際に使われている地球上の実在地点(臼田64m・野辺山45m・KAGRA・
Goldstone・Green Bank・FAST・LIGO×2・Virgo・ALMA・アレシボ跡 等)を、宇宙→地表の
連続ズーム動画(公開タイル合成・.webm録画可)で見るアプリ。ISS のライブ位置も表示。

| プラットフォーム | ファイル |
|---|---|
| Windows 10 / 11 | `GeoSignal-*-x64.exe` |
| Ubuntu | `GeoSignal-*-x86_64.AppImage` / `*-amd64.deb` |
| Android | `geosignal-debug.apk` |

ビルドは [`space-apps-build.yml`](../../.github/workflows/space-apps-build.yml) (Artifacts: spaceapps-*)。

```sh
node bada_gui_ide/tools/build-geo-signal.js
cd bada_gui_ide/geosignal-app/electron && npm install && npm start
```
