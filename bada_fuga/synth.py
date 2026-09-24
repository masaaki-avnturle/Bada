#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""score.json -> fuga.wav  (加算合成オルガン風 4 声 + 合成リバーブ)"""
import json, sys, math, os
import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve

SR = 44100
BPB_S = 4

# 声部ごとの音色: (倍音振幅, attack, release, gain, pan, detune cents, vibrato depth)
TIMBRE = {
    'S': dict(h=[1.0, .35, .18, .10, .06, .03], a=.018, r=.10, g=.62, pan=+.30, det=4.0, vib=.25),   # フルート系
    'A': dict(h=[1.0, .55, .40, .28, .18, .10, .06], a=.020, r=.10, g=.55, pan=-.20, det=3.0, vib=.15), # リード系
    'T': dict(h=[1.0, .70, .45, .32, .22, .15, .10, .07], a=.030, r=.12, g=.55, pan=+.15, det=5.0, vib=.12), # 弦系
    'B': dict(h=[1.0, .45, .30, .15, .08], a=.025, r=.13, g=.75, pan=-.30, det=2.0, vib=.0, sub=.45),   # プリンシパル+16'
}

def env(nsamp, a, r, sr=SR):
    e = np.ones(nsamp, dtype=np.float32)
    na = min(int(a * sr), nsamp); nr = min(int(r * sr), nsamp)
    if na > 0: e[:na] = np.linspace(0, 1, na, endpoint=False) ** 0.6
    if nr > 0: e[-nr:] *= np.linspace(1, 0, nr) ** 1.5
    return e

def tone(freq, dur, tb, sr=SR):
    nsamp = int((dur + tb['r']) * sr)
    t = np.arange(nsamp, dtype=np.float32) / sr
    out = np.zeros(nsamp, dtype=np.float32)
    vib = 1.0 + (tb['vib'] / 100.0) * 0.06 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t / 0.6, 0, 1) if tb['vib'] else 1.0
    for k, amp in enumerate(tb['h'], start=1):
        f = freq * k
        if f > sr * 0.45: break
        # 高い倍音ほど減衰を速く (弦/管の自然さ)
        decay = np.exp(-t * (0.25 * k))
        det = 2 ** (tb['det'] * (1 if k % 2 else -1) / 1200.0)
        out += amp * (np.sin(2 * np.pi * f * vib * t) + 0.5 * np.sin(2 * np.pi * f * det * vib * t + 0.7)) * decay
    if tb.get('sub'):
        out += tb['sub'] * np.sin(2 * np.pi * (freq / 2) * t)
    e = env(nsamp, tb['a'], tb['r'], sr)
    e[:int(dur * sr)] *= 1.0
    return out * e

VOWELS = {'a': ([(730, 130), (1090, 160), (2440, 240), (3400, 320)], [1.0, 0.75, 0.35, 0.12]),
          'o': ([(450, 110), (800, 130), (2600, 260), (3200, 320)], [1.0, 0.6, 0.18, 0.06])}
VOWEL = 'a'
def formant_amps(f0, nh=60):
    """母音のフォルマントで整形した倍音振幅 (合唱風)"""
    F, Wt = VOWELS[VOWEL]
    amps = []
    for k in range(1, nh + 1):
        f = k * f0
        if f > 16000: break
        a = sum(w / (1 + ((f - Fc) / bw) ** 2) for (Fc, bw), w in zip(F, Wt))
        amps.append(a / k ** 0.55)
    return np.array(amps, dtype=np.float32)

def choir_tone(freq, dur, a=0.16, r=0.35, sr=SR):
    nsamp = int((dur + r) * sr)
    t = np.arange(nsamp, dtype=np.float32) / sr
    amps = formant_amps(freq)
    N = 4096; ph = np.arange(N) / N
    table = np.zeros(N, dtype=np.float32)
    for k, amp in enumerate(amps, start=1):
        table += amp * np.sin(2 * np.pi * k * ph)
    table /= (np.abs(table).max() + 1e-9)
    tab = np.append(table, table[0])
    out = np.zeros(nsamp, dtype=np.float32)
    for det, vph in ((0.0, 0.0), (7.0, 1.1), (-6.0, 2.3)):
        f = freq * 2 ** (det / 1200.0)
        vib = 1 + 0.0045 * np.sin(2 * np.pi * 4.8 * t + vph) * np.clip((t - 0.2) / 0.6, 0, 1)
        phase = np.cumsum(f * vib / sr)
        out += np.interp((phase % 1.0) * N, np.arange(N + 1), tab)
    out /= 3
    return out * env(nsamp, a, r, sr)

def bell_tone(freq, dur, sr=SR):
    nsamp = int(dur * sr)
    t = np.arange(nsamp, dtype=np.float32) / sr
    parts = [(0.56, 0.35, .9), (0.92, 0.45, .7), (1.19, 0.6, .5), (1.71, 0.8, .5), (2.0, 1.0, .4),
             (2.74, 1.3, .3), (3.0, 1.5, .25), (3.76, 1.9, .2), (4.07, 2.2, .15), (5.4, 3.0, .08)]
    out = np.zeros(nsamp, dtype=np.float32)
    for ratio, dr, amp in parts:
        out += amp * np.sin(2 * np.pi * freq * ratio * t + 0.3 * ratio) * np.exp(-t * dr)
    out[:int(0.003 * sr)] *= np.linspace(0, 1, int(0.003 * sr))
    return out * np.exp(-t * 0.15)

def pulse_tone(sr=SR):
    """心拍のような低い打音: 80→38 Hz へ落ちるサイン + 短いノイズ"""
    nsamp = int(0.42 * sr)
    t = np.arange(nsamp, dtype=np.float32) / sr
    f = 38 + 42 * np.exp(-t * 18)
    ph = 2 * np.pi * np.cumsum(f) / sr
    body = np.sin(ph) * np.exp(-t * 9)
    noise = np.random.default_rng(5).standard_normal(nsamp).astype(np.float32) * np.exp(-t * 90) * 0.15
    y = body + noise
    y[:int(0.002 * sr)] *= np.linspace(0, 1, int(0.002 * sr))
    return y

def mallet_tone(freq, dur, vel=0.5, bright=True, sr=SR):
    """木琴系シンセ: 木琴の非整数倍音 (1, 3.93, 9.5 ...) の速い減衰 + 正弦波の持続 (シンセ成分)"""
    ring = 1.6 if freq < 700 else 1.1
    nsamp = int((dur + ring) * sr)
    t = np.arange(nsamp, dtype=np.float32) / sr
    parts = [(1.0, 1.0, 1.0), (3.93, 0.42 if bright else 0.25, 3.2), (9.5, 0.15 if bright else 0.06, 7.0), (2.0, 0.08, 4.0)]
    out = np.zeros(nsamp, dtype=np.float32)
    for ratio, amp, dr in parts:
        if freq * ratio > sr * 0.45: continue
        out += amp * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t * dr * (0.9 + freq / 2500.0))
    # シンセの持続成分 (弱いサイン + わずかなトレモロ) を音価のあいだ保つ
    sus = 0.22 * np.sin(2 * np.pi * freq * t) * (1 + 0.12 * np.sin(2 * np.pi * 5.5 * t))
    gate = np.ones(nsamp, dtype=np.float32); i0 = int(dur * sr)
    if i0 < nsamp: gate[i0:] = np.exp(-(t[i0:] - t[i0]) / 0.25)
    out += sus * gate * np.clip(t / 0.05, 0, 1)
    nh = int(0.002 * sr)
    out[:nh] += np.random.default_rng(int(freq) + 7).standard_normal(nh).astype(np.float32) * np.linspace(1, 0, nh) * 0.5 * vel
    att = int(0.0012 * sr); out[:att] *= np.linspace(0, 1, att)
    return out * (0.3 + 0.7 * vel)

