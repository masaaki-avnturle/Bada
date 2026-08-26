"""
hrv.py — 呼吸性洞性不整脈 (RSA) と圧受容器反射の共鳴モデル
==========================================================

呼吸に伴って心拍が変動する現象を **呼吸性洞性不整脈 (RSA)** という。
息を吸うと心拍が速まり、吐くと遅くなる。これは迷走神経を介した実在の生理現象で、
一般に心拍変動 (HRV) が大きいほど自律神経の柔軟性の指標とされる。

さらに、血圧を一定に保つ **圧受容器反射 (baroreflex)** のループには約5秒の
遅れがあり、系全体が **約0.1 Hz（毎分6回）に共鳴周波数**を持つ。そのため
毎分6回前後で呼吸すると心拍変動が最も大きくなる。これが「コヒーレント呼吸」が
毎分6回に設定されている理由である。

本モジュールはこの反射ループを 2次の減衰共振系としてモデル化する:

    x'' + 2ζω₀x' + ω₀²x = ω₀²·u(t)

    u(t) : 呼吸による駆動（肺の充満度を中心化したもの）
    ω₀   : 共鳴角周波数 = 2π·0.1 rad/s
    x    : 心拍数の変動分

RK4 で積分し、定常状態での心拍振幅と SDNN 相当値を求める。

⚠️ 教育目的の生理学モデルであり、医療機器でも診断ツールでもない。
   実際の心拍を測定するものではなく、計算されるのはモデル上の数値である。
   標準ライブラリのみで動作する。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .patterns import BreathPattern


@dataclass
class HRVConfig:
    hr_base: float = 66.0        # 安静時心拍数 (bpm)
    resonance_hz: float = 0.10   # 圧受容器反射の共鳴周波数 (Hz)
    damping: float = 0.22        # 減衰比 ζ（小さいほど共鳴が鋭い）
    gain: float = 3.0            # 呼吸→心拍のゲイン (bpm)
    dt: float = 0.05             # 積分刻み (秒)
    warmup: float = 60.0         # 過渡応答を捨てる時間 (秒)
    duration: float = 180.0      # 総シミュレーション時間 (秒)


class RSASimulator:
    """呼吸パターンを入力に、心拍変動の時系列を生成する。"""

    def __init__(self, cfg: HRVConfig | None = None) -> None:
        self.cfg = cfg or HRVConfig()

    # ---- 2次共振系の右辺 -------------------------------------------------- #
    def _derivs(self, x: float, v: float, u: float) -> Tuple[float, float]:
        c = self.cfg
        w0 = 2.0 * math.pi * c.resonance_hz
        dx = v
        dv = w0 * w0 * (u - x) - 2.0 * c.damping * w0 * v
        return dx, dv

    def simulate(self, pattern: BreathPattern) -> Dict[str, List[float]]:
        """
        心拍数の時系列を計算する。
        戻り値: {"t": [...], "hr": [...], "volume": [...]}（過渡応答を除いた分）
        """
        c = self.cfg
        t, x, v = 0.0, 0.0, 0.0
        ts: List[float] = []
        hrs: List[float] = []
        vols: List[float] = []

        n = int(c.duration / c.dt)
        for _ in range(n):
            # 呼吸駆動: 肺の充満度を [-1, 1] に中心化
            def drive(tt: float) -> float:
                return 2.0 * pattern.lung_volume(tt) - 1.0

            h = c.dt
            k1x, k1v = self._derivs(x, v, drive(t))
            k2x, k2v = self._derivs(x + 0.5 * h * k1x, v + 0.5 * h * k1v,
                                    drive(t + 0.5 * h))
            k3x, k3v = self._derivs(x + 0.5 * h * k2x, v + 0.5 * h * k2v,
                                    drive(t + 0.5 * h))
            k4x, k4v = self._derivs(x + h * k3x, v + h * k3v, drive(t + h))
            x += (h / 6.0) * (k1x + 2 * k2x + 2 * k3x + k4x)
            v += (h / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
            t += h

            if t >= c.warmup:
                ts.append(t)
                hrs.append(c.hr_base + c.gain * x)
                vols.append(pattern.lung_volume(t))

        return {"t": ts, "hr": hrs, "volume": vols}

    # ---- 指標 -------------------------------------------------------------- #
    def metrics(self, pattern: BreathPattern) -> Dict[str, float]:
        """
        RSA 振幅（心拍の振れ幅, bpm）と SDNN 相当値（RR間隔の標準偏差, ms）。
        いずれもモデル上の計算値であり、実測値ではない。
        """
        sim = self.simulate(pattern)
        hr = sim["hr"]
        if not hr:
            return {"rsa_amplitude": 0.0, "sdnn_ms": 0.0, "mean_hr": 0.0}

        rsa = max(hr) - min(hr)
        rr = [60000.0 / h for h in hr if h > 1e-6]      # RR間隔 (ms)
        mean_rr = sum(rr) / len(rr)
        var = sum((r - mean_rr) ** 2 for r in rr) / len(rr)
        return {
            "rsa_amplitude": rsa,
            "sdnn_ms": math.sqrt(var),
            "mean_hr": sum(hr) / len(hr),
            "breaths_per_minute": pattern.breaths_per_minute,
        }


def resonance_sweep(cfg: HRVConfig | None = None,
                    periods: List[float] | None = None) -> List[Tuple[float, float]]:
    """
    呼吸周期を変えて RSA 振幅を測り、共鳴の山を探す。
    戻り値: [(呼吸回数/分, RSA振幅), ...]
    """
    from .patterns import BreathPattern

    sim = RSASimulator(cfg)
    if periods is None:
        periods = [4.0 + 0.5 * i for i in range(33)]     # 4〜20秒
    out: List[Tuple[float, float]] = []
    for cycle in periods:
        # 吸う:吐く = 1:1 の単純パターンで周期だけを変える
        p = BreathPattern(f"{cycle:.1f}s", cycle / 2, 0.0, cycle / 2, 0.0)
        m = sim.metrics(p)
        out.append((p.breaths_per_minute, m["rsa_amplitude"]))
    return out


if __name__ == "__main__":
    from .patterns import PATTERNS

    sim = RSASimulator()
    print("パターン別のモデル上の心拍変動:")
    for key, p in PATTERNS.items():
        m = sim.metrics(p)
        print(f"  {p.name:14s} {m['breaths_per_minute']:5.1f}回/分  "
              f"RSA振幅={m['rsa_amplitude']:5.2f}bpm  SDNN={m['sdnn_ms']:6.2f}ms")

    print()
    sweep = resonance_sweep()
    best = max(sweep, key=lambda br: br[1])
    print(f"共鳴の山: {best[0]:.2f} 回/分 で RSA 振幅 {best[1]:.2f} bpm が最大")
