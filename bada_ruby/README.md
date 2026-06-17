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

## 未知事前エンジン — 数学の未解決問題を想像して証明する

`Bada::Prover`（未知事前エンジン / Unknown A-priori Engine）は、多様体・エントロピー
機構を種にして**未解決風の数学命題を「想像」し、健全な自動推論で判定**します。

```bash
bin/bada prove "大域的部分積分多様体の未解決問題を想像して証明して"
```

```ruby
puts Bada::Prover::Engine.new.render("ガンマ関数の未解決問題を想像して証明")
# OmegaChat からも: Bada::OmegaChat.new.discover("未解決問題を想像して")
```

### 健全性の契約（重要）

このエンジンは**証明できるものだけを「証明完了」と判定**し、誇張しません。

| 判定 | 意味 | 手法 |
|:--|:--|:--|
| **∎ 証明完了** | 完全・検証可能な方法で確立 | 多項式和の閉形式＋**数学的帰納法**、剰余系の**全数検査**、有限領域の全数検査 |
| **✗ 反証** | 具体的な**反例**を発見（健全） | 反例の明示 |
| **? 未解決** | 我々の手法では決定不能 | **経験的証拠のみ**（証明とは主張しない） |

実例（自動生成・自動判定）:
- `Σ_{k=1}^n (2k+2) = n²+3n` を帰納法で**証明**（閉形式を有限差分で構成し基底・段階を検証）。
- `7 | n⁷ − n`（フェルマーの小定理型）を**剰余系の全数検査で証明**。
- 誤った恒等式・整除性は**反例つきで反証**（例 `5 | n²−n` は n=2 で反例）。
- コラッツ／ゴールドバッハ型は**未解決**として範囲内の証拠のみ提示（証明ではないと明示）。

各命題は `engine.paper(conjecture)` で証明論文（Markdown+LaTeX）にもなります。

## 大脳基底核の熱ネットワーク — 体内神経システム（行動選択）

`Bada::Basal` は、**大脳基底核（basal ganglia）を体内の熱ネットワークとして模擬した
体内神経システム**を、**小型・モジュール化された小規模クラス**で実装します。各神経核は
ニューロン層と**同型**（重み付き和＋整流＝ニューロン）で、古典的**デザインパターン**で
配線され、横方向の熱伝導度は**ガンマ関数の大域的部分積分多様体** `1/(x·log x)²` から
与えられます。これが LLM デコーダと未知事前エンジン（命題エンジン）の**行動選択器**です。

```bash
bin/bada basal "大脳基底核の熱ネットワークで未解決問題を想像して証明する"
ruby examples/basal_demo.rb
```

### 神経核 = 小型クラス（ニューラルネットと同型）

| 神経核（クラス） | 役割 | 経路 |
|:--|:--|:--|
| `Cortex` | 候補（行動/トークン）の顕著性入力 | 入力 |
| `StriatumD1` | 直接路 / Go（ドーパミンで促進） | direct |
| `StriatumD2` | 間接路 / NoGo（ドーパミンで抑制） | indirect |
| `STN` | ハイパー直接路（広域 NoGo） | hyperdirect |
| `GPe` / `GPi` | 淡蒼球（GPi は出力、緊張性抑制） | 出力 |
| `Thalamus` | 選択的脱抑制でゲート＝行動選択 | 出力ゲート |

GPi の緊張性抑制を Go 路が下げて視床を**脱抑制**＝最も顕著なチャネルが選択されます。

### 採用デザインパターン

| パターン | 適用箇所 |
|:--|:--|
| **Strategy** | `Nucleus#activate`、ゲーティング（Argmax/Boltzmann） |
| **Composite** | `BasalGanglia`（神経核の小ネットワーク） |
| **Mediator** | `BasalGanglia` が核間の信号伝達を仲介 |
| **Observer** | `Dopamine`(SNc) が報酬予測誤差 RPE を線条体へ配信し学習 |
| **Factory** | `CircuitFactory`（配線済み回路を生成） |
| **Facade** | `BodyNeuralSystem` / `AprioriEngine` |

