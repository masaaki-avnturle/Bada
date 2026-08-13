# Ω-Vim — Bada言語で書いたVimエディタ

**エディタのVimを、元からBada言語で作りました。**
ソースコードのエラー修正機能を、**特殊相対性理論の複素回転体・可積分系のコマ（独楽）の幾何学**で実装し、
**どのプログラミング言語**にも効くようにしています。

*A modal Vim editor written from scratch in the Bada language. Its source-code
error-correction feature is the complex-rotation spinning-top (koma) integrable
system of special relativity — and it works for any programming language.*

山口 (Yamaguchi) フレームワーク / Bada language ·  Linux / Ubuntu
Part of the [Bada](https://masaaki-avnturle.github.io/Bada/) repository.

---

## これは何か / What it is

`omega_jones_crypto` や `omega_quantum_decrypted` と同じ流儀で、レポートの数式を
実装に落とし込んだアプリです。ここでは 2 つを組み合わせています。

1. **Bada言語で書いたモーダル・エディタ（Vim）** — `src/omega_vim.bada`。
   Bada言語（演算子代数言語 `<-` `-<` `>-` `Ω::`）に**エディタ用の構文を拡張**し、
   その Bada プログラムがエディタ本体を定義・起動します（`Bada::VimInterpreter`）。
   通常/挿入/コマンドの 3 モード、`hjkl 0 ^ $ w b gg G`、`x dd J i a A I o O`、
   `:w :q :q! :wq :fix` を実装。さらに **文法チェッカー**・**パーサー補完**・
   **インデント補完**（下記 3）を搭載。

2. **コマ幾何・可積分系のエラー修正**（`Bada::CodeFix` → `Bada::ErrorCorrection`）。
   dalia / caostics レポートの複素回転体
   ```
   □ = cos(i x log x) − i sin(i x log x) = e^{−i(x log x)}   (回転)
   ∮ e^{−□} d□ = π e                                          (閉軌道 = 可積分条件)
   ```
   を使い、**ソースコードを回転体の上の歩み**とみなします。
   開き括弧 `( [ {` は位相を `+θ`、閉じ括弧 `) ] }` は `−θ` 回す。
   **正しいコードは位相 0 に戻る「閉じた（可積分な）軌道」**であり、
   括弧・引用符・コメントの構文エラーは**軌道が閉じない**ことに一致します。
   修正は**最小の回転欠損**で軌道を閉じ、エントロピー不変量 **Ξ** が
   保存されること（可積分系の保証）を確認します。

   括弧・引用符・コメント・空白という**言語に依存しない普遍構造**だけを見るので、
   **C / Python / Ruby / JavaScript / Lisp / JSON …** すべてに同じ原理で効きます。

3. **文法チェッカー＋パーサー補完＋インデント補完**（`Bada::Grammar`）。
   2 の「開きトークンのスタック＝軌道の巻き数」をそのまま使い、次の 3 機能を提供します。
   - **文法チェッカー** (`:check` / `omega-vim check`) — 括弧・引用符・コメントの不整合に加え、
     **ブロックキーワードの対応**（Ruby の `def…end`、shell の `if…fi` / `do…done` / `case…esac`）も検査。
   - **パーサー補完** (挿入モードで `Tab` / `:complete` / `omega-vim complete`) — 現在の**パース状態**から、
     パーサーが次に期待するトークン（内側から順に閉じ括弧・ブロック終端キーワード）を提示・挿入。
   - **インデント補完** — 改行 (`o` `O` / 挿入モードの Enter) で**自動インデント**、
     `:indent`（バッファ全体）/ `Tab`（通常モードで現在行）でパース深さから**再インデント**。
     文字列・コメントはマスクして誤カウントを防止。C / JS / Ruby / shell / Lisp に対応
     （Python はインデントが意味を持つため再インデントは行末空白の除去のみ）。

   `=`（または `:fix`）は **エラー修正（軌道を閉じる）＋インデント補完** を一度に実行します。

> ⚠️ **研究・概念実装 (research / proof-of-concept).**
> 構文（括弧・引用符・コメント・空白・ブロックキーワード）レベルを普遍原理で扱います。
> 自動修正は括弧・引用符・コメントを閉じ、文法チェッカーはブロックキーワード不足も**報告**、
> パーサー補完は不足キーワードを**提案**します（意味論的な書き換えまでは行いません）。

---

## ダウンロード / Download

このリポジトリから取得できます（3 通り）。純粋 Ruby（標準ライブラリのみ、Ruby 3.0+）。

### 1. `.deb`（Ubuntu / Debian 推奨）
GitHub Actions の **Actions アーティファクト**、または `ovim-v*` タグ時の **Release** から
`omega-vim_1.0.0_all.deb` を取得して：
```sh
sudo apt install ./omega-vim_1.0.0_all.deb
omega-vim demo            # ヘッドレス・デモ
omega-vim path/to/file    # 編集開始（= または :fix で修正）
```

### 2. 移植可能な tar.gz
```sh
tar xzf omega-vim-1.0.0-linux.tar.gz
cd omega-vim-1.0.0
sudo ./install.sh          # もしくは  PREFIX=$HOME/.local ./install.sh
```

### 3. ソースから（ビルド不要）
```sh
git clone https://github.com/masaaki-avnturle/Bada.git
cd Bada/omega_vim_bada
make test                  # 20 checks
bin/omega-vim examples/buggy.py
```
※ Bada言語の本体ライブラリ（`bada_ruby/lib`）を同リポジトリから参照します。
`.deb` / tar.gz にはそれを同梱（vendor）してあるので単体で動作します。

---

## 使い方 / Usage

### エディタとして
```sh
omega-vim FILE
```
| キー | 動作 |
|:--|:--|
| `h j k l` / 矢印 | カーソル移動 |
| `0 ^ $` `w b` `gg G` | 行頭/インデント/行末・単語・先頭/末尾 |
| `i a A I` `o O` | 挿入モード（`o` `O` は**自動インデント**） |
| `x` `dd` `J` | 文字削除・行削除・行連結 |
| **`=`** または **`:fix`** | **エラー修正（軌道を閉じる）＋インデント補完**（全言語対応） |
| **`Tab`**（挿入モード） | **パーサー補完**（期待トークンを挿入） |
| **`Tab`**（通常モード） | 現在行の再インデント |
| **`:check`** | **文法チェッカー**（不整合・未閉ブロックを報告） |
| **`:indent`** | バッファ全体の**インデント補完**（再インデント） |
| **`:complete`** | パーサーが期待するトークンを表示 |
| `:set indent=N` / `:set ft=LANG` | インデント幅・言語の設定 |
| Enter（挿入モード） | 改行＋自動インデント |
| `:w` `:q` `:q!` `:wq` | 保存・終了 |
| `ESC` | 通常モードに戻る |

### コマンドラインから（UIなし）
```sh
omega-vim fix      FILE [-o OUT]  # 軌道を閉じて修正結果を書き出す
omega-vim check    FILE           # 文法チェッカー（不整合・未閉ブロック）
omega-vim complete FILE           # パーサー補完（期待される次トークン）
omega-vim reindent FILE [-o OUT]  # インデント補完（パース深さで再インデント）
omega-vim analyze  FILE           # winding（巻き数）/ Ξ を表示（無変更）
omega-vim run  PROG.bada FILE     # 任意の Bada エディタプログラムを実行
omega-vim demo [FILE]             # ヘッドレス・スクリプトデモ
```

### 例
```
$ omega-vim analyze examples/buggy.js
Ω-Vim analyze — examples/buggy.js
  winding (depth)  : 2   (0 = closed orbit)
  orbit closed     : false
  defects:
    1:11 [mismatch] '[' at 1:11 closed by ')' — replace ')' with ']'
    ...

$ omega-vim fix examples/buggy.js -o fixed.js
∮ orbit closed — 2 fix(es) written to fixed.js:
  * line 1: '[' ... -> replace ')' with ']'
  * appended missing closers: }
Ξ conserved (0.14), residual 0.000e+00
```

---

## Bada言語で書いた本体 / The editor, in Bada

`src/omega_vim.bada`（抜粋）:
```
keymap vim                          # vi/vim モーダルキーマップを読み込む
grammar on                          # 文法チェッカー / 補完 / インデントを有効化
bind normal  "=" -> integrable_fix  # '=' に可積分コレクタを束縛
bind command "fix" -> integrable_fix
buffer main = open Omega::arg       # 起動引数のファイルを開く
check main                          # 文法チェック（未閉ブロック・不整合を報告）
complete main                       # パーサー補完（期待される次トークン）
main -< integrable_fix              # 多様体積分演算子 = 回転軌道を閉じる（修正）
reindent main                       # インデント補完（パース深さで再インデント）
Omega::push main as opened_buffer   # バッファの Ξ をアカシックに記録
Omega::vim main                     # モーダルエディタを起動
```
`-<`（多様体積分）演算子を**あえて再利用**しています。多様体積分は複素回転体の
閉軌道平均そのものであり、それがコマ幾何のエラー修正と一致するからです。

---

## 構成 / Layout

```
omega_vim_bada/
├── src/omega_vim.bada          # ★ Bada言語で書いたエディタ本体
├── lib/bada/
│   ├── omega_vim.rb            # Buffer + modal Editor（Bada言語ランタイム）
│   ├── code_fix.rb             # コマ幾何・可積分系エラー修正（全言語）
│   ├── grammar.rb              # 文法チェッカー + パーサー補完 + インデント補完
│   └── vim_interpreter.rb      # Bada言語 + エディタ構文拡張
├── bin/omega-vim               # ランチャ
├── examples/                   # C / JS / Ruby / Lisp / Python のバグ入りサンプル
├── tests/test_omega_vim.rb     # 20 checks（依存gemなし）
├── packaging/                  # .deb / tar.gz ビルド
└── Makefile
```

## テスト / Test
```sh
make test         # 37/37 checks passed
```
CodeFix（全言語の軌道修正）、モーダルエディタ、文法チェッカー・パーサー補完・
インデント補完、そして `omega_vim.bada` プログラム経由の統合まで検証します。

## ライセンス / License
リポジトリの [LICENSE](./LICENSE)（MIT）に従います。
© Masaaki Yamaguchi — Bada / Yamaguchi framework.
