import math
from omega_gamma_agent import (
    GammaManifold, gamma, ibp_recurrence, self_check, OmegaGammaAgent,
)


def test_gamma_recurrence_identity():
    assert self_check()
    for s in (0.5, 1.5, 3.2, 7.0):
        assert math.isclose(gamma(s + 1), s * gamma(s), rel_tol=1e-9)


def test_ibp_recurrence_factor():
    assert ibp_recurrence(4.0) == 4.0


def test_manifold_step_grows_weight():
    m = GammaManifold()
    st = m.register(2.0, "x")
    m.step()
    # Γ(3)=2·Γ(2) → log_weight = log 2
    assert math.isclose(m.states[0].log_weight, math.log(2.0), rel_tol=1e-9)
    assert m.states[0].s == 3.0


def test_softmax_normalized():
    m = GammaManifold()
    m.register(1.0); m.register(2.0); m.register(0.5)
    m.step()
    dist = m.softmax()
    assert math.isclose(sum(dist), 1.0, rel_tol=1e-9)
    assert all(0.0 <= p <= 1.0 for p in dist)


def test_agent_answers_known_topic():
    a = OmegaGammaAgent()
    ans = a.ask("ガンマ関数の部分積分について教えて")
    assert "Γ(s+1)=s·Γ(s)" in ans


def test_agent_honest_about_agi():
    a = OmegaGammaAgent()
    ans = a.ask("これはagiなの chatgpt なの")
    assert "AGI" in ans


def test_agent_unknown_question():
    a = OmegaGammaAgent()
    ans = a.ask("zzzzz qqqqq")
    assert "見つかりません" in ans
