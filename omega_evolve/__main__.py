"""Command-line entry point for the Omega Self-Evolution Engine.

    python -m omega_evolve --target ripple --generations 40 --pop 150

Runs the self-evolution loop against a built-in target (or a CSV of x,y rows),
prints per-generation progress, and writes artifacts: the evolved TupleSpace
(JSON), an evolution report (Markdown), and the champion manifold.
"""

from __future__ import annotations

import argparse
import os
import time

from . import datasets, manifold as M
from .engine import Engine
from .llm import make_llm_mutator


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="omega_evolve", description=__doc__)
    p.add_argument("--target", choices=sorted(datasets.PRESETS), default="ripple",
                   help="built-in problem to evolve against")
    p.add_argument("--csv", help="evolve against x,y rows from a CSV instead")
    p.add_argument("--generations", type=int, default=40)
    p.add_argument("--pop", type=int, default=150)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--grow-depth", type=int, default=4)
    p.add_argument("--lambda-size", type=float, default=0.004,
                   help="entropy/parsimony penalty per node")
    p.add_argument("--lambda-rough", type=float, default=0.0,
                   help="monotonicity/smoothness penalty weight")
    p.add_argument("--patience", type=int, default=0,
                   help="stop after N generations without improvement (0=off)")
    p.add_argument("--llm", action="store_true",
                   help="enable the optional Claude mutation hook if available")
    p.add_argument("--out", default="omega_run", help="artifact output directory")
    p.add_argument("--quiet", action="store_true")
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)

    if args.csv:
        xs, ys, desc = datasets.from_csv(args.csv)
    else:
        xs, ys, desc = datasets.PRESETS[args.target]()

    llm = make_llm_mutator() if args.llm else None
    if args.llm and llm is None and not args.quiet:
        print("[llm] hook requested but unavailable (no ANTHROPIC_API_KEY / SDK); "
              "continuing offline.")

    engine = Engine(
        xs, ys, pop_size=args.pop, seed=args.seed, grow_depth=args.grow_depth,
        lambda_size=args.lambda_size, lambda_rough=args.lambda_rough, llm_mutator=llm,
    )

    if not args.quiet:
        print(f"omega_evolve :: target={desc}  points={len(xs)}  pop={args.pop}  "
              f"gens={args.generations}  seed={args.seed}")
        print("-" * 72)

    def report(gen, champ, row):
        if args.quiet:
            return
        ms = row["policy"]["mutation_strength"]
        print(f"gen {gen:>3} | best {row['best_fitness']:.4f} | champ "
              f"{row['champion_fitness']:.4f} | size {row['best_size']:>2} | "
              f"mut {ms:.2f} | TS {row['tuplespace']:>5} | {row['best_expr']}")

    t0 = time.time()
    result = engine.run(args.generations, patience=args.patience, on_generation=report)
    dt = time.time() - t0

    champ = result.champion
    from . import entropy
    rmse = entropy.rmse(champ.node, xs, ys)

    os.makedirs(args.out, exist_ok=True)
    ts_path = os.path.join(args.out, "tuplespace.json")
    rep_path = os.path.join(args.out, "evolution_report.md")
    result.space.save(ts_path)
    _write_report(rep_path, desc, args, result, rmse, dt)

    if not args.quiet:
        print("-" * 72)
        print(f"champion   : {M.to_string(champ.node)}")
        print(f"fitness    : {champ.fitness:.6f}    rmse: {rmse:.6f}    "
              f"size: {M.size(champ.node)}")
        print(f"target law : {desc}")
        print(f"tuplespace : {len(result.space)} write-once records")
        print(f"artifacts  : {ts_path}\n             {rep_path}")
        print(f"elapsed    : {dt:.2f}s over {result.generations} generations")
    return 0


def _write_report(path, desc, args, result, rmse, dt) -> None:
    champ = result.champion
    lines = []
    lines.append("# Omega Self-Evolution — run report\n")
    lines.append(f"- target law: `{desc}`")
    lines.append(f"- population: {args.pop}, generations: {result.generations}, "
                 f"seed: {args.seed}, grow-depth: {args.grow_depth}")
    lines.append(f"- elapsed: {dt:.2f}s, tuplespace records: {len(result.space)}\n")
    lines.append("## Champion manifold\n")
    lines.append(f"```\n{M.to_string(champ.node)}\n```\n")
    lines.append(f"- fitness: **{champ.fitness:.6f}**, rmse: **{rmse:.6f}**, "
                 f"size: {M.size(champ.node)}\n")

    lines.append("## Fitness trajectory\n")
    lines.append("| gen | champion | best | size | mut | success | TS |")
    lines.append("|----:|---------:|-----:|-----:|----:|--------:|---:|")
    for r in result.history:
        pol = r["policy"]
        lines.append(
            f"| {r['generation']} | {r['champion_fitness']:.4f} | "
            f"{r['best_fitness']:.4f} | {r['best_size']} | "
            f"{pol['mutation_strength']:.2f} | "
            f"{pol['success_rate'] if pol['success_rate'] is not None else '-'} | "
            f"{r['tuplespace']} |"
        )

    lines.append("\n## Self-rewritten policy (final @reviser state)\n")
    final = result.history[-1]["policy"] if result.history else {}
    lines.append("```json")
    import json
    lines.append(json.dumps(final, indent=2, ensure_ascii=False))
    lines.append("```")
    lines.append("\n> The variation/operator weights above were rewritten by the "
                 "engine's own credit assignment — the search strategy evolved "
                 "alongside the manifolds it was searching for.")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
