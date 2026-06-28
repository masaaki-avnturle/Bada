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

## BadaOS-EV — 電気自動車のオペレーティングシステム

`Bada::EVOS` は、**Bada 言語（演算子代数フレームワーク）で電気自動車の OS を元から
構築**したものです（純 Ruby・外部依存なし）。EV の OS は本質的に**ソフトリアルタイム
の制御ループ**であり、優先度／周期スケジューラが毎制御サイクルに全サブシステムを実行
します。Bada フレームワーク自身のプリミティブが中核を担います。

| EV の機能 | 使う Bada プリミティブ |
|:--|:--|
| センサ融合（電流・電圧・温度の外れ値除去） | `Bada::ErrorCorrection`（相対論的コマの可積分系） |
| ブラックボックス（フライトレコーダ） | `Bada::TupleSpace`（Ω::DATABASE / アカシック） |
| 異常検知・状態監視 | `Bada::Manifold` / `Bada::Entropy`（エントロピー不変量 Ξ） |
| 冷却ランプ則 e^{-x log x} | `Bada::BadaNode` の `>-` 量子右作用 |
| 駆動系効率マップ（ネイピア円） | `Bada::Special.x_log_x` |

```bash
bin/bada evos 30                  # BadaOS-EV を起動し走行サイクルを実行
ruby examples/ev_os_demo.rb       # 発進→巡航→回生→急速充電のシナリオ
ruby -Ilib test/test_evos.rb      # EV OS テスト（19 件）
bin/bada run examples/ev_os.bada  # Bada 言語そのものでバッテリ信号を整形
```

```ruby
require "bada"

ev = Bada::EVOS::Vehicle.new(capacity_kwh: 60.0).boot
ev.drive(0.6)          # アクセル（throttle ∈ [-1,1]、負は回生ブレーキ）
ev.run(ticks: 30)      # リアルタイム制御ループを 30 サイクル実行
puts ev.dashboard      # 計器クラスタ（HMI）を描画
ev.plug_in(:dc)        # DC 急速充電（CC/CV）
ev.run(ticks: 40)
puts ev.recorder.tail  # Ω::DATABASE ブラックボックスの読み出し
```

### リアルタイム・カーネルのタスク表（優先度順に毎サイクル実行）

| 優先度 | タスク | 役割 |
|:--|:--|:--|
| 100 | `sensors` | 物理量をサンプリングし **Bada エラー修正**で整形 |
| 90 | `powertrain` | ペダル → 電力、縦方向運動モデルで車速を積分（最高速ガバナー付） |
| 85 | `bms` | クーロンカウント SOC・I²R 自己発熱・**セルバランシング** |
| 80 | `charger` | プラグイン時の CC/CV 充電 |
| 70 | `thermal` | パック／キャビンの熱管理（`>-` で冷却需要を算出） |
| 50 | `diagnostics` | 安全限界 + **Ξ 不変量による情報論的異常検知**。重大故障で走行を停止 |
| 30 | `range` | 消費電力と航続距離の推定 |
| 10 | `recorder` | テレメトリを Ω::DATABASE へ記録 |

### モジュール構成（`Bada::EVOS`）

```
lib/bada/evos/kernel.rb          リアルタイム優先度／周期スケジューラ
lib/bada/evos/sensor.rb          エラー修正付き物理センサ
lib/bada/evos/battery.rb         BMS（SOC・電圧・自己発熱・セルバランシング）
lib/bada/evos/powertrain.rb      モーター／インバータ制御 + 縦方向運動モデル
lib/bada/evos/thermal.rb         バッテリ／キャビン熱管理
lib/bada/evos/charger.rb         CC/CV 充電コントローラ
lib/bada/evos/range_estimator.rb 消費・航続距離推定
lib/bada/evos/diagnostics.rb     故障マネージャ + Ξ 異常検知
lib/bada/evos/recorder.rb        Ω::DATABASE ブラックボックス
lib/bada/evos/dashboard.rb       テキスト HMI（計器クラスタ）
lib/bada/evos/vehicle.rb         車両全体を束ねる Facade
lib/bada/evos.rb                 BadaOS-EV エントリポイント
```

