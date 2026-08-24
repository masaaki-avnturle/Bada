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
  cli/        Node.js CLI:  node cli/bada-cli.js run|build|emit|tokens|ast <f.bada>
  examples/   hello / engine / core / quantum の各 .bada
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
