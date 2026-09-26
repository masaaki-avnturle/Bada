#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_requiem.py — 提出された録音 (MP3 / AAC / WAV ...) から「レクイエム」を生成し、MP4 動画として出力する。

  python3 requiem/make_requiem.py a.mp3 b.mp3 c.mp3 d.mp3 -o requiem/requiem.mp4

仕組み (依存: numpy, scipy, ffmpeg — ffmpeg は PATH か imageio-ffmpeg の同梱バイナリを使う)
  1. ffmpeg で全ファイルをモノラル 44.1 kHz の float に復号
  2. 解析 — Krumhansl 調性プロファイルで各曲の調を推定し、レクイエムの調 (ヘ短調 / 変イ長調) へ移調量を決める。
     1 秒刻みの音量・クロマ (12 音の分布) から「よく鳴っていて調性のはっきりした区間」「静かな区間」を選び出す。
  3. 変換 — フェーズボコーダによるタイムストレッチ、ピッチシフト、合成インパルス応答による畳み込みリバーブ、
     グラニュラー・フリーズ (曲の一瞬を引き延ばして持続音 = 「合唱」に)、逆再生リバーブ、ゲート (ディエス・イレ)、
     加算合成のドローン (オルガン)、非整数次倍音の鐘、サブベースの鼓動。
  4. 構成 — レクイエム典礼文の 5 楽章 (Introitus / Kyrie / Dies irae / Lacrimosa / Lux aeterna) に沿って
     タイムラインへ配置。Lacrimosa の低音は「嘆きのテトラコルド」 F–Eb–Db–C を下降し、
     Lux aeterna の最後はピカルディの三度 (F minor → F major) で閉じる。
  5. ffmpeg で音声を AAC、映像を libx264 (スペクトル可視化 + 楽章タイトル) に符号化し MP4 を書き出す。

