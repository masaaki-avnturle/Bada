# Contact Transporter Studio — Bada で書かれた ContactGPT · 異次元輸送機 3D CAD · UFO 設計図面

設計図書 **「CONTACT TRANSPORTER 異次元への輸送機 3 次元設計図書」**
([`contact_blueprint.pdf`](contact_blueprint.pdf), 量子プログラミング言語 Bada による生成, 37 ページ)
に載っている方程式から作ったアプリです。**3 つのアプリはすべて量子プログラミング言語 Bada で書かれており**
([`bada/apps/`](bada/apps/))、アプリ内の **Bada IDE** でソースを読み・書き換え・新しいアプリを作って、その場で実行できます。
1 枚の自己完結 HTML にまとめ、**Android APK / Windows 10・11 EXE / Linux AppImage・deb** として GitHub Actions でビルドします。

> ※ 設計図書自身が述べているとおり、これは論文の方程式に基づく**思索的・フィクションの設計図 (幾何的な可視化)** です。
> 工学的に検証された装置ではなく、異次元への輸送や反重力飛行を実現するものではありません。

## Bada がアプリケーションプログラミング言語

```
 bada/apps/contactgpt.bada   bada/apps/transporter.bada   bada/apps/ufo.bada      ← アプリ本体 (Bada)
 bada/lib/  complex · zeta · jones · quantum · blueprint · ufo_flight .bada        ← ライブラリ (Bada)
        │  ui_* / cad_* / sheet_draw / gpt_* / eq_* / chat_* …  (アプリ用組込み関数)
 src/bada.js      Bada 処理系 (字句解析 → 構文解析 → バイトコード → スタック VM)
 src/badalib.js   ランタイムライブラリ: 数学・文字列・3D メッシュ・図面・Transformer 行列演算・UI
```

- **Bada 処理系** [`src/bada.js`](src/bada.js) — リポジトリの本家 [`bada_silent_vim/bada`](../bada_silent_vim/bada) (Python) を
  JavaScript へ忠実に移植 (同じ文法・同じバイトコード・同じ意味論、Python の任意精度整数も BigInt で再現)。
  **リポジトリ内の Bada プログラム 99 本で Python 版と出力が完全一致** ([`tools/conformance.py`](tools/conformance.py) を CI で検査)。
  `<-` 代入 / `<->` 比較 / `-<` 分岐・spawn / `>-` 合流・emit / `->` 遷移 / `>>` / `=>`、`Omega::DATABASE[space]`、`def`、`#include`。
- **アプリ = Bada プログラム**。UI (パラメータ欄・計算結果・グラフ・ボタン・プリセット) も Bada の `ui_*` 宣言から生成され、
  値が変わると `build()`、アニメーションは毎フレーム `frame(t)`、チャットは送信ごとに `on_message(q)` が呼ばれます。
- **各タブの Bada コンソール (REPL)** — 動いているアプリと同じ VM で Bada を実行: `ui_set("diameter", 30)  build()` など。
- **Bada IDE タブ** — ファイル一覧 (apps / lib / examples / user)、構文ハイライト、構文チェック、逆アセンブル (バイトコード表示)、
  **実行先の選択** (輸送機 3D CAD タブ / UFO 設計図面タブ / ContactGPT タブ / コンソール)、新規・読込・保存 (.bada)、既定に戻す。
  編集内容はブラウザ (アプリ) 内に保存されます。`examples/my_ship.bada` は Bada で新しい宇宙船 (葉巻型母船) を設計する例、
  `examples/template.bada` は新規アプリのひな形です。

## Bada でプログラミングして、要求に応えてアプリを作る