_SAW_TABLE = None
def cluster_tone(freq, dur, vel=0.3, sr=SR):
    """電子シンセの持続音: 3 本のデチューン鋸歯波 (波形テーブル) + ゆっくりした揺れ。遅い立ち上がり・長い減衰。"""
    global _SAW_TABLE
    N = 4096
    if _SAW_TABLE is None:
        ph = np.arange(N) / N; tab = np.zeros(N, dtype=np.float32)
        for k in range(1, 28): tab += np.sin(2 * np.pi * k * ph) / k ** 1.25
        _SAW_TABLE = np.append(tab / np.abs(tab).max(), tab[0])
    a, r = 1.8, 2.6
    nsamp = int((dur + r) * sr)
    t = np.arange(nsamp, dtype=np.float32) / sr
    out = np.zeros(nsamp, dtype=np.float32)
    for det, vph in ((0.0, 0.0), (9.0, 1.7), (-11.0, 3.1)):
        f = freq * 2 ** (det / 1200.0) * (1 + 0.0015 * np.sin(2 * np.pi * 0.13 * t + vph))
        phase = np.cumsum(f / sr)
        out += np.interp((phase % 1.0) * N, np.arange(N + 1), _SAW_TABLE)
    out /= 3
    trem = 1 + 0.18 * np.sin(2 * np.pi * 0.37 * t + freq * 0.01)
    e = env(nsamp, a, r, sr)
    return out * e * trem * vel

_TABLES = {}
def _table(name, nh, p, odd_boost=1.0):
    key = (name, nh, p, odd_boost)
    if key not in _TABLES:
        N = 4096; ph = np.arange(N) / N; tab = np.zeros(N, dtype=np.float32)
        for k in range(1, nh + 1):
            tab += (np.sin(2 * np.pi * k * ph) / k ** p) * (odd_boost if k % 2 else 1.0)
        _TABLES[key] = np.append(tab / np.abs(tab).max(), tab[0])
    return _TABLES[key]

def _wavetable_voice(freq, nsamp, tab, dets, vib_depth, vib_rate, t, sr):
    N = 4096; out = np.zeros(nsamp, dtype=np.float32)
    for det, vph in dets:
        f = freq * 2 ** (det / 1200.0) * (1 + vib_depth * np.sin(2 * np.pi * vib_rate * t + vph) * np.clip((t - 0.25) / 0.5, 0, 1))
        phase = np.cumsum(f / sr)
        out += np.interp((phase % 1.0) * N, np.arange(N + 1), tab)
    return out / len(dets)

def string_tone(freq, dur, vel=0.5, dark=0.0, sr=SR):
    """弦楽合奏: 鋸歯波の波形テーブルを 5 本デチューンで重ね、ビブラート、遅い立ち上がり"""
    a, r = 0.45 + 0.3 * dark, 0.5
    nsamp = int((dur + r) * sr); t = np.arange(nsamp, dtype=np.float32) / sr
    nh = int(max(6, min(36, 9000.0 / freq)))
    tab = _table('str', nh, 1.15 + 0.5 * dark)
    dets = [(0.0, 0.0), (7.0, 1.1), (-6.0, 2.2), (12.0, 3.3), (-11.0, 4.4)]
    out = _wavetable_voice(freq, nsamp, tab, dets, 0.004, 5.3, t, sr)
    e = env(nsamp, a, r, sr)
    swell = 1 + 0.12 * np.sin(2 * np.pi * 0.22 * t)          # 弓の圧のうねり
    return out * e * swell * vel

def wind_tone(freq, dur, vel=0.5, kind='oboe', sr=SR):
    a, r = (0.09, 0.18) if kind == 'oboe' else (0.14, 0.22)
    nsamp = int((dur + r) * sr); t = np.arange(nsamp, dtype=np.float32) / sr
    if kind == 'oboe':
        tab = _table('ob', int(max(4, min(24, 8000.0 / freq))), 0.9, odd_boost=1.3)
        out = _wavetable_voice(freq, nsamp, tab, [(0.0, 0.0), (3.0, 1.0)], 0.006, 5.6, t, sr)
    else:
        tab = _table('fl', 5, 1.9)
        out = _wavetable_voice(freq, nsamp, tab, [(0.0, 0.0), (2.0, 1.0)], 0.005, 5.0, t, sr)
        breath = np.random.default_rng(int(freq)).standard_normal(nsamp).astype(np.float32) * 0.02
        out += breath
    return out * env(nsamp, a, r, sr) * vel

def horn_tone(freq, dur, vel=0.4, sr=SR):
    a, r = 0.16, 0.35
    nsamp = int((dur + r) * sr); t = np.arange(nsamp, dtype=np.float32) / sr
    tab = _table('hn', int(max(4, min(16, 4000.0 / freq))), 1.6)
    out = _wavetable_voice(freq, nsamp, tab, [(0.0, 0.0), (4.0, 1.5), (-4.0, 2.5)], 0.002, 4.5, t, sr)
    return out * env(nsamp, a, r, sr) * vel

def timp_tone(freq, dur, vel=0.5, sr=SR):
    """ティンパニ: 音価が 1.5 拍以上ならロール (毎秒 11 打)、それ以外は単打"""
    def stroke(v):
        ns = int(1.6 * sr); tt = np.arange(ns, dtype=np.float32) / sr
        f = freq * (1 + 0.25 * np.exp(-tt * 25))
        y = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-tt * 2.2)
        y += 0.5 * np.sin(2 * np.pi * freq * 1.5 * tt) * np.exp(-tt * 4.0)
        nz = np.random.default_rng(3).standard_normal(ns).astype(np.float32) * np.exp(-tt * 60) * 0.5
        return (y + nz) * v
    nsamp = int((dur + 1.6) * sr); out = np.zeros(nsamp, dtype=np.float32)
    if dur >= 1.2:
        k = 0; i = 0; rate = 11.0
        while i < int(dur * sr):
            v = 0.35 + 0.65 * min(1.0, i / (dur * sr) * 1.4)
            st = stroke(v * (0.9 + 0.1 * (k % 2))); j = min(nsamp, i + len(st))
            out[i:j] += st[:j - i]; i += int(sr / rate); k += 1
    else:
        st = stroke(1.0); out[:len(st)] += st[:nsamp]
    return out * vel

def brass_tone(freq, dur, vel=0.45, kind='trumpet', sr=SR):
    a, r = (0.06, 0.2) if kind == 'trumpet' else (0.1, 0.3)
    nsamp = int((dur + r) * sr); t = np.arange(nsamp, dtype=np.float32) / sr
    if kind == 'trumpet':
        tab = _table('tp', int(max(6, min(30, 9000.0 / freq))), 0.95)
        out = _wavetable_voice(freq, nsamp, tab, [(0.0, 0.0), (3.0, 1.0), (-3.0, 2.0)], 0.003, 5.8, t, sr)
    else:
        tab = _table('tb', int(max(6, min(24, 6000.0 / freq))), 1.2)
        out = _wavetable_voice(freq, nsamp, tab, [(0.0, 0.0), (4.0, 1.0), (-4.0, 2.0)], 0.002, 5.0, t, sr)
    # 金管の立ち上がりで倍音が開く感じ: 最初の 80ms を少し強く
    e = env(nsamp, a, r, sr); e[:int(0.08 * sr)] *= np.linspace(1.15, 1.0, int(0.08 * sr))
    return out * e * vel

def clarinet_tone(freq, dur, vel=0.45, sr=SR):
    a, r = 0.1, 0.2
    nsamp = int((dur + r) * sr); t = np.arange(nsamp, dtype=np.float32) / sr
    tab = _table('cl', int(max(4, min(16, 6000.0 / freq))), 1.1, odd_boost=2.2)   # 奇数倍音が強い
    out = _wavetable_voice(freq, nsamp, tab, [(0.0, 0.0), (2.0, 1.0)], 0.003, 5.2, t, sr)
    return out * env(nsamp, a, r, sr) * vel

