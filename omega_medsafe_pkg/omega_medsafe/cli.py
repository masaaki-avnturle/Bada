"""cli.py — `omega-medsafe 薬剤名 薬剤名 ...`（引数なしで対話入力）"""
from __future__ import annotations
import sys
from .checker import check, format_report


def main() -> int:
    if len(sys.argv) > 1:
        names = sys.argv[1:]
    else:
        print("お薬の名前を1行に1つ入力してください（空行で終了）:")
        names = []
        while True:
            try:
                line = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line:
                break
            names.extend(n for n in line.replace("、", ",").split(",") if n.strip())
    if not names:
        print("薬剤名が入力されませんでした。")
        return 1
    print()
    print(format_report(check(names)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