### 熱ネットワーク（体内）

`ThermalField` が顕著性をチャネル間で**熱拡散**（多様体伝導度で横方向相互作用、熱量保存）
し、**焼きなまし温度** `T(step)=T₀/log(step+e)` で冷却しながら Boltzmann ゲートで選択
します。ドーパミン（SNc）が RPE を配信して線条体の Go/NoGo 重みを学習させます。

### LLM・未知事前エンジンとの統合

- `Bada::Basal::BasalGangliaSampler` … LLM のロジットを大脳基底核に通し、上位 k トークンを
  皮質チャネルとして Go/NoGo＋熱焼きなましで選択する **Bada::NN デコーダ Strategy**。
- `Bada::Basal::AprioriEngine` … 未知事前エンジンが命題を「想像」→ 大脳基底核が**取り組む
  順序を顕著性で選択**→ 健全に証明→ 結果でドーパミン学習。`OmegaChat#deliberate` から利用可。

## 純 Bada 実装 — コアアルゴリズムを Bada 言語自身で記述

`bada/std/*.bada` は、アプリの**中核アルゴリズムを（薄いラッパではなく）Bada 言語自身で
実装**したものです。算術プリミティブ（`exp/sin/log/...`）だけをネイティブに借り、残りは
すべて Bada のループ・関数・リストで書いています。

```bash
bin/bada lang bada/app/native_engine.bada   # 純 Bada のエンジンを実行
```

| Bada ライブラリ | 実装内容（Bada 言語） |
|:--|:--|
| `std/special.bada` | **ガンマ関数（Lanczos 近似）**・ベータ・ζ ゲージ |
| `std/entropy.bada` | シャノンのエントロピー H = -Σ p log₂ p |
| `std/manifold.bada` | 多様体線素 `1/(x log x)²`・∬・**エントロピー不変量 Ξ** |
| `std/catastrophe.bada` | **三次方程式の実根（Cardano/三角法）**・カスプ判別式 |
| `std/polynomial.bada` | 多項式（係数リスト）の整数評価 |
| `std/prover.bada` | **未知事前エンジンの健全な証明**（剰余系の全数検査で `m\|E(n)`） |
| `std/basal.bada` | **大脳基底核の行動選択**（Go/NoGo→GPi→視床の脱抑制） |

検証済み（テスト）: `Γ(5)=24`、`β(2,3)=1/12`、`x³−3x` の実根 `±√3,0`、フェルマーの
小定理 `7|n⁷−n` を Bada で証明、`5|n²−n` を n=2 で反証、基底核が最強チャネルを選択。

> 注: Bada の**ランタイム**（字句/構文解析・インタプリタ）は Ruby のままです。言語は
> 自分自身を解釈できない（ネイティブ実行系が必要）ため、ここは原理的に Ruby が担います。
> その上で、**アプリのアルゴリズムは Bada 言語で記述**しています。

## 指示指向オブジェクト — `<-` 代入 / `-<` 分岐 / `>-` 合流

Bada 言語の3つの演算子を、**指示指向オブジェクト（directive-oriented objects）**の
中核プリミティブとして再定義しました。指示オブジェクトは複数の「レーン（分岐）」を運ぶ
データフローで、3演算子だけでフローを記述します。

| 演算子 | オブジェクト | 意味 |
|:--|:--|:--|
| `<-` | **代入オブジェクト** | 値を指示オブジェクトに代入（ロード） |
| `-<` | **分岐オブジェクト** | 各レーンを分岐ディレクティブでファンアウト |
| `>-` | **合流オブジェクト** | レーンを1つに合流（マージ／リデュース） |

```bash
bin/bada directive    # デモ実行
```

