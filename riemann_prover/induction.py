"""数学的帰納法 + 補集合の解析 + 保存量への射影による証明の修正。

1. 帰納法 (健全・厳密な有理数演算)
   主張 Σ_{k=1}^n f(k) = g(n)  (f, g は多項式) を
     基底  g(0) = 0,   段  g(n+1) − g(n) − f(n+1) ≡ 0  (多項式として恒等的に 0)
   で判定する。成り立てば証明完了、成り立たなければ最小の反例を返す。

2. 証明の修正 (可積分系のコマの誤り訂正の原理)
   bio_medicine/omega_apriori_injector/plugins/integrable_top.js は、ノイズで保存量
   |L|² からずれた軌道を等位集合へ射影して直す。帰納法では
     I(n) = g(n) − Σ_{k<=n} f(k)
   が保存量 (常に 0) であり、段の残差 g(n+1) − g(n) − f(n+1) がそのドリフトにあたる。
   誤った閉形式 g を I ≡ 0 の等位集合へ射影し (一意に定まる)、ドリフト 0 の式に直す。

3. 補集合 (最小反例) の解析
   真である n の集合の補集合 C (= 反例の集合) について、帰納法は
   「C に最小元がない ⇒ C は空」(整列性) と同値。コラッツ予想では降下補題により
   「最小反例が属しうる剰余類」を証明つきで絞り込める。ただし C が空であること
   (= 予想そのもの) は示せないので、予想の判定は open のまま。
"""

from __future__ import annotations

from fractions import Fraction

Poly = list  # coefficients, ascending powers, Fractions


def poly(coeffs) -> Poly:
    p = [Fraction(c) for c in coeffs]
    while p and p[-1] == 0:
        p.pop()
    return p


def p_eval(p: Poly, x) -> Fraction:
    acc = Fraction(0)
    for c in reversed(p):
        acc = acc * x + c
    return acc


def p_add(a: Poly, b: Poly, sign: int = 1) -> Poly:
    n = max(len(a), len(b))
    return poly([(a[i] if i < len(a) else 0) + sign * (b[i] if i < len(b) else 0) for i in range(n)])


def p_mul(a: Poly, b: Poly) -> Poly:
    out = [Fraction(0)] * (len(a) + len(b) - 1 if a and b else 0)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
    return poly(out)


def p_shift(p: Poly) -> Poly:
    """p(n) -> p(n+1)."""
    out, power = [], [Fraction(1)]
    for c in p:
        out = p_add(out, [c * x for x in power])
        power = p_mul(power, [1, 1])
    return poly(out)


def p_interpolate(points) -> Poly:
    out = []
    for i, (xi, yi) in enumerate(points):
        term, denom = [Fraction(1)], Fraction(1)
        for j, (xj, _) in enumerate(points):
            if i != j:
                term = p_mul(term, [-xj, 1])
                denom *= xi - xj
        out = p_add(out, [c * yi / denom for c in term])
    return poly(out)


def p_str(p: Poly) -> str:
    if not p:
        return "0"
    parts = []
    for i in range(len(p) - 1, -1, -1):
        if p[i] != 0:
            parts.append(f"({p[i]})" + ("" if i == 0 else "·n" if i == 1 else f"·n^{i}"))
    return " + ".join(parts)


def drift(f: Poly, g: Poly) -> Poly:
    """Induction-step residual g(n+1) − g(n) − f(n+1): zero iff the invariant is conserved."""
    return p_add(p_add(p_shift(g), g, -1), p_shift(f), -1)


def prove_sum(f, g) -> dict:
    """Decide  Σ_{k=1}^n f(k) = g(n)  for all n >= 0 by induction."""
    f, g = poly(f), poly(g)
    base, d = p_eval(g, 0), drift(f, g)
    out = {"kind": "sum_identity", "f": [str(c) for c in f], "g": [str(c) for c in g],
           "claim": f"Σ_(k=1..n) [{p_str(f)}] = {p_str(g)}", "method": "数学的帰納法"}
    if base == 0 and not d:
        out.update(status="proved", steps=[
            "基底: g(0) = 0 = 空和",
            "段: g(n+1) − g(n) − f(n+1) は多項式として恒等的に 0",
            "ゆえに帰納法によりすべての n ≥ 0 で成立"])
        return out
    total, n = Fraction(0), 0
    while total == p_eval(g, n):       # a counterexample exists within deg+2 steps
        n += 1
        total += p_eval(f, n)
    out.update(status="disproved", counterexample=n,
               steps=[f"n = {n}: 左辺 = {total}, 右辺 = {p_eval(g, n)}"],
               drift=p_str(d) if base == 0 else f"基底 g(0) = {base} ≠ 0")
    return out


