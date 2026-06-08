# Omega Self-Evolution Engine (`omega_evolve`)

A small, **runnable** generative-AI self-evolution application distilled from the
Yamaguchi reports in [`../extracted/`](../extracted/) — chiefly
[`Bada1.md`](../extracted/Bada1.md) (the Omega / asperal TupleSpace language) and
[`explorerfiles.md`](../extracted/explorerfiles.md) (the global-differential
manifold / entropy apparatus).

It is an **open-ended evolutionary program-synthesis engine whose search
strategy evolves itself**: it generates candidate "manifolds" (symbolic
expressions), scores them by a heat-entropy fitness, stores everything in a
write-once memory, and — crucially — a `@reviser` **rewrites its own production
rules** every generation from credit assignment. The strategy the system uses to
improve itself improves alongside the solutions. That self-referential rewrite
is the concrete, buildable core of "self-evolution" in the reports.

Pure standard library. **Runs fully offline.** An optional Claude mutation hook
can be switched on if an API key is present.

## How the reports map to the code

| Report concept | Module | What it is |
|---|---|---|
| TupleSpace — "辞書を書き換えることができない" (no overwrite) | `tuplespace.py` | write-once, content-addressed store with lineage |
| `manifold_emerge` — `source_array × operator_data` | `manifold.py` | grow expression trees from operands × operators |
| heat-entropy / zeta-gamma **単調性** (monotonicity) | `entropy.py` | fitness = accuracy − parsimony − roughness |
| `@reviser` rewrites its own parser/operators | `reviser.py` | meta-policy: operator weights + mutation strength, rewritten by credit assignment |
| `cognitive_system` reload / rebuild / re-create loop | `engine.py` | the generational self-evolution loop |
| "generated AI" generative step | `llm.py` (optional) | Claude proposes a mutation; degrades silently to offline |

## Run it

```sh
# evolve a formula that fits a built-in target (the engine only sees samples)
python -m omega_evolve --target quadratic --generations 40 --pop 150 --seed 3

# other built-in targets: ripple (x·sin x), damped, gamma (log x / x + 0.5)
python -m omega_evolve --target ripple

# evolve against your own data (CSV of x,y rows)
python -m omega_evolve --csv mydata.csv --generations 60

# self-checks
python -m omega_evolve.tests
```

Example (the engine re-derives `x² + 2x + 1` from data alone):

```
gen  40 | best 0.9717 | champ 0.9717 | size  7 | mut 0.10 | TS 5361 | ((x - -1.003) * (x + 0.995))
champion   : ((x - -1.003) * (x + 0.995))      # ≈ (x+1)²
fitness    : 0.971745    rmse: 0.004084
```

### Artifacts (written to `--out`, default `omega_run/`)

- `tuplespace.json` — every manifold, every champion (hall-of-fame), and every
  rewritten `@reviser` policy snapshot, with full parent lineage.
- `evolution_report.md` — champion, fitness trajectory, and the final
  self-rewritten policy.

## What makes it "self-evolving" (not just an evolutionary algorithm)

A plain GA evolves *solutions* with fixed operators. Here the **operators
themselves evolve**:

- the `@reviser` keeps weights over its variation operators
  (`point_mutate`, `subtree_mutate`, `crossover`, `hoist`, `const_tweak`) and
  over the unary/binary node-operators used to grow trees;
- after each generation it performs **credit assignment** — operators that
  produced children fitter than their parents gain weight, the rest decay;
- mutation strength follows Rechenberg's 1/5 success rule;
- each rewritten policy is committed to the write-once TupleSpace, so the whole
  trajectory of "the system editing its own rules" is recorded and auditable.

You can watch this happen: on a polynomial target the reviser drives the `/`
operator weight toward its floor and boosts `*`/`+`; on an oscillatory target it
keeps `sin`/`cos` alive. The search policy adapts to the problem it is on.

## Enabling the optional generative-LLM step

```sh
export ANTHROPIC_API_KEY=sk-...          # and: pip install anthropic
python -m omega_evolve --target ripple --llm
```

When enabled, ~5% of mutations ask Claude (`OMEGA_LLM_MODEL`, default
`claude-sonnet-4-6`) to propose a variant tree in the same encoding. Any
failure falls back to the offline mutators, so the core never depends on it.

## Architecture

```
omega_evolve/
├── tuplespace.py   write-once content-addressed memory + lineage
├── manifold.py     expression trees, protected operators, manifold_emerge
├── entropy.py      heat-entropy fitness (accuracy − parsimony − roughness)
├── reviser.py      @reviser: self-rewriting meta-policy + variation operators
├── engine.py       cognitive_system: the self-evolution loop + hall of fame
├── datasets.py     built-in target problems + CSV loader
├── llm.py          optional Claude mutation hook (off by default)
├── __main__.py     CLI + report writer
└── tests.py        self-checks (python -m omega_evolve.tests)
```

## Honest scope

This is **evolutionary self-improvement of a search policy**, not LLM weight
self-training. It is a faithful, working realisation of the reports' mechanism —
generate → score by entropy → store write-once → rewrite the generator — at a
scale that actually runs in seconds on a laptop with no dependencies. The
optional LLM hook is the bridge to a generative model, but the self-evolution
property holds with or without it.
