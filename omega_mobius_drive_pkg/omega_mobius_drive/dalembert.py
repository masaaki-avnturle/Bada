"""
dalembert.py — ダランベルシアン / 反ダランベルシアン場ソルバ
=============================================================

ダランベルシアン（波動作用素）:

    □ φ = (1/c²) ∂²φ/∂t² − ∂²φ/∂x²

これを 1 次元格子で陽的差分により時間発展させる。通常の □φ = 0 は波動方程式。
本モジュールでは、リポジトリの世界観にある「反ダランベルシアン
(anti-d'Alembertian)」を、**符号を反転した楕円型化 + 局所ソース項** として
数値実験できるようにする：

    □φ = −κ · S(x,t)      (κ: 結合定数, S: メビウス回路が供給する制御ソース)

これを「反重力発生器」と呼ぶ設定だが、物理的に重力を打ち消す装置ではない。
あくまで場の数値シミュレーション（研究・教育・アート）であり、得られるのは
格子上の場 φ と、その勾配から定義した見かけの「浮揚指標(lift index)」という
スカラー診断値にすぎない。

⚠️ 誠実な注記: 現実の反重力・反重力発生器は存在しない。ここで計算されるのは
   波動場のシミュレーション値であって、実際の力や加速度ではない。
   標準ライブラリのみで動作する。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class FieldConfig:
    nx: int = 128          # 空間格子点
    dx: float = 1.0        # 空間刻み
    dt: float = 0.5        # 時間刻み
    c: float = 1.0         # 波速
    kappa: float = 0.05    # 反ダランベルシアン結合定数

    @property
    def courant(self) -> float:
        """CFL 数 c·dt/dx。安定には <= 1 が必要。"""
        return self.c * self.dt / self.dx


class DAlembertField:
    """
    1D ダランベルシアン場の陽的差分ソルバ。

    step() で 1 時刻進める。source_fn(x, t) が反ダランベルシアンの制御ソース
    S(x,t)（通常はメビウス制御装置が供給）。
    """

    def __init__(self, cfg: FieldConfig | None = None) -> None:
        self.cfg = cfg or FieldConfig()
        if self.cfg.courant > 1.0 + 1e-12:
            raise ValueError(
                f"CFL条件違反: courant={self.cfg.courant:.3f} > 1. dt を小さく."
            )
        n = self.cfg.nx
        self.phi_prev: List[float] = [0.0] * n
        self.phi: List[float] = [0.0] * n
        self.t = 0.0
        self.anti = True   # True: 反ダランベルシアン(ソース符号反転)

    def seed_gaussian(self, center: Optional[int] = None, amp: float = 1.0,
                      width: float = 6.0) -> None:
        n = self.cfg.nx
        c = n // 2 if center is None else center
        for i in range(n):
            self.phi[i] = amp * math.exp(-((i - c) ** 2) / (2 * width * width))
        self.phi_prev = list(self.phi)

    def step(self, source_fn: Optional[Callable[[int, float], float]] = None) -> None:
        cfg = self.cfg
        n = cfg.nx
        r2 = (cfg.c * cfg.dt / cfg.dx) ** 2
        new = [0.0] * n
        for i in range(n):
            left = self.phi[i - 1] if i > 0 else self.phi[i]
            right = self.phi[i + 1] if i < n - 1 else self.phi[i]
            lap = left - 2.0 * self.phi[i] + right      # ∂²φ/∂x²
            # □φ=0 の標準更新
            val = 2.0 * self.phi[i] - self.phi_prev[i] + r2 * lap
            if source_fn is not None:
                s = source_fn(i, self.t)
                sign = -1.0 if self.anti else 1.0        # 反ダランベルシアンは符号反転
                val += sign * cfg.kappa * (cfg.dt ** 2) * s
            new[i] = val
        self.phi_prev = self.phi
        self.phi = new
        self.t += cfg.dt

    # ---- 診断値 ---------------------------------------------------------- #
    def energy(self) -> float:
        """離散場エネルギー（∝ Σ φ² + 勾配²）。有限で安定していることの目安。"""
        cfg = self.cfg
        e = 0.0
        for i in range(cfg.nx):
            right = self.phi[i + 1] if i < cfg.nx - 1 else self.phi[i]
            grad = (right - self.phi[i]) / cfg.dx
            e += 0.5 * (self.phi[i] ** 2 + grad ** 2)
        return e

    def lift_index(self) -> float:
        """
        見かけの「浮揚指標」: 場の非対称勾配の総和。
        物理的な揚力ではなく、シミュレーション上の診断スカラー。
        """
        cfg = self.cfg
        s = 0.0
        for i in range(cfg.nx):
            right = self.phi[i + 1] if i < cfg.nx - 1 else self.phi[i]
            s += (right - self.phi[i])
        return s


if __name__ == "__main__":
    f = DAlembertField(FieldConfig(nx=64, dt=0.4))
    f.seed_gaussian(amp=1.0)
    print(f"CFL={f.cfg.courant:.3f}")
    for k in range(20):
        f.step(source_fn=lambda i, t: math.sin(0.3 * t) if i == 32 else 0.0)
    print(f"t={f.t:.1f}  energy={f.energy():.4f}  lift_index={f.lift_index():.4e}")
