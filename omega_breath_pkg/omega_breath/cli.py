"""cli.py — `omega-breath [pattern] [cycles]` / `omega-breath --sim`

pattern: slow(既定) / coherent / box / 478
"""
from __future__ import annotations
import sys
from .patterns import PATTERNS, get
from .hrv import RSASimulator, resonance_sweep
from .guide import run_guide_safe


def show_simulation() -> None:
    sim = RSASimulator()
    print("=== 呼吸パターン別の心拍変動（モデル計算値） ===")
    print("パターン           回/分   RSA振幅      SDNN")
    for p in PATTERNS.values():
        m = sim.metrics(p)
        print(f"  {p.name:14s} {m['breaths_per_minute']:5.1f}  "
              f"{m['rsa_amplitude']:6.2f}bpm  {m['sdnn_ms']:7.2f}ms")

    print()
    print("=== 共鳴曲線（圧受容器反射の共鳴を探す） ===")
    sweep = resonance_sweep()
    peak = max(sweep, key=lambda br: br[1])
    top = max(v for _, v in sweep)
    for bpm, amp in sweep[::3]:
        bar = "█" * int(round(amp / top * 34))
        mark = "  ← 最大" if abs(bpm - peak[0]) < 1e-9 else ""
        print(f"  {bpm:5.2f}回/分 |{bar:<34}| {amp:5.2f}{mark}")
    print()
    print(f"→ 毎分 {peak[0]:.1f} 回付近で心拍変動が最大になる。これは圧受容器反射の")
    print("  ループ遅延（約5秒）が生む約0.1Hzの共鳴で、コヒーレント呼吸が")
    print("  毎分6回に設定されている理由でもある。")
    print()
    print("注記: 教育用の生理学モデルであり、実測値でも診断でもありません。")


def main() -> int:
    args = [a for a in sys.argv[1:]]
    if args and args[0] in ("--sim", "-s"):
        show_simulation()
        return 0
    if args and args[0] in ("--list", "-l"):
        for k, p in PATTERNS.items():
            print(f"  {k:9s} {p.name:14s} {p.breaths_per_minute:4.1f}回/分  {p.note}")
        return 0

    key = args[0] if args else "slow"
    cycles = int(args[1]) if len(args) > 1 else 4
    try:
        get(key)
    except KeyError as e:
        print(e)
        return 1
    run_guide_safe(key, cycles)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
