# kaleido — top-down kaleidoscope (万華鏡) of the equation-group videos

Takes the manifold animations from `eqvideo` and `transport` (10 surfaces,
computed in Bada), views each **from directly above** (z → colour), and folds a
single angular **wedge** into radial **mirror symmetry**, spinning it over the
animation frames — a true kaleidoscope of the equation group.

## Sources (all selectable in the kaleidoscope)
`eqgen`, `fermat`, `covariant`, `trigbeta`, `abelian` (from eqvideo) and
`seifert`, `kaluza`, `critline`, `amgm`, `binom` (from transport).

## How the kaleidoscope is formed
For every output pixel `(r, θ)` around the centre, the angle is folded into one
wedge `[0, 2π/S)` with alternating mirroring (the classic kaleidoscope fold);
the folded `(r, θ)` samples the **top-down** surface field (bilinear), coloured
by height. The wedge slowly rotates and the underlying surface advances each
frame, so the mandala continuously morphs.

## Use
```
kaleido list                 # the source animations
kaleido html out.html 8      # write the kaleidoscope (8 segments)
```
or in Python:
```python
from kaleido import KaleidoApp
app = KaleidoApp(); app.boot(); app.save_html("kaleido.html", segments=8)
```
Open `examples/kaleido.html` in a browser: pick a source from the dropdown,
drag the **segments** slider (3–16 mirrors), ⏸ to pause. The maths is Bada;
the top-down kaleidoscope fold is done in the canvas renderer.
