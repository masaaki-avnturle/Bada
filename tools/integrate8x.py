#!/usr/bin/env python3
"""Integrate the recordings into one piece: 8x pitch-preserving stretch, staggered fugal entries, hall reverb."""
import sys, subprocess, numpy as np
from requiem_fuga import SR, load, paulstretch, reverb

paths, out_wav = sys.argv[1:-1], sys.argv[-1]
st = []
for p in paths:
    x = load(p)
    print(f"{p}: {x.shape[1]/SR:.1f}s -> x8", flush=True)
    st.append(paulstretch(x, 8.0, win_s=0.25).astype(np.float32))
lens = [s.shape[1] for s in st]
step = int(np.mean(lens) * 0.25)
total = max(i * step + l for i, l in enumerate(lens)) + 8 * SR
mix = np.zeros((2, total), np.float32)
pans = [0.35, 0.65, 0.5, 0.45]
fade = 6 * SR
for i, s in enumerate(st):
    s[:, :fade] *= np.linspace(0, 1, fade)
    s[:, -fade:] *= np.linspace(1, 0, fade)
    g = np.array([[np.cos(pans[i] * np.pi / 2)], [np.sin(pans[i] * np.pi / 2)]]) * 1.414
    mix[:, i * step:i * step + s.shape[1]] += s * g / 2
del st
y = reverb(mix.astype(np.float64), 5.0, 0.35)
fi, fo = 6 * SR, 12 * SR
y[:, :fi] *= np.linspace(0, 1, fi)
y[:, -fo:] *= np.linspace(1, 0, fo)
y = np.tanh(1.2 * y / np.max(np.abs(y))) * 0.89 / np.tanh(1.2)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-", out_wav],
               input=(y.T * 32767).astype("<i2").tobytes(), check=True)
print("wrote", out_wav, f"{total/SR/60:.1f} min")
