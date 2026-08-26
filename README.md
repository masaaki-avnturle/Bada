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

## ⬇️ ダウンロード — ウルトラネットワーク専用ブラウザ (ZoneBrowser)

`https:`/`http:` に代わる暗号化 zone:// を閲覧する**専用ブラウザ**。**下のファイルを 1 つダウンロードして開くだけ**で動きます(インストール不要・依存なし・オフライン可):

### 👉 [**bada_gui_ide/dist/zone-browser.html をダウンロード**](bada_gui_ide/dist/zone-browser.html)

ダウンロード手順(GitHub 上):上のリンクを開き、ファイル表示画面の右上にある **「Download raw file」(⬇ アイコン)** を押すと保存できます。保存した `zone-browser.html` をダブルクリックすればブラウザで開きます。

### 📦 ウルトラネットワーク アプリ一式(単一HTML・ダウンロードして開くだけ)

以下はすべて **1 ファイル完結**の HTML アプリです。リンクを開き **「Download raw file」(⬇)** で保存 → ダブルクリックで起動(インストール不要・依存なし・オフライン可):

| アプリ | 内容 |
|:---|:---|
| [`zone-browser.html`](bada_gui_ide/dist/zone-browser.html) | ★ **ZoneBrowser** — zone:// 専用ブラウザ(P2P DHT + Jones量子暗号 + UltraDB複製 + 認知検索) |
| [`ngn-quantum.html`](bada_gui_ide/dist/ngn-quantum.html) | **NGN Quantum Grid** — zone:// を **NTT NGN 回線**に投射(地域局バックボーン環 + 各家庭/職場PCのHDD擬似量子レジスタ + NTT回線上のエンタングルメント) |
| [`zone-studio.html`](bada_gui_ide/dist/zone-studio.html) | **Zone Studio** — **`zone://` URI で自分の WWW を構築**し、NTT NGN 経由でウルトラネットワークに公開(UltraDB複製 + Jones量子暗号)。ページ作成/編集/プレビュー・`.zonesite` 書き出し/読み込み |
| [`lan-to-zone.html`](bada_gui_ide/dist/lan-to-zone.html) | **LAN → zone://** — 自分のLAN IPを `zone://url.or.jp/lan/` に暗号化取り込み |
| [`modem-vault.html`](bada_gui_ide/dist/modem-vault.html) | **Modem Vault** — 自分のモデム認証情報の量子暗号保管庫 + LAN検出 |
| [`quantum-shark.html`](bada_gui_ide/dist/quantum-shark.html) | **QuantumShark** — 量子暗号つきパケット アナライザ(`.qcap` 復号。デモ: master `demo`) |
| [`bada-zone.html`](bada_gui_ide/dist/bada-zone.html) | zone.bada ランナー(開くと自動実行) |

