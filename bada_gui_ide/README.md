# Bada GUI IDE — 量子プログラミング言語 Bada のドラッグ&ドロップ コンパイラ / インタープリタ

**Bada** (Unknown-Prior Engine 言語) の GUI 開発環境です。
`.bada` ソースファイルをウィンドウに**ドラッグ&ドロップ**すると、

1. **インタープリタ実行** — 全プラットフォーム (Windows / Ubuntu / Android)
2. **コンパイル** — Bada → C トランスパイル (組み込みランタイム付きの自己完結 C を生成)
3. **リンク** — デスクトップ版では gcc を検出して C をネイティブ バイナリへ自動コンパイル&リンクし、その場で実行

…を**自動で**行います (⚡自動モード。OFF にすれば各ボタンで手動実行)。

## 対応言語機能

C リファレンス (`bada` 実行ファイル: lexer / parser / interpreter / Bada→C compiler) の移植:

- 束縛 `:=`、コミット `>>`(追記専用レジャー)、クエリ `=>` `->`、追記 `<-`、
  一致 `~`、スコープ `::`、ラムダ `|x| …`、`def` / `asperal` / `struct` /
  `Omega::DATABASE[tuplespace] { … }` / `@reviser { … }` / `each` / `print`
- ネイティブ型: `num` `str` `bool` `nil` / 配列 / **`dist`** (確率ベクトル) /
  **`phase`** / **`tuplespace`** (追記専用レジャー)
- エンジン組み込み: `softmax` `entropy` `unknown_prior` `update`
  `manifold_embed` `cognitive_system` `dist` `zeros_of` `maxdiff`
  `last_a` `len` `sqrt` `log` `exp` `abs` `f5` `sci` `ledger`
