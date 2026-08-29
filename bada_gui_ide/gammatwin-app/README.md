# GammaTwin (地球型惑星ファインダー) — ネイティブ アプリ (APK / Windows / Ubuntu)

NASA Exoplanet Archive(Kepler/TESS 宇宙望遠鏡カタログ)から地球と境遇が同型な惑星を発見・ランキング。Γ重みESI + Jones多項式熱感知 + 銀河マップ + 実サーベイ望遠鏡ビュー (オフライン スナップショット内蔵)

| プラットフォーム | ファイル |
|---|---|
| Windows 10 / 11 | `GammaTwin-*-x64.exe` |
| Ubuntu | `GammaTwin-*-x86_64.AppImage` / `*-amd64.deb` |
| Android | `gammatwin-debug.apk` |

ビルドは [`space-apps-build.yml`](../../.github/workflows/space-apps-build.yml)。
ブランチ/`main` への push で自動ビルドされ、Actions の Artifacts
(`spaceapps-windows` / `spaceapps-linux` / `spaceapps-android`) から取得できます。
`space-v*` タグ / `workflow_dispatch` の `release_tag` で Release に添付。

```sh
node bada_gui_ide/tools/build-earth-twin.js
cd bada_gui_ide/gammatwin-app/electron && npm install && npm start
npm run dist         # Windows EXE
npm run dist:linux   # Ubuntu AppImage / deb
```

ライブ表示にはインターネット接続が必要です(データは NASA/NOAA/NICT/EUMETSAT/CDS の
公開サーバーから直接読み込み)。オフライン時は内蔵スナップショット/フォールバックで動作します。
