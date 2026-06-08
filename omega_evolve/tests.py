"""Minimal self-checks. Run: python -m omega_evolve.tests"""

from __future__ import annotations

from . import datasets, entropy, manifold as M
from .engine import Engine
from .tuplespace import TupleSpace


def test_tuplespace_write_once() -> None:
    ts = TupleSpace()
    k1 = ts.put({"a": 1}, tags=["x"])
    k2 = ts.put({"a": 1}, tags=["y"])      # identical content -> no new record
    assert k1 == k2
    assert len(ts) == 1
    assert ts.select("x") and not ts.select("y")  # tags fixed at first write
    k3 = ts.put({"a": 2})
    assert k3 != k1 and len(ts) == 2
    print("ok  tuplespace write-once")


def test_manifold_roundtrip() -> None:
    node = ("b", "+", ("u", "sin", ("var",)), ("const", 2.0))
    assert abs(M.evaluate(node, 0.0) - 2.0) < 1e-9
    assert M.size(node) == 4
    paths = M.all_paths(node)
    assert () in paths and (2,) in paths
    rebuilt = M.set_at(node, (3,), ("const", 5.0))
    assert M.get_at(rebuilt, (3,))[1] == 5.0
    print("ok  manifold structure + eval")


def test_protected_operators() -> None:
    # protected log/div never raise or return nan
    assert M.evaluate(("u", "log", ("const", 0.0)), 0.0) == 0.0
    assert M.evaluate(("b", "/", ("const", 1.0), ("const", 0.0)), 0.0) == 1.0
    print("ok  protected operators")


def test_evolution_improves_and_self_rewrites() -> None:
    xs, ys, _ = datasets.quadratic()
    eng = Engine(xs, ys, pop_size=120, seed=7, grow_depth=4)
    before = dict(eng.reviser.binary_w)
    res = eng.run(25, patience=0)
    champ = res.champion
    assert champ.fitness > 0.9, f"weak champion: {champ.fitness}"
    y_range = max(ys) - min(ys)
    assert entropy.rmse(champ.node, xs, ys) < 0.2 * y_range  # within 20% of scale
    # the @reviser must have rewritten its own policy
    after = eng.reviser.binary_w
    assert any(abs(after[k] - before[k]) > 1e-6 for k in before), "policy did not self-rewrite"
    # champions are queryable provenance records
    champs = res.space.select("champion")
    assert champs, "no champion records"
    # lineage of the champion reaches a root (emerge) record
    lin = res.space.lineage(champs[-1]["parents"][0])
    assert any(r["op"] == "emerge" for r in lin), "champion has no ancestry to a seed"
    print(f"ok  evolution: fitness={champ.fitness:.4f} "
          f"expr={M.to_string(champ.node)} records={len(res.space)}")


def main() -> int:
    test_tuplespace_write_once()
    test_manifold_roundtrip()
    test_protected_operators()
    test_evolution_improves_and_self_rewrites()
    print("\nALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
