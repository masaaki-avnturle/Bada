# 論文アプリ APK の署名鍵 (デバッグ用)

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
