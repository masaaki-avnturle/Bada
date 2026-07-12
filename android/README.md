<<<<<<< HEAD
# Bada Hologram — Android app (APK)

Packages the hologram apps into a downloadable **Android APK**. The apps are
self-contained HTML/canvas (the Bada-computed frames are embedded as JSON), so
they run **offline in a WebView** — no server, no network permission.

Bundled apps (launcher menu = `assets/holograms/index.html`):
- **Freeform マルチウィンドウ** — a Samsung-Freeform-style multi-window desktop
  hosting the other apps in draggable/resizable windows (close/min/max,
  split-snap) with a Play-Store-style taskbar (Start button + tasks + clock).
  The **Start menu lists the device's installed apps** (via a native
  PackageManager bridge) and launches them on tap, and a **size selector
  (携帯型 / 中 / 大)** chooses the opened window's size.
- **Quantum Crypto · Jones** — a cipher f(s) solved by f(s)/π(χ,x)−f(s) where
  π is the Jones polynomial; decryptable only under the necessary condition
  (matching key), the plaintext pulled from Omega::DATABASE, with the unlock
  bound to the person who pulls (identity-bound key)
- **Self-Evolving Quantum Algorithm** — a genetic algorithm evolves a quantum
  algorithm toward Grover amplification and writes it back out as Bada source
  code, self-validated by re-running the emitted source
- **Quantum Cache Disk** — the hard disk reinterpreted as a quantum cache:
  bit patterns → qubit amplitudes, a Reviser rewriting von-Neumann ops to
  quantum gates, a Grover telomere-thought prediction engine, the Jones thermal
  network, the Gamma integration-by-parts manifold and the uncertainty bound
- **Transparent + Japanese HHKB** — the display and Happy Hacking keyboard as
  glass over a **camera passthrough** (see the world behind the tablet, no
  video), with romaji→kana Japanese input
- **Spatial Hologram** — Vision-Pro-equivalent passthrough (apps float out of the
  transparent tablet)
- **Hologram Display** — reflection pyramid / free view
- **Float-up Hologram** — video floats up out of the conductive-plastic tablet
  (Jones-polynomial relief + power model)
- **Holographic HHKB** — the Happy Hacking Keyboard floating as a hologram
- **Mirror App** — smartphone mirror over the tablet, aerial display / aerial HHKB
  at the eyeglass-lens focus

## Download the APK
Every push to the app (or a manual run of the **Build Bada Hologram APK**
workflow) builds the APK and publishes it:
- as a **Release** asset — `bada-hologram.apk` under the `hologram-apk` release
  (a stable download link), and
- as a **workflow artifact** (`bada-hologram-apk`) on the Actions run.

Install it on Android (enable *Install unknown apps* for your browser/files app).
The transparent app asks for the **camera** so the world shows through the glass;
deny it and it falls back to a soft gradient.

## Build it yourself
```
# 1) render the bundled assets from the Bada apps
python3 android/generate_assets.py

# 2) build the APK  (needs JDK 17 + Android SDK; Gradle 8.7)
cd android
gradle assembleDebug          # or open the folder in Android Studio and Run
# -> app/build/outputs/apk/debug/app-debug.apk
```

## Layout
```
android/
  generate_assets.py            renders the hologram HTML into assets/ (from Bada)
  settings.gradle, build.gradle, gradle.properties
  app/
    build.gradle                dependency-free (plain Activity + WebView)
    src/main/AndroidManifest.xml
    src/main/java/com/bada/hologram/MainActivity.java
    src/main/assets/holograms/  the bundled, self-contained app HTML + index menu
    src/main/res/               launcher icon (vector) + strings
```
The CI workflow lives at `.github/workflows/android-apk.yml`.
=======
# Bada CodeFix — Android アプリ（APK）

**複素回転体の特殊相対性理論・可積分系のコマ（独楽）幾何**をエンジンにした、
ソースコードのエラー修正 Android アプリです。**複数投稿（複数ソース同時投稿）**に対応。

`bada_ruby/lib/bada/code_fix.rb`（Ruby 実装・テスト済み）を Kotlin に忠実移植した
`CodeFixEngine` を UI から呼び出します。

## 何をするか

各ソースを 1 つの *回転体* とみなし、括弧 `() [] {}`・引用符・Ruby の `def…end`
を回転軌道上の角度マーカーとして扱います。構文が正しい = **軌道が閉じる**
（可積分系の閉軌道条件 `∮ e^{-□} d□ = π e`）。構文エラーはコマが軌道から落ちること。
修正は保存量（括弧バランス）を戻して軌道を再び閉じることです。修正の信頼度は、
多様体エントロピー不変量 `Ξ` の保存度から読み取ります（`Manifold.kt`）。

対応言語：Ruby / Python / JavaScript(TS) / C 系ブレース言語。
検出・修正：括弧の不均衡・未終端文字列・Ruby の `end` 過不足。