def ep_tone(freq, dur, vel=0.5, sr=SR):
    nsamp = int((dur + 1.8) * sr)
    t = np.arange(nsamp, dtype=np.float32) / sr
    mod_idx = (1.5 + 2.5 * vel) * np.exp(-t * 4.0)
    carrier = np.sin(2 * np.pi * freq * t + mod_idx * np.sin(2 * np.pi * freq * 14.0 * t))
    e = 0.6 * np.exp(-t * (1.2 + 1.5 * freq / 1000)) + 0.4 * np.exp(-t * 0.25)
    key = np.ones(nsamp, dtype=np.float32)
    i0 = int(dur * sr)
    if i0 < nsamp: key[i0:] = np.exp(-(t[i0:] - t[i0]) / 0.4)
    att = int(0.003 * sr)
    carrier[:att] *= np.linspace(0, 1, att)
    trem = 1 + 0.06 * np.sin(2 * np.pi * 4.8 * t)
    return carrier * e * key * trem * (0.4 + 0.6 * vel)

def pad_tone(freq, dur, vel=0.3, sr=SR):
    a, r = 1.2, 2.5
    nsamp = int((dur + r) * sr); t = np.arange(nsamp, dtype=np.float32) / sr
    nh = int(max(4, min(20, 6000.0 / freq)))
    tab = _table('pad', nh, 1.4)
    dets = [(0.0, 0.0), (8.0, 1.3), (-7.0, 2.7)]
    out = _wavetable_voice(freq, nsamp, tab, dets, 0.003, 0.15, t, sr)
    lfo = 1 + 0.15 * np.sin(2 * np.pi * 0.12 * t + freq * 0.01)
    return out * env(nsamp, a, r, sr) * lfo * vel

def lead_tone(freq, dur, vel=0.5, sr=SR):
    a, r = 0.06, 0.35
    nsamp = int((dur + r) * sr); t = np.arange(nsamp, dtype=np.float32) / sr
    nh = int(max(4, min(18, 8000.0 / freq)))
    tab = _table('ld', nh, 1.0, odd_boost=2.0)
    dets = [(0.0, 0.0), (5.0, 1.0), (-5.0, 2.0)]
    out = _wavetable_voice(freq, nsamp, tab, dets, 0.005, 5.5, t, sr)
    out *= np.clip(t / 0.04, 0, 1)
    return out * env(nsamp, a, r, sr) * vel

def drum_brush(midi, dur, vel=0.5, sr=SR):
    if midi == 36:
        nsamp = int(0.35 * sr); t = np.arange(nsamp, dtype=np.float32) / sr
        f = 55 + 30 * np.exp(-t * 20)
        y = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t * 8) * 0.8
        nz = np.random.default_rng(36).standard_normal(nsamp).astype(np.float32) * np.exp(-t * 50) * 0.15
        return (y + nz) * vel
    elif midi == 38:
        nsamp = int(0.25 * sr); t = np.arange(nsamp, dtype=np.float32) / sr
        body = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 18) * 0.4
        swish = np.random.default_rng(38).standard_normal(nsamp).astype(np.float32)
        swish *= np.exp(-t * 12) * (1 + 0.5 * np.exp(-t * 40))
        from scipy.signal import lfilter
        swish = lfilter([0.6], [1, -0.4], swish).astype(np.float32)
        return (body + swish * 0.6) * vel
    elif midi == 42:
        nsamp = int(0.08 * sr); t = np.arange(nsamp, dtype=np.float32) / sr
        return np.random.default_rng(42).standard_normal(nsamp).astype(np.float32) * np.exp(-t * 60) * 0.4 * vel
    elif midi == 46:
        nsamp = int(0.2 * sr); t = np.arange(nsamp, dtype=np.float32) / sr
        return np.random.default_rng(46).standard_normal(nsamp).astype(np.float32) * np.exp(-t * 15) * 0.35 * vel
    return np.zeros(int(0.1 * sr), dtype=np.float32)

_CB_TABLES = {}
def contrabass_tone(freq, dur, vel=0.5, pizz=False, sr=SR):
    """コントラバス: arco = 胴の共鳴 (200 Hz 付近) を強めた鋸歯波 3 本 + 弓の擦過音 + 遅いビブラート、
    pizz = 指で弾いた弦 (倍音ごとに速く減衰) + 胴の低い鳴り"""
    if pizz:
        ring = 1.8
        nsamp = int((min(dur, 1.2) + ring) * sr); t = np.arange(nsamp, dtype=np.float32) / sr
        out = np.zeros(nsamp, dtype=np.float32)
        for k in range(1, 14):
            if freq * k > 5000: break
            out += (1.0 / k ** 1.25) * np.sin(2 * np.pi * freq * k * t + 0.4 * k) * np.exp(-t * (2.2 + 1.6 * k))
        out += 0.5 * np.sin(2 * np.pi * freq * t) * np.exp(-t * 1.3)
        nh = int(0.004 * sr)
        out[:nh] += np.random.default_rng(int(freq * 3)).standard_normal(nh).astype(np.float32) * np.linspace(0.6, 0, nh)
        out[:int(0.002 * sr)] *= np.linspace(0, 1, int(0.002 * sr))
        return out * vel
    a, r = 0.22, 0.45
    nsamp = int((dur + r) * sr); t = np.arange(nsamp, dtype=np.float32) / sr
    nh = int(max(8, min(40, 7000.0 / freq)))
    key = (nh, int(freq))
    if key not in _CB_TABLES:
        N = 4096; ph = np.arange(N) / N; tab = np.zeros(N, dtype=np.float32)
        for k in range(1, nh + 1):
            fk = freq * k
            body = 1.0 + 0.9 * math.exp(-((fk - 210.0) / 140.0) ** 2) + 0.35 * math.exp(-((fk - 520.0) / 200.0) ** 2)
            tab += np.sin(2 * np.pi * k * ph + 0.3 * k) * body / k ** 1.05
        _CB_TABLES[key] = np.append(tab / np.abs(tab).max(), tab[0])
    out = _wavetable_voice(freq, nsamp, _CB_TABLES[key], [(0.0, 0.0), (5.0, 1.3), (-6.0, 2.6)], 0.0035, 4.6, t, sr)
    bow = np.random.default_rng(int(freq * 7)).standard_normal(nsamp).astype(np.float32)
    from scipy.signal import lfilter
    bow = lfilter([0.08], [1, -0.92], bow).astype(np.float32) - lfilter([0.08], [1, -0.985], bow).astype(np.float32)
    out += bow * 0.35 * (1 + 0.5 * np.exp(-t * 6))
    e = env(nsamp, a, r, sr) * (1 + 0.1 * np.sin(2 * np.pi * 0.18 * t))
    return out * e * vel

def tanpura_tone(freq, dur, vel=0.3, sr=SR):
    """タンプーラ: 弾いた後に高次倍音が遅れて咲く (ジャワリ) 長い減衰の開放弦"""
    ring = max(dur, 3.5) + 1.5
    nsamp = int(ring * sr); t = np.arange(nsamp, dtype=np.float32) / sr
    out = np.zeros(nsamp, dtype=np.float32)
    for k in range(1, 24):
        fk = freq * k
        if fk > 9000: break
        bloom = 1 - np.exp(-t * (0.8 + 0.25 * k)) if k > 2 else 1.0
        sweep = np.exp(-((t - 0.25 * k ** 0.5) / (0.8 + 0.1 * k)) ** 2) * 0.6 + 0.4
        out += (1.0 / k ** 0.8) * bloom * sweep * np.sin(2 * np.pi * fk * (1 + 0.0004 * np.sin(2 * np.pi * 0.3 * t)) * t + k)
    out *= np.exp(-t * 0.55)
    out[:int(0.004 * sr)] *= np.linspace(0, 1, int(0.004 * sr))
    return out * vel * 0.35

