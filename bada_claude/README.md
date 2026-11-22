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
| [`src/lab.bada`](src/lab.bada) | **証明ラボ** (Bada)。`@reviser RIGOR` の規則・義務と、証明 / 論文 / コード生成 / 暗号の道具 |
| [`src/lab.js`](src/lab.js) | 証明ラボのネイティブ組込み: 仕様の作成、8 言語の発行器、論文、Jones 暗号 |
| [`src/semantic.bada`](src/semantic.bada) / [`tools/semantic-test.js`](tools/semantic-test.js) | **意味認識システム** (Bada) とそのテスト 25 件 |
| [`tools/lab-test.js`](tools/lab-test.js) / [`tools/codegen-test.js`](tools/codegen-test.js) | 証明ラボのテスト 48 件 / 生成コードの実コンパイル・実行 59 件 |

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

## 🔬 証明ラボ (v1.1.0)

未知事前エンジン・擬似量子コンピュータ・量子暗号を「道具」として頭脳に追加し、証明の論文と、リバイザによる厳密化されたソースコードを生成できるようにしました。

| 送る文 | 動作 |
|:---|:---|
| `リーマン予想を高さ 1000 まで調べて` / `深リーマン予想の証拠を見せて` | ζ 零点の数値検証 (偏角の原理 と 臨界線上の符号変化)、Schoenfeld 不等式、オイラー積の証拠 |
| `コラッツ予想を 14 ビットで` / `未解決問題の反例を探して` | 降下補題の証明、擬似量子コンピュータ (Grover 探索) による反例探索 |
| `Σ k^2 = n(n+1)(2n+1)/6` | 数学的帰納法で判定。誤りなら反例を示し、正しい式に修正して証明 |
| `論文を作成して` | 直前に扱った主張の論文を Markdown と LaTeX (`paper.tex`) で作成し、Jones 暗号で封印 |
| `厳密なソースコードを生成して` / `rust と c で` | 証明済みの公式から 8 言語のソースコードを生成 (下記) |
| `[1,1,1] で暗号化: 本文` / `復号 [1,1,1] <暗号文>` | 組みひもの Jones 多項式を鍵にした認証つき暗号 |

### リバイザによる厳密化されたソースコードの生成

[`src/lab.bada`](src/lab.bada) の `@reviser RIGOR` が、「各言語をどう厳密化するか」を新しい文として宣言します。

```bada
@reviser RIGOR {
  rule target(lang, label, ints, overflow) { … }   # 対象言語と桁あふれの扱い
  rule strict(lang, note) { … }                    # 言語ごとの厳密化規則
  rule selftest(lang, n) { … }                     # 自己検査の範囲
  rule obligation(id, title, check) { … }          # 生成の前提となる義務
}
target "rust", "Rust", "i128 + checked_mul / checked_add", "checked128"
strict "c", "符号付き桁あふれ (未定義動作) に入る前に検出して 0 を返す"
obligation "RS01", "主張が数学的帰納法で証明済みである", |s| s.status == "proved"
```

| 言語 | 整数の扱い | 厳密化 |
|:--|:--|:--|
| Python / Ruby | 任意精度整数 | 入力検査、余り 0 を確かめる割り算 |
| JavaScript | BigInt | Number を受け付けない |
| Java / Go | BigInteger / math/big | 例外・error で失敗を通知 |
| Rust | i128 | `checked_mul` / `checked_add`、桁あふれは `Err(Overflow)` |
| C | int64_t | `__builtin_*_overflow` で未定義動作の前に検出 |
| Bada | 倍精度 | 中間値が 2^53 未満に収まる n の範囲を計算し、範囲外は `nil` |

生成の前に義務を検査します (RS01 証明済み / RS02 f の係数が整数 / RS03 生成した Bada 版を実行して照合)。満たさなければ生成しません。各ファイルは実行すると、閉形式と定義どおりの和を照合する自己検査を行います。`tools/codegen-test.js` は、生成したコードを 8 言語すべてで実際にコンパイル・実行して確かめます (C は `-Wall -Wextra -Werror`、Rust は `-D warnings`)。

**範囲**: 生成できるのは「多項式の和の公式 Σ f(k) = g(n)」で、f の係数が整数のものです。任意のプログラムを厳密化する機能ではありません。

### 論文

- 帰納法で証明できた公式 → **定理と証明**の論文 (基底、帰納の段の展開、機械検査の説明、付録に生成コード)。
- リーマン予想・深リーマン予想・コラッツ予想・ゴールドバッハ予想・ルジャンドル予想 → **「計算的証拠の報告 (証明ではない)」**。未解決問題の「証明の論文」は作成しません。
- Claude API モードでは、検証結果を `<tool_result>` として Claude に渡し、判定を変えないよう指示します。暗号化・復号は API に送りません。

証明ラボの計算部分は [`bada_gpt/src/`](../bada_gpt/src/) (BadaGPT のエンジン) を `build.js` が取り込みます。

## 🧩 言語生成の意味認識システム (v1.2.0)

レポート *Entropy on manifold and differential of equation* (`system_transport.pdf`) に繰り返し現れるエントロピー方程式群を、文の統計量に対応させて使います ([`src/semantic.bada`](src/semantic.bada)、すべて Bada)。

