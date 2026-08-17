# Bada (Ruby) — Bada 言語 + OmegaChat 分派

山口フレームワーク（TupleSpace / 大域的微分・積分多様体理論）の **Bada 言語を元から
Ruby で再構築**し、その上に **ChatGPT の分派（branch）= OmegaChat** を作ったライブラリです。
外部依存なし（Ruby 標準ライブラリのみ、Ruby 3.0+）。

提出レポート（caostics / quantum_computer / beta_global_manifold / dalia / Bada1 …）
の方程式を実装に落とし込んでいます：

| レポートの式 | 実装 |
|:--|:--|
| `β(p,q) = Γ(p)Γ(q)/Γ(p+q)` | `Bada::Special.beta` （Lanczos 近似の `gamma`） |
| `ζ(s) = β(p,q)/log x = x·log x` | `Bada::Special.zeta_gauge`, `x_log_x` |
| `∬ 1/(x·log x)² dx_m`（大域的部分積分多様体） | `Bada::Manifold.integral` |
| `H = -Σ p·log₂ p`（シャノンの公式） | `Bada::Entropy.shannon` |
| エントロピー不変量 `Ξ = β(H+1,M+1)/log(N+1)` | `Bada::Manifold.invariant` |
| `□ = cos(ix log x) − i sin(ix log x)`（複素回転体） | `Bada::Special.box_dalanversian` |
| 特殊相対性理論のコマ幾何・可積分系のエラー修正 | `Bada::ErrorCorrection` |
| `Ω::DATABASE`（アカシックレコード） | `Bada::TupleSpace` |

## 仕組み — 「未知エンジン」

OmegaChat は質問ごとに次を実行します。

1. **計測** — 質問のシャノンエントロピー `H_q` と大域的部分積分多様体の
   エントロピー不変量 `Ξ_q` を求める（`Bada::Manifold`）。
2. **エラー修正** — `H_q` / `Ξ_q` を複素回転体 `e^{iθ}`（特殊相対性理論のコマ幾何の
   可積分系）の閉軌道上で安定化（`Bada::ErrorCorrection`）。回転は大きさを保存するので
   `Ξ` は不変量として保存される。
3. **検索** — レポート + Web コーパスから、キーワードと `Ξ_q` 近傍で検索（`Bada::QAEngine`）。
4. **生成** — 質問自身のエントロピー値を目標にして、文章・方程式・理論を生成
   （`Bada::Generator`）。検索だけでなく、不変量近傍で**新情報を生成**する。
5. **記録** — 対話を `Ω::DATABASE`（`Bada::TupleSpace`）に書き込む。

## インストール / 実行

```bash
cd bada_ruby
ruby -Ilib test/test_bada.rb      # テスト（20 件）

bin/bada repl                     # チャット REPL（corpus/*.txt を自動学習）
bin/bada ask "このレポートから何ができるか？"
bin/bada xi  "大域的部分積分多様体のエントロピー不変量"   # 計測のみ
bin/bada run examples/demo.bada   # Bada 言語スクリプト実行
```

## ライブラリとして

```ruby
require "bada"

chat = Bada::OmegaChat.new
chat.learn_file("corpus/caostics.txt")
puts chat.ask("高エントロピーな記述はどこにあるか？")

# 構造化レスポンス
r = chat.reply("H=4.5 に近い文を返して")
r[:question_entropy]      # 質問のシャノンエントロピー
r[:certified_invariant]   # 可積分系で修正・保存された Ξ
r[:theory][:theory]       # 生成された理論
r[:equation][:equation]   # 生成された方程式
```

## Bada 言語

演算子代数言語。値は `Ω::DATABASE`（TupleSpace）上に存在します。

