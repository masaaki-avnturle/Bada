# eqgen — generate the equation group from Euler's zeta & beta (in Bada)

Based on the report's middle pages:
- **Γ = β = π-operator** (p.15): the Beta function *is* the π-operator value.
- **generator relation** (p.16): `O(x) = ζ(s) / Σ_{k≥0} a_k f^k` — so **ζ(s)
  generates the equation group** through the power series.
- **Euler continued fractions** (p.13): the same equation in another form.

## What the engine does
- `o_from_zeta(ζ, a, f)` = `ζ / Σ a_k f^k` — the operator/equation generated
  from a zeta value and a chosen series.
- `zeta_from_series(O, a, f)` = `O · Σ a_k f^k` — the inverse: regenerate the
  zeta-value equation.
- **flow-in number**: `flow_in(ζ, a, …, target=1)` scans `f` for the value that
  lets ζ *flow into* the series (`O=1` ⇒ `ζ = Σ a_k f^k`). For `a_k = 1` this
  finds `f = 1 − 1/ζ(3) ≈ 0.168`.
- `generate_equations(ζ, a, fs)` — the whole equation **group** `[f, O(x)]`
  generated from one zeta value over a set of inputs.
- **β–ζ variable regularity**: `s = 2 ↔ (p,q) = (2,2)` via `ζ(2) = π²·B(2,2)`.
- `euler_cf(b0, c, b)` — the Euler continued-fraction form.

## Run
```
eqgen        # terminal command: runs the generator; records Omega::DATABASE[eqgen]
```
Cross-checked against Python in the tests.

> Note: the Beta/Γ/Euler-CF/`ζ(2)=π²·B(2,2)` parts are exact. The generator is a
> faithful realisation of the report's `O(x)=ζ(s)/Σ a_k f^k` relation; choosing
> the series `a_k` is a modelling choice (the "flow-in" search finds the input
> that makes a given equation close).
