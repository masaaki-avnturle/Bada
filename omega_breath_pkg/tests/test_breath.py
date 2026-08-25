import io
import math
from omega_breath import PATTERNS, get, RSASimulator, HRVConfig, resonance_sweep, run_guide, render_bar
from omega_breath.patterns import BreathPattern


def test_pattern_cycle_and_rate():
    p = get("478")
    assert math.isclose(p.cycle, 19.0)
    assert math.isclose(p.breaths_per_minute, 60.0 / 19.0)
    assert math.isclose(get("coherent").breaths_per_minute, 6.0)


def test_phase_sequence():
    p = get("box")     # 4/4/4/4
    assert p.phase_at(0.0)[0] == "吸う"
    assert p.phase_at(5.0)[0] == "止める"
    assert p.phase_at(9.0)[0] == "吐く"
    assert p.phase_at(13.0)[0] == "止める(空)"
    assert p.phase_at(16.5)[0] == "吸う"      # 次の周期へ折り返す


def test_lung_volume_bounds_and_endpoints():
    p = get("slow")
    for i in range(200):
        v = p.lung_volume(i * 0.137)
        assert 0.0 <= v <= 1.0
    assert math.isclose(p.lung_volume(0.0), 0.0, abs_tol=1e-9)
    assert math.isclose(p.lung_volume(p.inhale - 1e-9), 1.0, abs_tol=1e-6)


def test_resonance_peak_near_six_per_minute():
    """圧受容器反射の共鳴は毎分6回付近に出る（実在の生理学と一致）。"""
    peak_bpm, _ = max(resonance_sweep(), key=lambda br: br[1])
    assert 5.0 <= peak_bpm <= 7.0


def test_coherent_beats_fast_breathing():
    sim = RSASimulator()
    coherent = sim.metrics(get("coherent"))
    fast = sim.metrics(BreathPattern("速い", 1.5, 0.0, 1.5, 0.0))   # 20回/分
    assert coherent["rsa_amplitude"] > fast["rsa_amplitude"]


def test_hrv_values_are_physiologically_plausible():
    m = RSASimulator().metrics(get("coherent"))
    assert 3.0 < m["rsa_amplitude"] < 25.0        # bpm
    assert 10.0 < m["sdnn_ms"] < 200.0            # ms
    assert 50.0 < m["mean_hr"] < 90.0             # bpm


def test_simulate_drops_warmup_transient():
    cfg = HRVConfig(duration=120.0, warmup=60.0)
    out = RSASimulator(cfg).simulate(get("slow"))
    assert out["t"][0] >= 60.0
    assert all(math.isfinite(h) for h in out["hr"])


def test_render_bar():
    assert render_bar(0.0, 10) == "·" * 10
    assert render_bar(1.0, 10) == "█" * 10
    assert len(render_bar(0.37, 10)) == 10


def test_guide_runs_without_sleeping():
    """sleep を差し替えて即時実行できる（テスト可能性の確認）。"""
    buf = io.StringIO()
    secs = run_guide(get("slow"), cycles=1, stream=buf, sleep=lambda _: None, fps=4.0)
    text = buf.getvalue()
    assert secs == 10
    assert "吸う" in text and "吐く" in text
    assert "おつかれさまでした" in text
