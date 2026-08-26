"""
chain_model.py — 臨界連鎖の分岐過程モデル (Educational Branching-Process Model)
==============================================================================

中性子の連鎖反応を、教科書レベルの分岐過程（branching process）として
モデル化する。各世代の中性子は：

  - 確率 p_capture         : 制御吸収体に吸収され消滅（防止側の効果）
  - 確率 p_fission·(残り)  : 核分裂を誘発し ν 個（平均 2.4）の中性子を生む
  - それ以外               : 系外へ漏れて消滅

実効増倍率（1個の中性子が次世代に残す平均個数）は

    k_eff = ν · p_fission · (1 − absorption)

で、k_eff < 1 なら未臨界（連鎖は減衰）、k_eff > 1 なら超臨界（連鎖は成長）。
「連鎖防止」とは、吸収量 absorption を制御して常に k_eff < 1 に保つことである。

⚠️ 誠実な注記: これは教育・研究用の抽象モデルであり、実在の原子炉・核物質の
   設計データや工学量は一切含まない（教科書的な平均値 ν≈2.4 のみ使用）。
   実機の安全解析に使ってはならない。標準ライブラリのみで動作する。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


class LCG:
    """決定論的擬似乱数（seed 固定で再現可能）。"""

    def __init__(self, seed: int = 0x2545F491) -> None:
        self.state = seed & 0xFFFFFFFF

    def random(self) -> float:
        self.state = (1103515245 * self.state + 12345) & 0x7FFFFFFF
        return self.state / 0x7FFFFFFF


@dataclass
class CoreConfig:
    nu: float = 2.4            # 1核分裂あたりの平均中性子数（教科書値）
    p_fission: float = 0.45    # 核分裂誘発確率（抽象パラメータ）
    max_population: int = 200_000   # 数値発散を防ぐ人口上限（モデル都合）


class ChainCore:
    """
    分岐過程としての抽象「核」。

    step(absorption) で 1 世代進める。absorption ∈ [0,1] は制御側が
    その世代に挿入している吸収量（制御棒相当）。
    """

    def __init__(self, cfg: CoreConfig | None = None, seed: int = 0x2545F491,
                 initial_neutrons: int = 100) -> None:
        self.cfg = cfg or CoreConfig()
        self.rng = LCG(seed)
        self.population = initial_neutrons
        self.generation = 0

    def k_eff(self, absorption: float) -> float:
        """吸収量 a のときの実効増倍率（解析値）。"""
        a = min(max(absorption, 0.0), 1.0)
        return self.cfg.nu * self.cfg.p_fission * (1.0 - a)

    def critical_absorption(self) -> float:
        """k_eff = 1 となる吸収量（これ以上入れれば未臨界）。"""
        return 1.0 - 1.0 / (self.cfg.nu * self.cfg.p_fission)

    def step(self, absorption: float) -> int:
        """
        1 世代の確率的遷移。次世代の中性子数を返す。
        人口が大きい場合は期待値近似（decimal 部分を確率的に丸め）で高速化。
        """
        a = min(max(absorption, 0.0), 1.0)
        p_next = self.cfg.p_fission * (1.0 - a)   # 分裂まで生き残る確率

        if self.population > 5000:
            # 大人口: 期待値 + 確率的丸め（分岐過程の平均場近似）
            mean = self.population * p_next * self.cfg.nu
            base = int(mean)
            frac = mean - base
            nxt = base + (1 if self.rng.random() < frac else 0)
        else:
            # 小人口: 1個ずつモンテカルロ（消滅ゆらぎを忠実に再現）
            nxt = 0
            for _ in range(self.population):
                if self.rng.random() < p_next:
                    # ν=2.4 を 2個(60%) / 3個(40%) の混合で実現
                    nxt += 2 if self.rng.random() < 0.6 else 3

        self.population = min(nxt, self.cfg.max_population)
        self.generation += 1
        return self.population


if __name__ == "__main__":
    core = ChainCore(seed=11)
    print(f"critical absorption a* = {core.critical_absorption():.4f}")
    print(f"k_eff(a=0.0) = {core.k_eff(0.0):.3f}  (超臨界: 連鎖成長)")
    print(f"k_eff(a=0.2) = {core.k_eff(0.2):.3f}")
    print(f"k_eff(a=0.5) = {core.k_eff(0.5):.3f}  (未臨界: 連鎖減衰)")
    for g in range(6):
        core.step(absorption=0.5)
        print(f"  gen {core.generation}: population={core.population}")
