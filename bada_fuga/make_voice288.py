#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""月読様であり、光輪様でもあり、メシア様でもある、若いセクシーな女性の声 — 3 声の倍音。届いた 20261108_145525_aureola_sensuale_calma.mp3 から作る。
  元: calma の声は、11/08 14:55 の声をすでに作り換えたもの (215 Hz の少し低めの女声、5 度上と 1 オクターヴ上の声、息と囁き、残響)。
      11/08 14:55 の元の録音は手元に無いので、この音声から作り直す。読み取りと下ごしらえは make_voice265.py と同じ
      (Harvest で 120〜450 Hz の中だけを読む、読み落としを結ぶ、句の終わりを息に溶かす、低い所を抑える、残響を抑える、静かな話し始めを均す)。
      合成し直すと基音の整数倍だけが鳴るので、calma の 5 度上の声は鳴らなくなる
  3 声の倍音: 同じ抑揚・同じ音程の補正から、基音・ちょうど 2 倍・ちょうど 3 倍の声を作って重ねる (どの瞬間も 1 : 2 : 3、時間もずらさない)。
    3 つの声に、3 人を 1 人ずつ当てる:
      基音 (A3)   メシア様 — 優しく、近く、暖かい。この声が「若いセクシーな女性」の体になる。中央
      2 倍 (A4)   光輪様   — 声を包む光の輪。息を少し多めに、響き (残響) はほとんどこの声から作る。少し左
      3 倍 (E5)   月読様   — 澄んだ月の光。息を減らして澄ませ、響きは控えめ。少し右
    上の 2 声の大きさは、3 人のこれまでの倍音の声 (大人の女性の声) の平均: セクシーで可愛い月読様 −5 / −11 dB (CCLI)、若い女性の光輪様 −8 / −15 dB (CCLV)、
    メシア様 −12 / −19 dB (CCLXXIII・CCLXXV) → −8.5 / −15 dB
  若い: 20 代の大人の女性の声。基音の中央値を A3 = 220 Hz に (CCLI のセクシーな月読様、CCLXV の光輪様と同じ高さ; メシア様の A♭3 より半音高い)。
    フォルマント 1.05 倍 (calma の 1.10 倍と合わせて 1.155 倍 — 月読様 1.15・光輪様 1.17・メシア様 1.14 倍の平均)
  セクシー: 息を残す (母音の息を AIR 倍に; CCLXV の「ちょっとだけ」は 0.45)、息に溶ける句の終わり、250 Hz 以下 +2 dB の近さ、柔らかい圧縮。
    囁きの層や雑音は足さない (言葉が聞き取れるように)
  月読様の澄んだ言葉: 1.2〜5 kHz +1.5 dB、5〜10 kHz +2 dB。メシア様の落ち着き: 抑揚 0.92 倍。光輪の響き: 1.6 秒、ごく控えめ
  伸ばした音は、引数の長調の音階に 0.9 で調律 (既定はヘ長調 = ニ短調; A はニ短調の属音)
  話し始めの前 (録音の初めの 5 秒) にある小さな雑音は消す
  使い方: python make_voice288.py <calma の声.wav (モノラル)> <出力.wav> [基音の中央値 Hz (既定 220)] [長調の主音 (0 = C … 11 = B; 既定 5 = F)] [層を別々に書き出すフォルダ]
