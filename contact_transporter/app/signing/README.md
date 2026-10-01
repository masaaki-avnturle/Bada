# 署名鍵

## アプリ本体の固定鍵 (bada-apps-*) — 上書きインストールでアップデートするため

Actions がビルドする全アプリ (ContactGPT / 輸送機 3D CAD / UFO 設計図面 / BadaClaude / Bada 統合スタジオ) は、
**毎回この同じ鍵で署名**します。アプリ ID・ファイル名・署名が同じで、バージョンだけが大きくなるので、
新しい版をそのまま開けば上書きでアップデートされます (設定・作ったアプリ・学習した重みはそのまま)。

- `bada-apps-key.pk8` — PKCS#8 秘密鍵 (RSA 3072、暗号化なし)
- `bada-apps-cert.der` — X.509 証明書 (CN=Bada Apps, O=masaaki-avnturle Bada, C=JP、2056 年まで、コード署名用)
  SHA-256 指紋 `B4:9C:BD:46:A9:36:A5:50:90:57:76:E9:E4:C5:B9:32:1A:4A:03:EB:E6:92:1E:F9:34:F0:11:87:92:DC:D0:31`
- `bada-apps-codesign.pfx` — Windows の Authenticode 署名用 (同じ鍵と証明書、パスワード `bada-apps`)

| 端末 | 署名 | アップデートの条件 |
|:--|:--|:--|
| Android | `apksigner` (v2 + v3) で bada-apps 鍵 | 同じパッケージ ID + 同じ署名 + versionCode が大きい (100000 + ビルド番号) |
| Windows 10 / 11 | electron-builder が Authenticode 署名 (インストーラ・アプリ本体・ポータブル) | 同じ appId + バージョンが大きい (1.1.ビルド番号) |
| Linux | — (.deb はパッケージ名とバージョン) | 同じパッケージ名 + バージョンが大きい (`sudo apt install ./xxx.deb`) |

**注意**: この鍵はリポジトリで公開しているため、誰でも同じ署名のアプリを作れます (自分の端末で使う個人用の配布向け)。
他人に配る場合は、自分だけの鍵を作り、リポジトリの **Settings → Secrets and variables → Actions** に登録してください
(登録するとそちらが使われます。鍵を変えると、以前の鍵で署名した版には上書きできず一度アンインストールが必要です):

- `ANDROID_SIGNING_KEY_PK8` / `ANDROID_SIGNING_CERT` — `base64 -w0 key.pk8` / `base64 -w0 cert.der`
- `WIN_CSC_LINK` / `WIN_CSC_KEY_PASSWORD` — `base64 -w0 codesign.pfx` / そのパスワード

自己署名の証明書なので、Windows の SmartScreen には「発行元: Bada Apps」(未確認) と表示されます。
作り直す場合:
```sh
openssl req -x509 -newkey rsa:3072 -nodes -keyout key.pem -out cert.pem -days 10950 -sha256 \
  -subj "/CN=Bada Apps/O=masaaki-avnturle Bada/C=JP" -addext "keyUsage=critical,digitalSignature" \
  -addext "extendedKeyUsage=codeSigning" -addext "basicConstraints=critical,CA:FALSE"
openssl pkcs8 -topk8 -nocrypt -in key.pem -outform DER -out bada-apps-key.pk8
openssl x509 -in cert.pem -outform DER -out bada-apps-cert.der
openssl pkcs12 -export -inkey key.pem -in cert.pem -out bada-apps-codesign.pfx -passout pass:bada-apps \
  -name "Bada Apps" -certpbe PBE-SHA1-3DES -keypbe PBE-SHA1-3DES -macalg sha1
```

## 論文アプリ APK の鍵 (debug-*)


アプリ内で論文 PDF から作ったアプリを APK にするとき (src/exporters.js) の JAR 署名 (APK v1 署名) に使う
**デバッグ用の自己署名鍵**です。Android SDK の debug.keystore と同じく公開して構いません
(Play ストアへの公開用ではありません)。

- `debug-cert.der` — X.509 証明書 (CN=Bada Paper Apps (debug), RSA 2048, SHA-256)
- `debug-key.pk8`  — PKCS#8 秘密鍵 (暗号化なし)

作り直す場合:
```sh
openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem -days 10950 -sha256 -subj "/CN=Bada Paper Apps (debug)/O=masaaki-avnturle Bada/C=JP"
openssl pkcs8 -topk8 -nocrypt -in key.pem -outform DER -out debug-key.pk8
openssl x509 -in cert.pem -outform DER -out debug-cert.der
```