## BadaOS-HEV — ハイブリッド車のオペレーティングシステム

`Bada::HEVOS` は、**Bada 言語でハイブリッド車（シリーズ・パラレル方式）の OS を構築**
したものです。BadaOS-EV のリアルタイムカーネル・エラー修正センサ・バッテリ管理・熱
管理・Ω::DATABASE レコーダを**再利用**し、ハイブリッド特有の中核 — **内燃機関（ICE）**、
**燃料系**、**e-CVT 動力分割**、そして頭脳となる **適応 ECMS エネルギー管理** を加えます。

| HEV の機能 | 使う Bada プリミティブ |
|:--|:--|
| ECMS 等価係数 s の安定化（SOC 帰還の平滑化） | `Bada::ErrorCorrection`（相対論的コマの可積分系） |
| 走行パターン判定（Ξ）と異常検知 | `Bada::Manifold` / `Bada::Entropy`（エントロピー不変量 Ξ） |
| エンジン BSFC（熱効率）マップ | `Bada::Special.x_log_x`（ネイピア円） |
| ブラックボックス（フライトレコーダ） | `Bada::TupleSpace`（Ω::DATABASE / アカシック） |

```bash
bin/bada hev 30                   # BadaOS-HEV を起動し走行サイクルを実行
ruby examples/hev_os_demo.rb      # EV発進→合流ブースト→巡航→回生
ruby -Ilib test/test_hevos.rb     # HEV OS テスト（17 件）
bin/bada run examples/hev_os.bada # Bada 言語そのものでエネルギー配分を記述
```

```ruby
require "bada"

hev = Bada::HEVOS::Vehicle.new(battery_kwh: 1.6, fuel_l: 40.0).boot
hev.drive(0.5)         # アクセル（throttle ∈ [-1,1]、負は回生ブレーキ）
hev.run(ticks: 40)     # ECMS がエンジン／バッテリを毎サイクル裁定
puts hev.dashboard     # 計器クラスタ + エネルギーフロー表示
```

### エネルギー管理戦略（ECMS）— ハイブリッドの頭脳

エネルギーマネージャは毎サイクル、運転者の要求出力を満たす配分のうち、
**等価燃料コスト `J = 燃料パワー + s · バッテリパワー`** を最小化する
エンジン／バッテリ分担を選びます（`s` は電力を等価燃料へ換算する係数）。

| モード | 動作 |
|:--|:--|
| **EV** | 低負荷・SOC 十分 → エンジン停止、モーターのみ |
| **ENGINE** | 巡航 → エンジンが効率の良い動作点で車輪を駆動 |
| **BOOST** | 高負荷 → エンジン + バッテリで加勢 |
| **CHARGE** | SOC 下限 → エンジンが路面負荷より高出力で運転し発電（チャージサステイン、ヒステリシス付） |
| **REGEN** | 制動 → モーター発電でパックへ回収 |

`s` は SOC 帰還で適応し、**Bada エラー修正**で平滑化されるため、エンジンの
ON/OFF がチャタリング（リミットサイクル）しません。直近の要求出力の
**エントロピー不変量 Ξ** を測って走行パターン（穏やか／激しい）を判定し、配分に反映します。

### モジュール構成（`Bada::HEVOS`）

```
lib/bada/hevos/engine.rb            内燃機関（ICE）+ BSFC 熱効率マップ
lib/bada/hevos/fuel.rb              燃料タンク + 燃料流量の積分
lib/bada/hevos/strategy.rb         適応 ECMS エネルギー管理（頭脳）
lib/bada/hevos/hybrid_powertrain.rb エンジン + モーター + e-CVT 動力分割 + 運動モデル
lib/bada/hevos/diagnostics.rb      故障マネージャ（燃料／エンジン／SOC + Ξ 異常）
lib/bada/hevos/dashboard.rb        テキスト HMI（エネルギーフロー表示付）
lib/bada/hevos/vehicle.rb          車両全体を束ねる Facade
lib/bada/hevos.rb                  BadaOS-HEV エントリポイント
（バッテリ管理・熱管理・センサ・カーネル・レコーダは Bada::EVOS を再利用）
```

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
