<!--
  masaaki-avnturle / Bada — README.md
  Live: https://masaaki-avnturle.github.io/Bada/
  Cross-link: https://masaaki-avnturle.github.io/tuplenetwork/
-->

<div align="center">
<img src="https://masaaki-avnturle.github.io/tuplenetwork/assets/header.svg"
     alt="Masaaki Yamaguchi — Bada Language" width="900"/>
</div>

---

<div align="center">

### 🔤 Bada Language · BadaOS · omega_llm

[![Live Site](https://img.shields.io/badge/GitHub%20Pages-Bada%20Live%20Site-c8a44a?style=for-the-badge&logo=github&labelColor=04060a)](https://masaaki-avnturle.github.io/Bada/)
[![tuplenetwork](https://img.shields.io/badge/Portfolio-tuplenetwork-4a80d0?style=for-the-badge&labelColor=04060a)](https://masaaki-avnturle.github.io/tuplenetwork/)
[![Theory](https://img.shields.io/badge/Framework-Yamaguchi%20Theory-40b8c0?style=for-the-badge&labelColor=04060a)](https://masaaki-avnturle.github.io/tuplenetwork/#about)
[![Equations](https://img.shields.io/badge/Equations-54%2B%20Core-9060d0?style=for-the-badge&labelColor=04060a)](https://masaaki-avnturle.github.io/tuplenetwork/#equations)

</div>

---

<img src="https://masaaki-avnturle.github.io/tuplenetwork/assets/stats.svg"
     alt="Stats" width="900"/>

---

## ⬇️ ダウンロード — 原子の臨界期の強度シミュレータ (ACPI)

強レーザー場のなかで原子の**クーロン障壁が完全に抑制される時間窓 (= 臨界期)** と、
その窓での**強度** I(t) を計算するアプリ。**下のファイルを 1 つダウンロードして開くだけ**で
動きます (インストール不要・依存なし・オフライン可):

### 👉 [**bada_gui_ide/dist/atom-critical.html をダウンロード**](bada_gui_ide/dist/atom-critical.html)

ダウンロード手順(GitHub 上):上のリンクを開き、ファイル表示画面の右上にある **「Download raw file」(⬇ アイコン)** を押すと保存できます。保存した `atom-critical.html` をダブルクリックすればブラウザで開きます。

| ファイル | 内容 |
|:---|:---|
| [`atom-critical.html`](bada_gui_ide/dist/atom-critical.html) | ★ シミュレータ本体(単一 HTML)。元素・波長・ピーク強度・パルス幅・CEP を動かすと臨界期が即時に再計算され、4 枚の図と数値パネルが更新されます。CSV / JSON / PNG 出力付き |
| [`atom-critical-cli.js`](bada_gui_ide/cli/atom-critical-cli.js) | CLI 版 — `run` / `csv` / `json` / `sweep` / `scan` / `elements` / `selftest` |
| [`atom_critical.js`](bada_gui_ide/www/atom_critical.js) | モデルコア(GUI と CLI が共有) |
| [`atom_critical.bada`](bada_gui_ide/examples/atom_critical.bada) | 同じモデルの **Bada 言語**リファレンス実装 |

**臨界期とは** — 原子単位系で、クーロン障壁が完全に消える障壁抑制場は
`F_cr = I_p²/(4 Z_c)`、対応する臨界強度は `I_cr = F_cr² · I_a`
(`I_a = 3.5094×10¹⁶ W/cm²`)。臨界期は瞬時場が `|E(t)| ≥ F_cr` を満たす時間窓、
その強度は `I(t) = |E(t)|² · I_a` です。水素で `I_cr = 1.37×10¹⁴ W/cm²` という
既知の障壁抑制強度を再現します。直線偏光では臨界期は半サイクルごとの
**アト秒スケールのサブ窓**に分裂し、アプリはその 1 つ 1 つを表にします。

**二層モデル** — (A) 物理層: 障壁抑制場 · ADK トンネル電離率(水素で厳密解
`(4/F)e^{−2/3F}` に一致)· Keldysh γ · ポンデロモーティブ U_p。
(B) Ω 層(山口フレームワーク): `ζ(s)=β(p,q)/log x` · `ζ_n=(x log x)^n` ·
gamma-deprivation `e^{−x log x}` · Dalanversian `Λ=cos(ix log x)−i sin(ix log x)` ·
均衡余裕 `2e^{−x log x}`(臨界期で 0 へ潰れる = 重力/反重力均衡の喪失)·
Euler 極均衡 `x^n+y^n−nxyz=0` · Kauffman ブラケット `⟨D⟩(A)` ·
**臨界強度指数** `E(σ) = K(σ)×H(σ)/4(π_n,e_n)`。

```sh
node bada_gui_ide/cli/atom-critical-cli.js run  -e Ar -I 6e14 -l 800 -f 8
node bada_gui_ide/cli/atom-critical-cli.js scan -I 4e14      # 全元素を一括比較
node bada_gui_ide/cli/bada-cli.js run bada_gui_ide/examples/atom_critical.bada
```

zip 一式(CLI + コア + Bada 実装 + サンプル出力)は [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `acpi-dist.zip`。
ビルドは [`atom-critical-dist.yml`](.github/workflows/atom-critical-dist.yml) が実行します(`acpi-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。
詳細は [`bada_gui_ide/README.md`](bada_gui_ide/README.md) の「ACPI」節を参照。

> 直接リンク(右クリック→「名前を付けて保存」でも可):
> `https://raw.githubusercontent.com/masaaki-avnturle/Bada/main/bada_gui_ide/dist/atom-critical.html`
> (このブランチのマージ後に `main` から取得できます。マージ前は本ブランチの
> ファイル画面の「Download raw file」から取得してください)

---

## ⬇️ ダウンロード — ウルトラネットワーク専用ブラウザ (ZoneBrowser)

`https:`/`http:` に代わる暗号化 zone:// を閲覧する**専用ブラウザ**。**下のファイルを 1 つダウンロードして開くだけ**で動きます(インストール不要・依存なし・オフライン可):

### 👉 [**bada_gui_ide/dist/zone-browser.html をダウンロード**](bada_gui_ide/dist/zone-browser.html)

ダウンロード手順(GitHub 上):上のリンクを開き、ファイル表示画面の右上にある **「Download raw file」(⬇ アイコン)** を押すと保存できます。保存した `zone-browser.html` をダブルクリックすればブラウザで開きます。

| ファイル | 内容 |
|:---|:---|
| [`zone-browser.html`](bada_gui_ide/dist/zone-browser.html) | ★ 専用ブラウザ本体(単一 HTML)。アドレスバーに `zone://url.or.jp/` と入力して閲覧 |
| [`bada-zone.html`](bada_gui_ide/dist/bada-zone.html) | zone.bada ランナー(開くと自動実行) |
| [`zone.bada`](bada_gui_ide/examples/zone.bada) | zone:// スキームの Bada ソース |

#### 📱💻 ネイティブ アプリ (APK / Windows / Ubuntu)

ブラウザ不要のインストール型アプリも用意しています。[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `zonebrowser-debug.apk` |
| **Windows 10 / 11** | `ZoneBrowser-*-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `ZoneBrowser-*-x86_64.AppImage` / `ZoneBrowser-*-amd64.deb` |

ビルドは [`zonebrowser-app-build.yml`](.github/workflows/zonebrowser-app-build.yml) が実行します(`zonebrowser-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。詳細は [`bada_gui_ide/zonebrowser-app/`](bada_gui_ide/zonebrowser-app/) を参照。

> 直接リンク(右クリック→「名前を付けて保存」でも可):
> `https://raw.githubusercontent.com/masaaki-avnturle/Bada/main/bada_gui_ide/dist/zone-browser.html`
> (このブランチのマージ後に `main` から取得できます。マージ前は本ブランチの
> ファイル画面の「Download raw file」から取得してください)

---

## 📁 フォルダ構成 — Repository Structure

| フォルダ | 内容 | リンク |
|:--------|:----|:------|
| **`main/`** | Bada v3 ソースコード · BadaOS · TupleSpace全体インデックス · 4000+ LOC | [→ 開く](https://masaaki-avnturle.github.io/Bada/) |
| **`Bada++/`** | Bada言語C++拡張版 · 多様体演算子テンプレート · π(χ,x)非可換作用素 | [→ 開く](https://masaaki-avnturle.github.io/Bada/Bada%2B%2B/) |
| **`omega/`** | omega_llm エンジン · π-softmax · ℏ_eff注意 · gamma-deprivation · Omega::DATABASE | [→ 開く](https://masaaki-avnturle.github.io/Bada/omega/) |
| **`bada_gui_ide/`** | **Bada GUI IDE** — .badaをドラッグ&ドロップで自動コンパイル(Bada→C→ネイティブリンク)+インタープリタ実行 · @reviser文法拡張 · 量子サブ言語(qubit/H/CNOT/Measure) · **zone:// ウルトラネットワークWWW** (P2P DHT + Jones多項式量子暗号 AEAD, `examples/zone.bada`) | [→ 開く](bada_gui_ide/) |
| **`bada_gui_ide/dist/atom-critical.html`** | **ACPI — 原子の臨界期の強度シミュレータ** · 障壁抑制場 F_cr=I_p²/4Z_c · ADK トンネル電離 · Keldysh γ · Ω 作用素層 (ζ/β(p,q)/Γ-deprivation/Dalanversian/Euler 極均衡/Kauffman ⟨D⟩/E(σ)) · 単一 HTML | [→ 開く](bada_gui_ide/dist/atom-critical.html) |

---

## 🖱️ Bada GUI IDE — ダウンロード (Windows EXE / Ubuntu / Android APK)

`.bada` ソースを IDE ウィンドウに**ドラッグ&ドロップ**すると、**コンパイル(Bada→C→ネイティブリンク)** と**インタープリタ実行**を自動で行う GUI 開発環境です。論文 *Reviser-Extensible Grammars* の `@reviser : grammar` 文法拡張と Q# 風量子サブ言語 (`qubit` / `H` / `CNOT` / `Measure` / `Omega::Quantum`) を実装しています。

さらに `https:`/`http:` に代わるウルトラネットワークWWW の **`zone://url.or.jp`** スキームを Bada 言語自身で実装したリファレンス [`examples/zone.bada`](bada_gui_ide/examples/zone.bada) を同梱: `zone:` は中央サーバ・DNS ルートなしに P2P の仕組み(ピアハッシュのリング DHT)だけから構築され、通信は **Jones 多項式量子暗号** (`omega_jones_crypto_pkg` を Bada に移植) で保護されます — 各ゾーンの鍵は結び目図の Kauffman ブラケット標本から導出し、Bell 対 QKD がセッションソルトを合意、本文は Jones 鍵 AEAD で暗号化・封緘され、改ざんや誤った結び目は `409 zone-guard-reject` として排除、全レコードは追記専用 tuplespace(Akashic ゾーン台帳)にコミットされます。詳細は [`bada_gui_ide/README.md`](bada_gui_ide/README.md) の「zone://」節を参照。

| プラットフォーム | 入手 |
|:---|:---|
| **Windows 10 / 11** (EXE) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `Bada-GUI-IDE-*-x64.exe` |
| **Ubuntu** (AppImage / deb) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `Bada-GUI-IDE-*.AppImage` / `.deb` |
| **Android** (APK) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `bada-gui-ide-debug.apk` |
| **コマンドライン アプリ** (Windows) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `bada-cli.exe` — 単一実行ファイル。`run` / `build` (Bada→C→gcc) / `emit` / `tokens` / `ast` / **対話 `repl`** / `examples` |
| **コマンドライン アプリ** (Ubuntu) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `bada-cli-linux-x64` — 同上 (`chmod +x` して実行) |

ビルドは [`bada-ide-build.yml`](.github/workflows/bada-ide-build.yml) が自動実行します (`bada-ide-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。詳細は [`bada_gui_ide/README.md`](bada_gui_ide/README.md) を参照。

### 🌐 ウルトラネットワーク専用ブラウザ (ZoneBrowser) — インストール不要でダウンロード

`https:`/`http:` に代わる暗号化 zone:// を閲覧する**専用ブラウザ**を、**1 ファイルだけ**でどこでも動く自己完結版にしました:

| 入手方法 | 内容 |
|:---|:---|
| **専用ブラウザ (単一 HTML)** ★ | [`bada_gui_ide/dist/zone-browser.html`](bada_gui_ide/dist/zone-browser.html) をダウンロードして開くだけ。アドレスバーに `zone://url.or.jp/` と入力すると、P2P リング DHT でページを解決し、Bell 対 QKD + Jones 量子暗号で復号して表示。戻る/進む・リンク遷移・セキュリティパネル (DHT 鍵/経路/Jones 鍵/AEAD タグ/暗号文) 付き (依存なし・オフライン可) |
| **ランナー (単一 HTML)** | [`bada_gui_ide/dist/bada-zone.html`](bada_gui_ide/dist/bada-zone.html) — `zone.bada` を開くだけで自動実行 |
| **配布 zip** | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `bada-zone-dist.zip` (専用ブラウザ + ランナー + `zone.bada` + `bada.js` + CLI + README)。[`zone-dist.yml`](.github/workflows/zone-dist.yml) が `zone-v*` タグ / `workflow_dispatch` で生成・添付します |
| **CLI** | `node bada_gui_ide/cli/bada-cli.js run bada_gui_ide/examples/zone.bada` |

---

## 🔤 Bada Language — 設計原理

山口フレームワークの作用素環プログラミングを実現するために設計された独自OOP言語。

### 核心設計思想

```
// Bada v3 — 多様体演算子構文例

class ManifoldNode <- TupleSpace {
  operator <- (input) {
    return beta(p,q) / log(input);   // ζ(s) = β(p,q)/log x
  }
  operator -< (state) {
    return gamma(state) * exp(-state * log(state));  // Γ(s)
  }
  operator >- (output) {
    return pi_operator(chi, output);  // π(χ,x) non-commutative
  }
}

Omega::DATABASE[tuplespace] {
  push(ManifoldNode);  // Akashic Record への書き込み
}
```

### 演算子一覧

| 演算子 | 数学的対応 | 説明 |
|:------|:---------|:----|
| `<-`  | `π(χ,x) = [iπ, f(x)]` | 非可換左作用 |
| `-<`  | `∬1/(x·log x)² dx_m` | 多様体積分 |
| `>-`  | `⊕(iℏ∇)^⊕L` | 量子作用素右作用 |
| `Ω::` | `Ω::DATABASE` | TupleSpace名前空間 |

---

## 🖥️ omega_llm エンジン — `omega/` フォルダ

```c
/* omega_math.c — π-softmax 実装 */
double pi_softmax(double* logits, int n, double hbar_eff) {
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        // ⊕(iℏ∇)^⊕L スケーリング
        sum += exp(logits[i] * hbar_eff * M_PI);
    }
    return sum;
}

/* omega_tuplespace.c — Akashic Record */
void omega_push(OmegaDB* db, const char* key, Manifold* m) {
    // Ω::DATABASE ⊃ Z ⊃ C ⊕ ∇R⁺
    tuplespace_insert(db->akashic, key, manifold_encode(m));
}
```

### ファイル構成

| ファイル | 内容 |
|:--------|:----|
| `omega_core.h` | コアヘッダ · 型定義 · 多様体構造体 |
| `omega_math.c` | π-softmax · gamma-deprivation · β(p,q)積分 |
| `omega_tuplespace.c` | Omega::DATABASE · Akashic Record実装 |
| `omega_attention.c` | ℏ_eff注意スケーリング · Jones多項式カーネル |
| `omega_model.c` | モデル本体 · 推論ループ · 生成サンプリング |

---

## ⚡ Bada++ — `Bada++/` フォルダ

```cpp
// Bada++/manifold_operator.hpp
template<typename T, typename Gamma = GammaFunction<T>>
class ManifoldOperator {
    T pi_operator(T chi, T x) const {
        // π(χ,x) = [iπ(χ,x), f(x)] non-commutative
        return std::complex<T>(0, M_PI) * chi * std::log(x);
    }
    T beta_zeta(T p, T q) const {
        // ζ(s) = β(p,q)/log x
        return gamma_(p) * gamma_(q) / gamma_(p + q);
    }
};
```

---

## 🔗 関連リポジトリ

| リポジトリ | 内容 | リンク |
|:---------|:----|:------|
| **tuplenetwork** | 論文PDF全16本 · TupleSpace理論 · ポートフォリオ | [→](https://masaaki-avnturle.github.io/tuplenetwork/) |
| **tuplenetwork/pdf/** | caostics.pdf · jum.pdf · Bada__1.pdf 等 | [→](https://masaaki-avnturle.github.io/tuplenetwork/pdf/) |
| **tuplenetwork/altmistypdf/** | アミノ医薬・有機化学論文 | [→](https://masaaki-avnturle.github.io/tuplenetwork/altmistypdf/) |
| **tuplenetwork/exceedpdf/** | Secureproduct · Magic演算子 · カタストロフィ | [→](https://masaaki-avnturle.github.io/tuplenetwork/exceedpdf/) |
| **tuplenetwork/origin/** | 1998年原典・研究記録・履歴書 | [→](https://masaaki-avnturle.github.io/tuplenetwork/origin/) |

---

<img src="https://masaaki-avnturle.github.io/tuplenetwork/assets/timeline.svg"
     alt="Research Timeline" width="900"/>

---

<div align="center">

```
β(p,q) = Γ(p)Γ(q)/Γ(p+q)  ·  ζ(s) = x·log x
⊕(iℏ∇)^⊕L = e^{-x·log x}  ·  π(χ,x) = [iπ, f(x)]
        Ω::DATABASE ↔ ∞  ← TupleSpace Akashic
```

[![Portfolio](https://img.shields.io/badge/Full%20Portfolio-masaaki--avnturle.github.io%2Ftuplenetwork-4a80d0?style=for-the-badge&labelColor=04060a)](https://masaaki-avnturle.github.io/tuplenetwork/)

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Global Differential Manifold Research*

</div>
