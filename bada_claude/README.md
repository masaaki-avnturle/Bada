# ⟨ψ⟩ BadaClaude — Claude / ChatGPT の対話パイプラインを量子 Bada で作り換えた対話エンジン

**Claude や ChatGPT が「質問を受けて答える」までの仕組み — 字句化・意図推定・検索・道具使用・生成・記録 — を、量子プログラミング言語 Bada で全部書き直した対話アプリです。** 知識は同梱の論文 10 本と、`contact_blueprint.pdf` の方程式レジストリ **2111 本**です。

依存なし。単一 HTML で、オフラインで動きます (Claude API モードを除く)。

## 📥 ダウンロード

### GitHub Actions から (APK / Windows 10・11 / Linux)

1. リポジトリの **Actions** タブ → **BadaClaude app build (Android APK + Windows 10/11 EXE + Linux)** を開く
2. 最新の成功した実行 (緑のチェック) を開く
3. ページ下部の **Artifacts** からダウンロード

| アーティファクト | 中身 | 対象 |
|:---|:---|:---|
| `badaclaude-android` | `bada-claude-debug.apk` | Android 7.0 以上 |
| `badaclaude-windows` | `BadaClaude-*-x64.exe` (インストーラ) / `BadaClaude-*-portable.exe` | Windows 10 / 11 (x64) |
| `badaclaude-linux` | `BadaClaude-*-x86_64.AppImage` / `BadaClaude-*-amd64.deb` | Ubuntu などの Linux (x64) |

`bada_claude/` を変更して push すると自動でビルドされます。手動で実行するときは Actions 画面の **Run workflow** を押してください。`badaclaude-v*` タグ (例 `badaclaude-v1.0.0`) を push すると、同じファイルが GitHub Release にも添付されます。

- APK はデバッグ署名です。インストール時に「提供元不明のアプリ」を許可してください。
- Windows では SmartScreen が出ることがあります (「詳細情報」→「実行」)。コード署名はしていません。
- AppImage は `chmod +x BadaClaude-*.AppImage` の後に実行します。

### ブラウザで

[`index.html`](index.html) を開き **「Download raw file」(⬇)** で保存して、ダブルクリックで起動します (インストール不要)。

## 🧠 仕組み — 頭脳は Bada で書かれている

```
利用者の質問
  │
  ▼  brain.bada (Bada)
 ① 字句化          tokens()                         日本語は文字種の連なり + 漢字 2-gram
 ② 意図推定        Unknown-Prior Engine            a = softmax(z), ψ = √a·e^{iθ}, q = |ψ|² (= a)
 ③ 検索 (RAG)      BM25 転置索引                    論文チャンク 256 件 + 方程式 2111 本
 ④ 道具            数値核 / 量子回路 / Bada 実行     ζ Γ β W Z(t) Jones, qubit/H/CNOT/Measure
 ⑤ 生成            根拠つき応答 / 文字 5-gram LM     または Claude API へ文脈を渡す
 ⑥ 記録            Omega >> [...]                   append-only 台帳 Ω::DATABASE
```

| ファイル | 役割 |
|:---|:---|
| [`src/brain.bada`](src/brain.bada) | **対話パイプライン全体** (Bada)。意図・検索・道具・生成・Claude 用文脈の組み立て |
| [`src/engine.js`](src/engine.js) | Bada 処理系 (字句解析・構文解析・木構造インタプリタ) と数値核・量子レジスタ |
| [`src/app.js`](src/app.js) | ホスト: UI・履歴・Claude API への送信 (I/O だけ) |
| [`src/kb.json`](src/kb.json) | 知識ベース (`tools/build_kb.py` が `sources/*.pdf` から生成) |
| [`sources/`](sources/) | 元の PDF 10 本 |
| [`tools/build.js`](tools/build.js) | `src/` → `index.html` の組み立て |
| [`tools/engine-test.js`](tools/engine-test.js) | 単体テスト 75 件 |

アプリの **🧠 brain.bada** タブで、動いている頭脳のソースをそのまま読めます。**Ω 台帳** タブには、頭脳が行った commit (起動・各ターン・学習・Claude 応答) が追記されていきます。

## 💬 できること

