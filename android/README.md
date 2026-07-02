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