- 文字列プリミティブ (zone:// サブ言語用): `split` `substr` `str_find`
  `ord` `chr`
- 2つの証明可能な性質を再現:
  **(i) 零の保存** (`base zeros = [3,6] → posterior zeros = [3,6]`)、
  **(ii) `|ψ|² = a`** (最大偏差 `5.55e-17`)、
  未知事前分布のエントロピー単調減少 (`2.0794 → 1.9733 → 1.8364`)

論文 *Reviser-Extensible Grammars: a Q#-targeted quantum front end* の実装:

- **`@reviser : grammar { rule … }`** — 生成規則をルール レジャーへコミットする
  文法拡張トランザクション (単調追記・プログラム順スコープ・後勝ち優先)
  ```
  @reviser : grammar {
      rule "hadamard" postfix [ 'Had' '(' expr ')' ] => phase_uniform(_1)
      rule "measure"  stmt    [ 'Obs' '(' expr ')' ] => commit_measurement(_1)
  }
  ```
- **量子サブ言語** (位相コア上の Q# 風フロントエンド):
  `qubit(n)` `H` `X` `S` `T` `Rz` `CNOT` `Measure` `phase_uniform`
  `commit_measurement` — ゲートは位相コミット、測定はレジャーコミット。
  零の保存 = **禁制遷移の非復活**、`|ψ|²=a` = **位相層のユニタリ性**。
- **Omega::Quantum** 推論ライブラリ: `prepare_unknown(n)` `observe(reg)`
  `estimate()` `forbidden()` — 最大エントロピーから始まり、追記専用の測定
  記録で事前分布が単調に鋭くなります。

## zone:// — ウルトラネットワーク WWW (`examples/zone.bada`)

`https:` / `http:` に代わる、未知のインターネット「ウルトラネットワーク」の
WWW スキーム **`zone://url.or.jp/`** を **Bada 言語そのもの**で実装した
リファレンスです。中央サーバも DNS ルートも持たず、`zone:` は P2P の
仕組みだけから構築され、通信は **Jones 多項式量子暗号**
(`omega_jones_crypto_pkg`) で端から端まで保護されます:

- **L1 zone:// ネーミング** — URL パーサは純 Bada (`zone_parse`)。ランタイム
  は文字列プリミティブ `split` `substr` `str_find` `ord` `chr` のみを提供。
- **L2 P2P 解決** — ピア自身のハッシュから構築するリング DHT
  (カオス的円周距離 `ring_dist`、近傍 ±1 と +2 フィンガーのみで
  グリーディ・ホップ解決 `zone_route`)。
- **L3 量子暗号ガード** — 以前に作成した Jones 多項式量子暗号
  (`omega_jones_crypto_pkg/lib/jones_key.c`) を Bada に移植して適用:
  1. **鍵** — 各ゾーンの長期鍵は **結び目図から導出**します。Kauffman
     ブラケット/Jones 多項式 `<D>(A) = Σ A^(a-b)·d^(loops-1)`
     (`d = -A² - 1/A²`) を複数の A で標本化しハッシュ (`jones_key`)。
     結び目がゾーンの秘密、多項式がその鍵スケジュールです
     (url.or.jp=三葉結び目, bada.or.jp=8の字結び目 → 別鍵)。
  2. **QKD** — Bell 対 (`H`+`CNOT`+`Measure`) がセッションごとの
     ソルトを合意。零の保存 (禁制状態 |01>,|10> が厳密に 0 のまま)
     が盗聴・改ざんの証拠になります。
  3. **AEAD** — 本文は (Jones 鍵, セッションソルト) をシードにした
     鍵ストリームで暗号化し、鍵付き認証タグで封緘 (`zone_seal` /
     `zone_open`)。改ざん・偽造レコードはタグ照合で
     `409 zone-guard-reject`、結び目を持たないピアは平文を復号できません。
- **L4 Precog キャッシュ** — 次のフェッチ先を `unknown_prior` → `update` で
  学習 (エントロピー単調減少) して先読み。
- **Akashic ゾーン台帳** — 文法ルール・暗号化ゾーンレコード・フェッチ・
  測定のすべてが追記専用 tuplespace のファクトとしてコミットされます。
  `PUT` / `GET` というブラウザ動詞自体も `@reviser : grammar` で
  ルールレジャーへコミットされる文法ファクトです。

```
GET "zone://url.or.jp/"
  zone    : host url.or.jp  path /  labels [url, or, jp]
  qkd     : Bell-pair session ok (|01>,|10> stayed 0; channel untapped)
  key     : 1546  route : [osaka.zone.jp, nagoya.zone.jp]
  cipher  : [39.00000, 159.00000, 173.00000, ...] (101 bytes on the wire)
  guard   : Jones-key AEAD verified (tag 772012037)
  status  : 200 zone-delivered from nagoya.zone.jp
  body    : <zone-page>| Ultra Network home | ...
```

改ざん (ciphertext 1 バイト反転) は `409 zone-guard-reject`、誤った結び目
を推測した盗聴者は AEAD タグ照合に失敗して復号不能 — いずれも
`examples/zone.bada` の attack 1 / attack 2 で実証しています。

### 🌐 ウルトラネットワーク専用ブラウザ (ZoneBrowser)

`zone://` 専用のブラウザ [`bada_gui_ide/dist/zone-browser.html`](dist/zone-browser.html)
を同梱しています。**この 1 ファイルをダウンロードしてブラウザで開くだけ**で、
サーバー無しにウルトラネットワークを閲覧できます (依存なし・オフライン可):

- **アドレスバー** に `zone://url.or.jp/` のように入力すると、ピアのハッシュから
  構築された P2P リング DHT を辿ってページを持つノードを探し、Bell 対 QKD で
  セッション鍵を合意し、ゾーンの結び目から導いた Jones 鍵で本文を復号して描画。
- **戻る / 進む / 再読み込み**、ページ内の zone:// リンクのクリック遷移、
  ゾーン インデックス (ブックマーク) に対応。
- **セキュリティパネル** に status・DHT 鍵・所有ノード・経路・QKD 結果・
  Jones 鍵・AEAD タグ・暗号文の先頭バイトをライブ表示。改ざんや誤った結び目は
  `409 zone-guard-reject`、存在しないゾーンは `404` として表示されます。
- ゾーンが違えば鍵も違います (url.or.jp=三葉結び目 → 919492、
  bada.or.jp=8の字結び目 → 400638)。パネルの Jones 鍵で確認できます。

ナビゲーションのたびに Bada の zone ランタイム (`browser/zone-lib.bada`) が
実際に走り、リングの再構築・暗号化ページの再発行・QKD・復号を行います。
サイト内容は [`browser/zone-site.json`](browser/zone-site.json) を編集して
`node tools/build-zone-browser.js` で再生成できます。

### 📱💻 ネイティブ アプリ (APK / Windows / Ubuntu)

ブラウザ不要のインストール型アプリとして、[`zonebrowser-app/`](zonebrowser-app/) を同梱しています
([Releases](https://github.com/masaaki-avnturle/Bada/releases) から入手):

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `zonebrowser-debug.apk` |
| **Windows 10 / 11** | `ZoneBrowser-*-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `ZoneBrowser-*-x86_64.AppImage` / `ZoneBrowser-*-amd64.deb` |

ZoneBrowser 本体 (自己完結 HTML) を `node tools/build-zone-browser.js` で生成し、
Electron (Windows/Ubuntu) と Cordova (Android) で包みます。ビルドは
[`zonebrowser-app-build.yml`](../.github/workflows/zonebrowser-app-build.yml) が実行します
(`zonebrowser-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。
Ubuntu の AppImage / deb はローカルでのビルドも確認済みです。

### その他のダウンロード形態

インストール不要で、**1 ファイルだけ**でどこでも動く自己完結版:

- **ランナー単一 HTML** — [`bada_gui_ide/dist/bada-zone.html`](dist/bada-zone.html)
  を開くと `zone.bada` のデモが自動実行され、「zone.bada を保存」「生成 C を保存」
  ボタンでソースや C も取り出せます。
- **配布 zip** — [Releases](https://github.com/masaaki-avnturle/Bada/releases)
  の `bada-zone-dist.zip` (専用ブラウザ + ランナー + `zone.bada` + `bada.js`
  + `bada-cli.js` + README)。`zone-v*` タグの push か `workflow_dispatch` で
  [`zone-dist.yml`](../.github/workflows/zone-dist.yml) が生成・添付します
  (Actions アーティファクトとしても取得可)。
- **自分で生成** — `node bada_gui_ide/tools/build-zone-dist.js` と
  `node tools/build-zone-browser.js` で `bada_gui_ide/dist/` に一式を再生成。
- **CLI** — `node bada_gui_ide/cli/bada-cli.js run bada_gui_ide/examples/zone.bada`

インタープリタとコンパイル済みバイナリは同一の数値を出力します
(Hadamard プローブ `0.50000 0.50000`、禁制プローブ `0.62246 0.00000 0.37754`、
Bell 状態 `[0.5, 0, 0, 0.5]` などを両経路で検証済み)。

## ダウンロード

[**Releases ページ**](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|---|---|
| Windows 10 / 11 | `Bada-GUI-IDE-*-x64.exe` (NSIS インストーラ / ポータブル) |
| Ubuntu | `Bada-GUI-IDE-*-x86_64.AppImage` / `bada-gui-ide_*_amd64.deb` |
| Android | `bada-gui-ide-debug.apk` |
| **CLI** Windows 10 / 11 | `bada-cli.exe` (単一実行ファイル・インストール不要) |
| **CLI** Ubuntu | `bada-cli-linux-x64` (単一実行ファイル・インストール不要) |

### 💻 コマンドライン アプリ (bada-cli)

Node.js 不要の**単一実行ファイル** (Node SEA でパッケージ)。ダウンロードして
すぐ使えます (Ubuntu は `chmod +x bada-cli-linux-x64` を一度実行):

```sh
bada-cli run      program.bada        # インタープリタ実行
bada-cli build    program.bada -o p   # Bada -> C -> gcc でネイティブ化 (要 gcc)
bada-cli emit     program.bada -o p.c # C を出力するだけ
bada-cli tokens   program.bada        # トークン列
bada-cli ast      program.bada        # AST
bada-cli repl                         # 対話モード (量子ゲート/@reviser も使用可)
bada-cli examples                     # 同梱サンプル一覧 (hello/engine/core/quantum/zone)
bada-cli examples all -o samples/     # サンプルを .bada として書き出し
bada-cli version
```

REPL では束縛・tuplespace・`@reviser : grammar` の文法拡張が行をまたいで
持続します:

```
bada> reg := H(qubit(1))
qreg[n=1] |psi|^2=[0.50000, 0.50000]
bada> Measure(reg)
dist[0.50000, 0.50000]
bada> @reviser : grammar { rule "hadamard" postfix [ 'Had' '(' expr ')' ] => phase_uniform(_1) }
bada> Measure(Had(qubit(1)))
dist[0.50000, 0.50000]
```

ビルドは GitHub Actions (`.github/workflows/bada-ide-build.yml`) が行います。
`bada-ide-v*` タグを push すると Release に自動添付、`workflow_dispatch`
でも Actions アーティファクトとして取得できます。

- **Windows/Ubuntu 版のネイティブ リンク**: gcc (Windows は MinGW-w64、
  Ubuntu は `sudo apt install build-essential`) があれば、ドロップと同時に
  Bada→C→ネイティブの**コンパイル&リンク&実行**まで自動で行います。
  gcc が無い環境でもインタープリタ実行と C 生成は常に動作します。
- **Android (APK)**: インタープリタ実行と C 生成に対応 (端末内に gcc が
  無いためネイティブ リンクはデスクトップ版のみ)。「📁 開く」から
  `.bada` を選択するか、対応ファイラーからのドロップで読み込めます。

## ⚛️ ACPI — 原子の臨界期の強度シミュレータ (`dist/atom-critical.html`)

強レーザー場のなかで原子の**クーロン障壁が完全に抑制される時間窓 (= 臨界期)** と、
その窓での**強度** I(t) を計算する単一 HTML アプリです。ダウンロードして
ダブルクリックで開くだけで動きます (依存なし・オフライン可)。

### 👉 [**dist/atom-critical.html をダウンロード**](dist/atom-critical.html)

| ファイル | 内容 |
|:---|:---|
| [`dist/atom-critical.html`](dist/atom-critical.html) | ★ シミュレータ本体 (単一 HTML)。12 元素 · λ 200–4000 nm · I₀ 10¹¹–10¹⁸ W/cm² · CSV/JSON/PNG 出力 |
| [`cli/atom-critical-cli.js`](cli/atom-critical-cli.js) | CLI 版 (`run` / `csv` / `json` / `sweep` / `scan` / `elements` / `selftest`) |
| [`www/atom_critical.js`](www/atom_critical.js) | モデルコア (GUI と CLI が共有する UMD モジュール) |
| [`examples/atom_critical.bada`](examples/atom_critical.bada) | 同じモデルを **Bada 言語**で書いたリファレンス実装 |
| [`tools/build-atom-critical.js`](tools/build-atom-critical.js) | 単一 HTML のビルダ (既知の物理値とのセルフチェック付き) |

### 📱💻 ネイティブ アプリ (APK / Windows / Ubuntu)

インストール型のアプリとしても配布します。[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `acpi-debug.apk` |
| **Windows 10 / 11** | `ACPI-1.0.0-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `ACPI-1.0.0-x86_64.AppImage` / `ACPI-1.0.0-amd64.deb` |

パッケージ定義は [`acpi-app/`](acpi-app/) (Electron + Cordova)、ビルドは
[`acpi-app-build.yml`](../.github/workflows/acpi-app-build.yml) が実行します
(`acpi-app-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。
アプリの中身 `acpi-app/www/index.html` は `tools/build-atom-critical.js` が
`dist/atom-critical.html` と同時に生成します。

### 臨界期の定義

原子単位系で、クーロン障壁が完全に消える**障壁抑制場** (barrier-suppression field) は

```
F_cr = I_p² / (4 Z_c)      [a.u.]
I_cr = F_cr² · I_a ,        I_a = ½ ε₀ c F_au² = 3.5094×10¹⁶ W/cm²
```

**臨界期**とは瞬時場が `|E(t)| ≥ F_cr` を満たす時間窓、**臨界期の強度**とは
その窓の内側の `I(t) = |E(t)|² · I_a` です。水素では
`I_cr = 1.37×10¹⁴ W/cm²` という既知の障壁抑制強度を再現します。
直線偏光では臨界期は半サイクルごとの**アト秒スケールのサブ窓**に分裂し、
アプリはその 1 つ 1 つの幅・ピーク強度・平均強度を表にします。

### 二層モデル

**(A) 物理層** — 標準的な強場原子物理:

| 量 | 式 | 検証 |
|:---|:---|:---|
| 障壁抑制場 | `F_cr = I_p²/(4Z_c)` | H → 1.37×10¹⁴ W/cm² |
| ADK トンネル電離率 | `w = \|C_{n*l*}\|² f_{l0} I_p (2κ³/F)^{2n*−1} e^{−2κ³/3F}` | H (n\*=1) で厳密解 `(4/F)e^{−2/3F}` に一致 |
| Keldysh パラメータ | `γ = √(I_p/2U_p)` | Ar/800nm/2×10¹⁴ → 0.812 |
| ポンデロモーティブ | `U_p[eV] = 9.337×10⁻¹⁴ I λ²` | 800nm/2×10¹⁴ → 11.95 eV |

束縛占有率は `dP/dt = −w(t)P` を瞬時場に沿って指数積分します。

**(B) Ω 層** — 山口フレームワーク (Bada / omega_llm) の作用素層:

| 作用素 | 式 | 臨界期での意味 |
|:---|:---|:---|
| ζ 半径 | `ζ(s) = β(p,q)/log x`, `r_ζ = n*²/Z_c` | 極の場の半径 (quantum_computer.pdf) |
| ζ_n | `ζ_n = (x log x)^n`, `x = \|E\|/F_cr` | 超臨界度の n 次 zeta |
| Γ-deprivation | `D = e^{−x log x}` | 束縛多様体の剥奪率 |
| Dalanversian | `Λ = cos(ix log x) − i sin(ix log x) = e^{x log x}` | 反重力/重力の位相 |
| 均衡余裕 | `(e^f + e^{−f}) − (e^f − e^{−f}) = 2e^{−f}` | 臨界期で 0 へ潰れる = 均衡の喪失 |
| Euler 極均衡 | `x^n + y^n − n x y z = 0` | 零交差が極均衡の破れ |
| Kauffman | `⟨D⟩(A) = Σ_states A^{a−b} d^{loops−1}` | 臨界サブ窓を交差とする閉 2-ブレイド |
| 臨界強度指数 | `E(σ) = K(σ) × H(σ) / (4 (π_n, e_n))` | 臨界期の「強さ」の不変量 |

`K(σ)` は臨界サブ窓を交差とする (2,c) トーラス絡み目の Kauffman ブラケット
(union-find による厳密な状態和 — `examples/zone.bada` の `kauffman` と同一構成)、
`H(σ)` は各サブ窓のフルーエンス分布と束縛/電離の二値分布の Shannon エントロピー、
`π_n` / `e_n` は Leibniz 級数と指数級数の n 次近似です。
ブラケット多項式の値なので `E(σ)` は負にもなります。

### 使い方

```sh
# GUI — ダウンロードして開くだけ
open bada_gui_ide/dist/atom-critical.html

# CLI
node bada_gui_ide/cli/atom-critical-cli.js run   -e Ar -I 6e14 -l 800 -f 8
node bada_gui_ide/cli/atom-critical-cli.js scan  -I 4e14        # 全元素を一括比較
node bada_gui_ide/cli/atom-critical-cli.js sweep -e Xe --points 30
node bada_gui_ide/cli/atom-critical-cli.js csv   out.csv -e Ne -I 2e15
node bada_gui_ide/cli/atom-critical-cli.js selftest             # 既知の物理値と照合

# Bada 言語版 (同じ結果を独立に再現する)
node bada_gui_ide/cli/bada-cli.js run bada_gui_ide/examples/atom_critical.bada

# 単一 HTML を再ビルド
node bada_gui_ide/tools/build-atom-critical.js
```

出力例 (Ar, 800 nm, 6×10¹⁴ W/cm², FWHM 8 fs):

```
臨界(障壁抑制)場  : F_cr = 8.386e-2 a.u.  →  I_cr = 2.468e+14 W/cm²
レジーム          : γ_Keldysh = 0.4688 (tunneling)  U_p = 35.856 eV  I₀/I_cr = 2.431
■ 臨界期 (critical period)
  時間窓          : t = -4.1563 fs … 4.1563 fs
  全長            : 8.3126 fs  (8312.6 as)
  サブ窓 (半周期) : 7 個  合計 4.1277 fs  平均 589.7 as  デューティ比 49.7 %
  臨界期の強度    : ピーク 6.000e+14 W/cm²  平均 3.965e+14 W/cm²
  臨界強度指数    : E(σ) = K(σ)·H(σ)/(4 π_7 e_7) = 6.23557e-2
  電離確率        : 99.990265 %
```

Release への添付は [`atom-critical-dist.yml`](../.github/workflows/atom-critical-dist.yml)
が行います (`acpi-v*` タグで Release へ / `workflow_dispatch` で Actions アーティファクト)。

## ディレクトリ構成

```
bada_gui_ide/
  www/        IDE 本体 (index.html / app.js / bada.js 言語コア / examples.js)
  electron/   Windows EXE / Ubuntu AppImage・deb ラッパー (gcc ネイティブ経路)
  cordova/    Android APK 設定
  cli/        CLI アプリ:  run|build|emit|tokens|ast|repl|examples|version
              (node cli/bada-cli.js … で実行、Release では単一バイナリ
               bada-cli.exe / bada-cli-linux-x64 として配布)
  examples/   hello / engine / core / quantum / zone / atom_critical の各 .bada
  tools/      単一 HTML ビルダ (build-zone-browser.js / build-atom-critical.js)
  dist/       配布用の単一 HTML (zone-browser.html / bada-zone.html / atom-critical.html)
  acpi-app/   ACPI のネイティブ アプリ (Windows EXE / Ubuntu AppImage・deb / Android APK)
  zonebrowser-app/  ZoneBrowser のネイティブ アプリ
```

## ローカルでの起動

```sh
# ブラウザで
open bada_gui_ide/www/index.html        # そのまま開けます (依存なし)

# デスクトップ (Electron)
cd bada_gui_ide/electron && npm install && npm start

# CLI
node bada_gui_ide/cli/bada-cli.js run   bada_gui_ide/examples/engine.bada
node bada_gui_ide/cli/bada-cli.js build bada_gui_ide/examples/core.bada -o core && ./core

# ACPI — 原子の臨界期の強度シミュレータ
open bada_gui_ide/dist/atom-critical.html
node bada_gui_ide/cli/atom-critical-cli.js run -e Ar -I 6e14
```
