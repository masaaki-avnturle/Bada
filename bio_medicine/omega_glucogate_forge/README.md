# Ω-GlucoGate Forge — 形態形成場でつくる「糖取り込み薬剤」製造装置シミュレータ

糖尿病では、血液中に糖があるのに**細胞がその糖を取り込めない**（インスリン抵抗性 = GLUT4 が
細胞膜に出てこない）状態が起こります。本アプリは、これまでの `bio_medicine` 系アプリと同じ
**Γ大域的部分積分多様体 `e^{−x log x}` で変調した形態形成場（反応拡散場）**を薬剤の製造装置として使い、
**ドーパミン作動性（D2）の「糖取り込み薬剤」を鍛造 → 投与 → 血中の糖が細胞内へ入る過程を数値シミュレーション**
する、依存なし・ダブルクリック動作のアプリケーションです。

```
形態形成場 φ(r)  ── Γカーネルで拡散率を変調した Gray–Scott 反応拡散 ──▶ 収束形態
   │  形態記述子（充填率・分岐度・点対称性・特徴長）
   ▼
薬剤スペックの鍛造：D2親和性 pKi / 半減期 t½ / 経口F / BBB透過 / κ_インスリン感受性 / κ_GLUT4動員
   │
   ▼
経口PK（1-コンパートメント）→ 血漿濃度 Cp → D2占有率 Occ = Cp/(Cp+Ki) → 中枢は効果部位 Ce
   │
   ▼
生理モデル（dt = 1 min）
   ├ 肝糖放出 EGP を抑制（血中へ出る糖を減らす）
   ├ インスリン感受性 Si·(1+κ_ins·Ψ) を増強
   ├ インスリン非依存の GLUT4 動員 κ_GLUT4（本アプリの概念部分）
   └ 膵島 D2 はインスリン分泌を抑制（設計上のトレードオフ）
   ▼
【主目的】 U_cell = Vmax · M · G/(Km+G)  ← 血液中の糖が細胞内へ取り込まれる速度
```

---

## ⚠ 重要 — 概念シミュレーション・非医療

本アプリは**実在の医薬品を設計・製造・評価するものではありません**。出力される「薬剤」は
形態形成場の形状から決定論的に写像した**仮想パラメータの集合**であり、化学構造も合成法も
含みません。**シミュレーション結果を医療上の判断（薬の選択・用量・治療変更）に用いることはできません。**
治療に関することは必ず主治医にご相談ください。

着想の背景として、**ドーパミン D2 作動薬が 2 型糖尿病の血糖コントロールを改善しうる**という
実際の知見（中枢ドーパミン作動性トーンのリセットによる肝糖放出の低下とインスリン感受性の改善）を
参照していますが、**本モデルの係数はすべて概念的な仮想値**です。またモデルには、
**膵島の D2 受容体はインスリン分泌を抑制する**という逆向きの作用も入れてあり、
「中枢に効かせつつ膵島への曝露を抑える」という設計上のトレードオフを体験できるようにしています。

---

## ⬇️ ダウンロード（インストール不要）

| 入手方法 | 内容 |
|:---|:---|
| **単一 HTML（推奨）** ★ | [`www/index.html`](www/index.html) を「Download raw file」で保存 → ダブルクリックで起動。依存なし・オフライン可 |
| **Python CLI** | [`glucogate_sim.py`](glucogate_sim.py) — 標準ライブラリのみ。`python3 glucogate_sim.py` |
| **C（ネイティブ）** | [`glucogate.c`](glucogate.c) — `gcc -std=c99 -O2 -o glucogate glucogate.c -lm` |


### 📱💻 ネイティブ アプリ（インストール型）

