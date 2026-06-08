"""The fitness / "heat-entropy" score.

The reports repeatedly insist the final product is sorted by a *heat-entropy
value* and that the global-differential-manifold apparatus is governed by
*monotonicity* (単調性). We render that as a concrete, total fitness over a
dataset:

    fitness = accuracy(manifold, data)            # data-fit term
              - lambda_size * size(manifold)      # entropy / parsimony penalty
              - lambda_rough * roughness(manifold)# monotonicity (smoothness) term

`accuracy` uses a normalised RMSE so it lives in (0, 1]; an unusable manifold
(NaN/inf predictions) scores 0. The size penalty is the Kolmogorov-flavoured
"colmogoloph" term from the reports -- simpler manifolds are preferred. The
roughness term rewards the monotone / smooth behaviour the reports associate
with the zeta-gamma global manifold.
"""

from __future__ import annotations

import math
from typing import List

from . import manifold as M


def _finite(v: float) -> bool:
    return v == v and v not in (float("inf"), float("-inf"))


def rmse(node: M.Node, xs: List[float], ys: List[float]) -> float:
    preds = M.predict(node, xs)
    se = 0.0
    for p, y in zip(preds, ys):
        if not _finite(p):
            return float("inf")
        d = p - y
        se += d * d
    return math.sqrt(se / len(xs))


def roughness(node: M.Node, xs: List[float]) -> float:
    """Discrete second-difference magnitude -- a smoothness/monotonicity proxy."""
    preds = M.predict(node, xs)
    if any(not _finite(p) for p in preds):
        return float("inf")
    if len(preds) < 3:
        return 0.0
    acc = 0.0
    for i in range(1, len(preds) - 1):
        acc += abs(preds[i - 1] - 2 * preds[i] + preds[i + 1])
    return acc / (len(preds) - 2)


def fitness(
    node: M.Node,
    xs: List[float],
    ys: List[float],
    y_scale: float,
    lambda_size: float = 0.004,
    lambda_rough: float = 0.0,
) -> float:
    err = rmse(node, xs, ys)
    if not _finite(err):
        return 0.0
    accuracy = 1.0 / (1.0 + err / max(y_scale, 1e-9))
    score = accuracy - lambda_size * M.size(node)
    if lambda_rough:
        r = roughness(node, xs)
        if _finite(r):
            score -= lambda_rough * (r / (1.0 + r))
    return max(0.0, score)