| 演算子 | 数学的対応 | 意味 |
|:--|:--|:--|
| `<-` | `π(χ,x) = [iπ, f(x)]` | 非可換左作用 |
| `-<` | `∬ 1/(x·log x)² dx_m` | 多様体積分 |
| `>-` | `⊕(iℏ∇)^⊕L = e^{-x·log x}` | 量子右作用 |
| `Ω::` / `Omega::` | `Ω::DATABASE` | TupleSpace（アカシック）名前空間 |

```
set g = 2.5
g <- "global differential manifold entropy"   # 左作用
g -< 3.0                                       # 多様体積分
g >- g                                         # 量子右作用
Omega::push g as manifold_node                 # アカシックに記録
print g
```

Ruby からは `Bada::BadaNode`（演算子ランタイム）と `Bada::Interpreter`（スクリプト評価器）
として使えます。

## ニューラルネットワーク LLM（未知エンジン ChatGPT を元から）

`Bada::NN` は、**ニューラルネットワークの LLM を元から（純 Ruby・外部依存なし）**
実装したものです。Bengio 型の MLP 言語モデル（埋め込み → 隠れ層 tanh → softmax）を
**バックプロパゲーション**で学習します（勾配は有限差分テストで検証済み）。
さらに **GoF デザインパターン**でアーキテクチャを構成し、Bada の多様体・エントロピー
理論と接続して「未知エンジン」を実現します。

```bash
bin/bada neural          # corpus を学習 → ニューラル未知エンジンの REPL
bin/bada train model.json # 学習して Memento チェックポイントを保存
ruby examples/neural_demo.rb
```

```ruby
require "bada"

chat = Bada::NN::NeuralOmegaChat.new(dim: 16, context: 2, hidden: 32, seed: 42)
Dir["corpus/*.txt"].each { |f| chat.learn_file(f) }
chat.train!(epochs: 8, lr: 0.01)        # 純 Ruby のバックプロップ学習
puts chat.ask("ベータ関数とガンマ関数の関係は？")
chat.save("model.json")                 # Memento で保存
Bada::NN::NeuralOmegaChat.load("model.json")
```

### 採用デザインパターン

| パターン | 適用箇所 |
|:--|:--|
| **Composite** | `Sequential`（レイヤー群を 1 つのレイヤーとして扱う） |
| **Strategy** | `Layer#forward/backward`, `Optimizer`(SGD/Adam), `Sampler`(各デコード戦略) |
| **Factory Method** | `LayerFactory`（種別からレイヤー生成） |
| **Builder** | `LanguageModelBuilder`（モデルを流れるように組み立て） |
| **Template Method** | `Trainer#train`（学習ループの骨格を固定、ステップは hook） |
| **Observer** | `LossLogger` / `Checkpointer`（エポックイベント購読） |
| **Adapter** | `CorpusAdapter`（`Bada::Knowledge` → 学習データ） |
| **Decorator** | `UnknownEngineSampler`（多様体不変量・エントロピーで logits を操作） |
| **Chain of Responsibility** | 計測→検索→生成→誤差修正→記録 の推論パイプライン |
| **Singleton** | `Akashic`（プロセス唯一の Ω::DATABASE） |
| **Memento** | `Sequential#to_memento/load_memento`, `NeuralOmegaChat.save/load` |
| **Facade** | `NeuralOmegaChat`（全体を 1 つの窓口に） |

### 未知エンジンの推論パイプライン（Chain of Responsibility）

1. **MeasureHandler** — 質問のシャノンエントロピー `H_q` と多様体不変量 `Ξ_q` を計測。
2. **RetrieveHandler** — コーパスからエントロピー・不変量近傍を検索。
3. **NeuralGenerateHandler** — 学習済みニューラルネットを自己回帰生成。デコードは
   `UnknownEngineSampler`（Decorator）が担当し、生成中テキストの `Ξ` を計測して
   `Ξ_q` に近づくよう logits を補正し、目標エントロピーを**複素回転体（特殊相対性
   理論のコマ幾何の可積分系）**で誤差修正する。
