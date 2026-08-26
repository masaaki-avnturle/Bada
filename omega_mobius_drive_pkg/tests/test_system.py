import math
from omega_mobius_drive import (
    MobiusDisk, DAlembertField, FieldConfig, PseudoQuantumVM, MobiusDriveSystem,
)


def test_mobius_double_cover():
    d = MobiusDisk(sectors=8)
    d.write(0b10101010)
    d.seek(8)                       # 1 lap -> back face
    assert d.face == -1
    assert d.read() == (~0b10101010) & 0xFF
    d.seek(8)                       # 2 laps -> front restored
    assert d.face == 1
    assert d.read() == 0b10101010
    assert d.is_orientable_return()


def test_field_cfl_guard():
    try:
        DAlembertField(FieldConfig(nx=16, dx=1.0, dt=2.0, c=1.0))
        assert False, "should reject CFL>1"
    except ValueError:
        pass


def test_field_stays_finite():
    f = DAlembertField(FieldConfig(nx=48, dt=0.4))
    f.seed_gaussian(amp=1.0)
    for _ in range(50):
        f.step(source_fn=lambda i, t: math.sin(t) if i == 24 else 0.0)
    assert math.isfinite(f.energy())
    assert math.isfinite(f.lift_index())


def test_vm_deterministic_with_seed():
    p = [("LOAD",0,0),("H",0),("MEASURE",0),("HALT",)]
    a = PseudoQuantumVM(seed=123).run(list(p))
    b = PseudoQuantumVM(seed=123).run(list(p))
    assert a == b
    assert a[0] in (0, 1)


def test_vm_x_flips():
    vm = PseudoQuantumVM(seed=1)
    out = vm.run([("LOAD",0,0),("X",0),("MEASURE",0),("HALT",)])
    assert out == [1]


def test_system_runs_and_is_stable():
    s = MobiusDriveSystem(sectors=64, seed=7)
    s.run(cycles=40)
    summ = s.summary()
    assert summ["cycles"] == 40
    assert summ["stable"] == 1.0
    assert math.isfinite(summ["final_lift"])


def test_system_reproducible():
    a = MobiusDriveSystem(sectors=64, seed=99); a.run(30)
    b = MobiusDriveSystem(sectors=64, seed=99); b.run(30)
    assert a.summary() == b.summary()