| アプリ | 要求・質問の例 | Bada の処理 |
|:--|:--|:--|
| **ContactGPT** | 「直径40mで舷窓12個のUFOの設計図アプリを作って」「リング5つの異次元輸送機のCADを作って」「4量子ビットのGHZのプログラムを書いて」「ゼータの零点を60まで求めるアプリを作って」 | [`lib/codegen.bada`](bada/lib/codegen.bada) が要求を読み、**Bada のアプリケーションのソースを書いて** `user/` に保存 → 「🛠 作ったアプリ」タブ (3D) / チャット内 (計算・量子回路) で実行、IDE で編集 |
| **輸送機 3D CAD** | 「外環を80mに」「塔を1.5倍」「24時間の搭乗者にして」「図面を作って」「STLで保存」「Γは？」「共鳴角は？」「上から見せて」 | [`apps/transporter.bada`](bada/apps/transporter.bada) の `on_request(q)` |
| **UFO 設計図面** | 「直径40mで舷窓12個」「12個の窓と4本の脚」「コイルを5_1に」「リングを外して」「名前は「SKY-1」」「白い図面で」「図面をPNGで保存」「上昇は？」 | [`apps/ufo.bada`](bada/apps/ufo.bada) の `on_request(q)` |

日本語の要求文の解析 (キーワードの前後の数値・倍率・「」の名前・否定・書き出し形式・視点) も Bada で書いています ([`lib/nlp.bada`](bada/lib/nlp.bada))。
ContactGPT が書いたプログラムは、ふつうの Bada アプリと同じく `ui_*` で画面を宣言し、`build()` / `frame(t)` / `sheet_draw` で 3D と図面を作ります。

## 論文 PDF を投稿して、アプリを作ってダウンロード

4 アプリとも **「📄 論文→アプリ」タブ** で論文の PDF を投稿できます (ドロップまたは「📂 PDF を選ぶ」。同梱の設計図書で試すボタンもあります)。

**ファイルの取り込み (フォルダを開いて選ぶ)** — 論文 PDF・Bada ソース (IDE の「読込…」)・設計値 JSON・学習済みの重みは、どれも OS 標準のファイル画面で選びます:

| 端末 | ファイルを選ぶ画面 | 保存先 |
|:--|:--|:--|
| Android | 同梱プラグイン [`BadaFiles`](app/cordova/bada-files/) が Android の「ファイル」画面 (Storage Access Framework) を開く。どのフォルダ (Download・Google ドライブなど) からも選べる | `Download/` (MediaStore、権限不要)。Android 9 以下は保存先を選ぶ画面 |
| Windows 10 / 11・Linux | OS 標準の「開く」ダイアログ (最初はダウンロード フォルダ) | ダウンロード フォルダ |
| ブラウザ・論文から作った単体アプリ | ブラウザのファイル選択 | 既定のダウンロード先 |

「📂 ダウンロード フォルダを開く」ボタンで、保存したファイルの場所をエクスプローラー / ファイル マネージャー / Android のファイル アプリで開けます。
(以前の版は Android で `<input type="file" accept=".pdf">` の拡張子指定が原因でファイル画面が開かなかったため、作り換えました。)

1. **読む** — pdf.js (日本語 CMap 同梱、オフライン) で本文を取り出し、[`src/paper.js`](src/paper.js) が題名・方程式
   (登録簿形式 / 本文中の数式)・数値パラメータ (「記号 = 数値 単位」)・分類を抽出し、数式の両辺を数値評価して成立 / 不成立を判定
2. **Bada でアプリを書く** — [`lib/paper.bada`](bada/lib/paper.bada) が論文のデータを Bada のリテラルとして埋め込んだアプリを書く:
   **方程式多様体アプリ** (方程式を Jones 結び目の上に並べた 3D・分類リング・数値パラメータの柱・A3 図面・「式 3」「ζ を含む式」に答える `on_request`)、
   **論文から設計した UFO**、**論文から設計した異次元輸送機**。ContactGPT に「論文からアプリを作って」「この論文の○○について」と頼むこともできます
3. **ダウンロード フォルダへ保存** ([`src/exporters.js`](src/exporters.js))

