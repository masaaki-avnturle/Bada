"""
gamma_manifold.py — 大域的部分積分多様体 (Global Integration-by-Parts Manifold)
=================================================================================

ガンマ関数 Γ(s) = ∫_0^∞ t^{s-1} e^{-t} dt に対する部分積分（integration by
parts）は、大域的な漸化関係

        Γ(s + 1) = s · Γ(s)

を生む。これは「局所的な微小変化(dt)を、大域的な状態の再帰関係に畳み込む」
操作とみなせる。本モジュールは、この漸化構造を状態遷移の核として実装し、
上位のエージェント (agent.py) が思考ステップを「多様体上の再帰」として
進めるための数学的土台を提供する。

依存ライブラリなし（標準ライブラリの math のみ）。実機で動作する。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List


# --------------------------------------------------------------------------- #
#  1. ガンマ関数と部分積分漸化
# --------------------------------------------------------------------------- #
def log_gamma(s: float) -> float:
    """log Γ(s)。標準ライブラリの Lanczos 実装 (math.lgamma) を用いる。"""
    return math.lgamma(s)


def gamma(s: float) -> float:
    """Γ(s)。math.gamma は極 (s = 0, -1, -2, ...) で ValueError を出す。"""
    return math.gamma(s)


def ibp_recurrence(s: float) -> float:
    """
    部分積分が与える大域的漸化 Γ(s+1) = s·Γ(s)。

    これを「1ステップ前進」演算子として返す。数値的には
    Γ(s+1)/Γ(s) = s を検証できる恒等式であり、後段の状態更新の
    正規化係数として使う。
    """
    return s


def digamma(s: float, h: float = 1e-6) -> float:
    """
    ディガンマ関数 ψ(s) = d/ds log Γ(s) を中心差分で近似。
    部分積分多様体上の「勾配（自然な変化方向）」を与える。
    """
    return (log_gamma(s + h) - log_gamma(s - h)) / (2.0 * h)


# --------------------------------------------------------------------------- #
#  2. 多様体上の状態
# --------------------------------------------------------------------------- #
@dataclass
class ManifoldState:
    """
    部分積分多様体上の 1 点。

    s      : ガンマ関数のパラメータ（状態の「位相」）
    weight : その状態が持つ大域的重み（log スケールで保持し overflow を防ぐ）
    label  : 人が読むためのタグ
    """

    s: float
    log_weight: float = 0.0
    label: str = ""

    @property
    def weight(self) -> float:
        return math.exp(self.log_weight)

    def advance(self) -> "ManifoldState":
        """
        部分積分漸化を 1 回適用して次状態へ。
        Γ(s+1) = s·Γ(s) なので log_weight に log|s| を加算する。
        s <= 0 の極近傍は微小量だけずらして特異点を回避する。
        """
        s = self.s if self.s > 1e-9 else 1e-9
        return ManifoldState(
            s=s + 1.0,
            log_weight=self.log_weight + math.log(abs(ibp_recurrence(s))),
            label=self.label,
        )


# --------------------------------------------------------------------------- #
#  3. 大域的部分積分多様体
# --------------------------------------------------------------------------- #
class GammaManifold:
    """
    複数の ManifoldState を束ねた多様体。

    - register() で状態を登録
    - step()     で全状態を部分積分漸化で 1 歩進める
    - softmax()  で大域重みから正規化分布（注意/選択確率）を返す
    """

    def __init__(self) -> None:
        self.states: List[ManifoldState] = []
        self.epoch: int = 0

    def register(self, s: float, label: str = "") -> ManifoldState:
        st = ManifoldState(s=s, label=label)
        self.states.append(st)
        return st

    def step(self) -> None:
        self.states = [st.advance() for st in self.states]
        self.epoch += 1

    def softmax(self, temperature: float = 1.0) -> List[float]:
        """
        log_weight を温度付き softmax で確率分布に変換。
        これがエージェントの「どの状態に注意を向けるか」の分布になる。
        """
        if not self.states:
            return []
        logits = [st.log_weight / max(temperature, 1e-9) for st in self.states]
        m = max(logits)
        exps = [math.exp(l - m) for l in logits]
        z = sum(exps)
        return [e / z for e in exps]

    def dominant(self) -> ManifoldState:
        """最も大域重みの大きい状態を返す。"""
        return max(self.states, key=lambda st: st.log_weight)


# --------------------------------------------------------------------------- #
#  4. 自己検証（恒等式のチェック）
# --------------------------------------------------------------------------- #
def self_check() -> bool:
    """
    Γ(s+1) = s·Γ(s) が数値的に成り立つことを確認する。
    パッケージの健全性テストとして使う。
    """
    ok = True
    for s in (0.5, 1.0, 2.3, 4.7, 9.0):
        lhs = gamma(s + 1.0)
        rhs = s * gamma(s)
        if not math.isclose(lhs, rhs, rel_tol=1e-9):
            ok = False
    return ok


if __name__ == "__main__":
    print("Γ(s+1)=s·Γ(s) self-check:", "PASS" if self_check() else "FAIL")
    m = GammaManifold()
    for s, name in [(1.0, "reason"), (2.0, "recall"), (0.5, "explore")]:
        m.register(s, name)
    for _ in range(3):
        m.step()
    dist = m.softmax(temperature=2.0)
    for st, p in zip(m.states, dist):
        print(f"  {st.label:8s} s={st.s:5.2f}  p={p:.3f}")
