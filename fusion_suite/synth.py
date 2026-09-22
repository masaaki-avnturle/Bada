"""
synth.py — 依存最小(numpy / scipy)の加算合成シンセ + 簡易シーケンサ + 畳み込みリバーブ。

楽器: piano / strings / pad / organ / choir / bell / drone / harp
すべて mono で生成し、Mixer が pan して stereo バスへ置く。
"""
import numpy as np
from scipy import signal

SR = 44100


def midi_to_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def _t(n):
    return np.arange(n, dtype=np.float32) / SR


def adsr(n, a, d, s, r, hold):
    """hold = 鍵盤を押している秒数。全長 n サンプル(hold + release)。"""
    env = np.zeros(n, dtype=np.float32)
    ia, id_, ih = int(a * SR), int(d * SR), int(hold * SR)
    ih = max(ih, ia + id_)
    ir = n - ih
    env[:ia] = np.linspace(0, 1, ia, endpoint=False)
    env[ia:ia + id_] = np.linspace(1, s, id_, endpoint=False)
    env[ia + id_:ih] = s
    if ir > 0:
        env[ih:] = s * np.exp(-np.linspace(0, 6, ir) * (1.0 / max(r, 1e-3)) * 0.5)
    return env


def _onepole_lp(x, cutoff):
    b, a = signal.butter(2, min(cutoff, SR * 0.45) / (SR / 2), btype="low")
    return signal.lfilter(b, a, x).astype(np.float32)


# ---------------------------------------------------------------- instruments
def piano(f, hold, vel):
    """倍音の減衰速度を周波数・倍音次数に依存させた簡易ピアノ。"""
    dur = hold + 1.2
    n = int(dur * SR)
    t = _t(n)
    out = np.zeros(n, dtype=np.float32)
    B = 0.0003
    bright = 0.6 + 0.6 * vel
    for k in range(1, 9):
        fk = f * k * np.sqrt(1 + B * k * k)
        if fk > SR * 0.45:
            break
        amp = (1.0 / k) ** (1.6 - 0.5 * bright)
        decay = 0.9 + 0.35 * k + f / 900.0
        env = np.exp(-t * decay)
        out += amp * env * np.sin(2 * np.pi * fk * t + 0.3 * k)
    # 鍵盤を離した後の減衰
    ih = int(hold * SR)
    if ih < n:
        out[ih:] *= np.exp(-np.linspace(0, 8, n - ih))
    # アタック
    ia = int(0.004 * SR)
    out[:ia] *= np.linspace(0, 1, ia)
    # ハンマーノイズ
    nz = np.random.default_rng(int(f)).normal(0, 1, int(0.012 * SR)).astype(np.float32)
    nz *= np.exp(-np.linspace(0, 6, len(nz)))
    out[: len(nz)] += 0.03 * nz
    return out * vel * 0.55


def harp(f, hold, vel):
    dur = hold + 2.0
    n = int(dur * SR)
    t = _t(n)
    out = np.zeros(n, dtype=np.float32)
    for k in range(1, 14):
        fk = f * k
        if fk > SR * 0.45:
            break
        out += (1.0 / k) ** 1.2 * np.exp(-t * (1.2 + 0.6 * k)) * np.sin(2 * np.pi * fk * t)
    ia = int(0.003 * SR)
    out[:ia] *= np.linspace(0, 1, ia)
    return out * vel * 0.5


def _saw_stack(f, n, detunes, harmonics, vib_hz=5.0, vib_depth=0.004, roll=1.0):
    t = _t(n)
    vib = 1 + vib_depth * np.sin(2 * np.pi * vib_hz * t + np.random.rand() * 6) * np.minimum(1, t / 1.5)
    out = np.zeros(n, dtype=np.float32)
    for d in detunes:
        ph = np.cumsum(2 * np.pi * f * d * vib / SR).astype(np.float32)
        for k in range(1, harmonics + 1):
            if f * k * d > SR * 0.45:
                break
            out += (1.0 / k) ** roll * np.sin(k * ph)
    return out / len(detunes)


def strings(f, hold, vel):
    rel = 0.9
    n = int((hold + rel) * SR)
    src = _saw_stack(f, n, [0.997, 1.0, 1.004], 24, vib_hz=5.2, vib_depth=0.005, roll=1.1)
    src = _onepole_lp(src, 900 + 2500 * vel + f)
    env = adsr(n, 0.35, 0.3, 0.85, rel, hold)
    return src * env * vel * 0.28


def pad(f, hold, vel):
    rel = 2.5
    n = int((hold + rel) * SR)
    src = _saw_stack(f, n, [0.994, 1.0, 1.006], 16, vib_hz=0.3, vib_depth=0.003, roll=1.4)
    src = _onepole_lp(src, 500 + 1200 * vel)
    env = adsr(n, 1.8, 1.0, 0.9, rel, hold)
    return src * env * vel * 0.26


