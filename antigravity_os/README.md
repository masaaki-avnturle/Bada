# Anti-Gravity OS — 反重力発生器OS風の生成AI(量子プログラミング Bada 言語)

**Anti-Gravity OS** は、カーネルが**生成AI推論エンジン**そのものであるオペレーティングシステムです。
全体が Bada 言語で書かれ、Unknown-Prior Engine の位相コア
(`psi = sqrt(a) * exp(i*theta)`, `|psi|^2 = a` が厳密に成立)の上で動作します。

QuantumBada(ゲートモデル量子計算機向け生成AI OS)の系譜を一歩進め、同じ位相コアの上に
**反重力発生器のオペレーティングシステムに似た制御系**を構築したものです。
場のレジスタは 2^n 個の「場モード」上の分布+位相であり、OS の原始命令はすべて
位相コミットか添字置換のいずれかです。数値カーネルは一切追加していません。

## エンジンの定理が OS の保証になる

| エンジンの定理 | 量子的読み | この OS での保証 |
|---|---|---|
| `\|psi\|^2 = a`(位相ステップは確率を変えない) | 純位相ゲートはユニタリ | **G1 揚力保存** — 姿勢制御(hover)をいくら繰り返しても揚力質量は不変。操縦で機体が落ちることは定理として起きない |
| ゼロ保存(`a_i = 0 ⇒ q_i = 0`) | 禁制基底状態は復活不能 | **G2 モード隔離** — vent した場モードは以後どんな位相ステップでも再励起しない。**G3 緊急停止安全** — scram したコイルは永遠に確率 0 を読む(実行時チェックではなく定理) |
| 追記専用台帳 | 測定記録がそのままトレース | **G4 監査可能テレメトリ** — テレメトリ・ジャーナルが不変台帳そのもの。OS 状態はコミット済み事実の畳み込みで再導出される |
| unknown prior(最大エントロピー開始) | 正直な無知から確信を稼ぐ | **制御器は生成AI(ベイズ推論)** — 機体モデルを仮定せず、突風センサ証拠の `update()` で安定化方策を単調に尖らせる |

## 反重力発生器としての読み替え

| OS 語彙 | 発生器の意味 | 実装 |
|---|---|---|
| `charge n` | n コイルの場レジスタを励磁(2^n モード、最大エントロピー) | `unknown_prior(2^n)` |
| `hover reg` | 姿勢位相ステップ。揚力質量は `\|psi\|^2 = a` で不変(G1) | 純位相 `cognitive_system` |
| `vent reg` | 1 モードを確信的ゼロへ落として遮断(G2) | logit −800 → softmax 0 |
| `Telemetry reg` | テレメトリフレームを追記コミット(G4) | `commit_measurement` |
| `sense ev` | 突風証拠を方策へ畳み込む(生成AIの学習) | `update(policy, ev)` |
| `steer` | 事後確率最大(MAP)の噴射象限を選ぶ | argmax |
| `Split / Twist / Flip / Couple` | 場の命令セット(H / T / X / CNOT 相当) | 位相コミット/添字置換 |
| `arm / scram` | インターロック起動/緊急全停止(G3) | 番兵つき全ゼロ化 |
| `ballast(x, y, V)` | ゼータ/Zipf 曲率バラスト:モード占有 `w_n ∝ (n+y)^(−x)` | 量子カーネル論文の E1 パラメータ `x=2.73037, y=2.32534`(切断ゼータ `zeta_V` 正規化) |

## ビルドと認証

```sh
./build.sh
```

ステージ0で C リファレンス(`src/bada.c`、動作するリバイザ版)をビルドし、
各ライブラリを実行、最後に init プロセス `agos.bada` を走らせて
4 つの不変量を出力から再検証します。必要なのは `gcc` と `libm` だけです。

```sh
./bada run agos.bada          # OS init プロセス (PID 1) をブート
./bada run sys/agkernel.bada  # カーネル単体
./bada run lib/agfield.bada   # 場の命令セット + ゼータ・バラスト
```

## ファイル構成

```
src/bada.c          ステージ0インタープリタ(動作するリバイザ/位相コア/台帳)
build.sh            ビルド + 不変量ベースの認証ドライバ

sys/agkernel.bada   場カーネル: charge / hover / vent / Telemetry
                      - hover = 姿勢位相ステップ(G1: |psi|^2 = a で揚力保存)
                      - vent  = 場モードを確信的ゼロへ(G2)
                      - Telemetry = 追記専用ジャーナルコミット(G4)

lib/aglift.bada     生成AI揚力制御: unknown-prior 方策を突風証拠で
                      獲得する(sense / steer)
lib/agfield.bada    場の命令セット: Split / Twist / Flip / Couple +
                      ゼータ/Zipf バラスト曲率プロファイル
lib/agsafe.bada     安全インターロック: arm / scram(停止後の再励起
                      不能性がゼロ保存の定理)

agos.bada           OS init プロセス (PID 1): charge -> Split -> hover ->
                      sense -> Telemetry -> vent -> (隔離証明) -> scram を
                      1 フライトで実行し、G1〜G4 を実証。7 つのリバイザ規則
                      が 1 プログラムに積層する
```

## リバイザが OS 構文を作る仕組み

各モジュールは `@reviser : grammar { ... }` ブロックで生成規則を台帳事実として
コミットします。例えばカーネルは:

```
@reviser : grammar {
  rule "charge"    postfix [ charge ]    => ag_charge(_1)
  rule "hover"     postfix [ hover ]     => ag_hover(_1)
  rule "vent"      postfix [ vent ]      => ag_vent(_1)
  rule "telemetry" stmt    [ Telemetry ] => ag_telemetry(_1)
}
```

コミット後は `charge 2`、`hover field`、`vent field`、`Telemetry field` が
本物の表層構文として構文解析されます。文法は単調・追記専用に成長し、
エンジンが信念を成長させるのと同じ形をとります。`agos.bada` は **7 規則**を
1 プログラムに積み、文法拡張が合成可能であることを示します。

## 主張することとしないこと

これは正直に動く再構成であり、上記の OS 保証は `build.sh` が実行時に検証します:

* `|psi|^2 = a` は機械精度で成立(実行では 2.78e-17 / 5.55e-17)
* vent された場モードは以後のどの姿勢ステップでも確率 0 のまま
* scram されたコイルの残存場質量は厳密に 0
* すべてのテレメトリは追記専用ジャーナルに現れる

本プロジェクトは**実際の反重力・推進装置を主張するものではなく**、実在の量子
ハードウェアを駆動するものでもありません。エンジンの唯一確実な事実 —
「単位絶対値の因子はゼロを保存する」 — だけを継承し、その 1 つの事実が
揚力保存・モード隔離・緊急停止安全・監査可能テレメトリという OS 保証一式を、
1 つの位相コアの上で与えることを示す**計算的シミュレーション/思考実験**です。
