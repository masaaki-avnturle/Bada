"""cli.py — `omega-critical-guard [generations] [seed]`

シナリオ:
  1) 通常運転: ガードが k_eff < 1 を維持し連鎖を減衰させる
  2) 外乱試験: 中性子の大量注入に対し SCRAM が作動して連鎖を止める
  3) 無防備比較: ガードなし (absorption=0) では人口が急成長する様子を表示
  4) 臨界期の強度: 未臨界増倍 M=1/(1-k) の発散と、1/M 法による安全な接近
  5) 点炉動特性  : 遅発中性子と即発臨界の境界
"""
from __future__ import annotations
import sys
from .chain_model import ChainCore
from .guard import CriticalGuard
from .subcritical import (
    ApproachToCritical, run_unsafe_approach,
    format_intensity_table, format_approach_report, format_kinetics_report,
)


def main() -> int:
    generations = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 21

    print("--- シナリオ1: 通常運転（防止制御あり） ---")
    g1 = CriticalGuard(seed=seed)
    g1.run(generations=generations)
    print(g1.report())

    print()
    print("--- シナリオ2: 外乱試験（8000個注入 → SCRAM） ---")
    g2 = CriticalGuard(seed=seed)
    g2.run(generations=generations, perturbation_at=generations // 3,
           perturbation_neutrons=8000)
    print(g2.report())

    print()
    print("--- シナリオ3: 比較（防止制御なし, absorption=0） ---")
    core = ChainCore(seed=seed)
    peak = core.population
    for _ in range(12):
        core.step(absorption=0.0)
        peak = max(peak, core.population)
    print(f"12世代後の中性子数: {core.population} (最大 {peak})")
    print(f"k_eff(a=0) = {core.k_eff(0.0):.3f} > 1 のため連鎖が成長する。")
    print("→ 防止制御（シナリオ1,2）との差が連鎖防止の効果である。")

    print()
    print("--- シナリオ4: 臨界期の強度と 1/M 法による安全な接近 ---")
    print(format_intensity_table())
    print()
    approach = ApproachToCritical(seed=0x51DE)
    approach.run()
    print(format_approach_report(approach, run_unsafe_approach()))

    print()
    print("--- シナリオ5: 点炉動特性（遅発中性子と即発臨界） ---")
    print(format_kinetics_report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