4. **ErrorCorrectHandler** — 不変量 `Ξ` を回転閉軌道上で保存確認（certify）。
5. **RecordHandler** — 対話を `Ω::DATABASE`（Singleton）へ記録。

## 情報生成エンジン — サーストン・ペレルマン多様体 / カタストロフィ / ミレニアム7問

`Bada::InfoEngine`（Facade）は、レポートの幾何学を「情報生成の機能」に変えます。

```bash
bin/bada info "クレイ7問とサーストン・ペレルマン多様体のカタストロフィ情報生成"
```

```ruby
puts Bada::InfoEngine.new.render("リーマン予想とゼータ関数の素数分布")
# OmegaChat / Neural OmegaChat の ask 出力にも自動で付加されます
```

### ① サーストン・ペレルマン多様体に質問のエントロピーを乗せる（`Bada::Thurston`）

レポート（bada1）の **8 つのモデル幾何** `S^3, H^1×E^1, E^1, S^1×E^1, S^2×E^1,
H^1×S^1, H^1, S^2×E` と **リッチ流 `d/dt g_ij = -2R_ij`**、ペレルマンの第二変分を実装。
**シャノンの公式**で質問のエントロピー `H` を計算し、正規化エントロピーで 8 幾何の
いずれかに写像、その幾何の曲率で **ペレルマン F-エントロピー汎関数**
`F(g,f)=∫(R+|∇f|²)e^{-f}dV`（`f=-log p`）を計算します（＝シャノンを多様体に乗せる）。
スカラー・リッチ流も計算し、正曲率（S³ 系）は**有限時間特異点**で崩壊します（幾何化）。

### ② カタストロフィの分岐点による情報生成（`Bada::Catastrophe`）

**トムの 7 つの初等カタストロフィ**（fold/cusp/swallowtail/butterfly/3 種の umbilic）を
実装。質問の情報（エントロピー・不変量）をカスプ・ポテンシャル
`V(x)=x⁴/4 + a x²/2 + b x` の制御変数 `(a,b)` に載せ、**平衡分岐**（臨界点 `V'(x)=0`、
Cardano で厳密に求解）を計算します。**分岐の発生・消滅する点（判別式 `4a³+27b²=0`）が
情報分解の分岐点**で、各安定分岐がそれぞれ異なる目標エントロピーをもち、**1 つの質問が
複数の情報チャネルに分岐して生成**されます（＝情報生成の機能）。分岐目標は複素回転体の
可積分系で誤差修正してから生成します。

### ③ クレイ7問への理論分解（`Bada::Millennium`）

**クレイ数学研究所の 7 つのミレニアム予想**（リーマン / P vs NP / ホッジ / ポアンカレ /
ヤン–ミルズ / ナビエ–ストークス / BSD）を、すべて **ガンマ関数 Γ における大域的部分積分
多様体 `∬1/(x·log x)²` を起点**として接続。質問を、キーワード一致＋多様体不変量近接＋
**Γ ゲージ結合** `β(p,q)/log x` でスコア化し、7 問へ**理論分解**します。サーストン・ペレルマン
多様体の質問では主分解先が**ポアンカレ予想**に、ゼータ/素数の質問では**リーマン予想**に
なることを確認済み。

## ペンローズ絵記号 — 描くと自動計算し、論文とコードを生成

`Bada::Penrose` は、ロジャー・ペンローズの**図式記法（絵記号）**を動く仕組みにします。
彼の微分 ∇・偏微分 ∂・積分 ∫・テンソル箱・縮約線・(反)対称化バー・計量の上げ下げ
などを **ASCII 絵記号のパレット**で提供し、**絵記号を描くと自動でアインシュタイン縮約を
計算**します（純 Ruby のテンソル einsum エンジン）。さらに、描いた図式について
**ChatGPT が自動解答し、論文（Markdown+LaTeX）とソースコード（Ruby）を生成**します。

