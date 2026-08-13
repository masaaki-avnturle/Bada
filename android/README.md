# Bada IQ 判定器 — Android アプリ (APK)

これまでの Bada バイオ医療アプリ（**fMRI・MRI・脳トポグラフィ・DNA解析・血液検査**）の
生体信号から、対象者の IQ を計測して評価する Android アプリです。

**このアプリは Bada 言語で書かれたライブラリ（`bada_ruby/lib/bada_src/*.bada`）の上に
再構築されています。** 4 段階＋サーマルモードの数式はすべて Bada 言語で記述され
（`special.bada` / `iq.bada`）、アプリは Kotlin 実装の Bada VM（`BadaVM.kt`）でその
`.bada` ライブラリを**実行**します（APK に asset としてバンドル）。同じ `.bada` を Ruby CLI
（`bin/bada iq`）でも実行し、Kotlin VM と Ruby VM が同一の数値を出力することを検証済みです。

- **① IQ 計測** — 各生体信号を信頼度 ρ で IQ 尺度へ回帰
- **② ミラー統計** — 中央枢軸まわりの反射対称ロバスト要約
- **③ ベイズ推定** — 母集団事前 `N(100,15²)` とのガウス共役融合
- **④ ウィスパード判定器** — TupleSpace 不変量 `Ξ` でゲートした「囁き」判定
- **⑤ エキスパート分野判定** — 対象者の**個体識別能力**（神経速度＋機能統合＋視覚構造）と
  生体信号プロファイルから、どの分野のエキスパートか（放射線科医・法医/顔認証・生物分類学・
  数学・音楽・スポーツ・言語・美術 の 8 分野）を softmax で「囁き」判定

## 🌡️ 赤外線センサー + 温度計モード

メイン画面の「**赤外線センサー + 温度計モード ▶**」から、端末の**温度計**
（`TYPE_AMBIENT_TEMPERATURE`）と**赤外線近接センサー**（`TYPE_PROXIMITY`, IRベース）を
読み取り、赤外線体表温（IR ℃）と環境温度（℃）から IQ を推定します。

計算は**ガンマ関数の大域的部分積分多様体**を経由します。2 つのセンサー値が多様体上の
2 点測度を成し、そのシャノンエントロピー H と大域的部分積分 M = Σ p·(1/(x log x)²) を
ベータ・ゼータゲージ（β = Γ·Γ/Γ）で結合した**サーマル多様体不変量**

```
Ξ_T = β(H+1, M+1) / log 3
```

が、体表−環境勾配から得た標準化 z をゲージし、ウィスパード判定のゲートにもなります。
温度計センサーが無い端末では手動入力にフォールバックします（「センサーから取得」ボタン）。

**体外温度（皮膚温度）**: 赤外線カメラが実際に読むのは**体表＝皮膚(体外)温度**です。
推定モードはこの**皮膚温度**を駆動量として用います（`skin_excess`: 皮膚の基準 33℃ からの
超過を環境温で補正。neutral 皮膚33℃・環境23℃・Δ10 → 0）。皮膚温度の 3 点測度
（環境／皮膚／皮下）をガンマ関数の大域的部分積分多様体に通した熱エントロピー `H_bg` で
ゲージし、血液/DNA/fMRI/MRI/脳トポを推定します。

### タブレット計測モード（大脳基底核 熱エントロピー → 全モダリティ推定）

「**大脳基底核から 血液/DNA/fMRI/MRI/脳トポ を推定して評価**」ボタンでは、IR＋温度計から
深部脳（大脳基底核）の温度をモデル化し、その**熱エントロピー値**を 3 点測度
（環境・皮質IR・深部）でガンマ関数の大域的部分積分多様体に通して算出します
（`H_bg = β(H+1,M+1)/log 4`）。この `H_bg` から 5 つの生体信号（**血液・DNA・fMRI・MRI・
脳トポグラフィ**）の z スコアを推定し、通常の 4 段階（IQ推定・ミラー統計・ベイズ推定・
ウィスパード判定）を実行します。数式は Bada 言語（`iq.bada` の
`bg_thermal_entropy` / `derived_z`）にあります。

> 推定された生体信号は熱由来の教育的プロキシであり、実際の血液検査・DNA解析・
> fMRI/MRI 撮像ではありません。

### 赤外線カメラ + 温度計（タブレット機材で実測）

「**赤外線カメラで測定 ▶**」から、タブレットのカメラ映像の中心枠（対象者の額）を解析して
**赤外線体表温を近似**し（CameraX + `ImageAnalysis`、中心 ROI の赤成分を [30,37]℃ に写像）、
端末の温度計センサー（`TYPE_AMBIENT_TEMPERATURE`）で環境温を取得します。「この値で固定」
→「サーマル評価」または「大脳基底核推定」で、その 2 値を Bada 言語エンジンに渡して評価します。
初回はカメラ権限を要求します。

> 消費者向けタブレットの多くは放射計測型サーマルカメラを備えないため、通常カメラの赤成分から
> 体表温を近似する教育的プロキシです。放射計測 IR ではありません。

> ⚠️ 教育的モデルであり、医療機器・診断ではありません (not a medical diagnosis)。
> 生理学的には脳代謝スループットの教育的プロキシで、体温・IQ の臨床測定ではありません。

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
| `bada_ruby/lib/bada_src/special.bada` | Bada 言語の特殊関数（β/ζ ゲージ・多様体要素・Φ） |
| `bada_ruby/lib/bada_src/iq.bada` | Bada 言語の IQ エンジン（4 段階＋サーマル数式） |
| `app/src/main/java/com/masaaki/bada/iq/BadaVM.kt` | Bada 言語 VM（字句・構文・評価）。`.bada` を実行 |
| `app/src/main/java/com/masaaki/bada/iq/IqEngine.kt` | 入出力の橋渡し（数式は VM 経由で `.bada` を呼ぶ） |
| `app/src/main/java/com/masaaki/bada/iq/MainActivity.kt` | 生体信号 z スコア入力 UI と評価の実行 |
| `app/src/main/java/com/masaaki/bada/iq/ThermalActivity.kt` | 赤外線 + 温度計センサー読み取りと評価 |
| `app/src/main/res/layout/activity_main.xml` | 5 モダリティの z スコア入力フォーム |
| `app/src/main/res/layout/activity_thermal.xml` | 赤外線 IR / 環境温度 入力とセンサー取得 |
| `.github/workflows/android-apk.yml` | APK を CI でビルドし Releases へ公開 |

- `applicationId`: `com.masaaki.bada.iq` / `minSdk 26` / `targetSdk 34`
