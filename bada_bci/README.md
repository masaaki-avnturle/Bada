# BadaBCI — ブレインインターフェース スイッチ

脳に装着するブレインインターフェース（BCI）の **オン/オフ スイッチ** を中心にした
Android アプリ。リポジトリの Bada / Yamaguchi 理論（レポートの原理）に基づく
**概念実装・シミュレーション**です。

> ## ⚠️ 重要 — これは医療・神経デバイスの制御アプリではありません
>
> - 本アプリは **シミュレーション** です。実際に脳に装着・埋め込まれた
>   デバイスの電源を **切り替えることはできません／しません**。
> - 表示される脳波は **模擬信号**（描画デモ）で、センサーの実測値では
>   ありません。
> - いかなるソフトウェアも、純正ハードウェア・ファームウェアと医療的管理
>   なしに本物の神経デバイスを操作してはいけません。実機の EEG ヘッドセット
>   （Muse / OpenBCI / Emotiv 等）に繋ぐ場合は、`MainActivity.kt` の
>   `connect()` / `disconnect()` の“シーム”にその機器の **純正SDK** を差し込む
>   設計にしていますが、実機なしには動作しません。

## 機能

- 大きな **ON/OFF スイッチ**：OFF →（接続中）→ ON（セッション作動）→ OFF の
  状態遷移。
- ON の間だけ **模擬脳波**がアニメーション表示（`SignalView`）。
- **セッション記録**：ON/OFF の時刻をログに記録し、「記録を保存」で端末内
  （アプリ専用領域 `bci_logs/`）にテキスト保存。「記録を消去」でクリア。
- バックグラウンドに移ると自動的に OFF（セッションを放置しない）。

- 表示名: **BadaBCI スイッチ** / パッケージ: `com.yamaguchi.bci`

## APK のダウンロード（このリポジトリから）

GitHub Actions がビルドして公開します。

- **Actions** タブ →「Build BadaBCI APK」の最新実行 → **Artifacts** →
  `BadaBCI-apk` をダウンロード（zip内に `.apk`）。
- `v` で始まるタグを push すると **Releases** に `BadaBCI-debug.apk` を添付。

## ローカルビルド（Android SDK がある環境）

```sh
cd bada_bci
./gradlew assembleDebug
# 出力: app/build/outputs/apk/debug/app-debug.apk
```

構成: AGP 8.5.2 / Gradle 8.7 / Kotlin 1.9.24 / compileSdk 34 / minSdk 26。
