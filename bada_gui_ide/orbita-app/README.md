# Orbita (衛星から見る地球) — ネイティブ アプリ (APK / Windows / Ubuntu)

誰でも自由にアクセスできる公開衛星(Himawari-9/GOES/Meteosat/NASA EPIC)から宇宙から見た地球をライブ表示・動画再生 + NOAA/ISS パス予報 (要ネット)

| プラットフォーム | ファイル |
|---|---|
| Windows 10 / 11 | `Orbita-*-x64.exe` |
| Ubuntu | `Orbita-*-x86_64.AppImage` / `*-amd64.deb` |
| Android | `orbita-debug.apk` |

ビルドは [`space-apps-build.yml`](../../.github/workflows/space-apps-build.yml)。
ブランチ/`main` への push で自動ビルドされ、Actions の Artifacts
(`spaceapps-windows` / `spaceapps-linux` / `spaceapps-android`) から取得できます。
`space-v*` タグ / `workflow_dispatch` の `release_tag` で Release に添付。

```sh
node bada_gui_ide/tools/build-earth-view.js
cd bada_gui_ide/orbita-app/electron && npm install && npm start
npm run dist         # Windows EXE
npm run dist:linux   # Ubuntu AppImage / deb
```

ライブ表示にはインターネット接続が必要です(データは NASA/NOAA/NICT/EUMETSAT/CDS の
公開サーバーから直接読み込み)。オフライン時は内蔵スナップショット/フォールバックで動作します。
