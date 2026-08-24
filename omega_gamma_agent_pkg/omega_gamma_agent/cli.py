"""cli.py — 対話用コマンドライン. `python -m omega_gamma_agent.cli`"""
from __future__ import annotations
import sys
from .agent import OmegaGammaAgent


def main() -> int:
    agent = OmegaGammaAgent()
    print("Omega-Gamma Agent (ローカル/決定論的). 空行またはCtrl-Dで終了.")
    print("これは AGI でも ChatGPT でもありません。研究・教育用の骨組みです.\n")
    if len(sys.argv) > 1:
        print(agent.ask(" ".join(sys.argv[1:])))
        return 0
    while True:
        try:
            q = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            break
        print("bot> " + agent.ask(q))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
