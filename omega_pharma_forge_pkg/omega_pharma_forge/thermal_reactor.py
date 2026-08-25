"""
thermal_reactor.py — 温度結合反応器（熱暴走とその制御）
=======================================================

`reaction_network` の等温モデルに **温度** を導入する。実際の反応器で最も
危険なのは、発熱反応が温度を上げ、温度が Arrhenius 則で反応を速め、それが
さらに発熱を増やす **正のフィードバック（熱暴走 / thermal runaway）** である。

速度定数の温度依存（Arrhenius 則）:

    k(T) = k_ref · exp[ −(Ea/R) · (1/T − 1/T_ref) ]

熱収支:

    ρCp·V·dT/dt = Σ(−ΔH_j)·r_j·V − U·A·(T − T_jacket)
                  └── 反応熱（発熱）──┘   └── 冷却ジャケット ──┘

暴走の判定には **Semenov 条件**（発熱曲線の傾きが除熱直線の傾きを上回る）を
数値的に見る。すなわち

    d(発熱)/dT > d(除熱)/dT   →  熱暴走

制御は 2 系統:
  - 触媒投与量（連鎖係数 χ の制御 — 既存の synthesizer と同じ考え方）
  - 冷却ジャケット温度（除熱量の制御）
いずれも擬似量子VMの測定ビットで微調整する。

⚠️ 教育・研究用の抽象モデル。実在の試薬・手順・反応条件・装置設計値は一切
   含まない。実プラントの安全設計には使用できない。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List

from omega_mobius_drive import PseudoQuantumVM

from .reaction_network import ReactionNetwork, RateConstants, State


R_GAS = 8.314          # J/(mol·K) — 気体定数（唯一の実次元定数）


@dataclass
class ThermalConfig:
    """熱パラメータ（すべて説明用の無次元／簡略値）。"""

    T_ref: float = 300.0        # 速度定数の基準温度 (K)
    T_init: float = 300.0       # 初期温度 (K)
    T_jacket: float = 295.0     # 冷却ジャケット温度 (K)
    Ea_over_R: float = 6000.0   # 活性化温度 Ea/R (K)
    dH: float = 1.2e5           # 反応熱 −ΔH (J/mol 相当・発熱正)
    rho_cp_V: float = 2.0e3     # 熱容量 ρCp·V (J/K)
    UA: float = 600.0           # 総括伝熱係数×面積 U·A (W/K)
    T_alarm: float = 330.0      # 警報温度 (K)
    T_scram: float = 345.0      # 緊急停止温度 (K)


class ThermalReactor:
    """温度と濃度を同時に解く反応器。"""

    def __init__(self, rates: RateConstants | None = None,
                 thermal: ThermalConfig | None = None,
                 state: State | None = None, dt: float = 0.02) -> None:
        self.k_ref = rates or RateConstants()
        self.th = thermal or ThermalConfig()
        self.net = ReactionNetwork(rates=self._rates_at(self.th.T_init),
                                   state=state or State(), dt=dt)
        self.T = self.th.T_init
        self.dt = dt
        self.t = 0.0
        self.T_max = self.T

    # ---- Arrhenius 補正 ---------------------------------------------------- #
    def arrhenius(self, T: float) -> float:
        """基準温度に対する速度倍率。"""
        th = self.th
        return math.exp(-th.Ea_over_R * (1.0 / T - 1.0 / th.T_ref))

    def _rates_at(self, T: float) -> RateConstants:
        f = self.arrhenius(T)
        k = self.k_ref
        # 発熱を伴う分解・連鎖段のみ温度に強く依存させる（k5,k6 は据え置き）
        return RateConstants(k1=k.k1 * f, k2=k.k2 * f, k3=k.k3 * f,
                             k4=k.k4 * f, k5=k.k5, k6=k.k6)

    # ---- 発熱・除熱 -------------------------------------------------------- #
    def heat_generation(self, T: float | None = None) -> float:
        """反応による発熱速度 (W 相当)。分解・連鎖段の進行速度に比例させる。"""
        T = self.T if T is None else T
        k = self._rates_at(T)
        s = self.net.s
        r1 = k.k1 * s.P * s.C
        r2 = k.k2 * s.P * s.I * s.C
        r4 = k.k4 * s.I * s.I
        return self.th.dH * (r1 + r2 + r4)

    def heat_removal(self, T: float | None = None) -> float:
        """冷却ジャケットによる除熱速度 (W 相当)。"""
        T = self.T if T is None else T
        return self.th.UA * (T - self.th.T_jacket)

    def semenov_margin(self, dT: float = 0.5) -> float:
        """
        Semenov 判定の余裕 = d(除熱)/dT − d(発熱)/dT。
        正なら安定（温度が上がると除熱が勝って戻る）、
        負なら熱暴走（温度が上がるほど発熱が勝って加速する）。
        """
        dgen = (self.heat_generation(self.T + dT)
                - self.heat_generation(self.T - dT)) / (2 * dT)
        drem = (self.heat_removal(self.T + dT)
                - self.heat_removal(self.T - dT)) / (2 * dT)
        return drem - dgen

    @property
    def is_runaway(self) -> bool:
        return self.semenov_margin() < 0.0

    # ---- 1 ステップ -------------------------------------------------------- #
    def step(self, dose: float = 0.0, T_jacket: float | None = None) -> None:
        if T_jacket is not None:
            self.th.T_jacket = T_jacket

        # 現在温度での速度定数を反映して濃度を進める
        self.net.k = self._rates_at(self.T)
        self.net.step(dose=dose)

        # 熱収支を Euler 前進で進める（dt が小さいので十分）
        dT = (self.heat_generation() - self.heat_removal()) / self.th.rho_cp_V
        self.T += dT * self.dt
        self.T_max = max(self.T_max, self.T)
        self.t += self.dt


@dataclass
class ThermalDosingConfig:
    chi_target: float = 0.30
    chi_max: float = 0.45
    dose_high: float = 0.0020
    dose_low: float = 0.0005
    catalyst_budget: float = 0.30
    jacket_min: float = 280.0     # 冷却の下限温度 (K)
    jacket_base: float = 295.0
    cool_gain: float = 2.0        # 温度超過1Kあたりジャケットを下げる量
    steps: int = 3000


@dataclass
class ThermalFrame:
    t: float
    T: float
    chi: float
    I: float
    A: float
    B: float
    dose: float
    T_jacket: float
    margin: float
    scram: bool


class ThermalController:
    """
    触媒投与と冷却を同時に制御するコントローラ。
    擬似量子VMの測定ビットで投与量を振り分け、温度は比例冷却＋SCRAMで守る。
    """

    def __init__(self, rates: RateConstants | None = None,
                 thermal: ThermalConfig | None = None,
                 cfg: ThermalDosingConfig | None = None,
                 dt: float = 0.02, seed: int = 0xBADA) -> None:
        self.reactor = ThermalReactor(rates=rates, thermal=thermal, dt=dt)
        self.cfg = cfg or ThermalDosingConfig()
        self.vm = PseudoQuantumVM(n_regs=2, seed=seed)
        self.initial_mass = self.reactor.net.s.mass()
        self.dosed_total = 0.0
        self.scram_latched = False
        self.log: List[ThermalFrame] = []

    def _quantum_bit(self, error: float) -> int:
        self.vm.output = []
        self.vm.halted = False
        return self.vm.run([
            ("LOAD", 0, 0), ("H", 0),
            ("PHASE", 0, 0.8 * math.tanh(error)),
            ("MEASURE", 0), ("HALT",),
        ])[0]

    def decide(self) -> tuple:
        """(dose, T_jacket, scram) を決める。"""
        cfg, rc = self.cfg, self.reactor
        th = rc.th

        # --- 温度側: 超過分に比例してジャケットを下げる（比例冷却） ---
        excess = max(0.0, rc.T - th.T_ref)
        T_jacket = max(cfg.jacket_min, cfg.jacket_base - cfg.cool_gain * excess)

        # --- SCRAM: 温度 or Semenov 条件 ---
        if rc.T >= th.T_scram or rc.is_runaway:
            self.scram_latched = True
        if self.scram_latched:
            return 0.0, cfg.jacket_min, True

        # --- 触媒側: χ を目標に保つ（温度警報中は投与しない） ---
        if rc.T >= th.T_alarm or self.dosed_total >= cfg.catalyst_budget:
            return 0.0, T_jacket, False
        chi = rc.net.chain_factor()
        if chi >= cfg.chi_max:
            return 0.0, T_jacket, False
        bit = self._quantum_bit(cfg.chi_target - chi)
        dose = min(cfg.dose_high if bit else cfg.dose_low,
                   cfg.catalyst_budget - self.dosed_total)
        return dose, T_jacket, False

    def run(self, steps: int | None = None) -> List[ThermalFrame]:
        n = steps if steps is not None else self.cfg.steps
        rc = self.reactor
        for _ in range(n):
            dose, T_jacket, scram = self.decide()
            rc.step(dose=dose, T_jacket=T_jacket)
            self.dosed_total += dose
            s = rc.net.s
            self.log.append(ThermalFrame(
                rc.t, rc.T, rc.net.chain_factor(), s.I, s.A, s.B,
                dose, T_jacket, rc.semenov_margin(), scram))
        return self.log

    def summary(self) -> Dict[str, float]:
        if not self.log:
            return {}
        rc = self.reactor
        return {
            "steps": float(len(self.log)),
            "yield": rc.net.yield_fraction(self.initial_mass),
            "purity": rc.net.purity(),
            "T_max": rc.T_max,
            "T_final": rc.T,
            "stayed_below_alarm": float(rc.T_max < rc.th.T_alarm),
            "min_semenov_margin": min(f.margin for f in self.log),
            "catalyst_used": self.dosed_total,
            "mass_error": abs(rc.net.s.mass() - self.initial_mass),
            "scram": float(self.scram_latched),
        }

    def report(self) -> str:
        s = self.summary()
        return "\n".join([
            "=== 温度結合反応器 レポート (抽象モデル) ===",
            f"ステップ数            : {int(s['steps'])}",
            f"目的化合物 A の収率   : {s['yield']:.4f}",
            f"粗生成物中の純度      : {s['purity']:.4f}",
            f"最高温度              : {s['T_max']:.2f} K  "
            f"({'警報温度未満 ✓' if s['stayed_below_alarm'] else '警報温度超過 ✗'})",
            f"最終温度              : {s['T_final']:.2f} K",
            f"Semenov 余裕の最小値  : {s['min_semenov_margin']:.4f}  "
            f"({'常に安定 ✓' if s['min_semenov_margin'] > 0 else '暴走域に入った ✗'})",
            f"触媒 累積投与量       : {s['catalyst_used']:.4f}",
            f"SCRAM 作動            : {'あり' if s['scram'] else 'なし'}",
            f"質量保存誤差          : {s['mass_error']:.2e}",
            "",
            "注記: 抽象モデル上の数値であり、実在の装置・試薬・条件は含まない。",
        ])


def run_thermal_uncontrolled(catalyst: float = 0.30, steps: int = 3000,
                             dt: float = 0.02,
                             thermal: ThermalConfig | None = None) -> Dict[str, float]:
    """比較用: 触媒一括投与・冷却固定（制御なし）。熱暴走を起こしやすい。"""
    rc = ThermalReactor(thermal=thermal, dt=dt)
    m0 = rc.net.s.mass()
    rc.net.s.C = catalyst
    min_margin = rc.semenov_margin()
    runaway = False
    for _ in range(steps):
        rc.step()
        min_margin = min(min_margin, rc.semenov_margin())
        runaway = runaway or rc.is_runaway
    return {
        "yield": rc.net.yield_fraction(m0),
        "purity": rc.net.purity(),
        "T_max": rc.T_max,
        "min_semenov_margin": min_margin,
        "runaway": float(runaway),
    }


if __name__ == "__main__":
    c = ThermalController(seed=0xBADA)
    c.run()
    print(c.report())
    print()
    print("--- 比較: 制御なし（触媒一括投与・冷却固定） ---")
    u = run_thermal_uncontrolled()
    print(f"収率={u['yield']:.4f}  純度={u['purity']:.4f}  "
          f"最高温度={u['T_max']:.2f}K  熱暴走={'発生' if u['runaway'] else 'なし'}")
