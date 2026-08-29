# PlanetCinema (見つかった惑星の動画館) — ネイティブ アプリ (APK / Windows / Ubuntu)

GammaTwin で発見した惑星の動画館。複素回転 e^{iωt}・特殊相対論(γ/D/光行差)・Jones熱の表面クラス・ケプラー軌道推定・.webm動画録画 (オフライン スナップショット内蔵)

| プラットフォーム | ファイル |
|---|---|
| Windows 10 / 11 | `PlanetCinema-*-x64.exe` |
| Ubuntu | `PlanetCinema-*-x86_64.AppImage` / `*-amd64.deb` |
| Android | `planetcinema-debug.apk` |

ビルドは [`space-apps-build.yml`](../../.github/workflows/space-apps-build.yml)。
ブランチ/`main` への push で自動ビルドされ、Actions の Artifacts
(`spaceapps-windows` / `spaceapps-linux` / `spaceapps-android`) から取得できます。
`space-v*` タグ / `workflow_dispatch` の `release_tag` で Release に添付。

```sh
node bada_gui_ide/tools/build-planet-cinema.js
cd bada_gui_ide/planetcinema-app/electron && npm install && npm start
npm run dist         # Windows EXE
npm run dist:linux   # Ubuntu AppImage / deb
```

ライブ表示にはインターネット接続が必要です(データは NASA/NOAA/NICT/EUMETSAT/CDS の
公開サーバーから直接読み込み)。オフライン時は内蔵スナップショット/フォールバックで動作します。
