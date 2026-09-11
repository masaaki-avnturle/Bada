# ⟨ζ⟩ ゼータ・ポート — 異次元ポート開閉時刻表シミュレータ

**Bada 量子プログラミング言語**で書かれた、**visto.pdf**(Masaaki Yamaguchi
「M theory in monopolity of extra dimension Symmetry theory」)を中心文献とする
シミュレーションアプリケーション。**ゼータ関数の関係式(関数等式)の方程式の形を
エントロピー値として求め**、宇宙の**異次元へのポートが開閉する時刻表と住所**を
計算します。依存ゼロ・単一 HTML・オフライン動作。

## 👉 使い方

1. [`index.html`](index.html) を開き **「Download raw file」(⬇ アイコン)** で保存
2. ダブルクリックで起動(インストール不要・ネット接続不要)
3. 基準日時・ゼータ時間範囲・時間スケールを選んで **「▶ Bada でシミュレーション実行」**

CLI でも実行できます:

```sh
node bada_gui_ide/cli/bada-cli.js run bada_gui_ide/examples/zeta_port.bada
# または
node bada_gui_ide/cli/bada-cli.js examples zeta_port
```

GUI IDE(`bada_gui_ide/www/index.html`)のサンプル選択にも
**zeta_port.bada** として同梱されています。

## 模型 — visto.pdf の式がそのまま計算になる

中心文献 visto.pdf の宣言:

| visto.pdf | 本アプリでの実装 |
|:---|:---|
| 「シャノンの公式は、ゼータ関数である」 ∫ x log x = ζ(s) | 関係式の形のエントロピー S(t) = −Σ pₙ log pₙ(Bada 組み込み `entropy()`) |
| 「ゼータ関数は、重力場と反重力場の積」 ζ(s) = □·□⁻ = 1 | Z(t) の Dirichlet 項の正負分解 K − H = Z。零点で K = H、□·□⁻ = 1 が**厳密に**成立 |
| 「統一場理論はモノポールの磁気単極子」 E(σ) = K(σ) ⊗ H(σ) | K = 重力モノポール、H = 反重力モノポール。両者の釣り合いの瞬間 = ポートゲート |
| ∫∫ e^(−x²−y²) dxdy = π, πe ≅ eπ | ポート住所の K セクタ(π)・H セクタ(e)・ゾーンリング(2π, RING=4096) |
| rtl.pdf「Dimensions from D-brane is global cut manifold」 | 次元梯子 D5…D11(M 理論の余剰次元)を巡回してポート住所の次元を決定 |

**ゼータ関数の関係式** ζ(s) = χ(s)·ζ(1−s), χ(s) = 2^s π^(s−1) sin(πs/2) Γ(1−s) は
臨界線 s = ½+it を自分自身へ折り返します。この対称性が Riemann–Siegel の実関数

```
Z(t) = e^{iθ(t)} ζ(½ + it)      θ(t) = Riemann–Siegel theta
```

を実数にします — つまり **Z(t) が「関係式の方程式の形」そのもの**です。
Bada プログラムは純 Bada 実装(sin/cos は Taylor 展開、θ(t) と Z(t) の
Riemann–Siegel 公式、C0 剰余項込み)で Z(t) の符号変化を走査・二分法で精密化し、
各**非自明零点**(14.1347…, 21.0220…, 25.0109… — すべて実在の数学)を
**ポートゲートイベント**として検出します:

- 奇数番目の零点 → ポート **開**、偶数番目 → **閉**(□ / □⁻ 優勢の反転)
- 各イベントの**エントロピー値** S(t)、□·□⁻ バランス(零点で 1.00000)
- **時刻表**: 基準日時 + (t − t₀) × 実時間スケールで実時刻に写像
- **住所**: `port://D次元/Kセクタ.Hセクタ/zone-リング` + 天球座標(RA/DEC)

さらに Bell 対(H + CNOT + Measure)の**量子封緘**で時刻表台帳の改ざん検知
(zero-preservation)、`unknown_prior` → `update` の**ポート予報**
(Jaynes: エントロピー単調減少)、`@reviser : grammar` による **GATE 動詞**の
文法追加と、Bada エンジンの機構をフル活用しています。すべてのイベントは
追記専用 tuplespace 台帳にコミットされます。

## 出力例

```
  #   zeta time    clock         state   S(entropy)  □·□⁻    address
  01  t=14.13720   09:04:08   OPEN    S=1.88594  1.00000  port://D6/K500.H200/zone-1024
      RA 14h08m13s  DEC +0.00167
  02  t=21.02438   09:11:01   CLOSE   S=1.80452  1.00000  port://D7/K692.H734/zone-1417
      -- port stood open 6.88718 zeta units = 413s
```

## ファイル

| ファイル | 内容 |
|:---|:---|
| [`index.html`](index.html) | ★ 単一 HTML アプリ本体(Bada 言語コア + zeta_port.bada を内蔵) |
| [`build.js`](build.js) | `node zeta_port/build.js` で index.html を再生成(実行検証つき) |
| [`../bada_gui_ide/examples/zeta_port.bada`](../bada_gui_ide/examples/zeta_port.bada) | 中心プログラム(数学はすべてここ) |

※ 本アプリは Yamaguchi 理論草稿の数理アート・シミュレーションです。
ゼータ零点は実在の数学、ポートは理論上の解釈です。
