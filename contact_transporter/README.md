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

## ダウンロード (GitHub Actions)

1. リポジトリの **Actions** → **「Contact Transporter Studio build (Android APK + Windows 10/11 EXE + Linux)」** を開く
2. 最新の成功した実行 (✅) を開き、ページ下部の **Artifacts** からダウンロード

| Artifact | 中身 |
|:---|:---|
| `contact-transporter-android-apk` | `ContactTransporterStudio-android.apk` (提供元不明アプリのインストールを許可して導入) |
| `contact-transporter-windows-exe` | `ContactTransporterStudio-1.0.0-x64.exe` (インストーラ) / `…-portable.exe` (インストール不要) — Windows 10 / 11 |
| `contact-transporter-linux` | `ContactTransporterStudio-1.0.0-x86_64.AppImage` (`chmod +x` で実行) / `…-amd64.deb` (`sudo apt install ./….deb`) |
| `contact-transporter-www` | 自己完結 HTML (`index.html` をブラウザで開くだけでも動作) |

同じファイルは [Releases](https://github.com/masaaki-avnturle/Bada/releases) の **`contact-transporter-latest`** にも添付されます
(`ct-v*` タグを push するとそのタグの Release、Actions の **Run workflow** では任意のタグを指定可)。
ワークフロー: [`.github/workflows/contact-transporter-build.yml`](../.github/workflows/contact-transporter-build.yml)

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

## 4. 方程式レジストリ

全 2111 本 (数値評価 632 本: calc 220 / 成立 231 / 不成立 181、記号式 1479 本) を検索・タグ・状態で絞り込み表示。
[`data/equations.json`](data/equations.json) は [`tools/extract_equations.py`](tools/extract_equations.py) が
PDF のテキスト ([`data/contact_blueprint.txt`](data/contact_blueprint.txt)) から抽出したものです。

## 開発

```sh
node contact_transporter/tools/build.js      # → contact_transporter/dist/www/index.html (ブラウザで開けば動く)
node contact_transporter/tools/test.js       # Bada アプリ 3 本・設計図書の数値再現・GPT 勾配・CAD・図面のテスト
python3 contact_transporter/tools/conformance.py   # Bada の JS 移植 ↔ Python 本家 (全 .bada で出力一致)
node contact_transporter/tools/badahost.js apps/ufo.bada   # Bada アプリをヘッドレス実行
node contact_transporter/tools/train.js 2400 # ContactGPT をゼロから学習 (--resume で追加学習)
cd contact_transporter/app/electron && npm install && npm start   # デスクトップ版をローカル起動
```

```
contact_transporter/
  contact_blueprint.pdf        元の設計図書
  bada/  apps/ (contactgpt · transporter · ufo)  lib/ (complex · zeta · jones · quantum · blueprint · ufo_flight)  examples/
  data/  equations.json  contactgpt_weights.json  contact_blueprint.txt
  src/   bada.js badalib.js  physics.js gpt.js chat.js cad.js drafting.js viewer.js app.js index.html style.css
  tools/ build.js test.js conformance.py badahost.js train.js gradcheck.js extract_equations.py
  app/   electron/ (Windows / Linux)   cordova/config.xml (Android)
```

MIT License — masaaki-avnturle / Bada
