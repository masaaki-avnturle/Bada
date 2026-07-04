# Bada IQ 判定器 — Android アプリ (APK)

これまでの Bada バイオ医療アプリ（**fMRI・MRI・脳トポグラフィ・DNA解析・血液検査**）の
生体信号から、対象者の IQ を計測して評価する Android アプリです。ロジックは純 Ruby の
`Bada::IQ`（`bada_ruby/lib/bada/iq.rb`）を Kotlin へ**逐語移植**しており、`bin/bada iq` と
同じ数値を出力します。

- **① IQ 計測** — 各生体信号を信頼度 ρ で IQ 尺度へ回帰
- **② ミラー統計** — 中央枢軸まわりの反射対称ロバスト要約
- **③ ベイズ推定** — 母集団事前 `N(100,15²)` とのガウス共役融合
- **④ ウィスパード判定器** — TupleSpace 不変量 `Ξ` でゲートした「囁き」判定

> ⚠️ 教育的モデルであり、医療機器・診断ではありません (not a medical diagnosis)。

---

## 📥 APK をダウンロードする（ビルド不要）

GitHub Actions が APK を自動ビルドし、**Releases** に添付します。

1. リポジトリの **Releases** を開く → **Bada IQ APK (latest)**（タグ `apk-latest`）
2. `bada-iq.apk` をスマホでダウンロード
3. 「提供元不明のアプリ / 不明なアプリのインストール」を許可してインストール

または、任意の **Actions** 実行の成果物（Artifacts）`bada-iq-apk` からも取得できます。

バージョン付きリリースを作りたい場合はタグを push:

```bash
git tag v1.0 && git push origin v1.0   # v* タグで Release に APK が添付されます
```

---

## 🛠 ローカルでビルドする

Android SDK（cmdline-tools + platform 34 / build-tools 34）と JDK 17 が必要です。

```bash
cd android
./gradlew assembleDebug
# => app/build/outputs/apk/debug/app-debug.apk
```

## 構成

| ファイル | 内容 |
|:--------|:----|
| `app/src/main/java/com/masaaki/bada/iq/IqEngine.kt` | `Bada::IQ` の Kotlin 移植（4 段階の計算エンジン） |
| `app/src/main/java/com/masaaki/bada/iq/MainActivity.kt` | 入力 UI と評価の実行 |
| `app/src/main/res/layout/activity_main.xml` | 5 モダリティの z スコア入力フォーム |
| `.github/workflows/android-apk.yml` | APK を CI でビルドし Releases へ公開 |

- `applicationId`: `com.masaaki.bada.iq` / `minSdk 26` / `targetSdk 34`
