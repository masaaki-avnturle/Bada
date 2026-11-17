#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2025/01/08 14:42 の録音から、歌声だけを取り出した音声を作る (声は変えない)。
  1. extract_voice.py (UVR の MDX-Net、Kim_Vocal_2) で歌声を取り出す — 歌っていない所の伴奏の残りが消える
  2. 歌声に残っている伴奏の持続音 (G の倍音 786・1179・1571・1963・2354 Hz) を細い帯域で抜き、70 Hz 以下と 5.5 kHz 以上
     (録音の 6〜10 kHz の強い雑音) を落とす — make_voice255.py の下ごしらえと同じ
  3. 音量を上げる (波形の山を 0.89 に)。高さも速さも響きも変えない
  使い方: python voice_only255.py <取り出した歌声.wav (extract_voice.py の出力)> <出力.wav>
"""
import sys
import numpy as np, soundfile as sf
from make_voice255 import clean

if __name__ == '__main__':
    x, sr = sf.read(sys.argv[1]); x = clean((x.mean(axis=1) if x.ndim > 1 else x).astype(np.float64), sr)
    x = x / np.abs(x).max() * 0.89
    sf.write(sys.argv[2], x.astype(np.float32), sr)
    print('%.1f 秒、rms %.1f dB、peak %.2f' % (len(x) / sr, 20 * np.log10(np.sqrt((x ** 2).mean())), np.abs(x).max()))
