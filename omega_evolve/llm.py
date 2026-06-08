"""Optional generative-LLM mutation hook (disabled by default).

The offline engine is complete on its own. If an Anthropic API key and the
`anthropic` SDK are present, `make_llm_mutator` returns a callable that asks
Claude to propose a variant manifold in the same tuple encoding. Any failure
(no key, no SDK, network error, unpar, invalid tree) degrades silently to
`None`, so enabling it can only ever *add* candidate manifolds -- the core
search never depends on it.

The model id is read from OMEGA_LLM_MODEL (default: a current Claude model).
"""

from __future__ import annotations

import json
import os
import random
from typing import Callable, Optional

from . import manifold as M

_SYSTEM = (
    "You mutate a symbolic-regression expression tree over one variable x. "
    "Trees are JSON: [\"const\", number] | [\"var\"] | [\"u\", op, child] | "
    "[\"b\", op, left, right]. Unary ops: neg sin cos exp log sqrt square tanh. "
    "Binary ops: + - * /. Reply with ONLY the JSON of a single, slightly mutated "
    "tree (same encoding). No prose."
)


def _from_json(obj) -> M.Node:
    kind = obj[0]
    if kind == "const":
        return ("const", float(obj[1]))
    if kind == "var":
        return ("var",)
    if kind == "u":
        assert obj[1] in M.UNARY_OPS
        return ("u", obj[1], _from_json(obj[2]))
    if kind == "b":
        assert obj[1] in M.BINARY_OPS
        return ("b", obj[1], _from_json(obj[2]), _from_json(obj[3]))
    raise ValueError("bad node")


def _to_json(node: M.Node):
    k = node[0]
    if k == "const":
        return ["const", node[1]]
    if k == "var":
        return ["var"]
    if k == "u":
        return ["u", node[1], _to_json(node[2])]
    return ["b", node[1], _to_json(node[2]), _to_json(node[3])]


def make_llm_mutator() -> Optional[Callable[[M.Node, random.Random], Optional[M.Node]]]:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic  # type: ignore
    except ImportError:
        return None

    client = anthropic.Anthropic(api_key=key)
    model = os.environ.get("OMEGA_LLM_MODEL", "claude-sonnet-4-6")

    def mutate(node: M.Node, rng: random.Random) -> Optional[M.Node]:
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=512,
                system=_SYSTEM,
                messages=[{"role": "user",
                           "content": json.dumps(_to_json(node))}],
            )
            text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
            return _from_json(json.loads(text.strip()))
        except Exception:
            return None

    return mutate
