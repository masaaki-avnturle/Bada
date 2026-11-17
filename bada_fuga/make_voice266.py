#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""倍音の 3 声の、17 歳のホッとする女性の声 (CCLXVI の声)。
  元: 11/12 14:49 の録音 (男声、基音の中央値 112 Hz)。feminize_voice.py (WORLD) で女声にする
  倍音の 3 声 (CCLI からの作り方): 同じ抑揚・同じ音程の補正から、基音・ちょうど 2 倍・ちょうど 3 倍の高さの声を作って重ねる。どの瞬間も 1 : 2 : 3、時間もずらさない
    基音      B♭3 = 233 Hz を中心に (基音の中央値から半音数を決める; 20 代の声の A3 より半音高い)。フォルマント 1.19 倍 (17 歳の、軽く若い響き)、
              抑揚 0.92 倍 (落ち着き)、伸ばした音はヘ長調 (= ニ短調、トラック 18 と 8 の調) の音階に 0.9 で調律
    第 2 倍音  ちょうど 2 倍 (B♭4 のあたり)。フォルマント 1.23 倍、−8 dB、少し左
    第 3 倍音  ちょうど 3 倍 (F5 のあたり)。フォルマント 1.27 倍、−14 dB、少し右
  ホッとする: 息はほんの少し (0.10 — 柔らかさだけ。囁きの層なし、近接の低音なし = ドエロにしない)、柔らかい圧縮 (tanh ×1.8) で音量を均す、
    暖かい残響をごく控えめに (1.2 秒・0.10)
  仕上げ: 9.5 kHz 以上を落とし、250〜400 Hz の曇り −1 dB、言葉の 2〜5 kHz +2.5 dB、5〜9 kHz +0.5 dB (録音の 6〜8 kHz のサーッという成分を立てない)、
    120 Hz 以下を 0.6 削る。話し始めの前にある録音の小さな雑音 (1.5 秒のあたり) は消す。rms −24 dB、ステレオ
  使い方: python make_voice266.py <声の録音.wav (モノラル)> <出力.wav> [3 声を別々に書き出すフォルダ]
"""
import sys, os
import numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfiltfilt, fftconvolve
from scipy.ndimage import uniform_filter1d
from feminize_voice import feminize

TARGET = 233.08                                        # 基音の中央値をここへ (B♭3)
SCALE = [5, 7, 9, 10, 0, 2, 4]                         # ヘ長調 = ニ短調の音階 (移調した後の高さで)
FLATTEN = 0.92
# (倍音, フォルマント, 息, 音量 dB, 左右 −1〜+1, ここから上を落とす Hz)
VOICES = [(1.0, 1.19, 0.10, 0.0, 0.0, None), (2.0, 1.23, 0.08, -8.0, -0.3, 7000.0), (3.0, 1.27, 0.08, -14.0, 0.3, 6000.0)]
MUD_DB, PRES_DB, CLEAR_DB, COMP, REV = -1.0, 2.5, 0.5, 1.8, 0.10

def main(src, out, stems=None):
    x, sr = sf.read(src); x = (x.mean(axis=1) if x.ndim > 1 else x).astype(np.float64)
    y0 = librosa.resample(x, orig_sr=sr, target_sr=22050)
    f0, _, _ = librosa.pyin(y0, fmin=60, fmax=500, sr=22050, frame_length=2048); med0 = float(np.median(f0[~np.isnan(f0)]))
    semis = 12 * np.log2(TARGET / med0)
    L = R = 0.0; r1 = None
    for harm, formant, breath, lev, pan, top in VOICES:
        v = feminize(x, sr, 0, semis=semis, formant=formant, correct=0.9, flatten=FLATTEN, breath=breath, harm=harm, scale=SCALE).astype(np.float64)
        rms = np.sqrt((v ** 2).mean()); r1 = r1 or rms; v = v / rms * r1 * 10 ** (lev / 20.0)                # 3 声の音量を基音の声に対して決める
        if top: v = sosfiltfilt(butter(2, top, 'low', fs=sr, output='sos'), v)
        if stems: os.makedirs(stems, exist_ok=True); sf.write(os.path.join(stems, 'harm%d.wav' % harm), v.astype(np.float32), sr)
        a = (pan + 1.0) * np.pi / 4.0; L = L + v * np.cos(a); R = R + v * np.sin(a)
    n = len(L); bp = lambda v, lo, hi: sosfiltfilt(butter(2, [lo, hi], 'band', fs=sr, output='sos'), v)
    def finish(v, seed):
        v = sosfiltfilt(butter(2, 9500, 'low', fs=sr, output='sos'), v)
        v = v + bp(v, 250, 400) * (10 ** (MUD_DB / 20) - 1)                                                  # 曇り −1 dB
        v = v + bp(v, 2000, 5000) * (10 ** (PRES_DB / 20) - 1)                                               # 言葉のはっきりさ
        v = v + bp(v, 5000, 9000) * (10 ** (CLEAR_DB / 20) - 1)                                              # 澄んだ高域 (少しだけ)
        v = v - sosfiltfilt(butter(2, 120, 'low', fs=sr, output='sos'), v) * 0.6                             # 120 Hz 以下を 0.6 削る
        rng = np.random.default_rng(seed); K = int(sr * 1.2); t = np.arange(K) / sr
        ir = rng.standard_normal(K) * np.exp(-t / 0.3); ir = sosfiltfilt(butter(2, 5000, 'low', fs=sr, output='sos'), ir); ir[0] = 0; ir /= np.sqrt((ir ** 2).sum())
        return v, ir
    (L, irL), (R, irR) = finish(L, 266), finish(R, 267)
    hop = int(0.05 * sr); e = np.array([np.sqrt(((L[i * hop:(i + 1) * hop] + R[i * hop:(i + 1) * hop]) ** 2).mean()) for i in range(n // hop)])
    on = (uniform_filter1d((e > 0.08 * np.percentile(e, 97)).astype(float), 10, origin=-4) > 0.6).argmax()       # 話し始め: 0.5 秒のうち 6 割以上で声がある最初の所
    g = np.clip((np.arange(n) - (on * hop - int(0.3 * sr))) / (0.1 * sr), 0, 1); L, R = L * g, R * g             # その 0.3 秒前から 0.1 秒で開く (前の雑音を消す)
    pk = max(np.abs(L).max(), np.abs(R).max()); L, R = (np.tanh(c / pk * COMP) / COMP * pk for c in (L, R))  # 柔らかい圧縮 (音量を均す)
    y = np.stack([L + fftconvolve(L, irL)[:n] * REV, R + fftconvolve(R, irR)[:n] * REV], axis=1)             # 暖かい残響 (ごく控えめ)
    e = np.sqrt((y ** 2).mean(axis=0)); y = y * (np.sqrt(e[0] * e[1]) / e)[None, :]                           # 左右の音量を揃える
    rms = 20 * np.log10(np.sqrt((y ** 2).mean())); z = np.tanh(y * 10 ** ((-24.0 - rms) / 20) * 1.1) / 1.1
    sf.write(out, z.astype(np.float32), sr)
    print('基音 %.1f Hz → %.2f 半音上げ、%.1f 秒、rms %.1f dB、peak %.2f' % (med0, semis, n / sr, 20 * np.log10(np.sqrt((z ** 2).mean())), np.abs(z).max()))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
