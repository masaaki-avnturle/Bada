"""
patterns.py — 呼吸パターン
==========================

呼吸法を「吸う・止める・吐く・止める」の 4 相の長さ（秒）で表す。
時刻 t を渡すと、現在の相と、その相の中での進み具合 (0→1) を返す。

収録パターン（いずれも一般に知られた呼吸法）:
  4-7-8呼吸    : 吸4 / 止7 / 吐8      — 吐く時間が長く、就寝前に用いられる
  ボックス呼吸  : 4 / 4 / 4 / 4        — 落ち着いて集中したいとき
  コヒーレント呼吸: 吸5 / 吐5 (6回/分) — 心拍変動が最大になる共鳴周波数付近
  ゆっくり呼吸  : 吸4 / 吐6            — 吐く方を長くする最小構成

⚠️ 健康法の一般的な紹介であり、医療行為・治療の代替ではない。
   持病がある場合や息苦しさが出る場合は中止し、主治医に相談すること。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class BreathPattern:
    """4相の呼吸パターン（秒）。"""

    name: str
    inhale: float
    hold_in: float
    exhale: float
    hold_out: float
    note: str = ""

    @property
    def cycle(self) -> float:
        """1呼吸の長さ（秒）。"""
        return self.inhale + self.hold_in + self.exhale + self.hold_out

    @property
    def breaths_per_minute(self) -> float:
        return 60.0 / self.cycle

    def phase_at(self, t: float) -> Tuple[str, float]:
        """
        時刻 t（秒）における (相の名前, 相内の進捗0→1) を返す。
        相は "吸う" / "止める" / "吐く" / "止める(空)"。
        """
        u = t % self.cycle
        for name, dur in (("吸う", self.inhale), ("止める", self.hold_in),
                          ("吐く", self.exhale), ("止める(空)", self.hold_out)):
            if dur <= 0.0:
                continue
            if u < dur:
                return name, u / dur
            u -= dur
        return "吐く", 1.0            # 端数の保険

    def lung_volume(self, t: float) -> float:
        """
        肺の充満度 0→1 の近似。吸気で 0→1、呼気で 1→0 に線形変化し、
        保持相では一定。HRV シミュレータの駆動入力に使う。
        """
        phase, p = self.phase_at(t)
        if phase == "吸う":
            return p
        if phase == "止める":
            return 1.0
        if phase == "吐く":
            return 1.0 - p
        return 0.0


PATTERNS: Dict[str, BreathPattern] = {
    "478": BreathPattern(
        "4-7-8呼吸", 4.0, 7.0, 8.0, 0.0,
        "吐く時間を長くとる。就寝前に使われることが多い。"
        "息苦しければ 2-3.5-4 のように半分の長さから始める。",
    ),
    "box": BreathPattern(
        "ボックス呼吸", 4.0, 4.0, 4.0, 4.0,
        "4拍ずつ均等。落ち着いて集中したいときに。",
    ),
    "coherent": BreathPattern(
        "コヒーレント呼吸", 5.0, 0.0, 5.0, 0.0,
        "毎分6回。心拍変動が最も大きくなる共鳴周波数(約0.1Hz)付近。",
    ),
    "slow": BreathPattern(
        "ゆっくり呼吸", 4.0, 0.0, 6.0, 0.0,
        "吐く方を長くするだけの最小構成。どこでもできる。",
    ),
}


def get(key: str) -> BreathPattern:
    if key not in PATTERNS:
        raise KeyError(f"unknown pattern: {key}. 選択肢: {', '.join(PATTERNS)}")
    return PATTERNS[key]


if __name__ == "__main__":
    for k, p in PATTERNS.items():
        print(f"{k:9s} {p.name:14s} 1周期={p.cycle:4.1f}秒 "
              f"({p.breaths_per_minute:.1f}回/分)")
