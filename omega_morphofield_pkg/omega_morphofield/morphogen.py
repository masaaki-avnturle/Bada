"""
morphogen.py — 形態形成場（反応拡散系）と電磁誘導ドリフト
=========================================================

チューリングの形態形成理論に基づく **Gray-Scott 反応拡散系** を 2 次元格子で解く。

    ∂u/∂t = Du∇²u − u·v² + F(1−u) − (E·∇)u
    ∂v/∂t = Dv∇²v + u·v² − (F+k)v − (E·∇)v

    u : 基質（供給される側）
    v : 活性因子（自己触媒的に増える側）
    F : 供給率, k : 除去率
    E : **外部場のドリフト速度ベクトル**（電磁誘導の項）

パラメータを (F, k) = (0.030, 0.0565) 付近に取ると、斑点が成長して
**2つに分裂する**挙動が現れる。この領域は文献で "mitosis"（有糸分裂）領域と
呼ばれ、細胞分裂を思わせるパターンが自発的に生じる。本モジュールの
「細胞分岐」はこの分裂パターンを指す。

外部場 E は移流項として入り、パターン全体を場の方向へドリフトさせる。
生体で直流電場が細胞遊走の向きを変える現象（電気走性 / galvanotaxis）は
実在するが、**本モデルはその定量的再現ではなく、場が空間パターンを操作
できることを示す抽象モデル**である。

⚠️ 教育・研究用の数値シミュレーション。実在の細胞・組織・医療機器の
   モデルではなく、医療目的に使えるものではない。標準ライブラリのみで動作。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple, Dict


@dataclass
class FieldConfig:
    n: int = 64            # 格子サイズ (n×n, 周期境界)
    Du: float = 0.16       # 基質の拡散係数
    Dv: float = 0.08       # 活性因子の拡散係数
    F: float = 0.0300      # 供給率（分裂領域）
    k: float = 0.0565      # 除去率（分裂領域）
    dt: float = 1.0        # 時間刻み
    Ex: float = 0.0        # 外部場ドリフト x 成分
    Ey: float = 0.0        # 外部場ドリフト y 成分


class MorphogenField:
    """
    形態形成場。u/v を 1 次元リストで保持し、周期境界で解く。

    - seed_spot()      : 中央に活性因子の種を置く（分裂の起点）
    - step()           : 1 時刻進める
    - count_spots()    : 分裂して増えた「細胞」の数を数える
    - centroid()       : パターンの重心（場によるドリフトの計測に使う）
    """

    def __init__(self, cfg: FieldConfig | None = None) -> None:
        self.cfg = cfg or FieldConfig()
        n = self.cfg.n
        self.u: List[float] = [1.0] * (n * n)
        self.v: List[float] = [0.0] * (n * n)
        self.t = 0.0
        # 周期境界の近傍インデックスを前計算（内側ループを速くする）
        self._nb = self._build_neighbors(n)

    @staticmethod
    def _build_neighbors(n: int) -> List[Tuple[int, int, int, int]]:
        nb = []
        for j in range(n):
            for i in range(n):
                left = j * n + (i - 1) % n
                right = j * n + (i + 1) % n
                up = ((j - 1) % n) * n + i
                down = ((j + 1) % n) * n + i
                nb.append((left, right, up, down))
        return nb

    # ---- 初期化 ------------------------------------------------------------ #
    def seed_spot(self, radius: int = 4, cx: int | None = None,
                  cy: int | None = None, amp: float = 0.5) -> None:
        """中央（または指定位置）に活性因子の種を置く。"""
        n = self.cfg.n
        cx = n // 2 if cx is None else cx
        cy = n // 2 if cy is None else cy
        for j in range(n):
            for i in range(n):
                if (i - cx) ** 2 + (j - cy) ** 2 <= radius * radius:
                    idx = j * n + i
                    self.u[idx] = 1.0 - amp
                    self.v[idx] = amp

    def set_field(self, Ex: float, Ey: float) -> None:
        """外部場（電磁誘導ドリフト）を設定する。"""
        self.cfg.Ex, self.cfg.Ey = Ex, Ey

    # ---- 時間発展 ---------------------------------------------------------- #
    def step(self) -> None:
        c = self.cfg
        n = c.n
        u, v, nb = self.u, self.v, self._nb
        Ex, Ey, dt = c.Ex, c.Ey, c.dt
        new_u = [0.0] * (n * n)
        new_v = [0.0] * (n * n)

        for idx in range(n * n):
            l, r, up, dn = nb[idx]
            ui, vi = u[idx], v[idx]

            lap_u = u[l] + u[r] + u[up] + u[dn] - 4.0 * ui
            lap_v = v[l] + v[r] + v[up] + v[dn] - 4.0 * vi

            # 移流項は風上差分（安定性のため場の向きに応じて片側差分を選ぶ）
            adv_u = adv_v = 0.0
            if Ex > 0.0:
                adv_u += Ex * (ui - u[l]); adv_v += Ex * (vi - v[l])
            elif Ex < 0.0:
                adv_u += Ex * (u[r] - ui); adv_v += Ex * (v[r] - vi)
            if Ey > 0.0:
                adv_u += Ey * (ui - u[up]); adv_v += Ey * (vi - v[up])
            elif Ey < 0.0:
                adv_u += Ey * (u[dn] - ui); adv_v += Ey * (v[dn] - vi)

            uvv = ui * vi * vi
            du = c.Du * lap_u - uvv + c.F * (1.0 - ui) - adv_u
            dv = c.Dv * lap_v + uvv - (c.F + c.k) * vi - adv_v

            # 濃度は [0,1] の範囲に収める（数値誤差での逸脱を防ぐ）
            new_u[idx] = min(max(ui + dt * du, 0.0), 1.0)
            new_v[idx] = min(max(vi + dt * dv, 0.0), 1.0)

        self.u, self.v = new_u, new_v
        self.t += dt

    def run(self, steps: int) -> None:
        for _ in range(steps):
            self.step()

    # ---- 計測 -------------------------------------------------------------- #
    def total_activator(self) -> float:
        return sum(self.v)

    def count_spots(self, threshold: float = 0.25) -> int:
        """
        しきい値を超える連結領域の数 = 分裂してできた「細胞」の個数。
        周期境界を考慮した幅優先探索で数える。
        """
        n = self.cfg.n
        seen = [False] * (n * n)
        count = 0
        for start in range(n * n):
            if seen[start] or self.v[start] <= threshold:
                continue
            count += 1
            stack = [start]
            seen[start] = True
            while stack:
                idx = stack.pop()
                for nxt in self._nb[idx]:
                    if not seen[nxt] and self.v[nxt] > threshold:
                        seen[nxt] = True
                        stack.append(nxt)
        return count

    def centroid(self, threshold: float = 0.1) -> Tuple[float, float]:
        """
        活性因子の重心 (x, y)。周期境界のため円周平均で求める。
        外部場によるドリフトの計測に使う。
        """
        n = self.cfg.n
        sx = sy = cx = cy = w = 0.0
        for j in range(n):
            for i in range(n):
                val = self.v[j * n + i]
                if val <= threshold:
                    continue
                ax, ay = 2 * math.pi * i / n, 2 * math.pi * j / n
                sx += val * math.sin(ax); cx += val * math.cos(ax)
                sy += val * math.sin(ay); cy += val * math.cos(ay)
                w += val
        if w <= 1e-12:
            return (0.0, 0.0)
        x = (math.atan2(sx, cx) % (2 * math.pi)) * n / (2 * math.pi)
        y = (math.atan2(sy, cy) % (2 * math.pi)) * n / (2 * math.pi)
        return (x, y)

    def summary(self) -> Dict[str, float]:
        cx, cy = self.centroid()
        return {
            "t": self.t,
            "spots": float(self.count_spots()),
            "total_activator": self.total_activator(),
            "centroid_x": cx,
            "centroid_y": cy,
        }

    # ---- 表示 -------------------------------------------------------------- #
    def render(self, threshold_levels: str = " ·:+*#") -> str:
        """活性因子の分布をアスキーアートで描く。"""
        n = self.cfg.n
        levels = len(threshold_levels) - 1
        rows = []
        for j in range(n):
            row = []
            for i in range(n):
                val = self.v[j * n + i]
                row.append(threshold_levels[min(levels, int(val * levels * 2.2))])
            rows.append("".join(row))
        return "\n".join(rows)


if __name__ == "__main__":
    f = MorphogenField(FieldConfig(n=48))
    f.seed_spot(radius=3)
    for phase in range(4):
        f.run(1200)
        s = f.summary()
        print(f"t={s['t']:7.0f}  細胞数={int(s['spots']):3d}  "
              f"活性因子総量={s['total_activator']:8.2f}")
