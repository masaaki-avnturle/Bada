#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大人の 20 代の淑女の月読様の声、シャキッと (CCLVII・CCLVIII の声)。ドエロはやめる。
  録音の声 (男声) を feminize_voice.py (WORLD) で女声に。倍音の 3 声 (どの瞬間も 1 : 2 : 3、時間もずらさない) は CCLI からの作り方のまま、控えめに:
    基音      A3 = 220 Hz を中心に (基音の中央値から半音数を決める)。フォルマント 1.12 倍 (大人の響き)、抑揚 0.9 倍 (淑女の落ち着き)、
              伸ばした音はヘ長調の音階 (= ニ短調) に 0.9 で調律
    第 2 倍音  ちょうど 2 倍。フォルマント 1.16 倍、−9 dB、少し左 (1 オクターヴ上が前に出ると若く聞こえるので引く)
    第 3 倍音  ちょうど 3 倍。フォルマント 1.20 倍、−15 dB、少し右
  ドエロをやめる: 息を足さない (breath 0)、囁きの層なし、近接の低音なし、強い圧縮なし
  シャキッと (CCXLV の乾いた声と同じ考え方): 残響もエコーも入れない。250〜400 Hz の曇り −1.5 dB、子音の 2〜5 kHz +3 dB、
    澄んだ高域 5〜9 kHz +0.5 dB、9.5 kHz まで通す (録音の 6〜8 kHz のサーッという成分が立ちすぎないように、高域は少しだけ)、
    120 Hz 以下を 0.6 削る、圧縮はごく軽く (tanh ×1.2、立ち上がりを残す)。rms −24 dB、ステレオ
  使い方: python make_voice257.py <声の録音.wav (モノラル)> <出力.wav> [3 声を別々に書き出すフォルダ]
"""
import sys, os
import numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfiltfilt
from feminize_voice import feminize

# (倍音, フォルマント, 息, 音量 dB, 左右 −1〜+1, ここから上を落とす Hz)
VOICES = [(1.0, 1.12, 0.0, 0.0, 0.0, None), (2.0, 1.16, 0.0, -9.0, -0.3, 7000.0), (3.0, 1.20, 0.0, -15.0, 0.3, 6000.0)]

def main(src, out, stems=None, target=220.0, flatten=0.9, tonic_major=5):
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
    bp = lambda v, lo, hi: sosfiltfilt(butter(2, [lo, hi], 'band', fs=sr, output='sos'), v)
    def finish(v):
        v = sosfiltfilt(butter(2, 9500, 'low', fs=sr, output='sos'), v)
        v = v - bp(v, 250, 400) * (1 - 10 ** (-1.5 / 20))                                                    # 曇り −1.5 dB
        v = v + bp(v, 2000, 5000) * (10 ** (3.0 / 20) - 1)                                                   # 子音 +3 dB
        v = v + bp(v, 5000, 9000) * (10 ** (0.5 / 20) - 1)                                                   # 澄んだ高域 +0.5 dB
        return v - sosfiltfilt(butter(2, 120, 'low', fs=sr, output='sos'), v) * 0.6                          # 120 Hz 以下を 0.6 削る
    L, R = finish(L), finish(R)
    pk = max(np.abs(L).max(), np.abs(R).max()); y = np.stack([np.tanh(c / pk * 1.2) / 1.2 * pk for c in (L, R)], axis=1)   # ごく軽い圧縮。残響もエコーも入れない
    e = np.sqrt((y ** 2).mean(axis=0)); y = y * (np.sqrt(e[0] * e[1]) / e)[None, :]                           # 左右の音量を揃える
    rms = 20 * np.log10(np.sqrt((y ** 2).mean())); z = np.tanh(y * 10 ** ((-24.0 - rms) / 20) * 1.1) / 1.1
    sf.write(out, z.astype(np.float32), sr)
    print('基音 %.1f Hz → %.2f 半音上げ、%.1f 秒、rms %.1f dB、peak %.2f' % (med0, semis, len(z) / sr, 20 * np.log10(np.sqrt((z ** 2).mean())), np.abs(z).max()))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
