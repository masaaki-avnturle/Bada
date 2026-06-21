# discover — mathematical pattern-discovery apps, in Bada

Three discovery apps whose maths is written in the Bada language (`lib/*.bada`).

## 1. HΨ operator pattern finder (`hpsi.bada`, `hpsi_app.bada`)
Plug arbitrary numbers `x = ℏ·∇` into **HΨ = ⊕(iℏ∇)^⊕L** and study the partial
spectrum `S(x,L) = Σ_{k=1..L} (i·x)^k`. Discovered patterns:
- **phase period 4** (since `i⁴ = 1`),
- **real spectrum** (`im = 0`) exactly at `L mod 4 ∈ {0, 3}` (e.g. L = 3,4,7,8,…),
- **geometric growth** `|S(x,L+1)|/|S(x,L)| → x`.

## 2. Odd-zeta regularity (`zeta.bada`, `zeta_app.bada`)
For the odd zetas ζ(3), ζ(5), ζ(7)… the **excess** `d_s = ζ(s) − 1` obeys a
clean rule: `(ζ(s+2)−1)/(ζ(s)−1) → 1/4`. The app computes the ratios
(`0.183, 0.226, 0.241, 0.246 → 0.25`).

## 3. Odd-zeta a-priori engine — Monster denominators (`moonshine.bada`)
> **Exploratory / heuristic.** Closed forms for ζ(odd) are an *open problem*.
> This is a pattern-**analogy** engine, not a proof.

The engine looks for a *general form* `ζ(s) ≈ p/q` for odd `s` where the
**denominator q is a Monster number** — one of the 15 supersingular primes that
divide the Monster group order, or the moonshine numbers 24 / 196884 — and
reports the **numerator p** taking-rule. Euler's constant γ is tied to the
zetas (including ζ(3)) through the alternating series `γ = Σ_{k≥2} (−1)^k ζ(k)/k`,
which anchors the search.

```
discover hpsi        # operator pattern finder
discover zeta        # odd-zeta 1/4 regularity
discover moonshine   # Monster-denominator a-priori engine
```

All three run on the Bada VM; their results are recorded in
`Omega::DATABASE[hpsi|zeta|moonshine]` and cross-checked against Python
references in the tests.
