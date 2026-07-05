# YamaguchiHealth (Android) — SRS速読 / 瞬読

速読トレーニング用の Android アプリ（Kotlin）。レポート本文を貼り付けて、
2つのモードで高速表示します。読書トレーニング用で、医療機器ではありません。

| モード | 動作 |
|:--|:--|
| **SRS速読 (ブロック)** | 本文を **1ページ毎・ブロック毎** に中央表示 → 消去 → 次へ。ページが進むと加速 |
| **瞬読 (ランダム)** | 本文を小さな **単語(ぶ)単位** に分割し、画面の **ランダムな位置** に一瞬ずつ表示。ページが進むと加速 |

操作: 本文を貼り付け → モード選択 → 開始CPM / 加速 / 単位文字数 を設定 → **開始 / 停止**。

---

## APK のダウンロード（このリポジトリから）

APK は **GitHub Actions** がビルドして、このリポジトリから入手できます。
（`dl.google.com` がこの開発環境ではブロックされているため、ローカルでは
ビルドできません。CI 上でビルドします。）

**方法A — Actions のアーティファクト（毎ビルド）**
1. GitHub の **Actions** タブ → 「Build YamaguchiHealth APK」ワークフローの最新実行
2. 下部の **Artifacts** → `YamaguchiHealth-apk` をダウンロード（zip内に `.apk`）

**方法B — Release（タグを付けたとき）**
1. `v` で始まるタグを push（例）:
   ```sh
   git tag v1.0 && git push origin v1.0
   ```
2. GitHub の **Releases** ページから `YamaguchiHealth-debug.apk` をダウンロード

**インストール**: 端末の「提供元不明のアプリ / 不明なアプリのインストール」を
許可してから APK を開きます。これは署名済みの **debug APK** です。

---

## ローカルでビルドする場合（Android SDK がある環境）

```sh
cd yamaguchi_health/android
./gradlew assembleDebug
# 出力: app/build/outputs/apk/debug/app-debug.apk
```

構成: AGP 8.5.2 / Gradle 8.7 / Kotlin 1.9.24 / compileSdk 34 / minSdk 26。

> 注意 / Disclaimer: 本アプリは読書トレーニング用のツールであり、診断・治療・
> 医療行為を行うものではありません。
