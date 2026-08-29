# 🔐 Bada QuantumCrypto — Jones 多項式量子暗号 暗号化/解除アプリ

テキストとファイルを**暗号化**し、同じパスフレーズ + 結び目で**解除(復号)**できる
スタンドアロン アプリです。Android APK / Windows 10・11 EXE / Ubuntu AppImage・deb
として配布します。すべて端末内で完結し、**通信は一切行いません**。

## 📦 ダウンロード

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `quantumcrypto-debug.apk` — 「提供元不明のアプリ」を許可してインストール |
| **Windows 10 / 11** | `BadaQuantumCrypto-Setup-*-x64.exe` (インストーラ) / `BadaQuantumCrypto-Portable-*-x64.exe` (インストール不要) |
| **Ubuntu** | `BadaQuantumCrypto-*-x86_64.AppImage` (`chmod +x` して実行) / `BadaQuantumCrypto-*-amd64.deb` (`sudo apt install ./…`) |
| **どこでも** (単一 HTML) | [`www/index.html`](www/index.html) + [`www/qcrypto.js`](www/qcrypto.js) をダウンロードして同じフォルダに置き、ブラウザで開くだけ |

ビルドは [`quantumcrypto-app-build.yml`](../../.github/workflows/quantumcrypto-app-build.yml)
が自動実行します (`quantumcrypto-v*` タグを push すると Release に添付、
または Actions の workflow_dispatch で `release_tag` を指定)。

## 🔑 使い方

1. **暗号化** — テキスト タブに文章を入力(またはファイル タブでファイルを選択)し、
   パスフレーズと結び目(三葉 / 8の字 / 五葉)を選んで「🔒 暗号化」。
   結果は `-----BEGIN BADA QUANTUM CIPHER-----` ブロック(テキスト)または
   `.badaqc` ファイルとして保存できます。
2. **解除** — 受け取った暗号文ブロックを貼り付け(または `.badaqc` を選択)、
   同じパスフレーズを入れて「🔓 解除」。結び目はコンテナに記録されるので
   選び直す必要はありません。
3. パスフレーズは**別の経路**(口頭など)で相手と共有してください。
   誤ったパスフレーズや改ざんされたデータは AEAD タグ検証で
   `409 zone-guard-reject` として拒否されます。

## ⚙️ 仕組み

zone:// ウルトラネットワーク ([`browser/zone-lib.bada`](../browser/zone-lib.bada)) の
Jones 多項式量子暗号を単独アプリ用に移植したものです:

- **Jones 鍵** — 結び目図の Kauffman ブラケット ⟨L⟩ を A = 0.8, 1.0, 1.2, 1.5, 2.0 で
  標本化 (`kauffman()` / `jones_key()` の忠実な JS 移植) し、鍵導出ソルトに混合
- **QKD セッション** — Bell 対 (|00⟩+|11⟩)/√2 の測定シミュレーションで
  セッション相関ビットを採取しノンスに折り込み
- **鍵伸長** — PBKDF2-HMAC-SHA256 (24,000 反復) でパスフレーズ + Jones 鍵 + ソルトから
  暗号鍵 32B + MAC 鍵 32B を導出
- **本体暗号** — ChaCha20 ストリーム暗号 + HMAC-SHA256 タグ (encrypt-then-MAC AEAD)。
  復号はタグ検証に合格した場合のみ実行されます

> ⚠️ 本アプリは Bada プロジェクトの研究/デモ用実装です。実運用の機密データには
> 監査済みの暗号製品を使用してください。

## 🧪 自己検査

```
node bada_gui_ide/quantumcrypto-app/test/roundtrip.js
```

SHA-256 / HMAC の既知ベクタ、CJK テキストとバイナリの round-trip、
誤パスフレーズ・改ざんの拒否、Jones 鍵の決定性を検査します。
