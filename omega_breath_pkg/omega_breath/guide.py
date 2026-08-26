"""
guide.py — 呼吸ガイド（ターミナル表示）
=======================================

呼吸パターンに合わせて、ターミナルにバーを伸縮させながら「吸う/止める/吐く」を
案内する。実時間で動くので、画面に合わせて呼吸するだけでよい。

⚠️ 一般的な健康法の紹介であり、医療行為ではない。息苦しさ・めまいを感じたら
   すぐに中止して普段どおりの呼吸に戻すこと。持病がある場合は主治医に相談を。
"""

from __future__ import annotations

import sys
import time
from typing import Optional

from .patterns import BreathPattern, get


BAR_WIDTH = 40

# 相ごとの表示（記号は等幅で崩れにくいものを選ぶ）
PHASE_STYLE = {
    "吸う": ("▁▂▃▄▅▆▇█", "すーっと吸って"),
    "止める": ("█", "そのまま"),
    "吐く": ("█▇▆▅▄▃▂▁", "ゆーっくり吐いて"),
    "止める(空)": ("▁", "からっぽのまま"),
}


def render_bar(volume: float, width: int = BAR_WIDTH) -> str:
    """肺の充満度 0→1 を横バーで表す。"""
    filled = int(round(volume * width))
    return "█" * filled + "·" * (width - filled)


def run_guide(pattern: BreathPattern, cycles: int = 4,
              stream=None, sleep=time.sleep, fps: float = 12.0) -> int:
    """
    呼吸ガイドを cycles 回分表示する。実行した秒数（整数）を返す。

    stream/sleep を差し替えられるようにしてあるのでテストからも呼べる。
    """
    out = stream if stream is not None else sys.stdout
    total = pattern.cycle * cycles
    frames = int(total * fps)
    dt = 1.0 / fps

    out.write(f"\n{pattern.name} を {cycles} 回。画面に合わせて呼吸してください。\n")
    if pattern.note:
        out.write(f"（{pattern.note}）\n")
    out.write("途中でやめたくなったら Ctrl-C で止めて構いません。\n\n")

    last_phase: Optional[str] = None
    for i in range(frames):
        t = i * dt
        phase, prog = pattern.phase_at(t)
        vol = pattern.lung_volume(t)
        _, message = PHASE_STYLE.get(phase, ("", ""))

        # その相の残り秒数
        dur = {"吸う": pattern.inhale, "止める": pattern.hold_in,
               "吐く": pattern.exhale, "止める(空)": pattern.hold_out}[phase]
        remain = dur * (1.0 - prog)
        cycle_no = int(t // pattern.cycle) + 1

        if phase != last_phase:
            last_phase = phase
        out.write(
            f"\r  [{cycle_no}/{cycles}] {phase:9s} {message:12s} "
            f"|{render_bar(vol)}| あと{remain:4.1f}秒 "
        )
        out.flush()
        sleep(dt)

    out.write("\r" + " " * 100 + "\r")
    out.write("  おつかれさまでした。\n\n")
    out.flush()
    return int(total)


def run_guide_safe(pattern_key: str = "slow", cycles: int = 4) -> int:
    """Ctrl-C を穏やかに受け止める版。CLI から呼ぶ。"""
    p = get(pattern_key)
    try:
        return run_guide(p, cycles)
    except KeyboardInterrupt:
        sys.stdout.write("\r" + " " * 100 + "\r")
        sys.stdout.write("  ここまでで大丈夫です。おつかれさまでした。\n\n")
        return 0


if __name__ == "__main__":
    run_guide_safe("slow", cycles=2)
