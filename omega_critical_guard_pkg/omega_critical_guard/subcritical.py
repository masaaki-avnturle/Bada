"""
subcritical.py — 臨界に近づくときの「強度」: 未臨界増倍と安全な接近手順
=======================================================================

臨界点に近づくと何が起きるかを、**強度（増倍率）の発散**として扱う。

中性子源 S を置いた未臨界系では、1 個の中性子が k 個、その k 個がさらに k 個…
と有限等比級数で足し上がり、定常の中性子数は

    N = S · (1 + k + k² + k³ + …) = S / (1 − k)          (k < 1)

に落ち着く。この **M = 1/(1 − k)** を **未臨界増倍率 (subcritical multiplication)**
と呼ぶ。k → 1 で M は発散する。これが「臨界期の強度」の正体であり、
臨界点が近いほど、わずかな操作で応答が跳ね上がる理由でもある。

同時に応答の遅さも発散する（**臨界減速 / critical slowing down**）:

    τ = ℓ / (1 − k)

τ は擾乱が定常へ戻るまでの時定数。k → 1 では系がいつまでも落ち着かなくなる。

--------------------------------------------------------------------------
本モジュールの主題は **1/M 法（逆増倍法）による安全な臨界接近**である。
--------------------------------------------------------------------------

M が発散するということは、その逆数 1/M = 1 − k は臨界点で **0 に向かって
素直に落ちていく**ということでもある。そこで制御量 x に対して 1/M を測り、
直線を臨界（1/M = 0）へ外挿すれば、**まだ到達していない臨界点の位置を
事前に予測できる**。予測地点までの残り距離の半分より先へは進まない、という
規則を守れば、臨界を踏み越えることなく接近できる。

これは原子炉の起動や燃料装荷で実際に使われる標準的な安全手順であり、
「臨界に到達するため」ではなく **「意図せず臨界を越えないため」** の方法である。

⚠️ 誠実な注記:
   本モジュールが扱うのは無次元の実効増倍率 k のみである。実在の核種データ、
   断面積、質量、幾何形状、濃縮度は一切含まず、そこから導くこともできない。
   臨界量や装置の設計には使用できない、教育用の抽象モデルである。
   標準ライブラリのみで動作する。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .chain_model import LCG


# --------------------------------------------------------------------------- #
#  1. 未臨界増倍 — 臨界に近づくほど強度が発散する
# --------------------------------------------------------------------------- #
def multiplication(k: float) -> float:
    """
    未臨界増倍率 M = 1/(1 − k)。
    k → 1 で発散し、k ≥ 1 では定常解が存在しない（∞ を返す）。
    """
    if k >= 1.0:
        return math.inf
    return 1.0 / (1.0 - k)


def inverse_multiplication(k: float) -> float:
    """1/M = 1 − k。臨界で 0 になる、外挿しやすい量。"""
    return max(0.0, 1.0 - k)


def steady_population(k: float, source: float = 1.0) -> float:
    """中性子源 S のもとでの定常中性子数 N = S/(1 − k)。"""
    return source * multiplication(k)


def relaxation_time(k: float, lifetime: float = 1.0e-4) -> float:
    """
    臨界減速: 擾乱が定常へ戻る時定数 τ = ℓ/(1 − k)。
    k → 1 で発散する（応答がいつまでも収まらなくなる）。
    """
    if k >= 1.0:
        return math.inf
    return lifetime / (1.0 - k)


def approach_series(k: float, terms: int = 200, source: float = 1.0) -> float:
    """
    等比級数 S·Σ kⁿ を有限項で足した値。
    項数を増やすと steady_population に収束することを確かめるためのもの。
    """
    total = 0.0
    term = source
    for _ in range(terms):
        total += term
        term *= k
    return total


# --------------------------------------------------------------------------- #
#  2. 1/M 法による安全な臨界接近
# --------------------------------------------------------------------------- #
@dataclass
class Measurement:
    """1 ステップ分の測定。"""

    step: int
    position: float          # 制御量 x（0→1 で臨界へ近づく）
    k_eff: float             # そのときの実効増倍率（真値）
    count_rate: float        # 測定された計数率（M に比例、統計ゆらぎ込み）
    inverse_m: float         # 1/M の測定値
    predicted_critical: float  # このステップまでの外挿で予測した臨界位置
    supercritical: bool      # 臨界を越えてしまったか


@dataclass
class ApproachConfig:
    base_count: float = 1.0e3     # k=0 のときの計数率（源だけの寄与）
    counting_noise: float = 0.02  # 計数率の相対ゆらぎ
    safety_fraction: float = 0.5  # 予測地点までの残り距離のうち進んでよい割合
    min_step: float = 1.0e-3      # これ以下の刻みになったら接近を終える
    max_steps: int = 40


class ApproachToCritical:
    """
    1/M 法で臨界へ安全に近づく手順のシミュレータ。

    k_of_x(x) は制御量 x（例: 燃料装荷量や制御棒の引き抜き量）から実効増倍率を
    返す関数。既定は k(x) = k_max · x の線形モデルで、臨界位置は x_c = 1/k_max。

    各ステップで:
      1. 計数率を測る（M ∝ 計数率）
      2. 1/M を求める
      3. 直近 2 点の直線を 1/M = 0 へ外挿し、臨界位置を予測する
      4. **予測地点までの残り距離の safety_fraction 倍しか進まない**
    """

    def __init__(self, k_of_x: Optional[Callable[[float], float]] = None,
                 cfg: Optional[ApproachConfig] = None,
                 seed: int = 0x51DE) -> None:
        self.cfg = cfg or ApproachConfig()
        self.k_of_x = k_of_x or (lambda x: 1.25 * x)   # 臨界は x = 0.8
        self.rng = LCG(seed)
        self.log: List[Measurement] = []

    # ---- 測定 ------------------------------------------------------------- #
    def measure(self, x: float) -> tuple:
        """位置 x で計数率を測る。(k, count_rate, 1/M) を返す。"""
        k = self.k_of_x(x)
        if k >= 1.0:
            return k, math.inf, 0.0
        rate = self.cfg.base_count * multiplication(k)
        # 計数の統計ゆらぎ（±noise の一様分布で簡略化）
        noise = 1.0 + self.cfg.counting_noise * (2.0 * self.rng.random() - 1.0)
        rate *= noise
        inv_m = self.cfg.base_count / rate      # ≒ 1 − k
        return k, rate, inv_m

    # ---- 外挿 ------------------------------------------------------------- #
    def predict_critical(self) -> float:
        """
        直近 2 点の (x, 1/M) を通る直線を 1/M = 0 へ外挿し、臨界位置を予測する。
        傾きが負（1/M が減っている）でなければ予測不能として inf を返す。
        """
        if len(self.log) < 2:
            return math.inf
        a, b = self.log[-2], self.log[-1]
        dx = b.position - a.position
        dy = b.inverse_m - a.inverse_m
        if dx <= 0.0 or dy >= 0.0:
            return math.inf
        # y = a.inverse_m + (dy/dx)(x − a.position) = 0
        return a.position - a.inverse_m * dx / dy

    # ---- 接近手順 --------------------------------------------------------- #
    def run(self, start: float = 0.05, first_step: float = 0.15) -> List[Measurement]:
        """
        安全規則を守って臨界へ接近する。臨界を越えずに停止できれば成功。
        """
        cfg = self.cfg
        x = start
        step = first_step

        for i in range(cfg.max_steps):
            k, rate, inv_m = self.measure(x)
            over = k >= 1.0
            self.log.append(Measurement(
                step=i, position=x, k_eff=k, count_rate=rate,
                inverse_m=inv_m, predicted_critical=math.inf, supercritical=over,
            ))
            pred = self.predict_critical()
            self.log[-1].predicted_critical = pred

            if over:
                break                     # 越えてしまった（安全規則なしの場合）

            # 予測地点までの残りの safety_fraction 倍しか進まない
            if math.isfinite(pred):
                remaining = pred - x
                if remaining <= 0.0:
                    break
                step = min(step, remaining * cfg.safety_fraction)
            if step < cfg.min_step:
                break                     # 十分近づいたので終了
            x += step

        return self.log

    # ---- 診断 -------------------------------------------------------------- #
    def summary(self) -> Dict[str, float]:
        if not self.log:
            return {}
        last = self.log[-1]
        preds = [m.predicted_critical for m in self.log
                 if math.isfinite(m.predicted_critical)]
        return {
            "steps": float(len(self.log)),
            "final_position": last.position,
            "final_k": last.k_eff,
            "final_multiplication": multiplication(last.k_eff),
            "final_prediction": preds[-1] if preds else math.inf,
            "stayed_subcritical": float(not any(m.supercritical for m in self.log)),
            "max_k": max(m.k_eff for m in self.log),
        }


def run_unsafe_approach(k_of_x: Optional[Callable[[float], float]] = None,
                        fixed_step: float = 0.2,
                        cfg: Optional[ApproachConfig] = None,
                        seed: int = 0x51DE) -> Dict[str, float]:
    """
    比較用: 1/M の外挿を使わず、固定の刻みで進み続けた場合。
    臨界位置を知らないまま踏み越えてしまう。
    """
    cfg = cfg or ApproachConfig()
    kf = k_of_x or (lambda x: 1.25 * x)
    x = 0.05
    max_k = 0.0
    crossed = False
    steps = 0
    for _ in range(cfg.max_steps):
        k = kf(x)
        max_k = max(max_k, k)
        steps += 1
        if k >= 1.0:
            crossed = True
            break
        x += fixed_step
    return {
        "steps": float(steps),
        "final_position": x,
        "max_k": max_k,
        "crossed_critical": float(crossed),
    }


# --------------------------------------------------------------------------- #
#  3. 点炉動特性 — なぜ遅発中性子がなければ制御できないのか
# --------------------------------------------------------------------------- #
@dataclass
class KineticsConfig:
    """
    1 群の点炉動特性パラメータ（いずれも説明用の無次元値）。

    beta   : 遅発中性子割合。核分裂で「すぐに」出ずに遅れて出る中性子の割合。
    Lambda : 即発中性子の世代時間。
    lam    : 遅発中性子先行核の崩壊定数。
    """

    beta: float = 0.0065      # 教科書的な例示値（特定の核種データではない）
    Lambda: float = 1.0e-4
    lam: float = 0.0785


class PointKinetics:
    """
    1 群の点炉動特性方程式:

        dn/dt = (ρ − β)/Λ · n + λ·C
        dC/dt =  β/Λ · n − λ·C

    ρ は反応度（ρ = (k−1)/k）。**ρ < β** である限り、系の応答は遅発中性子の
    タイムスケール（秒〜分）に支配され、ゆっくり動くので制御できる。
    **ρ ≥ β（即発臨界）** に達すると即発中性子だけで連鎖が成立し、応答が
    Λ のタイムスケール（1e-4 秒）に跳ね上がって制御不能になる。

    即発臨界は「近づいてはならない境界」であり、運転はこれよりはるかに
    小さい ρ で行われる。
    """

    def __init__(self, cfg: Optional[KineticsConfig] = None, n0: float = 1.0) -> None:
        self.cfg = cfg or KineticsConfig()
        self.n = n0
        # 初期は臨界定常（ρ=0）で釣り合う先行核濃度
        self.c = self.cfg.beta * n0 / (self.cfg.Lambda * self.cfg.lam)
        self.t = 0.0

    def is_prompt_critical(self, rho: float) -> bool:
        """即発臨界の境界 ρ ≥ β を越えたか。"""
        return rho >= self.cfg.beta

    def _derivs(self, n: float, c: float, rho: float) -> tuple:
        cfg = self.cfg
        dn = (rho - cfg.beta) / cfg.Lambda * n + cfg.lam * c
        dc = cfg.beta / cfg.Lambda * n - cfg.lam * c
        return dn, dc

    def step(self, rho: float, dt: float) -> None:
        """RK4 で 1 ステップ進める。"""
        n, c = self.n, self.c
        k1n, k1c = self._derivs(n, c, rho)
        k2n, k2c = self._derivs(n + 0.5 * dt * k1n, c + 0.5 * dt * k1c, rho)
        k3n, k3c = self._derivs(n + 0.5 * dt * k2n, c + 0.5 * dt * k2c, rho)
        k4n, k4c = self._derivs(n + dt * k3n, c + dt * k3c, rho)
        self.n = max(n + (dt / 6.0) * (k1n + 2 * k2n + 2 * k3n + k4n), 0.0)
        self.c = max(c + (dt / 6.0) * (k1c + 2 * k2c + 2 * k3c + k4c), 0.0)
        self.t += dt

    def run(self, rho: float, duration: float, dt: float = 1.0e-3) -> List[tuple]:
        """(t, n) の時系列を返す。"""
        out = [(self.t, self.n)]
        for _ in range(int(duration / dt)):
            self.step(rho, dt)
            out.append((self.t, self.n))
        return out

    # ---- インアワー方程式 -------------------------------------------------- #
    def period(self, rho: float) -> float:
        """
        安定期（出力が e 倍になる時間）T = 1/ω。
        1 群のインアワー方程式  ρ = ωΛ + ωβ/(ω + λ)  を ω について解く。

        ρ が小さいほど T は長く（ゆっくり）、ρ → β で T → 0 に近づく。
        """
        cfg = self.cfg
        if abs(rho) < 1e-15:
            return math.inf                      # 臨界: 出力は変わらない

        def inhour(w: float) -> float:
            return w * cfg.Lambda + w * cfg.beta / (w + cfg.lam) - rho

        if rho > 0:
            lo, hi = 1e-12, 1.0
            while inhour(hi) < 0.0 and hi < 1e12:
                hi *= 10.0
        else:
            # 負の反応度では ω は負（−λ より大きい側に根がある）
            lo, hi = -cfg.lam + 1e-12, -1e-12
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if inhour(lo) * inhour(mid) <= 0.0:
                hi = mid
            else:
                lo = mid
        w = 0.5 * (lo + hi)
        return math.inf if abs(w) < 1e-15 else 1.0 / w


def reactivity_from_k(k: float) -> float:
    """反応度 ρ = (k − 1)/k。"""
    if abs(k) < 1e-15:
        return -math.inf
    return (k - 1.0) / k


# --------------------------------------------------------------------------- #
#  4. レポート
# --------------------------------------------------------------------------- #
def format_intensity_table(ks: Optional[List[float]] = None,
                           lifetime: float = 1.0e-4) -> str:
    """臨界に近づくにつれ強度と応答時間がどう発散するかの表。"""
    ks = ks or [0.0, 0.5, 0.8, 0.9, 0.95, 0.99, 0.999, 0.9999]
    lines = [
        "=== 臨界に近づくときの強度 (未臨界増倍) ===",
        "",
        "    k_eff      増倍率 M      1/M        緩和時間 τ",
    ]
    for k in ks:
        m = multiplication(k)
        tau = relaxation_time(k, lifetime)
        lines.append(f"  {k:8.4f}  {m:12.2f}  {inverse_multiplication(k):9.5f}  "
                     f"{tau:12.5f}")
    lines += [
        "",
        "  M = 1/(1−k) は k → 1 で発散する。これが『臨界期の強度』である。",
        "  同時に τ = ℓ/(1−k) も発散し、系はいつまでも落ち着かなくなる",
        "  （臨界減速）。1/M は逆に 0 へ素直に落ちるので、外挿に使える。",
    ]
    return "\n".join(lines)


def format_approach_report(approach: ApproachToCritical,
                           unsafe: Optional[Dict[str, float]] = None,
                           x_critical: float = 0.8) -> str:
    """1/M 法による接近手順のレポート。"""
    s = approach.summary()
    lines = [
        "=== 1/M 法による安全な臨界接近 ===",
        "",
        " step   位置 x    k_eff      計数率      1/M     臨界位置の予測",
    ]
    for m in approach.log:
        pred = "     —" if math.isinf(m.predicted_critical) \
            else f"{m.predicted_critical:8.4f}"
        lines.append(f"  {m.step:3d}  {m.position:8.4f}  {m.k_eff:7.4f}  "
                     f"{m.count_rate:10.1f}  {m.inverse_m:7.4f}  {pred}")
    lines += [
        "",
        f"  真の臨界位置       : {x_critical:.4f}",
        f"  最終予測           : {s['final_prediction']:.4f}",
        f"  到達位置           : {s['final_position']:.4f}  (k = {s['final_k']:.4f})",
        f"  最終増倍率 M       : {s['final_multiplication']:.1f}",
        f"  臨界を越えたか     : "
        f"{'いいえ ✓ 未臨界を維持' if s['stayed_subcritical'] else 'はい ✗'}",
    ]
    if unsafe:
        lines += [
            "",
            "--- 比較: 1/M の外挿を使わず固定の刻みで進んだ場合 ---",
            f"  到達位置 {unsafe['final_position']:.4f}  最大 k = {unsafe['max_k']:.4f}",
            f"  臨界を踏み越えた   : "
            f"{'はい ✗' if unsafe['crossed_critical'] else 'いいえ'}",
            "",
            "  → 1/M を外挿すると、まだ到達していない臨界位置が事前に分かる。",
            "    残り距離の半分より先へ進まない規則を守れば踏み越えずに済む。",
        ]
    lines += [
        "",
        "注記: 無次元の k のみを扱う教育用モデル。核種データ・断面積・質量・",
        "      幾何形状は一切含まず、臨界量や装置の設計には使用できない。",
    ]
    return "\n".join(lines)


def format_kinetics_report(cfg: Optional[KineticsConfig] = None) -> str:
    """遅発中性子と即発臨界の境界についてのレポート。"""
    cfg = cfg or KineticsConfig()
    pk = PointKinetics(cfg)
    lines = [
        "=== 点炉動特性: なぜ遅発中性子がないと制御できないのか ===",
        "",
        f"  遅発中性子割合 β = {cfg.beta}   即発中性子世代時間 Λ = {cfg.Lambda}",
        "",
        "    反応度 ρ     ρ/β      安定期 T        状態",
    ]
    for rho in (0.0005, 0.001, 0.002, 0.004, 0.0060, 0.0064):
        T = pk.period(rho)
        state = "即発臨界 ✗" if pk.is_prompt_critical(rho) else "制御可能"
        t_str = "      ∞" if math.isinf(T) else f"{T:9.3f}"
        lines.append(f"  {rho:9.5f}  {rho / cfg.beta:6.3f}  {t_str}      {state}")
    lines += [
        "",
        "  ρ が β よりずっと小さいうちは、応答は遅発中性子のタイムスケールに",
        "  支配されて安定期が長く、人間の操作が間に合う。",
        "  ρ が β に近づくほど T は急激に短くなり、ρ ≥ β（即発臨界）では",
        "  即発中性子だけで連鎖が成立して Λ のタイムスケールになる。",
        "  即発臨界は『近づいてはならない境界』であり、運転はこれよりはるかに",
        "  小さい ρ の範囲で行われる。",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(format_intensity_table())
    print()
    a = ApproachToCritical()
    a.run()
    print(format_approach_report(a, run_unsafe_approach()))
    print()
    print(format_kinetics_report())
