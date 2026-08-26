# omega-debug.keystore — アプリ署名鍵（デバッグ用・固定）

bio_medicine の各アプリ（Android APK）を **常に同じ鍵で署名**するための keystore です。

## なぜ必要か

GitHub Actions のランナーには `~/.android/debug.keystore` が存在しないため、
Android Gradle Plugin が**ビルドのたびにランダムな鍵を新規生成**します。
その結果、パッケージ名が同じでも署名証明書が毎回変わり、端末に入っている旧版の上へ
インストールしようとすると **署名不一致で「アプリがインストールされていません」** となります。

この keystore を `~/.android/debug.keystore` として配置することで、すべてのビルドが
同じ証明書で署名され、**上書き更新できる**ようになります。

## 指紋（この鍵で署名されたことの確認用）

```
SHA-256: fc3547e2fe491f44ce3e472cf3928af6c9c250e3a02ee0821a85a3a304cc0d55
```

ワークフローはビルド後に `apksigner verify --print-certs` で実際の署名を取得し、
この値と一致しなければビルドを失敗させます（署名が再びぶれないことの保証）。

## 注意

- これは**デバッグ用の鍵**で、パスワードは Android 標準の `android`（alias: `androiddebugkey`）です。
  リポジトリに含まれている以上、**秘密ではありません**。
- Google Play などのストア配布には使えません。配布する場合は別途リリース鍵を作成し、
  GitHub Secrets に格納してください。
- 目的は「配布した APK を上書き更新できるようにすること」だけです。
