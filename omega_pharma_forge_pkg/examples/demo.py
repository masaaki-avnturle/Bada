"""demo.py — 反応の時間推移を表示. `python examples/demo.py`"""
from omega_pharma_forge import QuantumSynthesizer, DosingConfig

s = QuantumSynthesizer(cfg=DosingConfig(steps=3000), seed=0xBADA)
s.run()
print(s.report())
print()
print("   t        P        I        A        B        C      chi   dose")
for f in s.log[::250]:
    print(f"{f.t:6.2f}  {f.P:.5f}  {f.I:.5f}  {f.A:.5f}  {f.B:.5f}  "
          f"{f.C:.5f}  {f.chi:.3f}  {f.dose:.4f}")