## ファイルのアップロード（複数可・PDF対応）

**「ファイルをアップロード」**ボタンから、ソースコードや PDF を**まとめて複数選択**して
取り込めます（Android の Storage Access Framework を使用。ストレージ権限は不要）。

- **ソースファイル**（.rb / .py / .js / .c … 拡張子問わず）→ UTF-8 テキストとして読み込み。
- **PDF**（.pdf）→ PdfBox-Android の `PDFTextStripper` で本文テキストを抽出。
  投稿された PDF（例: badasource1.pdf）のソースコードをそのまま修正対象にできます。

取り込んだファイルは 1 件ずつ投稿カードになります。ファイル名から言語を自動判定し、
**「すべて修正」**でまとめて修正します（複数投稿）。読み込みはバックグラウンドで実行。

## レポート生成AI — OmegaAgi（未知エンジン / AGI 分派）

メイン画面の **「🧠 レポート生成AI（OmegaAgi）を開く」** から、レポート駆動の
生成AIを利用できます（`OmegaAgi`）。クラウド LLM は使わず、端末内で完結します。

**仕組み** — アップロードしたレポート（ソースコード・PDF）を*計測済みコーパス*として
取り込み、質問を **ガンマ関数の大域的部分積分多様体**の不変量 Ξ を通じて相関させて
生成します（`bada_ruby/lib/bada/{knowledge,qa_engine,generator}.rb` の Kotlin 移植）。

- 各文の計測：`H = -Σ p·log₂ p`、`M = ∬ 1/(x·log x)² dμ`、
  `Ξ = β(H+1, M+1)/log(N+1) = Γ(H+1)Γ(M+1)/Γ(H+M+2) / log(N+1)`。
- **独自に相関する関数**：質問 q と文 d を、両者のエントロピーのオイラーベータ
  （ガンマ関数の比）で相関させ、多様体不変量の距離で減衰させる：

  `corr(q,d) = β(H_q+1, H_d+1) · 1/(1+|Ξ_q − Ξ_d|)` （＋キーワード重なり）

- 検索した根拠（相関スコア・カーネル β・ΔΞ）と、エントロピー整合した bigram
  マルコフ生成（`Generator`）による応答を表示します。

使い方：「レポートを取り込む」で複数ファイル/PDF を取り込む（または「デモレポート」）→
質問を入力 →「相関して生成」。`H=3.0` のようにエントロピー目標を指定することもできます。

## APK のダウンロード方法

GitHub Actions の **Build Android APK** ワークフローがビルドして公開します。

1. **ビルド成果物（Artifacts）から** — リポジトリの **Actions** タブ →
   最新の *Build Android APK* 実行 → 下部の **Artifacts** の `bada-codefix-apk`
   をダウンロード（`bada-codefix-debug.apk`）。
2. **リリースから** — `v*` タグ（例 `v0.1.0`）を push すると、APK が
   **Releases** の Assets に自動添付されます。

```bash
# 例：リリース経由で APK を配布する
git tag v0.1.0
git push origin v0.1.0
```

インストール：APK を Android 端末に転送し、「提供元不明のアプリ」を許可して開く
（デバッグ署名。Play ストア配布には別途リリース署名が必要）。

## ローカルビルド

Android SDK と JDK 17 が必要です。

```bash
cd android
./gradlew assembleDebug            # -> app/build/outputs/apk/debug/app-debug.apk
./gradlew testDebugUnitTest        # ユニットテスト（CodeFixEngineTest）
```

## 構成

| ファイル | 内容 |
|:--|:--|
| `app/src/main/java/io/bada/codefix/Manifold.kt` | Special/Entropy/Manifold の移植（Ξ 不変量） |
| `app/src/main/java/io/bada/codefix/CodeFixEngine.kt` | スキャナ・修正器・Repository（複数投稿） |
| `app/src/main/java/io/bada/codefix/MainActivity.kt` | UI（投稿追加・すべて修正・デモ・コピー） |
| `app/src/test/java/io/bada/codefix/CodeFixEngineTest.kt` | ユニットテスト |
| `.github/workflows/android-apk.yml` | APK ビルド & 公開 CI |

- 技術：Kotlin 1.9.24 / AGP 8.5.2 / Gradle 8.9 / compileSdk 34 / minSdk 24。
- 依存は最小（appcompat・material・core-ktx）。エンジンは純 Kotlin（外部依存なし）。

## 既知の制限

括弧が本当に複数行にまたがる `(`/`[` の閉じ位置推定と、Ruby `end` 不足の挿入位置は
本質的に曖昧なためヒューリスティックです（信頼度 `Ξ` 保存度として自己申告）。
`;` の欠落など、区切り・引用符・`end` のバランス以外のエラーは対象外です。
>>>>>>> 3de4c4eeff220b1147c5213330aeb74407352774