def bansuri_tone(freq, dur, vel=0.4, sr=SR):
    """バンスリ (竹の横笛): 下から滑り上がる音の入り (ミーンド)、息の雑音、遅れて掛かるビブラート"""
    a, r = 0.12, 0.3
    nsamp = int((dur + r) * sr); t = np.arange(nsamp, dtype=np.float32) / sr
    glide = 2 ** ((-120.0 * np.exp(-t / 0.09)) / 1200.0)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.0 * t) * np.clip((t - 0.35) / 0.5, 0, 1)
    phase = np.cumsum(freq * glide * vib / sr)
    tab = _table('bn', 6, 2.1)
    out = np.interp((phase % 1.0) * 4096, np.arange(4097), tab).astype(np.float32)
    from scipy.signal import lfilter
    br = np.random.default_rng(int(freq)).standard_normal(nsamp).astype(np.float32)
    br = lfilter([0.25], [1, -0.75], br).astype(np.float32)
    out += br * (0.07 + 0.08 * np.exp(-t * 8))
    return out * env(nsamp, a, r, sr) * vel

def heart_tone(freq, kind='lub', vel=1.0, sr=SR):
    """心音: lub = I 音 (僧帽弁・三尖弁が閉じる「ドッ」— 低く長く、22 ms 後に 2 つ目の弁の山)、
    dub = II 音 (大動脈弁・肺動脈弁の「クン」— 短く明るい)。音高は freq (和音の低音 / 5 度)。"""
    lub = kind == 'lub'
    nsamp = int((0.34 if lub else 0.22) * sr); t = np.arange(nsamp, dtype=np.float32) / sr
    f = freq * (1 + (0.45 if lub else 0.3) * np.exp(-t * 35))
    ph = 2 * np.pi * np.cumsum(f) / sr
    body = np.sin(ph) + 0.5 * np.sin(2 * ph + 0.4) + (0.2 if lub else 0.32) * np.sin(3 * ph + 0.9)
    e = (1 - np.exp(-t / 0.005)) * np.exp(-t / (0.06 if lub else 0.036))
    if lub:
        t2 = np.clip(t - 0.022, 0, None)
        e += 0.5 * (t > 0.022) * (1 - np.exp(-t2 / 0.005)) * np.exp(-t2 / 0.05)
    from scipy.signal import lfilter
    nz = np.random.default_rng(17 if lub else 23).standard_normal(nsamp).astype(np.float32)
    nz = lfilter([0.06], [1, -0.94], nz).astype(np.float32) * np.exp(-t / 0.014) * (2.2 if lub else 1.4)
    y = np.tanh(1.6 * (body * e + nz)) / np.tanh(1.6)
    return y.astype(np.float32) * vel

def _noise(n, seed):
    return np.random.default_rng(seed).standard_normal(n).astype(np.float32)

def _lp(x, a):
    from scipy.signal import lfilter
    return lfilter([a], [1, -(1 - a)], x).astype(np.float32)

def rock_drum(kind, vel=0.8, freq=110.0, sr=SR):
    """ロックのドラム: kick / snare / hatc / hato / crash / ride / tom (freq が音高)"""
    if kind == 'kick':
        n = int(0.45 * sr); t = np.arange(n, dtype=np.float32) / sr
        f = 48 + 110 * np.exp(-t * 32)
        y = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t * 7.5)
        y += 0.35 * _lp(_noise(n, 1), 0.25) * np.exp(-t * 180)                 # ビーターのアタック
        y = np.tanh(1.8 * y) / np.tanh(1.8)
    elif kind == 'snare':
        n = int(0.4 * sr); t = np.arange(n, dtype=np.float32) / sr
        body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 24) + 0.5 * np.sin(2 * np.pi * 330 * t) * np.exp(-t * 30)
        nz = _noise(n, 2); nz = nz - _lp(nz, 0.08)                              # 高域のスナッピー
        y = 0.7 * body + 0.9 * nz * np.exp(-t * 16)
    elif kind in ('hatc', 'hato', 'ride', 'crash'):
        dur, dec = {'hatc': (0.08, 60), 'hato': (0.45, 7), 'ride': (1.2, 3.2), 'crash': (2.6, 1.3)}[kind]
        n = int(dur * sr); t = np.arange(n, dtype=np.float32) / sr
        metal = sum(np.sign(np.sin(2 * np.pi * f0 * t + i)) for i, f0 in enumerate((205.3, 304.4, 369.6, 522.7, 540.0, 800.0)))
        nz = _noise(n, 3 if kind != 'crash' else 4)
        y = 0.25 * metal + (0.8 if kind == 'crash' else 0.5) * nz
        y = y - _lp(y, 0.35 if kind != 'ride' else 0.2)                         # 金属音は高域だけ
        if kind == 'ride': y += 0.4 * np.sin(2 * np.pi * 3100 * t) * np.exp(-t * 2)
        y *= np.exp(-t * dec) * (1 - np.exp(-t / 0.001))
        if kind == 'crash': y *= 1.2
    else:                                                                      # tom
        n = int(0.6 * sr); t = np.arange(n, dtype=np.float32) / sr
        f = freq * (1 + 0.35 * np.exp(-t * 25))
        y = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t * 6) + 0.2 * _lp(_noise(n, 5), 0.3) * np.exp(-t * 60)
        y = np.tanh(1.4 * y)
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32) * vel

def synth_bass(freq, dur, vel=0.6, sr=SR):
    """シンセ・ベース: 鋸歯波 2 本 + 矩形の低音、フィルターが開いてすぐ閉じる。キックに合わせて頭を少し沈める (ポンピング)"""
    n = int((dur + 0.08) * sr); t = np.arange(n, dtype=np.float32) / sr
    tab = _table('saw', 24, 1.0)
    bright = _wavetable_voice(freq, n, tab, [(0.0, 0.0), (9.0, 1.0)], 0.0, 0.0, t, sr)
    sub = np.sign(np.sin(2 * np.pi * freq / 2 * t)) * 0.35
    dark = _lp(bright, 0.06)
    y = dark + (bright - dark) * np.exp(-t / 0.07) + _lp(sub, 0.05)
    pump = 0.35 + 0.65 * np.clip(t / 0.06, 0, 1) ** 1.5
    return y * env(n, 0.004, 0.08, sr) * pump * vel

def arp_pluck(freq, dur, vel=0.4, sr=SR):
    """アルペジオのシンセ: 鋸歯波 + 矩形波、明るい立ち上がりからすぐ暗くなる短い音"""
    n = int((min(dur, 0.35) + 0.25) * sr); t = np.arange(n, dtype=np.float32) / sr
    y = _wavetable_voice(freq, n, _table('saw', 18, 1.0), [(0.0, 0.0), (-7.0, 1.3)], 0.0, 0.0, t, sr)
    y += 0.4 * np.sign(np.sin(2 * np.pi * freq * 1.002 * t))
    dark = _lp(y, 0.08)
    y = (dark + (y - dark) * np.exp(-t / 0.05)) * np.exp(-t / 0.18)
    y[:int(0.002 * sr)] *= np.linspace(0, 1, int(0.002 * sr))
    return y * vel

def guitar_power(freq, dur, vel=0.5, mute=True, sr=SR):
    """歪んだギターのパワーコード (根音 + 5 度 + オクターヴ)。mute=True はブリッジ・ミュートの刻み"""
    n = int((dur + (0.06 if mute else 0.6)) * sr); t = np.arange(n, dtype=np.float32) / sr
    tab = _table('saw', 30, 1.0)
    y = sum(_wavetable_voice(freq * r, n, tab, [(0.0, 0.0), (8.0, 1.0)], 0.002, 5.0, t, sr) * a for r, a in ((1, 1.0), (1.5, 0.8), (2, 0.6)))
    y *= np.exp(-t / (0.09 if mute else 1.4))
    y = np.tanh(7.0 * y)                                                        # 歪み
    y = _lp(y, 0.35); y = _lp(y, 0.45); y = y - _lp(y, 0.012)                  # キャビネット
    return y * env(n, 0.003, 0.05, sr) * vel

_BEAT_GRID = (np.array([0.0, 1e6]), np.array([0.0, 1e6]))       # (時刻, 拍) — main() がスコアのテンポ・マップで置き換える
def beat_of(t):
    return np.interp(t, _BEAT_GRID[0], _BEAT_GRID[1])

