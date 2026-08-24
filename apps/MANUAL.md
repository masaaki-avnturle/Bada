# Bada 取扱説明書

**BadaTelegraph — 7エンジン思考入力計器群（Android / Windows 10・11 / Ubuntu / CLI）**

- 精度基準: **silent-talk 0.92 超**
- 入力方式: **発声・打鍵なし（思考／ウィスパード）**
- 実装: Ruby ＋ Java（共有コア・同一入力でバイト一致）
- 区分: **生成シミュレーション**

---

## 1. 概要と安全上の注意

Bada は、**発声もタイプもせずに**文章・ソースコード・論文・チャット応答を入力する「サイレント入力」の実験機です。すべての入力機能は基準精度（silent-talk 相当の 92.0%）を**上回る精度**で動作するよう設計されています。

| エンジン | 機能 |
|---|---|
| ① 宇宙電信 | 量子もつれペアの物理証明つきメッセージ送信 |
| ② 擬似量子計算機（QC） | ディスク内蔵ノイマン型の擬似 QC。半導体 Verilog ソースも生成 |
| ③ 思考言語化（Mind） | 信号から思考の言語化・心像・脳内コードを合成 |
| ④ コード生成（Coder） | 意図から言語自動判定つきでプログラムを生成 |
| ⑤ サイレント入力 IME | 手がかりを各エンジンの文章・ソースに言語化 |
| ⑥ ウィスパード（Whisper） | 母音を落とした英語や未知言語を完全文へ復元 |
| ⑦ Bada Vim | 構文ハイライト付き全画面モーダルエディタ。思考コマンドで Bada 言語をプログラミング |
| ⑧ ChatΩ | Jones 多項式×ガンマ多様体の AGI 自己進化チャット（chatGPT 進化版） |

> **重要**: 本製品は**生成シミュレーション**です。実際の脳波・思考を読み取る BCI ではなく、ChatΩ も実在の AGI ではありません。「思考入力」は量子シード駆動の決定的サンプラが多様体プライアから語を捕捉する演出であり、表示される精度もシミュレーション上の指標です。

## 2. 入手とインストール

