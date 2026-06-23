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

## Float-up display (Jones relief + conductive-plastic power)
The video can **float up out of a conductive-plastic tablet**: the light "mounds
up" (盛る) following the **Jones polynomial** of a knot, and the tablet's power
draw is modelled so the display runs inside a power budget.

* `apps/hologram/lib/hologram.bada` now `#include`s the Jones-polynomial library
  (`apps/lib/jones.bada`) and computes, in Bada:
  * `jones_trefoil()` → `V(t) = t + t³ − t⁴` (Kauffman state sum),
    `poly_eval`, and `relief_flat(n, ph)` — the per-pixel **relief height** the
    light is raised to (swept across the display radius, disk-clamped);
  * `tablet_power(bright, elev, area)` — the **conductive-plastic** power in
    watts (raising the relief higher costs more), `power_scale(power, budget)`
    (dim to fit a budget) and `battery_minutes(power, wh)`.
* `hologram/floatup.py` raises the surface off a conductive-plastic plane with a
  contact shadow and a lift driven by the relief, so the image **floats up**; a
  HUD shows V(t), the live power draw and a budget slider (the panel dims to
  stay within it — it works *even with* power consumption, 電力消費でもできる).

## Holographic Happy Hacking Keyboard
`holokbd` floats the **HHKB Professional (US)** keyboard as a hologram. The
layout — all 60 keys, their positions/widths, **Control left of A**, the split
right Shift + Fn, the 1U Delete, the 6U spacebar and the iconic sparse bottom
corners — is computed in Bada (`apps/hologram/lib/keyboard.bada`, as
`[x, y, w, code]`). The keycaps mound up off the conductive-plastic plane with a
holographic ripple sweeping across them; hover/click lights a key.

## Mirror app — aerial image between tablet & phone
Hold a smartphone **face-down over the tablet** with its mirror facing down: by
the **eyeglass-lens focal principle** a real aerial image forms *in the gap*,
realizing the holographic display and the HHKB keyboard in midair.

* `apps/hologram/lib/mirror.bada` computes, in Bada:
  * `lens_image(do, f)` — the thin-lens / concave-mirror law `1/f = 1/do + 1/di`;
  * `lorentz(v, c)` — the **special-relativity** factor `γ = 1/√(1−(v/c)²)`;
  * `focal_jones(d, v, c, ph)` — the focal length set by the **special-relativity
    Jones polynomial** (|V(t)| of the trefoil ÷ γ);
  * `focus_z(d, v, c, ph)` — the height of the aerial focus in the gap `[0, d]`,
    which shifts relativistically (≈3.9 cm at rest → ≈9.5 cm near 0.9c).
* `hologram/mirror.py` + `MirrorApp` draws the side cross-section (tablet, phone
  mirror, rays converging to the focal point) with a **v/c slider** that moves
  the focus, and the front view of the **realized floating image** — toggle
  between the equation-group display and the HHKB keyboard.

## Spatial display (Vision-Pro-equivalent passthrough)
Launch the hologram on the tablet and the **tablet turns transparent**
(passthrough), while its applications **float out as spatial windows** — the
Apple-Vision-Pro-equivalent feature.

* `apps/hologram/lib/spatial.bada` (`#include`s mirror.bada) computes, in Bada:
  * `window_arc(n, radius, spread)` / `window_flat` — the app windows on a
    **concave shell** facing the viewer (centre deepest, edges wrap toward you);
  * `passthrough_alpha(launch)` — the tablet transparency as the display boots
    (1 = opaque → 0.15 = see-through);
  * `parallax(z, head, refz)` and `depth_scale(z, near, far)` — head-parallax
    and depth sizing of each window;
  * `spatial_focus(d, v, c, ph)` — the focal depth the windows are anchored to,
    via the mirror-state lens + special-relativity Jones polynomial.
* `hologram/spatial.py` + `VisionApp` render the passthrough scene: the
  transparent tablet, the apps flying out to the arc on launch (with the live
  holographic display in the centre window), the **spatial HHKB keyboard**
  floating in front, head-parallax and gaze-to-focus on mouse move.

## Transparent display + Japanese HHKB (see-through, no video)
`hologlass` renders the holographic display **and** the Happy Hacking keyboard
as **glass** over a **camera passthrough** background — no video content, so you
see straight through them to the world behind the tablet, even while running.

* `apps/hologram/lib/romaji_kana.bada` is the **Japanese input** for the
  keyboard: a romaji→hiragana table + converter (gojuon, dakuten/handakuten,
  youon, sokuon, syllabic n), e.g. `konnichiwa → こんにちわ`, `nippon → にっぽん`.
  The table is the authoritative source (verified by tests) and is exported to
  the renderer, which converts the romaji preedit live (hiragana / katakana
  toggle).
* `hologram/glass.py` + `GlassApp` draw the transparent glass display panel and
  the glass HHKB over the rear camera (`getUserMedia`, graceful fallback to a
  room gradient); type with the on-screen keys or a physical keyboard.

## Freeform multi-window desktop (Samsung-Freeform style)
`freeform` is a multi-window desktop: the tablet's apps open in **draggable,
resizable freeform windows** (each hosting the real bundled app in an iframe)
with window **close / minimize / maximize** buttons and **edge split-snap**
(left|right halves), plus a Play-Store/Android-style **taskbar** with a **Start
button**, running-app buttons and a clock.

