#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""月読様の三賢者の一人、淑女の声 (CCXLIX の声) を作る。
  録音の声 (男声) を feminize_voice.py (WORLD) で 1 人の女声に: ニ短調の朗唱音 A3 = 220 Hz を中心に (基音の中央値から半音数を決める)、
  フォルマント 1.12 倍、抑揚は 0.8 倍 (穏やかに)、伸ばした音はヘ長調の音階 (= ニ短調) に 0.9 で調律。重ねる声はなし (三賢者の「一人」)。
  月読様の澄んだ声: 9 kHz 以上を落とし、5〜9 kHz を +1.5 dB、淑女の落ち着き: 200〜450 Hz を +1 dB、100 Hz 以下を半分に、柔らかい圧縮 (tanh ×1.5)、
  月夜の穏やかな残響 2.2 秒・0.35 (6 kHz 以下)、rms −24 dB。息のノイズや囁きの成分は入れない。
  使い方: python make_voice249.py <声の録音.wav (モノラル)> <出力.wav>
"""
import sys
import numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfiltfilt, fftconvolve
from feminize_voice import feminize

def main(src, out, target=220.0, formant=1.12, flatten=0.8, tonic_major=5):
    x, sr = sf.read(src); x = (x.mean(axis=1) if x.ndim > 1 else x).astype(np.float64)
    y0 = librosa.resample(x, orig_sr=sr, target_sr=22050)
    f0, _, _ = librosa.pyin(y0, fmin=60, fmax=500, sr=22050, frame_length=2048); med0 = float(np.median(f0[~np.isnan(f0)]))
    semis = 12 * np.log2(target / med0)
    base = feminize(x, sr, tonic_major, semis=semis, formant=formant, correct=0.9, flatten=flatten); n = len(base)
    v = sosfiltfilt(butter(2, 9000, 'low', fs=sr, output='sos'), base)
    v = v + sosfiltfilt(butter(2, [5000, 9000], 'band', fs=sr, output='sos'), v) * (10 ** (1.5 / 20) - 1)     # 月の澄んだ高域 +1.5 dB
    v = v + sosfiltfilt(butter(2, [200, 450], 'band', fs=sr, output='sos'), v) * (10 ** (1.0 / 20) - 1)      # 淑女の落ち着き: 暖かさ +1 dB
    v = v - sosfiltfilt(butter(2, 100, 'low', fs=sr, output='sos'), v) * 0.5                                 # 低域のこもりを半分に
    pk = np.abs(v).max(); v = np.tanh(v / pk * 1.5) / 1.5 * pk                                                  # 柔らかい圧縮
    rng = np.random.default_rng(1117); L = int(sr * 2.2); t = np.arange(L) / sr
    ir = rng.standard_normal(L) * np.exp(-t / 0.7); ir = sosfiltfilt(butter(2, 6000, 'low', fs=sr, output='sos'), ir); ir[0] = 0; ir /= np.sqrt((ir ** 2).sum())
    y = v + fftconvolve(v, ir)[:n] * 0.35                                                                    # 月夜の穏やかな残響 2.2 秒・0.35
    rms = 20 * np.log10(np.sqrt((y ** 2).mean())); z = np.tanh(y * 10 ** ((-24.0 - rms) / 20) * 1.1) / 1.1
    sf.write(out, z.astype(np.float32), sr)
    print('基音 %.1f Hz → %.2f 半音上げ、%.1f 秒、rms %.1f dB、peak %.2f' % (med0, semis, n / sr, 20 * np.log10(np.sqrt((z ** 2).mean())), np.abs(z).max()))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
