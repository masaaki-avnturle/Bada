"""Target problems for the engine to evolve a manifold against.

Each preset returns (xs, ys, description). The engine never sees the generating
formula -- only the samples -- so success means it *re-derived* the law from
data, the report's "manifold emerges from the database" in miniature.
"""

from __future__ import annotations

import csv
import math
from typing import List, Tuple

Dataset = Tuple[List[float], List[float], str]


def _grid(a: float, b: float, n: int) -> List[float]:
    if n == 1:
        return [a]
    step = (b - a) / (n - 1)
    return [a + i * step for i in range(n)]


def quadratic(n: int = 40) -> Dataset:
    xs = _grid(-3, 3, n)
    ys = [x * x + 2 * x + 1 for x in xs]
    return xs, ys, "x^2 + 2x + 1"


def ripple(n: int = 60) -> Dataset:
    xs = _grid(-4, 4, n)
    ys = [x * math.sin(x) for x in xs]
    return xs, ys, "x * sin(x)"


def damped(n: int = 60) -> Dataset:
    xs = _grid(0, 6, n)
    ys = [math.exp(-0.4 * x) * math.cos(3 * x) for x in xs]
    return xs, ys, "exp(-0.4 x) * cos(3 x)"


def gamma_like(n: int = 50) -> Dataset:
    """A zeta/gamma-flavoured monotone target from the reports."""
    xs = _grid(0.2, 4.0, n)
    ys = [math.log(x) / x + 0.5 for x in xs]
    return xs, ys, "log(x)/x + 0.5"


PRESETS = {
    "quadratic": quadratic,
    "ripple": ripple,
    "damped": damped,
    "gamma": gamma_like,
}


def from_csv(path: str) -> Dataset:
    xs: List[float] = []
    ys: List[float] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        for row in reader:
            if len(row) < 2:
                continue
            try:
                x, y = float(row[0]), float(row[1])
            except ValueError:
                continue            # skip header / non-numeric rows
            xs.append(x)
            ys.append(y)
    if not xs:
        raise ValueError(f"no (x,y) numeric rows found in {path}")
    return xs, ys, f"csv:{path}"
