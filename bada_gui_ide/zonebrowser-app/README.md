# ZoneBrowser — ウルトラネットワーク専用ブラウザ (ネイティブ アプリ)

`zone://` ウルトラネットワーク WWW の専用ブラウザ **ZoneBrowser** を、
**Windows 10/11・Ubuntu・Android** のネイティブ アプリとしてパッケージします。

ZoneBrowser 本体 (`www/index.html`) は完全自己完結の HTML で、Bada 言語コア・
zone:// ランタイム (`../browser/zone-lib.bada`)・ゾーンサイト (`../browser/zone-site.json`)
を同梱しています。`node ../tools/build-zone-browser.js` で生成されます
(この `www/index.html` はビルド生成物のため git 管理外)。

## ディレクトリ構成

```
zonebrowser-app/
  www/index.html   ZoneBrowser 本体 (自己完結・ビルド時に生成)
  electron/        Windows EXE / Ubuntu AppImage・deb ラッパー
  cordova/         Android APK 設定
```

## 入手 (Releases)

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|---|---|
| Windows 10 / 11 | `ZoneBrowser-*-x64.exe` (NSIS インストーラ / ポータブル) |
| Ubuntu | `ZoneBrowser-*-x64.AppImage` / `ZoneBrowser-*-x64.deb` |
| Android | `zonebrowser-debug.apk` |

ビルドは GitHub Actions [`zonebrowser-app-build.yml`](../../.github/workflows/zonebrowser-app-build.yml)
が行います。`zonebrowser-v*` タグの push で Release に自動添付、`workflow_dispatch`
でも Actions アーティファクトとして取得できます。

## ローカルでのビルド / 起動

```sh
# ZoneBrowser 本体 (www/index.html) を生成
node bada_gui_ide/tools/build-zone-browser.js

# デスクトップ (Electron) — 起動
cd bada_gui_ide/zonebrowser-app/electron && npm install && npm start

# Windows EXE / Ubuntu AppImage・deb
npm run dist         # Windows (要 Windows もしくは wine)
npm run dist:linux   # Ubuntu

# Android APK (Cordova)
cordova create cordova-build io.github.masaaki_avnturle.zonebrowser ZoneBrowser
cp -r bada_gui_ide/zonebrowser-app/www cordova-build/www
cp bada_gui_ide/zonebrowser-app/cordova/config.xml cordova-build/config.xml
cd cordova-build && cordova platform add android@12.0.1 && cordova build android
```

## 使い方

アプリを起動し、アドレスバーに `zone://url.or.jp/` と入力して開きます。
P2P リング DHT でページを解決し、Bell 対 QKD でセッション鍵を合意、ゾーンの
結び目から導いた Jones 鍵で本文を復号して表示します。右のセキュリティパネルに
DHT 鍵・経路・Jones 鍵・AEAD タグ・暗号文が表示されます。
