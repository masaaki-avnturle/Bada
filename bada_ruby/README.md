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
lib/bada/chat.rb             OmegaChat（ChatGPT 分派）
```

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*
