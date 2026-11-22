"""未解決問題の反例を、擬似量子コンピュータ上の Grover 探索でさがすシミュレータ。

擬似量子コンピュータは既存の状態ベクトルシミュレータ
bada_webos/quantum/shor9.py の StateVector を使う (QuantOS の擬似量子カーネルと同じ方式)。

健全性:
  * 「すべての n で P(n)」型の予想は、反例が 1 つ見つかれば反証できるが、
    有限範囲に反例がないことは予想の証明にならない。予想の判定は open のまま。
  * これはシミュレーションなので、オラクルを作るために 2^k 個の基底状態すべてで
    P を古典的に評価している。したがって「n < 2^k に反例なし」は全数検査として
    確定するが、量子的な高速化 (√N 回の問い合わせ) は実機でしか得られない。
"""

from __future__ import annotations

import math
import random

from bada_webos.quantum import StateVector


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    for d in range(3, math.isqrt(n) + 1, 2):
        if n % d == 0:
            return False
    return True


def _sigma(n: int) -> int:
    total = 0
    for d in range(1, math.isqrt(n) + 1):
        if n % d == 0:
            total += d + (n // d if d * d != n else 0)
    return total


def _harmonic(n: int) -> float:
    return math.fsum(1 / k for k in range(1, n + 1))


# Each problem: index i (a basis state) -> n, and counterexample(n) -> bool.
def _goldbach_cx(n):      # n even >= 4 that is NOT a sum of two primes
    return not any(_is_prime(p) and _is_prime(n - p) for p in range(2, n // 2 + 1))


def _collatz_cx(n, limit=10_000):   # n that does not reach 1
    for _ in range(limit):
        if n == 1:
            return False
        n = n // 2 if n % 2 == 0 else 3 * n + 1
    return True


def _legendre_cx(n):      # no prime strictly between n² and (n+1)²
    return not any(_is_prime(m) for m in range(n * n + 1, (n + 1) ** 2))


def _lagarias_cx(n):      # σ(n) > H_n + exp(H_n)·log(H_n)   (any such n disproves RH)
    h = _harmonic(n)
    return _sigma(n) > h + math.exp(h) * math.log(h) + 1e-9


def _euler_poly_cx(n):    # n² + n + 41 composite
    return not _is_prime(n * n + n + 41)


PROBLEMS = {
    "riemann_lagarias": {
        "title": "リーマン予想 (Lagarias の同値形)",
        "statement": "すべての n ≥ 1 で σ(n) ≤ H_n + exp(H_n)·log(H_n)",
        "n_of": lambda i: i + 1, "cx": _lagarias_cx, "known": "open",
    },
    "goldbach": {
        "title": "ゴールドバッハ予想",
        "statement": "4 以上のすべての偶数は 2 つの素数の和",
        "n_of": lambda i: 2 * i + 4, "cx": _goldbach_cx, "known": "open",
    },
    "collatz": {
        "title": "コラッツ予想",
        "statement": "すべての n ≥ 1 は 3n+1 操作で 1 に到達する",
        "n_of": lambda i: i + 1, "cx": _collatz_cx, "known": "open",
    },
    "legendre": {
        "title": "ルジャンドル予想",
        "statement": "すべての n ≥ 1 で n² と (n+1)² の間に素数がある",
        "n_of": lambda i: i + 1, "cx": _legendre_cx, "known": "open",
    },
    "euler_polynomial": {
        "title": "（対照実験・偽の命題）n² + n + 41 は常に素数",
        "statement": "すべての n ≥ 0 で n² + n + 41 は素数",
        "n_of": lambda i: i, "cx": _euler_poly_cx, "known": "false",
    },
}


def is_counterexample(problem: str, n: int) -> bool:
    """Classical re-check of a claimed counterexample (used by the PatchGuard gate)."""
    return bool(PROBLEMS[problem]["cx"](n))


def grover_search(marked: list[bool], seed: int = 0, shots: int = 16) -> dict:
    """Grover search on the pseudo-quantum computer for an index with marked[i] True."""
    N = len(marked)
    k = N.bit_length() - 1
    if 1 << k != N:
        raise ValueError("len(marked) must be a power of two")
    M = sum(marked)
    sv = StateVector(k)
    for q in range(k):
        sv.h(q)
    iterations = 0
    if 0 < M < N:
        iterations = max(0, round(math.pi / (4 * math.asin(math.sqrt(M / N))) - 0.5))
    amps = sv.amps
    for _ in range(iterations):
        for i in range(N):                      # oracle: phase-flip marked states
            if marked[i]:
                amps[i] = -amps[i]
        for q in range(k):                      # diffusion: H^k (2|0><0| - 1) H^k
            sv.h(q)
        for i in range(1, N):
            amps[i] = -amps[i]
        for q in range(k):
            sv.h(q)
    probs = [abs(a) ** 2 for a in amps]
    p_marked = math.fsum(p for p, m in zip(probs, marked) if m)
    # Each shot is a fresh run of the circuit followed by a measurement.
    samples = random.Random(seed).choices(range(N), weights=probs, k=shots)
    return {"qubits": k, "marked": M, "iterations": iterations,
            "success_probability": p_marked, "measured": samples[0], "samples": samples}


def quantum_search(problem: str, qubits: int = 10, seed: int = 0) -> dict:
    spec = PROBLEMS[problem]
    N = 1 << qubits
    ns = [spec["n_of"](i) for i in range(N)]
    marked = [bool(spec["cx"](n)) for n in ns]
    g = grover_search(marked, seed)
    samples = g.pop("samples")
    n, found, shots = ns[samples[0]], False, 0
    for idx in samples:                         # every measurement is re-checked classically
        shots += 1
        if is_counterexample(problem, ns[idx]):
            n, found = ns[idx], True
            g["measured"] = idx
            break
    out = {
        "problem": problem, "title": spec["title"], "statement": spec["statement"],
        "range": [ns[0], ns[-1]], **g, "shots": shots,
        "counterexample": n if found else None,
        "counterexamples_in_range": sum(marked),
    }
    if found:
        out["status"] = "disproved"
        out["bounded_status"] = "disproved"
    else:
        out["status"] = "open"
        # no marked state exists in the register => exhaustive for this range
        out["bounded_status"] = "verified" if g["marked"] == 0 else "inconclusive"
    return out


def quantum_search_all(qubits: int = 10, seed: int = 0) -> list[dict]:
    return [quantum_search(p, qubits, seed) for p in PROBLEMS]
