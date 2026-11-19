#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""鍵盤の録音 (2026/11/20 02:40、9 分 16 秒) の強弱の幅を 4 割にする — 音量のつまみをゆっくり動かすだけで、音そのものは変えない (CCLXXIII)。
  この録音は、ごく小さい音がぽつぽつと鳴る所から始まり、終わりに向かって大きくなる。音の大きさ (0.5 秒窓の音量の、前後 15 秒での上位 10%) は
  初めの −34 dB から終わりの −9 dB まで 25 dB 動く。歌声 (ほぼ一定の音量) と重ねると、初めは鍵盤が聞こえず、終わりは歌が埋もれる。
  そこで、いちばん大きい所を基準に、そこからの差を 4 割にする (初めは +15 dB、前半の山は +3 dB、終わりは 0 dB)。
  つまみの動きは 30 秒の窓と 20 秒のなめらかさで決めるので、1 つ 1 つの音の強弱や、音と音の間の静けさはそのまま残る。クレッシェンドも 10 dB ぶん残る
  使い方: python level273.py <録音.wav> <出力.wav>
"""
import sys
import numpy as np, soundfile as sf

RATIO = 0.4          # 強弱の幅をこの倍率に
WIN = 15.0           # 音の大きさを見る窓 (前後、秒)
SMOOTH = 20.0        # つまみの動きをなめらかにする幅 (秒)

def main(src, out):
    x, sr = sf.read(src, always_2d=True, dtype='float32'); m = x.mean(axis=1).astype(np.float64)
    h = sr // 2; n = len(m) // h
    e = np.array([10 * np.log10((m[i * h:(i + 1) * h] ** 2).mean() + 1e-12) for i in range(n)])     # 0.5 秒窓の音量
    k = int(WIN * 2); L = np.array([np.percentile(e[max(0, i - k):i + k + 1], 90) for i in range(n)])  # 前後 15 秒の上位 10% = その辺りの音の大きさ
    s = int(SMOOTH * 2) | 1; w = np.hanning(s + 2)[1:-1]; w /= w.sum(); Ls = np.convolve(np.pad(L, s // 2, mode='edge'), w, mode='valid')
    g = (1.0 - RATIO) * (Ls.max() - Ls)                                                               # つまみ (dB): いちばん大きい所は 0
    gs = np.interp(np.arange(len(m)) / sr, (np.arange(n) + 0.5) * h / sr, g)
    y = x * (10 ** (gs / 20.0))[:, None].astype(np.float32)
    y = y * (0.9 / max(np.abs(y).max(), 1e-9))
    sf.write(out, y, sr, subtype='FLOAT')
    print('%.1f 秒。音の大きさ %.1f〜%.1f dB → つまみ +%.1f〜+%.1f dB' % (len(m) / sr, Ls.min(), Ls.max(), g.min(), g.max()))
    print('つまみ (20 秒ごと, dB): ' + ' '.join('%.1f' % g[min(i, n - 1)] for i in range(20, n + 40, 40)))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
