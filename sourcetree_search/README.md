# 🔎 Bada Search — SourceTree 付属 PDF・ソースコード検索エンジン (Windows 10/11)

Git GUI **SourceTree** の「カスタム操作」に登録して付属アプリとして使う検索エンジンです。
リポジトリを丸ごとインデックスし、**プログラミング言語のソースコード**(C/C++/JavaScript/
TypeScript/Python/Ruby/Java/Go/Rust/PHP/C#/Swift/Kotlin/Shell/SQL/HTML/CSS/Bada/OmegaScript
ほか 40 種以上)と **PDF の中身**(FlateDecode ストリームからのテキスト抽出 — 依存ライブラリ
ゼロ)を横断検索します。単体アプリとしても動きます。

## ⬇️ ダウンロード (Windows 10 / 11)

[Releases](https://github.com/masaaki-avnturle/Bada/releases) から:

| ファイル | 内容 |
|:---|:---|
| `BadaSearch-Setup-*-x64.exe` | NSIS インストーラ (インストール先変更可) |
| `BadaSearch-Portable-*-x64.exe` | インストール不要のポータブル版 |

ビルドは [`sourcetree-search-build.yml`](../.github/workflows/sourcetree-search-build.yml)
が自動実行します (`stsearch-v*` タグを push すると Release に添付、
または Actions の `workflow_dispatch` で `release_tag` を指定)。

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
`Tj` / `TJ` / 16 進文字列 (UTF-16BE 対応) のテキスト オペレータから本文を抽出します。
外部ライブラリ・ネットワーク不要。画像だけのスキャン PDF や CID フォント埋め込みの
一部 PDF はテキストを取れないことがあります (その場合は検索対象から自動で外れます)。

## テスト

```
node sourcetree_search/tools/test-search.js
```

FlateDecode PDF の生成→抽出、言語判定、AND / 正規表現 / 大文字小文字 / 言語・パス
フィルタ、日本語検索、バイナリと `.git` の除外など 15 項目を検証します
(CI の `test-core` ジョブでも実行)。
