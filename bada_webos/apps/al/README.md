# AL — Laevatein AI / Machine OS  (codename **AL**)

A Full-Metal-Panic-themed **simulation**, with **all libraries written in the
Bada language itself** and a **quantum algorithm implemented in Bada**.  AL is
the artificial intelligence and machine-circuit OS of the ARX-8 Laevatein.

> Fiction: anti-gravity coolant, machine consciousness and the "unknown
> a-priori engine" are dramatised. Everything here is a runnable *simulation*.

## Subsystems (every one is a Bada library — `lib/*.bada`)

| Bada library | role |
|:--|:--|
| `qsim.bada` | **quantum algorithm** — Grover's search (real-amplitude state vector) amplifies the Lambda Driver's marked resonance mode out of `2^n` unknowns. |
| `cooling.bada` | **Lambda Driver cooling** — feedback control of the supercooled-metal anti-gravity coolant on the palladium reactor; returns `[maxT, finalT, meltdown]`. |
| `neuro.bada` | **self-evolving consciousness** — a recurrent palladium-reactor neural net (quantum-microtubule seeded) that hill-climbs to maximise global-workspace ignition. |
| `apriori.bada` | **unknown a-priori engine** — generates new source code from the AI's state seed (the engine that writes the engine). |
| `fpga.bada` | **robot neural FPGA** — sensor→motor reflexes synthesised to lookup tables (obstacle avoidance). |
| `mathx.bada`, `rng.bada` | Bada math (`fsqrt`) and a reproducible PRNG. |

`al_laevatein.bada` boots all of them on the Bada VM and records the AL state in
the `Omega::DATABASE[al]` Akashic TupleSpace.

## Run
```bash
# the whole AL OS, on the Bada VM (libraries written in Bada)
python3 -c "import sys; sys.path.insert(0,'../../../bada_silent_vim'); \
  from bada import run_program; run_program('al_laevatein.bada')"

# from the BadaWebOS terminal:
al                 # boot summary (mode, consciousness, cooling)
al grover 4 11     # the quantum algorithm
al cool 120 220 0.8
al mind 8 60 1234  # evolve machine consciousness
al robot 1 0 1     # robot FPGA motor command
al gen 77 3        # a-priori engine source generation
```

## Verified
- Grover returns the marked mode for several `(n, marked)` (e.g. `grover(4,11)=11`).
- Cooling stays below the meltdown threshold under nominal load and melts down
  under extreme load.
- The neural network evolves to ignite most of its neurons.
- Robot FPGA: clear path → `[1,1]`; obstacle ahead, left open → `[0,1]` (turn).

Booted as the **"AL — Laevatein AI OS"** window on the BadaWebOS desktop and
exposed through the terminal `al` command.
