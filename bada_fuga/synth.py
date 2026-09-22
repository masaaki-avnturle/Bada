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

def main(score='score.json', out='fuga.wav'):
    d = json.load(open(score))
    total = d['duration'] + 4.0
    N = int(total * SR)
    L = np.zeros(N, dtype=np.float32); R = np.zeros(N, dtype=np.float32)
    rng = np.random.default_rng(3)
    for nt in d['notes']:
        tb = TIMBRE[nt['v']]
        freq = 440.0 * 2 ** ((nt['m'] - 69) / 12.0)
        dur = max(nt['d'] - 0.035, 0.06)
        y = tone(freq, dur, tb)
        # 主題の音は少し強く
        g = tb['g'] * (1.18 if nt['label'] else 1.0) * (1.0 + 0.04 * rng.standard_normal())
        # 高音域は少し控えめに
        g *= min(1.0, (72.0 / max(freq, 72.0)) ** 0.25)
        i0 = int(nt['t'] * SR); i1 = min(i0 + len(y), N)
        pan = tb['pan']
        L[i0:i1] += y[:i1 - i0] * g * math.cos((pan + 1) * math.pi / 4)
        R[i0:i1] += y[:i1 - i0] * g * math.sin((pan + 1) * math.pi / 4)
    # 合成リバーブ (指数減衰ノイズ, ローパス)
    ir_len = int(2.2 * SR)
    t = np.arange(ir_len) / SR
    def make_ir(seed):
        r = np.random.default_rng(seed).standard_normal(ir_len).astype(np.float32)
        r *= np.exp(-t / 0.75)
        # simple one-pole lowpass
        a = 0.35; y = np.zeros_like(r); acc = 0.0
        for i in range(ir_len):
            acc = a * r[i] + (1 - a) * acc; y[i] = acc
        y[:int(0.012 * SR)] = 0
        return y / np.sqrt((y ** 2).sum())
    irL, irR = make_ir(11), make_ir(12)
    wet = 0.30
    Lw = fftconvolve(L, irL)[:N].astype(np.float32); Rw = fftconvolve(R, irR)[:N].astype(np.float32)
    mixL = L + wet * Lw * 3.0; mixR = R + wet * Rw * 3.0
    st = np.stack([mixL, mixR], axis=1)
    peak = np.abs(st).max()
    st = st / peak * 0.89
    # soft knee
    st = np.tanh(st * 1.15) / np.tanh(1.15)
    # fade out tail
    tail = int(2.5 * SR)
    st[-tail:] *= np.linspace(1, 0, tail)[:, None]
    sf.write(out, st, SR, subtype='PCM_16')
    print('wrote', out, '%.1fs' % total, 'peak', peak)

if __name__ == '__main__':
    main(*sys.argv[1:3])
