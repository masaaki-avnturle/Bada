# omega_neurothermal

**ガンマ多様体 ニューロ・サーマル ワークベンチ**
Gamma-Manifold Neuro-Thermal Workbench — C99 application + browser GUI

山口フレームワーク（`explorerfiles` / `caostics` / `quantum_computer` / `Bada#` の各レポート）に記述される
**「ガンマ関数の大域的部分積分多様体の熱エネルギー」** を起点に、その熱エネルギーが
**大脳基底核を通って脳と体（末端）へ流れるエネルギー体** としてモデル化し、
そこへ **赤外線センサー・温度計・MRI・fMRI・脳トポグラフィ・血液検査・CTスキャン・DNA/RNA解析**
の装置機能（数値シミュレーション）を統合したC言語アプリケーションです。
CLI と、ブラウザで動く GUI の両方を提供します。

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
make                      # CLI と GUI の両方をビルド
make run                  # CLI: ./omega_neurothermal pipeline
make gui                  # GUI サーバ起動 → ブラウザで http://localhost:8080
make clean
```

依存は標準Cと `libm` のみ（GUIは POSIX ソケットを使用）。外部ライブラリ・パッケージは不要。

---

## 🖥️ GUI（ブラウザUI）— 全アプリに赤外線センサー + 温度計を付属

```sh
make gui                              # = ./omega_neurothermal_gui 8080 ./web
./omega_neurothermal_gui 9000 ./web   # ポート指定も可
```

`omega_neurothermal_gui` は **依存ライブラリ不要の軽量HTTPサーバ**（`src/gui_server.c`）で、
既存の計算モジュールをそのまま再利用します。起動後ブラウザで `http://localhost:8080` を開くと、
ダッシュボード型GUIが表示されます（localhostのみ待受）。

- **画面上部のセンサーバーは全タブ共通で常設**：🔴赤外線センサー(IR)・🌡️温度計(Thermo)・
  ⚖️融合体温(Fused)・Γ熱エネルギー T' を常時表示し、2秒ごとにライブ更新します。
- **すべての API 応答に `sensors` ブロックを同梱** しているため、どのアプリ画面でも
  赤外線センサーと温度計の現在値が必ず付属します（ご要望「全アプリにセンサー付属」を実装）。
- タブ：統合パイプライン / Γ熱多様体(曲線) / 大脳基底核(バー) / 赤外線+温度計(時系列) /
  MRI(信号ヒートグリッド) / fMRI(BOLD曲線) / 脳トポグラフィ(頭皮マップcanvas) /
  CTスキャン(HU表) / 血液検査(判定表) / DNA / RNA。

### GUI のAPIエンドポイント

| エンドポイント | 返却 |
|:--|:--|
| `GET /api/pipeline` | 統合結果 + sensors |
| `GET /api/gamma?lo=&hi=&steps=` | T' と Γ'(γ) 曲線 + sensors |
| `GET /api/basal?E=&dopamine=` | 各核・各体節のエネルギー + sensors |
| `GET /api/sensor?trueC=&emiss=` | IR/温度計/融合の時系列 + sensors |
| `GET /api/mri?tissue=` | TR×TE 信号グリッド + sensors |
| `GET /api/fmri` | BOLD 時系列 + sensors |
| `GET /api/topo` | 16電極電位 + sensors |
| `GET /api/ct` | 層別 μ/厚み/HU・透過率 + sensors |
| `GET /api/blood?bias=` | マーカー基準範囲判定 + sensors |
| `GET /api/dna?seq=` | 配列統計/k-mer + sensors |
| `GET /api/rna?seq=` | 転写mRNA/翻訳ペプチド + sensors |

> 🔒 サーバは `127.0.0.1`（localhost）のみで待ち受け、外部公開しません。教育・可視化用途専用です。

---

## CLI サブコマンド

| コマンド | 装置機能 | モデル |
|:--|:--|:--|
| `gamma [lo hi steps]` | ガンマ熱多様体 | `T'=∫Γ'(γ)dx_m`（Lanczos Γ + ディガンマ） |
| `basal [E dopamine]` | 大脳基底核エネルギー流 | 直接路/間接路、SNcドーパミン利得、視床→末端の指数減衰 |
| `sensor [trueC emiss]` | 赤外線センサー + 温度計 | Stefan–Boltzmann `M=εσT⁴` / 一次遅れ接触温度 / 逆分散融合 |
| `mri [tissue]` | MRI | スピンエコー `S=ρ(1−e^{−TR/T1})e^{−TE/T2}` |
| `fmri` | fMRI | 正準二重ガンマHRFと神経活動の畳み込みBOLD |
| `topo` | 脳トポグラフィ | 基底核線源を頭皮16電極へ `1/r²` 投影 |
| `ct` | CTスキャン（脳→末端） | Beer–Lambert 透過率 + Hounsfield値 |
| `blood [bias]` | 血液検査 | 主要8マーカーの基準範囲判定（体熱バイアス連動） |
| `dna [seq]` | DNA解析 | 長さ/塩基組成/GC含量/最頻k-mer |
| `rna [dnaSeq]` | RNA解析 | 転写 T→U + 標準遺伝暗号によるコドン翻訳 |
| `pipeline` / `all` | 統合パイプライン | Γ熱 → 体温 → センサー融合 → 基底核伝播 → 血液/DNA/RNA |

---

## データフロー

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
├── src/
│   ├── gamma_thermal.{h,c}   Γ・ψ・Γ' と T'=∫Γ'dx_m の数値積分、熱→体温写像
│   ├── basal_ganglia.{h,c}   基底核の核モデルと脳→体末端エネルギー伝播
│   ├── sensors.{h,c}         赤外線センサー / 温度計 / センサー融合
│   ├── imaging.{h,c}         MRI / fMRI(HRF) / 脳トポグラフィ / CT
│   ├── labanalysis.{h,c}     血液検査 / DNA / RNA(転写・翻訳)
│   ├── main.c                CLIディスパッチと統合パイプライン
│   └── gui_server.c          GUI用 依存なしHTTPサーバ + JSON API
└── web/
    ├── index.html            ダッシュボード（常設センサーバー付き）
    ├── style.css             ダークUIテーマ
    └── app.js                タブUI・canvas可視化・ライブセンサー更新
```

すべて `-std=c99 -Wall -Wextra` で警告ゼロ。