配布物は [latest リリース](https://github.com/masaaki-avnturle/Bada/releases/tag/latest) から入手できます。

| プラットフォーム | ファイル | 手順 |
|---|---|---|
| Android | `BadaTelegraph.apk` | 端末に転送して開き、「提供元不明のアプリ」を許可してインストール |
| Windows 10/11 | `BadaTelegraph-1.0.exe` | ダブルクリックでインストール。スタートメニューから起動 |
| Windows（ポータブル） | `BadaTelegraph-windows-x64.zip` | 展開して `BadaTelegraph\BadaTelegraph.exe`（Java 同梱） |
| Ubuntu（.deb） | `badatelegraph_1.0_amd64.deb` | `sudo apt install ./badatelegraph_1.0_amd64.deb` → `/opt/badatelegraph/bin/BadaTelegraph` |
| Linux（ポータブル） | `BadaTelegraph-linux-x64.tar.gz` | 展開して `BadaTelegraph/bin/BadaTelegraph`（Java 同梱） |
| CLI（Ruby 版） | リポジトリ `bada_ruby/` | Ruby 3.x・依存なし。`ruby -Ilib bin/bada <コマンド>` |

## 3. 起動方法

**GUI**: そのまま起動するとタブ（①〜⑧）が開きます。

**デスクトップのフラグ**:

| フラグ | 動作 |
|---|---|
| `--gui`（既定） | GUI を起動 |
| `--qc` | 擬似 QC のデモ実行（Bell 回路） |
| `--mind "信号"` | 思考言語化 |
| `--silent "手がかり | :code | …"` | サイレント IME（`|` で行区切り） |
| `--code "意図"` | コード生成 |
| `--whisper "qntm lght wv"` | ウィスパード復元（長長文レポート） |
| `--latex "主題"` / `--math "主題"` | pLaTeX 論文／数学論文 |
| `--agi "質問"`（`--chat`） | ChatΩ 自己進化チャット |
| `"MESSAGE"`（フラグなし） | 宇宙電信で送信・証明 |

**Android**: スピナーで ①宇宙電信〜⑨ChatΩ を切替。モードを選ぶとデモ入力が自動セットされます。

## 4. 共通入力ボタン

- **🧠 思考入力** — 押すだけで（手がかりも不要）思考を捕捉し、その欄に合った内容を入力。押すたびに別の思考。
- **🧠 英語思考入力** — 英語モードの単語を思考から捕捉し、正確な英語で入力。
- **🔉 ウィスパード英語** — **全画面の複数行エディタ**が開く。ウィスパード英語を複数行そのまま打鍵し、**⚡ 一括復元**（Ctrl+Enter）で複数行を一辺に・一瞬で完全な英語へ復元 → 「確定してこの欄へ」。エディタ内の 🧠 思考入力ボタンで打鍵も不要。

## 5. 各エンジンの使い方（要点）

- **① 宇宙電信**: メッセージ＋材料・温度・冗長度 → 「送信・証明」。Bell/CHSH・Jones 相関つきレポート。
- **② 擬似QC**: BadaQASM（`H 0; CX 0 1; HALT`、`bell`/`ghz`）を実行。「Verilog」で半導体 RTL 生成。
- **③ 思考言語化**: 対象＋信号 → 言語化・心像・脳内アプリの Bada ソース。
- **④ コード生成**: 英日どちらの意図でも言語自動判定してコード生成。
- **⑤ サイレント IME**: 1 行ずつ言語化。`:qc` 等で出力先を切替（第 8 節）。
- **⑥ ウィスパード**: `qntm lght wv` → *quantum light wave*。未知言語も英語へ。既定で 10〜16 文の長長文レポート。
- **⑧ ChatΩ**: プロンプト → 「進化して応答」。世代ごとの fitness・Jones 値・組みひも語を表示し、基準超えの整合精度で応答。

## 6. Bada Vim エディタ

**ノーマルモードのキー**: `i a o O`（挿入）・`W`（ウィスパード英語挿入モード）・`x` `dd`（削除）・`h j k l 0 $ gg G`（移動）・`:`（ex コマンド行）。INSERT からは `Esc` で戻る。

**ウィスパード英語挿入**: `W` で入り複数行を打鍵 → `Esc` で打鍵した複数行を一辺に一括復元。`:burst` はバッファ全体、`:burst a;b;c` は `;` 区切りを一度に復元。

**ex コマンド**:

| コマンド | 動作 |
|---|---|
| `:w [file]` / `:q` / `:wq` | 保存／終了 |
| `:d` / `:%d` | 行削除／全消去 |
| `:set ft=…` | filetype 切替（bada/verilog/qasm/latex/coder） |
| `:think` | 思っただけのコマンドを 1 手適用 |
| `:thinkprog [n] [en|ja]` | 思考コマンドだけで Bada プログラムを書く（既定 8 手） |
| `:kw <キーワード>` | キーワードのコマンド入力 |
| `:lang en` / `:lang ja` | 英語モード／日本語（print文関係のみ）の使い分け |
| `:bada` / `:qc` / `:verilog` / `:math` / `:latex` / `:report` / `:whisper` / `:whisperen` | 各生成物をカーソル位置に挿入 |
| `:burst [a;b;…]` | 複数行の一括ウィスパード復元 |

ツールバーの 🔩 半導体・⚛ QC・🧩 Bada・📄 数学論文・📝 レポート ボタンは対応する ex コマンドを実行します。

## 7. 思考コマンドと言語の使い分け

**🧠 思考コマンド**は 1 手、**🧠 思考プログラミング (Bada)** は 8 手の思考コマンドで、`set` → `<-` 束縛 → `Omega::push` → `print` のライフサイクルを持つ**文法検証済み（Bada✓）**のプログラムを書き上げます。

**キーワード表（`:kw`）**: `set/代入`・`assign/束縛`・`push/送出`・`print/表示`・`delete/削除`・`top/先頭`・`bottom/末尾`・`save/保存`・`english/英語`・`japanese/日本語`

**使い分け（`:lang`）**:
- 予約語（`set`/`print`/`push`/`as`/`Omega::`）と演算子は**常に正確な英語**
- `en` モード（既定）: 文字列も英語語彙から直接引いた正確な英語（precision 0.96 以上）
- `ja` モード: **print 文関係の文字列リテラルにだけ日本語**

## 8. サイレント入力 IME のモード

`:text` 文章 / `:code` ソース / `:qc` QC＋実行 / `:verilog` 半導体 / `:telegraph` 宇宙電信 / `:bada` Bada 構文 / `:whisper` 英語復元 / `:report` 長長文レポート / `:latex` `:math` 論文

## 9. CLI リファレンス（`bin/bada`）

| コマンド | 動作 |
|---|---|
| `bada silent` | サイレント IME（対話） |
| `bada whisper "qntm lght wv"` | ウィスパード復元 |
| `bada vim [file]` | Bada Vim（第 6・7 節の ex すべて対応） |
| `bada agi "質問" [--gen 8] [--pop 12]` | ChatΩ |
| `bada latex "主題"` / `bada math "主題"` | 論文生成 |
| `bada code "意図" [--lang python]` | コード生成 |
| `bada qc [bell|ghz|run f.qasm]` | 擬似 QC（`qc verilog` で RTL） |
| `bada mind "信号"` / `bada quantum "MSG"` | 思考言語化／宇宙電信 |

## 10. 精度・決定性・免責

- **精度**: すべてのサイレント入力は `SILENT_TALK_BASELINE = 0.92` を上回るよう床上げされ、`precision X% > silent-talk 92.0%` と表示されます。
- **決定性**: 思考捕捉・思考コマンド・ChatΩ は量子シード駆動の決定的 PRNG（nonce 付き）。同じ nonce で同じ結果。Ruby 版と Java 版はバイト一致。
- **検証**: 思考プログラミングの出力は Bada インタプリタ／文法規則で、数学論文は `\begin`/`\end` 対応で検査されます。

> **免責**: すべての「思考入力」「ウィスパード復元」「AGI 自己進化」は計算による生成シミュレーションであり、人の脳・思考・発話を実際に読み取る機能はありません。