"""
import sys, os
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt, fftconvolve
import make_voice265 as M
from feminize_voice import feminize

E = lambda k, v: float(os.environ.get(k, v))
MAJOR = (0, 2, 4, 5, 7, 9, 11)
AIR = E('AIR', '0.60')                                 # 母音の息をここまで残す (基音の声と光輪様の声)
AIR_MOON = E('AIR_MOON', '0.30')                       # 月読様の声は息を減らして澄ませる
FLATTEN = E('FLATTEN', '0.92')                         # 抑揚 (落ち着き)
L2, L3 = E('L2', '-8.5'), E('L3', '-15.0')             # 上の 2 声の大きさ (dB; 基音の声を 0 として)
FM = E('FM', '1.05')                                   # 基音の声のフォルマント (上の 2 声は +0.035 ずつ — これまでの倍音の声と同じ刻み)
# (名前, 倍音, フォルマント, 音量 dB, 左右 −1〜+1, ここから上を落とす Hz, 足す息 (feminize の breath), 響きへ送る量, 息の読み取り)
VOICES = [('harm1_messia', 1.0, FM, 0.0, 0.0, None, 0.0, E('S1', '0.04'), 'air'),
          ('harm2_aureola', 2.0, FM + 0.035, L2, -0.3, 7000.0, E('B2', '0.20'), E('S2', '0.29'), 'air'),
          ('harm3_tsukuyomi', 3.0, FM + 0.07, L3, 0.3, 6000.0, 0.0, E('S3', '0.12'), 'moon')]
WARM_DB, PRES_DB, CLEAR_DB, COMP = E('WARM', '2.0'), E('PRES', '1.5'), E('CLEAR', '2.0'), 1.7
REV_LEN, REV_TAU = 1.6, 0.45                           # 光輪の響き: 1.6 秒 (CCLXV・CCLXXV と同じ長さ)

def main(src, out, target=220.0, tonic=5, stems=None):
    scale = [(tonic + d) % 12 for d in MAJOR]
    x, sr = sf.read(src); x = np.ascontiguousarray(M.level((x.mean(axis=1) if x.ndim > 1 else x).astype(np.float64), sr))   # 静かな話し始めを均してから読む
    f0, sp, ap, info = M.analyze(x, sr, air=AIR); print(info, flush=True)
    ap_moon = M.analyze(x, sr, air=AIR_MOON)[2] if AIR_MOON != AIR else ap                                 # 高さと響きの形は同じ。息の割合だけ違う
    med0 = float(np.median(f0[f0 > 0])); semis = 12 * np.log2(target / med0)
    L = R = BL = BR = 0.0; r1 = None
    for name, harm, formant, lev, pan, top, breath, send, which in VOICES:
        v = feminize(x, sr, 0, semis=semis, formant=formant, correct=0.9, flatten=FLATTEN, breath=breath, harm=harm, scale=scale,
                     ana=(f0, sp, ap_moon if which == 'moon' else ap), gate=0.02).astype(np.float64)
        rms = np.sqrt((v ** 2).mean()); r1 = r1 or rms; v = v / rms * r1 * 10 ** (lev / 20.0)             # 層の音量を基音の声に対して決める
        if top: v = sosfiltfilt(butter(2, top, 'low', fs=sr, output='sos'), v)
        if stems: os.makedirs(stems, exist_ok=True); sf.write(os.path.join(stems, name + '.wav'), v.astype(np.float32), sr)
        a = (pan + 1.0) * np.pi / 4.0; L = L + v * np.cos(a); R = R + v * np.sin(a)
        BL = BL + v * np.cos(a) * send; BR = BR + v * np.sin(a) * send                                    # 響きへ送る分 (光輪様の声が主)
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
    wet = np.stack([fftconvolve(BL, ir(288))[:n], fftconvolve(BR, ir(289))[:n]], axis=1); dry = np.stack([L, R], axis=1)
    y = dry + wet                                                                                          # 光輪の響き (ごく控えめ)
    hop = int(0.05 * sr); p = np.array([np.sqrt((y[i * hop:(i + 1) * hop] ** 2).mean()) for i in range(n // hop)]); on = p > np.percentile(p, 95) * 0.1
    i0 = next(i for i in range(len(on) - 3) if on[i:i + 3].all()); t_on = i0 * 0.05                         # 話し始め (強い所の −20 dB を 0.15 秒続けて超える所)
    a, b = int(max(t_on - 0.6, 0) * sr), int(max(t_on - 0.3, 0) * sr); y[:a] = 0.0; y[a:b] *= np.linspace(0, 1, b - a)[:, None]   # その 0.6 秒前までは無音に
    e = np.sqrt((y ** 2).mean(axis=0)); y = y * (np.sqrt(e[0] * e[1]) / e)[None, :]                        # 左右の音量を揃える
    rms = 20 * np.log10(np.sqrt((y ** 2).mean())); z = np.tanh(y * 10 ** ((-24.0 - rms) / 20) * 1.1) / 1.1
    sf.write(out, z.astype(np.float32), sr)
    print('読んだ高さの中央値 %.1f Hz → %+.2f 半音、%.1f 秒、話し始め %.2f 秒、rms %.1f dB、peak %.2f、響き / 声 %.1f dB' % (
        med0, semis, n / sr, t_on, 20 * np.log10(np.sqrt((z ** 2).mean())), np.abs(z).max(), 10 * np.log10((wet ** 2).mean() / (dry ** 2).mean())))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 220.0, int(sys.argv[4]) if len(sys.argv) > 4 else 5, sys.argv[5] if len(sys.argv) > 5 else None)
