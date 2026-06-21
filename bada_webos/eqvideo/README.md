# eqvideo — equation-group 3D animation video dictionary (in Bada)

A **dictionary** of the zeta/beta equation-group **manifolds**, each shown as a
**3D animation** whose surface *displaces* over time. The surfaces z(x,y; t) are
computed in Bada (`apps/eqvideo/lib/manifolds.bada`); a renderer turns the
frames into a browsable **animated-HTML video** and a terminal ASCII flip-book.

## Dictionary entries
| name | manifold | what it is |
|:--|:--|:--|
| `eqgen` | ζ/β equation generator | `O(x) = ζ(3)/Σ a_k f^k`, the equation group rotating in `t` |
| `fermat` | Fermat complex manifold | `z = 1 − |x|ⁿ − |y|ⁿ`, `n = 2→4` (hypersurface deformation) |
| `covariant` | complex covariant integral manifold | a traveling-wave field (covariant integral), phase in `t` |
| `trigbeta` | trigonometric Beta function | the Beta integrand `sinᵖθ·cos²θ` over `[0,π]`, `p = 1→4` |
| `abelian` | Abelian manifold (complex torus) | doubly-periodic surface displaced by the modular `t` |

Each entry's **displacement** (how far a sample point moves over the animation)
is recorded in `Omega::DATABASE[eqvideo]`.

## Use
```
eqvideo list             # the dictionary
eqvideo view fermat      # ASCII flip-book of an entry's animation
eqvideo html video.html  # write the browsable animated video dictionary
```
The HTML (`examples/eqvideo.html`) draws each surface as an isometric 3D mesh,
cycles the frames, and has a dropdown to pick the dictionary entry — open it in
a browser to watch the manifolds displace.

## Pipeline
```
manifolds.bada  ──(frames)──>  eqvideo/bridge.py  ──>  render.py
   z(x,y;t) in Bada              n×n grids per frame      ASCII + animated HTML
```
Cross-checked against Python in the tests.
