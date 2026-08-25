import math
from omega_pharma_forge import (
    ReactionNetwork, RateConstants, State,
    QuantumSynthesizer, DosingConfig, run_uncontrolled,
)


def test_mass_conservation():
    net = ReactionNetwork(state=State(P=1.0, C=0.25))
    m0 = net.s.mass()
    for _ in range(500):
        net.step()
    assert abs(net.s.mass() - m0) < 1e-9


def test_concentrations_nonnegative():
    net = ReactionNetwork(state=State(P=1.0, C=0.5))
    for _ in range(800):
        net.step()
        for v in net.s.as_dict().values():
            assert v >= 0.0


def test_no_catalyst_no_chain():
    """触媒ゼロなら連鎖は立たず、前駆体は消費されない。"""
    net = ReactionNetwork(state=State(P=1.0, C=0.0))
    assert net.chain_factor() == 0.0
    for _ in range(300):
        net.step()
    assert math.isclose(net.s.P, 1.0, rel_tol=1e-12)
    assert net.s.A == 0.0


def test_chain_factor_scales_with_catalyst():
    """χ は触媒濃度に比例する（投与が制御レバーである根拠）。"""
    a = ReactionNetwork(state=State(P=1.0, C=0.05))
    b = ReactionNetwork(state=State(P=1.0, C=0.10))
    assert math.isclose(b.chain_factor(), 2.0 * a.chain_factor(), rel_tol=1e-12)


def test_controller_stays_subcritical():
    s = QuantumSynthesizer(cfg=DosingConfig(steps=2000), seed=0xBADA)
    s.run()
    d = s.summary()
    assert d["stayed_subcritical"] == 1.0
    assert d["max_chi"] < 1.0


def test_control_beats_uncontrolled_dump():
    """制御ありは、触媒一括投与より高純度・高収率になる。"""
    s = QuantumSynthesizer(cfg=DosingConfig(steps=3000), seed=0xBADA)
    s.run()
    c = s.summary()
    u = run_uncontrolled(steps=3000)
    assert c["purity"] > u["purity"]
    assert c["yield"] > u["yield"]
    assert c["max_I"] < u["max_I"]


def test_lower_chi_target_gives_higher_purity():
    """選択性トレードオフ: χ を絞るほど中間体が減り純度が上がる。"""
    hi = QuantumSynthesizer(cfg=DosingConfig(chi_target=0.80, chi_max=0.95,
                                             steps=3000), seed=0xBADA)
    lo = QuantumSynthesizer(cfg=DosingConfig(chi_target=0.30, chi_max=0.45,
                                             steps=3000), seed=0xBADA)
    hi.run(); lo.run()
    assert lo.summary()["purity"] > hi.summary()["purity"]
    assert lo.summary()["max_I"] < hi.summary()["max_I"]


def test_scram_latches_on_supercritical():
    cfg = DosingConfig(chi_target=5.0, chi_max=9.0, chi_scram=1.0,
                       dose_high=0.05, dose_low=0.05, catalyst_budget=1.0,
                       steps=200)
    s = QuantumSynthesizer(cfg=cfg, seed=1)
    s.run()
    assert s.summary()["scram"] == 1.0


def test_reproducible():
    a = QuantumSynthesizer(cfg=DosingConfig(steps=800), seed=77); a.run()
    b = QuantumSynthesizer(cfg=DosingConfig(steps=800), seed=77); b.run()
    assert a.summary() == b.summary()
