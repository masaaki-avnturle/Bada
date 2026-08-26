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

## 🔌 @reviser : extension — Bada / C / Python / Java による機能拡張

リバイザは文法だけでなく**実装**も拡張できます。拡張トランザクション

```
@reviser : extension <bada|c|python|java> {
    fun 名前 |引数, ...| """コード"""
}
```

は各拡張を追記専用レジャーへ `["extension", lang, name, params]` として
コミットし、`名前(...)` を呼び出し可能にします (`examples/extensions.bada`):

| 言語 | コード規約 | 実行 |
|:---|:---|:---|
| **bada** | コードは Bada ソース (`return` 可) — **自己拡張** | 全プラットフォーム |
| **c** | `double 名前(double p1, …)` の**関数本体** (数値のみ) | インタープリタ: gcc でビルドして FFI 呼び出し / **コンパイラ: 生成 C にインライン**されネイティブ関数になる |
| **python** | `ARGS` (JSON デコード済みリスト) を読み `RESULT` に代入 — リストも可 | CLI・デスクトップ IDE (要 python3) |
| **java** | `static double run(double[] args)` の**本体** (数値のみ) | CLI・デスクトップ IDE (要 JDK) |

- 引数は JSON でマーシャリング (`dist` / 量子レジスタは確率ベクトルとして渡る)
- 複数行コードは **`"""` 三重引用符文字列** (エスケープ不要の raw ブロック)
- C / Java はソースのハッシュでキャッシュされ再コンパイルされません
- ブラウザ / APK では bada 拡張のみ動作し、他言語は明示メッセージで縮退

```
@reviser : extension c {
    fun c_hypot |a, b| """ return sqrt(a*a + b*b); """
}
print(c_hypot(3, 4))          # => 5   (bada build なら生成Cにインライン)
```

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

## ディレクトリ構成

```
bada_gui_ide/
  www/        IDE 本体 (index.html / app.js / bada.js 言語コア / examples.js)
  electron/   Windows EXE / Ubuntu AppImage・deb ラッパー (gcc ネイティブ経路)
  cordova/    Android APK 設定
  cli/        CLI アプリ:  run|build|emit|tokens|ast|repl|examples|version
              (node cli/bada-cli.js … で実行、Release では単一バイナリ
               bada-cli.exe / bada-cli-linux-x64 として配布)
  examples/   hello / engine / core / quantum / zone の各 .bada
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
```
