# Zone Studio — ネイティブ アプリ (APK / Windows / Ubuntu)

`zone://` URI で自分の WWW を構築・公開するアプリ **Zone Studio** を、
**Windows 10/11・Ubuntu・Android** のネイティブ アプリとしてパッケージします。

本体 (`www/index.html`) は完全自己完結の HTML で、Bada 言語コア・zone://
ランタイム(`../browser/zone-lib.bada`)・NGN 拡張(`../ngngrid/ngn-extra.bada`)
を同梱します。`node ../tools/build-zone-studio.js` で生成されます
(この `www/index.html` はビルド生成物のため git 管理外)。

## ディレクトリ構成

```
zonestudio-app/
  www/index.html   Zone Studio 本体 (自己完結・ビルド時に生成)
  electron/        Windows EXE / Ubuntu AppImage・deb ラッパー
  cordova/         Android APK 設定
```

## 入手 (Releases)

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|---|---|
| Windows 10 / 11 | `Zone-Studio-*-x64.exe` (NSIS インストーラ / ポータブル) |
| Ubuntu | `Zone-Studio-*-x86_64.AppImage` / `Zone-Studio-*-amd64.deb` |
| Android | `zone-studio-debug.apk` |

ビルドは GitHub Actions [`zonestudio-app-build.yml`](../../.github/workflows/zonestudio-app-build.yml)
が行います。`zonestudio-v*` タグの push で Release に自動添付、`workflow_dispatch`
でも Actions アーティファクトとして取得できます(このブランチ/`main` への
push でも自動ビルドされ、Actions の Artifacts から取得可)。

## ローカルでのビルド / 起動

```sh
node bada_gui_ide/tools/build-zone-studio.js       # 本体 www/index.html を生成
cd bada_gui_ide/zonestudio-app/electron && npm install && npm start   # 起動
npm run dist         # Windows EXE
npm run dist:linux   # Ubuntu AppImage / deb
```
