"""
tumor_dynamics.py — 腫瘍の増殖停滞と耐性競合の個体群動態
=========================================================

「腫瘍が停滞する（stasis）」という現象を、**数理腫瘍学の個体群動態モデル**として
扱う。扱うのは細胞集団の増減であって、薬の成分でも用量でもない。

モデル: Gompertz 増殖 + 感受性/耐性の 2 集団競合

    dS/dt = r_S · S · ln(K/(S+R)) − ε(t)·κ·S
    dR/dt = r_R · R · ln(K/(S+R))

    S : 治療感受性クローン
    R : 治療耐性クローン（耐性のコストとして r_R < r_S）
    K : 環境収容力（栄養・空間の上限）
    ε(t) ∈ [0,1] : **無次元の治療強度パラメータ**
    κ : 感受性クローンへの効果係数

ここで ε は **薬の用量でも成分濃度でもない**。「感受性クローンの死亡率が
どれだけ上がるか」を 0〜1 で表しただけの抽象パラメータである。

本モデルが示すこと — 停滞は「強く叩くこと」では得られない:
  S と R は同じ K を奪い合っている。ε を上げ続けて S を消し去ると、
  S による競合抑制が外れて R が空いた席を占め、腫瘍は再増殖する
  （competitive release）。逆に S をあえて残す断続的な治療は、S に R を
  抑えさせ続けるため、腫瘍全体が長く**停滞**する。

これは Gatenby らの適応療法(adaptive therapy)や Goldie-Coldman の耐性理論で
知られる、実在する数理的帰結である。

⚠️ 教育・研究用の抽象モデルであり、治療方針の助言ではない。実在の薬剤・
   成分・用量・投与計画は一切含まず、そこから導くこともできない。
   実際のがん治療は主治医と決めるものである。標準ライブラリのみで動作。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class TumorConfig:
    r_S: float = 0.030        # 感受性クローンの増殖率
    r_R: float = 0.021        # 耐性クローンの増殖率（耐性のコストで低い）
    K: float = 1.0e4          # 環境収容力（細胞数の上限）
    kappa: float = 0.055      # 治療強度1あたりの感受性クローン死亡率
    S0: float = 8.0e3         # 感受性クローンの初期数
    R0: float = 4.0e1         # 耐性クローンの初期数（わずかに存在）
    dt: float = 0.25          # 時間刻み（日相当）
    duration: float = 900.0   # 観察期間


@dataclass
class TumorFrame:
    t: float
    S: float
    R: float
    epsilon: float

    @property
    def total(self) -> float:
        return self.S + self.R


class TumorModel:
    """Gompertz 増殖 + 耐性競合の 2 集団モデル（RK4 積分）。"""

    def __init__(self, cfg: TumorConfig | None = None) -> None:
        self.cfg = cfg or TumorConfig()
        self.S = self.cfg.S0
        self.R = self.cfg.R0
        self.t = 0.0
        self.log: List[TumorFrame] = []

    @property
    def total(self) -> float:
        return self.S + self.R

    def _derivs(self, S: float, R: float, eps: float):
        c = self.cfg
        N = max(S + R, 1e-9)
        growth = math.log(c.K / N) if N < c.K else 0.0   # 収容力超過では増殖せず
        dS = c.r_S * S * growth - eps * c.kappa * S
        dR = c.r_R * R * growth
        return dS, dR

    def step(self, eps: float) -> None:
        h = self.cfg.dt
        S, R = self.S, self.R
        k1S, k1R = self._derivs(S, R, eps)
        k2S, k2R = self._derivs(S + 0.5 * h * k1S, R + 0.5 * h * k1R, eps)
        k3S, k3R = self._derivs(S + 0.5 * h * k2S, R + 0.5 * h * k2R, eps)
        k4S, k4R = self._derivs(S + h * k3S, R + h * k3R, eps)
        self.S = max(S + (h / 6.0) * (k1S + 2 * k2S + 2 * k3S + k4S), 0.0)
        self.R = max(R + (h / 6.0) * (k1R + 2 * k2R + 2 * k3R + k4R), 0.0)
        self.t += h
        self.log.append(TumorFrame(self.t, self.S, self.R, eps))

    def run(self, policy: Callable[["TumorModel"], float],
            duration: float | None = None) -> List[TumorFrame]:
        """policy(model) -> 治療強度 ε を毎ステップ呼び出して進める。"""
        d = duration if duration is not None else self.cfg.duration
        n = int(d / self.cfg.dt)
        for _ in range(n):
            self.step(min(max(policy(self), 0.0), 1.0))
        return self.log

    # ---- 評価指標 ---------------------------------------------------------- #
    def summary(self) -> Dict[str, float]:
        if not self.log:
            return {}
        n0 = self.cfg.S0 + self.cfg.R0
        totals = [f.total for f in self.log]
        # 進行までの時間: 初期腫瘍量の1.2倍を最初に超えた時刻
        progression = float("inf")
        for f in self.log:
            if f.total > 1.2 * n0:
                progression = f.t
                break
        # 停滞: 後半の腫瘍量が初期の1.2倍以内に収まっているか
        tail = [f.total for f in self.log[len(self.log) // 2:]]
        return {
            "final_total": totals[-1],
            "final_S": self.S,
            "final_R": self.R,
            "resistant_fraction": self.R / max(self.total, 1e-9),
            "max_total": max(totals),
            "time_to_progression": progression,
            "stalled": float(max(tail) <= 1.2 * n0),
            "treatment_fraction": sum(1 for f in self.log if f.epsilon > 0.0)
                                  / len(self.log),
        }


# --------------------------------------------------------------------------- #
#  治療強度の方針（いずれも用量ではなく無次元パラメータ ε の与え方）
# --------------------------------------------------------------------------- #
def policy_none(_: TumorModel) -> float:
    """無治療。"""
    return 0.0


def policy_continuous(_: TumorModel) -> float:
    """常時最大強度（ε=1 を掛け続ける）。"""
    return 1.0


def make_adaptive_policy(on_ratio: float = 1.0, off_ratio: float = 0.9,
                         epsilon: float = 1.0) -> Callable[[TumorModel], float]:
    """
    適応方針: 腫瘍量が初期の on_ratio 倍まで戻ったら治療を入れ、
    off_ratio 倍まで減ったら止める（ヒステリシス）。
    感受性クローンをあえて残し、耐性クローンを競合で抑えさせる。
    """
    state = {"on": True}

    def policy(m: TumorModel) -> float:
        n0 = m.cfg.S0 + m.cfg.R0
        n = m.total
        if state["on"] and n <= off_ratio * n0:
            state["on"] = False
        elif not state["on"] and n >= on_ratio * n0:
            state["on"] = True
        return epsilon if state["on"] else 0.0

    return policy


def compare_policies(cfg: TumorConfig | None = None) -> Dict[str, Dict[str, float]]:
    """3 方針を同一条件で比較する。"""
    out: Dict[str, Dict[str, float]] = {}
    for name, pol in (("無治療", policy_none),
                      ("常時最大強度", policy_continuous),
                      ("適応的（断続）", make_adaptive_policy())):
        m = TumorModel(cfg)
        m.run(pol)
        out[name] = m.summary()
    return out


def format_comparison(results: Dict[str, Dict[str, float]]) -> str:
    lines = ["=== 治療方針と腫瘍動態の比較（抽象モデル） ===", ""]
    lines.append("方針             最終腫瘍量   耐性割合   進行までの時間   停滞")
    for name, s in results.items():
        ttp = s["time_to_progression"]
        ttp_str = "  達せず" if math.isinf(ttp) else f"{ttp:7.1f}"
        lines.append(
            f"  {name:14s} {s['final_total']:9.1f}   "
            f"{s['resistant_fraction']:6.1%}   {ttp_str}       "
            f"{'はい ✓' if s['stalled'] else 'いいえ'}")
    lines += [
        "",
        "常時最大強度では感受性クローンが消え、競合から解放された耐性クローンが",
        "空いた席を占めて再増殖する（competitive release）。感受性クローンをあえて",
        "残す断続的な方針では、耐性クローンが抑え込まれ腫瘍量が停滞する。",
        "",
        "注記: ε は用量でも成分濃度でもなく、感受性クローンの死亡率を 0〜1 で",
        "      表した無次元パラメータ。本モデルは治療方針の助言ではありません。",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(format_comparison(compare_policies()))
