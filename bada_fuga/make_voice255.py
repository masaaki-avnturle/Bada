#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ドエロの若い女性の光輪様の歌声 (CCLV の声) を作る。
  元: 2025/01/08 14:42 の歌の録音 (4 分 19 秒) から extract_voice.py で取り出した歌声 (男声、ハ短調、基音の中央値 156 Hz、音域 B♭2〜G3)。
  下ごしらえ: 歌声に残っている伴奏の持続音 (G の倍音 786・1179・1571・1963・2354 Hz) を細い帯域で抜き、70 Hz 以下と 5.5 kHz 以上
    (録音の 6〜10 kHz に強い雑音がある) を落とす。声の高さは 100〜420 Hz の中だけで読む (句の終わりで、息や伴奏の残りを声の高さと読み違えないように)
  変換 (feminize_voice.py = WORLD):
    高さ      14 半音上げる — ハ短調がニ短調 (トラック 18 の調) になり、音域は C4〜A4 (若い女性の歌の音域)。
              伸ばした音はニ短調の音階 (D E F G A B♭ C と導音の C♯) に 0.8 で調律。旋律の動き (抑揚) はそのまま
    若い女性  フォルマント 1.17 倍
    光輪      倍音の声を 2 つ: 基音のちょうど 2 倍 (1 オクターヴ上、−8 dB、少し左)、ちょうど 3 倍 (1 オクターヴと純正 5 度上、−15 dB、少し右)。
              同じ旋律から作るので、どの瞬間も 1 : 2 : 3。それに光輪の響き (残響 2.2 秒・0.3)
    ドエロ    息の多い発声 (0.5)、同じ歌を声帯を鳴らさずに囁いた層 (−14 dB)、近さ (500 Hz 以下 +2.5 dB、基音が前に)、柔らかい圧縮 (tanh ×2.0)
  仕上げ: 7.5 kHz 以上を落とし、2〜5 kHz +2 dB (言葉)、70 Hz 以下を半分に、左右の音量を揃えて、rms −24 dB。ステレオ。
  使い方: python make_voice255.py <取り出した歌声.wav (extract_voice.py の出力)> <出力.wav> [層を別々に書き出すフォルダ]
