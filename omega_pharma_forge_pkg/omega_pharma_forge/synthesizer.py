"""
synthesizer.py — 擬似量子 触媒投与コントローラ
==============================================

`omega_mobius_drive.pseudo_quantum.PseudoQuantumVM`（ノイマン型 擬似量子VM）を
判断核として、反応系 (reaction_network.ReactionNetwork) への触媒剤の投与量を
逐次決定する。

制御が効く理由:
    連鎖成長段 (2) P + I + C -> 2I + C は触媒 C を要するため、連鎖係数

        χ = k2·P·C / (k3 + 2·k4·I)

    は投与量 C の直接の関数になる。C=0 なら χ=0（連鎖は立たない）、
    C を増やせば χ が上がる。つまり **投与量が臨界性の制御レバー**である。

制御目標 — 選択性 vs 速度の実在するトレードオフ:
    目的物は I → A と **1次** (rate = k3·I) で生成される。
    副生成物は 2I → 2B と **2次** (rate = 2·k4·I²) で生成される。よって

        A への選択性 = k3·I / (k3·I + 2·k4·I²) = k3 / (k3 + 2·k4·I)

    すなわち **中間体 I を低く保つほど純度が上がる**が、I が低いと生成速度
    k3·I も小さく時間がかかる。χ を 1 未満に保つことは I の暴走を防ぎ、
    この綱引きを高純度側に倒すことに相当する。

制御則:
  1. 臨界ガード   : χ ≥ chi_max で投与停止、χ ≥ chi_scram で以後打ち切り(SCRAM)
  2. 擬似量子ディザ: 目標 χ との誤差を PHASE として VM に注入し、測定ビットで
                    投与量を 2 段（多め / 少なめ）に振り分ける
  3. 総量制限     : 触媒の累積投与量に上限を設ける

⚠️ 教育・研究用の抽象シミュレーション。実在の試薬・手順・反応条件は含まず、
   実際の化合物や医薬品を作ることはできない。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Dict

from omega_mobius_drive import PseudoQuantumVM

from .reaction_network import ReactionNetwork, RateConstants, State


@dataclass
class DosingConfig:
    chi_target: float = 0.30     # 維持したい連鎖係数（1未満＝臨界未満）
    chi_max: float = 0.45        # これを超えたら投与停止
    chi_scram: float = 1.00      # これを超えたら以後 SCRAM（投与を打ち切る）
    dose_high: float = 0.0020    # 擬似量子ビット=1 のときの投与量
    dose_low: float = 0.0005     # 擬似量子ビット=0 のときの投与量
    catalyst_budget: float = 0.30  # 触媒の累積投与量の上限
    steps: int = 3000            # 反応時間ステップ数


@dataclass
class Frame:
    t: float
    P: float
    I: float
    A: float
    B: float
    C: float
    chi: float
    dose: float
    qbit: int
    scram: bool


class QuantumSynthesizer:
    """擬似量子VMで触媒投与を制御する合成シミュレータ。"""

    def __init__(self, rates: RateConstants | None = None,
                 cfg: DosingConfig | None = None, dt: float = 0.02,
                 seed: int = 0xBADA) -> None:
        self.net = ReactionNetwork(rates=rates, state=State(), dt=dt)
        self.cfg = cfg or DosingConfig()
        self.vm = PseudoQuantumVM(n_regs=2, seed=seed)
        self.initial_mass = self.net.s.mass()
        self.dosed_total = 0.0
        self.scram_latched = False
        self.log: List[Frame] = []

    # ---- 擬似量子の判断 --------------------------------------------------- #
    def _quantum_bit(self, error: float) -> int:
        """χ の誤差を位相に写し、測定ビットを得る。"""
        self.vm.output = []
        self.vm.halted = False
        return self.vm.run([
            ("LOAD", 0, 0),
            ("H", 0),
            ("PHASE", 0, 0.8 * math.tanh(error)),
            ("MEASURE", 0),
            ("HALT",),
        ])[0]

    def decide_dose(self) -> tuple:
        """今ステップの投与量を決める。(dose, qbit, scram) を返す。"""
        cfg = self.cfg
        chi = self.net.chain_factor()

        if chi >= cfg.chi_scram:
            self.scram_latched = True
        if self.scram_latched or chi >= cfg.chi_max:
            return 0.0, 0, self.scram_latched
        if self.dosed_total >= cfg.catalyst_budget:
            return 0.0, 0, False

        # χ が目標より低い → 誤差正 → ビット1が出やすい → 多めに投与
        error = cfg.chi_target - chi
        bit = self._quantum_bit(error)
        dose = cfg.dose_high if bit else cfg.dose_low
        dose = min(dose, cfg.catalyst_budget - self.dosed_total)
        return dose, bit, False

    # ---- メインループ ----------------------------------------------------- #
    def run(self, steps: int | None = None) -> List[Frame]:
        n = steps if steps is not None else self.cfg.steps
        for _ in range(n):
            dose, bit, scram = self.decide_dose()
            self.net.step(dose=dose)
            self.dosed_total += dose
            s = self.net.s
            self.log.append(Frame(self.net.t, s.P, s.I, s.A, s.B, s.C,
                                  self.net.chain_factor(), dose, bit, scram))
        return self.log

    # ---- 診断 -------------------------------------------------------------- #
    def summary(self) -> Dict[str, float]:
        if not self.log:
            return {}
        chis = [f.chi for f in self.log if math.isfinite(f.chi)]
        return {
            "steps": float(len(self.log)),
            "yield": self.net.yield_fraction(self.initial_mass),
            "purity": self.net.purity(),
            "max_I": max(f.I for f in self.log),
            "max_chi": max(chis) if chis else 0.0,
            "stayed_subcritical": float(all(c < 1.0 for c in chis)),
            "catalyst_used": self.dosed_total,
            "mass_error": abs(self.net.s.mass() - self.initial_mass),
            "scram": float(self.scram_latched),
        }

    def report(self) -> str:
        s = self.summary()
        return "\n".join([
            "=== 擬似量子 触媒投与シミュレーション レポート (抽象モデル) ===",
            f"反応ステップ数        : {int(s['steps'])}",
            f"目的化合物 A の収率   : {s['yield']:.4f}  (物質量比)",
            f"粗生成物中の純度      : {s['purity']:.4f}  (A/(A+B))",
            f"最大 連鎖係数 χ       : {s['max_chi']:.4f}  "
            f"({'臨界未満を維持 ✓' if s['stayed_subcritical'] else '臨界超過あり ✗'})",
            f"最大 中間体濃度 I     : {s['max_I']:.4f}  (低いほど高選択性)",
            f"触媒 累積投与量       : {s['catalyst_used']:.4f}",
            f"SCRAM 作動            : {'あり' if s['scram'] else 'なし'}",
            f"質量保存誤差          : {s['mass_error']:.2e}",
            "",
            "注記: 収率・純度は抽象モデル上の化学量であり、薬効・安全性を",
            "      示すものではない。実在の試薬・手順・条件は含まない。",
        ])


def run_uncontrolled(rates: RateConstants | None = None, catalyst: float = 0.30,
                     steps: int = 3000, dt: float = 0.02) -> Dict[str, float]:
    """
    比較用: 触媒を最初に一括投与し、連鎖制御を行わない場合。
    χ が 1 を大きく超えて連鎖が暴走し、中間体 I が高濃度になるため
    2次の過分解 (2I→2B) が優位となって純度が落ちる。
    """
    net = ReactionNetwork(rates=rates, state=State(), dt=dt)
    m0 = net.s.mass()
    net.s.C = catalyst
    max_chi, max_i = net.chain_factor(), net.s.I
    for _ in range(steps):
        net.step()
        c = net.chain_factor()
        if math.isfinite(c):
            max_chi = max(max_chi, c)
        max_i = max(max_i, net.s.I)
    return {
        "yield": net.yield_fraction(m0),
        "purity": net.purity(),
        "max_chi": max_chi,
        "max_I": max_i,
        "mass_error": abs(net.s.mass() - m0),
    }


if __name__ == "__main__":
    synth = QuantumSynthesizer(seed=0xBADA)
    synth.run()
    print(synth.report())
    print()
    print("--- 比較: 制御なし（触媒一括投与） ---")
    u = run_uncontrolled()
    print(f"収率={u['yield']:.4f}  純度={u['purity']:.4f}  "
          f"最大χ={u['max_chi']:.2f}  最大I={u['max_I']:.4f}")
