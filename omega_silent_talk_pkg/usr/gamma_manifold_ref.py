# -*- coding: utf-8 -*-
"""gamma_manifold_ref.py

Global partial-integration manifold of the Gamma function — pure-Python
reference implementation (mirrors lib/gamma_manifold.c).

Gamma(s) = integral_0^inf t^(s-1) e^(-t) dt  satisfies, by integration
by parts, Gamma(s+1) = s * Gamma(s).  Iterating the identity gives a
family of "charts"

    Gamma(s) = Gamma(s + n) / (s (s+1) ... (s+n-1)),   n = 0, 1, 2, ...

Each chart is a partial-integration step; gluing all charts together
extends the local integral (Re s > 0) to a global object on
C \\ {0, -1, -2, ...}.  We use that atlas as a feature map: a signal
sample x is embedded as the vector of chart coordinates, which is the
"global partial-integration manifold" coordinate used by the pipeline.

Pure Python, no third-party dependencies.
"""

import math

# Lanczos coefficients (g = 7, n = 9)
_LANCZOS_G = 7.0
_LANCZOS_C = [
    0.99999999999980993, 676.5203681218851, -1259.1392167224028,
    771.32342877765313, -176.61502916214059, 12.507343278686905,
    -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7,
]


def gamma(s):
    """Real Gamma(s) via the Lanczos approximation (reflection for s < 0.5)."""
    if s < 0.5:
        return math.pi / (math.sin(math.pi * s) * gamma(1.0 - s))
    s -= 1.0
    a = _LANCZOS_C[0]
    t = s + _LANCZOS_G + 0.5
    for i in range(1, len(_LANCZOS_C)):
        a += _LANCZOS_C[i] / (s + i)
    return math.sqrt(2.0 * math.pi) * (t ** (s + 0.5)) * math.exp(-t) * a


def gpi_kernel(x):
    """Manifold kernel k(x) = 1 / (x * (log x)^2), domain x > 1."""
    if x <= 1.0 + 1e-12:
        return 0.0
    lx = math.log(x)
    return 1.0 / (x * lx * lx)


def gpi_manifold(a, b, nodes):
    """M(a,b) = double-integral_a^b 1/(x log x)^2 dx.

    Simpson per local chart plus the integration-by-parts boundary
    residual [-1/log x], averaged to glue the charts into a global object.
    Matches gpi_manifold() in lib/gamma_manifold.c.
    """
    if nodes < 2:
        nodes = 2
    if a <= 1.0:
        a = 1.0 + 1e-6
    if b <= a:
        return 0.0
    h = (b - a) / float(nodes)
    acc = 0.0
    for i in range(nodes):
        x0 = a + h * i
        x1 = x0 + h
        xm = 0.5 * (x0 + x1)
        local = (h / 6.0) * (gpi_kernel(x0) + 4.0 * gpi_kernel(xm) + gpi_kernel(x1))
        boundary = (1.0 / math.log(x0 if x0 > 1 else 1.000001)) - (1.0 / math.log(x1))
        acc += 0.5 * (local + boundary)
    return acc


def chart_coords(x, n_charts=4):
    """Embed a sample x as its atlas coordinates:
    log|Gamma(x + k)| through the first n_charts partial-integration charts."""
    coords = []
    for k in range(n_charts):
        try:
            coords.append(math.log(abs(gamma(x + k)) + 1e-300))
        except (ValueError, OverflowError):
            coords.append(0.0)
    return coords


if __name__ == "__main__":
    # sanity checks against known closed forms
    print("Gamma(0.5) =", gamma(0.5), " (sqrt(pi) =", math.sqrt(math.pi), ")")
    print("Gamma(5)   =", gamma(5.0), " (= 24)")
    print("manifold(2, 26, 24) =", gpi_manifold(2.0, 26.0, 24))
    print("chart_coords(2.0) =", chart_coords(2.0))