乱数は seed 固定で、同じ入力からは同じ曲が生成される。
"""
import argparse
import math
import os
import shutil
import subprocess
import sys
from fractions import Fraction

import numpy as np
import scipy.signal as sg
from scipy.io import wavfile

SR = 44100
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
# Krumhansl–Kessler key profiles
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
TONIC = 5  # F  (F minor = relative of Ab major)


# ----------------------------------------------------------------------------- ffmpeg
def ffmpeg_exe():
    p = shutil.which('ffmpeg')
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        sys.exit('ffmpeg が見つかりません。ffmpeg をインストールするか `pip install imageio-ffmpeg` してください。')


def decode(path, sr=SR):
    cmd = [ffmpeg_exe(), '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(sr), '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    return x - np.mean(x)


def ffmpeg_has_filter(name):
    out = subprocess.run([ffmpeg_exe(), '-hide_banner', '-filters'], capture_output=True, text=True).stdout
    return any(line.split()[1:2] == [name] for line in out.splitlines() if line.strip())


# ----------------------------------------------------------------------------- utilities
def sec(t):
    return int(round(t * SR))


def db(x):
    return 10 ** (x / 20)


def note_hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def fade(x, fin=0.0, fout=0.0):
    x = x.copy()
    n = len(x)
    a = min(sec(fin), n)
    if a > 0:
        ramp = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
        x[:a] *= ramp[:, None] if x.ndim == 2 else ramp
    b = min(sec(fout), n)
    if b > 0:
        ramp = np.cos(np.linspace(0, np.pi / 2, b)) ** 2
        x[n - b:] *= ramp[:, None] if x.ndim == 2 else ramp
    return x


def butter(x, hz, kind, order=4):
    sos = sg.butter(order, hz, kind, fs=SR, output='sos')
    return sg.sosfiltfilt(sos, x, axis=0)


def normalize(x, peak_db=-1.0):
    m = np.max(np.abs(x)) + 1e-12
    return x * db(peak_db) / m


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def set_rms(x, target_db):
    return x * db(target_db - rms_db(x))


def to_stereo(x, width=0.0, seed=0):
    """mono -> stereo。width>0 で左右に微小な遅延差 (Haas) を付けて広げる。"""
    if x.ndim == 2:
        return x
    if width <= 0:
        return np.stack([x, x], axis=1)
    d = int(width * 0.012 * SR)
    l = np.concatenate([x, np.zeros(d)])
    r = np.concatenate([np.zeros(d), x])
    return np.stack([l, r], axis=1)


def pan(x, p):
    """x: stereo。p ∈ [-1, 1] 定パワーパン。"""
    th = (p + 1) * np.pi / 4
    return x * np.array([np.cos(th), np.sin(th)]) * math.sqrt(2)


# ----------------------------------------------------------------------------- analysis
def frame_features(x, hop_s=1.0):
    """1 秒ごとの (rms_dB, chroma[12], active) を返す。"""
    hop = sec(hop_s)
    n = len(x) // hop
    if n < 2:
        n = 1
        x = np.concatenate([x, np.zeros(hop * 2 - len(x))])
    frames = x[:n * hop].reshape(n, hop)
    rms = 20 * np.log10(np.sqrt(np.mean(frames ** 2, axis=1)) + 1e-9)
    win = sg.get_window('hann', 4096)
    freqs = np.fft.rfftfreq(4096, 1 / SR)
    band = (freqs > 60) & (freqs < 2500)
    pcs = (np.round(12 * np.log2(np.maximum(freqs, 1) / 440)).astype(int)) % 12
    chroma = np.zeros((n, 12))
    for i in range(n):
        seg = frames[i]
        starts = range(0, max(1, hop - 4096), 2048)
        spec = np.zeros(len(freqs))
        for s in starts:
            piece = seg[s:s + 4096]
            if len(piece) < 4096:
                piece = np.concatenate([piece, np.zeros(4096 - len(piece))])
            spec += np.abs(np.fft.rfft(piece * win))
        for pc in range(12):
            chroma[i, pc] = spec[band & (pcs == pc)].sum()
        chroma[i] /= chroma[i].sum() + 1e-12
    peak = rms.max()
    active = rms > peak - 35
    return rms, chroma, active


def tonalness(chroma):
    """クロマ分布のエントロピーから調性の明瞭度 (0..1) を得る。"""
    c = chroma / (chroma.sum(axis=-1, keepdims=True) + 1e-12)
    h = -(c * np.log(c + 1e-12)).sum(axis=-1)
    return 1 - h / np.log(12)


def detect_key(chroma_mean):
    best = None
    for k in range(12):
        for name, prof in (('maj', MAJOR_PROFILE), ('min', MINOR_PROFILE)):
            c = np.corrcoef(np.roll(prof, k), chroma_mean)[0, 1]
            if best is None or c > best[0]:
                best = (c, k, name)
    return best


def shift_to_requiem_key(chroma_mean):
    """ヘ短調 / 変イ長調に最も近づく移調量 (半音, -6..+6) を選ぶ。"""
    f_minor = np.roll(MINOR_PROFILE, TONIC)
    ab_major = np.roll(MAJOR_PROFILE, (TONIC + 3) % 12)
    best = (-9, 0)
    for s in range(-6, 7):
        rolled = np.roll(chroma_mean, s)
        score = max(np.corrcoef(f_minor, rolled)[0, 1], np.corrcoef(ab_major, rolled)[0, 1]) - 0.03 * abs(s)
        if score > best[0]:
            best = (score, s)
    return best[1]


class Source:
    def __init__(self, path, idx):
        self.path = path
        self.idx = idx
        self.x = decode(path)
        self.dur = len(self.x) / SR
        self.rms, self.chroma, self.active = frame_features(self.x)
        self.tonal = tonalness(self.chroma)
        weights = np.where(self.active, 1.0, 0.0)
        cm = (self.chroma * weights[:, None]).sum(0) / (weights.sum() + 1e-9)
        self.key = detect_key(cm)
        self.shift = shift_to_requiem_key(cm)
        self.loud = float(np.median(self.rms[self.active])) if self.active.any() else float(self.rms.mean())
        self.used = []
        # 音楽的な内容があるか (8 秒の無音に近い録音などは「風」として扱う)
        self.is_texture = self.dur < 20 or self.loud < -40

    def describe(self):
        c, k, m = self.key
        return (f"[{self.idx}] {os.path.basename(self.path)}  {self.dur:6.1f}s  key={NOTE_NAMES[k]}{m} (r={c:.2f})"
                f"  shift={self.shift:+d}  loud={self.loud:.1f}dB  {'texture' if self.is_texture else 'music'}")

    def pick(self, dur_s, want='loud', rank=0):
        """dur_s 秒の区間を選ぶ。want: 'loud' (よく鳴る) / 'soft' (静かだが鳴っている) / 'tonal'。"""
        n = len(self.rms)
        w = max(1, int(round(dur_s)))
        if w >= n:
            return 0.0
        cands = []
        lo, hi = np.percentile(self.rms[self.active], [5, 95]) if self.active.any() else (self.rms.min(), self.rms.max())
        for s in range(0, n - w, 1):
            act = self.active[s:s + w].mean()
            if act < 0.6:
                continue
            loud = np.clip((self.rms[s:s + w].mean() - lo) / (hi - lo + 1e-9), 0, 1)
            ton = self.tonal[s:s + w].mean()
            if want == 'loud':
                score = 0.6 * loud + 0.4 * ton
            elif want == 'soft':
                score = 0.6 * (1 - loud) + 0.4 * ton + 0.3 * act
            else:
                score = ton + 0.2 * loud
            # 既に使った区間との重なりを避ける
            overlap = sum(max(0, min(s + w, b) - max(s, a)) for a, b in self.used) / w
            score -= 1.5 * overlap
            cands.append((score, s))
        if not cands:
            return 0.0
        cands.sort(key=lambda c: -c[0])
        start = cands[min(rank, len(cands) - 1)][1]
        self.used.append((start, start + w))
        return float(start)

    def cut(self, start_s, dur_s):
        a = sec(start_s)
        b = min(len(self.x), a + sec(dur_s))
        seg = self.x[a:b]
        if len(seg) < sec(dur_s):
            seg = np.concatenate([seg, np.zeros(sec(dur_s) - len(seg))])
        return seg

    def take(self, dur_s, want='loud', rank=0, semitones=None):
        seg = self.cut(self.pick(dur_s, want, rank), dur_s)
        st = self.shift if semitones is None else semitones
        if st:
            seg = pitch_shift(seg, st)
        return seg


# ----------------------------------------------------------------------------- DSP: phase vocoder
def stretch(x, rate, n_fft=2048, hop=512):
    """フェーズボコーダ。rate>1 で遅く (長く) なる。"""
    if abs(rate - 1) < 1e-3 or len(x) < n_fft * 2:
        return x.copy()
    win = sg.get_window('hann', n_fft)
    padded = np.concatenate([np.zeros(n_fft // 2), x, np.zeros(n_fft)])
    n_in = 1 + (len(padded) - n_fft) // hop
    frames = np.lib.stride_tricks.sliding_window_view(padded, n_fft)[::hop][:n_in]
    X = np.fft.rfft(frames * win, axis=1)
    mag = np.abs(X).astype(np.float32)
    ph = np.angle(X).astype(np.float32)
    del X
    omega = (2 * np.pi * hop * np.arange(n_fft // 2 + 1) / n_fft).astype(np.float32)
    n_out = int((n_in - 2) * rate)
    out = np.zeros(n_out * hop + n_fft)
    phase = ph[0].astype(np.float64).copy()
    block = 1024
    for b0 in range(0, n_out, block):
        idx = np.arange(b0, min(n_out, b0 + block))
        pos = idx / rate
        k = np.minimum(pos.astype(int), n_in - 2)
        frac = (pos - k)[:, None]
        m = (1 - frac) * mag[k] + frac * mag[k + 1]
        dphi = ph[k + 1] - ph[k] - omega
        dphi -= 2 * np.pi * np.round(dphi / (2 * np.pi))
        inc = (omega + dphi).astype(np.float64)
        if b0 == 0:
            inc[0] = 0
        phases = phase + np.cumsum(inc, axis=0)
        phase = phases[-1]
        y = np.fft.irfft(m * np.exp(1j * phases), n=n_fft, axis=1) * win
        for j, i in enumerate(idx):
            out[i * hop:i * hop + n_fft] += y[j]
    return out / 1.5


def resample_by(x, factor):
    """長さを factor 倍にリサンプル (factor<1 で短く = 高く)。"""
    fr = Fraction(factor).limit_denominator(2000)
    return sg.resample_poly(x, fr.numerator, fr.denominator)


def pitch_shift(x, semitones):
    if abs(semitones) < 1e-3:
        return x.copy()
    factor = 2 ** (semitones / 12)
    y = stretch(x, factor)
    y = resample_by(y, 1 / factor)
    if len(y) < len(x):
        y = np.concatenate([y, np.zeros(len(x) - len(y))])
    return y[:len(x)]


# ----------------------------------------------------------------------------- DSP: reverb / textures
_IR_CACHE = {}


def make_ir(seconds, damp_hz=3500, seed=0, predelay=0.02):
    key = (seconds, damp_hz, seed, predelay)
    if key in _IR_CACHE:
        return _IR_CACHE[key]
    rng = np.random.default_rng(seed)
    n = sec(seconds)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    tail = noise * np.exp(-6.91 * t / seconds)
    # 高域ほど早く減衰する (空気吸収) — 2 段階のローパス
    tail = sg.sosfilt(sg.butter(2, damp_hz, 'low', fs=SR, output='sos'), tail)
    late = sg.sosfilt(sg.butter(2, damp_hz * 0.45, 'low', fs=SR, output='sos'), tail)
    mixw = np.clip(t / seconds, 0, 1)
    tail = tail * (1 - mixw) + late * mixw
    ir = np.zeros(n + sec(predelay))
    ir[sec(predelay):] += tail
    for d, g in [(0.009, 0.6), (0.017, 0.45), (0.027, 0.4), (0.039, 0.32), (0.051, 0.25), (0.067, 0.2)]:
        ir[sec(d)] += g * rng.choice([-1, 1])
    ir /= np.sqrt(np.sum(ir ** 2))
    _IR_CACHE[key] = ir
    return ir


def reverb(x, seconds=5.0, wet=0.5, dry=1.0, damp_hz=3500, seed=0, width=1.0):
    """mono/stereo → stereo。左右で別のインパルス応答を使い広がりを出す。"""
    if x.ndim == 1:
        xl = xr = x
    else:
        xl, xr = x[:, 0], x[:, 1]
    irl = make_ir(seconds, damp_hz, seed)
    irr = make_ir(seconds, damp_hz, seed + 101)
    if width < 1:
        irr = irr * width + irl * (1 - width)
    n = len(xl) + len(irl) - 1
    out = np.zeros((n, 2))
    out[:len(xl), 0] += dry * xl
    out[:len(xr), 1] += dry * xr
    out[:, 0] += wet * sg.fftconvolve(xl, irl)
    out[:, 1] += wet * sg.fftconvolve(xr, irr)
    return out


def reverse_reverb(x, seconds=4.0, wet=1.0):
    """逆再生 → リバーブ → 再逆再生: 音が「吸い込まれるように」立ち上がるスウェル。"""
    y = reverb(x[::-1], seconds, wet=wet, dry=0.0)
    return y[::-1]


def granular_freeze(x, center_s, dur_s, grain_s=0.14, hop_s=0.03, jitter_s=0.06, seed=0):
    """center 付近の一瞬をグレインで引き延ばし、持続音にする。"""
    rng = np.random.default_rng(seed)
    g = sec(grain_s)
    win = sg.get_window('hann', g)
    n = sec(dur_s) + g
    out = np.zeros(n)
    c = sec(center_s)
    pos = 0
    while pos + g < n:
        src = int(c + rng.uniform(-1, 1) * sec(jitter_s))
        src = max(0, min(len(x) - g, src))
        out[pos:pos + g] += x[src:src + g] * win * rng.uniform(0.7, 1.0)
        pos += sec(hop_s) + int(rng.integers(-sec(hop_s) // 3, sec(hop_s) // 3 + 1))
    return out[:sec(dur_s)] * (hop_s / grain_s) * 2


def gate(x, period_s, duty=0.5, depth=1.0, attack_s=0.005, release_s=0.04):
    """一定周期のゲート (ディエス・イレの息詰まるような刻み)。"""
    t = np.arange(len(x)) / SR
    phase = (t % period_s) / period_s
    env = (phase < duty).astype(float)
    k = max(1, sec(release_s))
    env = sg.lfilter([1 / k] * k, [1], env)
    ka = max(1, sec(attack_s))
    env = sg.lfilter([1 / ka] * ka, [1], env)
    return x * (1 - depth + depth * env)


def saturate(x, drive=3.0):
    return np.tanh(x * drive) / np.tanh(drive)


def tremolo(x, hz=0.5, depth=0.3):
    t = np.arange(len(x)) / SR
    return x * (1 - depth + depth * 0.5 * (1 + np.sin(2 * np.pi * hz * t)))


# ----------------------------------------------------------------------------- synths
def drone(freq, dur_s, seed=0, partials=8, brightness=1.3, lfo_hz=0.07, attack=4.0, release=6.0):
    """オルガン風の加算合成ドローン。左右で倍音のデチューンを変えて広がりを出す。"""
    rng = np.random.default_rng(seed)
    n = sec(dur_s)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for ch in range(2):
        for p in range(1, partials + 1):
            amp = 1.0 / p ** brightness
            det = 1 + rng.uniform(-1, 1) * 0.0015 * (1 + 0.5 * ch)
            drift = 1 + 0.0007 * np.sin(2 * np.pi * rng.uniform(0.03, 0.12) * t + rng.uniform(0, 6.28))
            am = 1 - 0.35 * (0.5 + 0.5 * np.sin(2 * np.pi * lfo_hz * rng.uniform(0.6, 1.4) * t + rng.uniform(0, 6.28)))
            out[:, ch] += amp * am * np.sin(2 * np.pi * freq * p * det * drift * t + rng.uniform(0, 6.28))
    out = butter(out, 3200, 'low', 2)
    out = fade(out, attack, release)
    return out / (partials ** 0.5)


def bell(freq, dur_s=9.0, seed=0, brightness=1.0):
    """非整数次倍音の鐘。"""
    rng = np.random.default_rng(seed)
    n = sec(dur_s)
    t = np.arange(n) / SR
    ratios = [0.56, 0.92, 1.0, 1.19, 1.71, 2.0, 2.74, 3.0, 3.76, 4.07, 5.4]
    amps = [0.7, 0.9, 1.0, 0.65, 0.5, 0.55, 0.32, 0.3, 0.2, 0.15, 0.08]
    out = np.zeros(n)
    for r, a in zip(ratios, amps):
        decay = 1.6 + 5.0 / (r ** 1.2)
        det = 1 + rng.uniform(-1, 1) * 0.002
        out += a * (brightness if r > 1.5 else 1.0) * np.exp(-t / decay) * np.sin(2 * np.pi * freq * r * det * t)
    strike = rng.standard_normal(sec(0.02)) * np.exp(-np.arange(sec(0.02)) / sec(0.004))
    out[:len(strike)] += 0.6 * butter(strike, 1500, 'high', 2)
    out = fade(out, 0.002, 0.5)
    return out / np.max(np.abs(out) + 1e-9)


def heartbeat(freq=43.65, dur_s=1.2):
    n = sec(dur_s)
    t = np.arange(n) / SR
    env = np.exp(-t / 0.28)
    y = np.sin(2 * np.pi * freq * t * (1 + 0.6 * np.exp(-t / 0.03))) * env
    return y


def breath(texture, dur_s, seed=0):
    """ノイズに近い短い録音を「風 / 息」として引き延ばす (ループ + クロスフェード + フィルタの揺らぎ)。"""
    rng = np.random.default_rng(seed)
    src = texture[sec(0.2):] if len(texture) > sec(1.5) else texture
    if rms_db(src) < -70:
        src = rng.standard_normal(len(src)) * 1e-3
    n = sec(dur_s)
    out = np.zeros(n + len(src))
    pos = 0
    seg_len = len(src)
    while pos < n:
        piece = fade(src, 0.4, 0.4) * rng.uniform(0.6, 1.0)
        if rng.random() < 0.5:
            piece = piece[::-1]
        out[pos:pos + seg_len] += piece
        pos += int(seg_len * 0.7)
    out = out[:n]
    t = np.arange(n) / SR
    # ゆらぐバンドパス: 低周波の LFO で明るさを変える
    lo = butter(out, 600, 'low', 2)
    hi = butter(out, 600, 'high', 2)
    mix = 0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t + rng.uniform(0, 6.28))
    out = lo * (1 - 0.6 * mix) + hi * (0.3 + 0.7 * mix)
    out = butter(out, 90, 'high', 2)
    out = butter(out, 7000, 'low', 2)
    return set_rms(out, -30)


# ----------------------------------------------------------------------------- mixer
class Mix:
    def __init__(self, dur_s):
        self.buf = np.zeros((sec(dur_s) + SR * 20, 2))
        self.markers = []

    def add(self, x, at_s, gain_db=0.0, pan_pos=0.0, width=0.0):
        if x.ndim == 1:
            x = to_stereo(x, width)
        if pan_pos:
            x = pan(x, pan_pos)
        a = sec(at_s)
        b = min(a + len(x), len(self.buf))
        self.buf[a:b] += x[:b - a] * db(gain_db)

    def mark(self, at_s, title, sub):
        self.markers.append((at_s, title, sub))

    def render(self, end_s):
        y = self.buf[:sec(end_s)]
        y = butter(y, 28, 'high', 2)
        y = y + 0.7 * butter(y, 3000, 'high', 2)  # 高域に少し空気感 (約 +4.6 dB シェルフ)
        y = set_rms(y, -20)
        # ソフトリミッタ
        y = np.tanh(y * 1.4) / np.tanh(1.4)
        return normalize(y, -1.0)


# ----------------------------------------------------------------------------- composition
def compose(sources, seed=7):
    rng = np.random.default_rng(seed)
    music = [s for s in sources if not s.is_texture]
    textures = [s for s in sources if s.is_texture]
    if not music:
        music = sources
    # 音量の大きい順 (Dies irae 用)、静かな順 (Introitus 用)
    by_loud = sorted(music, key=lambda s: -s.loud)
    S_loud = by_loud[0]
    S_soft = by_loud[-1]
    S_mid = by_loud[len(by_loud) // 2] if len(by_loud) > 2 else by_loud[0]
    tex = textures[0].x if textures else rng.standard_normal(sec(6)) * 1e-3

    F1, F2, C2, C3 = note_hz(41), note_hz(53), note_hz(48), note_hz(60)
    Db2, Eb2, Ab2, A3, Ab3 = note_hz(49), note_hz(51), note_hz(56), note_hz(69), note_hz(68)
    F3, F4, C4, B3 = note_hz(65), note_hz(77), note_hz(72), note_hz(71)

    # --- タイムライン (秒)
    T_INTRO, T_KYRIE, T_DIES, T_LACR, T_LUX, T_END = 0, 92, 200, 300, 428, 552
    mix = Mix(T_END)

    # ===== I. Introitus — Requiem aeternam (永遠の安息を) =====
    mix.mark(T_INTRO, 'I. Introitus', 'Requiem aeternam dona eis, Domine — 主よ、永遠の安息を彼らに与えたまえ')
    mix.add(drone(F1, 100, seed=1, partials=6, attack=8, release=10), 0, -14)
    mix.add(drone(C2, 96, seed=2, partials=6, attack=12, release=10), 4, -20)
    mix.add(breath(tex, 100, seed=3), 0, -6, width=1.0)
    mix.add(reverb(bell(F3, 12, seed=4, brightness=1.3), 8, wet=0.8, damp_hz=6000), 6, -12)
    mix.add(reverb(bell(C4, 12, seed=5, brightness=1.3), 8, wet=0.8, damp_hz=6000), 50, -16, pan_pos=0.3)
    # 静かな曲を 2.6 倍に引き延ばし、朧げに
    frag = S_soft.take(28, want='soft')
    slow = stretch(frag, 2.6)
    slow = butter(slow, 3000, 'low', 2)
    slow = fade(slow, 6, 8)
    mix.add(reverb(slow, 7, wet=0.9, dry=0.5, seed=6), 22, -8, width=0.8)

    # ===== II. Kyrie (憐れみの讃歌) — 3 声のカノン =====
    mix.mark(T_KYRIE, 'II. Kyrie', 'Kyrie eleison — 主よ、憐れみたまえ')
    theme = S_mid.take(30, want='tonal')
    theme = fade(stretch(theme, 1.6), 3, 5)  # 48 s
    for i, (semi, delay, g, p) in enumerate([(0, 0, -9, -0.4), (-5, 14, -10, 0.4), (-12, 28, -11, 0.0), (7, 42, -14, -0.2)]):
        v = pitch_shift(theme, semi) if semi else theme
        v = butter(v, 5000 if semi > -12 else 1200, 'low', 2)
        mix.add(reverb(v, 6, wet=0.8, dry=0.6, seed=10 + i), T_KYRIE + 2 + delay, g, pan_pos=p)
    # 和声の土台: i – VI – V – i
    for j, (root, at, ln) in enumerate([(F1, 0, 34), (Db2, 30, 30), (C2, 58, 28), (F1, 84, 26)]):
        mix.add(drone(root, ln, seed=20 + j, partials=5, attack=5, release=6), T_KYRIE + at, -16)
    for k in range(0, 100, 4):  # 心拍
        mix.add(heartbeat(F1), T_KYRIE + 4 + k, -12 + rng.uniform(-2, 0))
    mix.add(breath(tex, 100, seed=21), T_KYRIE, -12, width=1.0)

    # ===== III. Dies irae (怒りの日) =====
    mix.mark(T_DIES, 'III. Dies irae', 'Dies irae, dies illa — 怒りの日、その日は')
    L = 92
    hot = S_loud.take(L, want='loud')
    hot = fade(hot, 1.0, 2.0)
    # 刻み: 逆再生スウェルで突入し、ゲートと歪みで息詰まる刻みに
    period = 60 / 92 / 2  # 8 分音符 @ 92 bpm
    gated = gate(saturate(hot, 2.5), period, duty=0.55, depth=0.85)
    mix.add(reverse_reverb(hot[:sec(6)], 5), T_DIES - 6, -12)
    mix.add(reverb(gated, 2.2, wet=0.35, dry=1.0, damp_hz=5000, seed=30), T_DIES, -7, width=0.6)
    # 1 オクターブ下の影と、上の叫び
    low = butter(pitch_shift(hot, -12), 500, 'low', 2)
    mix.add(reverb(low, 3, wet=0.4, seed=31), T_DIES, -9)
    cry = fade(pitch_shift(hot[sec(40):sec(80)], 12), 4, 6)
    mix.add(reverb(butter(cry, 1200, 'high', 2), 4, wet=0.9, dry=0.3, seed=32), T_DIES + 40, -18, pan_pos=0.5)
    # 鼓動を 4 分音符で、鐘は三全音 (F–B) — diabolus in musica
    beat = 60 / 92
    for k in range(int(L / beat)):
        acc = 0 if k % 4 == 0 else -6
        mix.add(heartbeat(F1 if k % 8 < 4 else Db2 / 2, 0.8), T_DIES + k * beat, -8 + acc)
    for k, (f, at) in enumerate([(F3, 0), (B3, 16), (F3, 32), (B3, 48), (F3, 64), (B3, 72), (F3, 80), (B3, 84), (F3, 88)]):
        mix.add(reverb(bell(f, 8, seed=40 + k, brightness=1.6), 6, wet=0.7), T_DIES + at, -10, pan_pos=(-0.5 if k % 2 else 0.5))
    mix.add(drone(F1, L + 6, seed=41, partials=10, brightness=1.0, attack=2, release=6), T_DIES, -13)
    # 突然の断絶
    mix.add(reverb(bell(F2, 14, seed=42), 10, wet=1.0, dry=0.3), T_DIES + L, -8)

    # ===== IV. Lacrimosa (涙の日) — 嘆きのテトラコルド F–Eb–Db–C =====
    mix.mark(T_LACR, 'IV. Lacrimosa', 'Lacrimosa dies illa — 涙の日、その日は')
    lament = [(F2, 0), (Eb2, 16), (Db2, 32), (C2, 48), (F2, 64), (Eb2, 80), (Db2, 96), (C2, 112)]
    for j, (root, at) in enumerate(lament):
        mix.add(drone(root, 18, seed=50 + j, partials=6, attack=3, release=5), T_LACR + at, -19)
        mix.add(reverb(bell(root * 4, 10, seed=60 + j, brightness=1.3), 9, wet=0.9, damp_hz=6000), T_LACR + at, -17, pan_pos=(-0.4 if j % 2 else 0.4))
    # 主題を 3 倍に引き延ばし、1 オクターブ下へ — 涙
    frag = S_mid.take(36, want='tonal', rank=1)
    slow = fade(butter(pitch_shift(stretch(frag, 3.0), -12), 2000, 'low', 2), 8, 10)  # 108 s
    mix.add(reverb(slow, 9, wet=1.0, dry=0.4, seed=70), T_LACR + 6, -13, width=0.9)
    # 静かな曲の逆再生スウェル (吸い込まれるように)
    for j, at in enumerate([12, 44, 76, 108]):
        sw = S_soft.take(10, want='soft', rank=j)
        sw = fade(butter(sw, 3000, 'low', 2), 0.5, 1.5)
        mix.add(reverse_reverb(sw, 6), T_LACR + at - 6, -16, pan_pos=(0.6 if j % 2 else -0.6))
    mix.add(breath(tex, 130, seed=71), T_LACR, -8, width=1.0)

    # ===== V. Lux aeterna (永遠の光) — 合唱 (グラニュラー) とピカルディの三度 =====
    mix.mark(T_LUX, 'V. Lux aeterna', 'Lux aeterna luceat eis — 永遠の光が彼らを照らしたまえ')
    center = S_loud.pick(8, want='tonal', rank=2) + 4
    choir = granular_freeze(S_loud.x, center, 110, seed=80)
    if S_loud.shift:
        choir = pitch_shift(choir, S_loud.shift)
    choir = butter(choir, 6500, 'low', 2)
    choir = fade(choir, 12, 14)
    mix.add(reverb(choir, 8, wet=0.9, dry=0.5, damp_hz=5000, seed=81), T_LUX, -9, width=0.8)
    mix.add(reverb(fade(pitch_shift(choir, 7), 20, 14), 8, wet=1.0, dry=0.3, seed=82), T_LUX + 8, -18, pan_pos=-0.5)
    shimmer = tremolo(fade(pitch_shift(choir, 12), 30, 14), 0.3, 0.4)
    mix.add(reverb(shimmer, 10, wet=1.0, dry=0.0, damp_hz=7000, seed=83), T_LUX + 16, -17, pan_pos=0.5)
    # 静かな曲をゆっくり、光の中で
    frag = S_soft.take(30, want='tonal', rank=1)
    slow = fade(butter(stretch(frag, 2.2), 4000, 'low', 2), 8, 12)
    mix.add(reverb(slow, 8, wet=0.9, dry=0.5, seed=84), T_LUX + 30, -10, width=0.8)
    # VI – III – i(major): Db – Ab – F(+A) 、最後はピカルディの三度
    mix.add(drone(Db2, 40, seed=90, partials=6, attack=6, release=8), T_LUX, -15)
    mix.add(drone(Ab2, 40, seed=91, partials=6, attack=8, release=8), T_LUX + 36, -17)
    mix.add(drone(F1, 60, seed=92, partials=6, attack=12, release=16), T_LUX + 66, -15)
    mix.add(drone(C3, 52, seed=93, partials=5, attack=10, release=16), T_LUX + 72, -20)
    mix.add(drone(A3, 40, seed=94, partials=4, attack=14, release=16), T_LUX + 84, -22)  # 長三度 = 光
    mix.add(reverb(bell(F4, 14, seed=95), 12, wet=1.0, dry=0.4), T_LUX + 96, -14)
    mix.add(reverb(bell(F3, 16, seed=96), 12, wet=1.0, dry=0.4), T_LUX + 112, -12)
    mix.add(breath(tex, 120, seed=97), T_LUX, -10, width=1.0)

    y = mix.render(T_END)
    y = fade(y, 0.5, 8.0)
    return y, mix.markers


# ----------------------------------------------------------------------------- video
def find_font(candidates):
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


LATIN_FONTS = ['/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
               '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
               '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
               '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',
               'C:/Windows/Fonts/georgia.ttf', 'C:/Windows/Fonts/times.ttf',
               '/System/Library/Fonts/Supplemental/Georgia.ttf']
JP_FONTS = ['/etc/alternatives/fonts-japanese-gothic.ttf',
            '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf',
            'C:/Windows/Fonts/meiryo.ttc', 'C:/Windows/Fonts/msgothic.ttc',
            '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc']


def render_card(path, w, h, lines):
    """透過 PNG のタイトルカードを描く。lines: [(text, font_path, size_ratio, y_ratio, rgb)]"""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        return False
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    shadow = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ds = ImageDraw.Draw(shadow)
    # 文字の背後に柔らかい暗幕 (上下にぼかした半透明の帯) を敷いて可読性を保つ
    ys = [h * y_r for _, _, _, y_r, _ in lines]
    sizes = [h * size_r for _, _, size_r, _, _ in lines]
    top = int(min(ys) - h * 0.06)
    bottom = int(max(y + sz for y, sz in zip(ys, sizes)) + h * 0.05)
    band = Image.new('L', (w, h), 0)
    ImageDraw.Draw(band).rectangle([0, top, w, bottom], fill=170)
    band = band.filter(ImageFilter.GaussianBlur(h * 0.04))
    veil = Image.new('RGBA', (w, h), (4, 3, 6, 255))
    veil.putalpha(band)
    img = Image.alpha_composite(img, veil)
    d = ImageDraw.Draw(img)
    for text, font_path, size_r, y_r, rgb in lines:
        if not text or not font_path:
            continue
        font = ImageFont.truetype(font_path, int(h * size_r))
        bbox = d.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (w - tw) / 2 - bbox[0]
        y = h * y_r - bbox[1]
        ds.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 230))
        d.text((x, y), text, font=font, fill=rgb + (255,))
    shadow = shadow.filter(ImageFilter.GaussianBlur(4))
    out = Image.alpha_composite(shadow, img)
    out.save(path)
    return True


def render_video(wav_path, out_path, markers, dur_s, size='1280x720', fps=30, crf=29, title='Requiem'):
    ff = ffmpeg_exe()
    w, h = (int(v) for v in size.split('x'))
    latin = find_font(LATIN_FONTS)
    jp = find_font(JP_FONTS)
    ivory, dim, gold = (232, 220, 192), (190, 180, 160), (214, 176, 96)
    cards = []  # (png, start, dur)
    if latin:
        title_png = out_path + '.card0.png'
        ok = render_card(title_png, w, h, [
            (title.upper(), latin, 0.12, 0.34, ivory),
            ('in F minor', latin, 0.032, 0.50, gold),
            ('generated from the submitted recordings', latin, 0.026, 0.56, dim),
            ('提出された録音より生成 — ヘ短調', jp, 0.026, 0.61, dim),
        ])
        if ok:
            cards.append((title_png, 0.8, 12.0))
            for i, (at, mt, sub) in enumerate(markers):
                latin_line, jp_line = (sub.split(' — ') + [''])[:2]
                png = out_path + f'.card{i + 1}.png'
                render_card(png, w, h, [
                    (mt, latin, 0.062, 0.76, ivory),
                    (latin_line, latin, 0.028, 0.855, gold),
                    (jp_line, jp, 0.026, 0.905, dim),
                ])
                start = float(at) + 0.5 if at >= 12 else 13.5  # 冒頭はタイトルの後に
                cards.append((png, start, 16.0))
    # 映像: CQT スペクトル (低音 = 金色の炎 → 高音 = 青白い光)
    bar_h = (h * 2 // 3) // 2 * 2
    chain = [f"[0:a]showcqt=s={w}x{h}:r={fps}:axis=0:bar_h={bar_h}:sono_h={h - bar_h}:"
             f"bar_g=4:sono_g=6:count=4:sono_v=10:bar_v=16,"
             f"colorchannelmixer=rr=0.78:rg=0.22:rb=0.04:gr=0.30:gg=0.50:gb=0.10:br=0.12:bg=0.20:bb=0.42[v0]"]
    cur = 'v0'
    cmd = [ff, '-y', '-v', 'error', '-stats', '-i', wav_path]
    for i, (png, start, d) in enumerate(cards):
        cmd += ['-loop', '1', '-framerate', str(fps), '-t', f'{d:.2f}', '-i', png]
        k = i + 1
        chain.append(f"[{k}:v]format=rgba,fade=t=in:st=0:d=1.5:alpha=1,fade=t=out:st={d - 2.5:.2f}:d=2.5:alpha=1,"
                     f"setpts=PTS-STARTPTS+{start:.2f}/TB[c{k}]")
        chain.append(f"[{cur}][c{k}]overlay=0:0:eof_action=pass:enable='between(t\\,{start:.2f}\\,{start + d:.2f})'[v{k}]")
        cur = f'v{k}'
    chain.append(f"[{cur}]fade=t=in:st=0:d=2,fade=t=out:st={dur_s - 6:.2f}:d=6,format=yuv420p[v]")
    cmd += ['-filter_complex', ';'.join(chain), '-map', '[v]', '-map', '0:a',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', str(crf), '-pix_fmt', 'yuv420p', '-r', str(fps),
            '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', f'{dur_s:.2f}', out_path]
    try:
        subprocess.run(cmd, check=True)
    finally:
        for png, _, _ in cards:
            if os.path.exists(png):
                os.remove(png)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description='録音からレクイエムを生成して MP4 を書き出す')
    ap.add_argument('inputs', nargs='+', help='入力音声 (mp3 / m4a / wav ...)')
    ap.add_argument('-o', '--output', default='requiem.mp4')
    ap.add_argument('--wav', default=None, help='ミックスの WAV も保存する場合のパス')
    ap.add_argument('--no-video', action='store_true', help='WAV のみ (MP4 を作らない)')
    ap.add_argument('--size', default='1280x720')
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--crf', type=int, default=29)
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--title', default='Requiem')
    args = ap.parse_args()

    print('[1/4] decoding + analysis')
    sources = [Source(p, i + 1) for i, p in enumerate(args.inputs)]
    for s in sources:
        print('   ', s.describe())
    print('[2/4] composing (F minor)')
    y, markers = compose(sources, seed=args.seed)
    dur = len(y) / SR
    print(f'    duration {int(dur // 60)}:{int(dur % 60):02d}   peak {20 * np.log10(np.max(np.abs(y))):.1f} dBFS   rms {rms_db(y):.1f} dBFS')
    wav_path = args.wav or (os.path.splitext(args.output)[0] + '.mix.wav')
    print('[3/4] writing', wav_path)
    wavfile.write(wav_path, SR, (np.clip(y, -1, 1) * 32767).astype(np.int16))
    if args.no_video:
        return
    print('[4/4] encoding video', args.output)
    render_video(wav_path, args.output, markers, dur, args.size, args.fps, args.crf, args.title)
    if not args.wav:
        os.remove(wav_path)
    print('done:', args.output, f'{os.path.getsize(args.output) / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
