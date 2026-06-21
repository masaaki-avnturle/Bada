# hologram — project the equation-group videos onto a Hologram Display

Built from the report **"Hologram Display" (Yamaguchi)**. Takes the
equation-group videos already built (eqvideo / transport / slideshow surfaces,
all computed in Bada) and projects each one onto a **four-mirror reflection
pyramid** — `before` (top), `after` (bottom), `left`, `right` — modulated by
the report's **light field** computed in Bada.

## The light field (in Bada)
`apps/hologram/lib/hologram.bada` implements the report's optics:

```
1/e^(x log x) + 1/e^(-x log x) = 1/y                     (light position)
beta(p,q) = 2(cos(i x log x) + i sin(i x log x)) = 2 cosh(x log x)
||ds^2|| = ∫ ( v/√(1+(v/c)^2) + i v/√(1+(v/c)^2) ) dvol   (complex line element)
||ds^2|| = 8πG (p/c^3 + V/S)                              (material mass balance)
```

The amplitude is **complex** — a *reality* surface `light_re` and an *imaginary*
surface `light_im` (the report's "camera mechanism of imaginary and reality
surfaces"); `light_mag = |re + i·im|` is the displayed brightness, peaking on
the `light_pos` ridge (where `x log x = 0`). `exp`, `log`, `sin`, `cos`, `sqrt`
are all implemented in Bada (series / Newton). The geometry — `quad_names`,
`quad_rot` (`before 0°, right 90°, after 180°, left 270°`) — is in Bada too.

## How it displays
Each pixel of the chosen equation-group surface is drawn as a top-down heatmap
**multiplied by the Bada light field** (the SiO₂-mirror reflection), with faint
regions made transparent so the image floats on black. That tile is then drawn
onto the four mirrors of the pyramid. Put a transparent pyramid on the screen
and a single floating image is reconstructed; or switch to **free view** for the
reconstruction shown directly (with the imaginary/reality phase shimmer).

## Use
```
hologram list                 # the videos + mirrors + light field
hologram html out.html        # reflection-pyramid display
hologram html out.html free   # free-view reconstruction
```
or in Python:
```python
from hologram import HologramApp
app = HologramApp(); app.boot(); app.save_html("hologram.html")
```

Open `out.html`: pick which equation group to project, toggle pyramid ↔ free
view, pause. The surfaces and the β(p,q) light field are computed in Bada; the
reflection compositing is done in the canvas renderer.
