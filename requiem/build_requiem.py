#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bada Requiem builder
====================
手持ちの録音 (mp3 / wav ...) を素材に、坂本龍一「Libera me」や LUNA SEA「MOTHER」の
レクイエム的な "包み込む (all-round)" 音楽像へ作り換え、mp4 として書き出す。

処理の流れ
  1. 各素材を読み込み、調を推定して F minor / Ab major の一族 (Fm, Bbm, Ab, Db) に ±1 半音以内で移調
  2. フェーズボコーダ (旋律用) と Paulstretch (残響雲用) で 1.2〜5 倍に引き伸ばし、
     オクターブ/五度のハーモニー層と Haas 効果でステレオ化
  3. 六つの楽章 (Introitus / Kyrie / Dies irae / Lacrimosa / Libera me / Lux aeterna) に配置
  4. 配置済み素材の Chroma から小節ごとに和音を推定し、聖歌隊パッド・弦・オルガン・ピアノが
     その和音を追いかける (素材と伴奏がぶつからない)
  5. 鐘・ティンパニ、大聖堂リバーブ、ソフトリミッタでマスタリング
  6. ffmpeg (imageio-ffmpeg) で CQT スペクトラム映像 + 楽章タイトルを合成し H.264/AAC の mp4 に

使い方
  python3 build_requiem.py --src <録音のあるディレクトリ> --out <出力ディレクトリ>
