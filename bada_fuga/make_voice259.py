#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大人の 20 代の淑女の光輪様の歌声、シャキッと (CCLIX の声)。ドエロはやめる。
  make_voice256.py (大人の 20 代の歌声) と同じ高さと響き — 7 半音上げ (基音の中央値 B♭3、音域 F3〜D4)、フォルマント 1.11 倍、
  伸ばした音はニ短調の音階 (D E F G A B♭ C) に 0.8 で調律 — で、変える所:
    ドエロをやめる  息を足さない (0.45 → 0)、囁きの層なし、近さの低音なし (500 Hz 以下 +2.5 → 0 dB)、強い圧縮なし (tanh ×2.0 → ×1.2)
    シャキッと      残響を入れない (2.2 秒・0.28 → なし)、言葉の 2〜5 kHz を +2 → +3 dB
    淑女            倍音の声 (光輪) をさらに引く (−10・−16 → −11・−17 dB)、息を足さない
  使い方: python make_voice259.py <取り出した歌声.wav (extract_voice.py の出力)> <出力.wav> [層を別々に書き出すフォルダ]
"""
import sys
import make_voice255 as M

SEMIS = 7.0
SCALE = [2, 4, 5, 7, 9, 10, 0]                         # ニ短調: D E F G A B♭ C (移調した後の高さで)
# (名前, 倍音, フォルマント, 息, 音量 dB, 左右 −1〜+1, ここから下を落とす Hz, ここから上を落とす Hz)
VOICES = [('harm1', 1.0, 1.11, 0.0, 0.0, 0.0, None, None), ('harm2', 2.0, 1.15, 0.0, -11.0, -0.35, None, 6000.0), ('harm3', 3.0, 1.19, 0.0, -17.0, 0.35, None, 5000.0)]

if __name__ == '__main__':
    M.main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None, semis=SEMIS, voices=VOICES, scale=SCALE, warm_db=0.0, comp=1.2, rev=0.0, seed=259, pres_db=3.0)