def organ(f, hold, vel):
    rel = 0.15
    n = int((hold + rel) * SR)
    t = _t(n)
    out = np.zeros(n, dtype=np.float32)
    for mult, amp in [(0.5, 0.35), (1, 1.0), (2, 0.55), (3, 0.25), (4, 0.3), (6, 0.12), (8, 0.15)]:
        if f * mult > SR * 0.45:
            break
        out += amp * np.sin(2 * np.pi * f * mult * t)
    trem = 1 + 0.03 * np.sin(2 * np.pi * 5.5 * t)
    env = adsr(n, 0.03, 0.05, 1.0, rel, hold)
    return out * trem * env * vel * 0.13


_FORMANTS = {  # 母音 "ah" -> "oh" の中間
    "ah": [(650, 1.0, 90), (1100, 0.45, 110), (2600, 0.18, 170)],
    "oh": [(450, 1.0, 80), (800, 0.4, 90), (2500, 0.12, 160)],
}


def choir(f, hold, vel, vowel="ah"):
    rel = 1.2
    n = int((hold + rel) * SR)
    src = _saw_stack(f, n, [0.995, 1.0, 1.005], 40, vib_hz=5.6, vib_depth=0.007, roll=1.0)
    out = np.zeros(n, dtype=np.float32)
    for fc, g, bw in _FORMANTS[vowel]:
        b, a = signal.butter(2, [max(fc - bw, 40) / (SR / 2), min(fc + bw, SR * 0.45) / (SR / 2)], btype="band")
        out += g * signal.lfilter(b, a, src).astype(np.float32)
    # 息のノイズ
    nz = np.random.default_rng(int(f * 7)).normal(0, 1, n).astype(np.float32)
    nz = _onepole_lp(nz, 3000) * 0.015
    env = adsr(n, 0.6, 0.4, 0.9, rel, hold)
    return (out * 1.6 + nz) * env * vel * 0.9


def bell(f, hold, vel):
    dur = max(hold, 0.5) + 3.5
    n = int(dur * SR)
    t = _t(n)
    out = np.zeros(n, dtype=np.float32)
    for ratio, amp, dec in [(1.0, 1.0, 0.9), (2.0, 0.55, 1.3), (2.4, 0.35, 1.6), (3.0, 0.25, 2.0), (4.5, 0.12, 2.6), (5.33, 0.08, 3.0)]:
        fk = f * ratio
        if fk > SR * 0.45:
            break
        out += amp * np.exp(-t * dec) * np.sin(2 * np.pi * fk * t)
    ia = int(0.002 * SR)
    out[:ia] *= np.linspace(0, 1, ia)
    return out * vel * 0.3


def drone(f, hold, vel):
    rel = 3.0
    n = int((hold + rel) * SR)
    t = _t(n)
    out = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2 * t + 0.5) + 0.12 * np.sin(2 * np.pi * f * 3 * t)
    out += 0.2 * np.sin(2 * np.pi * f * 1.002 * t)
    slow = 1 + 0.08 * np.sin(2 * np.pi * 0.11 * t)
    env = adsr(n, 3.0, 1.0, 1.0, rel, hold)
    return out.astype(np.float32) * slow * env * vel * 0.22


def flute(f, hold, vel):
    """息のノイズを含む柔らかい笛。"""
    rel = 0.35
    n = int((hold + rel) * SR)
    t = _t(n)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.0 * t) * np.minimum(1, t / 0.8)
    ph = np.cumsum(2 * np.pi * f * vib / SR).astype(np.float32)
    out = np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)
    nz = np.random.default_rng(int(f * 3)).normal(0, 1, n).astype(np.float32)
    b, a = signal.butter(2, [min(f * 0.9, SR * 0.4) / (SR / 2), min(f * 1.1 + 200, SR * 0.45) / (SR / 2)], btype="band")
    out += 0.12 * signal.lfilter(b, a, nz)
    env = adsr(n, 0.12, 0.2, 0.85, rel, hold)
    return out.astype(np.float32) * env * vel * 0.3


def horn(f, hold, vel):
    """ホルン/金管: ローパスした鋸歯を丸いアタックで。"""
    rel = 0.5
    n = int((hold + rel) * SR)
    src = _saw_stack(f, n, [0.999, 1.0, 1.001], 18, vib_hz=4.5, vib_depth=0.003, roll=1.3)
    src = _onepole_lp(src, 600 + 1800 * vel)
    env = adsr(n, 0.15, 0.25, 0.85, rel, hold)
    return src * env * vel * 0.32


def timpani(f, hold, vel):
    """ティンパニ: ピッチが僅かに落ちる膜の音 + 打撃ノイズ。"""
    dur = max(hold, 0.3) + 2.5
    n = int(dur * SR)
    t = _t(n)
    sweep = f * (1 + 0.08 * np.exp(-t * 12))
    ph = np.cumsum(2 * np.pi * sweep / SR).astype(np.float32)
    out = np.sin(ph) * np.exp(-t * 2.2) + 0.4 * np.sin(1.5 * ph) * np.exp(-t * 4.0) + 0.2 * np.sin(2.0 * ph) * np.exp(-t * 6.0)
    nz = np.random.default_rng(int(f * 11)).normal(0, 1, n).astype(np.float32)
    nz = _onepole_lp(nz, 900) * np.exp(-t * 30)
    out = out + 0.5 * nz
    ia = int(0.003 * SR)
    out[:ia] *= np.linspace(0, 1, ia)
    return out.astype(np.float32) * vel * 0.6


