# omega_iq_telomere_pkg — Bada 赤外線IQ・テロメア分裂測定アプリ

> 上の写真の絵を方程式化し、赤の矢印の方向の線の順番に基づいて、Jones多項式の
> テロメアの分裂過程を、タブレットの赤外線カメラと温度計で駆動し、IQ を測定する
> 独自アプリケーションを **Bada言語** で書き、**apk パッケージ** として組み立てたもの。
> さらに **真逆(mirror)の性質**（V(t) ↔ V(1/t)、上がる作用 ↔ 下げる作用）を内蔵する。

Turn the drawing into equations, read its lines in the red-arrow order, run the
Jones-polynomial **telomere splitting** process, drive it with the tablet's
**infrared camera + thermometer**, and measure an **IQ** — written in the repo's
**Bada language** and assembled as an **APK-format package**, with the framework's
**真逆 (mirror) property** built in.

---

## パイプライン / Pipeline

```
 写真の絵                赤の矢印の順               Jones多項式
 (bond-lines)  ──▶  drawing → equations  ──▶  V(t) = Kauffman bracket
                    lib/omega_iq/drawing.rb     lib/omega_iq/jones.rb
                          │                            │
                          │                            ├──▶ 真逆  V(1/t)   (mirror knot)
                          ▼                            ▼
                    テロメア分裂 (skein)         赤外線カメラ + 温度計
                    lib/omega_iq/telomere.rb     lib/omega_iq/thermal.rb
                          │                            │
                          └──────────────┬─────────────┘
                                         ▼
                                     IQ測定 (順 + 真逆)
                                   lib/omega_iq/iq.rb
```

| ステップ | 意味 | 実装 |
|:--|:--|:--|
| 1. 絵の方程式化 | 絵の bond-line 群を赤矢印の順に閉じた折れ線として読み、各線の媒介変数方程式を出し、自己交差を交点として抽出して結び目図に変換 | `drawing.rb` |
| 2. Jones多項式 | Kauffman括弧の状態和を Laurent 多項式で計算し、writhe で正規化して V(t) | `jones.rb` |
| 3. 真逆の性質 | 各交差の上下を反転（=鏡像結び目）。その Jones多項式は V(1/t)。Na↔K・上がる作用↔下げる作用の結び目理論的対応 | `jones.rb` `Jones.mirror` |
| 4. テロメア分裂 | 先頭（テロメア）交差を skein 関係で A/B 平滑化し二娘図へ分裂。世代ごとに交差が1つ減る（Hayflick 段）。senescence=結び目が解ける。分裂エントロピー（bit）も算出 | `telomere.rb` |
| 5. 赤外線カメラ+温度計 | タブレットの IR フレーム(P2 PGM)と温度計を読み、平均温度・空間コヒーレンス・Boltzmann 評価点 `t_eval = exp(-Θ/T)` を得る | `thermal.rb` |
| 6. IQ測定 | complexity(Jones次数幅)・magnitude(|V(t_eval)|)・entropy(分裂)・coherence(熱)を合成し、平均100・標準偏差15に標準化。順と真逆の両方 | `iq.rb` |

---

## ダウンロード / Download

- **GitHub Release**（推奨）: リポジトリの **Releases** ページから `bada_iq.apk` をダウンロード
  → https://github.com/masaaki-avnturle/Bada/releases
  `bada-iq-*` タグを push すると、GitHub Actions（`.github/workflows/release-apk.yml`）が
  テストを実行し apk をビルドして Release にアセットとして添付する。Actions タブから手動実行も可能。
- **直リンク**（このブランチのコミット済み apk）:
  https://github.com/masaaki-avnturle/Bada/raw/claude/jones-polynomial-telomere-py9vra/omega_iq_telomere_pkg/dist/bada_iq.apk

## 実行 / Run

```sh
make test     # 19 の単体テスト (Ruby のみ、外部 gem 不要)
make run      # Bada アプリ app/main.bada を直接実行
make apk      # dist/bada_iq.apk を組み立てて Bada ランタイムで起動
make package  # apk を作るだけ (起動しない)
```

