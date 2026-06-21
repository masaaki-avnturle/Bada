# topdown — each equation group's domain as a flat 2D top-down video

Takes all the equation-group graphs (the same 12 used by the slideshow) and
renders **each one's domain as a flat 2D video seen from straight above** —
the `[-1,1]²` region as an animated heatmap (z → colour, no 3D projection).

A global **kaleidoscope fold** toggle switches every tile between the plain
top-down view (square) and the radially mirror-folded kaleidoscope (circular) —
the "based on the 3D kaleidoscope" mode.

## Domains
`eqgen, fermat, covariant, trigbeta, abelian` (eqvideo) ·
`seifert, kaluza, critline, amgm, binom` (transport) ·
`caustic, dalembert` (report surfaces).

## Controls (open `examples/topdown.html`)
- a **checkbox per equation group** (individual, arbitrary selection) + all/none,
- **kaleidoscope fold** toggle (plain top-down ↔ radial kaleidoscope),
- **click a tile** to enlarge, ⏸ to pause.

## Use
```
topdown list              # the equation-group domains
topdown html out.html     # plain 2D top-down
topdown html out.html fold  # kaleidoscope-folded top-down
```
or in Python:
```python
from topdown import TopDownApp
app = TopDownApp(); app.boot(); app.save_html("topdown.html", fold=False)
```
The surfaces are computed in Bada; the top-down (and optional kaleidoscope fold)
rendering is done per-pixel in the canvas renderer.