| ボタン | 保存されるもの |
|:--|:--|
| 作ったアプリ | Bada ソース `paper_*.bada` |
| 単体アプリ | `paper_*.html` — Bada 処理系 + 作ったアプリ入りの 1 ファイル。どの端末のブラウザでも動く |
| Windows アプリ | `paper_*.exe` — Windows 10 / 11 用。ダブルクリックで `%LOCALAPPDATA%\BadaApps\` に展開し、標準搭載の Microsoft Edge のアプリ ウィンドウで起動 ([ランチャー](app/windows/launcher.c)、Actions で Windows 実機テスト)。署名なしのため初回は SmartScreen の「詳細情報 → 実行」 |
| Android アプリ | `paper_*.apk` — ランナー APK の `assets/www/index.html` を差し替え、APK v1 (JAR) 署名 ([デバッグ鍵](app/signing/)) |
| Linux アプリ | `bada-paper-*_1.0.0_all.deb` — `sudo apt install ./….deb` でアプリ一覧に入る (Chromium / Firefox / xdg-open で起動) |
| 設計書 PDF | `paper_*_report.pdf` — 表紙・3D (等角図)・A3 図面・方程式・Bada ソースのページ |
| 論文 PDF | 投稿した PDF (原本) |

保存先: Windows 10 / 11・Linux (Electron 版) は OS の **ダウンロード** フォルダ、Android は `Download/` (Android 9 以下は保存先を選ぶ画面)、ブラウザは既定のダウンロード先。
※ 論文から作った APK はすべて同じパッケージ ID (`io.github.masaaki_avnturle.badapaperapp`) なので、新しく入れると前のものを置き換えます。

**Actions でも作れます**: [`papers/`](papers/) に PDF を置いて push すると、`paper-apps` ジョブが同じ一式を作り Artifacts **`PaperApps`** に置きます。

## ダウンロード (GitHub Actions) — 4 つのアプリ

リポジトリの **Actions** → **「Bada 4 apps build (ContactGPT / 輸送機 3D CAD / UFO 設計図面 / BadaClaude …)」** →
最新の成功した実行 (✅) を開き、ページ下部の **Artifacts** からダウンロードします。

| アプリ | Android (APK) | Windows 10 / 11 (EXE) | Linux (AppImage / deb) |
|:--|:--|:--|:--|
| **ContactGPT** | `ContactGPT-android-apk` | `ContactGPT-windows-exe` | `ContactGPT-linux` |
| **輸送機 3D CAD** | `TransporterCAD-android-apk` | `TransporterCAD-windows-exe` | `TransporterCAD-linux` |
| **UFO 設計図面** | `UFODesigner-android-apk` | `UFODesigner-windows-exe` | `UFODesigner-linux` |
| **BadaClaude** | `BadaClaude-android-apk` | `BadaClaude-windows-exe` | `BadaClaude-linux` |
| **Bada 統合スタジオ** (4 アプリ入りの統合アプリ) | `BadaStudio-android-apk` | `BadaStudio-windows-exe` | `BadaStudio-linux` |
| 論文 PDF から作ったアプリ | `PaperApps` (論文ごとに `.apk` / `.deb` / `.html` / `.bada` / 図面 / 論文 PDF) | ← | ← |

- **Android**: zip を展開して `…-android.apk` を開く (提供元不明のアプリのインストールを許可)
- **Windows 10 / 11**: `…-1.0.0-x64.exe` はインストーラ、`…-1.0.0-portable.exe` はインストール不要
- **Linux**: `chmod +x …-x86_64.AppImage` で実行、または `sudo apt install ./…-amd64.deb`

同じファイルは [Releases](https://github.com/masaaki-avnturle/Bada/releases) の **`contact-transporter-latest`** にも添付されます
(`ct-v*` タグを push するとそのタグの Release)。ワークフロー: [`.github/workflows/contact-transporter-build.yml`](../.github/workflows/contact-transporter-build.yml)、
アプリの定義 (名前・ID・含める画面): [`apps.json`](apps.json)。各アプリには Bada IDE・方程式レジストリが付いています。

## Bada 統合スタジオ — 4 アプリを 1 つに

**ContactGPT・BadaClaude・異次元輸送機 3D CAD・UFO 設計図面**を 1 つにまとめた統合アプリです (`apps.json` の `studio`)。
タブ: 💬 ContactGPT / 🧠 BadaClaude / 🛰 輸送機 3D CAD / 🛸 UFO 設計図面 / 📄 論文→アプリ / ⌨ Bada IDE / ∑ 方程式 2111 / ⓘ。
どちらの対話タブで「…のアプリを作って」と頼んでも、書かれた Bada アプリはそのまま CAD / UFO タブで動き、IDE で編集できます。
学習した ContactGPT の重みは BadaClaude の生成にも使われます。Claude API の設定欄は BadaClaude タブにあります。
Android は `BadaStudio-android-apk`、Windows 10 / 11 は `BadaStudio-windows-exe`、Linux は `BadaStudio-linux` からダウンロードします (アプリ ID は従来の統合版と同じなので、上書きで更新されます)。

## 1. ContactGPT — [`bada/apps/contactgpt.bada`](bada/apps/contactgpt.bada)

対話の流れはすべて Bada: `計算 …` は Bada の式として評価 (例 `計算 rs_z(14.1347)`, `計算 c_text(zeta_c([2, 0]), 8)`)、
方程式 ID の参照、設計値の即答 (lib/blueprint.bada で計算)、全文検索、そして生成。
**生成は Bada が 1 文字ずつ決めます**: Transformer のロジット (`gpt_logits`) → 上位 k (`topk`) → 温度付き softmax →
**量子状態 ψ_i = √a_i · e^{iθ_i} に符号化 (`q_encode`) → Born 則で測定 (`q_measure`)** — 設計図書 Q.1–Q.10 の「認知システム」そのもの。

### Transformer (ランタイムライブラリ側)

[`src/gpt.js`](src/gpt.js) — 外部ライブラリなし、Float32Array 上のテープ式自動微分で書いた decoder-only Transformer。

- トークン埋め込み + 位置埋め込み → [LayerNorm → **因果的マルチヘッド自己注意** → 残差 → LayerNorm → MLP (GELU) → 残差] × 2 層 → LayerNorm → 語彙ロジット (埋め込み共有)
- 学習: 交差エントロピー、**Adam** (β₁ 0.9, β₂ 0.99)、勾配クリップ、ウォームアップ + コサイン減衰
- 文字単位トークナイザ (日本語・数式記号をそのまま扱う)、推論は温度 + top-k サンプリング
- **コーパス = 設計図書の全方程式 2111 本 + 設計パラメータ Q&A** ([`tools/train.js`](tools/train.js))。
  学習済み重み [`data/contactgpt_weights.json`](data/contactgpt_weights.json) (float16) をアプリに同梱
- アプリ内の **Web Worker** で追加学習 / **ゼロから学習し直す** ことも可能 (損失曲線を表示、重みの保存・読込)
- 逆伝播は数値微分と照合済み (`tools/gradcheck.js`, 相対誤差 < 1e-5)

検索エンジン [`src/chat.js`](src/chat.js) (文字 bigram BM25 + タグ + 日本語キーワード展開) は Bada から `eq_search` で呼びます。

## 2. 異次元輸送機の 3D CAD — [`bada/apps/transporter.bada`](bada/apps/transporter.bada)

設計図書 第 1 章の値を **Bada で** 方程式から計算し ([`bada/lib/blueprint.bada`](bada/lib/blueprint.bada)。
Riemann–Siegel θ、Borwein 法の ζ(½+it)、Jones 多項式、複素数演算もすべて Bada — [`tools/test.js`](tools/test.js) で PDF の値と照合)、
`cad_torus` / `cad_knot` / `cad_pose` … で部品を組み立て、`frame(t)` でジンバルを回します。

| 段 | 方程式 | 値 |
|:---|:---|:---|
| ② 特殊相対論 | Γ = 18 h / 1 s, φ = arcosh Γ | Γ = 64800, 1−β = 1.19075e-10, φ = 11.7722 |
| ②' 輸送計量 | e^{−2πT\|ψ\|} = 1/Γ | T\|ψ\| = 1.76329 (x log x = 1 の根 1.76322) |
| ③ 複素回転体 | Θ = θ + iφ, ω 段間比 φ/π, Ω = Mgl/(I₃ω₃) | ω = 0.10472, 0.39241, 1.47043 rad/s, Ω = 3.7064 |
| ④ Γ・ζ 多様体 | θ(φ), Z(φ) = e^{iθ(φ)} ζ(½ + iφ) | θ = −2.58136, Z = −1.33415 |
| ⑤ Jones | V_K(t*), t* = e^{iθ(φ)} | 3_1: −0.116342 + 2.30908i, 4_1: 3.56478, 5_1: −2.81527 + 1.09654i |

- 部品: ジンバル外環 / 中環 / 内環 (角速度 ω で入れ子回転)、軸受、ポッド (歳差 Ω)、塔・ガントリー、
  **Jones コイル** (3_1 = (2,3) トーラス結び目, 5_1 = (2,5), 4_1 = 8 の字結び目 — 床下)、床版・井戸、
  **扉の軸 n̂** (CERN の衝突で粒子が消えた方向) と **共鳴窓** (|V(e^{iα})| の極小角)
- WebGL ビューア (オービット / パン / ピンチ、ISO・上・正面・側面、ワイヤ、青図、部品の表示切替)
- 書き出し: **STL** (バイナリ) / **OBJ + MTL** / **DXF (3DFACE)** / PNG / **図面 SVG・DXF** / パラメータ JSON

## 3. UFO 設計図面作成ソフト — [`bada/apps/ufo.bada`](bada/apps/ufo.bada)

船体の回転断面・部品配置・寸法・部材表・飛行計算をすべて Bada で書いています (`sheet_draw` で A3 図面を生成)。

- パラメトリック円盤機: 直径・縁厚・上下殻高さ・ドーム・舷窓・推進ポッド・着陸脚・反重力コイル (Jones 3_1 / 4_1 / 5_1)・コンタクト・リング・配色
- プリセット: 標準円盤 01 / アダムスキー型 / 大型母船 / コンタクト機
- **A3 図面を自動作図** ([`src/drafting.js`](src/drafting.js)): 第三角法の平面図・正面図・右側面図 + 等角図、
  輪郭線・特徴稜線の正投影、寸法線、中心線、尺度の自動選択、表題欄、**部材表** (EXP.156 の材料: SiO₂ プリズム, Fe·Co60·Pt·Al 合金, Al₂O₃, Cs, Mg, He, H₂ …)、注記
- **飛行モデル (UFO.1–26)**: x = 1 + r₀/r, **L = cosh(x log x)** (地表 2.125), a = (L − 1)·g_eff (11.047 m/s²),
  U = GMm/r, E_ag = U·L, E⊥ = mc² − ½mv², 上昇シミュレーション (10 s で 607.6 m, 110.46 m/s)
- 書き出し: **図面 SVG / PNG / DXF**、STL / OBJ / DXF 3D、プロジェクト JSON の保存・読込

## 4. BadaClaude — [`bada/apps/badaclaude.bada`](bada/apps/badaclaude.bada)

Claude / ChatGPT が「質問を受けて答える」までの仕組みを、**正規の Bada** (`<-` `-<` `>-` `->` `<->` `Omega::DATABASE`) で書いた対話エンジンです。
知識は論文 10 本 ([`data/badaclaude/sources/`](data/badaclaude/sources/) + 設計図書) の抜粋 256 件と方程式 2111 本。

| 段 | Bada での処理 |
|:--|:--|
| ① 字句化 | `kb_tokens(q)` (文字種の連なり + 漢字 2-gram) → 不要語の除去 → 同義語の展開 (`query_tokens`) |
| ② 意図推定 | Unknown-Prior Engine: 手掛かり z → a = softmax(z) → ψ_i = √a_i·e^{iθ_i} (`q_encode`) → \|ψ\|² (`q_probs`) |
| ③ 検索 | BM25。ホストは転置索引 (`kb_postings`) を渡すだけで、**採点・順位付けは Bada** (`search`) |
| ④ 道具 | アプリ作成 (`codegen`) / 計算 (`bada_expr`) / 量子回路 (H + CNOT, Born 則測定) / 送った ```` ```bada ```` コードの実行 / 設計値 / 投稿論文 |
| ⑤ 回答 | 出典 (論文名・ページ・方程式 ID) つきの回答、Transformer + 量子測定の生成 (任意)、**Claude API** (任意) |
| ⑥ 記録 | `Omega::DATABASE[ledger]` に boot / turn / build / claude を追記 (「台帳」で表示) |

