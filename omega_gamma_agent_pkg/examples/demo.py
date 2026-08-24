"""demo.py — 最小デモ. `python examples/demo.py`"""
from omega_gamma_agent import OmegaGammaAgent

agent = OmegaGammaAgent()
for q in [
    "ガンマ関数の部分積分と多様体について",
    "Bada言語とは？",
    "これはAGI？ChatGPT？",
    "使い方を教えて",
]:
    print(agent.explain(q))
    print("=" * 64)