`app/main.bada`（Bada言語ソース）:

```
set diagram = "assets/diagram_arrows.txt"
set thermal = "assets/thermal_frame.pgm"
load  drawing from diagram   # 絵 -> 方程式
jones                        # Jones多項式
mirror                       # 真逆 V(1/t)
split telomere               # テロメア分裂
sense thermal from thermal   # 赤外線カメラ + 温度計
measure iq                   # IQ測定 (順 + 真逆)
report
```

### 出力例 / Sample output

同梱の絵（赤矢印順に読むと五芒星＝ **cinquefoil 5₁** 結び目）に対して:

```
[2] Jones多項式   from 5 crossings, writhe 5
    V(t)      = - t^7 + t^6 - t^5 + t^4 + t^2
    真逆 V(1/t) = t^-2 + t^-4 - t^-5 + t^-6 - t^-7      # = 標準 5_1 の Jones多項式
[3] テロメア分裂  Hayflick limit = 5 divisions ... split entropy = 2.0471 bits
[4] 赤外線カメラ + 温度計  mean temp = 37.27 degC  coherence = 0.9719  t_eval = 0.380434
[5] IQ (順) = 112.7   IQ (真逆) = 113.8   真逆 divergence = 1.1
```

`test/test_iq.rb` は、この Jones多項式が既知の 5₁ 結び目のものと一致することを検証する。

---

## APK について / About the APK

`dist/bada_iq.apk` は Android パッケージ（ZIP）の標準レイアウト
（`AndroidManifest.xml` · `bada_apk.json` · `app/` · `lib/` · `assets/` · `res/` ·
`META-INF/`）で組まれた **APK 形式パッケージ**である。`file` コマンドは
`Android package (APK), with AndroidManifest.xml` と認識する。

コンパイル済み `classes.dex` の代わりに **Bada ランタイム**
（`lib/omega_iq` + `app/main.bada`）を同梱しており、BadaOS ランタイム／デスクトップ上で
`bin/run_iq`（`run.sh`）から実行できる。実タブレットでは `MeasureActivity` が
赤外線カメラ(`/dev/badaos/ir0`)と温度計を読み、デスクトップでは同梱の
`assets/thermal_frame.pgm` にフォールバックする。

> 注: これは Play ストア署名済みの Dalvik バイナリ APK ではなく、Android の APK
> レイアウトに従った Bada ランタイム用パッケージ。この点を正直に明記しておく。

---

## ファイル構成

```
omega_iq_telomere_pkg/
├── AndroidManifest.xml      APK マニフェスト (赤外線カメラ/温度計の権限, Bada entry)
├── bada_apk.json            Bada APK 記述子 (pipeline / sensors / 真逆 property)
├── build_apk.sh             .apk (zip) 組み立て + SHA-256 マニフェスト
├── run.sh                   apk を展開して Bada ランタイムで起動
├── Makefile                 test / run / apk / package / clean
├── app/main.bada            Bada言語アプリ本体
├── lib/omega_iq/            エンジン (drawing, jones, telomere, thermal, iq, bada_runtime)
├── assets/
│   ├── diagram_arrows.txt   絵の bond-line + 赤矢印順 (五芒星 = 5_1)
│   └── thermal_frame.pgm    赤外線カメラのサンプルフレーム (P2 PGM)
├── res/values/strings.xml   文言リソース
├── bin/run_iq               ランチャ (MeasureActivity 相当)
└── test/test_iq.rb          単体テスト (Ruby, gem 不要)
```

## 自分の絵で試す / Use your own drawing

`assets/diagram_arrows.txt` を編集する:

```
# S id x1 y1 x2 y2   … 絵の線 (bond)
S 0  0.0 1.0  0.5878 -0.8090
...
# ARROW … 赤い矢印の順に線 id を並べる
ARROW 0 1 2 3 4
```

線を赤矢印の順に閉じた折れ線として読み、その自己交差から結び目図を作り、以降の
Jones多項式・テロメア分裂・IQ を再計算する。

---

*Bada language · omega_iq · 山口フレームワーク準拠 — 真逆(mirror)対応版*