```
let flow = 0 <- 7                                      # 代入 → <| 7 |>
let p = flow -< [def(x) return x end,
                 def(x) return x * x end,
                 def(x) return x * x * x end]          # 分岐 → <| 7, 49, 343 |>
print p >- def(a, b) return a + b end                  # 合流(和) → 399

# 連鎖（代入→分岐→合流のパイプライン）
print (0 <- 5) -< [def(x) return x+1 end,
                   def(x) return x+2 end,
                   def(x) return x+3 end] >- def(a,b) return a+b end   # 21
```

分岐ディレクティブ `-<` の右辺:
- 関数 → 各レーンを写像
- 関数のリスト → 各レーンを全関数にファンアウト（レーンが増える）
- 値のリスト → レーンを明示的に置換
- 数 `n` → 各レーンを n 複製

合流 `>-` の右辺は2引数のマージ関数（`reduce`）。匿名関数 `def(x) ... end` が値として使えます。
（従来の多様体演算子の数学は `left_act/right_act/manifold_integral` 関数として残置。）

## リバイザーによる言語分岐システム — Bada の亜種を派生

`Bada::Lang::Reviser` は、ベースの Bada 言語を**改訂（revise）して亜種（variant/方言）を
派生**し、親→子の**系譜（branch tree）**を成す「言語分岐システム」です。各亜種は実際に
動く独立した言語で、**キーワード別名・改名（日本語キーワード可）・組込みの追加/上書き・
プレリュード**を持ち、自身のスペックの**多様体エントロピー不変量 Ξ**を分岐の同一性
トリガーとして帯びます。

```bash
bin/bada dialects     # 亜種を派生して実行し、分岐系譜を表示
```

```ruby
# 日本語キーワードの亜種を派生
ja = Bada::Lang.fork(name: "bada-ja") do
  rename :def, "関数"
  rename :end, "終"
  rename :print, "表示"
  rename :return, "返す"
  builtin("二乗") { |x| x * x }
end

Bada::Lang.run(<<~BADA, dialect: ja)
  関数 sq(x)
    返す 二乗(x)
  終
  表示 str(sq(9))     # => 81
BADA

# さらに分岐（子の亜種は親の改訂を継承）
ja2 = Bada::Lang.fork(name: "bada-ja-π", parent: ja) do
  builtin("円周率") { Math::PI }
  note "adds 円周率"
end

puts Bada::Lang::Dialect.base.render_tree   # 分岐系譜（各枝に Ξ）
ja2.lineage.map(&:name)                       # ["bada","bada-ja","bada-ja-π"]
ja2.diff_from_parent                          # 親との差分（この枝の改訂のみ）
```

改訂操作（`Reviser.fork { ... }` の DSL）:

| 操作 | 意味 |
|:--|:--|
| `rename :def, "関数"` | 役割の表層語を改名（旧語は無効化） |
| `keyword "func", :def` | 表層語の**別名**を追加（旧語も有効） |
| `builtin("二乗") { ... }` | 組込み関数を追加/上書き |
| `prelude "..."` | その亜種の構文で先に走るプレリュード |
| `note "..."` | 系譜に改訂メモを記録 |

ベース言語と他の亜種は互いに影響しません（各 `Dialect` はキーワード写像・組込み・
プレリュードを独立に保持）。系譜は `lineage`/`descendants`/`render_tree`/`diff_from_parent`
で参照できます。

## Bada 言語そのもの — ライブラリもアプリも Bada で記述

これまでの機能は Ruby で実装した「エンジン（カーネル）」です。`Bada::Lang` はその上に
**Bada 言語（字句解析→Pratt 構文解析→木構造インタプリタ）**を載せ、**必要なライブラリも
アプリ本体も Bada 言語自身で記述**できるようにします。Bada 言語は関数・ライブラリ
（モジュール）・`import`・ネイティブ橋渡し（カーネル）を備えます。

```bash
bin/bada lang bada/app/unknown_engine.bada   # Bada 言語で書いたアプリを実行
bin/bada lang                                # 既定アプリを実行
```

