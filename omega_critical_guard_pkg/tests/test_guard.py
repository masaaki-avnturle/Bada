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


# --------------------------------------------------------------------------- #
#  未臨界増倍と 1/M 法による安全な臨界接近
# --------------------------------------------------------------------------- #
from omega_critical_guard import (
    multiplication, inverse_multiplication, steady_population, relaxation_time,
    approach_series, ApproachToCritical, ApproachConfig, run_unsafe_approach,
    PointKinetics, KineticsConfig, reactivity_from_k,
)


def test_multiplication_diverges_at_criticality():
    """M = 1/(1-k) は k→1 で発散する。これが臨界期の強度。"""
    assert math.isclose(multiplication(0.0), 1.0)
    assert math.isclose(multiplication(0.5), 2.0)
    assert math.isclose(multiplication(0.99), 100.0)
    assert math.isclose(multiplication(0.999), 1000.0)
    assert math.isinf(multiplication(1.0))
    assert math.isinf(multiplication(1.5))


def test_multiplication_is_monotone_increasing():
    ks = [0.0, 0.3, 0.6, 0.9, 0.99]
    ms = [multiplication(k) for k in ks]
    assert all(b > a for a, b in zip(ms, ms[1:]))


def test_inverse_multiplication_goes_linearly_to_zero():
    """1/M = 1-k は臨界で 0 になり、k に対して直線。だから外挿できる。"""
    for k in (0.0, 0.25, 0.5, 0.75, 0.9):
        assert math.isclose(inverse_multiplication(k), 1.0 - k)
    assert inverse_multiplication(1.0) == 0.0


def test_geometric_series_converges_to_steady_population():
    """S(1 + k + k^2 + ...) が S/(1-k) に収束する。"""
    for k in (0.3, 0.6, 0.9):
        assert math.isclose(approach_series(k, terms=400, source=1.0),
                            steady_population(k, 1.0), rel_tol=1e-9)


def test_relaxation_time_diverges_critical_slowing_down():
    """臨界減速: tau = l/(1-k) も k→1 で発散する。"""
    assert math.isclose(relaxation_time(0.0, 1e-4), 1e-4)
    assert math.isclose(relaxation_time(0.9, 1e-4), 1e-3)
    assert relaxation_time(0.999, 1e-4) > relaxation_time(0.99, 1e-4)
    assert math.isinf(relaxation_time(1.0, 1e-4))


def test_one_over_m_extrapolation_predicts_the_critical_point():
    """まだ到達していない臨界位置を、1/M の外挿が事前に当てる。"""
    a = ApproachToCritical(k_of_x=lambda x: 1.25 * x, seed=0x51DE)   # 臨界 x=0.8
    a.run()
    pred = a.summary()["final_prediction"]
    assert math.isclose(pred, 0.8, abs_tol=0.01), pred


def test_safe_approach_never_crosses_critical():
    a = ApproachToCritical(seed=0x51DE)
    a.run()
    s = a.summary()
    assert s["stayed_subcritical"] == 1.0
    assert s["max_k"] < 1.0


def test_safe_approach_still_gets_close():
    """安全でありながら、ちゃんと臨界の近くまで到達する。"""
    a = ApproachToCritical(seed=0x51DE)
    a.run()
    assert a.summary()["final_k"] > 0.99


def test_unsafe_fixed_step_approach_crosses_critical():
    """外挿を使わず固定刻みで進むと踏み越える。"""
    u = run_unsafe_approach(fixed_step=0.2)
    assert u["crossed_critical"] == 1.0
    assert u["max_k"] >= 1.0


def test_approach_is_reproducible():
    a = ApproachToCritical(seed=99); a.run()
    b = ApproachToCritical(seed=99); b.run()
    assert a.summary() == b.summary()


def test_reactivity_from_k():
    assert math.isclose(reactivity_from_k(1.0), 0.0)
    assert reactivity_from_k(1.01) > 0
    assert reactivity_from_k(0.99) < 0


def test_prompt_critical_boundary_is_beta():
    pk = PointKinetics(KineticsConfig(beta=0.0065))
    assert not pk.is_prompt_critical(0.0064)
    assert pk.is_prompt_critical(0.0065)
    assert pk.is_prompt_critical(0.010)


def test_period_matches_the_one_group_analytic_formula():
    """小さな rho では T = (beta - rho)/(lambda*rho) に一致する。"""
    cfg = KineticsConfig(beta=0.0065, Lambda=1e-4, lam=0.0785)
    pk = PointKinetics(cfg)
    for rho in (0.0005, 0.001, 0.002):
        analytic = (cfg.beta - rho) / (cfg.lam * rho)
        assert math.isclose(pk.period(rho), analytic, rel_tol=0.05), rho


def test_period_shortens_as_reactivity_approaches_beta():
    """rho が beta に近づくほど安定期は短くなる = 制御が難しくなる。"""
    pk = PointKinetics()
    periods = [pk.period(r) for r in (0.0005, 0.001, 0.002, 0.004, 0.006)]
    assert all(b < a for a, b in zip(periods, periods[1:]))


def test_critical_reactor_holds_steady_power():
    """rho = 0 なら出力は変わらない（臨界定常）。"""
    pk = PointKinetics(n0=1.0)
    pk.run(0.0, duration=5.0, dt=1e-3)
    assert math.isclose(pk.n, 1.0, rel_tol=1e-3)


def test_negative_reactivity_reduces_power():
    pk = PointKinetics(n0=1.0)
    pk.run(-0.002, duration=5.0, dt=1e-3)
    assert pk.n < 1.0


def test_small_positive_reactivity_grows_slowly():
    """遅発中性子のおかげで、小さな正の反応度では出力はゆっくりしか増えない。"""
    pk = PointKinetics(n0=1.0)
    pk.run(0.0005, duration=1.0, dt=1e-3)
    assert 1.0 < pk.n < 1.5     # 1 秒では数割しか増えない
