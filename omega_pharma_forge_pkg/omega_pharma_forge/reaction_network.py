"""
reaction_network.py — 自己触媒的分解連鎖の反応速度論モデル
==========================================================

フラバン(flavan)系前駆体に触媒剤を投与し、分解 → 自己触媒的な連鎖反応を経て
目的化合物へ変換する過程を、**質量作用則 (mass-action kinetics)** の常微分
方程式系として抽象化する。RK4 で時間積分する。

化学種（すべて抽象的な記号であり、実在の特定化合物ではない）:
    P : 前駆体 (precursor, フラバン骨格を想定した出発物)
    C : 触媒剤 (catalyst, 反応で再生される)
    I : 活性中間体 (open-chain intermediate, 連鎖の担い手)
    A : 目的化合物 (target product)
    B : 副生成物 (byproduct, 連鎖停止・過分解の産物)

素反応:
    (1) P + C  --k1-->  I + C        触媒による分解開始（触媒は再生）
    (2) P + I + C --k2--> 2 I + C    触媒媒介の自己触媒的連鎖成長 ← 臨界性の源
    (3) I      --k3-->  A            目的化合物への変換
    (4) 2 I    --k4-->  2 B          二分子停止（過分解 → 副生成物）
    (5) A      --k5-->  B            目的物の緩やかな分解
    (6) C      --k6-->  C_dead       触媒の失活（別勘定）

質量保存: P + I + A + B は常に一定（素反応がすべて単位を保存する）。
これはテストで検証される、本モデルの健全性条件である。

⚠️ 誠実な注記:
   これは反応速度論の教育用抽象モデルであり、実在の医薬品・試薬・合成手順・
   反応条件を一切含まない。速度定数はすべて説明用の無次元パラメータである。
   実際の創薬は有機合成・薬理評価・臨床試験・規制審査を要し、本シミュレーションから
   実際の化合物や医薬品を作ることはできない。標準ライブラリのみで動作する。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class RateConstants:
    """速度定数（すべて無次元の説明用パラメータ）。"""

    k1: float = 0.25   # P + C -> I + C   触媒開始
    k2: float = 6.00   # P + I + C -> 2I + C  触媒媒介の連鎖成長
    k3: float = 0.35   # I -> A           目的物生成
    k4: float = 0.90   # 2I -> 2B         二分子停止（過分解）
    k5: float = 0.010  # A -> B           目的物の分解
    k6: float = 0.020  # C -> C_dead      触媒失活


@dataclass
class State:
    """濃度状態（無次元）。"""

    P: float = 1.0
    C: float = 0.0
    I: float = 0.0
    A: float = 0.0
    B: float = 0.0
    C_dead: float = 0.0

    def mass(self) -> float:
        """保存量: P 由来の物質収支（触媒は別勘定）。"""
        return self.P + self.I + self.A + self.B

    def as_dict(self) -> Dict[str, float]:
        return {"P": self.P, "C": self.C, "I": self.I,
                "A": self.A, "B": self.B, "C_dead": self.C_dead}


class ReactionNetwork:
    """質量作用則の ODE 系を RK4 で積分する。"""

    def __init__(self, rates: RateConstants | None = None,
                 state: State | None = None, dt: float = 0.02) -> None:
        self.k = rates or RateConstants()
        self.s = state or State()
        self.dt = dt
        self.t = 0.0

    # ---- 右辺（時間微分） ------------------------------------------------- #
    def _derivs(self, y: List[float]) -> List[float]:
        P, C, I, A, B, Cd = y
        k = self.k
        r1 = k.k1 * P * C          # P + C -> I + C
        r2 = k.k2 * P * I * C      # P + I + C -> 2I + C（触媒媒介）
        r3 = k.k3 * I              # I -> A
        r4 = k.k4 * I * I          # 2I -> 2B
        r5 = k.k5 * A              # A -> B
        r6 = k.k6 * C              # C -> C_dead

        dP = -r1 - r2
        dI = r1 + r2 - r3 - 2.0 * r4
        dA = r3 - r5
        dB = 2.0 * r4 + r5
        dC = -r6
        dCd = r6
        return [dP, dC, dI, dA, dB, dCd]

    # ---- RK4 1 ステップ --------------------------------------------------- #
    def step(self, dose: float = 0.0) -> None:
        """
        dt だけ時間を進める。dose > 0 なら触媒剤をその量だけ投与する
        （制御装置が呼ぶ）。
        """
        self.s.C += max(dose, 0.0)
        y = [self.s.P, self.s.C, self.s.I, self.s.A, self.s.B, self.s.C_dead]
        h = self.dt

        k1 = self._derivs(y)
        k2 = self._derivs([y[i] + 0.5 * h * k1[i] for i in range(6)])
        k3 = self._derivs([y[i] + 0.5 * h * k2[i] for i in range(6)])
        k4 = self._derivs([y[i] + h * k3[i] for i in range(6)])
        y = [y[i] + (h / 6.0) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i])
             for i in range(6)]

        # 数値誤差で負濃度になるのを防ぐ（物理的に濃度は非負）
        y = [max(v, 0.0) for v in y]
        self.s = State(P=y[0], C=y[1], I=y[2], A=y[3], B=y[4], C_dead=y[5])
        self.t += h

    # ---- 連鎖の臨界指標 ---------------------------------------------------- #
    def chain_factor(self) -> float:
        """
        連鎖成長率 / 停止率 の比。分岐過程の k_eff に相当する。

            χ = k2·P·C / (k3 + 2·k4·I)

        χ > 1 なら連鎖は自己増殖的に成長（臨界超過 = 暴走）、
        χ < 1 なら停止側が勝ち連鎖は減衰する。連鎖成長段が触媒 C を要するため、
        **投与量 C が χ の直接の制御レバー**になる（C=0 なら χ=0＝連鎖は立たない）。
        制御装置はこの χ を 1 未満に保ちながら収率を稼ぐ。
        """
        k = self.k
        denom = k.k3 + 2.0 * k.k4 * self.s.I
        if denom <= 1e-12:
            return float("inf")
        return (k.k2 * self.s.P * self.s.C) / denom

    # ---- 収率指標（化学量のみ。薬効ではない） ------------------------------ #
    def yield_fraction(self, initial_mass: float) -> float:
        """目的化合物 A の収率 = A / 初期物質量。"""
        return self.s.A / initial_mass if initial_mass > 1e-12 else 0.0

    def purity(self) -> float:
        """粗生成物中の A の割合 = A / (A + B)。"""
        d = self.s.A + self.s.B
        return self.s.A / d if d > 1e-12 else 0.0


if __name__ == "__main__":
    net = ReactionNetwork()
    m0 = net.s.mass()
    net.s.C = 0.20                      # 触媒を一括投与
    print(f"initial mass = {m0:.6f}, chain_factor = {net.chain_factor():.3f}")
    for _ in range(400):
        net.step()
    print(f"t={net.t:.1f}  A={net.s.A:.4f}  B={net.s.B:.4f}  P={net.s.P:.4f}")
    print(f"yield={net.yield_fraction(m0):.3f}  purity={net.purity():.3f}")
    print(f"mass conservation error = {abs(net.s.mass() - m0):.2e}")