依存: numpy scipy librosa soundfile pillow imageio-ffmpeg
"""
import argparse, glob, math, os, subprocess, sys, warnings
from fractions import Fraction

import numpy as np
import scipy.signal as sig
import soundfile as sf

warnings.filterwarnings("ignore")
SR = 44100
BPM = 56.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT
NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
RNG = np.random.default_rng(20260926)


# ----------------------------------------------------------------------------- utils
def log(*a):
    print(*a, flush=True)


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return 'ffmpeg'


def load_mono(path):
    """任意形式 → mono float32 44.1k (ffmpeg 経由)"""
    cmd = [ffmpeg_exe(), '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-']
    raw = subprocess.run(cmd, stdout=subprocess.PIPE, check=True).stdout
    y = np.frombuffer(raw, dtype=np.float32).copy()
    return y


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def sosfilt(y, kind, fc, order=2):
    sos = sig.butter(order, fc, kind, fs=SR, output='sos')
    if y.ndim == 1:
        return sig.sosfiltfilt(sos, y)
    return np.stack([sig.sosfiltfilt(sos, y[:, c]) for c in range(y.shape[1])], 1)


def normalize(y, peak=0.9):
    m = np.max(np.abs(y)) + 1e-9
    return y * (peak / m)


def env_fade(n, fi, fo):
    e = np.ones(n, dtype=np.float32)
    fi = min(fi, n); fo = min(fo, n)
    if fi > 0:
        e[:fi] = np.linspace(0, 1, fi)
    if fo > 0:
        e[n - fo:] *= np.linspace(1, 0, fo)
    return e


def to_stereo(y):
    if y.ndim == 2:
        return y
    return np.stack([y, y], 1)


def haas(y, delay_ms=17.0, width=0.6):
    """モノ → 擬似ステレオ (Haas + 逆相の軽いコム)"""
    d = int(SR * delay_ms / 1000)
    l = np.copy(y)
    r = np.zeros_like(y)
    r[d:] = y[:-d]
    return np.stack([l * (1 - 0.15 * width) + r * 0.15 * width, r * (1 - 0.15 * width) + l * 0.15 * width], 1)


# ----------------------------------------------------------------------------- stretching / pitch
def resample_ratio(y, ratio):
    """ratio 倍に音程を上げる (長さは 1/ratio に)"""
    fr = Fraction(ratio).limit_denominator(2000)
    return sig.resample_poly(y, fr.denominator, fr.numerator).astype(np.float32)


def paulstretch(y, stretch, window_s=0.28, seed=0):
    """Paulstretch (ランダム位相 STFT) — 残響雲のような引き伸ばし"""
    rng = np.random.default_rng(seed)
    ws = int(window_s * SR) // 2 * 2
    win = np.hanning(ws).astype(np.float32)
    hop_out = ws // 2
    hop_in = hop_out / stretch
    n_out = int(len(y) * stretch) + ws
    out = np.zeros(n_out, dtype=np.float32)
    ypad = np.concatenate([y, np.zeros(ws, dtype=np.float32)])
    n_frames = int((len(y) - 1) / hop_in) + 1
    for i in range(n_frames):
        ip = int(i * hop_in)
        frame = ypad[ip:ip + ws]
        if len(frame) < ws:
            break
        spec = np.fft.rfft(frame * win)
        spec = np.abs(spec) * np.exp(1j * rng.uniform(0, 2 * np.pi, len(spec)))
        f = np.fft.irfft(spec, ws).astype(np.float32) * win
        op = i * hop_out
        if op + ws > n_out:
            break
        out[op:op + ws] += f
    return out / (np.sqrt(np.mean(win ** 2)) * 2 + 1e-9)


def pv_stretch(y, stretch):
    import librosa
    return librosa.effects.time_stretch(y, rate=1.0 / stretch).astype(np.float32)


def pitch_shift(y, semis):
    import librosa
    if abs(semis) < 1e-6:
        return y
    return librosa.effects.pitch_shift(y, sr=SR, n_steps=semis).astype(np.float32)


# ----------------------------------------------------------------------------- analysis
MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MNR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def estimate_key(y):
    import librosa
    y22 = librosa.resample(y, orig_sr=SR, target_sr=22050)
    ch = librosa.feature.chroma_cqt(y=y22, sr=22050).mean(1)
    best = None
    for i in range(12):
        for mode, prof in (('maj', MAJ), ('min', MNR)):
            c = np.corrcoef(ch, np.roll(prof, i))[0, 1]
            if best is None or c > best[0]:
                best = (c, i, mode)
    return best[1], best[2], best[0]


# 目的の調の一族: F minor と関係調 Ab major、下属調 Bb minor、Db major
def transposition_for(root, mode):
    """±1 半音以内で F minor 一族 (Fm, Bbm, Cm / Ab, Db, Eb) に入る移調量"""
    targets = {'min': [5, 10, 0], 'maj': [8, 1, 3]}[mode]  # F, Bb, C / Ab, Db, Eb
    best = None
    for t in (0, -1, 1, -2, 2):
        if (root + t) % 12 in targets:
            if best is None or abs(t) < abs(best):
                best = t
    return best if best is not None else 0


# ----------------------------------------------------------------------------- synth
def make_table(f0, kind='choir', size=8192):
    """帯域制限ウェーブテーブル (倍音振幅を絶対周波数のフォルマントで重み付け)"""
    nh = int(min(80, 18000 / f0))
    h = np.arange(1, nh + 1)
    freqs = h * f0
    if kind == 'choir':       # "ah" 〜 "oh" の母音フォルマント
        amp = 1.0 / h ** 0.9
        form = (np.exp(-((freqs - 600) / 200) ** 2) * 1.0
                + np.exp(-((freqs - 1100) / 260) ** 2) * 0.55
                + np.exp(-((freqs - 2500) / 350) ** 2) * 0.22
                + 0.12)
        amp = amp * form
    elif kind == 'strings':
        amp = 1.0 / h ** 1.05
        amp *= 1.0 / (1 + (freqs / 3200) ** 2)
    elif kind == 'organ':
        amp = np.zeros(nh)
        for k, a in ((1, 1.0), (2, 0.55), (3, 0.25), (4, 0.35), (6, 0.12), (8, 0.10)):
            if k <= nh:
                amp[k - 1] = a
    else:
        amp = 1.0 / h
    ph = np.linspace(0, 2 * np.pi, size, endpoint=False)
    tbl = np.zeros(size)
    for k, a in zip(h, amp):
        tbl += a * np.sin(k * ph + (0 if kind == 'organ' else RNG.uniform(0, 2 * np.pi)))
    return (tbl / (np.max(np.abs(tbl)) + 1e-9)).astype(np.float32)


def osc(f0, n, kind, vib_hz=5.0, vib_depth=0.004, detune_cents=0.0, seed=0):
    """テーブル読み出し発振器 (ビブラート・デチューン付き)"""
    tbl = make_table(f0 * 2 ** (detune_cents / 1200), kind)
    size = len(tbl)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    f = f0 * 2 ** (detune_cents / 1200) * (1 + vib_depth * np.sin(2 * np.pi * vib_hz * t + rng.uniform(0, 6.28))
                                           * np.minimum(1, t / 1.5))
    phase = np.cumsum(f / SR) * size + rng.uniform(0, size)
    idx = phase % size
    i0 = idx.astype(np.int64)
    fr = (idx - i0).astype(np.float32)
    i1 = (i0 + 1) % size
    return tbl[i0] * (1 - fr) + tbl[i1] * fr


def adsr(n, a, d, s, r):
    a = int(a * SR); d = int(d * SR); r = int(r * SR)
    e = np.ones(n, dtype=np.float32) * s
    a = min(a, n); e[:a] = np.linspace(0, 1, a)
    if d > 0 and a + d <= n:
        e[a:a + d] = np.linspace(1, s, d)
    r = min(r, n)
    if r > 0:
        e[n - r:] *= np.linspace(1, 0, r)
    return e


def voice_note(midi, dur, kind, gain=1.0, attack=1.2, release=1.5, unison=3, spread=8.0, pan=0.0, seed=0):
    """ステレオのサステイン音 (聖歌隊 / 弦 / オルガン)"""
    n = int(dur * SR)
    f0 = midi_hz(midi)
    out = np.zeros((n, 2), dtype=np.float32)
    for u in range(unison):
        det = (u - (unison - 1) / 2) * spread if unison > 1 else 0.0
        vd = 0.0 if kind == 'organ' else (0.0035 if kind == 'choir' else 0.0045)
        s = osc(f0, n, kind, vib_hz=4.6 + 0.4 * u, vib_depth=vd, detune_cents=det, seed=seed * 7 + u)
        p = pan + (u - (unison - 1) / 2) * 0.35 / max(1, unison - 1)
        p = float(np.clip(p, -1, 1))
        out[:, 0] += s * math.cos((p + 1) * math.pi / 4)
        out[:, 1] += s * math.sin((p + 1) * math.pi / 4)
    out *= adsr(n, attack, 0.0, 1.0, release)[:, None] * (gain / unison)
    return out


def bell(midi, dur=9.0, gain=1.0):
    """鐘 (非整数倍音の減衰和音)"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = midi_hz(midi)
    ratios = [0.5, 1.0, 1.183, 1.506, 2.0, 2.514, 2.662, 3.011, 4.166, 5.433]
    amps = [0.5, 1.0, 0.6, 0.5, 0.45, 0.35, 0.3, 0.25, 0.12, 0.08]
    y = np.zeros(n, dtype=np.float32)
    for r, a in zip(ratios, amps):
        f = f0 * r
        if f > 18000:
            continue
        tau = 3.5 / (r ** 0.7)
        y += a * np.sin(2 * np.pi * f * t + RNG.uniform(0, 6.28)) * np.exp(-t / tau)
    y *= np.minimum(1, t / 0.004)
    y = normalize(y, 1.0) * gain
    return haas(y, 9.0, 0.8)


