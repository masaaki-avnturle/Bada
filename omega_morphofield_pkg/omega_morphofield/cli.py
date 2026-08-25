"""cli.py — `omega-morphofield [morph|field|tumor|all]`"""
from __future__ import annotations
import sys
from .morphogen import MorphogenField, FieldConfig
from .tumor_dynamics import compare_policies, format_comparison


def demo_morph(n: int = 40, steps: int = 1500) -> None:
    print("=== 形態形成場: 種から細胞が分岐していく ===")
    f = MorphogenField(FieldConfig(n=n))
    f.seed_spot(radius=3)
    for _ in range(4):
        f.run(steps // 4)
        s = f.summary()
        print(f"  t={s['t']:6.0f}  細胞数={int(s['spots']):3d}  "
              f"活性因子総量={s['total_activator']:7.1f}")
    print()
    print(f.render())


def demo_field(n: int = 40, steps: int = 400) -> None:
    print("=== 電磁誘導ドリフト: 外部場でパターンを操作する ===")
    print("  Ex      重心x     重心y    細胞数")
    for Ex in (0.0, 0.01, 0.03, 0.05):
        f = MorphogenField(FieldConfig(n=n, Ex=Ex))
        f.seed_spot(radius=3)
        f.run(steps)
        cx, cy = f.centroid()
        print(f"  {Ex:.2f}   {cx:6.2f}   {cy:6.2f}    {f.count_spots():3d}")
    print("→ Ex=0 では重心は中央のまま。場をかけると場の向き(x)にだけ移動し、")
    print("  y は動かない。外部場がパターンの位置を制御できることを示す。")


def demo_tumor() -> None:
    print(format_comparison(compare_policies()))


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("morph", "all"):
        demo_morph()
        print()
    if mode in ("field", "all"):
        demo_field()
        print()
    if mode in ("tumor", "all"):
        demo_tumor()
    if mode not in ("morph", "field", "tumor", "all"):
        print("使い方: omega-morphofield [morph|field|tumor|all]")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