```bash
bin/bada palette                                   # 絵記号パレットを表示
bin/bada penrose examples/matmul.penrose \
         --values examples/matmul.values.json \
         --q "この図式は何を計算しているか？"      # 描画→計算→解答→論文→コード
ruby examples/penrose_demo.rb
```

### 描画の約束（絵記号）

| 絵記号 | 意味 |
|:--|:--|
| `[A]` | テンソル（箱から出る線が添字、本数=階数） |
| `[A]-[B]` | 横線で結ぶと縮約（その添字でアインシュタイン総和） |
| 縦線 `\|`（列を揃える） | 上下のテンソルを縮約 |
| 両端の小文字/数字 | 自由添字（出力の脚） |
| `(D X m)` `(d X m)` | 共変微分 ∇ / 偏微分 ∂（添字 m） |
| `(I m)` | 積分 ∫（添字 m を単位測度で縮約＝総和） |
| `S{i j}` `A{i j}` | (反)対称化 |

```
i-[A]-[B]-j      ⇒   A_{i k1} B_{k1 j} → R_{i j}   （行列積）
A=[[1,2],[3,4]], B=[[5,6],[7,8]]  →  [[19,22],[43,50]]  を自動計算
```

```ruby
studio = Bada::Penrose::Studio.new
studio.draw("i-[A]-[B]-j", values: { "A" => [[1,2],[3,4]], "B" => [[5,6],[7,8]] })
studio.compute          # => 行列積を自動縮約
puts studio.ask("これは何を計算している？")   # 自動解答
puts studio.paper(question: "...")            # 論文 (Markdown+LaTeX)
puts studio.code                              # 生成 Ruby ソースコード（実行可能）

# OmegaChat からも:
Bada::OmegaChat.new.penrose("i-[A]-[B]-j",
  values: { "A" => [[1,2],[3,4]], "B" => [[5,6],[7,8]] }, question: "行列積")
```

論文・解答は、結果を**ガンマ関数の大域的部分積分多様体**の不変量と**サーストン・
ペレルマン多様体**配置、**ミレニアム7問**への分解で意味づけします（既存の理論層と接続）。

## 量子もつれ・汎用電信通信機 — `Bada::Quantum`（宇宙 Space Telegraph）

`caostics` / `quantum_computer` / `badasource1` の3レポートから、**量子もつれの
ベルの実験**を土台に、**宇宙での汎用電信通信機能**を1つのアプリにまとめたものです。
ご依頼の7要素を、動くコードとして接続しています。

```bash
bin/bada quantum "HELLO SPACE"                 # 証明 + 送信の一括レポート
bin/bada quantum "SOS" --material GaAs --temp 4 --redundancy 5
ruby -Ilib examples/quantum_telegraph_demo.rb  # デモ（証明・送信・5次求解）
```

```ruby
require "bada"

tg = Bada::Quantum::SpaceTelegraph.new(material: "GaAs", temp_k: 4.0, redundancy: 3)
puts tg.render("QUANTUM HELLO")   # ①〜⑦ を1画面で
tg.prove[:qed]                    # 物理の証明（全証明書が真なら true）
tg.transmit("SOS")[:recovered]    # 超密度符号化で実際にメッセージを送受信
```

