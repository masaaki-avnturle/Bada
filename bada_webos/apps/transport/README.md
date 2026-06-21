# transport — "Integrate of theorem" equation generator + manifold video (Bada)

Based on the **system_transport.pdf** report's middle pages, where

> **ζ(x) = P²ⁿ · Σ_{k≥0} a_k xᵏ**,  with **a_k = Σᵣ ₙCᵣ** (binomial coefficients),
> **Σ a_k fᵏ = 1/(1−z)** (geometric closure), **χ(x) = (−1)ᵏ a_k**,
> Γ = β, the **AM-GM** inequality `(x+y)/2 ≥ √(xy)`, and ζ steady on **Re = 1/2**.

Because `a_k = C(n,r)`, the equation group is exactly **`Σ a_k fᵏ = (1+f)ⁿ`** —
so ζ(s) generates the equation group through a binomial series.

## The binomial equation generator (`transport.bada`)
- `series_binom(n,f)` = `Σ C(n,r) fʳ` = `(1+f)ⁿ` (the report's a_k = ΣₙCᵣ).
- `series_alt(n,f)` = `Σ (−1)ʳ C(n,r) fʳ` = `(1−f)ⁿ` (the χ = (−1)ᵏ a_k version).
- `generate_P(s,n,f)` = `(ζ(s)/(1+f)ⁿ)^{1/2n}` — the **P²ⁿ factor** from ζ.
- `flow_in(s,n,…)` — the **flow-in number** `f` making `(1+f)ⁿ = ζ(s)`
  (for s=3, n=2 it finds `f = √ζ(3) − 1 ≈ 0.096`).
- `amgm_gap(a,b)` = `(a+b)/2 − √(ab) ≥ 0`.

## The report's manifolds (video dictionary)
| name | manifold |
|:--|:--|
| `seifert` | Seifert fibered space — rotating concentric fibres |
| `kaluza` | Kaluza-Klein 5th dimension — two compactified circle modes |
| `critline` | ζ critical line Re=1/2: `|Σ n^{−(1/2+is)}|` (Riemann zeros = valleys) |
| `amgm` | AM-GM inequality manifold `(a+b)/2 − √(ab) ≥ 0` |
| `binom` | binomial equation surface `Σ C(n,r) gʳ = (1+g)ⁿ` |

Each surface z(x,y;t) is computed in Bada and rendered (via the eqvideo
renderer) as an animated-HTML 3D **video dictionary** (`examples/transport.html`).

## Use
```
transport gen            # the binomial equation generator (zeta -> equations)
transport list           # the manifold dictionary
transport view critline  # ASCII flip-book of the ζ critical line surface
transport html v.html    # the browsable animated video dictionary
```
Records to `Omega::DATABASE[transport]`; cross-checked against Python in tests.
