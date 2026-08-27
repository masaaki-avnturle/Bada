# MadoKey (窓使いのキー) — Word / Excel / LibreOffice のキーバインド常駐ツール

奈由太氏の **「窓使いの憂鬱」** へのオマージュ。設定ファイル `madokey.mayu` に
書いたキーバインドを常駐で待ち受け、**前面のアプリ (Word / Excel / LibreOffice
Writer / Calc) を自動判定**して、**ルビ付け・合計・コピー・任意コマンド**を
「ひと押し」で送り込みます。行を書き換えるだけで**独自のキーバインド**に
できます。

- 🪟 **Windows 10 / 11**: Word・Excel（`pip install pynput pywin32 psutil`）
- 🐧 **Ubuntu**: LibreOffice Writer・Calc（`pip install pynput` + `python3-uno`）
- 🖱️ **設定エディタ (単一HTML)**: [`dist/madokey.html`](../dist/madokey.html) を
  ブラウザで開き、キーバインドを画面で編集 → `madokey.mayu` / `madokey.ahk`
  として書き出し（インストール不要・オフライン）。

## すぐ使える初期バインド (madokey.mayu)

| キー | 対象 | 動作 |
|---|---|---|
| **Ctrl+Alt+R** | Word / Excel / Writer | **ルビ**（ふりがな。よみは IME/エンジンが自動補完） |
| **Ctrl+Alt+S** | Excel / Calc | **合計**（Excel=Alt+= オートSUM / Calc=`.uno:AutoSum`） |
| **Ctrl+Alt+C / X / V** | すべて | コピー / 切り取り / 貼り付け |
| **Ctrl+Alt+B** | Word / Excel | 太字（リボン `ExecuteMso("Bold")`） |
| **Ctrl+Alt+H** | Word | 蛍光ペン |
| **Ctrl+Alt+M / D** | すべて | 定型文の挿入（住所 / 【重要】） |
| **Ctrl+Alt+F5 / F12** | — | 設定の再読込 / 終了 |

## 動かし方

```sh
pip install -r requirements.txt        # pynput (必須), Windows は pywin32/psutil
python madokey.py                      # madokey.mayu を読み込み常駐
python madokey.py -c my.mayu           # 別の設定ファイル
python madokey.py --check              # 設定を解析して一覧表示（常駐しない）
python madokey.py --emit-ahk madokey.ahk   # AutoHotkey v1 スクリプトを書き出し
```

- **Windows で Python を使いたくない場合**: `--emit-ahk` で生成した
  `madokey.ahk` を [AutoHotkey v1](https://www.autohotkey.com/) で実行すれば、
  同じキーバインドが常駐します（`ExecuteMso` も COM 経由で動作）。
- **Ubuntu で LibreOffice の `uno`/`sum(Calc)`/`ruby(Writer)` を使う**には、
  UNO 接続を有効にした状態で起動しておくと確実です:
  ```sh
  soffice --calc --accept="socket,host=localhost,port=2002;urp;"
  ```
  （`python3-uno` パッケージも必要: `sudo apt install python3-uno`）

## 設定ファイルの書式 (madokey.mayu)

```
bind <修飾>+<キー> [@対象] = <アクション> [引数]
```

- **修飾**: `Ctrl` / `Alt` / `Shift` / `Win`（`+` でつなぐ・大文字小文字は無視）
- **対象** `@word` `@excel` `@writer` `@calc` `@any`（省略時 `any`）。前面アプリを
  自動判定し、一致するバインドを優先。
- **アクション**:
  - `ruby` … ルビ（Word=`PhoneticGuide` / Excel=`PhoneticShowOrHide` / Writer=`.uno:RubyDialog`）
  - `sum` … 合計（Excel=`Alt+=` / Calc=`.uno:AutoSum`）
  - `copy` / `cut` / `paste`
  - `mso <IdMso>` … 任意の Office リボン コマンド（Windows, Word/Excel）
  - `uno <.uno:Cmd>` … 任意の LibreOffice コマンド（Writer/Calc）
  - `keys <combo>` … 任意のキー送出（例 `keys Ctrl+Shift+V`）
  - `text <文字列>` … 定型文の挿入
  - `run <コマンド>` … 外部コマンドの実行
  - `reload` / `quit` … MadoKey 自身の操作

行末 `#` 以降はコメント。**この 1 ファイルを書き換えるだけ**で独自バインドに
変更できます。

## しくみ

- キー待ち受け・キー送出は **pynput**。`Ctrl+Alt+<X>` 系を使うのでアプリ本来の
  キーを奪いません。
- 前面アプリの判定: Windows は前面ウィンドウのプロセス名 (WINWORD/EXCEL/soffice)、
  Linux は `xdotool`/`xprop` のアクティブ ウィンドウ名。
- 実行: `copy`/`keys`/`text`/`sum(Excel)` はキー送出（追加設定なしで動作）、
  `mso` は Word/Excel の COM `CommandBars.ExecuteMso`、`uno`/`sum(Calc)`/
  `ruby(Writer)` は起動中 LibreOffice への UNO dispatch。

## 入手

設定エディタ `dist/madokey.html` は
[`apps-dist.yml`](../../.github/workflows/apps-dist.yml) のバンドルに含まれ、
Actions の Artifacts から取得できます。常駐本体（`madokey.py` / `madokey.mayu` /
`requirements.txt`）はこのフォルダをそのままダウンロードしてください。
