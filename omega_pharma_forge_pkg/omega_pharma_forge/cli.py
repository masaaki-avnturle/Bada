"""cli.py — `omega-pharma-forge [steps] [seed]`

シナリオ:
  1) 擬似量子制御あり  : χ を臨界未満に保ち、高純度で目的物を得る
  2) χ 目標値スイープ  : 選択性 vs 速度のトレードオフと最適点を示す
  3) 制御なし一括投与  : 連鎖が暴走し中間体が高濃度 → 過分解で純度低下
  4) 温度結合反応器    : 発熱による熱暴走(Semenov条件)とその制御
"""
from __future__ import annotations
import sys
from .synthesizer import QuantumSynthesizer, DosingConfig, run_uncontrolled
from .thermal_reactor import ThermalController, ThermalDosingConfig, run_thermal_uncontrolled


def main() -> int:
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0xBADA

    print("--- シナリオ1: 擬似量子コントローラによる逐次投与 ---")
    synth = QuantumSynthesizer(cfg=DosingConfig(steps=steps), seed=seed)
    synth.run()
    print(synth.report())

    print()
    print("--- シナリオ2: χ 目標値スイープ（選択性 vs 速度） ---")
    print("chi_target   収率      純度     最大I     最大χ")
    for ct in (0.80, 0.50, 0.30, 0.20):
        s = QuantumSynthesizer(
            cfg=DosingConfig(chi_target=ct, chi_max=ct + 0.15, steps=steps),
            seed=seed)
        s.run()
        d = s.summary()
        print(f"  {ct:.2f}      {d['yield']:.4f}   {d['purity']:.4f}   "
              f"{d['max_I']:.4f}   {d['max_chi']:.3f}")
    print("→ χ を絞るほど中間体 I が下がり純度が上がる。ただし絞りすぎると")
    print("  反応が遅く時間内に終わらず収率が落ちる（内点に最適値がある）。")

    print()
    print("--- シナリオ3: 制御なし（触媒を最初に一括投与） ---")
    u = run_uncontrolled(steps=steps)
    print(f"収率={u['yield']:.4f}  純度={u['purity']:.4f}  "
          f"最大χ={u['max_chi']:.2f}  最大I={u['max_I']:.4f}")
    print("→ χ≫1 で連鎖が暴走し中間体が高濃度になるため、2次の過分解")
    print("  (2I→2B) が優位となり純度・収率とも制御ありに劣る。")

    print()
    print("--- シナリオ4: 温度結合反応器（熱暴走とその制御） ---")
    tc = ThermalController(cfg=ThermalDosingConfig(steps=steps), seed=seed)
    tc.run()
    print(tc.report())
    print()
    tu = run_thermal_uncontrolled(steps=steps)
    print("  比較: 制御なし（触媒一括投与・冷却固定）")
    print(f"    収率={tu['yield']:.4f}  純度={tu['purity']:.4f}  "
          f"最高温度={tu['T_max']:.2f}K  "
          f"熱暴走={'発生' if tu['runaway'] else 'なし'}")
    print("→ 発熱→昇温→Arrhenius加速→さらに発熱、の正のフィードバックで熱暴走する。")
    print("  Semenov条件 d(発熱)/dT > d(除熱)/dT が成立した時点で安定点は失われる。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
