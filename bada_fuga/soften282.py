#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""鍵盤の録音を「しっとり」に仕上げる — 音量のつまみと、雑音だけの帯域を落とすこと (CCLXXXII)。音の高さも速さも変えない、何も足さない。
  0) 3 kHz から上を落とす: この鍵盤の音は 2.4 kHz までしか無く、その上は録音の雑音 (サーという音) だけ。静かな所で雑音が目立たないように
  1) ゆっくりしたつまみ (level273.py と同じやり方): その辺りの音の大きさ (0.5 秒窓の音量の、前後 15 秒での上位 10%) を、いちばん大きい所を基準に、
     差を RATIO 倍に縮める。level273.py は 4 割 (0.4)、ここでは 2 割 5 分 (0.25) — 山を小さく、静かな所を近くに
  2) 柔らかい打鍵 (速いつまみ): 強く弾いた音だけを、弾いた瞬間から抑える。音の山 (10 ミリ秒窓) が基準 (鳴っている所の中央値) を超えた分を半分に (2:1、
     境目は 6 dB の幅でなだらかに)。抑えたつまみは 1 秒に 12 dB の速さで戻すので、音の余韻が少し持ち上がって、長く残る。
     つまみは音より 5 ミリ秒先に動かし始めるので、打鍵の頭が歪まない
  3) 曲の中の大きさの流れ (ARC): 「録音の秒:dB」を並べたもの。その間はまっすぐつなぐ (例: 0:-1,176:-1,301:-2 — 176 秒まで −1 dB、301 秒にかけて −2 dB へ)
  使い方: python soften282.py <録音.wav> <出力.wav> [RATIO=0.25] [CR=2.0] [ARC]
"""
import sys
import numpy as np, soundfile as sf
from scipy.ndimage import maximum_filter1d, uniform_filter1d
from scipy.signal import butter, sosfiltfilt

LOWPASS = 3000.0     # ここから上を落とす (Hz; 鍵盤の音は 2.4 kHz まで)
WIN = 15.0           # 音の大きさを見る窓 (前後、秒)
SMOOTH = 20.0        # ゆっくりしたつまみをなめらかにする幅 (秒)
KNEE = 6.0           # 柔らかい打鍵: 境目の幅 (dB)
REL = 12.0           # 柔らかい打鍵: つまみが戻る速さ (dB / 秒)
LOOK = 0.005         # 柔らかい打鍵: つまみを先に動かす時間 (秒)

def slow_ride(m, sr, ratio):
    h = sr // 2; n = len(m) // h
    e = np.array([10 * np.log10((m[i * h:(i + 1) * h] ** 2).mean() + 1e-12) for i in range(n)])     # 0.5 秒窓の音量
    k = int(WIN * 2); L = np.array([np.percentile(e[max(0, i - k):i + k + 1], 90) for i in range(n)])  # 前後 15 秒の上位 10% = その辺りの音の大きさ
    s = int(SMOOTH * 2) | 1; w = np.hanning(s + 2)[1:-1]; w /= w.sum(); Ls = np.convolve(np.pad(L, s // 2, mode='edge'), w, mode='valid')
    g = (1.0 - ratio) * (Ls.max() - Ls)                                                               # つまみ (dB): いちばん大きい所は 0
    return np.interp(np.arange(len(m)) / sr, (np.arange(n) + 0.5) * h / sr, g), Ls

def soft_touch(m, sr, cr):
    """強く弾いた音だけを抑えるつまみ (dB, 0 以下) を返す"""
    w = int(0.010 * sr) | 1; p = 20 * np.log10(maximum_filter1d(np.abs(m), w) + 1e-9)                 # 音の山 (10 ミリ秒窓)
    thr = np.median(p[p > p.max() - 45.0])                                                            # 基準: 鳴っている所 (いちばん大きい音から 45 dB 以内) の中央値
    over = p - thr; s = 1.0 - 1.0 / cr
    red = np.where(over <= -KNEE / 2, 0.0, np.where(over >= KNEE / 2, over * s, (over + KNEE / 2) ** 2 / (2 * KNEE) * s))   # 抑える量 (dB)
    red = maximum_filter1d(red, int(2 * LOOK * sr) | 1)                                               # 先読み: 音の山より 5 ミリ秒前から抑える
    out = np.empty_like(red); cur = 0.0; step = REL / sr
    for i in range(len(red)):                                                                         # 戻りは 1 秒に 12 dB
        cur = red[i] if red[i] > cur else max(cur - step, red[i]); out[i] = cur
    out = uniform_filter1d(out, int(LOOK * sr) | 1)                                                   # 動き始めをなめらかに
    return -out, thr

def main(src, out, ratio=0.25, cr=2.0, arc=''):
    x, sr = sf.read(src, always_2d=True, dtype='float32')
    x = sosfiltfilt(butter(4, LOWPASS, btype='lowpass', fs=sr, output='sos'), x.astype(np.float64), axis=0).astype(np.float32)   # 位相を動かさない
    m = x.mean(axis=1).astype(np.float64)
    g1, Ls = slow_ride(m, sr, ratio)
    y = x * (10 ** (g1 / 20.0))[:, None].astype(np.float32); m2 = y.mean(axis=1).astype(np.float64)
    g2, thr = soft_touch(m2, sr, cr)
    z = y * (10 ** (g2 / 20.0))[:, None].astype(np.float32)
    rms0 = np.sqrt((z.astype(np.float64) ** 2).mean())
    if arc:                                                                                           # 曲の中の大きさの流れ
        pts = [tuple(float(v) for v in a.split(':')) for a in arc.split(',')]
        g3 = np.interp(np.arange(len(m)) / sr, [t for t, _ in pts], [d for _, d in pts]); z = z * (10 ** (g3 / 20.0))[:, None].astype(np.float32)
    drms = 20 * np.log10(np.sqrt((z.astype(np.float64) ** 2).mean()) / rms0)
    z = z * (0.9 / max(np.abs(z).max(), 1e-9))
    sf.write(out, z, sr, subtype='FLOAT')
    crest = lambda v: 20 * np.log10(np.abs(v).max() / (np.sqrt((v.astype(np.float64) ** 2).mean()) + 1e-12))
    act = g2[m2 ** 2 > 1e-7]
    print('%.1f 秒。ゆっくりしたつまみ: 音の大きさ %.1f〜%.1f dB → +%.1f〜+%.1f dB (幅を %.2f 倍に)' % (len(m) / sr, Ls.min(), Ls.max(), g1.min(), g1.max(), ratio))
    print('柔らかい打鍵: 基準 %.1f dB、抑えた量は最大 %.1f dB、鳴っている所の平均 %.1f dB、3 dB 以上抑えた時間 %.0f 秒。山と平均の比 %.1f → %.1f dB' % (
        thr, -g2.min(), -act.mean(), (g2 < -3).sum() / sr, crest(y.mean(axis=1)), crest(z.mean(axis=1))))
    if arc: print('大きさの流れ: %s → 録音全体の rms は %+.2f dB' % (arc, drms))

if __name__ == '__main__':
    a = sys.argv
    main(a[1], a[2], float(a[3]) if len(a) > 3 else 0.25, float(a[4]) if len(a) > 4 else 2.0, a[5] if len(a) > 5 else '')