"""
import sys, os
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, fftconvolve, iirnotch, filtfilt
from feminize_voice import feminize

SEMIS = 14.0
SCALE = [2, 4, 5, 7, 9, 10, 0, 1]                      # ニ短調: D E F G A B♭ C と、導音の C♯ (移調した後の高さで)
NOTCH = [(786.0, 40.0), (1179.0, 35.0), (1571.0, 30.0), (1963.0, 45.0), (2354.0, 40.0)]     # 残っている伴奏の持続音 (Hz, Q)
# (名前, 倍音 (0 = 囁き), フォルマント, 息, 音量 dB, 左右 −1〜+1, ここから下を落とす Hz, ここから上を落とす Hz)
VOICES = [('harm1', 1.0, 1.17, 0.50, 0.0, 0.0, None, None), ('harm2', 2.0, 1.22, 0.40, -8.0, -0.35, None, 6000.0),
          ('harm3', 3.0, 1.27, 0.30, -15.0, 0.35, None, 5000.0), ('whisper', 0.0, 1.17, 0.0, -14.0, 0.0, 900.0, 6000.0)]

def clean(x, sr):
    for f0, q in NOTCH:
        b, a = iirnotch(f0, q, sr); x = filtfilt(b, a, x)
    x = sosfiltfilt(butter(4, 70, 'high', fs=sr, output='sos'), x); x = sosfiltfilt(butter(6, 5500, 'low', fs=sr, output='sos'), x)
    return x / (np.sqrt((x ** 2).mean()) + 1e-12) * 10 ** (-26.0 / 20)

def main(src, out, stems=None, semis=SEMIS, voices=VOICES, scale=SCALE, warm_db=2.5, comp=2.0, rev=0.30, seed=255):
    """semis 以降は、同じ作り方で別の声を作るときに変える所 (make_voice256.py)。既定は CCLV の声"""
    x, sr = sf.read(src); x = clean((x.mean(axis=1) if x.ndim > 1 else x).astype(np.float64), sr)
    if stems: os.makedirs(stems, exist_ok=True); sf.write(os.path.join(stems, 'clean.wav'), x.astype(np.float32), sr)
    L = R = 0.0; r1 = None
    for name, harm, formant, breath, lev, pan, lo, hi in voices:
        v = feminize(x, sr, 0, semis=semis, formant=formant, correct=0.8, flatten=1.0, breath=breath, harm=harm or 1.0, whisper=(harm == 0), scale=scale, f0_floor=100, f0_ceil=420).astype(np.float64)
        if harm == 0:                                                                                        # 囁きは先に帯域を決めてから音量を合わせる
            v = sosfiltfilt(butter(2, lo, 'high', fs=sr, output='sos'), v); v = sosfiltfilt(butter(2, hi, 'low', fs=sr, output='sos'), v)
        rms = np.sqrt((v ** 2).mean()); r1 = r1 or rms; v = v / rms * r1 * 10 ** (lev / 20.0)                # 層の音量を基音の声に対して決める
        if harm and hi: v = sosfiltfilt(butter(2, hi, 'low', fs=sr, output='sos'), v)
        if stems: sf.write(os.path.join(stems, name + '.wav'), v.astype(np.float32), sr)
        a = (pan + 1.0) * np.pi / 4.0; L = L + v * np.cos(a); R = R + v * np.sin(a)
    n = len(L); bp = lambda v, lo, hi: sosfiltfilt(butter(2, [lo, hi], 'band', fs=sr, output='sos'), v)
    def finish(v, seed):
        v = sosfiltfilt(butter(2, 7500, 'low', fs=sr, output='sos'), v)
        v = v + sosfiltfilt(butter(2, 500, 'low', fs=sr, output='sos'), v) * (10 ** (warm_db / 20) - 1)      # 近さ: 基音のあたり +2.5 dB
        v = v + bp(v, 2000, 5000) * (10 ** (2.0 / 20) - 1)                                                   # 言葉のはっきりさ +2 dB
        v = v - sosfiltfilt(butter(2, 70, 'low', fs=sr, output='sos'), v) * 0.5                              # 70 Hz 以下のこもりを半分に
        rng = np.random.default_rng(seed); K = int(sr * 2.2); t = np.arange(K) / sr
        ir = rng.standard_normal(K) * np.exp(-t / 0.7); ir = sosfiltfilt(butter(2, 5500, 'low', fs=sr, output='sos'), ir); ir[0] = 0; ir /= np.sqrt((ir ** 2).sum())
        return v, ir
    (L, irL), (R, irR) = finish(L, seed), finish(R, seed + 1)
    pk = max(np.abs(L).max(), np.abs(R).max()); L, R = (np.tanh(c / pk * comp) / comp * pk for c in (L, R))  # 柔らかい圧縮 (近く)
    y = np.stack([L + fftconvolve(L, irL)[:n] * rev, R + fftconvolve(R, irR)[:n] * rev], axis=1)             # 光輪の響き 2.2 秒・0.3
    e = np.sqrt((y ** 2).mean(axis=0)); y = y * (np.sqrt(e[0] * e[1]) / e)[None, :]                           # 左右の音量を揃える
    rms = 20 * np.log10(np.sqrt((y ** 2).mean())); z = np.tanh(y * 10 ** ((-24.0 - rms) / 20) * 1.1) / 1.1
    sf.write(out, z.astype(np.float32), sr)
    print('%.1f 秒、%g 半音上げ、rms %.1f dB、peak %.2f' % (n / sr, semis, 20 * np.log10(np.sqrt((z ** 2).mean())), np.abs(z).max()))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
