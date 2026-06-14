# bada_webos — a Web OS written around the Bada language

A single, runnable system that fulfils the brief: **a Web OS whose application
programming language is Bada**, built on the previously-designed **quantum
computer OS**, windowed by **w9wm**, with **quantum error correction**, an
**Android 12 installer**, a **Rails→OS** design bridge, a **cloud-bridged
settings panel**, and the **ultranetwork** rebuilt on top.

Pure **Python 3 (stdlib only)** + Bada programs running on the Bada VM
(`bada_silent_vim/bada`). No third-party packages.

```
                         ┌─────────────── BadaWebOS ───────────────┐
 Rails scaffold ─▶ railsbridge ─▶ OS app (object + HTML windows) ─┐ │
 settings ◀▶ cloud (Bridge+Repeater) ◀▶ HardwareProfile          │ │
 ultranetwork.bada ─▶ ultranet (TupleSpace/XOR/gravity/repeater) ─┼─▶ w9wm desktop ─▶ HTML
 Android 12 app ─▶ android.installer ─▶ launcher window          │ │
            all apps run on ── kernel (Bada VM) ── on a quantum  ─┘ │
            substrate protected by Shor-9 QEC ─────────────────────┘
```

## Subsystems

| dir | what it is |
|:--|:--|
| `quantum/` | **Shor 9-qubit code** on a 512-amplitude state-vector simulator — corrects any single-qubit X/Y/Z error (all 27 cases, fidelity ≈ 1.0). Protects the kernel's boot register. |
| `kernel/` | **QuantumKernel** — boots with Shor-9 QEC, holds the object registry (*function→object*), soft-driver registry (*hardware→software*), and runs Bada apps (*Bada = app language*). |
| `wm/` | **w9wm** reproduction — 9wm semantics + title bars + **8 virtual screens**, click-to-focus, root menu `New/Reshape/Move/Delete/Hide` + screens; ASCII & HTML renderers. |
| `railsbridge/` | **Rails→OS** transpiler — a scaffold resource becomes an OS app: model→object schema, actions→methods, views→HTML window templates, routes→menu, device→soft driver. |
| `cloud/` | **Settings panel** synced to a **CloudStore** through a **Bridge + Repeater**, and `adapt_to_hardware` to fit the design to the device (dpi→font, size→layout, touch→hit-target). |
| `ultranet/` | the **ultranetwork**: TupleSpace + arrow-syntax eval (on the Bada VM), neural **XOR learning**, **gravity-port** gates, **bridge/repeater** propagation. |
| `android/` | **Android 12** installer — verify manifest (targetSdk 31), resolve runtime permissions, install, launch as a window. |
| `render/` | renders the whole desktop to one HTML page (the "HTML-template OS frame"). |
| `apps/` | Bada applications (`ultranetwork.bada`). |

## Run it

```bash
cd bada_webos

python3 webos.py                 # boot the whole OS, write generated/desktop.html
python3 cli.py boot --html out.html
python3 cli.py qec --all         # all 27 single-qubit errors corrected
python3 cli.py ultranet          # TupleSpace + XOR + gravity + repeater
python3 cli.py rails article title:string body:text published:boolean
python3 cli.py android           # install + launch the Android 12 app
python3 cli.py wm                # w9wm ASCII desktop + root menu
python3 cli.py run apps/ultranetwork.bada   # run a Bada app through the kernel

make test                        # 18 tests
```

### What `boot` produces
```
Shor-9 QEC : Y@4 -> Y@4 -> fidelity 1.0 (OK)
objects    : ['article']          drivers : ['article']
windows    : ['Articles — index', 'Articles — new', 'ultranetwork',
              'Settings (cloud-bridged)', 'Android: Bada Notes (com.bada.notes)']
ultranet   : XOR acc 1.0, propagation {'A':1.0,'B':0.6,'C':0.36,'D':0.432,'E':0.2592}
settings   : layout=desktop font_scale=1.25 (cloud v…)
android    : ['com.bada.notes']
```
and `examples/desktop.html` — the rendered w9wm desktop.

## Design decisions (from the Q&A)
- **Ultranetwork core**: TupleSpace + arrow evaluator, gravity-port gates,
  neural XOR learning, bridge/repeater propagation — all included.
- **Window config**: desktop + multiple windows, full WM (**w9wm**, 8 screens).
- **QEC**: **Shor 9-qubit code**.
- **w9wm fidelity**: reproduced as-is (9wm semantics + title bars + 8 virtual
  screens + the standard root menu).
- **App language**: **Bada** — apps are `.bada` programs on the Bada VM.

## Relationship to `bada_silent_vim/`
This package reuses the Bada compiler + VM from `../bada_silent_vim/bada`.
That earlier package also lets you **operate Bada by silent talk**; here Bada
is the application language of a full Web OS.
