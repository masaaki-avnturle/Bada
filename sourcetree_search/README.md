# 🔎 Bada Search — SourceTree 付属 PDF・ソースコード検索エンジン (Windows 10/11)

Git GUI **SourceTree** の「カスタム操作」に登録して付属アプリとして使う検索エンジンです。
リポジトリを丸ごとインデックスし、**プログラミング言語のソースコード**(C/C++/JavaScript/
TypeScript/Python/Ruby/Java/Go/Rust/PHP/C#/Swift/Kotlin/Shell/SQL/HTML/CSS/Bada/OmegaScript
ほか 40 種以上)と **PDF の中身**(FlateDecode ストリームからのテキスト抽出 — 依存ライブラリ
ゼロ)を横断検索します。単体アプリとしても動きます。

## 🏥 単語補完 大画面モード (既定画面 — 広島大学病院の薬剤検索風)

起動すると、**黒い大画面の端末**が開き、検索ボックスに数文字を打つだけで、
論文(PDF)とソースコードから抽出した**単語の補完候補がポップアップメニューで出現**します
(広島大学医学部附属病院の薬剤検索システムと同じインクリメンタル補完)。

- **索引時に語彙(ボキャブラリ)を構築** — ソースの識別子(`jonesKey`, `kauffman_bracket` …)と
  論文本文の単語、和文の語(`量子多項式` …)を収集し、出現頻度と出現ファイル数を記録。
- **入力途中で候補をポップアップ** — 前方一致を最優先、足りなければ部分一致で補い、**頻度の高い順**に表示。
  各候補に「○件 / ○ファイル」と「前方/部分」タグ付き。
- **キーボード操作** — `↑`/`↓` で候補移動、`Enter` で確定(その語で全文検索)、`Esc` で閉じる。
  マウスのクリックでも選択可。
- 候補を選ぶと、その単語で本文・コードを横断検索し、**行番号つき・ハイライト付き**で大画面に表示。

> 画面右上の「**詳細ビュー →**」で、従来のフィルタ付き一覧ビュー(下記)にいつでも切り替えられます
> (詳細ビュー側の「🏥 単語補完 大画面 →」で戻れます)。

## 🎬 付属エディタ BadaCineVim (シネマ風 Vim ビューア/エディタ)

検索結果の各ファイルの **🎬 CineVim** ボタンから、そのファイルを **Vim スタイルの
モーダル・エディタ**で開けます(黒い大画面に合うシネマ風オーバーレイ・依存ゼロの純 JS)。
検索語の **該当行へ自動ジャンプ**し、一致箇所をハイライトします。

- **NORMAL**: `h j k l` 移動 / `0 $ ^` 行頭末 / `w b` 単語 / `gg G` 先頭末 /
  `x` 1字削除 / `dd` 行削除 / `Ctrl-d` `Ctrl-u` 半画面 / `n` `N` 検索送り
- **INSERT**: `i a A I o O` で挿入開始、`Enter` 改行、`Backspace`、`Esc` で NORMAL へ
- **COMMAND**: `/語` 検索、`:w` 保存、`:q` 閉じる、`:wq` 保存して閉じる、`:<行番号>` 移動
- 論文(PDF 由来テキスト)は **読み取り専用 `[RO]`** で開き、編集・保存はしません。
  ソースコードは `:w` でその場に保存できます(Electron 版)。

> 由来: リポジトリの mini-Vim 実装 (`neovim/omega-vim.c`) の操作系を、Web/Electron の
> Bada Search に合わせて純 JS で作り直した付属エディタです。

## ⬇️ ダウンロード

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| プラットフォーム | ファイル | 使い方 |
|:---|:---|:---|
| **Windows 10 / 11** | `BadaSearch-Setup-*-x64.exe` / `BadaSearch-Portable-*-x64.exe` | SourceTree のカスタム操作から / 単体でも |
| **Android** | `badasearch-debug.apk` | 端末のファイルを選んで単語補完検索 + CineVim |

ビルドは [`sourcetree-search-build.yml`](../.github/workflows/sourcetree-search-build.yml)
が自動実行します (`stsearch-v*` タグを push すると Release に EXE と APK を添付、
または Actions の `workflow_dispatch` で `release_tag` を指定)。

