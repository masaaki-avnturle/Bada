"""demo.py — 外乱→SCRAM→鎮静の推移を表示. `python examples/demo.py`"""
from omega_critical_guard import CriticalGuard

g = CriticalGuard(seed=21)
g.run(generations=60, perturbation_at=20, perturbation_neutrons=3000)
print(g.report())
print()
print("gen  population  absorption  k_eff   qbit  SCRAM")
for t in g.log[::4]:
    print(f"{t.generation:3d}  {t.population:10d}  {t.absorption:9.3f}  {t.k_eff:.3f}   {t.qbit}    {'*' if t.scram else ''}")