* `apps/hologram/lib/freeform.bada` computes the window-manager geometry —
  `maximize_rect`, `snap_rect` (split-snap), `cascade` (new-window placement),
  `clamp_rect` (keep on screen), `taskbar_layout` — and the launchable
  `app_catalog` (title / file / glyph). The renderer mirrors these for live
  drag / resize.
* `hologram/freeform.py` + `FreeformApp` render the desktop (DOM windows, pointer
  drag/resize for mouse + touch, Start menu, taskbar, close/min/max).
* The **Start menu lists the device's installed apps** (in the APK): a native
  `AndroidApps` bridge (PackageManager) feeds `listApps()` / `launchApp(pkg)`,
  so installed apps appear above the bundled Bada apps and launch on tap. In a
  plain browser (no bridge) only the bundled apps show.
* A **launch-size selector** (`size_presets` in Bada: 携帯型 / 中 / 大) picks the
  size of the next opened window — `window_size` returns a tall narrow phone
  window, a medium window, or a large window (mirrored in the renderer).

## Quantum Cache Disk
`qcache` reinterprets a PC's hard disk as a **quantum cache**, all computed in
Bada (`apps/hologram/lib/qcache.bada`):
* the disk's **bit patterns become a normalized qubit state** (`disk_state`) —
  the hard disk "becomes a quantum computer";
* a **Reviser** rewrites von-Neumann cache ops into quantum gates (`revise_op`:
  READ→MEASURE, WRITE→NOT, FETCH→HADAMARD, EVICT→RESET, SEARCH→GROVER);
* an FPGA-style **Grover a-priori engine** (`grover`) amplifies the marked
  "thought pattern" derived from the target's **DNA-telomere** division
  (`telomere` / `predict_block`);
* the **Jones polynomial** gives a thermal network (`jones_thermal`, t=e^−β);
* the **Gamma integration-by-parts manifold** Γ(z+1)=z·Γ(z) (`gamma_ibp`) is the
  global weighting; and
* the **semiconductor uncertainty principle** Δaddr·Δdata ≥ ħ/2
  (`uncertainty_bound`).

`hologram/qcache.py` + `QCacheApp` render the dashboard (disk grid, Reviser
table, prediction engine, thermal/Gamma curves, uncertainty).

## Self-evolving quantum algorithm (source-code prototype)
`qevolve` turns the quantum machinery into a **self-evolving source-code
prototype**, all in Bada (`apps/hologram/lib/qevolve.bada`):
* a quantum program is a **gene** — a sequence of real-amplitude meta-gates
  (IDENTITY / ORACLE / DIFFUSE);
* a **genetic algorithm** (deterministic LCG PRNG, tournament selection,
  crossover, mutation, elitism) evolves the gene to maximize the amplitude on
  the marked state — **rediscovering Grover amplification by selection** (e.g.
  fitness 0.47 → 0.91 over generations);
* `emit_source` writes the evolved program back out **as Bada source code**
  (`def evolved_amp() { … }`), and the renderer **re-runs that emitted source**
  to confirm `evolved_fitness()` matches — the self-evolving source-code seed.

`hologram/qevolve.py` + `QEvolveApp` render the evolution curve, the evolved
gene, and the self-generated, self-validated Bada source.

## Use
```
qevolve list                   # evolution summary + self-validation
qevolve source                 # print the self-generated Bada source
qevolve html qe.html           # the self-evolving quantum-algorithm dashboard
qcache list                    # the quantum cache disk summary
qcache html q.html             # the quantum cache disk dashboard
freeform list                  # the multi-window desktop summary
freeform html f.html           # the freeform window manager + taskbar
hologlass list                 # the transparent / Japanese-input summary
hologlass html g.html          # transparent display + JP HHKB (camera behind)
holovision list                # the spatial passthrough summary
holovision html v.html         # the Vision-Pro-equivalent spatial display
hologram list                  # the videos + mirrors + light field
hologram html out.html         # reflection-pyramid display
hologram html out.html free    # free-view reconstruction
hologram html out.html float   # float-up display (Jones relief + power)
holokbd  list                  # the HHKB layout + power
holokbd  html kbd.html         # the floating holographic HHKB
holomirror list                # the mirror-app aerial focus (rest → 0.9c)
holomirror html m.html         # mirror app realizing the display
holomirror html m.html keyboard  # mirror app realizing the HHKB
```
or in Python:
```python
from hologram import HologramApp, HoloKeyboardApp, MirrorApp
app = HologramApp(); app.boot()
app.save_html("hologram.html")        # reflection pyramid
app.save_floatup("floatup.html")      # float-up (Jones relief + power)
HoloKeyboardApp().boot(); HoloKeyboardApp().save_html("holokbd.html")
m = MirrorApp(); m.boot()
m.save_html("holomirror.html")            # aerial display
m.save_html("holomirror_kbd.html", True)  # aerial HHKB keyboard
```

The surfaces, the β(p,q) light field, the Jones relief, the power model, the
HHKB layout and the mirror/lens aerial optics are all computed in Bada; the
reflection / float-up / keyboard / aerial compositing is done in the canvas
renderer.