def timpani(midi=41, dur=1.6, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = midi_hz(midi)
    f = f0 * (1 + 0.6 * np.exp(-t / 0.05))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.45)
    y += 0.5 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR) * np.exp(-t / 0.22)
    noise = RNG.normal(0, 1, n) * np.exp(-t / 0.03) * 0.5
    y = sosfilt(y + noise, 'low', 900)
    y *= np.minimum(1, t / 0.002)
    return to_stereo(normalize(y, 1.0) * gain)


def piano(midi, dur=2.6, gain=1.0, pan=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = midi_hz(midi)
    y = np.zeros(n, dtype=np.float32)
    for k in range(1, 13):
        f = f0 * k * math.sqrt(1 + 0.0004 * k * k)
        if f > 16000:
            break
        y += (1.0 / k ** 1.3) * np.sin(2 * np.pi * f * t + RNG.uniform(0, 6.28)) * np.exp(-t * (0.9 + 0.35 * k))
    y *= np.minimum(1, t / 0.003)
    y = normalize(y, 1.0) * gain * np.exp(-t / 2.2)
    out = np.zeros((n, 2), dtype=np.float32)
    out[:, 0] = y * math.cos((pan + 1) * math.pi / 4)
    out[:, 1] = y * math.sin((pan + 1) * math.pi / 4)
    return out


# ----------------------------------------------------------------------------- reverb
def make_ir(seconds=6.5, rt60=5.5, seed=1):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = np.zeros((n, 2), dtype=np.float32)
    for c in range(2):
        noise = rng.normal(0, 1, n)
        # 高域ほど早く減衰する大聖堂の残響
        lo = sosfilt(noise, 'low', 1500) * np.exp(-6.91 * t / rt60)
        hi = sosfilt(noise, 'high', 1500) * np.exp(-6.91 * t / (rt60 * 0.35))
        ir[:, c] = lo + 0.5 * hi
        # 初期反射
        for d in (0.019, 0.031, 0.047, 0.071, 0.093):
            k = int(d * SR) + c * 37
            ir[k, c] += rng.uniform(0.4, 0.9)
    ir *= np.minimum(1, t / 0.005)[:, None]
    ir[0, :] = 0
    return ir / (np.sqrt(np.sum(ir ** 2, 0)).max() + 1e-9)


def reverb(x, ir, wet=0.5, dry=1.0):
    out = np.zeros((len(x) + len(ir) - 1, 2), dtype=np.float32)
    for c in range(2):
        out[:, c] = sig.oaconvolve(x[:, c], ir[:, c]).astype(np.float32)
    out *= wet
    out[:len(x)] += x * dry
    return out


# ----------------------------------------------------------------------------- chord following
CHORDS = {  # F minor 一族の三和音 (ピッチクラス)
    'Fm': [5, 8, 0], 'Bbm': [10, 1, 5], 'Cm': [0, 3, 7], 'Ab': [8, 0, 3], 'Db': [1, 5, 8],
    'Eb': [3, 7, 10], 'Gb': [6, 10, 1], 'C': [0, 4, 7], 'F': [5, 9, 0], 'Ebm': [3, 6, 10],
}


def chord_track(mix_mono, sec_start, sec_end, allowed, prev=None, hold_bars=1):
    """小節ごとに、配置済み素材の Chroma に最もよく合う和音を選ぶ (ヒステリシス付き)"""
    import librosa
    seg = mix_mono[int(sec_start * SR):int(sec_end * SR)]
    y22 = librosa.resample(seg, orig_sr=SR, target_sr=22050)
    hop = 2048
    ch = librosa.feature.chroma_cqt(y=y22, sr=22050, hop_length=hop)
    fps = 22050 / hop
    bars = []
    nbars = int(math.ceil((sec_end - sec_start) / BAR))
    for b in range(nbars):
        i0 = int(b * BAR * fps); i1 = int((b + 1) * BAR * fps)
        c = ch[:, i0:max(i0 + 1, i1)].mean(1)
        if c.sum() < 1e-6:
            bars.append(prev or allowed[0]); continue
        c = c / (np.linalg.norm(c) + 1e-9)
        scores = {}
        for name in allowed:
            tmpl = np.zeros(12); pcs = CHORDS[name]
            tmpl[pcs[0]] = 1.0; tmpl[pcs[1]] = 0.8; tmpl[pcs[2]] = 0.9
            tmpl /= np.linalg.norm(tmpl)
            scores[name] = float(c @ tmpl)
        best = max(scores, key=scores.get)
        if prev in scores and scores[best] - scores[prev] < 0.06:
            best = prev
        bars.append(best); prev = best
    return bars


def voicing(name, bass_lo=38):
    """和音名 → (バス MIDI, 聖歌隊 3 声 MIDI, 高音弦 MIDI)"""
    pcs = CHORDS[name]
    root = pcs[0]
    bass = bass_lo + ((root - bass_lo) % 12)            # 38..49 (D2..C#3)
    third = 53 + ((pcs[1] - 53) % 12)                    # 53..64
    fifth = 53 + ((pcs[2] - 53) % 12)
    top = 60 + ((root - 60) % 12)
    choir = sorted([bass + 12, third, fifth, top])
    hi = 72 + ((pcs[2] - 72) % 12)
    return bass, choir, hi


# ----------------------------------------------------------------------------- arrangement
SECTIONS = [
    # (英題, 和訳 / 典礼文, start, end)
    ("I. Introitus", "Requiem aeternam dona eis, Domine", "永遠の安息を", 0, 100),
    ("II. Kyrie", "Kyrie eleison", "主よ、憐れみたまえ", 100, 195),
    ("III. Dies irae", "Dies irae, dies illa", "怒りの日", 195, 300),
    ("IV. Lacrimosa", "Lacrimosa dies illa", "涙の日", 300, 400),
    ("V. Libera me", "Libera me, Domine, de morte aeterna", "我を解き放ちたまえ", 400, 520),
    ("VI. Lux aeterna", "Lux aeterna luceat eis", "永遠の光", 520, 612),
]
TOTAL = SECTIONS[-1][-1] + 10  # 末尾の残響ぶん


class Mix:
    def __init__(self, total):
        self.n = int(total * SR)
        self.buf = np.zeros((self.n, 2), dtype=np.float32)

    def place(self, y, start, gain=1.0, fade_in=2.0, fade_out=4.0):
        y = to_stereo(y)
        s = int(start * SR)
        m = min(len(y), self.n - s)
        if m <= 0:
            return
        e = env_fade(m, int(fade_in * SR), int(fade_out * SR))
        self.buf[s:s + m] += y[:m] * e[:, None] * gain


def prep_stem(y, semis, stretch, mode, seed=0, harmony=None, take=None, offset=0.0):
    """素材 → 移調 + 引き伸ばし + ハーモニー層 + ステレオ化 (正規化済み)"""
    if take is not None:
        y = y[int(offset * SR):int((offset + take) * SR)]
    y = y * env_fade(len(y), int(0.5 * SR), int(1.0 * SR))
    ratio = 2 ** (semis / 12)
    layers = []
    if mode == 'paul':
        base = resample_ratio(y, ratio) if semis else y
        l = paulstretch(base, stretch * ratio, seed=seed)
        r = paulstretch(base, stretch * ratio, seed=seed + 1000)
        st = np.stack([l, r], 1)
        layers.append((st, 1.0))
    else:
        base = pitch_shift(y, semis)
        st = haas(pv_stretch(base, stretch), 14.0 + seed % 7, 0.7)
        layers.append((st, 1.0))
    for hs, hg in (harmony or []):
        hr = 2 ** (hs / 12)
        hb = resample_ratio(y, ratio * hr)
        hl = paulstretch(hb, stretch * ratio * hr, seed=seed + 7 + hs)
        hr_ = paulstretch(hb, stretch * ratio * hr, seed=seed + 1007 + hs)
        hst = np.stack([hl, hr_], 1)
        if hs > 0:
            hst = sosfilt(hst, 'low', 2200)
        else:
            hg *= 0.6
        layers.append((hst, hg))
    n = max(len(l[0]) for l in layers)
    out = np.zeros((n, 2), dtype=np.float32)
    for st, g in layers:
        out[:len(st)] += normalize(st, 0.9) * g
    out = sosfilt(out, 'high', 55)
    return normalize(out, 0.9)


def build(src_dir, out_dir, video=True, quick=False):
    import librosa
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(src_dir, '*.*')))
    files = [f for f in files if f.lower().endswith(('.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'))]
    if not files:
        sys.exit('no audio files in ' + src_dir)
    log(f'{len(files)} sources')
    srcs = []
    for i, f in enumerate(files):
        y = load_mono(f)
        y = normalize(sosfilt(y, 'high', 60), 0.9)
        root, mode, conf = estimate_key(y)
        t = transposition_for(root, mode)
        srcs.append(dict(idx=i + 1, path=f, y=y, key=f'{NAMES[root]} {mode}', semis=t, dur=len(y) / SR))
        log(f'  [{i + 1:02d}] {os.path.basename(f)}  {len(y) / SR:6.1f}s  key={NAMES[root]} {mode} ({conf:.2f}) -> {t:+d}')

    def S(k):  # 1 始まりの素材番号 (足りなければ巡回)
        return srcs[(k - 1) % len(srcs)]

    mix = Mix(TOTAL)
    mix_src = Mix(TOTAL)   # 素材のみ (和音推定用)

    def put(k, start, gain, stretch, mode, take=None, offset=0.0, harmony=None, fi=3.0, fo=6.0, semis_extra=0):
        s = S(k)
        y = prep_stem(s['y'], s['semis'] + semis_extra, stretch, mode, seed=k * 13, harmony=harmony,
                      take=take, offset=offset)
        mix_src.place(y, start, gain, fi, fo)
        log(f'    stem {s["idx"]:02d} @ {start:6.1f}s  {mode:5s} x{stretch:<4}  {len(y) / SR:6.1f}s  g={gain}')

    # ---- I. Introitus (0-100): 静かな雲、鐘、素材 01 を 4 倍に
    log('I. Introitus')
    put(1, 8, 0.55, 4.0, 'paul', take=24, harmony=[(12, 0.25), (-12, 0.3)], fi=8, fo=10)
    put(12, 40, 0.45, 2.0, 'pv', take=32, offset=4, fi=6, fo=8)
    # ---- II. Kyrie (100-195): Bb minor の素材群
    log('II. Kyrie')
    put(6, 100, 0.55, 3.0, 'paul', take=32, harmony=[(7, 0.2), (-12, 0.3)], fi=6, fo=10)
    put(5, 108, 0.6, 1.5, 'pv', take=60, offset=2, fi=4, fo=8)
    put(7, 150, 0.55, 1.4, 'pv', take=34, offset=6, harmony=[(12, 0.15)], fi=4, fo=8)
    # ---- III. Dies irae (195-300): 密度と緊張
    log('III. Dies irae')
    put(3, 195, 0.45, 2.0, 'paul', take=50, harmony=[(-12, 0.35)], fi=5, fo=8)
    put(8, 200, 0.7, 1.25, 'pv', take=60, offset=8, fi=3, fo=6)
    put(13, 240, 0.7, 1.25, 'pv', take=50, offset=20, harmony=[(12, 0.15)], fi=3, fo=6)
    put(15, 262, 0.55, 1.0, 'pv', take=36, offset=18, fi=3, fo=8)
    # ---- IV. Lacrimosa (300-400): 長調の素材で光が差す
    log('IV. Lacrimosa')
    put(9, 300, 0.5, 3.0, 'paul', take=32, harmony=[(12, 0.2)], fi=6, fo=10)
    put(4, 306, 0.6, 1.3, 'pv', take=48, offset=4, fi=4, fo=6)
    put(11, 335, 0.6, 1.5, 'pv', take=44, offset=30, fi=4, fo=6)
    put(16, 356, 0.55, 1.2, 'pv', take=40, offset=6, harmony=[(-12, 0.25)], fi=4, fo=8)
    put(14, 370, 0.45, 2.0, 'paul', take=16, fi=6, fo=10)
    # ---- V. Libera me (400-520): F minor 回帰、最大の厚み
    log('V. Libera me')
    put(2, 400, 0.5, 3.0, 'paul', take=38, harmony=[(-12, 0.35), (7, 0.15)], fi=6, fo=10)
    put(12, 404, 0.7, 1.5, 'pv', take=70, offset=40, harmony=[(12, 0.2)], fi=4, fo=8)
    put(10, 450, 0.7, 1.3, 'pv', take=54, offset=30, fi=4, fo=8)
    put(1, 470, 0.55, 1.5, 'pv', take=34, offset=20, harmony=[(12, 0.2)], fi=4, fo=10)
    # ---- VI. Lux aeterna (520-612): 極端に引き伸ばした光
    log('VI. Lux aeterna')
    put(16, 520, 0.5, 5.0, 'paul', take=18, harmony=[(12, 0.3), (-12, 0.3)], fi=8, fo=14)
    put(12, 540, 0.4, 4.0, 'paul', take=17, offset=120, harmony=[(12, 0.2)], fi=8, fo=14)
    put(11, 560, 0.35, 5.0, 'paul', take=10, offset=180, fi=8, fo=14)

    mix.buf += mix_src.buf

    # ---- 和音推定 (素材に追従)
    mono = mix_src.buf.mean(1)
    allowed_by_sec = {
        'I. Introitus': ['Fm', 'Db', 'Ab', 'Cm', 'Bbm', 'C'],
        'II. Kyrie': ['Bbm', 'Gb', 'Db', 'Fm', 'Ebm', 'Ab'],
        'III. Dies irae': ['Fm', 'Bbm', 'Db', 'Cm', 'C', 'Ab', 'Eb', 'Gb'],
        'IV. Lacrimosa': ['Ab', 'Db', 'Eb', 'Fm', 'Bbm', 'Cm'],
        'V. Libera me': ['Fm', 'Bbm', 'Db', 'Ab', 'C', 'Cm', 'Eb'],
        'VI. Lux aeterna': ['Ab', 'Db', 'Fm', 'F', 'Bbm'],
    }
    prev = None
    plan = []   # (start, end, chord, section)
    for name, latin, jp, s0, s1 in SECTIONS:
        bars = chord_track(mono, s0, s1, allowed_by_sec[name], prev)
        prev = bars[-1]
        for b, c in enumerate(bars):
            b0 = s0 + b * BAR; b1 = min(s1, b0 + BAR)
            if b1 - b0 > 0.5:
                plan.append((b0, b1, c, name))
    # 終止はピカルディ (F major)
    if plan:
        b0, b1, c, name = plan[-1]
        plan[-1] = (b0, b1, 'F', name)
        plan[-2] = (plan[-2][0], plan[-2][1], 'Fm', name)
    # 和音を連結 (同じ和音が続く小節は 1 音にまとめる)
    merged = []
    for b0, b1, c, name in plan:
        if merged and merged[-1][2] == c and merged[-1][3] == name and abs(merged[-1][1] - b0) < 1e-3:
            merged[-1] = (merged[-1][0], b1, c, name)
        else:
            merged.append((b0, b1, c, name))
    with open(os.path.join(out_dir, 'chords.txt'), 'w') as fh:
        for b0, b1, c, name in merged:
            fh.write(f'{b0:7.2f} {b1:7.2f}  {c:4s}  {name}\n')
    log('chord plan:', ' '.join(f'{c}' for _, _, c, _ in merged))

    # ---- 楽章ごとの伴奏ダイナミクス
    dyn = {  # choir, strings_hi, strings_lo, organ, piano, timpani
        'I. Introitus': (0.26, 0.10, 0.12, 0.30, 0.00, 0.0),
        'II. Kyrie': (0.34, 0.16, 0.16, 0.22, 0.00, 0.0),
        'III. Dies irae': (0.40, 0.24, 0.26, 0.24, 0.00, 1.0),
        'IV. Lacrimosa': (0.30, 0.18, 0.12, 0.10, 0.28, 0.0),
        'V. Libera me': (0.42, 0.24, 0.20, 0.28, 0.16, 0.5),
        'VI. Lux aeterna': (0.30, 0.14, 0.10, 0.30, 0.18, 0.0),
    }
    log('synth: choir / strings / organ')
    for b0, b1, c, name in merged:
        g_ch, g_sh, g_sl, g_or, g_pi, g_ti = dyn[name]
        dur = b1 - b0 + 2.5
        bass, choir, hi = voicing(c)
        # 聖歌隊 (4 声)
        for k, m in enumerate(choir):
            mix.place(voice_note(m, dur, 'choir', gain=g_ch, attack=1.8, release=2.5, unison=3, spread=9,
                                 pan=(k - 1.5) * 0.4, seed=int(b0) + k), b0, 1.0, 0.0, 0.0)
        # 弦: 高音 + 低音 (チェロ/コントラバス)
        mix.place(voice_note(hi, dur, 'strings', gain=g_sh, attack=2.2, release=2.5, unison=4, spread=11,
                             pan=0.3, seed=int(b0) + 9), b0, 1.0, 0.0, 0.0)
        mix.place(voice_note(hi - 5 if (hi - 5) % 12 in CHORDS[c] else hi - 7, dur, 'strings', gain=g_sh * 0.8,
                             attack=2.4, release=2.5, unison=4, spread=11, pan=-0.3, seed=int(b0) + 10), b0, 1.0, 0.0, 0.0)
        mix.place(voice_note(bass, dur, 'strings', gain=g_sl, attack=1.5, release=2.0, unison=3, spread=6,
                             pan=-0.1, seed=int(b0) + 11), b0, 1.0, 0.0, 0.0)
        # オルガン (バス + 1 オクターブ下)
        mix.place(voice_note(bass - 12, dur, 'organ', gain=g_or * 0.45, attack=1.0, release=2.0, unison=1, pan=0.0), b0, 1.0, 0.0, 0.0)
        mix.place(voice_note(bass, dur, 'organ', gain=g_or * 0.5, attack=1.0, release=2.0, unison=1, pan=0.0), b0, 1.0, 0.0, 0.0)
        # ピアノ (アルペジオ, 8 分音符)
        if g_pi > 0:
            pcs = CHORDS[c]
            arp = [bass + 12, bass + 12 + ((pcs[1] - bass) % 12), bass + 12 + ((pcs[2] - bass) % 12), bass + 24,
                   bass + 24 + ((pcs[1] - bass) % 12), bass + 24, bass + 12 + ((pcs[2] - bass) % 12),
                   bass + 12 + ((pcs[1] - bass) % 12)]
            t = b0
            k = 0
            while t < b1 - 0.1:
                m = arp[k % len(arp)]
                vel = g_pi * (0.8 + 0.2 * math.sin(k * 0.7)) * (1.0 if k % 8 == 0 else 0.7)
                mix.place(piano(m, 2.8, vel, pan=(m - 60) / 30), t, 1.0, 0.0, 0.0)
                t += BEAT / 2; k += 1
        # ティンパニ (怒りの日のリズム: ♩ ♪♪ ♩ 休)
        if g_ti > 0:
            t = b0
            while t < b1 - 0.1:
                for off, v in ((0, 1.0), (1.0, 0.55), (1.5, 0.55), (2.0, 0.9)):
                    tt = t + off * BEAT
                    if tt < b1:
                        mix.place(timpani(bass - 12 + 12 * (bass - 12 < 33), 1.8, 0.55 * v * g_ti), tt, 1.0, 0.0, 0.0)
                t += BAR

    # ---- 鐘
    log('bells')
    bell_times = [(0.0, 65, 0.7), (BAR * 2, 53, 0.55), (BAR * 4, 65, 0.5), (BAR * 6, 53, 0.45),
                  (195, 53, 0.6), (300, 65, 0.45), (400, 65, 0.7), (400 + BAR * 2, 53, 0.5), (400 + BAR * 4, 65, 0.45),
                  (520, 65, 0.55), (520 + BAR * 4, 65, 0.4), (520 + BAR * 8, 65, 0.35), (598, 53, 0.6), (606, 65, 0.7)]
    for t, m, g in bell_times:
        mix.place(bell(m, 10.0, g), t, 1.0, 0.0, 0.0)

    # ---- 楽曲全体のダイナミクス曲線 (dB): 静かな導入 → 怒りの日 → 涙 → Libera me の頂点 → 光へ消える
    log('dynamic arc')
    arc = [(0, -9), (30, -7), (100, -6), (150, -4), (195, -1), (230, 0), (295, -1), (300, -6), (350, -5),
           (400, -3), (440, -1), (480, 0), (515, -2), (520, -6), (560, -7), (600, -9), (TOTAL, -12)]
    tt = np.arange(mix.n) / SR
    g = np.interp(tt, [a for a, _ in arc], [b for _, b in arc])
    mix.buf *= (10 ** (g / 20)).astype(np.float32)[:, None]

    # ---- リバーブ・マスタリング
    log('reverb / master')
    ir = make_ir(6.5, 5.5)
    y = reverb(mix.buf, ir, wet=0.55, dry=0.85)[:mix.n]
    y = sosfilt(y, 'high', 32)
    # ソフトリミッタ
    y = y / (np.percentile(np.abs(y), 99.95) + 1e-9) * 0.8
    y = np.tanh(y * 1.1) / math.tanh(1.1)
    y = normalize(y, 0.95)
    y *= env_fade(len(y), int(0.5 * SR), int(9 * SR))[:, None]
    wav = os.path.join(out_dir, 'requiem.wav')
    sf.write(wav, y, SR, subtype='PCM_16')
    log('wrote', wav, f'{len(y) / SR:.1f}s')

    if video:
        render_video(wav, out_dir, quick=quick)
    return wav