### 🖥️📱 EXE と APK (BadaCineVim を融合)

- **Windows EXE** — Electron。SourceTree のカスタム操作 (`$REPO`) から起動し、
  リポジトリを Node でインデックスして横断検索。起動画面は広島大学病院風の
  黒い大画面(単語補完)で、結果は **BadaCineVim** で編集もできます (`:w` 保存)。
- **Android APK** — 同じ黒い大画面を Cordova で収録。SourceTree/Node が無い端末では、
  **端末内のファイル/フォルダを選ぶ**とブラウザ側エンジン (`searchweb.js`) が
  PDF(`DecompressionStream` で展開)とソースを索引し、単語補完 → 検索 →
  **BadaCineVim**(閲覧専用)で該当行へジャンプ、までを 1 アプリで行います。

検索エンジン `searchcore.js` は Node(EXE)でもブラウザ(APK)でも動く UMD で、
両者で同一のコードを使います(CI が core/www の同一性を検証)。

## 🌳 SourceTree に付属させる手順

1. SourceTree の **ツール → オプション → カスタム操作** を開き「**追加**」
2. **メニューキャプション**: `Bada Search (PDF・コード検索)`
3. **実行するスクリプト**: インストールした `BadaSearch.exe` のフルパス
   (既定: `C:\Users\<あなた>\AppData\Local\Programs\BadaSearch\BadaSearch.exe`、
   ポータブル版は置いた場所)
4. **パラメータ**: `$REPO`

以後、SourceTree でリポジトリを開いた状態で **操作 → カスタム操作 → Bada Search** を
選ぶと、そのリポジトリを自動インデックスして検索画面が開きます
(`$REPO` がコマンドライン引数としてアプリに渡ります)。

## 使い方

- **検索語** — 空白区切りは AND 検索。`正規表現` チェックで regex、`大文字小文字` で厳密一致
- **言語フィルタ** — 検出された言語 (PDF 含む) で絞り込み / **パス絞り込み** — 例 `src/`
- 結果はファイルごとにヒット数順で並び、**行番号つき・ハイライト付き**で表示。
  「開く」で既定アプリ、📁 でエクスプローラー表示
- インデックスは `.git` / `node_modules` / `dist` などを自動除外、バイナリも自動判定で除外

## PDF 検索について

PDF は内蔵パーサーが FlateDecode / 無圧縮のコンテンツ ストリームを伸長し、
`Tj` / `TJ` / 16 進文字列のテキスト オペレータから本文を抽出します。
外部ライブラリ・ネットワーク不要。

**日本語の文字化け対策**: 日本語 PDF が使う CID フォント (Identity-H) では、
文字列の 2 バイトは Unicode ではなくグリフ ID のため、そのまま文字コード化すると
文字化けします。本パーサーは PDF 内の **`/ToUnicode` CMap** (`beginbfchar` /
`beginbfrange`) を解析して **CID → Unicode に変換**するため、日本語も正しく
索引・検索できます (Node=EXE / ブラウザ=APK 共通のロジック)。ブラウザ側 (APK) は
`DecompressionStream` で伸長し、`/Length` または末尾 EOL の調整で厳格な展開にも対応します。
画像だけのスキャン PDF や `/ToUnicode` を持たない一部 PDF はテキストを取れないことが
あります (その場合は検索対象から自動で外れます)。

## テスト

```
node sourcetree_search/tools/test-search.js
```

FlateDecode PDF の生成→抽出、言語判定、AND / 正規表現 / 大文字小文字 / 言語・パス
フィルタ、日本語検索、バイナリと `.git` の除外、さらに**単語補完エンジン**
(語彙構築 / 前方一致・部分一致補完 / 和文補完 / 補完語での全文検索)など 25 項目以上を
検証します。

```
node sourcetree_search/tools/test-cinevim.js
```

BadaCineVim エンジン(Vim モーション / 挿入・削除 / 検索 / ex コマンド / 読み取り専用)
35 項目を検証します。いずれも CI の `test-core` ジョブで実行。黒い大画面 UI と
CineVim オーバーレイは Playwright/Chromium のスモークテストで、ポップアップ出現→
候補選択→結果表示、および CineVim の起動→移動→挿入→保存→クローズまで確認済みです。
