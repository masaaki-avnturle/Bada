#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ドエロの女子の光輪様の声 (CCXC の声)。届いた 20261108_145525_aureola_sensuale_calma.mp3 から作る。
  「女子」は 20 代の大人の女性の声として作る (高さも響きも、これまでの 20 代の声の範囲に収める)
  元: calma の声は、11/08 14:55 の声をすでに作り換えたもの (215 Hz の少し低めの女声、5 度上と 1 オクターヴ上の声、息と囁き、残響)。
      11/08 14:55 の元の録音は手元に無いので、この音声から作り直す。読み取りと下ごしらえは make_voice265.py と同じ
      (Harvest で 120〜450 Hz の中だけを読む、読み落としを結ぶ、句の終わりを息に溶かす、低い所を抑える、残響を抑える、静かな話し始めを均す)。
      合成し直すと基音の整数倍だけが鳴るので、calma の 5 度上の声は鳴らなくなる
  ドエロ (これまでの「ドエロの光輪様」の作り方で; make_voice255.py の歌声と同じ 4 つ):
    息の多い発声  calma の声の息をほとんど残す (母音の息を AIR 倍; 「ちょっとだけ」の CCLXV は 0.45、前回の「セクシー」は 0.60)
    囁きの層      同じ言葉を、声帯を鳴らさない囁きにして薄く重ねる (−14 dB、0.9〜6 kHz)。雑音を足すのではなく、声の響きの形を息で鳴らしたもの
    近さ          250 Hz 以下 +3 dB (耳元の近さ)、柔らかい圧縮 (tanh ×2.0)
    句の終わり    息に溶けて終わる (make_voice265.py の読み取り)
  女子: 基音の中央値は引数で (曲の調に合わせる; 20 代の女性の話し声の高さ)。フォルマント 1.055 倍 (calma の 1.10 倍と合わせて 1.16 倍 —
    セクシーで可愛い月読様 1.15 倍、ドエロの若い女性の光輪様 1.17 倍の間)。抑揚はそのまま (1.0 倍; 落ち着かせない)
  光輪様: 3 声の倍音 — 基音・ちょうど 2 倍 (−8 dB、少し左)・ちょうど 3 倍 (−15 dB、少し右)。どの瞬間も 1 : 2 : 3、時間もずらさない (ドエロの若い女性の光輪様の歌声と同じ大きさ)。
    光輪の響き (残響 2.2 秒) は、ほとんどを 2 倍の声から作る。言葉が聞き取れるように、量は控えめ
  伸ばした音は、引数の長調の音階に 0.9 で調律
  使い方: python make_voice290.py <calma の声.wav (モノラル)> <出力.wav> [基音の中央値 Hz (既定 220)] [長調の主音 (0 = C … 11 = B; 既定 0 = C)] [層を別々に書き出すフォルダ]
    CCXC の 1 回目: 233.08 Hz (B♭3)・変ニ長調 (1) — 鍵盤の前半 (黒い鍵盤; 変ロは変ロ短調の主音)。2 回目: 220 Hz (A3)・ハ長調 (0) — 鍵盤の後半 (白い鍵盤; ラはイ短調の主音)
