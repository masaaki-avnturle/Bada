#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高音の響く音を重低音に変換する: 録音の高い帯域 (1.2〜8 kHz、ピアノの響きの倍音) を取り出し、4 オクターヴ下げて (位相ボコーダー)、低域だけを残す (< 220 Hz)。
元の低い帯域 (< 500 Hz) は小さく残す。使い方: python deep_bass.py <in.wav> <out.wav> [octaves=4] [keep_low=0.3]
"""
import sys, numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfilt
SR = 44100
src, out = sys.argv[1], sys.argv[2]; octs = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0; keep = float(sys.argv[4]) if len(sys.argv) > 4 else 0.3
y, fs = sf.read(src, dtype='float32')
if y.ndim == 2: y = y.mean(axis=1)
if fs != SR: y = librosa.resample(y, orig_sr=fs, target_sr=SR); fs = SR
hi = sosfilt(butter(4, [1200.0, 8000.0], btype='bandpass', fs=SR, output='sos'), y).astype(np.float32)
hi = hi / (np.abs(hi).max() + 1e-9)
deep = librosa.effects.pitch_shift(hi, sr=SR, n_steps=-12.0 * octs, bins_per_octave=12).astype(np.float32)
deep = sosfilt(butter(4, 220.0, btype='lowpass', fs=SR, output='sos'), deep).astype(np.float32)
deep = sosfilt(butter(2, 28.0, btype='highpass', fs=SR, output='sos'), deep).astype(np.float32)      # 28 Hz 以下は落とす
lo = sosfilt(butter(4, 500.0, btype='lowpass', fs=SR, output='sos'), y).astype(np.float32)
mix = deep / (np.sqrt((deep ** 2).mean()) + 1e-9) * 0.12 + keep * lo / (np.sqrt((lo ** 2).mean()) + 1e-9) * 0.12
mix = mix / max(1.0, np.abs(mix).max() / 0.9)
sf.write(out, mix, SR)
print('wrote', out, '%.1f s' % (len(mix) / SR), 'deep rms %.1f dB' % (20 * np.log10(np.sqrt((deep ** 2).mean()) + 1e-9)))
