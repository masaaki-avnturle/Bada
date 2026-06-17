# Bada — 実装オーバービュー (bada_ruby / bada_c)

このリポジトリには、山口フレームワーク（TupleSpace / 大域的部分積分多様体理論）に基づく
**Bada 言語と未知（事前）エンジンの2つの実装**が含まれます。レポートの方程式
（ガンマ関数・ベータ・ゼータ・シャノンのエントロピー・大域的部分積分多様体の不変量）を
動くコードに落とし込んでいます。

> このファイルは追加のインデックスです。トップの `README.md` はそのまま残しています。

## `bada_ruby/` — Ruby ホスト実装（フル機能）

純 Ruby（標準ライブラリのみ、Ruby 3.0+）。`cd bada_ruby` 後に各 CLI を実行。

| 層 | 内容 | 主な入口 |
|:--|:--|:--|
| 数学核 | gamma(Lanczos)/beta/zeta ゲージ・**多様体エントロピー不変量 Ξ**・複素回転体の可積分エラー修正 | `Bada::Special` `Bada::Manifold` `Bada::ErrorCorrection` |
| 言語生成 | シャノン駆動の文章/方程式/理論生成・QA | `Bada::Generator` `Bada::QAEngine` |
| ChatGPT 分派 | 計測→検索→生成→誤差修正→記録 | `Bada::OmegaChat` |
| ニューラル LLM | 自作 MLP 言語モデル＋**バックプロップ**（デザインパターン構成） | `Bada::NN`（`bada neural`） |
| 情報生成 | サーストン・ペレルマン多様体／カタストロフィ分岐／ミレニアム7問分解 | `Bada::InfoEngine`（`bada info`） |
| ペンローズ絵記号 | 描画→自動計算（テンソル縮約）→論文/コード生成 | `Bada::Penrose`（`bada penrose`） |
| 未知事前エンジン | 命題を想像し**健全に証明/反証/未解決判定** | `Bada::Prover`（`bada prove`） |
| 大脳基底核 | 体内熱ネットワークの行動選択（Go/NoGo→視床脱抑制） | `Bada::Basal`（`bada basal`） |
| Bada 言語 | 字句/構文解析・インタプリタ・ライブラリ・import | `Bada::Lang`（`bada lang`） |
| 純 Bada 標準ライブラリ | コアアルゴリズムを Bada 言語自身で記述 | `bada/std/*.bada` |

テスト: `ruby -Ilib -e 'Dir["test/test_*.rb"].each{|f| require File.expand_path(f)}'` → **125 件パス**。

## `bada_c/` — C 実装（インタプリタ＋ネイティブコンパイラ）

`bada.c`（純 C + libm）。**cons リスト構造**を中核デザインパターンとし、コード・クラス・
オブジェクト・クラス網をすべてリストで表現。多様体エントロピー不変量を言語の中枢
トリガー（`xi`/`thermal`）として用い、**オブジェクト指向**と**自己進化**、そして
**実行形式ファイルを生成するコンパイラ**を備えます。

```sh
cd bada_c && make
./bada run examples/engine.bada                       # インタプリタ
./bada build examples/engine.bada -o engine && ./engine  # ネイティブ ELF 生成
./bada run examples/evolve.bada                       # 自己進化（Bada が Bada を生成）
make test                                             # ALL PASS
```

## 正直な範囲

- 本物の未解決問題（リーマン予想等）を「解いた」とは主張しません。決定可能なクラス
  （和の帰納法・剰余系の全数検査・有限領域）のみ**健全に証明**し、偽命題は**反例で反証**、
  それ以外は**未解決（経験的証拠のみ）**として明示します。
- C 版の「コンパイル」はソース埋め込み＋ランタイムリンクで、出力は本物のネイティブ
  実行形式です。「自己進化」は有界（Bada が Bada を生成・実行・コンパイルする）。
- 言語ランタイム自体はホスト（Ruby / C）が担います（言語は自分自身だけでは実行不能なため）。

## 開発ブランチ

`claude/bada-ruby-conversion-7DMUQ`
