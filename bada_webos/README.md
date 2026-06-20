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
| `terminal/` | a **terminal** that bundles **bash** (20+ builtins, pipes, redirection), **vim** (the modal BadaVim) and **emacs** (C-x C-s / C-k / C-y …) over one in-memory **VFS** — files made with bash are edited by either editor and run with `bada`. Also exposes the `qcrypto` command. |
| `qcrypto/` | **quantum-crypto app** wrapping the repo's `jones_quantum_crypto` engine: cryptanalysing a quantum (Ed25519) digital signature recovers a secret braid and **activates Jones-polynomial quantum cryptography**. A desktop window + the terminal `qcrypto` command + `apps/quantum_crypto.bada` on the VM. |
| `apps/lib/` | the **Jones polynomial implemented in the Bada language itself** — `laurent.bada` (Laurent-polynomial algebra) + `jones.bada` (Kauffman-bracket state sum, union-find, writhe normalisation). `apps/quantum_crypto_jones.bada` computes `V(t)` on the Bada VM; cross-checked against the Python reference (trefoil → `t+t³−t⁴`, figure-eight, Hopf, …). |
| `al/` + `apps/al/` | **AL — Laevatein AI / machine OS** (Full-Metal-Panic-themed simulation), with **all libraries written in Bada**: a **quantum algorithm** (Grover, `qsim.bada`), Lambda Driver **cooling** control (`cooling.bada`), **self-evolving neural consciousness** (`neuro.bada`), the **a-priori code engine** (`apriori.bada`), **robot FPGA** control (`fpga.bada`), and the **pilot resonance link** — EEG **gamma** extraction (`eeg.bada`), **fMRI/topography** (`fmri_topo.bada`), a **resonance device** (`resonance.bada`), **haloperidol biofeedback** (`biofeedback.bada`) and the **Lambda Driver** projecting an **AT field + anti-gravity** from the pilot's gamma waves (`lambda_drive.bada`). Desktop window + terminal `al` command. |
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
python3 cli.py term              # terminal demo: bash + vim + emacs + bada
python3 cli.py term -i           # interactive terminal — type into vim/emacs
python3 cli.py term -i --line    # interactive, line-input editors (no curses)
python3 cli.py run apps/ultranetwork.bada   # run a Bada app through the kernel
python3 cli.py run apps/quantum_crypto.bada # the quantum-crypto flow in Bada

make test                        # 42 tests
```

### Quantum crypto app (Jones-polynomial quantum cryptography)
Cryptanalysing the quantum digital signature activates the Jones cipher. From
the terminal:
```
bada@webos:~$ qcrypto                 # break the signature -> activate
quantum signature: VALID
cryptanalysis: broke key 0042 in 43 tries
recovered braid: [1, 1, 1]
Jones V(t) = +1*t^1 +1*t^3 -1*t^4
Jones-polynomial quantum cryptography ACTIVATED
bada@webos:~$ qcrypto jones 1 1 1     # Jones polynomial (reference engine)
bada@webos:~$ qcrypto badajones 1 1 1 # Jones polynomial computed IN BADA
V(t) = +1*t^1 +1*t^3 -1*t^4  (computed in Bada)
```
The full engine lives in `../jones_quantum_crypto/` (also a standalone CLI).
The **Jones polynomial is also implemented natively in Bada** under
`apps/lib/` and run on the VM:
```bash
python3 -c "import sys; sys.path.insert(0,'../bada_silent_vim'); \
  from bada import run_program; run_program('apps/quantum_crypto_jones.bada')"
```

### Terminal — bash · vim · emacs in one place
```
bada@webos:~$ echo say \"hello from the terminal\" > hello.bada
bada@webos:~$ vim hello.bada        # modal editor; o-pen a line, :wq to save
bada@webos:~$ cat hello.bada
say "hello from the terminal"
print 6 * 7
bada@webos:~$ bada hello.bada       # run it on the Bada VM
hello from the terminal
42
bada@webos:~$ emacs notes.txt       # C-x C-s save, C-x C-c exit
```
bash builtins: `pwd cd ls echo cat mkdir touch rm cp mv head grep wc env
export whoami clear bada vim emacs help`, with pipes (`|`) and redirection
(`>`/`>>`).  bash, vim and emacs all share the same VFS.

#### Interactive character input
`term -i` is a real REPL: running `vim FILE` or `emacs FILE` drops you into the
editor and **your keystrokes go straight into the buffer**.

* On a real terminal it opens a full-screen **curses** editor — vim with
  INSERT/NORMAL modes (`i` to insert, `Esc`, `hjkl`, `:w`/`:q`/`:wq`) and emacs
  with self-insert + `C-f C-b C-n C-p C-a C-e`, `C-d`, `C-k` kill, `C-y` yank,
  `C-x C-s` save, `C-x C-c` exit.
* With no tty (pipes / web shell) it falls back to **line input** — typed lines
  are inserted; `:wq`/`:q` (vim) and `C-x C-s`/`C-x C-c` (emacs) still work — so
  character input works everywhere.

```
bada@webos:~$ vim story.bada
say "typed live in vim"      ← typed by you
print 6 * 7                  ← typed by you
:wq
bada@webos:~$ bada story.bada
typed live in vim
42
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
