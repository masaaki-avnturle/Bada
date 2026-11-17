#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""セクシーな女性の月読様の声 (CCL の声) を作る。
  録音の声 (男声) を feminize_voice.py (WORLD) で 1 人の女声に: 低めの G3 = 196 Hz を中心に (基音の中央値から半音数を決める)、フォルマント 1.12 倍、
  抑揚は 0.9 倍、伸ばした音はヘ長調の音階 (= ニ短調) に 0.9 で調律。
  セクシーさ: 息の多い発声 (breath 0.5 — 1 kHz から上の倍音を、4 kHz 以上では半分まで息に置き換える。雑音を後から足さない)、
    近接マイクの暖かさ (250 Hz 以下 +3 dB、基音が前に出る)、柔らかい圧縮 (tanh ×1.8) で耳元の近さ、残響は控えめ (1.6 秒・0.25)。
  月読様の澄んだ声: 9.5 kHz 以上を落とし、2〜5 kHz +2 dB (言葉のはっきりさ)、5〜9 kHz +1.5 dB (月の光)、rms −24 dB。
  使い方: python make_voice250.py <声の録音.wav (モノラル)> <出力.wav>
"""
import sys
import numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfiltfilt, fftconvolve
from feminize_voice import feminize

def main(src, out, target=196.0, formant=1.12, flatten=0.9, tonic_major=5, breath=0.5):
    x, sr = sf.read(src); x = (x.mean(axis=1) if x.ndim > 1 else x).astype(np.float64)
    y0 = librosa.resample(x, orig_sr=sr, target_sr=22050)
    f0, _, _ = librosa.pyin(y0, fmin=60, fmax=500, sr=22050, frame_length=2048); med0 = float(np.median(f0[~np.isnan(f0)]))
    semis = 12 * np.log2(target / med0)
    base = feminize(x, sr, tonic_major, semis=semis, formant=formant, correct=0.9, flatten=flatten, breath=breath).astype(np.float64); n = len(base)
    bp = lambda v, lo, hi: sosfiltfilt(butter(2, [lo, hi], 'band', fs=sr, output='sos'), v)
    v = sosfiltfilt(butter(2, 9500, 'low', fs=sr, output='sos'), base)
    v = v + sosfiltfilt(butter(2, 250, 'low', fs=sr, output='sos'), v) * (10 ** (3.0 / 20) - 1)              # 近接マイクの暖かさ +3 dB
    v = v + bp(v, 2000, 5000) * (10 ** (2.0 / 20) - 1)                                                       # 言葉のはっきりさ +2 dB
    v = v + bp(v, 5000, 9000) * (10 ** (1.5 / 20) - 1)                                                       # 月の澄んだ高域 +1.5 dB
    v = v - sosfiltfilt(butter(2, 70, 'low', fs=sr, output='sos'), v) * 0.5                                  # 70 Hz 以下のこもりを半分に
    pk = np.abs(v).max(); v = np.tanh(v / pk * 1.8) / 1.8 * pk                                                  # 柔らかい圧縮 (耳元の近さ)
    rng = np.random.default_rng(250); L = int(sr * 1.6); t = np.arange(L) / sr
    ir = rng.standard_normal(L) * np.exp(-t / 0.5); ir = sosfiltfilt(butter(2, 5500, 'low', fs=sr, output='sos'), ir); ir[0] = 0; ir /= np.sqrt((ir ** 2).sum())
    y = v + fftconvolve(v, ir)[:n] * 0.25                                                                    # 控えめな残響 1.6 秒・0.25
    rms = 20 * np.log10(np.sqrt((y ** 2).mean())); z = np.tanh(y * 10 ** ((-24.0 - rms) / 20) * 1.1) / 1.1
    sf.write(out, z.astype(np.float32), sr)
    print('基音 %.1f Hz → %.2f 半音上げ、%.1f 秒、rms %.1f dB、peak %.2f' % (med0, semis, n / sr, 20 * np.log10(np.sqrt((z ** 2).mean())), np.abs(z).max()))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