def formant_log2(beats):
    """倍音を鳴らす共鳴の中心 (log2 Hz): 2 小節で 300 Hz → 3000 Hz → 300 Hz とゆっくり往復 (拍に同期)"""
    return np.log2(300.0) + 3.3 * (0.5 - 0.5 * np.cos(2 * np.pi * beats / 8.0))

def overtone_tone(freq, dur, vel, t0, kmax=28, a=0.12, r=0.7, sr=SR):
    """倍音シンセ: 倍音列を加算合成し、狭い共鳴 (倍音唱法のように) が倍音を 1 本ずつ鳴らしながら上下する"""
    n = int((dur + r) * sr); t = np.arange(n, dtype=np.float32) / sr
    L = formant_log2(beat_of(t0 + t)).astype(np.float32)
    vib = 1 + 0.0025 * np.sin(2 * np.pi * 4.6 * t) * np.clip((t - 0.3) / 0.6, 0, 1)
    ph = (2 * np.pi * freq * np.cumsum(vib) / sr).astype(np.float32)
    out = np.zeros(n, dtype=np.float32); K = max(4, min(kmax, int(7500.0 / freq)))
    for k in range(1, K + 1):
        w = k ** -0.7 * (0.12 + 1.9 * np.exp(-((np.float32(math.log2(k * freq)) - L) / 0.17) ** 2))
        out += w * np.sin(k * ph + 0.7 * k)
    return out * env(n, a, r, sr) * vel / 2.2

_BANK = {'samples': [], 'audio': {}}
def load_bank(path):
    """build_sampler.py が作った録音の 1 音サンプル集"""
    _BANK['samples'] = json.load(open(path))['samples']; _BANK['audio'] = {}

