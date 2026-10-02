#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""録音の中の息のような音 (1〜4 kHz が調波でなく平らなノイズになっている 0.5 秒) を見つけ、その間だけ 1〜6 kHz を下げる (既定 −12 dB、0.1 秒でなめらかに)。
  ピアノの音はそのまま (ほかの区間は触らない)。使い方: python dip_breath.py <in.wav> <out.wav> [flat_min=0.3] [level_min_dB=-40] [dip_dB=12]"""
import sys, numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt

def find(y, sr, flat_min=0.3, lvl_min=-40.0, seg_s=0.5):
    seg = int(seg_s * sr); out = []
    for i in range(0, len(y) - seg, seg // 2):
        x = y[i:i + seg] * np.hanning(seg); sp = np.abs(np.fft.rfft(x)) ** 2; fr = np.fft.rfftfreq(seg, 1 / sr)
        band = sp[(fr > 1000) & (fr < 4000)]; flat = np.exp(np.log(band + 1e-12).mean()) / (band.mean() + 1e-12)
        lvl = 20 * np.log10(np.sqrt((y[i:i + seg] ** 2).mean()) + 1e-9)
        if flat > flat_min and lvl > lvl_min: out.append((i / sr, (i + seg) / sr))
    merged = []
    for a, b in out:
        if merged and a <= merged[-1][1] + 0.01: merged[-1][1] = b
        else: merged.append([a, b])
    return merged

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    flat_min = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3; lvl_min = float(sys.argv[4]) if len(sys.argv) > 4 else -40.0; dip = float(sys.argv[5]) if len(sys.argv) > 5 else 12.0
    y, sr = sf.read(src, dtype='float32'); y = y.mean(1) if y.ndim > 1 else y
    wins = find(y, sr, flat_min, lvl_min)
    band = sosfiltfilt(butter(4, [1000.0, 6000.0], btype='bandpass', fs=sr, output='sos'), y).astype(np.float32)
    g = np.zeros(len(y), dtype=np.float32); r = int(0.1 * sr); ramp = np.linspace(0, 1, r, dtype=np.float32)
    for a, b in wins:
        i0, i1 = int(a * sr), int(b * sr); g[i0:i1] = 1.0
        g[max(0, i0 - r):i0] = np.maximum(g[max(0, i0 - r):i0], ramp[-(i0 - max(0, i0 - r)):]); g[i1:i1 + r] = np.maximum(g[i1:i1 + r], ramp[::-1][:len(g[i1:i1 + r])])
    out = y - band * g * (1 - 10 ** (-dip / 20.0))
    sf.write(dst, out, sr, subtype='PCM_16')
    print('breath-like windows: %d' % len(wins), [(round(a, 1), round(b, 1)) for a, b in wins])
