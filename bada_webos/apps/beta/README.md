# beta — Beta function, difference-equation factorization, zeta links (in Bada)

Put **p = 2, q = 2** into the Beta function and run the algorithms for each
relationship, all written in the Bada language (`lib/betalib.bada`).

`B(p,q) = Γ(p)Γ(q)/Γ(p+q)`, `Γ(n) = (n−1)!`, so **B(2,2) = 1/6**.

## The relationships (algorithms)
- **Difference-equation factorization (Pascal):** `B(p,q) = B(p+1,q) + B(p,q+1)`
  — verified, e.g. `B(2,2) = B(3,2) + B(2,3) = 1/12 + 1/12`.
- **Step recurrences:** `B(p,q+1) = B(p,q)·q/(p+q)`, `B(p+1,q) = B(p,q)·p/(p+q)`
  — every related equation is generated from a neighbour.
- **Symmetry:** `B(p,q) = B(q,p)`.
- **Exact zeta link:** `ζ(2) = π²·B(2,2) = π²/6`.
- **ζ(3) adaptation (report heuristic):** the report's `ζ(s) = β(p,q)/log x`
  is solved for `x`, giving `x = exp(B(2,2)/ζ(3)) ≈ 1.1487`, for which
  `B(2,2)/ln x = ζ(3)`.
- **Generate all equations:** `generate_relations()` produces the family
  `B(2,2), B(2,3), B(3,2), B(2,4), B(3,3)` from the `B(2,2)` seed.

## Run
```
beta                       # terminal command: runs the whole algorithm set
```
Results are recorded in `Omega::DATABASE[beta]` and cross-checked against
Python in the tests.

> Note: the Beta recurrences and `ζ(2) = π²·B(2,2)` are exact, provable maths.
> The `ζ(3) = B(2,2)/log x` step is the report's heuristic relation (solved for
> x), not a proven closed form for ζ(3).