def repair_sum(f, g) -> dict:
    """Project a wrong closed form onto the level set I ≡ 0 and prove the result."""
    f, g = poly(f), poly(g)
    pts, total = [(Fraction(0), Fraction(0))], Fraction(0)
    for n in range(1, len(f) + 2):
        total += p_eval(f, n)
        pts.append((Fraction(n), total))
    fixed = p_interpolate(pts)
    proof = prove_sum(f, fixed)
    return {"kind": "repair", "original": prove_sum(f, g), "repaired": proof,
            "drift_before": p_str(drift(f, g)), "drift_after": p_str(drift(f, fixed)),
            "status": proof["status"]}


# ---------------------------------------------------------------------------
# Complement (minimal counterexample) analysis: Collatz descent sieve
# ---------------------------------------------------------------------------
def _reaches_one(n: int, limit: int = 100_000) -> bool:
    for _ in range(limit):
        if n == 1:
            return True
        n = n // 2 if n % 2 == 0 else 3 * n + 1
    return False


def collatz_descent(bits: int = 12) -> dict:
    """Lemma (proved): a minimal Collatz counterexample n0 satisfies n0 >= 2^bits and
    n0 mod 2^bits ∈ survivors.

    Proof: write n = 2^bits·q + r (q >= 1). The first `bits` steps of
    T(n) = n/2 (n even), (3n+1)/2 (n odd) depend only on r, and send n to a·q + b.
    If a < 2^bits and 2^bits − a > b − r at some step, that iterate is < n for every
    q >= 1, so n is not minimal (strong induction: the smaller iterate reaches 1).
    n < 2^bits is checked directly.
    """
    M = 1 << bits
    survivors = []
    for r in range(M):
        a, b, descended = M, r, False
        for _ in range(bits):
            if b % 2:
                a, b = 3 * a // 2, (3 * b + 1) // 2
            else:
                a, b = a // 2, b // 2
            if a < M and M - a > b - r:
                descended = True
                break
        if not descended:
            survivors.append(r)
    small_ok = all(_reaches_one(n) for n in range(1, M))
    return {
        "kind": "collatz_descent", "bits": bits, "modulus": M,
        "claim": f"コラッツ予想の最小反例 n0 は n0 ≥ {M} かつ n0 mod {M} が {len(survivors)} 個の剰余類のいずれか",
        "survivor_count": len(survivors), "survivors_head": survivors[:12],
        "excluded_fraction": 1 - len(survivors) / M,
        "small_cases_verified": small_ok,
        "method": "強い帰納法 (降下) + 補集合の剰余類ふるい",
        "status": "proved" if small_ok else "disproved",
        "conjecture_status": "open",
    }


NO_STEP = [
    {"kind": "no_inductive_step", "problem": "riemann_hypothesis", "status": "open",
     "note": "零点は離散的な添字 n に沿った P(n) ⇒ P(n+1) の形を持たず、既知の帰納の段がない"},
    {"kind": "no_inductive_step", "problem": "deep_riemann_hypothesis", "status": "open",
     "note": "オイラー積の収束は極限の主張であり、有限段の帰納では到達できない"},
    {"kind": "no_inductive_step", "problem": "goldbach", "status": "open",
     "note": "2n が素数 2 個の和でも 2n+2 について何も導けない。補集合に既知の降下構造がない"},
]


def induction_report(bits: int = 12) -> list[dict]:
    return [
        prove_sum([0, 1], [0, Fraction(1, 2), Fraction(1, 2)]),
        prove_sum([0, 0, 0, 1], [0, 0, Fraction(1, 4), Fraction(1, 2), Fraction(1, 4)]),
        repair_sum([0, 0, 1], [0, Fraction(1, 5), Fraction(3, 5), Fraction(2, 5)]),  # wrong: n(n+1)(2n+1)/5
        collatz_descent(bits),
        *NO_STEP,
    ]


def recheck(entry: dict) -> bool:
    """Independent re-derivation of one report entry (used by the PatchGuard gate)."""
    kind = entry.get("kind")
    if kind == "sum_identity":
        return prove_sum(entry["f"], entry["g"])["status"] == entry["status"]
    if kind == "repair":
        return recheck(entry["repaired"]) and entry["repaired"]["status"] == entry["status"]
    if kind == "collatz_descent":
        fresh = collatz_descent(int(entry["bits"]))
        return (entry.get("conjecture_status") == "open" and fresh["status"] == entry["status"]
                and fresh["survivor_count"] == entry["survivor_count"])
    if kind == "no_inductive_step":
        return entry.get("status") == "open"
    return False
