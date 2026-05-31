# omega_neurothermal

**ガンマ多様体 ニューロ・サーマル ワークベンチ**
Gamma-Manifold Neuro-Thermal Workbench — C99 application

山口フレームワーク（`explorerfiles` / `caostics` / `quantum_computer` / `Bada#` の各レポート）に記述される
**「ガンマ関数の大域的部分積分多様体の熱エネルギー」** を起点に、その熱エネルギーが
**大脳基底核を通って脳と体（末端）へ流れるエネルギー体** としてモデル化し、
そこへ **赤外線センサー・温度計・MRI・fMRI・脳トポグラフィ・血液検査・CTスキャン・DNA/RNA解析**
の装置機能（数値シミュレーション）を統合したC言語アプリケーションです。

> ⚠️ **安全に関する明記**
> 本ソフトウェアは **教育・可視化・理論探求のための数値シミュレーション** です。
> 実在の医療機器の制御、患者データの取得、診断・治療・投薬判断には **一切使用できません**。
> すべての入出力は合成データに対する数式モデルの結果です。

---

## 理論的根拠 — 中核方程式

`explorerfiles` (l.147–158, l.334) より：

```
ガンマ関数の大域的部分積分多様体 = 統一場
    T' = ∫ Γ(γ)' dx_m
    E  = m c² − ½ m v² = ‖ds²‖ = ∫ Γ(γ)' dx_m
```

本実装では被積分関数を **Γ'(x) = Γ(x)·ψ(x)**（ψ はディガンマ関数）とし、
合成シンプソン則で `T' = ∫ Γ'(γ) dx_m` を数値積分します。
微積分学の基本定理どおり `∫₁⁵ Γ'(x)dx = Γ(5) − Γ(1) = 24 − 1 = 23` を厳密に再現します。
得られた熱エネルギー量は `tanh` 飽和写像で生理的レンジの深部体温[°C]へ変換します。

---

## ビルド & 実行

```sh
make                      # gcc -std=c99 -O2 -Wall -Wextra ... -lm
./omega_neurothermal pipeline
make run                  # = pipeline
make clean
```

依存は標準Cと `libm` のみ。POSIX `rand_r` を使用（`_POSIX_C_SOURCE=200809L`）。

---

## サブコマンド

| コマンド | 装置機能 | モデル |
|:--|:--|:--|
| `gamma [lo hi steps]` | ガンマ熱多様体 | `T'=∫Γ'(γ)dx_m`（Lanczos Γ + ディガンマ） |
| `basal [E dopamine]` | 大脳基底核エネルギー流 | 直接路/間接路、SNcドーパミン利得、視床→末端の指数減衰 |
| `sensor [trueC emiss]` | 赤外線センサー + 温度計 | Stefan–Boltzmann `M=εσT⁴` / 一次遅れ接触温度 / 逆分散融合 |
| `mri [tissue]` | MRI | スピンエコー `S=ρ(1−e^{−TR/T1})e^{−TE/T2}`（gray/white/csf/fat/muscle/blood） |
| `fmri` | fMRI | 正準二重ガンマHRFと神経活動の畳み込みBOLD |
| `topo` | 脳トポグラフィ | 基底核線源を頭皮16電極へ `1/r²` 投影 |
| `ct` | CTスキャン（脳→末端） | Beer–Lambert 透過率 + Hounsfield値 |
| `blood [bias]` | 血液検査 | 主要8マーカーの基準範囲判定（体熱バイアス連動） |
| `dna [seq]` | DNA解析 | 長さ/塩基組成/GC含量/最頻k-mer |
| `rna [dnaSeq]` | RNA解析 | 転写 T→U + 標準遺伝暗号によるコドン翻訳 |
| `pipeline` / `all` | 統合パイプライン | Γ熱 → 体温 → センサー融合 → 基底核伝播 → 血液/DNA/RNA |

### 実行例

```sh
./omega_neurothermal gamma 1 5 2000     # T' = 23.0  -> core 38.50 C
./omega_neurothermal basal 23 0.6       # 基底核から手・足末端までのエネルギー
./omega_neurothermal mri csf            # 脳脊髄液のMRI信号テーブル
./omega_neurothermal rna ATGGCCATTGTA   # mRNA + ペプチド (M A I ...)
```

---

## データフロー（pipeline）

```
 [Γ多様体]  T' = ∫Γ'(γ)dx_m
     │  tanh写像
     ▼
 深部体温 (°C) ──► [赤外線センサー εσT⁴] ┐
     │                                    ├─► 逆分散融合 ─► 融合体温
     └──────────► [接触温度計 一次遅れ] ──┘
     │
     ▼
 [大脳基底核] 直接路/間接路 ─► 視床 ─► 体幹/上肢/下肢/手/足（指数減衰）
     │
     ▼
 [血液検査] 体熱バイアス連動  /  [DNA・RNA解析]  /  [MRI・fMRI・脳トポ・CT 装置群]
```

---

## ファイル構成

```
omega_neurothermal_pkg/
├── Makefile
├── README.md
└── src/
    ├── gamma_thermal.{h,c}   Γ・ψ・Γ' と T'=∫Γ'dx_m の数値積分、熱→体温写像
    ├── basal_ganglia.{h,c}   基底核の核モデルと脳→体末端エネルギー伝播
    ├── sensors.{h,c}         赤外線センサー / 温度計 / センサー融合
    ├── imaging.{h,c}         MRI / fMRI(HRF) / 脳トポグラフィ / CT
    ├── labanalysis.{h,c}     血液検査 / DNA / RNA(転写・翻訳)
    └── main.c                CLIディスパッチと統合パイプライン
```

すべて `-std=c99 -Wall -Wextra` で警告ゼロ。
