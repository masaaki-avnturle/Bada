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

## 🜁 ダウンロード — Bada VM Pro(今までの集大成)

**量子プログラミング言語 Bada のオペレーティングシステム。** デスクトップは **w9wm window manager**(9wm + 仮想スクリーン 4 面、右クリック = New/Reshape/Move/Delete/Hide)、ベース(カーネル)は **BadaGPT** で、**OS の update / upgrade も BadaGPT が実行**します。**bash / apt / vim / emacs / ssh / xinetd / texlive-full / screen / fcitx-mozc を事前インストール**した Ubuntu 風ユーザーランドと**日本語入力対応ターミナル 3 種**(xterm / x-terminal-emulator / terminal)、**Bada on Rails**(scaffold → CRUD)、**合い言葉コマンド**、**トランスフォーマー・スタジオ**、**GUI / CUI プログラミング**をひとつに統合。依存ゼロ・単一 HTML・オフライン動作、**ライブ CD (`BadaVMPro-live.iso`) 配布 + ISO マウント機能**つき。

### 👉 [**bada_vm_pro/index.html をダウンロード**](bada_vm_pro/index.html)

上のリンクを開き **「Download raw file」(⬇ アイコン)** で保存 → ダブルクリックで起動(インストール不要)。

#### 📱💻 ネイティブ アプリ (APK / Windows / Ubuntu)

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-vm-pro-debug.apk` |
| **Windows 10 / 11** | `BadaVMPro-*-x64.exe` (NSIS インストーラ / ポータブル) |
| **Ubuntu** | `BadaVMPro-*-x86_64.AppImage` / `BadaVMPro-*-amd64.deb` |
| **ライブ CD** (ISO) | `BadaVMPro-live.iso` — ISO 9660 + El Torito ブータブル。マウントして `INDEX.HTM` を開けば OS 起動、VM Pro 内でも「ISO をマウント」で `/mnt/cdrom` に読込可 |

ビルドは [`badavmpro-app-build.yml`](.github/workflows/badavmpro-app-build.yml) が実行します(`badavmpro-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。使い方・合い言葉・量子 Bada 文法は [`bada_vm_pro/`](bada_vm_pro/) を参照。

---

## ⚔ ダウンロード — Laevateinn(自動走行アシスタントAI「アル」)

自動走行の自動車**レーヴァテイン**とアシスタントAI**アル**。**アルのトランスフォーマーが車両を操縦**します — 知覚 attention を操舵角と加減速の2値に写す制御ヘッドが、その2値だけで車体(自転車近似モデル)を動かし、周囲(16レイセンサへの attention)を検知して自動で回避・減速・停止・再発進。測位は 2 モード — **🌐 Web地図モード**は衛星を使わず、ウェブサイトから受信する地図タイル(AEAD 検証つき)+推測航法+ランドマーク補正で走り、**🛰 人工衛星モード**は 4 機の擬似距離から最小二乗で測位します。A* 経路計画・依存ゼロ・単一 HTML。

**🔗 実車接続対応**: ELM327 互換の **BLE OBD-II アダプタに本物の Bluetooth で接続**し、実車の速度・回転数・水温・電圧をリアルタイム受信(ブラウザ = Web Bluetooth / APK = BLE プラグイン。ELM327 初期化列 + PID ポーリング + 分割パケット再結合を実装、読取専用)。**アルの音声案内**は、スマホとカーナビの既存 Bluetooth オーディオ接続を通じて**車のスピーカーから流れます**。アダプタなしでも「デモ接続」で全経路を確認可能。

### 👉 [**laevateinn/index.html をダウンロード**](laevateinn/index.html)