**一括ダウンロード(zip)**: [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `bada-ultranetwork-apps.zip`。[`apps-dist.yml`](.github/workflows/apps-dist.yml) が `apps-v*` タグ / `workflow_dispatch` で生成・添付します。自分で生成する場合は `node bada_gui_ide/tools/build-all-apps.js`。

#### 🟢 GitHub Actions からダウンロード

このブランチ(および `main`)へ push すると [`apps-dist.yml`](.github/workflows/apps-dist.yml) が自動実行され、成果物が Actions に残ります:

1. リポジトリの **Actions** タブ → 左の **「Ultra Network apps (downloadable bundle)」** を開く
2. 最新の実行(緑チェック)をクリック
3. 下部の **Artifacts** から **`bada-ultranetwork-apps`** をダウンロード(5つの単一HTML + `bada-ultranetwork-apps.zip` を含む zip)

ネイティブ アプリ(APK / Windows EXE / Ubuntu)は **「ZoneBrowser app build」** の実行画面の Artifacts(`zonebrowser-windows` / `zonebrowser-linux` / `zonebrowser-android`)から取得できます。Release への添付が必要な場合は、各ワークフローを `workflow_dispatch` で実行し `release_tag`(例 `apps-v1.1.0`)を指定してください。

各アプリに付属する CLI(自分のマシン/LAN対象)は [`bada_gui_ide/zoneimport/`](bada_gui_ide/zoneimport/) · [`modemvault/`](bada_gui_ide/modemvault/) · [`netcapture/`](bada_gui_ide/netcapture/) を参照。

#### 📱💻 ネイティブ アプリ (APK / Windows / Ubuntu)

ブラウザ不要のインストール型アプリも用意しています。[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `zonebrowser-debug.apk` |
| **Windows 10 / 11** | `ZoneBrowser-*-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `ZoneBrowser-*-x86_64.AppImage` / `ZoneBrowser-*-amd64.deb` |

ビルドは [`zonebrowser-app-build.yml`](.github/workflows/zonebrowser-app-build.yml) が実行します(`zonebrowser-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。詳細は [`bada_gui_ide/zonebrowser-app/`](bada_gui_ide/zonebrowser-app/) を参照。

**NGN Quantum Grid**(zone:// を NTT NGN に投射)もネイティブ アプリを用意しています:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `ngn-quantum-grid-debug.apk` |
| **Windows 10 / 11** | `NGN-Quantum-Grid-*-x64.exe` |
| **Ubuntu** | `NGN-Quantum-Grid-*-x86_64.AppImage` / `NGN-Quantum-Grid-*-amd64.deb` |

ビルドは [`ngngrid-app-build.yml`](.github/workflows/ngngrid-app-build.yml)([`bada_gui_ide/ngngrid-app/`](bada_gui_ide/ngngrid-app/))。Ubuntu の AppImage / deb はローカルビルド確認済み。

**Zone Studio**(zone:// で自分の WWW を構築)もネイティブ アプリを用意しています:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `zone-studio-debug.apk` |
| **Windows 10 / 11** | `Zone-Studio-*-x64.exe` |
| **Ubuntu** | `Zone-Studio-*-x86_64.AppImage` / `Zone-Studio-*-amd64.deb` |

ビルドは [`zonestudio-app-build.yml`](.github/workflows/zonestudio-app-build.yml)([`bada_gui_ide/zonestudio-app/`](bada_gui_ide/zonestudio-app/))。Ubuntu の AppImage / deb はローカルビルド確認済み。

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

---

## 🖱️ Bada GUI IDE — ダウンロード (Windows EXE / Ubuntu / Android APK)

`.bada` ソースを IDE ウィンドウに**ドラッグ&ドロップ**すると、**コンパイル(Bada→C→ネイティブリンク)** と**インタープリタ実行**を自動で行う GUI 開発環境です。論文 *Reviser-Extensible Grammars* の `@reviser : grammar` 文法拡張と Q# 風量子サブ言語 (`qubit` / `H` / `CNOT` / `Measure` / `Omega::Quantum`) を実装しています。

さらに `https:`/`http:` に代わるウルトラネットワークWWW の **`zone://url.or.jp`** スキームを Bada 言語自身で実装したリファレンス [`examples/zone.bada`](bada_gui_ide/examples/zone.bada) を同梱: `zone:` は中央サーバ・DNS ルートなしに P2P の仕組み(ピアハッシュのリング DHT)だけから構築され、通信は **Jones 多項式量子暗号** (`omega_jones_crypto_pkg` を Bada に移植) で保護されます — 各ゾーンの鍵は結び目図の Kauffman ブラケット標本から導出し、Bell 対 QKD がセッションソルトを合意、本文は Jones 鍵 AEAD で暗号化・封緘され、改ざんや誤った結び目は `409 zone-guard-reject` として排除、全レコードは追記専用 tuplespace(Akashic ゾーン台帳)にコミットされます。

**進化版 UltraWeb** [`examples/ultraweb.bada`](bada_gui_ide/examples/ultraweb.bada): 以前のウルトラネットワーク(**UltraDatabase** = `Omega.DATABASE[first..fourth]` 分散DB + `cognitive_system`/`manifold_scan`)を融合し、各レコードを最近傍 4 ピアに複製(クォーラム読み取りで改ざん複製を自己修復・単一障害点なし)、`cognitive_system` 検索(位相コアの softmax = |ψ|²)でゾーン全体を関連度順にランキングします。詳細は [`bada_gui_ide/README.md`](bada_gui_ide/README.md) の「zone://」節を参照。

| プラットフォーム | 入手 |
|:---|:---|
| **Windows 10 / 11** (EXE) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `Bada-GUI-IDE-*-x64.exe` |
| **Ubuntu** (AppImage / deb) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `Bada-GUI-IDE-*.AppImage` / `.deb` |
| **Android** (APK) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `bada-gui-ide-debug.apk` |

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