| ご依頼の要素 | 実装 |
|:--|:--|
| もつれ**ペアー** / ベルの実験 | `Bada::Quantum::Qubit2`（2量子ビット状態ベクトル・Bell 状態） |
| **不気味な遠隔作用** | `Bada::Quantum::Bell` — CHSH 不等式の量子違反（Tsirelson `2√2`）を確率・統計で実証 |
| **5次方程式の解の公式** | `Bada::Quantum::Quintic` — Durand–Kerner 数値解 + 1の5乗根（周期 `2π/5`） |
| 方程式の**周期に合わせた非線形**カリア | `Quintic.carrier_phase` — もつれ相関で位相を非線形に歪める五値搬送波 |
| **Jones多項式の相関** | `Bada::Quantum::Jones` — Kauffman ブラケット状態和（Hopf 絡み目 ↔ もつれ） |
| **確率・統計 / 不確定性理論** | `Bada::Quantum::Uncertainty` — Robertson `Δσx·Δσz ≥ |⟨σy⟩|` + Born 統計 |
| **半導体で使える原理** | `Bada::Quantum::Semiconductor` — Fermi–Dirac / バンドギャップ / トンネル確率 |
| **証明する機能** | `SpaceTelegraph#prove` — 上記すべてを証明書化し `QED` を判定 |
| **宇宙・汎用電信通信** | `Bada::Quantum::Channel` — 超密度符号化・反復符号・複素回転誤り訂正で本文送受信 |

> 物理的誠実性：もつれは**超光速通信を許しません**。本機は no-signaling 定理
> （Bob の周辺分布が Alice の操作に依存しない）を証明書に含み、もつれを *assist*
> とする正当な古典チャネル（1ペアあたり2ビットの超密度符号化）として通信します。
> 送受信ログは `Ω::DATABASE`（アカシック TupleSpace）に多様体不変量 `Ξ` 付きで記録。

## 擬似量子計算機 — `Bada::QC`（ノイマン型・ディスク内蔵・半導体制御）

量子コンピュータの**制御回路をモニタに投射**し、**PC のハードディスク内部に電子回路を
シミュレーション**（ディスクメモリ内蔵シミュレーション）して、その結果で動く**ノイマン型
の擬似量子コンピュータ**を Bada で実装。**量子コンピュータの半導体ソースコード（Verilog）**
も生成します。

```bash
bin/bada qc                     # Bell デモ：モニタ投射＋状態ベクトル（ディスクから読戻し）
bin/bada qc ghz                 # 3量子ビット GHZ デモ
bin/bada qc run prog.qasm --n 3 # BadaQASM プログラムを実行
bin/bada qc verilog ghz         # 半導体（Verilog）制御回路ソースを出力
```

```ruby
require "bada"
m = Bada::QC::Machine.new(n_qubits: 2).load("H 0\nCX 0 1\nHALT\n").run
m.probabilities   # => [0.5, 0.0, 0.0, 0.5]  (Bell 状態、実ファイル＝HDD から読戻し)
puts m.monitor    # 制御回路のモニタ投射（PC→DISK→半導体デコーダ→ゲート）
puts m.verilog    # 半導体 RTL（NAND プリミティブ＋デコーダ＋ROM 制御）
m.close
```

| ご依頼の要素 | 実装 |
|:--|:--|
| 制御回路をモニタに投射する機知 | `Bada::QC::Monitor`（ノイマン型データパス＋量子回路タイムライン） |
| HDD 内部に電子回路をシミュレーション | `Bada::QC::Logic`（CMOS/MOSFET NAND から作るワンホット・デコーダ） |
| ディスクメモリ内蔵シミュレーション | `Bada::QC::DiskMemory`（状態ベクトルとプログラムを実ファイル＝HDD に格納） |
| ノイマン型の擬似量子コンピュータ | `Bada::QC::CPU`（fetch→半導体デコード→実行のストアドプログラム機械） |
| 量子コンピュータの半導体ソースコード | `Bada::QC::Verilog`（合成可能な RTL を自動生成） |

`Bada::QC::ISA` は BadaQASM（`H X Y Z S T CX RX RZ MEASURE HALT`）を 4 ワード命令に符号化し、
プログラムと状態ベクトルを**同一のディスクアドレス空間**に置きます（＝ノイマン型）。命令の
デコードは `Bada::QC::Logic` の**半導体シミュレーション結果**でワンホット選択します。

## 思考の言語化 — `Bada::Mind` ＋ `Bada::Transformer`