# ----------------------------------------------------------------------------- video
def find_font():
    for p in ('/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf',
              '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf',
              '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if os.path.exists(p):
            return p
    return None


def title_card(path, big, latin, jp, W=1280, H=720, sub=None):
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fp = find_font()
    f1 = ImageFont.truetype(fp, 64) if fp else ImageFont.load_default()
    f2 = ImageFont.truetype(fp, 30) if fp else ImageFont.load_default()
    f3 = ImageFont.truetype(fp, 34) if fp else ImageFont.load_default()

    def center(txt, font, y, fill):
        w = d.textlength(txt, font=font)
        d.text(((W - w) / 2 + 2, y + 2), txt, font=font, fill=(0, 0, 0, 160))
        d.text(((W - w) / 2, y), txt, font=font, fill=fill)

    center(big, f1, H * 0.30, (245, 236, 210, 255))
    center(latin, f2, H * 0.30 + 90, (200, 190, 160, 235))
    center(jp, f3, H * 0.30 + 140, (230, 222, 200, 245))
    if sub:
        center(sub, f2, H * 0.30 + 200, (170, 165, 150, 220))
    im.save(path)


def render_video(wav, out_dir, quick=False):
    W, H, FPS = 1280, 720, 30
    ff = ffmpeg_exe()
    dur = sf.info(wav).duration
    cards = []
    # オープニング
    p = os.path.join(out_dir, 'card_00.png')
    title_card(p, 'REQUIEM', 'Bada Requiem — for sixteen recordings', '鎮魂曲 — 十六の録音より', W, H,
               sub='after Sakamoto "Libera me" / LUNA SEA "MOTHER"')
    cards.append((p, 0.5, 9.0))
    for k, (name, latin, jp, s0, s1) in enumerate(SECTIONS):
        p = os.path.join(out_dir, f'card_{k + 1:02d}.png')
        title_card(p, name, latin, jp, W, H)
        cards.append((p, s0 + (10.0 if k == 0 else 0.0), 8.0))
    p = os.path.join(out_dir, 'card_end.png')
    title_card(p, 'Requiescant in pace', 'Bada Requiem', '安らかに', W, H)
    cards.append((p, dur - 12, 11.0))

    inputs = ['-i', wav]
    fc = []
    # 背景: CQT スペクトラム (バー + ソノグラム) を暗く滲ませる
    fc.append(f"[0:a]showcqt=s={W}x{H}:fps={FPS}:axis=0:bar_g=2.5:sono_g=4:bar_v=8:sono_v=14:count=6:"
              f"cscheme=0.75|0.55|0.25|0.35|0.35|0.75:tc=0.4:basefreq=38:endfreq=4200,"
              f"format=rgba,split[ca][cb];[cb]hflip[cbf];[ca][cbf]blend=all_mode=lighten,"
              f"gblur=sigma=1.5,lagfun=decay=0.94,"
              f"colorbalance=rs=-0.05:gs=-0.1:bs=0.12:rh=0.1:gh=0.02:bh=-0.05,"
              f"eq=brightness=-0.04:contrast=1.15:saturation=0.85,"
              f"format=rgba,fade=t=in:st=0:d=3,fade=t=out:st={dur - 6:.2f}:d=6[bg]")
    prev = '[bg]'
    for k, (p, st, d) in enumerate(cards):
        inputs += ['-loop', '1', '-t', f'{d:.2f}', '-i', p]
        idx = k + 1
        fc.append(f"[{idx}:v]format=rgba,fade=t=in:st=0:d=2:alpha=1,fade=t=out:st={d - 2.5:.2f}:d=2.5:alpha=1,"
                  f"setpts=PTS-STARTPTS+{st:.3f}/TB[c{idx}]")
        fc.append(f"{prev}[c{idx}]overlay=eof_action=pass:format=auto[o{idx}]")
        prev = f'[o{idx}]'
    fc.append(f"{prev}format=yuv420p[v]")
    out = os.path.join(out_dir, 'requiem.mp4')
    cmd = [ff, '-y', '-v', 'error', '-stats'] + inputs + [
        '-filter_complex', ';'.join(fc), '-map', '[v]', '-map', '0:a',
        '-c:v', 'libx264', '-preset', 'ultrafast' if quick else 'fast', '-crf', '21', '-r', str(FPS),
        '-c:a', 'aac', '-b:a', '224k', '-movflags', '+faststart', '-shortest',
    ]
    if quick:
        cmd += ['-t', '40']
    cmd.append(out)
    log('ffmpeg video ...')
    subprocess.run(cmd, check=True)
    log('wrote', out)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--src', required=True, help='録音 (mp3/wav/m4a ...) を置いたディレクトリ')
    ap.add_argument('--out', default='output', help='出力ディレクトリ')
    ap.add_argument('--no-video', action='store_true', help='wav のみ書き出す')
    ap.add_argument('--quick', action='store_true', help='映像を 40 秒だけ高速に書き出す (確認用)')
    a = ap.parse_args()
    build(a.src, a.out, video=not a.no_video, quick=a.quick)