def sampler_tone(midi, dur, vel, rid, rel=0.35, sr=SR):
    """実録音の音で鳴らす: いちばん近い音高の録音の 1 音 (できればその区間の録音) を移調し、
    長い音は持続部をクロスフェードでループして伸ばす"""
    cands = [c for c in _BANK['samples'] if c['rid'] == 'VOX'] if rid == 'VOX' else [c for c in _BANK['samples'] if c['rid'] != 'VOX']
    cands = cands or _BANK['samples']                     # 'VOX' = 歌声のサンプルだけから選ぶ
    s = min(cands, key=lambda c: abs(c['midi'] - midi) + (0.0 if c['rid'] == rid else 2.5) - 0.02 * c['purity'])
    if s['file'] not in _BANK['audio']: _BANK['audio'][s['file']] = sf.read(s['file'], dtype='float32')[0]
    src = _BANK['audio'][s['file']]
    ratio = 2 ** ((midi - s['midi']) / 12.0)
    n_out = int((dur + rel) * sr); need = int(n_out * ratio) + 4
    ext = src
    if len(ext) < need:                                   # 持続部 (30%〜90%) をクロスフェードでつないで伸ばす
        a, b = int(0.3 * len(src)), int(0.9 * len(src)); loop = src[a:b]; xf = min(int(0.06 * sr), len(loop) // 3)
        fade = np.linspace(0, 1, xf, dtype=np.float32); ext = src[:b].copy()
        while len(ext) < need:
            ext = np.concatenate([ext[:-xf], ext[-xf:] * (1 - fade) + loop[:xf] * fade, loop[xf:]])
    y = np.interp(np.arange(n_out) * ratio, np.arange(len(ext)), ext).astype(np.float32)
    i0 = int(dur * sr); t = np.arange(n_out - i0, dtype=np.float32) / sr
    y[i0:] *= np.exp(-t / (rel / 3))
    y[:int(0.004 * sr)] *= np.linspace(0, 1, int(0.004 * sr))
    return y * vel

_SAMPLES = {}
def sample_clip(path, off, dur, sr=SR, fin=0.03, fout=None):
    """録音の抜粋: 60 Hz 以下と 8 kHz 以上を落とし、入りと終わりをフェード"""
    if path not in _SAMPLES:
        y, fs = sf.read(path, dtype='float32')
        if y.ndim == 2: y = y.mean(axis=1)
        if fs != sr:
            from scipy.signal import resample_poly
            y = resample_poly(y, sr, fs).astype(np.float32)
        from scipy.signal import butter, sosfilt
        y = sosfilt(butter(2, [60.0, 8000.0], btype='bandpass', fs=sr, output='sos'), y).astype(np.float32)
        _SAMPLES[path] = y / (np.sqrt((y ** 2).mean()) + 1e-9) * 0.1
    y = _SAMPLES[path][int(off * sr):int((off + dur) * sr)].copy()
    fi, fo = int(min(fin, dur / 3) * sr), int((min(1.5, dur / 4) if fout is None else min(fout, dur / 2)) * sr)
    y[:fi] *= np.linspace(0, 1, fi); y[-fo:] *= np.linspace(1, 0, fo)
    return y

def drone_tone(freq, dur, sr=SR):
    a, r = 2.5, 3.0
    nsamp = int((dur + r) * sr)
    t = np.arange(nsamp, dtype=np.float32) / sr
    out = np.zeros(nsamp, dtype=np.float32)
    lfo = 1 + 0.25 * np.sin(2 * np.pi * 0.09 * t) + 0.1 * np.sin(2 * np.pi * 0.23 * t + 1.0)
    for k, amp in ((1, .5), (2, 1.0), (3, .45), (4, .3), (5, .18), (6, .12), (8, .07)):
        det = 1 + 0.0008 * np.sin(2 * np.pi * 0.05 * k * t)
        out += amp * np.sin(2 * np.pi * freq * k * det * t)
    out *= lfo
    e = env(nsamp, a, r, sr)
    return out * e

def piano_tone(freq, dur, vel=0.6, pedal=1.4, sr=SR, soft=False):
    """グランドピアノ風: 非整数倍音 (弦の剛性 B)、倍音ごとの減衰、2 本弦のうなり、ハンマー雑音、ペダル残響
    soft=True: 高音が木琴に聞こえないよう、打鍵雑音を抑え、減衰を長く、倍音を控えめにする"""
    rel = pedal
    nsamp = int((dur + rel) * sr)
    t = np.arange(nsamp, dtype=np.float32) / sr
    B = 0.00025 + 0.0006 * (freq / 1000.0)            # 高音ほど剛性の影響が大きい
    bright = 1.05 + 0.9 * (1.0 - vel) + (0.6 if soft else 0.0)   # 弱打ほど倍音が少ない
    d0 = (0.35 + 0.9 * (freq / 440.0) ** 0.6) * (0.55 if soft else 1.0)   # 基本減衰 (低音は長く鳴る)
    out = np.zeros(nsamp, dtype=np.float32)
    nparts = int(min(40, 7000.0 / freq))
    for k in range(1, max(2, nparts) + 1):
        fk = freq * k * math.sqrt(1 + B * k * k)
        if fk > sr * 0.45: break
        amp = 1.0 / (k ** bright)
        if k == 1: amp *= 1.0
        dk = d0 * (1 + 0.12 * k * k) ** 0.5
        # 二段減衰: 立ち上がり直後に速く落ち、その後ゆっくり
        e = 0.55 * np.exp(-t * dk * 3.2) + 0.45 * np.exp(-t * dk)
        det = 1.0 + (0.0012 if (k % 2 == 0 and freq > 130) else 0.0)
        out += amp * e * (np.sin(2 * np.pi * fk * t) + (0.55 * np.sin(2 * np.pi * fk * det * t + 0.9) if freq > 130 else 0.0))
    # ハンマー雑音 (5 ms) と胴鳴り
    nh = int(0.006 * sr)
    out[:nh] += np.random.default_rng(int(freq)).standard_normal(nh).astype(np.float32) * np.linspace(1, 0, nh) * (0.08 if soft else 0.35) * vel
    if freq < 200:
        out += 0.25 * np.sin(2 * np.pi * freq * 0.5 * t) * np.exp(-t * 2.5)
    # 鍵を離す: ペダルで長めに減衰
    key = np.ones(nsamp, dtype=np.float32)
    i0 = int(dur * sr)
    if i0 < nsamp:
        key[i0:] = np.exp(-(t[i0:] - t[i0]) / (rel * 0.35))
    att = int((0.012 if soft else 0.0025) * sr)
    key[:att] *= np.linspace(0, 1, att) ** 0.5
    return out * key * (0.35 + 0.65 * vel)

def main(score='score.json', out='fuga.wav'):
    d = json.load(open(score))
    base_dir = os.path.dirname(os.path.abspath(score))
    total = d['duration'] + (7.0 if d.get('meta', {}).get('style') in ('requiem', 'piano', 'mallet', 'grief', 'elegia', 'concerto', 'symphony', 'pconcerto', 'sweet', 'acceptance', 'heart', 'rock', 'mantra', 'arrhythmia', 'recsampler') else 4.0)
    N = int(total * SR)
    L = np.zeros(N, dtype=np.float32); R = np.zeros(N, dtype=np.float32)
    HL = np.zeros(N, dtype=np.float32); HR = np.zeros(N, dtype=np.float32)   # 鼓動 (ほぼ乾いた音で近くに)
    rng = np.random.default_rng(3)
    style = d.get('meta', {}).get('style', 'organ')
    requiem = style in ('requiem', 'heart', 'rock', 'arrhythmia')
    symphony = style == 'symphony'
    pconcerto = style == 'pconcerto'
    piano = style in ('piano', 'mallet', 'grief', 'elegia', 'concerto', 'pconcerto', 'sweet', 'acceptance')
    mallet = style == 'mallet'
    grief = style == 'grief'
    elegia = style in ('elegia', 'concerto', 'pconcerto', 'acceptance')
    concerto = style == 'concerto'
    sweet = style == 'sweet'
    acc = style == 'acceptance'
    mantra = style == 'mantra'
    recs = style == 'recsampler'
    if recs: load_bank(d['meta']['bank'])
    global _BEAT_GRID
    if d.get('bar_times'):
        bts = np.array(d['bar_times']); nb = len(bts) - 1
        _BEAT_GRID = (np.concatenate([np.linspace(bts[i], bts[i + 1], BPB_S, endpoint=False) for i in range(nb)] + [bts[-1:]]), np.arange(nb * BPB_S + 1, dtype=float))
    detach = d.get('meta', {}).get('detach', 1.0)
    humanize = bool(d.get('meta', {}).get('humanize', False))
    spb = 60.0 / d['bpm']
    VORD = {'B': 0, 'T': 1, 'A': 2, 'S': 3}
    global VOWEL
    VOWEL = d.get('meta', {}).get('vowel', 'a')
    for nt in d['notes']:
        tb = TIMBRE[nt['v']]
        freq = 440.0 * 2 ** ((nt['m'] - 69) / 12.0)
        dur = max(nt['d'] - 0.035, 0.06)
        t_off = 0.0
        role = nt.get('role', '')
        if symphony or (pconcerto and role in ('tutti', 'both')) or (acc and role in ('str', 'both')):
            # 弦 5 部: S→Vn I, A→Vn II, T→Va, B→Vc (+Cb 1 オクターヴ下)
            dyn = nt.get('dyn', 1.0); det = nt.get('det', 1.0)
            vel = min(1.0, 0.5 * (1.15 if nt['label'] else 1.0) * dyn + 0.05)
            if acc and role == 'both': vel *= 0.7
            dd = max(0.12, nt['d'] * det)
            dark = {'S': 0.0, 'A': 0.15, 'T': 0.45, 'B': 0.75}[nt['v']]
            y = string_tone(freq, dd, vel, dark=dark)
            if det < 0.8:   # スタッカート気味: 立ち上がりを速く
                y = y * np.minimum(1.0, np.arange(len(y)) / (0.04 * SR))
            t_off = 0.012 * VORD[nt['v']] + rng.uniform(-0.006, 0.006)
            g = 0.85
            pan = {'S': -0.45, 'A': -0.2, 'T': 0.15, 'B': 0.4}[nt['v']]
            i0 = max(0, int((nt['t'] + t_off) * SR)); i1 = min(i0 + len(y), N)
            L[i0:i1] += y[:i1 - i0] * g * math.cos((pan + 1) * math.pi / 4); R[i0:i1] += y[:i1 - i0] * g * math.sin((pan + 1) * math.pi / 4)
            if nt['v'] == 'B':
                if acc: yb = contrabass_tone(freq / 2 if freq / 2 >= 41.0 else freq, dd, vel * 0.9)
                else: yb = string_tone(freq / 2, dd, vel * 0.8, dark=1.0)
                i1 = min(i0 + len(yb), N)
                L[i0:i1] += yb[:i1 - i0] * g * 0.5; R[i0:i1] += yb[:i1 - i0] * g * 0.85
            if not ((pconcerto or acc) and role == 'both'): continue
        if pconcerto and role == 'tutti': continue
        if recs:
            vel = 0.55 * (1.15 if nt['label'] else 1.0) * nt.get('dyn', 1.0)
            y = sampler_tone(nt['m'], max(0.2, nt['d'] * 0.97), vel, nt.get('src', ''))
            if nt['v'] == 'B':                                    # 低音は 1 オクターヴ下の柔らかい正弦波で支える
                tt = np.arange(len(y), dtype=np.float32) / SR
                y = y + 0.35 * vel * np.sin(2 * np.pi * freq / 2 * tt) * np.minimum(1, tt / 0.05) * np.minimum(1, np.maximum(0, (nt['d'] + 0.3 - tt) / 0.3))
        elif mantra:
            vel = 0.5 * (1.15 if nt['label'] else 1.0) * nt.get('dyn', 1.0)
            y = overtone_tone(freq, dur + 0.08, vel, nt['t'])
        elif piano:
            vel = min(1.0, 0.62 * (1.12 if nt['label'] else 1.0) * nt.get('dyn', 1.0) + 0.08)
            if humanize:
                # ルバート: 小節内の位置で強弱の起伏、声部ごとの打鍵の時間差 (低音が先)、強拍はわずかに遅れる
                pos = (nt['beat'] % 4) / 4.0
                vel *= 0.9 + 0.12 * math.sin(math.pi * pos + 0.3) * (1.0 if nt['v'] in 'SB' else 0.6)
                if nt['v'] in 'AT' and not nt['label']: vel *= 0.85           # 内声は控えめ
                t_off = 0.016 * VORD[nt['v']] + (0.03 if (nt['beat'] % 4) == 0 else 0.0) + rng.uniform(-0.008, 0.008)
            # 音符の長さを detach 倍に (elegia は 0.92: ほぼレガート、ペダル長め)
            y = piano_tone(freq, max(0.18, nt['d'] * detach), vel, pedal=(0.7 if grief else (1.9 if elegia else 1.4)), soft=(elegia and freq > 700))
        elif requiem:
            # 合唱 (フォルマント) + オルガンの混合。長い音ほど合唱が前へ
            y = tone(freq, dur, tb) * 0.45
            yc = choir_tone(freq, dur + 0.05)
            m = min(len(y), len(yc)); y = y[:m] + yc[:m] * 0.85
        else:
            y = tone(freq, dur, tb)
        # 主題の音は少し強く
        g = tb['g'] * (1.18 if nt['label'] else 1.0) * (1.0 + 0.04 * rng.standard_normal()) * nt.get('dyn', 1.0)
        if piano: g = 0.9 * (1.0 + 0.03 * rng.standard_normal())
        # 高音域は少し控えめに
        g *= min(1.0, (72.0 / max(freq, 72.0)) ** 0.25)
        i0 = max(0, int((nt['t'] + t_off) * SR)); i1 = min(i0 + len(y), N)
        pan = tb['pan'] if not piano else max(-0.6, min(0.6, (nt['m'] - 60) / 40.0))
        L[i0:i1] += y[:i1 - i0] * g * math.cos((pan + 1) * math.pi / 4)
        R[i0:i1] += y[:i1 - i0] * g * math.sin((pan + 1) * math.pi / 4)
    # 鐘・ドローン
    for ex in d.get('extras', []):
        freq = 440.0 * 2 ** ((ex['m'] - 69) / 12.0)
        if (concerto or symphony or pconcerto) and ex['v'] in ('V1', 'V2', 'VA', 'VC', 'CB', 'WW', 'FL', 'HN', 'TP', 'TR', 'TB', 'CL'):
            v = ex['v']; vel = ex.get('gain', 0.4)
            if v in ('V1', 'V2'): y = string_tone(freq, ex['d'], vel, dark=0.0)
            elif v == 'VA': y = string_tone(freq, ex['d'], vel, dark=0.4)
            elif v == 'VC': y = string_tone(freq, ex['d'], vel, dark=0.7)
            elif v == 'CB': y = string_tone(freq, ex['d'], vel * 0.9, dark=1.0)
            elif v == 'WW': y = wind_tone(freq, ex['d'], vel, 'oboe')
            elif v == 'FL': y = wind_tone(freq, ex['d'], vel, 'flute')
            elif v == 'HN': y = horn_tone(freq, ex['d'], vel)
            elif v == 'TR': y = brass_tone(freq, ex['d'], vel, 'trumpet')
            elif v == 'TB': y = brass_tone(freq, ex['d'], vel, 'trombone')
            elif v == 'CL': y = clarinet_tone(freq, ex['d'], vel)
            else: y = timp_tone(freq, ex['d'], vel)
            pan = {'V1': -0.45, 'V2': -0.25, 'VA': 0.15, 'VC': 0.35, 'CB': 0.5, 'WW': 0.1, 'FL': -0.1, 'HN': 0.3, 'TP': 0.2, 'TR': 0.35, 'TB': 0.45, 'CL': -0.05}[v]
            i0 = int(ex['t'] * SR); i1 = min(i0 + len(y), N)
            L[i0:i1] += y[:i1 - i0] * math.cos((pan + 1) * math.pi / 4); R[i0:i1] += y[:i1 - i0] * math.sin((pan + 1) * math.pi / 4)
            continue
        if ex['v'] in ('DR', 'SB', 'AR', 'GT'):                  # ロックバンド + シンセ (乾いた音で前に、少しだけ響きへ)
            v = ex['v']; vel = ex.get('gain', 0.6)
            if v == 'DR': y = rock_drum(ex.get('kind', 'kick'), vel, freq)
            elif v == 'SB': y = synth_bass(freq, ex['d'], vel)
            elif v == 'AR': y = arp_pluck(freq, ex['d'], vel)
            else: y = guitar_power(freq, ex['d'], vel, mute=ex.get('mute', True))
            y = y * d.get('meta', {}).get('band_gain', 1.0)
            pan = ex.get('pan', 0.0); send = {'DR': 0.18, 'SB': 0.05, 'AR': 0.35, 'GT': 0.2}[v]
            cl, cr = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
            i0 = int(ex['t'] * SR); i1 = min(i0 + len(y), N)
            HL[i0:i1] += y[:i1 - i0] * cl; HR[i0:i1] += y[:i1 - i0] * cr
            L[i0:i1] += y[:i1 - i0] * cl * send; R[i0:i1] += y[:i1 - i0] * cr * send
            continue
        if ex['v'] == 'OD':                                      # 倍音ドローン: 低い D の倍音が共鳴に合わせて 1 本ずつ鳴り響く
            y = overtone_tone(freq, ex['d'], ex.get('gain', 0.5), ex['t'], kmax=90, a=2.5, r=4.0)
            i0 = int(ex['t'] * SR); i1 = min(i0 + len(y), N)
            L[i0:i1] += y[:i1 - i0] * 0.707; R[i0:i1] += y[:i1 - i0] * 0.707
            continue
        if ex['v'] == 'PD' and style == 'rock':
            y = pad_tone(freq, ex['d'], ex.get('gain', 0.2)); i0 = int(ex['t'] * SR); i1 = min(i0 + len(y), N)
            L[i0:i1] += y[:i1 - i0] * 0.707; R[i0:i1] += y[:i1 - i0] * 0.707
            continue
        if ex['v'] == 'HB':
            y = heart_tone(freq, ex.get('kind', 'lub'), ex.get('gain', 1.0)) * d.get('meta', {}).get('heart_gain', 1.0)
            i0 = int(ex['t'] * SR); i1 = min(i0 + len(y), N)
            HL[i0:i1] += y[:i1 - i0] * 0.707; HR[i0:i1] += y[:i1 - i0] * 0.707
            L[i0:i1] += y[:i1 - i0] * 0.12; R[i0:i1] += y[:i1 - i0] * 0.12       # わずかに響きへ
            continue
        if recs and ex['v'] == 'PF':                        # 実録音の音のピアノ (音域で左右に振る)
            y = sampler_tone(ex['m'], max(0.08, ex['d']), ex.get('gain', 0.3), ex.get('rid', ''), rel=ex.get('rel', 0.35))
            pan = max(-0.6, min(0.6, (ex['m'] - 62) / 40.0))
            i0 = int(ex['t'] * SR); i1 = min(i0 + len(y), N)
            L[i0:i1] += y[:i1 - i0] * math.cos((pan + 1) * math.pi / 4); R[i0:i1] += y[:i1 - i0] * math.sin((pan + 1) * math.pi / 4)
            continue
        if recs and ex['v'] in ('OS', 'DN', 'PK'):          # 実録音の音のオスティナート・持続音・鼓動
            v = ex['v']; vel = ex.get('gain', 0.4)
            if v == 'PK':                                   # 鼓動: 録音の低い打鍵を 2 オクターヴ下げ、低域だけ残す
                y = sampler_tone(ex['m'], 0.3, 1.0, ex.get('rid', ''), rel=0.3)
                from scipy.signal import butter, sosfilt
                y = sosfilt(butter(4, 160.0, btype='lowpass', fs=SR, output='sos'), y).astype(np.float32)
                y = y / (np.abs(y).max() + 1e-9) * vel
                i0 = int(ex['t'] * SR); i1 = min(i0 + len(y), N)
                HL[i0:i1] += y[:i1 - i0] * 0.707; HR[i0:i1] += y[:i1 - i0] * 0.707
                L[i0:i1] += y[:i1 - i0] * 0.1; R[i0:i1] += y[:i1 - i0] * 0.1
                continue
            if v == 'DN':                                   # 持続音: 打鍵を消して (ゆっくり立ち上げ) ループで伸ばす
                y = sampler_tone(ex['m'], ex['d'], vel, ex.get('rid', ''), rel=2.0)
                y[:int(1.2 * SR)] *= np.linspace(0, 1, int(1.2 * SR)) ** 2; pan = 0.0
            else:
                y = sampler_tone(ex['m'], ex['d'], vel, ex.get('rid', ''), rel=0.5)
                pan = 0.35 if int(round(ex['beat'] * 2)) % 2 else -0.35
            i0 = int(ex['t'] * SR); i1 = min(i0 + len(y), N)
            L[i0:i1] += y[:i1 - i0] * math.cos((pan + 1) * math.pi / 4); R[i0:i1] += y[:i1 - i0] * math.sin((pan + 1) * math.pi / 4)
            continue
        if ex['v'] == 'TB': continue                  # 採譜した録音の音 (表示用・無音)
        if ex['v'] == 'REC':
            ratio = 2 ** (ex.get('semis', 0) / 12.0)            # 移調はテープのように速さごと変える
            y = sample_clip(os.path.join(base_dir, ex['src']), ex['off'], ex['d'] * ratio, fin=ex.get('fin', 0.03), fout=ex.get('fout')) * ex.get('gain', 1.0)
            if ratio != 1.0: y = np.interp(np.arange(int(len(y) / ratio)) * ratio, np.arange(len(y)), y).astype(np.float32)
            if ex.get('pshift'):                            # 速さを変えない移調 (歌声)
                import librosa
                y = librosa.effects.pitch_shift(y, sr=SR, n_steps=ex['pshift']).astype(np.float32)
            i0 = int(ex['t'] * SR); i1 = min(i0 + len(y), N); dl = int(0.009 * SR)
            L[i0:i1] += y[:i1 - i0] * 0.707
            j0 = min(i0 + dl, N); j1 = min(j0 + len(y), N); R[j0:j1] += y[:j1 - j0] * 0.707
            continue
        if acc and ex['v'] in ('CB', 'CBP', 'TA', 'BN', 'V1', 'V2', 'VA', 'VC', 'WW', 'FL', 'PD'):
            v = ex['v']; vel = ex.get('gain', 0.4)
            if v == 'CB': y = contrabass_tone(freq, ex['d'], vel)
            elif v == 'CBP': y = contrabass_tone(freq, ex['d'], vel, pizz=True)
            elif v == 'TA': y = tanpura_tone(freq, ex['d'], vel)
            elif v == 'BN': y = bansuri_tone(freq, ex['d'], vel)
            elif v in ('V1', 'V2'): y = string_tone(freq, ex['d'], vel, dark=0.0)
            elif v == 'VA': y = string_tone(freq, ex['d'], vel, dark=0.4)
            elif v == 'VC': y = string_tone(freq, ex['d'], vel, dark=0.7)
            elif v == 'WW': y = wind_tone(freq, ex['d'], vel, 'oboe')
            elif v == 'FL': y = wind_tone(freq, ex['d'], vel, 'flute')
            else: y = pad_tone(freq, ex['d'], vel)
            pan = {'CB': 0.3, 'CBP': 0.3, 'TA': -0.3, 'BN': -0.15, 'V1': -0.45, 'V2': -0.25, 'VA': 0.15, 'VC': 0.35, 'WW': 0.1, 'FL': -0.1, 'PD': 0.0}[v]
            i0 = int(ex['t'] * SR); i1 = min(i0 + len(y), N)
            L[i0:i1] += y[:i1 - i0] * math.cos((pan + 1) * math.pi / 4); R[i0:i1] += y[:i1 - i0] * math.sin((pan + 1) * math.pi / 4)
            continue
        if sweet and ex['v'] in ('EP', 'PD', 'LD', 'DR', 'V1', 'V2', 'VA', 'VC', 'WW', 'FL'):
            v = ex['v']; vel = ex.get('gain', 0.4)
            if v == 'EP': y = ep_tone(freq, ex['d'], vel)
            elif v == 'PD': y = pad_tone(freq, ex['d'], vel)
            elif v == 'LD': y = lead_tone(freq, ex['d'], vel)
            elif v == 'DR': y = drum_brush(ex['m'], ex['d'], vel)
            elif v in ('V1', 'V2'): y = string_tone(freq, ex['d'], vel, dark=0.0)
            elif v == 'VA': y = string_tone(freq, ex['d'], vel, dark=0.4)
            elif v == 'VC': y = string_tone(freq, ex['d'], vel, dark=0.7)
            elif v == 'WW': y = wind_tone(freq, ex['d'], vel, 'oboe')
            elif v == 'FL': y = wind_tone(freq, ex['d'], vel, 'flute')
            else: continue
            pan = {'EP': 0.25, 'PD': 0.0, 'LD': -0.2, 'DR': 0.0, 'V1': -0.45, 'V2': -0.25, 'VA': 0.15, 'VC': 0.35, 'WW': 0.1, 'FL': -0.1}.get(v, 0.0)
            if v == 'DR': pan = {36: 0.0, 38: -0.1, 42: 0.15, 46: 0.2}.get(ex['m'], 0.0)
            i0 = int(ex['t'] * SR); i1 = min(i0 + len(y), N)
            L[i0:i1] += y[:i1 - i0] * math.cos((pan + 1) * math.pi / 4); R[i0:i1] += y[:i1 - i0] * math.sin((pan + 1) * math.pi / 4)
            continue
        if ex['v'] == 'C':
            y = cluster_tone(freq, ex['d'], ex.get('gain', 0.3)); pan = 0.25 * math.sin(ex['m'])
            i0 = int(ex['t'] * SR); i1 = min(i0 + len(y), N)
            L[i0:i1] += y[:i1 - i0] * math.cos((pan + 1) * math.pi / 4); R[i0:i1] += y[:i1 - i0] * math.sin((pan + 1) * math.pi / 4)
            continue
        if ex['v'] in ('H', 'W', 'L'):
            vel = ex.get('gain', 0.5)
            if grief or elegia: ex = dict(ex, d=max(0.18, ex['d'] * detach))
            if elegia:
                y = piano_tone(freq, ex['d'], vel, pedal=2.4, soft=(ex['v'] == 'H')) * 0.9
            elif mallet and ex['v'] in ('H', 'W'):
                y = mallet_tone(freq, ex['d'], vel, bright=(ex['v'] == 'H')) * (1.1 if ex['v'] == 'H' else 0.9)
            else:
                y = piano_tone(freq, ex['d'], vel, pedal=(0.7 if grief else (2.2 if ex['v'] == 'H' else 1.4))) * 0.9
            pan = {'H': 0.35, 'W': 0.1, 'L': -0.35}[ex['v']]
            i0 = int(ex['t'] * SR); i1 = min(i0 + len(y), N)
            L[i0:i1] += y[:i1 - i0] * math.cos((pan + 1) * math.pi / 4); R[i0:i1] += y[:i1 - i0] * math.sin((pan + 1) * math.pi / 4)
            continue
        if ex['v'] == 'X':
            y = bell_tone(freq, ex['d'] + 3.0) * 0.55 * ex.get('gain', 1.0); pan = 0.0
        elif ex['v'] == 'P':
            y = pulse_tone() * 0.9 * ex.get('gain', 1.0)
        else:
            y = drone_tone(freq, ex['d']) * 0.30 * ex.get('gain', 1.0); pan = 0.0
        i0 = int(ex['t'] * SR); i1 = min(i0 + len(y), N)
        L[i0:i1] += y[:i1 - i0] * 0.707; R[i0:i1] += y[:i1 - i0] * 0.707
    # 合成リバーブ (指数減衰ノイズ, ローパス)
    rv_len, rv_decay, wet = (4.2, 1.4, 0.36) if recs else (5.0, 1.7, 0.46) if mantra else (4.4, 1.45, 0.40) if acc else (4.2, 1.35, 0.42) if requiem else ((4.6, 1.5, 0.42) if grief else ((3.6, 1.15, 0.34) if mallet else ((3.8, 1.2, 0.36) if (concerto or symphony or pconcerto or sweet) else ((3.4, 1.05, 0.30) if elegia else ((3.0, 0.9, 0.26) if piano else (2.2, 0.75, 0.30))))))
    ir_len = int(rv_len * SR)
    t = np.arange(ir_len) / SR
    def make_ir(seed):
        r = np.random.default_rng(seed).standard_normal(ir_len).astype(np.float32)
        r *= np.exp(-t / rv_decay)
        # simple one-pole lowpass
        from scipy.signal import lfilter
        a = 0.35; y = lfilter([a], [1, -(1 - a)], r).astype(np.float32)
        y[:int(0.012 * SR)] = 0
        return y / np.sqrt((y ** 2).sum())
    irL, irR = make_ir(11), make_ir(12)
    Lw = fftconvolve(L, irL)[:N].astype(np.float32); Rw = fftconvolve(R, irR)[:N].astype(np.float32)
    mixL = L + wet * Lw * 3.0 + HL; mixR = R + wet * Rw * 3.0 + HR
    st = np.stack([mixL, mixR], axis=1)
    peak = np.abs(st).max()
    st = st / peak * 0.89
    # soft knee
    st = np.tanh(st * 1.15) / np.tanh(1.15)
    # fade out tail
    tail = int((5.0 if (requiem or piano or symphony or mantra or recs) else 2.5) * SR)
    st[-tail:] *= np.linspace(1, 0, tail)[:, None]
    sf.write(out, st, SR, subtype='PCM_16')
    print('wrote', out, '%.1fs' % total, 'peak', peak)

if __name__ == '__main__':
    main(*sys.argv[1:3])
