"""Manifolds == expression trees, and `manifold_emerge` that grows them.

A "manifold" is an expression tree over a single free variable ``x`` built from
an operand pool (the report's ``pholograph_data`` / ``source_array``) and an
operator pool (``operator_data``). Trees are encoded as nested tuples so they
are hashable and trivially serialisable for the write-once TupleSpace:

    ("const", value)
    ("var",)
    ("u", op_name, child)
    ("b", op_name, left, right)

All operators are *protected* (total functions) so evaluation never raises and
the search space stays smooth -- standard practice in genetic programming.
"""

from __future__ import annotations

import math
import random
from typing import Callable, Dict, List, Tuple

Node = tuple

# --- operator_data : unary -------------------------------------------------
_CLAMP = 60.0


def _safe_exp(a: float) -> float:
    return math.exp(a) if a < _CLAMP else math.exp(_CLAMP)


def _safe_log(a: float) -> float:
    a = abs(a)
    return math.log(a) if a > 1e-12 else 0.0


UNARY_OPS: Dict[str, Callable[[float], float]] = {
    "neg": lambda a: -a,
    "sin": math.sin,
    "cos": math.cos,
    "exp": _safe_exp,
    "log": _safe_log,                       # protected log
    "sqrt": lambda a: math.sqrt(abs(a)),    # protected sqrt
    "square": lambda a: a * a,
    "tanh": math.tanh,
}

# --- operator_data : binary ------------------------------------------------
BINARY_OPS: Dict[str, Callable[[float, float], float]] = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b if abs(b) > 1e-9 else 1.0,   # protected division
}

_PRETTY = {"+": "+", "-": "-", "*": "*", "/": "/"}


# --- evaluation ------------------------------------------------------------
def evaluate(node: Node, x: float) -> float:
    kind = node[0]
    if kind == "const":
        return node[1]
    if kind == "var":
        return x
    if kind == "u":
        return UNARY_OPS[node[1]](evaluate(node[2], x))
    # binary
    return BINARY_OPS[node[1]](evaluate(node[2], x), evaluate(node[3], x))


def predict(node: Node, xs: List[float]) -> List[float]:
    out = []
    for x in xs:
        try:
            v = evaluate(node, x)
        except (OverflowError, ValueError, ZeroDivisionError):
            v = float("nan")
        out.append(v)
    return out


# --- structure helpers -----------------------------------------------------
def size(node: Node) -> int:
    kind = node[0]
    if kind in ("const", "var"):
        return 1
    if kind == "u":
        return 1 + size(node[2])
    return 1 + size(node[2]) + size(node[3])


def depth(node: Node) -> int:
    kind = node[0]
    if kind in ("const", "var"):
        return 1
    if kind == "u":
        return 1 + depth(node[2])
    return 1 + max(depth(node[2]), depth(node[3]))


def all_paths(node: Node, path: Tuple[int, ...] = ()) -> List[Tuple[int, ...]]:
    """Every subtree address (as a path of child indices)."""
    paths = [path]
    kind = node[0]
    if kind == "u":
        paths += all_paths(node[2], path + (2,))
    elif kind == "b":
        paths += all_paths(node[2], path + (2,))
        paths += all_paths(node[3], path + (3,))
    return paths


def get_at(node: Node, path: Tuple[int, ...]) -> Node:
    for i in path:
        node = node[i]
    return node


def set_at(node: Node, path: Tuple[int, ...], replacement: Node) -> Node:
    if not path:
        return replacement
    i = path[0]
    rest = path[1:]
    node = list(node)
    node[i] = set_at(node[i], rest, replacement)
    return tuple(node)


def to_string(node: Node) -> str:
    kind = node[0]
    if kind == "const":
        return f"{node[1]:g}"
    if kind == "var":
        return "x"
    if kind == "u":
        return f"{node[1]}({to_string(node[2])})"
    return f"({to_string(node[2])} {_PRETTY[node[1]]} {to_string(node[3])})"


# --- manifold_emerge : random growth --------------------------------------
def _terminal(rng: random.Random) -> Node:
    if rng.random() < 0.55:
        return ("var",)
    return ("const", round(rng.uniform(-3.0, 3.0), 3))


def manifold_emerge(
    rng: random.Random,
    max_depth: int,
    unary_w: Dict[str, float],
    binary_w: Dict[str, float],
    p_terminal: float = 0.25,
) -> Node:
    """Grow a fresh manifold from operand x operator, biased by the reviser's
    current operator weights (so the self-rewritten policy steers generation)."""
    if max_depth <= 1 or rng.random() < p_terminal:
        return _terminal(rng)
    if rng.random() < 0.45:
        op = _weighted_choice(rng, unary_w)
        return ("u", op, manifold_emerge(rng, max_depth - 1, unary_w, binary_w, p_terminal))
    op = _weighted_choice(rng, binary_w)
    return (
        "b",
        op,
        manifold_emerge(rng, max_depth - 1, unary_w, binary_w, p_terminal),
        manifold_emerge(rng, max_depth - 1, unary_w, binary_w, p_terminal),
    )


def _weighted_choice(rng: random.Random, weights: Dict[str, float]) -> str:
    keys = list(weights)
    total = sum(weights[k] for k in keys)
    r = rng.uniform(0.0, total)
    upto = 0.0
    for k in keys:
        upto += weights[k]
        if upto >= r:
            return k
    return keys[-1]