- 例: 「ゼータ関数とベータ関数の関係は?」→「もっと」/「ACAFE.17」/「計算 rs_z(14.134725)」/「ベル状態を見せて」/「リーマン予想は証明されたの?」/「直径40mで舷窓12個のUFOの設計図アプリを作って」/「台帳」
- **📄 論文→アプリ** タブ: ほかの 3 アプリと同じく、PDF を投稿して作ったアプリ・Windows 10 / 11 EXE・APK・Linux .deb・設計書 PDF・論文 PDF をダウンロード フォルダへ保存
- **Claude API モード (任意)**: 右の設定で「Claude API」を選び API キーを入れると、Bada が検索・計算した結果を `<bada_context>` としてシステムプロンプトに入れ、Claude に送ってストリーミング表示します (`system_prompt` も Bada)。モデル `claude-opus-5-5` (既定) / `claude-sonnet-5-5` / `claude-haiku-4-5`、effort low / medium / high。Opus 5.5 / Sonnet 5.5 では `fallbacks: "default"` (ベータ `server-side-fallback-2026-07-01`) を付け、安全分類器が拒否したときは API 側の代替モデルが答えます。キーは「端末に保存」を選んだときだけ端末内に保存し、通信先は `https://api.anthropic.com` だけです (この接続を許可しているのは BadaClaude だけ)。
- 正直な範囲: **Anthropic の Claude や OpenAI の ChatGPT の学習済みの重みは含みません**。ローカルの知識は同梱の論文と方程式だけです。論文集自身が「未解決」「予想」と標識した主張 (リーマン予想・P ≠ NP) を解決済みとしては扱いません。
- 知識ベースの再生成: `python3 contact_transporter/tools/build_kb.py` (pip install pypdf cffi) → `data/badaclaude/kb.json`

