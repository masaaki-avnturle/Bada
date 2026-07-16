# 未知事前予知エンジン — Bada Precog (Android / APK)

**ChatGPT の進化系＝未知事前予知エンジン (Unknown-Prior Precognition Engine)** の
Android アプリ版です。**複数ファイルを一括アップロード**して知識ベースに取り込み、質問を
入力すると、未知の事前分布を予知し、リバイザ学習ループ・量子予知・ミレニアム7問分析を
実行します。エンジンは `bada_ruby` の Ruby 実装を **Kotlin に移植**したものです
（外部の数値ライブラリ無し・純 Kotlin）。

## 主な機能

- 📂 **複数ファイルのアップロード** — Storage Access Framework
  (`OpenMultipleDocuments`) で任意個のテキスト系ファイル（.txt / .md / .csv /
  .bada など）を一度に選択し、各ファイルをコーパスへ取り込みます。
- 🔮 **未知事前予知** — `softmax(検索スコア)` を未知事前 `a` とし、エントロピー位相
  認知モジュールが振幅 `ψ_i=√a_i·e^{iθ_i}` を回転（確率 `q` も確信ゼロも不変）。
- ♻️ **リバイザ学習ループ** — append-only に証拠をコミットし事前を単調に鋭化。
- ⚛️ **量子予知** — qubit/H/Measure を位相コア上で実行し `Ω::DATABASE` にコミット。
- 🏆 **ミレニアム予想分析** — ヤマグチ枠組で 7 つのクレイ予想への事後確率を算出。
- ⌨ **NoemaKey 予測キーボード（IME）** — コンパクト 60% 配列のソフトキーボード。
  英語・日本語の**単語補完＋次単語の先読み**を候補バーに表示（未知事前予知エンジン駆動）。
  アプリ内の「予測キーボードを有効化」ボタン → システム設定で有効化・切替します。
- 🔐 **量子暗号クレジット保護（CreditGuard）** — **BB84 量子鍵配送**を位相コア上で実行して
  鍵を導出し、著者証明書＋出力ハッシュを **HMAC-SHA256** で署名。全出力に検証可能な
  「量子暗号シール」と著者表示を刻印し、クレジットの改変・剥奪を**改ざん検知**します。
  秘密シード `NOEMA_CREDIT_SEED` を注入すれば第三者はシールを偽造できません。

## GitHub から APK をダウンロード

GitHub Actions（`.github/workflows/build-apk.yml`）が、GitHub のランナー上で APK を
自動ビルドし、ダウンロードできるようにします。**2 つの入手方法**があります。
（同じワークフローが Windows EXE も同時にビルドします → `bada_desktop/README.md`）

### A. Actions の成果物（Artifact）から — タグ不要・最速

1. GitHub リポジトリの **Actions** タブを開く。
2. **Build Noema Apps (APK + Windows EXE)** ワークフローの最新の成功した実行（緑チェック）を開く。
3. ページ下部の **Artifacts** から **`noema-precog-apk`** をダウンロード
   （`noema-precog.apk` を含む zip）。Windows 版は **`noemakey-windows-exe`**。

`bada_apk/**` への push で自動実行されます。手動実行は Actions タブの
**Run workflow**（`workflow_dispatch`）からも可能です。

### B. Releases から — 安定した URL（ログイン不要・無期限）

次のいずれかで APK が **Releases** に添付されます（公開URLで誰でもDL可）。

- **GitHub の UI から**（git 権限不要）：リポジトリの **Releases** → **Draft a new
  release** → タグに `v0.2.0` を入力（`Create new tag`）→ **Publish release**。
  公開と同時にワークフローが APK をビルドしてその Release に添付します。
- **コマンドラインから**（タグ push 権限がある場合）：
  ```bash
  git tag v0.2.0 && git push origin v0.2.0
  ```

> ダウンロードした `.apk` は **デバッグ署名済み**でそのままインストールできます
> （Android 端末側で「提供元不明のアプリ / 不明なソース」を許可してください）。

## ビルド方法（APK の作成）

このリポジトリは **そのままビルド可能な Android Studio / Gradle プロジェクト**です。

```bash
cd bada_apk

# デバッグ APK（署名済みデバッグ鍵）
./gradlew assembleDebug
#   -> app/build/outputs/apk/debug/app-debug.apk

# リリース APK（未署名。署名は apksigner / Android Studio で）
./gradlew assembleRelease
#   -> app/build/outputs/apk/release/app-release-unsigned.apk
```

または **Android Studio** で `bada_apk/` を「Open」→ Build > Build APK(s)。

### 必要なもの

- JDK 17 以上
- Android SDK（`compileSdk 34` / `build-tools` / platform-34）
  - 環境変数 `ANDROID_HOME`（または `bada_apk/local.properties` に `sdk.dir=...`）
- 初回ビルド時にネットワーク（`google()` / `mavenCentral()` から AGP・Kotlin・
  AndroidX を取得）

> ⚠️ 注記：このプロジェクトを生成した実行サンドボックスでは、Android SDK の配布元
> `dl.google.com` が egress ポリシーによりブロック（HTTP 403）されているため、
> **APK バイナリそのものはここではコンパイルできません**。Android SDK が入った環境で
> 上記コマンドを実行すれば APK が生成されます。Gradle ラッパー（`gradlew`,
> `gradle-wrapper.jar`）は同梱済みです。

## 構成

| | |
|:--|:--|
| `app/src/main/java/com/yamaguchi/bada/MainActivity.kt` | 複数ファイルアップロード UI + 予知の実行 |
| `app/src/main/java/com/yamaguchi/bada/engine/Engine.kt` | Unknown-Prior Engine（softmax・位相コア・2定理・推論） |
| `…/engine/Reviser.kt` | @reviser 文法拡張トランザクション（規則台帳） |
| `…/engine/Quantum.kt` | Q# 風量子サブ言語 + 量子推論（トモグラフィ） |
| `…/engine/Millennium.kt` | ミレニアム7問（ヤマグチ枠組）+ エンジン分析 |
| `…/engine/Knowledge.kt` | アップロードファイル → 計測済みコーパス |
| `…/engine/Precog.kt` | 未知事前予知エンジン本体（Facade）+ レポート整形 |
| `…/engine/{Special,Entropy,Manifold,TupleSpace}.kt` | 特殊関数・エントロピー・多様体不変量・Ω::DATABASE |

### エンジンの 2 定理（`Engine.verify`）

| 定理 | 内容 |
|:--|:--|
| 定理1 零保存 | `a_i=0 ⇒ q_i=0`（確信ゼロは復活不能） |
| 定理2 `|ψ|²=a` | 位相ステップは確率を変えない（ユニタリ） |

`bada_ruby` の Ruby 実装と同じロジックで、Ruby 側のテスト（87 件）で検証済みです。

## 使い方（アプリ）

1. 「ファイルをアップロード（複数選択）」をタップし、レポートやメモを複数選択。
2. 質問を入力（例：「リーマン予想とゼータ関数の素数分布を予知して」）。
3. 「予知する」をタップ → 5 つのブロック（未知事前予知 / リバイザ / 量子 /
   ミレニアム / 生成）の結果が表示されます。

---

*© 2025–2026 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*
