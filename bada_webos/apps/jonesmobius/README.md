# jonesmobius — are the Beta/Zeta equations Jones-polynomial Möbius equations?

A Bada analyzer that tests each equation for **Möbius form**
`z ↦ (a z + b)/(c z + d)` (a Möbius map is `[a,b,c,d]`) and builds the **causal
graph** of all the equations.

## What it finds
- **Jones mirror = Möbius inversion** `t ↦ 1/t` = `[0,1,1,0]` (class 4, an
  involution): the mirror knot's Jones polynomial is `V(1/t)`, verified by
  exponent negation (trefoil `t+t³−t⁴` ↔ mirror `−t⁻⁴+t⁻³+t⁻¹`). So the Jones
  polynomial relation *is* a Möbius equation.
- **Beta step recurrence** `B(2,2) → B(2,3)` = Möbius **scaling** `[2,0,0,4]`
  (class 2), verified.
- **Zeta link** `B(2,2) → ζ(2)=π²/6` = Möbius **scaling** `[π²,0,0,1]`
  (class 2), verified.

## Causal graph
`[src, dst, möbius_class, verified]`:
```
[[B22, B23, 2, 1], [B22, zeta2, 2, 1], [Jones, Jones_mirror, 4, 1]]
```
Every listed equation is a Möbius equation, and they are causally linked
through scalings (Beta/Zeta) and the inversion (Jones mirror).

## Run
```
mobius        # terminal command (runs the analyzer; records Omega::DATABASE[causal])
```
Cross-checked against Python in the tests.