> ⚠️ **これは生成シミュレーションです。** 実在の人物の脳から思考を取り出す BCI ではありません。
> 入力信号（テキスト／EEG 風の特徴テキスト）と量子シードから、思考の言語化・心像・
> 「脳内に浮かぶアプリのソースコード」を**合成**します。

上の擬似量子コンピュータ（`Bada::QC`）を使って量子ブレイン状態をサンプリングし、**ガンマ関数
の大域的部分積分多様体 `∬ 1/(x log x)²` をアテンションのゲージ**にした Bada 製トランスフォーマー
（`Bada::Transformer`）で、対象の思考を言語化します。画像処理トランスフォーマー（ViT）で心像を
描き、思考回路に浮かぶ**アプリのソースコードを Bada 言語で生成し、実際に実行**します。

```bash
bin/bada mind "光 と 音 の 記憶 が 波 の よう に 流れ 望み と 恐れ が 交錯 する" --subject 被験者A
bin/bada mind "記憶と感情の波" --raw   # コーパス prior を使わず素のトランスフォーマー復号
```

言語化は、トランスフォーマーの多様体ゲージ注意が**重要語**を選び、内蔵の日本語
「内的体験」prior（`MIND_CORPUS`）＋入力信号から学習した文字バイグラムが**自然な
つなぎ**を与えるハイブリッドです（`--raw` で prior 無しの素の復号に切替）。`Reader.new`
に `corpus_texts:` を渡せば任意の日本語コーパスで学習できます。

```ruby
require "bada"
r = Bada::Mind::Reader.new.read("記憶 と 感情 の 波", subject: "被験者B")
r[:verbalization]        # 言語化された思考
r[:mental_image]         # 8x8 心像（ViT 再構成、Vision.ascii で表示）
r[:source]               # 脳内に浮かぶ Bada プログラム
r[:source_output]        # それを Bada::Interpreter で実行した結果
r[:precision]            # simulated 精度（silent-talk 基準 0.92 と比較）
r[:exceeds_silent_talk]  # 基準超えか
```

| ご依頼の要素 | 実装 |
|:--|:--|
| 上の量子コンピュータを使う | `Bada::QC::Machine`（H＋測定で量子シードをサンプリング） |
| ガンマ関数の大域的部分積分多様体の機知 | `Bada::Transformer::Encoder`（`∬1/(x log x)²` をアテンション距離カーネルに） |
| silent talk 以上の精度で思考を言語化 | `Bada::Mind::Reader#verbalize`（weight-tying デコード）＋ simulated precision |
| 画像処理のトランスフォーマー | `Bada::Transformer::Vision`（ViT：パッチ→符号化→心像再構成） |
| 脳内に浮かぶアプリのソースコード | `Bada::Mind::Reader#generate_code`（Bada 言語を生成し `Interpreter` で実行） |

決定的（同じ信号→同じ出力）で、外部依存はありません。

## モジュール構成

