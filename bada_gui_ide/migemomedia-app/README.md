# Migemogram Media — ネイティブ アプリ + Google 連携 (APK / Windows / Ubuntu)

自分のPC/クラウドの写真・動画を Instagram 風に見て、zone://url.or.jp に取り込む
アプリ **Migemogram Media** を、**Windows 10/11・Ubuntu・Android** のネイティブ
アプリとしてパッケージします。あわせて **Google Drive / Google Photos の実 OAuth
連携**を備えます。

## Google 連携 (Drive / Photos) — 使い方

1. **自分の OAuth クライアントID** を用意します(Google Cloud Console → API とサービス →
   認証情報 → 「OAuth 2.0 クライアント ID」→ アプリの種類「ウェブ アプリケーション」)。
   スコープ: `drive.readonly`, `photoslibrary.readonly`(OAuth 同意画面で有効化)。
2. **承認済みの JavaScript 生成元** に、アプリを開いている生成元を登録します。
   - **デスクトップ版**: 本アプリは内部の localhost サーバで配信するため、起動時の
     `http://127.0.0.1:<ポート>` を登録します(ポートは毎回変わる場合があるので、
     固定したい場合は `electron/main.js` の `server.listen(0, ...)` を固定ポートに変更)。
   - **ホスト版**: HTTPS でホストした URL を登録。
   - `file://` は Google のサインインで使用できません。
3. アプリの「☁ Google接続」→ クライアントID を入力 → 接続 → 「Drive から読み込む」/
   「Photos から読み込む」。
4. **Android (WebView)** は Google の OAuth を弾くことが多いため、Android では手動URL/
   端末内メディアの取り込みをご利用ください(実機の Photos は端末のギャラリーから選択)。

未接続・オフライン時は、「＋ PCから追加」「🔗 URL追加」に自動フォールバックします。

## 構成 / 入手

```
migemomedia-app/
  www/index.html   本体 (自己完結・ビルド時に生成)
  electron/        Windows EXE / Ubuntu AppImage・deb (localhost 配信で OAuth 対応)
  cordova/         Android APK 設定
```

| プラットフォーム | ファイル |
|---|---|
| Windows 10 / 11 | `Migemogram-Media-*-x64.exe` |
| Ubuntu | `Migemogram-Media-*-x86_64.AppImage` / `*-amd64.deb` |
| Android | `migemogram-media-debug.apk` |

ビルドは [`migemomedia-app-build.yml`](../../.github/workflows/migemomedia-app-build.yml)。
ブランチ/`main` への push で自動ビルドされ、Actions の Artifacts から取得できます。
`migemomedia-v*` タグ / `workflow_dispatch` で Release に添付。

```sh
node bada_gui_ide/tools/build-migemo-media.js
cd bada_gui_ide/migemomedia-app/electron && npm install && npm start
npm run dist         # Windows EXE
npm run dist:linux   # Ubuntu AppImage / deb
```
