# Bada in C — interpreter + compiler (native executables)

A from-scratch implementation of the **Bada language in C** (`bada.c`, ~600 lines,
pure C + libm). It is both an **interpreter** and a **compiler that emits native
executable files**, and it implements the requested ideas concretely:

| 要求 | 実装 |
|:--|:--|
| C言語でBadaを作る | `bada.c` — 字句/構文解析・評価器・ランタイムを C で実装 |
| 実行形式ファイルを作るコンパイラ | `bada build f.bada -o exe` → ソースを埋め込み cc でネイティブ ELF を生成 |
| インタープリタ | `bada run f.bada` / `bada repl` / `bada eval "..."` |
| 中枢トリガー = 多様体エントロピー不変量 | `xi(list)` / `thermal(net)` を `tgamma` で計算（言語の組込みトリガー） |
| オブジェクト指向のクラス | `class/new/method/send`（クラスもオブジェクトも cons リスト） |
| 多様体の熱エントロピー × クラス・ネットワーク | `thermal(weights)` がクラス網の不変量を返し選択を駆動 |
| リスト構造と同じデザインパターン | **すべてが cons リスト**（コード=データ、ホモイコニック） |
| 自己進化 | `evolve.bada` が Xi トリガーで新しい Bada ソースを生成→実行→コンパイル |

## ビルドと実行

```sh
make                              # cc bada.c -lm -o bada
./bada run examples/engine.bada   # インタープリタ
./bada build examples/engine.bada -o engine && ./engine   # ネイティブ実行形式
./bada repl                       # 対話
make test                         # 全テスト（ALL PASS）
```

`bada build` はランタイム `bada.c` の場所を `BADA_HOME` か実行ファイルの隣から探します。

## 言語

すべての値は数値・文字列・真偽・nil・**cons リスト**・関数・組込み。コードもリスト
（ホモイコニック）。構文は C 風：

```
def fib(n)
  if n < 2
    return n
  end
  return fib(n - 1) + fib(n - 2)
end
print "fib(10) = " + str(fib(10))
```

### 組込み（ランタイム）

- リスト構造: `list car cdr cons at len append`
- 多様体トリガー: `gamma beta xlogx element zeta_gauge entropy xi thermal`
- 数学: `exp log sqrt sin cos pow mod floor abs pi`
- オブジェクト（リスト上）: `class new method send get_slot set_slot class_name`
- 自己進化IO: `read_file write_file`

### オブジェクト指向（クラスもオブジェクトもリスト）

```
let Particle = class("Particle")
method(Particle, "energy", def(self)
  return get_slot(self, "mass") * pow(get_slot(self, "speed"), 2)
end)
let p = new(Particle)
set_slot(p, "mass", 2)
set_slot(p, "speed", 3)
print p.energy()                  # send 経由のディスパッチ
# クラス・ネットワークの熱エントロピー（中枢トリガー）
print thermal(list(18, 5, 4))
```

### 自己進化（Bada が Bada を書く）

`examples/evolve.bada` は多様体エントロピー不変量 `Xi` を計算し、しきい値を超えたら
新しい Bada プログラムを生成して書き出します。生成物は実行も**ネイティブコンパイル**も可能。

## 例

- `examples/engine.bada` — リポジトリのコア（ガンマ/不変量・健全な整除性証明・基底核選択）を C版 Bada で
- `examples/objects.bada` — クラス/オブジェクト（リスト）と熱エントロピー・トリガー
- `examples/evolve.bada` — 自己進化

## 正直な範囲

- これは Bada のコア方言の C 実装です。Ruby ホスト版 Bada（`../bada_ruby`）の全機能
  （NN 学習・正規表現トークナイザ等）を網羅するものではなく、言語の中核（リスト構造・
  OOP・多様体トリガー・インタプリタ＆コンパイラ・自己進化）を C で完全動作させたものです。
- 「コンパイル」はソース埋め込み＋ランタイムリンク方式で、出力は本物のネイティブ ELF
  実行形式です。完全な最適化ネイティブコード生成（直接の機械語トランスパイル）は今後の拡張。
- 「自己進化」は健全で有界（Bada が Bada ソースを生成し実行/コンパイルする）。無制限の
  自己改変や AGI 的主張ではありません。
