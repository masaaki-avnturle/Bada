# superpose — all the equation-group videos overlaid into one

What do you get if you **superimpose all the videos**? This takes the 10
manifold animations (`eqvideo` + `transport`, computed in Bada), normalises each
surface to a common scale, and **sums/averages them frame-by-frame** into one
field — the combined equation-group landscape.

The result is a shifting **interference pattern**: where several surfaces crest
together the field rises, where they cancel it flattens, and the whole thing
breathes as the 10 sources move at their own rates.

## Sources overlaid
`eqgen, fermat, covariant, trigbeta, abelian` (eqvideo) +
`seifert, kaluza, critline, amgm, binom` (transport).

## Views
- **3D** (`examples/superpose.html`): the combined field as an isometric 3D
  surface animation.
- **kaleidoscope** (`examples/superpose_kaleido.html`): the combined field seen
  from directly above, mirror-folded into radial symmetry.

## Use
```
superpose stats          # which videos are overlaid + field displacement
superpose html out.html  # the 3D superposition video
superpose kaleido out.html  # the top-down kaleidoscope of the superposition
```
or in Python:
```python
from superpose import SuperposeApp
app = SuperposeApp(); app.boot()
app.save_3d("superpose.html"); app.save_kaleido("superpose_kaleido.html")
```
The surfaces are computed in Bada; the overlay (normalise + average) and the
rendering are done in Python.