### Bada 言語の構文

```
import "lib/manifold.bada"

library Mani
  def xi(q)
    return Manifold.xi(q)      # ネイティブ橋渡し（カーネル）
  end
  def quantum(q)
    let x = Manifold.xi(q)
    return x >- x              # Bada 演算子（量子右作用）
  end
end

def fib(n)
  if n < 2
    return n
  end
  return fib(n - 1) + fib(n - 2)
end

print "Xi = " + str(Mani.xi("..."))
```

- 値: 数値・文字列・真偽・`nil`・リスト `[...]`
- 演算: `+ - * /`、比較 `== != < <= > >=`、`and/or/not`、**Bada 演算子 `<- -< >-`**
- 文: `let`/代入・`def`/`return`・`library/end`・`if/elsif/else/end`・`while/end`・`print`・`import`
- `Mod.fn(args)`: ユーザーライブラリ／ネイティブモジュール（`Manifold`/`Entropy`/`Special`/
  `Info`/`Prover`/`Basal`/`Penrose`）を呼ぶ

### Bada 言語で書いたライブラリとアプリ（`bada/` ディレクトリ）

```
bada/lib/core.bada       基盤ヘルパ（整形・最大値）
bada/lib/manifold.bada   大域的部分積分多様体ライブラリ（H/Ξ/M/ζ ゲージ）
bada/lib/engines.bada    情報生成・証明・大脳基底核・ペンローズを束ねる
bada/app/unknown_engine.bada  未知事前エンジン アプリ本体（Bada 言語）
```

アプリは Bada 言語で書かれ、Bada 言語のライブラリを `import` し、ネイティブカーネル経由で
各エンジンを駆動します（計測→情報生成→健全な証明→大脳基底核ゲーティング→ペンローズ計算）。

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
lib/bada/prover/polynomial.rb  厳密な有理数係数多項式（健全な証明の基盤）
lib/bada/prover/proof.rb       証明器（恒等式/整除性/有限/経験的）と Proof
lib/bada/prover/conjecture.rb  命題の「想像」生成 + 数論ユーティリティ
lib/bada/prover/engine.rb      未知事前エンジン（imagine→prove→render/paper）
lib/bada/basal/nucleus.rb      神経核の小型クラス（Cortex/Striatum/STN/GPe/GPi/Thalamus）
lib/bada/basal/synapse.rb      シナプス + ガンマ多様体由来の熱伝導度
lib/bada/basal/thermal.rb      熱拡散場 + 焼きなまし温度 + ゲート戦略
lib/bada/basal/dopamine.rb     ドーパミン（SNc, Observer）+ 可塑性
lib/bada/basal/circuit.rb      BasalGanglia（Mediator+Composite）行動選択
lib/bada/basal/factory.rb      CircuitFactory（回路生成）
lib/bada/basal/sampler.rb      BasalGangliaSampler（NN デコーダ）
lib/bada/basal/engine.rb       BodyNeuralSystem / AprioriEngine（Facade）
lib/bada/lang/lexer.rb       Bada 言語 字句解析
lib/bada/lang/parser.rb      Bada 言語 構文解析（Pratt）+ AST
lib/bada/lang/interpreter.rb Bada 言語 インタプリタ（関数/モジュール/演算子）
lib/bada/lang/kernel.rb      ネイティブ橋渡し（エンジンを Bada へ公開）
lib/bada/lang/dialect.rb     言語の亜種（キーワード写像/組込み/系譜/Ξ）
lib/bada/lang/reviser.rb     リバイザー（亜種を派生する分岐システム + DSL）
lib/bada/lang.rb             Bada 言語 Facade（run/run_file/import/fork）
bada/lib/*.bada · bada/app/*.bada  Bada 言語で書いたライブラリとアプリ
bada/std/*.bada              純 Bada 実装の標準ライブラリ（特殊関数〜証明〜基底核）
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