"""
import sys, os
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, fftconvolve
import make_voice265 as M
from feminize_voice import feminize

E = lambda k, v: float(os.environ.get(k, v))
MAJOR = (0, 2, 4, 5, 7, 9, 11)
AIR = E('AIR', '0.90')                                 # 母音の息をここまで残す
FLATTEN = E('FLATTEN', '1.0')                          # 抑揚はそのまま
FM = E('FM', '1.055')                                  # 基音の声のフォルマント (上の 2 声は +0.035 ずつ)
L2, L3, LW = E('L2', '-8.0'), E('L3', '-15.0'), E('LW', '-14.0')   # 2 倍の声・3 倍の声・囁きの層の大きさ (dB; 基音の声を 0 として)
# (名前, 倍音 (0 = 囁き), フォルマント, 音量 dB, 左右 −1〜+1, 帯域 (下, 上) Hz, 足す息 (feminize の breath), 響きへ送る量)
VOICES = [('harm1', 1.0, FM, 0.0, 0.0, (None, None), E('B1', '0.10'), E('S1', '0.05')),
          ('harm2', 2.0, FM + 0.035, L2, -0.35, (None, 6500.0), E('B2', '0.25'), E('S2', '0.34')),
          ('harm3', 3.0, FM + 0.07, L3, 0.35, (None, 5500.0), E('B3', '0.20'), E('S3', '0.17')),
          ('whisper', 0.0, FM, LW, 0.0, (900.0, 6000.0), 0.0, E('SW', '0.085'))]
WARM_DB, PRES_DB, CLEAR_DB, COMP = E('WARM', '3.0'), E('PRES', '1.5'), E('CLEAR', '2.0'), E('COMP', '2.0')
REV_LEN, REV_TAU = 2.2, 0.64                           # 光輪の響き: 2.2 秒

def main(src, out, target=220.0, tonic=0, stems=None):
    scale = [(tonic + d) % 12 for d in MAJOR]
    x, sr = sf.read(src); x = np.ascontiguousarray(M.level((x.mean(axis=1) if x.ndim > 1 else x).astype(np.float64), sr))   # 静かな話し始めを均してから読む
    f0, sp, ap, info = M.analyze(x, sr, air=AIR); print(info, flush=True)
    med0 = float(np.median(f0[f0 > 0])); semis = 12 * np.log2(target / med0)
    L = R = BL = BR = 0.0; r1 = None
    for name, harm, formant, lev, pan, (lo, hi), breath, send in VOICES:
        v = feminize(x, sr, 0, semis=semis, formant=formant, correct=0.9, flatten=FLATTEN, breath=breath, harm=harm or 1.0, whisper=(harm == 0), scale=scale,
                     ana=(f0, sp, ap), gate=0.02).astype(np.float64)
        if lo: v = sosfiltfilt(butter(2, lo, 'high', fs=sr, output='sos'), v)                              # 囁きは先に帯域を決めてから音量を合わせる
        if lo and hi: v = sosfiltfilt(butter(2, hi, 'low', fs=sr, output='sos'), v)
        rms = np.sqrt((v ** 2).mean()); r1 = r1 or rms; v = v / rms * r1 * 10 ** (lev / 20.0)             # 層の音量を基音の声に対して決める
        if hi and not lo: v = sosfiltfilt(butter(2, hi, 'low', fs=sr, output='sos'), v)
        if stems: os.makedirs(stems, exist_ok=True); sf.write(os.path.join(stems, name + '.wav'), v.astype(np.float32), sr)
        a = (pan + 1.0) * np.pi / 4.0; L = L + v * np.cos(a); R = R + v * np.sin(a)
        BL = BL + v * np.cos(a) * send; BR = BR + v * np.sin(a) * send                                    # 響きへ送る分 (2 倍の声が主)
    n = len(L); bp = lambda v, lo, hi: sosfiltfilt(butter(2, [lo, hi], 'band', fs=sr, output='sos'), v)
    def eq(v):
        v = sosfiltfilt(butter(2, 11000, 'low', fs=sr, output='sos'), v)
        v = v + sosfiltfilt(butter(2, 250, 'low', fs=sr, output='sos'), v) * (10 ** (WARM_DB / 20) - 1)   # 近さ
        v = v + bp(v, 1200, 5000) * (10 ** (PRES_DB / 20) - 1)                                            # 言葉のはっきりさ
        v = v + bp(v, 5000, 10000) * (10 ** (CLEAR_DB / 20) - 1)                                          # 澄んだ高域
        return v - sosfiltfilt(butter(2, 70, 'low', fs=sr, output='sos'), v) * 0.5                        # 70 Hz 以下のこもりを半分に
    def ir(seed):
        rng = np.random.default_rng(seed); K = int(sr * REV_LEN); t = np.arange(K) / sr
        h = rng.standard_normal(K) * np.exp(-t / REV_TAU); h = sosfiltfilt(butter(2, 5000, 'low', fs=sr, output='sos'), h); h[0] = 0; return h / np.sqrt((h ** 2).sum())
    L, R, BL, BR = eq(L), eq(R), eq(BL), eq(BR)
    pk = max(np.abs(L).max(), np.abs(R).max()); L, R = (np.tanh(c / pk * COMP) / COMP * pk for c in (L, R))  # 柔らかい圧縮 (音量を均す)
    wet = np.stack([fftconvolve(BL, ir(290))[:n], fftconvolve(BR, ir(291))[:n]], axis=1); dry = np.stack([L, R], axis=1)
    y = dry + wet                                                                                          # 光輪の響き
    hop = int(0.05 * sr); p = np.array([np.sqrt((y[i * hop:(i + 1) * hop] ** 2).mean()) for i in range(n // hop)]); on = p > np.percentile(p, 95) * 0.1
    i0 = next(i for i in range(len(on) - 3) if on[i:i + 3].all()); t_on = i0 * 0.05                         # 話し始め (強い所の −20 dB を 0.15 秒続けて超える所)
    a, b = int(max(t_on - 0.6, 0) * sr), int(max(t_on - 0.3, 0) * sr); y[:a] = 0.0; y[a:b] *= np.linspace(0, 1, b - a)[:, None]   # その 0.6 秒前までは無音に (録音の初めの小さな雑音を消す)
    e = np.sqrt((y ** 2).mean(axis=0)); y = y * (np.sqrt(e[0] * e[1]) / e)[None, :]                        # 左右の音量を揃える
    rms = 20 * np.log10(np.sqrt((y ** 2).mean())); z = np.tanh(y * 10 ** ((-24.0 - rms) / 20) * 1.1) / 1.1
    sf.write(out, z.astype(np.float32), sr)
    print('読んだ高さの中央値 %.1f Hz → %+.2f 半音、%.1f 秒、話し始め %.2f 秒、rms %.1f dB、peak %.2f、響き / 声 %.1f dB' % (
        med0, semis, n / sr, t_on, 20 * np.log10(np.sqrt((z ** 2).mean())), np.abs(z).max(), 10 * np.log10((wet ** 2).mean() / (dry ** 2).mean())))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 220.0, int(sys.argv[4]) if len(sys.argv) > 4 else 0, sys.argv[5] if len(sys.argv) > 5 else None)