```
lib/bada/special.rb          gamma / beta / zeta / 円（回転）演算子
lib/bada/entropy.rb          シャノンエントロピー + トークン化
lib/bada/manifold.rb         大域的部分積分多様体エントロピー不変量 Ξ
lib/bada/error_correction.rb 複素回転・特殊相対性・可積分系エラー修正
lib/bada/tuplespace.rb       Ω::DATABASE（アカシックレコード）
lib/bada/language.rb         Bada 言語（BadaNode + Interpreter）
lib/bada/knowledge.rb        レポート/Web 取り込み → 計測済みコーパス
lib/bada/generator.rb        エントロピー駆動の文章/方程式/理論生成
lib/bada/qa_engine.rb        エントロピー駆動の質問応答
lib/bada/thurston.rb         サーストン・ペレルマン多様体 + シャノンエントロピー配置
lib/bada/catastrophe.rb      トム7カタストロフィ・分岐点情報生成
lib/bada/millennium.rb       クレイ7問のガンマ多様体理論分解
lib/bada/info_engine.rb      情報生成エンジン（上記3つの Facade）
lib/bada/penrose/tensor.rb   テンソル + 一般アインシュタイン縮約 einsum
lib/bada/penrose/palette.rb  ペンローズ絵記号パレット
lib/bada/penrose/diagram.rb  図式モデル + DSL ビルダー
lib/bada/penrose/canvas.rb   絵記号パーサ（描画→図式）+ レンダラ
lib/bada/penrose/evaluator.rb 図式の自動計算（縮約・積分・(反)対称化・微分）
lib/bada/penrose/paper.rb    論文生成（Markdown+LaTeX）
lib/bada/penrose/codegen.rb  ソースコード生成（Ruby）
lib/bada/penrose/studio.rb   Studio（描画→計算→解答→論文→コードの Facade）
lib/bada/quantum/qubit.rb        2量子ビット状態ベクトル・Bell 状態・ゲート
lib/bada/quantum/bell.rb         CHSH 不等式・Tsirelson・不気味な遠隔作用の証明
lib/bada/quantum/quintic.rb      5次方程式 Durand–Kerner 解 + 周期非線形カリア
lib/bada/quantum/jones.rb        Kauffman ブラケット → Jones 多項式相関
lib/bada/quantum/uncertainty.rb  Robertson 不確定性 + Born 確率統計
lib/bada/quantum/semiconductor.rb Fermi–Dirac / バンドギャップ / トンネル
lib/bada/quantum/channel.rb      超密度符号化・反復符号・誤り訂正の通信路
lib/bada/quantum/telegraph.rb    SpaceTelegraph（証明+送信の Facade）
lib/bada/qc/disk_memory.rb   ディスク(HDD)内蔵メモリ：状態ベクトル＋プログラム
lib/bada/qc/logic.rb         CMOS/MOSFET NAND 電子回路シミュレーション＋デコーダ
lib/bada/qc/isa.rb           BadaQASM 命令セット＋ストアドプログラム符号化
lib/bada/qc/cpu.rb           ノイマン型 fetch-decode-execute 制御ユニット
lib/bada/qc/monitor.rb       制御回路のモニタ投射
lib/bada/qc/verilog.rb       半導体（RTL）ソースコード生成
lib/bada/qc/machine.rb       擬似量子計算機 Machine（Facade）
lib/bada/transformer/tensor.rb   純Ruby 行列演算 + 決定的 PRNG
lib/bada/transformer/model.rb    多様体ゲージ・マルチヘッド注意 Encoder
lib/bada/transformer/vision.rb   画像処理トランスフォーマー（ViT）
lib/bada/mind.rb             思考の言語化・心像・脳内コード生成（simulation Facade）
lib/bada/chat.rb             OmegaChat（ChatGPT 分派）

lib/bada/nn/linalg.rb        純Ruby 線形代数（matvec / outer / softmax）
lib/bada/nn/layers.rb        Layer（EmbeddingConcat / Linear / Tanh / ReLU）
lib/bada/nn/sequential.rb    Sequential（Composite）+ CrossEntropy 損失 + Memento
lib/bada/nn/factory.rb       LayerFactory + LanguageModelBuilder
lib/bada/nn/optimizer.rb     SGD / Adam（Strategy）
lib/bada/nn/observer.rb      LossLogger / Checkpointer（Observer）
lib/bada/nn/vocab.rb         Vocab + CorpusAdapter（Adapter）
lib/bada/nn/trainer.rb       Trainer（Template Method）バックプロップ学習
lib/bada/nn/sampler.rb       デコード戦略 + UnknownEngineSampler（Decorator）
lib/bada/nn/generator.rb     NeuralGenerator（自己回帰生成）
lib/bada/nn/pipeline.rb      推論パイプライン（Chain of Responsibility）+ Akashic（Singleton）
lib/bada/nn/chat.rb          NeuralOmegaChat（Facade）
```

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*