上のリンクを開き **「Download raw file」(⬇ アイコン)** で保存 → ダブルクリックで起動。APK (`laevateinn-al-debug.apk`) / Windows EXE / Ubuntu 版は [Releases](https://github.com/masaaki-avnturle/Bada/releases) から([`laevateinn-app-build.yml`](.github/workflows/laevateinn-app-build.yml) が `laevateinn-v*` タグでビルド)。詳細は [`laevateinn/`](laevateinn/) を参照。

---

## ⬇️ ダウンロード — ウルトラネットワーク専用ブラウザ (ZoneBrowser)

`https:`/`http:` に代わる暗号化 zone:// を閲覧する**専用ブラウザ**。**下のファイルを 1 つダウンロードして開くだけ**で動きます(インストール不要・依存なし・オフライン可):

### 👉 [**bada_gui_ide/dist/zone-browser.html をダウンロード**](bada_gui_ide/dist/zone-browser.html)

ダウンロード手順(GitHub 上):上のリンクを開き、ファイル表示画面の右上にある **「Download raw file」(⬇ アイコン)** を押すと保存できます。保存した `zone-browser.html` をダブルクリックすればブラウザで開きます。

| ファイル | 内容 |
|:---|:---|
| [`zone-browser.html`](bada_gui_ide/dist/zone-browser.html) | ★ 専用ブラウザ本体(単一 HTML)。アドレスバーに `zone://url.or.jp/` と入力して閲覧。**🛡 ZoneShield 付属** — Jones多項式量子暗号のセキュリティソフト(下記) |
| [`bada-zone.html`](bada_gui_ide/dist/bada-zone.html) | zone.bada ランナー(開くと自動実行) |
| [`zone.bada`](bada_gui_ide/examples/zone.bada) | zone:// スキームの Bada ソース |

#### 🛡 付属セキュリティソフト — ZoneShield(量子暗号アプリケーション)

ZoneBrowser のツールバー右端の **🛡 ボタン**で起動。ネットワークが使っているのと**同一の Bada 実装**(結び目図 → Kauffman/Jones 多項式 → 鍵 → AEAD、Bell対 QKD セッション salt)を、手元の道具として使えます:

- **封緘(暗号化)** — 任意のテキスト(日本語可)を host の結び目鍵で封緘し、コピペできる**封筒 JSON** を出力
- **開封(復号)** — 封筒 JSON を貼り付けると AEAD タグを検証してから復号。改ざん・結び目違いは **409 で拒否**し平文を出さない
- **セキュリティスキャン** — 公開中の全 zone ページを再配信して Jones-AEAD 検証し、改ざん検知の自己テスト(暗号文 1 ユニット反転 → 409)まで実施したレポートを表示

APK / EXE / AppImage 版にもそのまま同梱されます(同じ `www/index.html` を包むため)。

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
| **`cpp_builder/`** | **Bada C++Builder** — Inprise/Borland C++Builder 風 RAD IDE のブラウザ再現(オマージュ) · フォームデザイナ + Object Inspector + コンポーネントパレット · Unit1.cpp/h/dfm 自動生成 · C++サブセット実行系 (F9) · 単一HTML/依存ゼロ | [→ 開く](cpp_builder/) |
| **`bada_vm_pro/`** | ★ **Bada VM Pro(集大成)** — w9wm デスクトップ(9wm + 仮想スクリーン) · BadaGPT カーネル(OS update/upgrade 担当) · bash/apt/vim/emacs/ssh/xinetd/texlive-full/screen/fcitx-mozc 事前インストール · 日本語入力対応ターミナル · Bada on Rails · 量子 Bada 実行系 · 合い言葉コマンド · self-attention トランスフォーマー · GUI/CUI プログラミング · APK/EXE/AppImage/**ライブ CD ISO** 配布 | [→ 開く](bada_vm_pro/) |
| **`laevateinn/`** | **Laevateinn** — 自動走行アシスタントAI「アル」 · トランスフォーマー知覚(16レイ attention) · 衛星不使用のWeb地図測位(AEAD検証タイル+推測航法+ランドマーク補正)/人工衛星測位(最小二乗) · A* 経路計画 · APK/EXE/AppImage 配布 | [→ 開く](laevateinn/) |

---

## 🏗️ Bada C++Builder — Inprise/Borland C++Builder 風 RAD IDE (オマージュ)

1997〜2001 年ごろの **Inprise (Borland) C++Builder** の開発環境を、依存ゼロの**単一 HTML** としてブラウザ上に再現しました(非公式・教育目的のオマージュです)。

**👉 [`cpp_builder/index.html` を開く](cpp_builder/index.html)** / GitHub Pages: <https://masaaki-avnturle.github.io/Bada/cpp_builder/>

- **フォームデザイナ** — コンポーネントパレット (Standard/Additional/Win32/System, 14種) からクリック配置、8px グリッドスナップ、ドラッグ移動・リサイズ
- **Object Inspector** — Properties / Events タブ。イベント欄ダブルクリックでハンドラ自動生成
- **コード自動生成** — VCL 風の `Unit1.cpp` / `Unit1.h` / `Unit1.dfm` を常時生成、ハンドラ本体は編集可能
- **F9 で実行** — 内蔵の C++ サブセット・ミニインタープリタ (`if/while/for`、`Label1->Caption`、`Memo1->Lines->Add`、`ShowMessage`、`IntToStr`、`TTimer` など) が設計したフォームを実際に動かします

#### 📱💻 ネイティブ アプリ (APK / Windows 10・11 / Ubuntu)

ブラウザ不要のインストール型アプリも [Releases](https://github.com/masaaki-avnturle/Bada/releases) からダウンロードできます:

| プラットフォーム | ファイル |
|:---|:---|
| **Android** (APK) | `bada-cppbuilder-debug.apk` |
| **Windows 10 / 11** | `BadaCppBuilder-*-x64.exe` (NSIS インストーラ) / `BadaCppBuilder-*-portable.exe` (ポータブル) |
| **Ubuntu** | `BadaCppBuilder-*-x86_64.AppImage` / `BadaCppBuilder-*-amd64.deb` |

ビルドは [`cppbuilder-app-build.yml`](.github/workflows/cppbuilder-app-build.yml) が実行します(`cppbuilder-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。詳細は [`cpp_builder/README.md`](cpp_builder/README.md) を参照。

---

## 🖱️ Bada GUI IDE — ダウンロード (Windows EXE / Ubuntu / Android APK)

`.bada` ソースを IDE ウィンドウに**ドラッグ&ドロップ**すると、**コンパイル(Bada→C→ネイティブリンク)** と**インタープリタ実行**を自動で行う GUI 開発環境です。論文 *Reviser-Extensible Grammars* の `@reviser : grammar` 文法拡張と Q# 風量子サブ言語 (`qubit` / `H` / `CNOT` / `Measure` / `Omega::Quantum`) を実装しています。

さらに **`@reviser : extension`** で Bada を **Bada自身 / C / Python / Java** で機能拡張できます([`examples/extensions.bada`](bada_gui_ide/examples/extensions.bada)): 各拡張は追記専用レジャーへコミットされる拡張トランザクションで、C 拡張は**コンパイラが生成 C にインライン**してネイティブ化、Python / Java / C 拡張はインタープリタ(CLI・デスクトップ IDE)の FFI ブリッジで実行、Bada 拡張(自己拡張)は全プラットフォームで動作します。

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

### 🔐 量子暗号アプリ (Bada QuantumCrypto) — 暗号化と解除(復号)

zone:// の **Jones 多項式量子暗号**を単独アプリにしたもの。テキストとファイルを**暗号化**し、同じパスフレーズ + 結び目で**解除**できます (Kauffman ブラケット鍵導出 + Bell 対 QKD + ChaCha20/HMAC AEAD、端末内完結・通信なし):

| プラットフォーム | 入手 |
|:---|:---|
| **Android** (APK) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `quantumcrypto-debug.apk` |
| **Windows 10 / 11** (EXE) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `BadaQuantumCrypto-Setup-*-x64.exe` (インストーラ) / `BadaQuantumCrypto-Portable-*-x64.exe` (インストール不要) |
| **Ubuntu** (AppImage / deb) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `BadaQuantumCrypto-*.AppImage` / `.deb` |
| **どこでも** (HTML) | [`bada_gui_ide/quantumcrypto-app/www/`](bada_gui_ide/quantumcrypto-app/www/) の `index.html` + `qcrypto.js` をブラウザで開くだけ |

ビルドは [`quantumcrypto-app-build.yml`](.github/workflows/quantumcrypto-app-build.yml) が自動実行します (`quantumcrypto-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。使い方と仕組みは [`bada_gui_ide/quantumcrypto-app/README.md`](bada_gui_ide/quantumcrypto-app/README.md) を参照。

### 🜁 Bada VM Pro — 量子 Bada OS (w9wm デスクトップ)

量子 Bada 言語の OS。デスクトップは **w9wm window manager** (9wm + 仮想スクリーン 4 面、右クリック = New/Reshape/Move/Delete/Hide)、カーネルは BadaGPT。**bash / apt / vim / emacs / ssh / xinetd / texlive-full / screen / fcitx-mozc** を事前インストールし、**日本語入力対応**のターミナル (xterm / x-terminal-emulator / terminal) を同梱:

| プラットフォーム | 入手 |
|:---|:---|
| **Android** (APK) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `bada-vm-pro-debug.apk` |
| **Windows 10 / 11** (EXE) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `BadaVMPro-*-x64.exe` (インストーラ / ポータブル) |
| **Ubuntu** (AppImage / deb) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `BadaVMPro-*.AppImage` / `.deb` |
| **ライブ CD** (ISO) | Releases / [Actions](https://github.com/masaaki-avnturle/Bada/actions) の `BadaVMPro-live.iso` — ISO 9660 + El Torito ブータブル (マウントして `INDEX.HTM` を開けば OS 起動)。VM Pro 自身もアプリメニューから ISO を `/mnt/cdrom` にマウント可能 |
| **どこでも** (単一 HTML) | [`bada_vm_pro/index.html`](bada_vm_pro/index.html) をダウンロードして開くだけ |

ビルドは [`badavmpro-app-build.yml`](.github/workflows/badavmpro-app-build.yml) が自動実行します (`badavmpro-v*` タグで Release へ添付 / `workflow_dispatch`)。詳細は [`bada_vm_pro/README.md`](bada_vm_pro/README.md) を参照。

### 🔎 Bada Search — SourceTree 付属 PDF・ソースコード検索エンジン (Windows 10/11)

Git GUI **SourceTree** のカスタム操作 (`$REPO`) に登録して付属アプリとして使う検索エンジン。リポジトリ丸ごとを対象に、**40 種以上のプログラミング言語のソース**と **PDF の中身** (FlateDecode テキスト抽出・依存ゼロ) を AND / 正規表現 / 言語・パスフィルタで横断検索し、行番号 + ハイライト付きで表示します:

| プラットフォーム | 入手 |
|:---|:---|
| **Windows 10 / 11** (EXE) | [Releases](https://github.com/masaaki-avnturle/Bada/releases) の `BadaSearch-Setup-*-x64.exe` (インストーラ) / `BadaSearch-Portable-*-x64.exe` (インストール不要) |

SourceTree への登録: ツール → オプション → カスタム操作 → スクリプトに `BadaSearch.exe`、パラメータに `$REPO`。ビルドは [`sourcetree-search-build.yml`](.github/workflows/sourcetree-search-build.yml) が自動実行します (`stsearch-v*` タグ / `workflow_dispatch`)。詳細は [`sourcetree_search/README.md`](sourcetree_search/README.md) を参照。

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
