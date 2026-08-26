import math
from omega_morphofield import (
    MorphogenField, FieldConfig, TumorModel, TumorConfig,
    policy_none, policy_continuous, make_adaptive_policy,
)


# ---- 形態形成場 ----------------------------------------------------------- #
def test_uniform_state_stays_uniform():
    """種を置かなければ一様状態は崩れない（自発的なノイズを持たない）。"""
    f = MorphogenField(FieldConfig(n=16))
    f.run(200)
    assert f.total_activator() == 0.0
    assert f.count_spots() == 0


def test_concentrations_stay_bounded():
    f = MorphogenField(FieldConfig(n=24))
    f.seed_spot(radius=3)
    f.run(400)
    assert all(0.0 <= x <= 1.0 for x in f.u)
    assert all(0.0 <= x <= 1.0 for x in f.v)


def test_seed_divides_into_multiple_cells():
    """分裂領域では1つの種が複数の細胞に分岐する。"""
    f = MorphogenField(FieldConfig(n=48))
    f.seed_spot(radius=3)
    assert f.count_spots() == 1
    f.run(1500)
    assert f.count_spots() > 1


def test_field_drifts_pattern_along_its_direction():
    """外部場をかけると、その向きにだけ重心が動く。"""
    n, steps = 40, 300
    still = MorphogenField(FieldConfig(n=n, Ex=0.0))
    still.seed_spot(radius=3); still.run(steps)
    sx, sy = still.centroid()

    driven = MorphogenField(FieldConfig(n=n, Ex=0.04))
    driven.seed_spot(radius=3); driven.run(steps)
    dx, dy = driven.centroid()

    assert abs(dx - sx) > 1.0          # 場の向き(x)には動く
    assert abs(dy - sy) < 0.5          # 直交方向(y)には動かない


def test_zero_field_keeps_centroid_centered():
    n = 40
    f = MorphogenField(FieldConfig(n=n, Ex=0.0, Ey=0.0))
    f.seed_spot(radius=3)
    f.run(300)
    cx, cy = f.centroid()
    assert abs(cx - n / 2) < 1.0 and abs(cy - n / 2) < 1.0


def test_render_shape():
    f = MorphogenField(FieldConfig(n=12))
    f.seed_spot(radius=2)
    rows = f.render().split("\n")
    assert len(rows) == 12 and all(len(r) == 12 for r in rows)


# ---- 腫瘍動態 -------------------------------------------------------------- #
def test_untreated_tumor_reaches_carrying_capacity():
    m = TumorModel(TumorConfig(duration=400.0))
    m.run(policy_none)
    assert m.total > 0.95 * m.cfg.K


def test_populations_stay_nonnegative_and_finite():
    m = TumorModel(TumorConfig(duration=400.0))
    m.run(policy_continuous)
    assert m.S >= 0.0 and m.R >= 0.0
    assert math.isfinite(m.S) and math.isfinite(m.R)


def test_continuous_treatment_selects_for_resistance():
    """常時最大強度は感受性クローンを消し、耐性クローンだけを残す。"""
    m = TumorModel()
    m.run(policy_continuous)
    s = m.summary()
    assert s["resistant_fraction"] > 0.95
    assert s["final_S"] < s["final_R"]


def test_adaptive_delays_progression_versus_continuous():
    """適応的方針は、常時最大強度より進行を遅らせる（適応療法の帰結）。"""
    cont = TumorModel(); cont.run(policy_continuous)
    adapt = TumorModel(); adapt.run(make_adaptive_policy())
    assert (adapt.summary()["time_to_progression"]
            > cont.summary()["time_to_progression"])


def test_adaptive_stalls_with_less_treatment():
    """しかも治療している時間は短い。"""
    adapt = TumorModel(); adapt.run(make_adaptive_policy())
    s = adapt.summary()
    assert s["stalled"] == 1.0
    assert s["treatment_fraction"] < 0.5


def test_epsilon_is_clamped_to_unit_interval():
    """治療強度は 0〜1 に制限される（用量ではなく無次元パラメータ）。"""
    m = TumorModel(TumorConfig(duration=10.0))
    m.run(lambda _: 5.0)
    assert all(f.epsilon <= 1.0 for f in m.log)
    m2 = TumorModel(TumorConfig(duration=10.0))
    m2.run(lambda _: -3.0)
    assert all(f.epsilon >= 0.0 for f in m2.log)


def test_reproducible():
    a = TumorModel(); a.run(make_adaptive_policy())
    b = TumorModel(); b.run(make_adaptive_policy())
    assert a.summary() == b.summary()
