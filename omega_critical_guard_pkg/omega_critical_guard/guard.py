"""
guard.py — 擬似量子 連鎖防止ガード (Pseudo-Quantum Criticality Guard)
=====================================================================

`omega_mobius_drive.pseudo_quantum.PseudoQuantumVM`（ノイマン型 擬似量子VM）を
制御装置として使い、分岐過程の核 (chain_model.ChainCore) を **常に未臨界
(k_eff < 1) に保つ** フィードバック制御器。

制御則（2 段構え）:
  1. ベースライン: 解析的な臨界吸収量 a* = 1 − 1/(ν·p_f) に安全余裕 margin を
     加えた a* + margin を常時挿入（決定論的な下限保証）。
  2. 擬似量子ディザ: 人口誤差を PHASE として VM に注入し、測定ビットで
     吸収量を微調整（±dither）。確率的な探索で振動を抑える。
  3. SCRAM: 人口が scram_threshold を超えたら吸収量を最大 (a=1) に固定。

⚠️ 教育・研究用の抽象モデル。実在の炉の制御・安全系ではない。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Dict

from omega_mobius_drive import PseudoQuantumVM

from .chain_model import ChainCore, CoreConfig


@dataclass
class GuardConfig:
    margin: float = 0.08           # 臨界吸収量への安全余裕
    dither: float = 0.02           # 擬似量子ビットによる微調整幅
    target_population: int = 100   # 維持したい監視用中性子数
    scram_threshold: int = 5000    # これを超えたら SCRAM（全挿入）
    scram_release_below: int = 50  # SCRAM解除の人口条件


@dataclass
class GuardTelemetry:
    generation: int
    population: int
    absorption: float
    k_eff: float
    qbit: int
    scram: bool


class CriticalGuard:
    """擬似量子VMを判断核に持つ連鎖防止コントローラ。"""

    def __init__(self, core: ChainCore | None = None,
                 cfg: GuardConfig | None = None, seed: int = 0xC0FFEE) -> None:
        self.core = core or ChainCore(seed=seed)
        self.cfg = cfg or GuardConfig()
        self.vm = PseudoQuantumVM(n_regs=2, seed=seed)
        self.scram_active = False
        self.log: List[GuardTelemetry] = []

    # ---- 擬似量子判断: 誤差を位相に入れ、測定ビットで ±dither ------------- #
    def _quantum_dither(self, error: float) -> int:
        phase = 0.5 * math.tanh(error)     # 人口誤差 → 位相
        self.vm.output = []
        self.vm.halted = False
        bit = self.vm.run([
            ("LOAD", 0, 0),
            ("H", 0),
            ("PHASE", 0, phase),
            ("MEASURE", 0),
            ("HALT",),
        ])[0]
        return bit

    def decide_absorption(self) -> tuple:
        """現世代の吸収量を決める。(absorption, qbit, scram) を返す。"""
        cfg = self.cfg
        pop = self.core.population

        # SCRAM 判定（ラッチ式: 一度作動したら人口が下がるまで解除しない）
        if pop >= cfg.scram_threshold:
            self.scram_active = True
        elif self.scram_active and pop <= cfg.scram_release_below:
            self.scram_active = False
        if self.scram_active:
            return 1.0, 0, True

        base = self.core.critical_absorption() + cfg.margin
        # 人口が目標より多い→誤差正→ビット1が出やすい→吸収を増やす
        error = (pop - cfg.target_population) / max(cfg.target_population, 1)
        bit = self._quantum_dither(error)
        absorption = base + (cfg.dither if bit else -cfg.dither)
        return min(absorption, 1.0), bit, False

    # ---- メインループ ----------------------------------------------------- #
    def run(self, generations: int = 60,
            perturbation_at: int = -1, perturbation_neutrons: int = 0) -> List[GuardTelemetry]:
        """
        generations 世代の防止制御を実行。
        perturbation_at 世代目に perturbation_neutrons 個を外部注入して
        （中性子源の乱入など）外乱に対する防止動作を試験できる。
        """
        for g in range(generations):
            if g == perturbation_at:
                self.core.population += perturbation_neutrons
            absorption, bit, scram = self.decide_absorption()
            k = self.core.k_eff(absorption)
            self.core.step(absorption)
            self.log.append(GuardTelemetry(
                self.core.generation, self.core.population,
                absorption, k, bit, scram,
            ))
        return self.log

    # ---- 診断 -------------------------------------------------------------- #
    def summary(self) -> Dict[str, float]:
        if not self.log:
            return {}
        ks = [t.k_eff for t in self.log]
        pops = [t.population for t in self.log]
        return {
            "generations": len(self.log),
            "max_k_eff": max(ks),
            "always_subcritical": float(all(k < 1.0 for k in ks)),
            "max_population": max(pops),
            "final_population": pops[-1],
            "scram_events": float(sum(1 for t in self.log if t.scram)),
            "extinguished": float(pops[-1] == 0),
        }

    def report(self) -> str:
        s = self.summary()
        lines = [
            "=== 臨界連鎖防止シミュレーション レポート (教育用モデル) ===",
            f"世代数                  : {int(s['generations'])}",
            f"最大 k_eff              : {s['max_k_eff']:.4f}  "
            f"({'常に未臨界 ✓' if s['always_subcritical'] else '臨界超過あり ✗'})",
            f"最大中性子数            : {int(s['max_population'])}",
            f"最終中性子数            : {int(s['final_population'])}",
            f"SCRAM 作動世代数        : {int(s['scram_events'])}",
            f"連鎖消滅                : {'はい' if s['extinguished'] else 'いいえ'}",
            "",
            "注記: 教科書的な分岐過程モデルであり、実在の炉・核物質の設計データは",
            "      含まない。実機の安全解析には使用できない。",
        ]
        return "\n".join(lines)


if __name__ == "__main__":
    guard = CriticalGuard(seed=21)
    guard.run(generations=60, perturbation_at=20, perturbation_neutrons=3000)
    print(guard.report())