ブラウザ不要のインストール型アプリを [Releases](https://github.com/masaaki-avnturle/Bada/releases) から入手できます:

| プラットフォーム | ファイル | 起動方法 |
|:---|:---|:---|
| **Android** (APK) | `glucogate-forge-debug.apk` | 端末にコピーしてタップ（提供元不明のアプリのインストールを許可） |
| **Windows 10 / 11** | `Omega-GlucoGate-Forge-1.0.0-x64.exe`(NSIS インストーラ)<br>`Omega-GlucoGate-Forge-1.0.0-x64.exe`(ポータブル) | ダブルクリック |
| **Ubuntu** | `Omega-GlucoGate-Forge-1.0.0-x86_64.AppImage` | `chmod +x` して実行 |
| **Ubuntu** (deb) | `Omega-GlucoGate-Forge-1.0.0-amd64.deb` | `sudo dpkg -i` または `sudo apt install ./...deb` |

ビルドは [`glucogate-app-build.yml`](../../.github/workflows/glucogate-app-build.yml) が実行します
(`glucogate-v*` タグで Release へ添付 / `workflow_dispatch` で Actions アーティファクト)。
パッケージ前に **C / Python / 単一HTML の 3 実装が同じ結果を出すことを CI で検証**しています。

---

## 使い方（アプリ）

```bash
xdg-open www/index.html        # or: python3 -m http.server 8000
```

1. **① 形態形成場 製造装置** — 供給率 F・消滅率 k・Γカーネル κ・種を決めて
   「▶ 場を収束させて薬剤を鍛造」。反応拡散が収束していく様子がそのまま製造工程です。
   **「⚙ 自動鍛造」**を押すと、N 個の候補を試作して**最良の薬剤を自動探索**します。
2. **② 薬剤スペック / 投与設計** — 鍛造された薬剤の親和性・半減期・BBB透過などを確認し、
   病態プリセット（2型糖尿病 中等症／重症／非糖尿病）、食事の炭水化物量、
   1回量・投与回数・時刻・投与日数を設定します。
3. **③ 生体シミュレーション** — 最終24時間の
   血糖 G(t)／**細胞内への取り込み U_cell(t) と累積量**／GLUT4膜提示率 M(t)／
   インスリンと D2 占有率を、**無投薬の対照と重ねて**表示します。
4. **④ 出力・ソース生成** — `glucogate.spec.json`（薬剤スペック＋指標）、
   `timeseries.csv`、および**鍛造した薬剤の定数を焼き込んだ C / Python / JavaScript ソース**を
   ダウンロードできます（生成コードは単体でコンパイル・実行可能）。

### CLI

```bash
python3 glucogate_sim.py --preset t2d --days 7 --dose 4.8 --csv out.csv --json spec.json
python3 glucogate_sim.py --auto-forge 16          # 製造装置が最良の薬剤を自動探索
gcc -std=c99 -O2 -o glucogate glucogate.c -lm && ./glucogate --preset t2d-severe --auto-forge 8
```

---

## モデル（何を解いているか）

**① 形態形成場（製造装置）** — Γカーネルで拡散係数を空間変調した Gray–Scott 系:

```
∂u/∂t = Du(r)∇²u − uv² + F(1−u)
∂v/∂t = Dv(r)∇²v + uv² − (F+k)v
Du(r) = Du₀·(½ + ½·e^{−κr log κr})        ← Γ大域的部分積分多様体による変調
```

収束形態から 4 記述子を読み出し、単調写像で薬剤スペックへ:
**充填率→半減期**、**分岐度→D2親和性**、**点対称性→経口バイオアベイラビリティ**、
**特徴長→BBB透過指数**（同じ種・同じ (F,k,κ) からは常に同じ薬剤が鍛造されます）。

**② PK** — 経口 1-コンパートメント + 効果部位:
`dA_gut/dt = −ka·A_gut`, `dA/dt = ka·F_oral·A_gut − ke·A`, `Cp = A/Vd`,
`dCe/dt = keo(BBB·Cp − Ce)`, 占有率 `Occ = C/(C+Ki)`。

**③ 生理（dt = 1 min）**

| 状態量 | 式 |
|:---|:---|
| 血糖 `G` | `dG/dt = (Ra_meal + EGP − U_ii − U_cell)/V_G` |
| 肝糖放出 `EGP` | `EGP₀(1−α·Ψ)/(1+k_EGP(I−I_b)/I_b)` ×低血糖時の代償 |
| インスリン `I` | `dI/dt = 分泌(G, β) ·(1 − ι·Occ_末梢) − n(I−I_min)` |
| インスリン作用 `X` | `dX/dt = p₂(S_i(1+κ_ins·Ψ)(I−I_z) − X)` |
| GLUT4 膜提示 `M` | `dM/dt = (M_∞(X + κ_GLUT4·0.02·Occ) − M)/τ_M`, `M_∞` は Hill 型 |
| **細胞内取り込み** | **`U_cell = V_max·M·G/(K_m+G)`** |
| 慢性感作 `Ψ` | `dΨ/dt = (Occ_中枢 − Ψ)/τ_sens` (τ = 2 日) |

`V_max` と基礎分泌は、**病態プリセットの基礎状態で収支が閉じるように自己校正**されます
（体重 70 kg 相当、`V_G=112 dL`、`K_m=90 mg/dL`、`EGP₀=145 mg/min`、`U_ii=70 mg/min`）。

### 主指標 — 「細胞内クリアランス」

定常状態では **1日の総取り込み量は摂取量にほぼ拘束されます**。薬剤が改善するのは
**同じ量の糖を、より低い血糖値で細胞に入れられるか**であり、それを表すのが
**細胞内クリアランス `U_cell/G` (dL/min)** です。本アプリの主指標はここです。

参考値（2型糖尿病 中等症・4.8 mg×1回/日・7日投与）:

| 指標 | 対照(無投薬) | 投薬 |
|:---|---:|---:|
| 平均血糖 | 183.9 mg/dL | 158.2 mg/dL |
| 推定HbA1c | 8.03 % | 7.14 % |
| **細胞内クリアランス** | **0.916 dL/min** | **1.179 dL/min (+28.7 %)** |
| GLUT4 膜提示率 | 30.0 % | 33.6 % |

---

## 検証

`www/index.html`（JavaScript）・`glucogate_sim.py`（Python）・`glucogate.c`（C）の
**3 実装が同一の薬剤 UID と同一の指標**を出すことを確認済みです
（例: 形態形成場 grid=48 / 500 steps / F=0.037 / k=0.060 / κ=1.0 / seed=7 →
`Ω-GG-2253-18AC`, pKi 8.03, 平均血糖 対照 183.9 / 投薬 158.2 mg/dL）。
アプリの「④ 出力」が生成する C / Python / JavaScript ソースも、
コンパイル・実行してアプリと同じ値（平均血糖 157.4 mg/dL / TIR 67.7 % / 細胞内取込 274.5 g/日）を
再現することを確認しています。

## 関連

`omega_telomere_forge`（Γ多様体の鍛造） · `omega_function_foundry` · `omega_patternforge` ·
`omega_thermal_trace`（体内の熱流トレース） · `omega_tomograph`

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / bio_medicine · 概念実証（非医療）*