INSTRUMENTS = {
    "piano": piano, "harp": harp, "strings": strings, "pad": pad,
    "organ": organ, "choir": choir, "bell": bell, "drone": drone,
    "flute": flute, "horn": horn, "timpani": timpani,
}
# 楽器ごとのリバーブ送り量
SEND = {"piano": 0.35, "harp": 0.4, "strings": 0.5, "pad": 0.6, "organ": 0.45,
        "choir": 0.65, "bell": 0.6, "drone": 0.25,
        "flute": 0.5, "horn": 0.5, "timpani": 0.4}


# ---------------------------------------------------------------- reverb
def make_ir(seconds=3.2, decay=1.1, seed=7):
    n = int(seconds * SR)
    rng = np.random.default_rng(seed)
    t = _t(n)
    ir = np.zeros((n, 2), dtype=np.float32)
    for ch in range(2):
        nz = rng.normal(0, 1, n).astype(np.float32)
        env = np.exp(-t / decay)
        # 高域ほど早く減衰させる(時間変化ローパスの近似)
        nz = _onepole_lp(nz, 6000) * 0.6 + _onepole_lp(nz, 1500) * 0.4
        ir[:, ch] = nz * env
    # 初期反射
    for d, g in [(0.011, 0.5), (0.023, 0.35), (0.037, 0.25), (0.052, 0.18)]:
        i = int(d * SR)
        ir[i, 0] += g
        ir[i + 7, 1] += g
    ir /= np.abs(ir).sum(axis=0).max() / 12
    return ir


def reverb(bus, ir):
    out = np.zeros_like(bus)
    for ch in range(2):
        out[:, ch] = signal.fftconvolve(bus[:, ch], ir[:, ch])[: len(bus)]
    return out


# ---------------------------------------------------------------- mixer
class Mixer:
    def __init__(self, total_seconds):
        n = int(total_seconds * SR)
        self.dry = np.zeros((n, 2), dtype=np.float32)
        self.send = np.zeros((n, 2), dtype=np.float32)
        self.n = n

    def place(self, buf, start_sec, pan=0.0, gain=1.0, send=0.0):
        i = int(start_sec * SR)
        if i >= self.n:
            return
        buf = buf[: self.n - i]
        l = np.cos((pan + 1) * np.pi / 4)
        r = np.sin((pan + 1) * np.pi / 4)
        seg = self.dry[i:i + len(buf)]
        seg[:, 0] += buf * l * gain
        seg[:, 1] += buf * r * gain
        if send > 0:
            seg = self.send[i:i + len(buf)]
            seg[:, 0] += buf * l * gain * send
            seg[:, 1] += buf * r * gain * send

    def note(self, inst, start_sec, midi, hold_sec, vel=0.7, pan=0.0, gain=1.0, **kw):
        buf = INSTRUMENTS[inst](midi_to_hz(midi), hold_sec, vel, **kw)
        self.place(buf, start_sec, pan, gain, SEND[inst])

    def stereo(self, buf, start_sec, gain=1.0, send=0.0):
        i = int(start_sec * SR)
        buf = buf[: self.n - i]
        self.dry[i:i + len(buf)] += buf * gain
        if send > 0:
            self.send[i:i + len(buf)] += buf * gain * send

    def render(self, ir, wet=0.9):
        out = self.dry + reverb(self.send, ir) * wet
        return out


def compress(x, threshold_db=-20.0, ratio=2.5, attack=0.02, release=0.4):
    """バス・コンプレッサ(RMS 検出、ソフトニー無し)。独奏ピアノの静かな楽句を持ち上げる。"""
    mono = np.abs(x).max(axis=1)
    env = np.zeros_like(mono)
    a_c = np.exp(-1.0 / (attack * SR))
    r_c = np.exp(-1.0 / (release * SR))
    # 区間ごとの最大値で近似してから平滑化(高速化)
    blk = 256
    n = len(mono) // blk
    peaks = mono[: n * blk].reshape(n, blk).max(axis=1)
    e = 0.0
    out = np.zeros(n, dtype=np.float32)
    for i in range(n):
        p = peaks[i]
        c = a_c ** blk if p > e else r_c ** blk
        e = c * e + (1 - c) * p
        out[i] = e
    env = np.repeat(out, blk)
    env = np.concatenate([env, np.full(len(mono) - len(env), env[-1] if len(env) else 0)])
    thr = 10 ** (threshold_db / 20)
    gain = np.ones_like(env)
    over = env > thr
    gain[over] = (thr * (env[over] / thr) ** (1.0 / ratio)) / env[over]
    return x * gain[:, None]


def soft_limit(x, ceiling=0.95):
    peak = np.abs(x).max()
    if peak > ceiling:
        x = x * (ceiling / peak)
    return np.tanh(x * 1.1) / np.tanh(1.1)


def write_wav(path, x):
    from scipy.io import wavfile
    wavfile.write(path, SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))
