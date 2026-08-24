#!/usr/bin/env python3
"""gen_signal.py — 合成脳信号/熱エネルギー列を生成 (numpy 不要)."""
import math, sys

def neuro(n=24):
    return [((1.0 if i % 2 else -1.0) + 0.03 * ((i * 37) % 5 - 2)) for i in range(n)]

def thermal(n=16):
    return [36.9 + 0.15 * math.sin(0.5 * i) for i in range(n)]

if __name__ == "__main__":
    kind = sys.argv[1] if len(sys.argv) > 1 else "neuro"
    vals = thermal() if kind == "thermal" else neuro()
    print("\n".join(f"{v:.6f}" for v in vals))
