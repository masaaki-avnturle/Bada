# Omega Critical-Guard

**擬似量子コンピュータをフィードバック制御器に使う、臨界連鎖「防止」シミュレーション**

本リポジトリの `omega_mobius_drive_pkg`（ノイマン型 擬似量子VM）を判断核として
再利用し、分岐過程（branching process）でモデル化した抽象的な「核」を
**常に未臨界 (k_eff < 1) に保つ**アプリケーションです。

```
 中性子人口 ──誤差──▶ [擬似量子VM: H → PHASE(誤差) → 測定] ──bit──▶ 吸収量 ±dither
     ▲                                                                │
     └───────────── ChainCore.step(absorption) ◀──────────────────────┘
                （人口 ≥ 閾値で SCRAM: 吸収量を最大に固定）
```

## モデル（教科書レベル）

1 世代の中性子は、吸収されるか、確率 p_fission·(1−a) で核分裂を誘発して
平均 ν≈2.4 個の中性子を生みます。実効増倍率は

```
k_eff = ν · p_fission · (1 − absorption)
```

で、**k_eff < 1 なら連鎖は減衰**（未臨界）、k_eff > 1 なら成長（超臨界）。
「連鎖防止」とは吸収量 absorption の制御で k_eff < 1 を保証することです。

ガードは 3 段構え：
1. **解析ベースライン** — 臨界吸収量 a\* = 1 − 1/(ν·p_f) に安全余裕を加えて常時挿入
2. **擬似量子ディザ** — 人口誤差を位相 PHASE として VM に注入し、測定ビットで微調整
3. **SCRAM** — 人口が閾値超過で吸収量を最大に固定（ラッチ式、人口低下で解除）

## ⚠️ 正直な位置づけ（重要）

- 教育・研究用の**抽象的な分岐過程モデル**です。実在の原子炉・核物質の設計
  データ・工学量は一切含みません（使うのは教科書的平均値 ν≈2.4 のみ）。
- **実機の安全解析・設計には使用できません。**
- 「擬似量子VM」も本物の量子コンピュータではなく、振幅を実数で模した
  決定論的シミュレーションです（`omega_mobius_drive_pkg` 参照）。

## インストール

先に擬似量子VMパッケージを入れてから本パッケージを入れます：

```bash
cd omega_mobius_drive_pkg  && pip install -e .
cd ../omega_critical_guard_pkg && pip install -e .
```

依存は `omega-mobius-drive` のみ（外部ライブラリゼロ）。Python 3.8+。

## 使い方

```bash
omega-critical-guard 60 21     # 60世代, seed=21 で3シナリオ実行
```

- **シナリオ1** 通常運転: k_eff < 1 を維持し連鎖が減衰・消滅
- **シナリオ2** 外乱試験: 8000個の中性子を注入 → SCRAM が1世代で鎮圧
- **シナリオ3** 比較: 防止制御なし (a=0, k_eff=1.08) では連鎖が成長

```python
from omega_critical_guard import CriticalGuard

g = CriticalGuard(seed=21)
g.run(generations=60, perturbation_at=20, perturbation_neutrons=3000)
print(g.report())          # 常に未臨界 ✓ / SCRAM回数 / 最終人口
```

## テスト

```bash
pytest -q    # 7テスト: k_eff解析値・無防備成長・防止減衰・SCRAM・再現性
```

## 構成

```
omega_critical_guard_pkg/
├── pyproject.toml / README.md / LICENSE
├── omega_critical_guard/
│   ├── chain_model.py   # 分岐過程の抽象核 (k_eff, モンテカルロ/平均場)
│   ├── guard.py         # 擬似量子ディザ + SCRAM の防止制御器
│   └── cli.py           # 3シナリオ・アプリケーション
├── examples/demo.py
└── tests/test_guard.py
```

## ライセンス

MIT License（リポジトリ本体に準拠）
