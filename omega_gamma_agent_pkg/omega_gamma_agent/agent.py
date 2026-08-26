"""
agent.py — Omega-Gamma Agent
============================

`gamma_manifold` の大域的部分積分漸化を「思考ステップ」の核として使う、
小さな検索・応答エージェント。

⚠️ 誠実な位置づけ:
  これは AGI ではありません。ChatGPT のような大規模言語モデルでもありません。
  外部モデルもクラウドも使わず、ネットワークにも接続しない、完全にローカルで
  動作する **決定論的な検索＋テンプレート応答エンジン** です。ガンマ関数の
  部分積分漸化 (Γ(s+1)=s·Γ(s)) を、知識片への「注意の重み付け」に用いる
  ところが本パッケージの独自点であり、研究・教育・アート目的の骨組みです。

動作:
  1. 知識ベース (knowledge base) の各エントリを多様体上の状態として登録
  2. 質問の語と各エントリの重なりで初期パラメータ s を決める
  3. 部分積分漸化で数ステップ状態を進め、softmax で注意分布を得る
  4. 最も重みの大きいエントリを根拠に応答を組み立てる
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .gamma_manifold import GammaManifold


def _tokens(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())


@dataclass
class Knowledge:
    """知識片。key に反応語、text に応答本文を持つ。"""

    keys: List[str]
    text: str


DEFAULT_KB: List[Knowledge] = [
    Knowledge(
        ["gamma", "ガンマ", "関数", "部分積分", "多様体", "manifold"],
        "ガンマ関数 Γ(s)=∫_0^∞ t^{s-1}e^{-t}dt に部分積分を施すと大域的漸化 "
        "Γ(s+1)=s·Γ(s) が得られます。本エージェントはこの漸化を注意の重み更新に使います。",
    ),
    Knowledge(
        ["bada", "言語", "language", "omega"],
        "Bada は本リポジトリの作用素環プログラミング言語で、omega_llm エンジンや "
        "π-softmax などの構文を持ちます。このエージェントはその思想を Python で骨組み化したものです。",
    ),
    Knowledge(
        ["agi", "chatgpt", "ai", "知能", "思考"],
        "これは AGI でも ChatGPT でもありません。ローカルで動く決定論的な検索＋"
        "テンプレート応答エンジンで、ガンマ漸化を注意重みに用いる研究用の骨組みです。",
    ),
    Knowledge(
        ["hello", "hi", "こんにちは", "はじめまして", "help", "使い方"],
        "こんにちは。質問を入力すると、知識ベースの中からガンマ多様体上の注意重みが"
        "最大のエントリを根拠に応答します。`ask(\"...\")` を呼び出してください。",
    ),
]


class OmegaGammaAgent:
    """ガンマ多様体を推論核に持つローカル・エージェント。"""

    def __init__(self, kb: List[Knowledge] | None = None, steps: int = 3) -> None:
        self.kb = kb if kb is not None else DEFAULT_KB
        self.steps = steps

    def _score(self, question: str, k: Knowledge) -> float:
        """
        反応語が質問に含まれる数を初期パラメータ s の基礎にする。
        日本語は空白で分かち書きされないため、英単語はトークン集合で、
        それ以外（日本語など）は部分文字列一致で数える。
        """
        q_lower = question.lower()
        overlap = 0
        for key in k.keys:
            key_l = key.lower()
            if key_l.isascii():
                # 英単語は境界付き一致（日本語と連結していても拾えるよう境界に \b と非英字境界の両方を許す）
                if re.search(r"(?<![a-z0-9])" + re.escape(key_l) + r"(?![a-z0-9])", q_lower):
                    overlap += 1
            elif key_l in q_lower:
                overlap += 1
        return float(overlap)

    def rank(self, question: str) -> List[Tuple[Knowledge, float]]:
        """質問に対する各知識片の注意確率を返す（降順）。"""
        manifold = GammaManifold()
        # s は 0 の極を避けるため最低 0.5 から始める。重なりが多いほど大きく。
        for k in self.kb:
            s0 = 0.5 + self._score(question, k)
            manifold.register(s0, label=k.text[:24])
        for _ in range(self.steps):
            manifold.step()
        probs = manifold.softmax(temperature=2.0)
        ranked = sorted(zip(self.kb, probs), key=lambda kp: kp[1], reverse=True)
        return ranked

    def ask(self, question: str) -> str:
        """質問に応答する。"""
        ranked = self.rank(question)
        best, p = ranked[0]
        # 全エントリの重なりが 0 のときは確率が一様になる → 分からない旨を返す。
        top_overlap = self._score(question, best)
        if top_overlap == 0:
            return (
                "その質問に対応する知識片が見つかりませんでした。"
                "gamma / bada / agi / 使い方 などの語を含めて試してください。"
            )
        return best.text

    def explain(self, question: str) -> str:
        """応答の根拠（注意分布）を可視化する。"""
        ranked = self.rank(question)
        lines = [f"Q: {question}", "注意分布 (ガンマ多様体 softmax):"]
        for k, p in ranked:
            lines.append(f"  p={p:.3f}  {k.text[:40]}...")
        lines.append("")
        lines.append("A: " + self.ask(question))
        return "\n".join(lines)


if __name__ == "__main__":
    agent = OmegaGammaAgent()
    for q in ["ガンマ関数の部分積分について教えて", "これはAGIなの？", "使い方は？"]:
        print(agent.explain(q))
        print("-" * 60)