## 5. 方程式レジストリ

全 2111 本 (数値評価 632 本: calc 220 / 成立 231 / 不成立 181、記号式 1479 本) を検索・タグ・状態で絞り込み表示。
[`data/equations.json`](data/equations.json) は [`tools/extract_equations.py`](tools/extract_equations.py) が
PDF のテキスト ([`data/contact_blueprint.txt`](data/contact_blueprint.txt)) から抽出したものです。

## 開発

```sh
node contact_transporter/tools/build.js all  # → dist/{contactgpt,transporter,ufo,badaclaude,studio}/www/index.html (ブラウザで開けば動く)
node contact_transporter/tools/package-app.js ufo   # → dist/ufo/electron (Windows/Linux) + dist/ufo/cordova (Android)
node contact_transporter/tools/test.js       # Bada アプリ 4 本・設計図書の数値再現・GPT 勾配・CAD・図面のテスト
python3 contact_transporter/tools/conformance.py   # Bada の JS 移植 ↔ Python 本家 (全 .bada で出力一致)
node contact_transporter/tools/badahost.js apps/ufo.bada   # Bada アプリをヘッドレス実行
node contact_transporter/tools/train.js 2400 # ContactGPT をゼロから学習 (--resume で追加学習)
cd contact_transporter/dist/ufo/electron && npm install && npm start   # デスクトップ版をローカル起動
```

```
contact_transporter/
  contact_blueprint.pdf        元の設計図書
  bada/  apps/ (contactgpt · transporter · ufo · badaclaude)  lib/ (complex · zeta · jones · quantum · blueprint · ufo_flight · nlp · codegen
         · paper · answers · gen · paper_chat)  examples/
  data/  equations.json  contactgpt_weights.json  contact_blueprint.txt  badaclaude/ (kb.json · sources/ 論文 9 本)
  src/   bada.js badalib.js  paper.js exporters.js  physics.js gpt.js chat.js cad.js drafting.js viewer.js app.js index.html style.css
  tools/ build.js package-app.js test.js conformance.py badahost.js train.js gradcheck.js extract_equations.py build_kb.py
         paper2app.js paperinfo.js verify-apk.js   (論文 PDF → アプリ)
  papers/  論文 PDF の投稿先 (Actions が PaperApps を作る)   app/signing/  論文アプリ APK のデバッグ署名鍵
  apps.json  4 アプリ + 統合版の定義 (名前・アプリ ID・含める画面)
  app/   electron/ (Windows / Linux)   cordova/config.xml (Android)
```

MIT License — masaaki-avnturle / Bada
