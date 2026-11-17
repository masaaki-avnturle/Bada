#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""倍音の 3 声で、セクシーで可愛い女性の月読様の声 (CCLI の声) を作る。
  録音の声 (男声) を feminize_voice.py (WORLD) で女声に。3 声は倍音の関係 (オルガンの 8' + 4' + 2 2/3' と同じ重ね方):
    基音の声   A3 = 220 Hz を中心に (基音の中央値から半音数を決める)。フォルマント 1.15 倍、息 0.45 — セクシーな声 (近く、暖かく、息まじり)
    第 2 倍音  基音のちょうど 2 倍 (1 オクターヴ上、A4 = 440 Hz)。フォルマント 1.21 倍、息 0.30、−5 dB、少し左 — 可愛い声
    第 3 倍音  基音のちょうど 3 倍 (1 オクターヴと純正 5 度上、E5 = 660 Hz)。フォルマント 1.27 倍、息 0.25、−11 dB、少し右 — 光
    倍音の声はフォルマントを上げるぶん録音の 6〜8 kHz のサーッという成分も上にずれて目立つので、7 kHz / 6 kHz から上を落とす (声の高さと言葉の帯域は残る)
  3 声とも同じ抑揚・同じ音程の補正から作る (feminize の harm) ので、どの瞬間も 1 : 2 : 3 のまま。時間もずらさない — うなりも、ぼやけも、返しも出ない。
  抑揚はそのまま (1.0 倍 — 可愛さ)、伸ばした音はヘ長調の音階 (= ニ短調) に 0.9 で調律。
  仕上げ: 9.5 kHz 以上を落とし、250 Hz 以下 +2 dB (近さ)、2〜5 kHz +2 dB (言葉)、5〜9 kHz +1.5 dB (可愛い明るさ)、70 Hz 以下を半分に、柔らかい圧縮 (tanh ×1.8)、
    残響は控えめ (1.6 秒・0.22、左右で別の響き)、左右の音量を揃えて、rms −24 dB。ステレオ。
  使い方: python make_voice251.py <声の録音.wav (モノラル)> <出力.wav> [3 声を別々に書き出すフォルダ]
"""
import sys, os
import numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfiltfilt, fftconvolve
from feminize_voice import feminize

# (倍音, フォルマント, 息, 音量 dB, 左右 −1〜+1, ここから上を落とす Hz)
VOICES = [(1.0, 1.15, 0.45, 0.0, 0.0, None), (2.0, 1.21, 0.30, -5.0, -0.3, 7000.0), (3.0, 1.27, 0.25, -11.0, 0.3, 6000.0)]

def main(src, out, stems=None, target=220.0, flatten=1.0, tonic_major=5):
    x, sr = sf.read(src); x = (x.mean(axis=1) if x.ndim > 1 else x).astype(np.float64)
    y0 = librosa.resample(x, orig_sr=sr, target_sr=22050)
    f0, _, _ = librosa.pyin(y0, fmin=60, fmax=500, sr=22050, frame_length=2048); med0 = float(np.median(f0[~np.isnan(f0)]))
    semis = 12 * np.log2(target / med0)
    L = R = 0.0; r1 = None
    for harm, formant, breath, lev, pan, top in VOICES:
        v = feminize(x, sr, tonic_major, semis=semis, formant=formant, correct=0.9, flatten=flatten, breath=breath, harm=harm).astype(np.float64)
        rms = np.sqrt((v ** 2).mean()); r1 = r1 or rms; v = v / rms * r1 * 10 ** (lev / 20.0)                # 3 声の音量を基音の声に対して決める
        if top: v = sosfiltfilt(butter(2, top, 'low', fs=sr, output='sos'), v)
        if stems: os.makedirs(stems, exist_ok=True); sf.write(os.path.join(stems, 'harm%d.wav' % harm), v.astype(np.float32), sr)
        a = (pan + 1.0) * np.pi / 4.0; L = L + v * np.cos(a); R = R + v * np.sin(a)
    n = len(L); bp = lambda v, lo, hi: sosfiltfilt(butter(2, [lo, hi], 'band', fs=sr, output='sos'), v)
    def finish(v, seed):
        v = sosfiltfilt(butter(2, 9500, 'low', fs=sr, output='sos'), v)
        v = v + sosfiltfilt(butter(2, 250, 'low', fs=sr, output='sos'), v) * (10 ** (2.0 / 20) - 1)          # 近接マイクの暖かさ +2 dB
        v = v + bp(v, 2000, 5000) * (10 ** (2.0 / 20) - 1)                                                   # 言葉のはっきりさ +2 dB
        v = v + bp(v, 5000, 9000) * (10 ** (1.5 / 20) - 1)                                                   # 可愛い明るさ +1.5 dB
        v = v - sosfiltfilt(butter(2, 70, 'low', fs=sr, output='sos'), v) * 0.5                              # 70 Hz 以下のこもりを半分に
        rng = np.random.default_rng(seed); K = int(sr * 1.6); t = np.arange(K) / sr
        ir = rng.standard_normal(K) * np.exp(-t / 0.5); ir = sosfiltfilt(butter(2, 5500, 'low', fs=sr, output='sos'), ir); ir[0] = 0; ir /= np.sqrt((ir ** 2).sum())
        return v, ir
    (L, irL), (R, irR) = finish(L, 251), finish(R, 252)
    pk = max(np.abs(L).max(), np.abs(R).max()); L, R = (np.tanh(c / pk * 1.8) / 1.8 * pk for c in (L, R))    # 柔らかい圧縮 (耳元の近さ)
    y = np.stack([L + fftconvolve(L, irL)[:n] * 0.22, R + fftconvolve(R, irR)[:n] * 0.22], axis=1)           # 控えめな残響 1.6 秒・0.22
    e = np.sqrt((y ** 2).mean(axis=0)); y = y * (np.sqrt(e[0] * e[1]) / e)[None, :]                           # 左右の音量を揃える (第 2 倍音が左、第 3 倍音が右で、左が少し大きくなる)
    rms = 20 * np.log10(np.sqrt((y ** 2).mean())); z = np.tanh(y * 10 ** ((-24.0 - rms) / 20) * 1.1) / 1.1
    sf.write(out, z.astype(np.float32), sr)
    print('基音 %.1f Hz → %.2f 半音上げ、%.1f 秒、rms %.1f dB、peak %.2f' % (med0, semis, n / sr, 20 * np.log10(np.sqrt((z ** 2).mean())), np.abs(z).max()))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
