"""@reviser -- the self-rewriting meta-policy.

This is the heart of the "self-evolution". In the reports, ``@reviser`` rewrites
the system's own production rules (its parser, its extractor, its operators).
Here the reviser owns the *policy that generates and mutates manifolds*:

    * weights over the variation operators (point / subtree / crossover / hoist /
      const-tweak),
    * weights over the unary and binary node-operators used when growing trees,
    * a mutation strength and grow depth.

After every generation the reviser performs **credit assignment**: variation
operators (and node-operators) that produced children fitter than their parents
have their weights increased; the rest decay. The mutation strength follows
Rechenberg's 1/5 success rule. The policy is therefore *rewritten by its own
results* -- the engine improves the strategy it uses to improve itself -- and
each rewritten policy snapshot is committed to the write-once TupleSpace.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

from . import manifold as M

VARIATION_OPS = ["point_mutate", "subtree_mutate", "crossover", "hoist", "const_tweak"]


class Reviser:
    def __init__(self, rng: random.Random, grow_depth: int = 4) -> None:
        self.rng = rng
        self.var_w: Dict[str, float] = {op: 1.0 for op in VARIATION_OPS}
        self.unary_w: Dict[str, float] = {op: 1.0 for op in M.UNARY_OPS}
        self.binary_w: Dict[str, float] = {op: 1.0 for op in M.BINARY_OPS}
        self.mutation_strength = 1.0
        self.grow_depth = grow_depth
        # per-generation accounting
        self._trials = 0
        self._successes = 0
        self._var_credit: Dict[str, float] = {op: 0.0 for op in VARIATION_OPS}
        self._node_credit_u: Dict[str, float] = {op: 0.0 for op in M.UNARY_OPS}
        self._node_credit_b: Dict[str, float] = {op: 0.0 for op in M.BINARY_OPS}

    # -- generation lifecycle ----------------------------------------------
    def begin_generation(self) -> None:
        self._trials = 0
        self._successes = 0
        for d in (self._var_credit, self._node_credit_u, self._node_credit_b):
            for k in d:
                d[k] = 0.0

    def choose_variation(self) -> str:
        return _weighted_choice(self.rng, self.var_w)

    def record(self, var_op: str, child: M.Node, gain: float) -> None:
        """Register the outcome of one variation event."""
        self._trials += 1
        improved = gain > 0.0
        if improved:
            self._successes += 1
            self._var_credit[var_op] += gain
            # spread a little credit to the node-operators present in the winner
            for u in _unary_ops_in(child):
                self._node_credit_u[u] += gain
            for b in _binary_ops_in(child):
                self._node_credit_b[b] += gain

    def adapt(self) -> Dict[str, object]:
        """Rewrite the policy from this generation's credit, return a snapshot."""
        decay = 0.85
        # variation-operator weights: decay then reward successful ops
        for op in self.var_w:
            self.var_w[op] = decay * self.var_w[op] + self._var_credit[op]
        _renorm(self.var_w, floor=0.05, target=len(self.var_w))
        # node-operator weights
        for op in self.unary_w:
            self.unary_w[op] = decay * self.unary_w[op] + self._node_credit_u[op]
        _renorm(self.unary_w, floor=0.05, target=len(self.unary_w))
        for op in self.binary_w:
            self.binary_w[op] = decay * self.binary_w[op] + self._node_credit_b[op]
        _renorm(self.binary_w, floor=0.1, target=len(self.binary_w))
        # 1/5 success rule for mutation strength
        rate = (self._successes / self._trials) if self._trials else 0.0
        if rate > 0.2:
            self.mutation_strength = min(3.0, self.mutation_strength * 1.15)
        elif rate < 0.2:
            self.mutation_strength = max(0.1, self.mutation_strength / 1.15)
        return self.snapshot(success_rate=round(rate, 4))

    def snapshot(self, success_rate: Optional[float] = None) -> Dict[str, object]:
        return {
            "variation_weights": {k: round(v, 4) for k, v in self.var_w.items()},
            "unary_weights": {k: round(v, 4) for k, v in self.unary_w.items()},
            "binary_weights": {k: round(v, 4) for k, v in self.binary_w.items()},
            "mutation_strength": round(self.mutation_strength, 4),
            "success_rate": success_rate,
        }

    # -- variation operators (operate on manifolds) ------------------------
    def grow(self, max_depth: Optional[int] = None) -> M.Node:
        return M.manifold_emerge(
            self.rng, max_depth or self.grow_depth, self.unary_w, self.binary_w
        )

    def vary(self, op: str, parent: M.Node, mate: Optional[M.Node]) -> M.Node:
        if op == "crossover" and mate is not None:
            return self._crossover(parent, mate)
        if op == "subtree_mutate":
            return self._subtree_mutate(parent)
        if op == "hoist":
            return self._hoist(parent)
        if op == "const_tweak":
            return self._const_tweak(parent)
        return self._point_mutate(parent)

    def _rand_path(self, node: M.Node) -> Tuple[int, ...]:
        return self.rng.choice(M.all_paths(node))

    def _point_mutate(self, node: M.Node) -> M.Node:
        path = self._rand_path(node)
        sub = M.get_at(node, path)
        kind = sub[0]
        if kind == "const":
            new = ("const", round(sub[1] + self.rng.gauss(0, self.mutation_strength), 3))
        elif kind == "var":
            new = ("const", round(self.rng.uniform(-3, 3), 3))
        elif kind == "u":
            new = ("u", _weighted_choice(self.rng, self.unary_w), sub[2])
        else:
            new = ("b", _weighted_choice(self.rng, self.binary_w), sub[2], sub[3])
        return M.set_at(node, path, new)

    def _subtree_mutate(self, node: M.Node) -> M.Node:
        path = self._rand_path(node)
        return M.set_at(node, path, self.grow(max_depth=max(2, self.grow_depth - 1)))

    def _crossover(self, a: M.Node, b: M.Node) -> M.Node:
        pa = self._rand_path(a)
        pb = self._rand_path(b)
        donor = M.get_at(b, pb)
        child = M.set_at(a, pa, donor)
        if M.depth(child) > self.grow_depth + 4:        # leash on bloat
            return self._hoist(child)
        return child

    def _hoist(self, node: M.Node) -> M.Node:
        paths = [p for p in M.all_paths(node) if p]
        if not paths:
            return node
        return M.get_at(node, self.rng.choice(paths))

    def _const_tweak(self, node: M.Node) -> M.Node:
        const_paths = [p for p in M.all_paths(node) if M.get_at(node, p)[0] == "const"]
        if not const_paths:
            return self._point_mutate(node)
        path = self.rng.choice(const_paths)
        val = M.get_at(node, path)[1]
        return M.set_at(node, path, ("const", round(val + self.rng.gauss(0, self.mutation_strength), 3)))


# --- helpers ---------------------------------------------------------------
def _unary_ops_in(node: M.Node) -> List[str]:
    out: List[str] = []
    if node[0] == "u":
        out.append(node[1])
        out += _unary_ops_in(node[2])
    elif node[0] == "b":
        out += _unary_ops_in(node[2]) + _unary_ops_in(node[3])
    return out


def _binary_ops_in(node: M.Node) -> List[str]:
    out: List[str] = []
    if node[0] == "b":
        out.append(node[1])
        out += _binary_ops_in(node[2]) + _binary_ops_in(node[3])
    elif node[0] == "u":
        out += _binary_ops_in(node[2])
    return out


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


def _renorm(weights: Dict[str, float], floor: float, target: float) -> None:
    for k in weights:
        if weights[k] < floor:
            weights[k] = floor
    total = sum(weights.values())
    scale = target / total
    for k in weights:
        weights[k] *= scale
