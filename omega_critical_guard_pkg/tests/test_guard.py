import math
from omega_critical_guard import ChainCore, CoreConfig, CriticalGuard, GuardConfig


def test_k_eff_analytic():
    core = ChainCore()
    # k_eff = nu * p_f * (1-a)
    assert math.isclose(core.k_eff(0.0), 2.4 * 0.45, rel_tol=1e-12)
    a_star = core.critical_absorption()
    assert math.isclose(core.k_eff(a_star), 1.0, rel_tol=1e-9)
    assert core.k_eff(a_star + 0.05) < 1.0


def test_unguarded_chain_grows():
    core = ChainCore(seed=5, initial_neutrons=100)
    for _ in range(10):
        core.step(absorption=0.0)
    assert core.population > 100      # k>1 で成長


def test_guarded_chain_stays_subcritical():
    g = CriticalGuard(seed=21)
    g.run(generations=60)
    s = g.summary()
    assert s["always_subcritical"] == 1.0
    assert s["max_k_eff"] < 1.0


def test_guarded_chain_decays():
    g = CriticalGuard(seed=21)
    g.run(generations=80)
    assert g.summary()["final_population"] < 100


def test_scram_on_perturbation():
    g = CriticalGuard(seed=21)
    g.run(generations=60, perturbation_at=10, perturbation_neutrons=100000)
    s = g.summary()
    assert s["scram_events"] >= 1          # SCRAM が作動した
    assert s["final_population"] < 100     # 連鎖は抑え込まれた


def test_scram_latch_releases():
    cfg = GuardConfig(scram_threshold=500, scram_release_below=50)
    g = CriticalGuard(cfg=cfg, seed=3)
    g.run(generations=40, perturbation_at=5, perturbation_neutrons=2000)
    scrams = [t.scram for t in g.log]
    assert any(scrams)
    assert not scrams[-1]                  # 人口低下後は解除されている


def test_reproducible():
    a = CriticalGuard(seed=77); a.run(50)
    b = CriticalGuard(seed=77); b.run(50)
    assert a.summary() == b.summary()
