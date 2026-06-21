# slideshow — all the equation-group graphs as a flash-transition video

Plays **every equation group** from the report corpus as a slide, each a **live
3D animated graph**, and advances between them with **PowerPoint-style flash
transition effects** (event-driven).

## Equation groups (slides)
From the reports (zeta/Riemann, Beta, Jones/Kauffman, manifolds, caustics,
d'Alembertian, …), realised in Bada:
`eqgen, fermat, covariant, trigbeta, abelian` (eqvideo) ·
`seifert, kaluza, critline, amgm, binom` (transport) ·
`caustic` (cusp catastrophe — caostics.pdf) ·
`dalembert` (d'Alembertian wave □ψ=0 — zeta_dalanversian.pdf).

## Flash transitions (event handling)
Each slide change fires one of six PowerPoint-like effects in turn —
**flash, fade, wipe, zoom, spin, blinds** — driven by events:
- auto-advance on a timer (≈3.6 s), and
- **click**, **Space** (play/pause), **←/→** (prev/next) keyboard events.

## Use
```
slideshow list           # the equation groups + the effect list
slideshow html out.html  # write the slideshow video
```
or in Python:
```python
from slideshow import SlideshowApp
app = SlideshowApp(); app.boot(); app.save_html("slideshow.html")
```
Open `examples/slideshow.html`: it auto-plays the 12 equation-group graphs with
flashing transitions; click or use the arrow keys to drive it. The graph maths
is computed in Bada; the slideshow + flash effects are in the HTML/JS renderer.