| 式 (レポート) | 対応させた量 | 使い道 |
|:--|:--|:--|
| (E1) `x log x` | エントロピー密度。`S(p) = −Σ p log p` | 文の情報量 H、文脈とのずれ D (Jensen–Shannon) |
| (E2) `log(x log x) ≥ 2 (y log y)^{1/2}` | `x = e^H`、`y = e^D` | **意味の門**: ずれが大きい文ほど多くの情報量を要求する足切り |
| (E3) `∫∫ 1/(x log x)² dx_m` | 語の順位 r の事前分布 `p0(r) ∝ 1/((r+1) log(r+1))²` | 未知語にも有限の驚き `−log p(w)` を与える平滑化 |
| (E4) `F = ∫ (R + ∇i∇j f)² / −(R + Δf) dm` | `f` = 文字 n-gram の驚き。勾配二乗を `e^{−f}` で重み付け | **情報の流れ**の滑らかさ |

(E2) で `D = 0` とすると門のしきい値は `x log x = 1`、つまり `x = e^{W(1)} ≈ 1.763` (既存の組込み `xlogx_root()`) になります。

| 送る文 | 動作 |
|:---|:---|
| `意味を認識して: 文` | 情報量・意味の担い手 (頻度 × 驚きが大きい語)・最も近い文脈・ずれ・門・流れを表示 |
| `ゼータ関数で文章を生成して` | 文字 5-gram モデルで候補を 8 個作り、門 (E2) で足切りしてから、文脈とのずれ D が最も小さい候補を選ぶ。全候補の表つき |

**実測** (`tools/semantic-test.js`):
- 文書の照合: 60 文書について、前半の語の分布から同じ文書の後半を当てる課題で、1 位正解 27/60 (45%)、3 位以内 40/60 (67%)。まぐれ当たりは 1.7% です。
- 生成の選別: 6 つの話題の平均で、選んだ文のずれ D は 0.527、候補全体の平均は 0.594 でした (小さいほど文脈に近い)。

**限界**:
- レポートは物理・幾何の文脈でこれらの式を述べており、言語については定めていません。どの量を x, y, f とみなすかは**本アプリの設計上の選択**で、レポートから導かれた定理ではありません。
- 意味認識は語の分布の統計です。文の内容が正しいかどうかは判定しません。
- 門 (E2) は通常の長さの文をほぼ通します (情報量の無い文だけを落とす弱い足切り)。選別の大半はずれ D の順位付けが担っています。
- 生成される文は文字 5-gram の出力なので、選別しても文として不自然なことがあります。自然な文章が必要なときは Claude API モードを使ってください (意味認識の結果は文脈として Claude に渡されます)。
- レポート自体は知識ベース (`kb.json`) には追加していません。

## 🔑 Claude API モード (任意)

⚙ 設定で **Claude API** を選び、Anthropic の API キーを入れると、Bada の頭脳が検索・計算した結果 (`<bada_context>`) をシステムプロンプトに入れて Claude に送り、ストリーミングで回答を表示します。

- モデル: `claude-opus-5-5` (既定) / `claude-sonnet-5-5` / `claude-haiku-4-5`
- effort: low / medium / high (Haiku 4.5 では送りません)
- Opus 5.5 と Sonnet 5.5 では `fallbacks: "default"` (ベータ `server-side-fallback-2026-07-01`) を付けています。安全分類器が応答を拒否した場合、API 側で代替モデルに切り替えて答えを返します。拒否 (`stop_reason: "refusal"`) はその旨を表示します。
- キーは端末のアプリ内保存領域 (localStorage) にだけ保存され、送信先は `https://api.anthropic.com` だけです。ブラウザから直接呼ぶため `anthropic-dangerous-direct-browser-access` ヘッダを使っています。共有端末ではキーを保存しないでください。

## ⚖ 正直な範囲

- **未解決問題は証明できません。** 証明ラボが「証明完了」と出すのは、帰納法で厳密に決まる多項式の等式と、コラッツの降下補題のような有限の手続きで確定する主張だけです。リーマン予想などへの判定は必ず「未解決」です。
- **Anthropic の Claude や OpenAI の ChatGPT の学習済みの重みは含まれていません。** 作り換えたのは「応答する仕組み」です。ローカルモードの知識は同梱の論文と方程式、それに Bada の数値核だけで、汎用の会話はできません。汎用の会話が必要なときは Claude API モードを使ってください。
- 生成 (`文章を生成`) は文字 5-gram の統計モデルです。文のつながりを真似るだけで、内容の正しさは保証しません。
- 方程式の判定 (成立 / 不成立) は `contact_blueprint.pdf` に記録された数値検証の結果をそのまま表示しています。論文集自身が「未解決」「予想」「否定」と標識した主張 (リーマン予想・P ≠ NP など) を、BadaClaude が解決済みとして扱うことはありません。
- 輸送機の設計図と UFO-OS は、論文の方程式に基づく思索的な可視化です (原本の注記どおり)。

## 🔧 開発

```sh
python3 bada_claude/tools/build_kb.py     # PDF → src/kb.json (pip install pypdf cffi)
node bada_claude/tools/build.js           # src/ → index.html
node bada_claude/tools/engine-test.js     # 75 件のテスト
node bada_claude/tools/lab-test.js        # 証明ラボ 48 件
node bada_claude/tools/semantic-test.js   # 意味認識 25 件
node bada_claude/tools/codegen-test.js    # 生成コードを各言語でコンパイル・実行
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
