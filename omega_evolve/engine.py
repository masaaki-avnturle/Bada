"""cognitive_system -- the self-evolution loop.

Each generation:

  1. evaluate every manifold's heat-entropy fitness,
  2. archive the champion (hall of fame, write-once into the TupleSpace),
  3. breed a new population: select parents by tournament, ask the @reviser for
     a variation operator, apply it, and commit the child + its lineage,
  4. let the @reviser **rewrite its own policy** from this generation's credit.

The loop is open-ended: stop on a generation budget or when a target fitness /
stagnation criterion is met.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from . import entropy, manifold as M
from .reviser import Reviser
from .tuplespace import TupleSpace, content_hash


@dataclass
class Individual:
    node: M.Node
    fitness: float = 0.0
    key: str = ""


@dataclass
class EvolutionResult:
    champion: Individual
    history: List[Dict[str, object]] = field(default_factory=list)
    space: Optional[TupleSpace] = None
    generations: int = 0


class Engine:
    def __init__(
        self,
        xs: List[float],
        ys: List[float],
        *,
        pop_size: int = 120,
        seed: int = 0,
        elitism: int = 2,
        tournament: int = 4,
        grow_depth: int = 4,
        lambda_size: float = 0.004,
        lambda_rough: float = 0.0,
        llm_mutator: Optional[Callable[[M.Node, random.Random], Optional[M.Node]]] = None,
    ) -> None:
        self.xs, self.ys = xs, ys
        self.y_scale = (max(ys) - min(ys)) or 1.0
        self.pop_size = pop_size
        self.elitism = elitism
        self.tournament = tournament
        self.lambda_size = lambda_size
        self.lambda_rough = lambda_rough
        self.rng = random.Random(seed)
        self.reviser = Reviser(self.rng, grow_depth=grow_depth)
        self.space = TupleSpace()
        self.llm_mutator = llm_mutator
        self.population: List[Individual] = []

    # -- scoring ------------------------------------------------------------
    def score(self, node: M.Node) -> float:
        return entropy.fitness(
            node, self.xs, self.ys, self.y_scale, self.lambda_size, self.lambda_rough
        )

    def _commit(self, node: M.Node, fit: float, *, op: str, parents: List[str], tags) -> Individual:
        key = self.space.put(
            list(_jsonable(node)),
            tags=tags,
            parents=parents,
            op=op,
            meta={"fitness": round(fit, 6), "size": M.size(node), "expr": M.to_string(node)},
        )
        return Individual(node=node, fitness=fit, key=key)

    def _enshrine(self, ind: Individual, *, generation: int) -> str:
        """Record a champion as a distinct hall-of-fame provenance record that
        *references* the manifold key. (We never re-put the manifold itself --
        the TupleSpace is write-once, so a fresh record is the only way to add
        the 'champion' tag without colliding with the existing manifold.)"""
        return self.space.put(
            {
                "champion": True,
                "generation": generation,
                "manifold": ind.key,
                "fitness": round(ind.fitness, 6),
                "expr": M.to_string(ind.node),
                "size": M.size(ind.node),
            },
            tags=["champion"],
            op="hall_of_fame",
            parents=[ind.key],
        )

    # -- population ---------------------------------------------------------
    def _seed_population(self) -> None:
        self.population = []
        for _ in range(self.pop_size):
            node = self.reviser.grow()
            fit = self.score(node)
            ind = self._commit(node, fit, op="emerge", parents=[], tags=["manifold"])
            self.population.append(ind)
        self.population.sort(key=lambda i: i.fitness, reverse=True)

    def _select(self) -> Individual:
        best = None
        for _ in range(self.tournament):
            cand = self.rng.choice(self.population)
            if best is None or cand.fitness > best.fitness:
                best = cand
        return best

    # -- main loop ----------------------------------------------------------
    def run(
        self,
        generations: int = 40,
        *,
        target_fitness: float = 0.999,
        patience: int = 0,
        on_generation: Optional[Callable[[int, Individual, Dict[str, object]], None]] = None,
    ) -> EvolutionResult:
        self._seed_population()
        history: List[Dict[str, object]] = []
        champion = self.population[0]
        self._enshrine(champion, generation=0)
        stagnation = 0

        for gen in range(1, generations + 1):
            self.reviser.begin_generation()
            self.population.sort(key=lambda i: i.fitness, reverse=True)
            new_pop: List[Individual] = self.population[: self.elitism]

            while len(new_pop) < self.pop_size:
                parent = self._select()
                op = self.reviser.choose_variation()
                mate = self._select() if op == "crossover" else None
                child_node = self.reviser.vary(op, parent.node, mate.node if mate else None)

                # optional generative-LLM mutation, applied rarely if available
                if self.llm_mutator is not None and self.rng.random() < 0.05:
                    proposed = self.llm_mutator(child_node, self.rng)
                    if proposed is not None:
                        child_node = proposed
                        op = "llm_mutate"

                fit = self.score(child_node)
                parents = [parent.key] + ([mate.key] if mate else [])
                child = self._commit(child_node, fit, op=op, parents=parents, tags=["manifold"])
                self.reviser.record(op if op != "llm_mutate" else "subtree_mutate",
                                    child_node, fit - parent.fitness)
                new_pop.append(child)

            self.population = new_pop
            self.population.sort(key=lambda i: i.fitness, reverse=True)
            gen_best = self.population[0]

            improved = gen_best.fitness > champion.fitness + 1e-9
            if improved:
                champion = gen_best
                self._enshrine(champion, generation=gen)
                stagnation = 0
            else:
                stagnation += 1

            policy = self.reviser.adapt()
            self.space.put({"generation": gen, "policy": policy},
                           tags=["policy"], op="reviser.adapt")

            row = {
                "generation": gen,
                "best_fitness": round(gen_best.fitness, 6),
                "champion_fitness": round(champion.fitness, 6),
                "best_expr": M.to_string(gen_best.node),
                "best_size": M.size(gen_best.node),
                "policy": policy,
                "tuplespace": len(self.space),
            }
            history.append(row)
            if on_generation:
                on_generation(gen, champion, row)

            if champion.fitness >= target_fitness:
                break
            if patience and stagnation >= patience:
                break

        return EvolutionResult(champion=champion, history=history,
                               space=self.space, generations=len(history))


def _jsonable(node: M.Node):
    """Tuples -> lists so the node round-trips through JSON in the TupleSpace."""
    kind = node[0]
    if kind == "const":
        return [kind, node[1]]
    if kind == "var":
        return [kind]
    if kind == "u":
        return [kind, node[1], _jsonable(node[2])]
    return [kind, node[1], _jsonable(node[2]), _jsonable(node[3])]
