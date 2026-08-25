"""demo.py — 内部統制システムを回してレポート表示. `python examples/demo.py`"""
from omega_mobius_drive import MobiusDriveSystem, FieldConfig

sys = MobiusDriveSystem(sectors=64, field_cfg=FieldConfig(nx=96, dt=0.4), seed=7)
sys.run(cycles=48)
print(sys.report())
print()
print("cycle  bit face   energy      lift_index")
for t in sys.log[::8]:
    print(f"{t.cycle:5d}  {t.bit}   {t.disk_face:+d}   {t.field_energy:9.4f}  {t.lift_index:+.4e}")