| 送る文 | 動作 |
|:---|:---|
| `ゼータ関数とベータ関数の関係は?` | 論文と方程式を検索し、出典 (論文名・ページ・方程式 ID) つきで回答 |
| `もっと` | 同じ質問の続きの検索結果 |
| `ACAFE.17` | 方程式 ID で直接参照 (判定: 成立 / 不成立 / 数値評価 / 記号式) |
| `計算 zeta(2)` / `beta(1/2, 1/2)` / `rs_Z(14.134725)` | Bada で数値計算 |
| `ベル状態を作って` / `GHZ` / `reviser で文法を拡張して` | Q# 型量子副言語で回路を実行 |
| ` ```bada ... ``` ` | 送ったコードを Bada で実行 |
| `方程式は全部で何本?` | レジストリの統計 (判定別・タグ別・系列別) |
| `輸送機の設計図` | CONTACT TRANSPORTER の設計パラメータを Bada で再計算 |
| `リーマン予想は証明されたの?` | 論文集自身の標識 (**未解決**) に従って回答 |
| `ゼータ関数で文章を生成して` | 論文コーパスで学習した文字 5-gram モデルで生成 |

ほかに **Bada エディタ** (実行例 6 本、Ctrl+Enter で実行) と **方程式レジストリ** (全 2111 本の検索・判定/タグ絞り込み) があります。

## 🔑 Claude API モード (任意)

⚙ 設定で **Claude API** を選び、Anthropic の API キーを入れると、Bada の頭脳が検索・計算した結果 (`<bada_context>`) をシステムプロンプトに入れて Claude に送り、ストリーミングで回答を表示します。

- モデル: `claude-opus-5-5` (既定) / `claude-sonnet-5-5` / `claude-haiku-4-5`
- effort: low / medium / high (Haiku 4.5 では送りません)
- Opus 5.5 と Sonnet 5.5 では `fallbacks: "default"` (ベータ `server-side-fallback-2026-07-01`) を付けています。安全分類器が応答を拒否した場合、API 側で代替モデルに切り替えて答えを返します。拒否 (`stop_reason: "refusal"`) はその旨を表示します。
- キーは端末のアプリ内保存領域 (localStorage) にだけ保存され、送信先は `https://api.anthropic.com` だけです。ブラウザから直接呼ぶため `anthropic-dangerous-direct-browser-access` ヘッダを使っています。共有端末ではキーを保存しないでください。

## ⚖ 正直な範囲

- **Anthropic の Claude や OpenAI の ChatGPT の学習済みの重みは含まれていません。** 作り換えたのは「応答する仕組み」です。ローカルモードの知識は同梱の論文と方程式、それに Bada の数値核だけで、汎用の会話はできません。汎用の会話が必要なときは Claude API モードを使ってください。
- 生成 (`文章を生成`) は文字 5-gram の統計モデルです。文のつながりを真似るだけで、内容の正しさは保証しません。
- 方程式の判定 (成立 / 不成立) は `contact_blueprint.pdf` に記録された数値検証の結果をそのまま表示しています。論文集自身が「未解決」「予想」「否定」と標識した主張 (リーマン予想・P ≠ NP など) を、BadaClaude が解決済みとして扱うことはありません。
- 輸送機の設計図と UFO-OS は、論文の方程式に基づく思索的な可視化です (原本の注記どおり)。

## 🔧 開発

```sh
python3 bada_claude/tools/build_kb.py     # PDF → src/kb.json (pip install pypdf cffi)
node bada_claude/tools/build.js           # src/ → index.html
node bada_claude/tools/engine-test.js     # 75 件のテスト
```

`index.html` は生成物です。`src/` を編集したら `build.js` を実行してからコミットしてください (CI が `build.js --check` で一致を確認します)。

### Bada 言語 (この処理系が受け付ける方言)

```bada
x := 1                         # 束縛          x = x + 1  # 代入
fn f(n) { return n * 2 }       # 関数          g := |x| x * x   # ラムダ
Omega >> ["fact", x]           # 台帳へ commit (append-only)
xs <- 4                        # 配列へ追加    Omega::DATABASE  # スコープ
STAR ~ x                       # 漸進型の整合 (常に true)
[1, 2, 3] => |v| v + 1         # 写像照会
struct V { x, y }              # struct と  fn V.norm(self) { ... }
@reviser GRAMMAR {             # 文法拡張: 規則を台帳に commit すると
  rule bell(r) { H(r, 0); CNOT(r, 0, 1) }
}
qubit q[2]                     # 以降 `bell q` が新しい文として解析される
bell q
Measure(q, 0)                  # 測定は台帳への commit
```

組込み: `softmax entropy unknown_prior update dist phase cognitive_system zeros_of maxdiff manifold_embed` / `gamma lgamma digamma beta zeta rs_theta rs_Z lambertw xlogx_root jones integrate deriv solve` / `H X Y Z S T RX RY RZ CNOT CZ SWAP Measure probs amps qstate` ほか。
