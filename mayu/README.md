# 窓使いの憂鬱 (mayu) — クロスプラットフォーム版

**キーの再割り当てエンジン。** 本家「窓使いの憂鬱」(mayu / mad window user's yuutsu) の
`.mayu` 設定ファイル構文を解析し、キーの入れ替え・修飾キーの再定義・
キーシーケンス出力を行います。

- **Linux** — `evdev` で物理キーボードを掴み、`uinput` 仮想キーボードから再送出（実フック）
- **macOS / Windows / その他** — 同じ変換ロジックを **シミュレータ** として実行（`simulate`）

本家は Windows のカーネル型キーボードフィルタドライバでしたが、本実装は
純粋 Python で書かれ、変換ロジック（設定パーサ + 状態機械）を OS 非依存に保っています。
Linux では OS 依存部を evdev のデバイス grab で置き換えています。

---

## 特長

| 機能 | 対応 |
|:-----|:-----|
| `.mayu` 設定構文（`keymap` / `key` / `mod` / `include` / `def key` / `def alias` / `def subst` / `window`）| ✅ |
| 修飾子付き打鍵（`C-` `S-` `A-`/`M-` `W-`）| ✅ |
| don't-care 修飾子 `*`、キー解放トリガ `~` | ✅ |
| 修飾子の「消費」（`C-b = Left` で Control を出力に漏らさない）| ✅ |
| キーシーケンス出力（`C-k = S-End Delete`）| ✅ |
| CapsLock を Control に（`mod control += CapsLock`）| ✅ |
| キーマップの親子継承（`keymap Derived : Base`）| ✅ |
| Linux 実キーフック（evdev/uinput）| ✅ |
| 全OS共通シミュレータ | ✅ |

---

## クイックスタート

```bash
cd mayu

# 1) 設定を検証
python3 -m mayu.cli check examples/emacs.mayu

# 2) 打鍵をシミュレート（実キーボードは不要・全OS）
python3 -m mayu.cli simulate examples/emacs.mayu --keys "C-b C-f C-n C-p C-a C-e"
#   入力 : C-b C-f C-n C-p C-a C-e
#   出力 : Left Right Down Up Home End

# 3) キー名一覧
python3 -m mayu.cli keys --grep Left
```

`pip install -e .` すると `mayu` コマンドとして使えます。

```bash
pip install -e .
mayu simulate examples/vi-nav.mayu --keys "W-h W-j W-k W-l"
```

### Linux で実際にキーを再割り当てする

```bash
pip install evdev            # Linux のみ必要
sudo mayu list-devices       # 入力デバイスを確認
sudo mayu run examples/emacs.mayu           # 自動選択
sudo mayu run examples/emacs.mayu -d /dev/input/event3   # デバイス指定
```

`run` は物理キーボードを `grab`（占有）して OS への直接入力を止め、変換後のイベントを
仮想キーボードから送出します。停止は `Ctrl-C`。root もしくは `input` グループ + `/dev/uinput`
への書込権限が必要です。

---

## 設定ファイル (.mayu) の書き方

```mayu
# コメントは # から行末まで

# CapsLock を Control として使う（押している間だけ）
mod control += CapsLock

# 別ファイルを取り込む
# include "104.mayu"

keymap Global
  key CapsLock = &Ignore      # 単独打鍵は無効（修飾子としてのみ）
  key C-b = Left              # Control+b -> ←
  key C-f = Right
  key C-k = S-End Delete      # 1 打鍵 -> 複数キーのシーケンス
  key *C-A = Home             # * は他の修飾子を問わない
```

### 対応ディレクティブ

| 構文 | 意味 |
|:-----|:-----|
| `include "FILE"` | 別の設定ファイルを取り込む（二重取り込みは自動抑止）|
| `def key NAME = 0xNN` | 新しいキー名と keycode を定義 |
| `def alias NAME = KEY` | キーの別名を定義 |
| `def subst PAT = OUT ...` | 全キーマップ共通のフォールバック置換 |
| `mod MOD = KEY ...` | 修飾子に物理キーを割り当て（置換）|
| `mod MOD += KEY` / `-= KEY` | 割り当ての追加 / 削除 |
| `keymap NAME [ : PARENT ]` | キーマップ定義（親から継承）|
| `window NAME /regex/ : PARENT` | ウィンドウタイトル別キーマップ |
| `key PAT = OUT ...` | 打鍵の再割り当て（keymap 配下）|

修飾子: `S-`=Shift, `C-`=Control, `A-`/`M-`=Alt, `W-`=Windows。
前置 `*`=don't care、`~`=キー解放時。
組み込み関数: `&Ignore`（握りつぶす）、`&Default`（素通し）。

---

## 同梱例

| ファイル | 内容 |
|:---------|:-----|
| `config/default.mayu` | 最小設定（CapsLock を Control に）|
| `examples/emacs.mayu` | Emacs 風カーソル移動（C-b/f/n/p, C-a/e, C-k …）|
| `examples/swap-ctrl-caps.mayu` | CapsLock ↔ LeftControl の入れ替え |
| `examples/vi-nav.mayu` | Windows + hjkl で矢印（vi 風）|

```bash
make demo     # 主要な変換例をまとめて表示
make test     # テスト実行
make check    # 全 example を検証
```

---

## アーキテクチャ

```
入力イベント列
   │
   ▼
┌─────────────┐   .mayu   ┌──────────────┐
│  lexer      │◀──────────│  config      │  設定 (keymaps, mod割当, ...)
│ (字句解析)  │           │  (構文解析)  │
└─────────────┘           └──────┬───────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  engine          │  論理修飾子の遅延アサート
                        │  (状態機械)      │  ・修飾子の消費
                        └────────┬─────────┘  ・ホールド / シーケンス
                                 │
                ┌────────────────┴────────────────┐
                ▼                                  ▼
     ┌────────────────────┐            ┌────────────────────────┐
     │ SimulateBackend    │            │ EvdevBackend (Linux)   │
     │ 全OS・検証/デモ    │            │ evdev grab + uinput    │
     └────────────────────┘            └────────────────────────┘
```

| モジュール | 役割 |
|:-----------|:-----|
| `mayu/keys.py` | キー名 ↔ keycode（evdev 準拠）のテーブル |
| `mayu/lexer.py` | `.mayu` の字句解析（コメント・行継続・文字列）|
| `mayu/keyseq.py` | `C-b` 等のストローク表現と解析 |
| `mayu/config.py` | 構文解析 → `Config`（keymaps / mod / subst）|
| `mayu/engine.py` | 再割り当て状態機械（修飾子の消費・保持・シーケンス）|
| `mayu/backends/simulate.py` | 全OS共通シミュレータ |
| `mayu/backends/linux_evdev.py` | Linux 実キーフック |
| `mayu/cli.py` | `check` / `simulate` / `keys` / `run` / `list-devices` |

---

## テスト

```bash
python3 -m pytest tests/ -q     # 43 tests
```

字句解析・ストローク解析・構文解析・エンジン変換（修飾子消費、ホールド、
シーケンス、CapsLock→Control、down/up 均衡）を網羅しています。

---

## 制限

- ワンショット修飾子（CapsLock を「単打で Esc・長押しで Control」）は未対応
- ウィンドウ別キーマップ（`window`）の解析は行うが、切替はタイトル文字列の
  外部入力が前提（Linux 実フックでは既定の `Global` を使用）
- マウスイベント・IME 連携・`&` 関数の大半は未実装（`&Ignore` / `&Default` のみ）

## ライセンス

MIT
