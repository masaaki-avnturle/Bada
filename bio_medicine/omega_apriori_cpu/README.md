# Ω-Apriori Core — 未知事前エンジン CPU

`omega_tomograph` の **テロメア分裂細胞の原理** を起点に、
**FPGA 様の再構成可能ロジックファブリック** を「全世代の人類」に見立てた個体群として
遺伝的に進化させ、事前には与えない隠れ関数（＝**未知事前 a-priori**）を自己発見する
小型 **AI エンジン CPU コア** を構築する三層実装です。

```
分裂細胞テロメア原理  →  FPGA様 4入力LUTファブリック  →  進化的 a-priori 発見  →  AI-CPU コア
```

| 言語 | ファイル | 役割 |
|:--|:--|:--|
| **C** | `apriori_cpu.c` / `apriori_cpu.h` | **中核ファブリック**: 4入力LUTネットワーク、前方伝播評価、テロメア/Hayflick/テロメラーゼ |
| **Python** | `apriori_engine.py` | **テロメア進化エンジン**: 世代GA（選択・交叉・テロメア比例変異）、C を ctypes 呼び出し（純Pythonフォールバック内蔵）、`run.json` 出力 |
| **HTML/JS** | `index.html` | **可視化**: ブラウザ内で同じGAをライブ実行、適合度/テロメア/老化推移・ファブリック状態・CPU真理値表。`run.json` 読込対応 |

---

## ⚠ 重要 — 非医療・概念実証

「テロメア分裂」「人類の進化」は**遺伝的アルゴリズムのメタファ**として用いています。
実在の人体・医療・余命予測・人類の遺伝的改変とは**一切無関係**で、できることは
小さなブール関数を進化的に学習する LUT ネットワークの構築のみです。

---

## ファブリックの仕様（3実装で共通）

- 一次入力 `inbits=6` → `layers=3` 層 × `width=8` セルの LUT ネットワーク → 出力 `outbits=3`
- 各セル = 4入力LUT（16bit真理値表）＋ 4本のルーティング選択 ＋ テロメアカウンタ
- ゲノム = `layers*width*6 = 144` バイト
- **テロメア**: 分裂(再構成)で短縮、`Hayflick` 限界で複製老化 → LUT凍結（恒等通過＝可塑性喪失）
- **テロメラーゼ**: エリート個体を再活性化し「全世代」の進化を継続
- **適合度**: 隠れ目標関数（`popcount` / `parity` / `add`）との出力ビット一致率

## 使い方

```bash
# 1) C 中核をビルド（共有ライブラリ＋スタンドアロンデモ）
make            # → libaprioricpu.so, apriori_demo
./apriori_demo  # ランダム探索デモ＋テロメア老化の確認

# 2) Python 進化エンジン（C を自動利用、無ければ純Python）
python3 apriori_engine.py --generations 150 --pop 80 --target popcount --out run.json
python3 apriori_engine.py --target parity --no-c     # 純Pythonで実行

# 3) ブラウザで可視化（単体でライブ実行。run.json も読込可）
xdg-open index.html      # or: python3 -m http.server 8000
```

参考実測（seed=1）: `parity` は適合度 ~0.98、`popcount` は小規模ファブリックの限界で ~0.72。
世代が進むとテロメアが短縮し複製老化率が上昇、エリートのテロメラーゼ再活性化で進化が継続する様子が観察できます。

---

*© 2025 Masaaki Yamaguchi · 山口 雅旭 · Bada / bio_medicine · 概念実証（非医療）*
