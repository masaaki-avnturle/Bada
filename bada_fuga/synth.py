#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""score.json -> fuga.wav  (加算合成オルガン風 4 声 + 合成リバーブ)"""
import json, sys, math
import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve

SR = 44100

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
    total = d['duration'] + (7.0 if d.get('meta', {}).get('style') in ('requiem', 'piano', 'mallet', 'grief', 'elegia', 'concerto') else 4.0)
    N = int(total * SR)
    L = np.zeros(N, dtype=np.float32); R = np.zeros(N, dtype=np.float32)
    rng = np.random.default_rng(3)
    style = d.get('meta', {}).get('style', 'organ')
    requiem = style == 'requiem'
    piano = style in ('piano', 'mallet', 'grief', 'elegia', 'concerto')
    mallet = style == 'mallet'
    grief = style == 'grief'
    elegia = style in ('elegia', 'concerto')
    concerto = style == 'concerto'
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
        if piano:
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
        i0 = int((nt['t'] + t_off) * SR); i1 = min(i0 + len(y), N)
        pan = tb['pan'] if not piano else max(-0.6, min(0.6, (nt['m'] - 60) / 40.0))
        L[i0:i1] += y[:i1 - i0] * g * math.cos((pan + 1) * math.pi / 4)
        R[i0:i1] += y[:i1 - i0] * g * math.sin((pan + 1) * math.pi / 4)
    # 鐘・ドローン
    for ex in d.get('extras', []):
        freq = 440.0 * 2 ** ((ex['m'] - 69) / 12.0)
        if concerto and ex['v'] in ('V1', 'V2', 'VA', 'VC', 'CB', 'WW', 'FL', 'HN', 'TP'):
            v = ex['v']; vel = ex.get('gain', 0.4)
            if v in ('V1', 'V2'): y = string_tone(freq, ex['d'], vel, dark=0.0)
            elif v == 'VA': y = string_tone(freq, ex['d'], vel, dark=0.4)
            elif v == 'VC': y = string_tone(freq, ex['d'], vel, dark=0.7)
            elif v == 'CB': y = string_tone(freq, ex['d'], vel * 0.9, dark=1.0)
            elif v == 'WW': y = wind_tone(freq, ex['d'], vel, 'oboe')
            elif v == 'FL': y = wind_tone(freq, ex['d'], vel, 'flute')
            elif v == 'HN': y = horn_tone(freq, ex['d'], vel)
            else: y = timp_tone(freq, ex['d'], vel)
            pan = {'V1': -0.45, 'V2': -0.25, 'VA': 0.15, 'VC': 0.35, 'CB': 0.5, 'WW': 0.1, 'FL': -0.1, 'HN': 0.3, 'TP': 0.2}[v]
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
    rv_len, rv_decay, wet = (4.2, 1.35, 0.42) if requiem else ((4.6, 1.5, 0.42) if grief else ((3.6, 1.15, 0.34) if mallet else ((3.8, 1.2, 0.36) if concerto else ((3.4, 1.05, 0.30) if elegia else ((3.0, 0.9, 0.26) if piano else (2.2, 0.75, 0.30))))))
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
    mixL = L + wet * Lw * 3.0; mixR = R + wet * Rw * 3.0
    st = np.stack([mixL, mixR], axis=1)
    peak = np.abs(st).max()
    st = st / peak * 0.89
    # soft knee
    st = np.tanh(st * 1.15) / np.tanh(1.15)
    # fade out tail
    tail = int((5.0 if (requiem or piano) else 2.5) * SR)
    st[-tail:] *= np.linspace(1, 0, tail)[:, None]
    sf.write(out, st, SR, subtype='PCM_16')
    print('wrote', out, '%.1fs' % total, 'peak', peak)

if __name__ == '__main__':
    main(*sys.argv[1:3])
