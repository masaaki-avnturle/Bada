# Omega Möbius-Drive System

**擬似量子コンピュータ × メビウス回路ハードディスク × 反ダランベルシアン場** を
1 つの内部統制ループに束ねた、PC 内部で完結するシミュレーション。

```
 [擬似量子VM] --bit--> [メビウス回路HDD] --極性--> [反ダランベルシアン場]
       ^                                                  |
       |------------------- lift_index フィードバック ------|
```

---

## ⚠️ 正直な位置づけ（重要）

本パッケージは **反重力発生器の実機ではありません**。現実には反重力・反重力
発生器を作る方法は存在せず、本コードが計算するのは物理的な力ではなく、格子上の
**波動場の数値シミュレーション値**です。`lift_index`（浮揚指標）も揚力そのもの
ではなく、場の非対称勾配から定義した診断スカラーにすぎません。

その上で本パッケージは、あなたのリポジトリの世界観（擬似量子・メビウス位相・
ダランベルシアン）を **実際に動く・再現可能な・依存ゼロの Python シミュレーション**
として体験できる形にまとめた、研究／教育／アート目的の骨組みです。

構成要素はすべて実在の概念を数値的に正しく実装しています：
- **メビウス位相の二重被覆**（1 周で表裏反転、2 周で復帰）
- **ダランベルシアン波動作用素** □φ の陽的差分（CFL 安定条件つき）
- **ノイマン型（プログラム内蔵）仮想機械**と擬似量子ビット状態＋測定

---

## インストール

```bash
cd omega_mobius_drive_pkg
pip install -e .
```

依存ライブラリはゼロ（標準 `math` のみ）。Python 3.8+。

## 使い方

```bash
omega-mobius-drive 40 7        # 40サイクル, seed=7
# または
python -m omega_mobius_drive.cli 40 7
```

```python
from omega_mobius_drive import MobiusDriveSystem, FieldConfig

sys = MobiusDriveSystem(sectors=64, field_cfg=FieldConfig(nx=96, dt=0.4), seed=7)
sys.run(cycles=48)
print(sys.report())
```

個別部品も単体で使えます：

```python
from omega_mobius_drive import MobiusDisk, DAlembertField, PseudoQuantumVM

d = MobiusDisk(sectors=8); d.write(0b10101010); d.seek(8)
print(d.face, bin(d.read()))        # 1周で裏面 → ビット反転
```

## テスト

```bash
pip install -e ".[test]"
pytest -q
```

## 構成

```
omega_mobius_drive_pkg/
├── pyproject.toml / README.md / LICENSE
├── omega_mobius_drive/
│   ├── mobius_disk.py     # メビウス位相の仮想HDD（電子制御装置）
│   ├── dalembert.py       # ダランベルシアン/反ダランベルシアン場ソルバ
│   ├── pseudo_quantum.py  # ノイマン型 擬似量子VM
│   ├── controller.py      # 3部品を束ねる内部統制システム
│   └── cli.py
├── examples/demo.py
└── tests/test_system.py
```

## ライセンス

MIT License（リポジトリ本体に準拠）
