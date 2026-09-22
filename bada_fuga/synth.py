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

def formant_amps(f0, nh=60):
    """母音「ア」のフォルマントで整形した倍音振幅 (合唱風)"""
    F = [(730, 130), (1090, 160), (2440, 240), (3400, 320)]; Wt = [1.0, 0.75, 0.35, 0.12]
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

def main(score='score.json', out='fuga.wav'):
    d = json.load(open(score))
    total = d['duration'] + (7.0 if d.get('meta', {}).get('style') == 'requiem' else 4.0)
    N = int(total * SR)
    L = np.zeros(N, dtype=np.float32); R = np.zeros(N, dtype=np.float32)
    rng = np.random.default_rng(3)
    style = d.get('meta', {}).get('style', 'organ')
    requiem = style == 'requiem'
    for nt in d['notes']:
        tb = TIMBRE[nt['v']]
        freq = 440.0 * 2 ** ((nt['m'] - 69) / 12.0)
        dur = max(nt['d'] - 0.035, 0.06)
        if requiem:
            # 合唱 (フォルマント) + オルガンの混合。長い音ほど合唱が前へ
            y = tone(freq, dur, tb) * 0.45
            yc = choir_tone(freq, dur + 0.05)
            m = min(len(y), len(yc)); y = y[:m] + yc[:m] * 0.85
        else:
            y = tone(freq, dur, tb)
        # 主題の音は少し強く
        g = tb['g'] * (1.18 if nt['label'] else 1.0) * (1.0 + 0.04 * rng.standard_normal()) * nt.get('dyn', 1.0)
        # 高音域は少し控えめに
        g *= min(1.0, (72.0 / max(freq, 72.0)) ** 0.25)
        i0 = int(nt['t'] * SR); i1 = min(i0 + len(y), N)
        pan = tb['pan']
        L[i0:i1] += y[:i1 - i0] * g * math.cos((pan + 1) * math.pi / 4)
        R[i0:i1] += y[:i1 - i0] * g * math.sin((pan + 1) * math.pi / 4)
    # 鐘・ドローン
    for ex in d.get('extras', []):
        freq = 440.0 * 2 ** ((ex['m'] - 69) / 12.0)
        if ex['v'] == 'X':
            y = bell_tone(freq, ex['d'] + 3.0) * 0.55 * ex.get('gain', 1.0); pan = 0.0
        else:
            y = drone_tone(freq, ex['d']) * 0.30 * ex.get('gain', 1.0); pan = 0.0
        i0 = int(ex['t'] * SR); i1 = min(i0 + len(y), N)
        L[i0:i1] += y[:i1 - i0] * 0.707; R[i0:i1] += y[:i1 - i0] * 0.707
    # 合成リバーブ (指数減衰ノイズ, ローパス)
    rv_len, rv_decay, wet = (4.2, 1.35, 0.42) if requiem else (2.2, 0.75, 0.30)
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
    tail = int((5.0 if requiem else 2.5) * SR)
    st[-tail:] *= np.linspace(1, 0, tail)[:, None]
    sf.write(out, st, SR, subtype='PCM_16')
    print('wrote', out, '%.1fs' % total, 'peak', peak)

if __name__ == '__main__':
    main(*sys.argv[1:3])
