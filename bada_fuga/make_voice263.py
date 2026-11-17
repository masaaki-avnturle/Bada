#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""月読様の女子学生の歌声 (CCLXIII の声)。tablet260 の男性の歌声 (取り出した歌声) を 1 オクターヴ (半音 12 個ぶん) 上げて作り換える。
  make_voice255.py と同じ作り方 (下ごしらえ → WORLD) で、変える所:
    高さ      **12 半音上げる** — ちょうど 1 オクターヴなので、歌はハ短調のまま (tablet260 のテープにそのまま合う)。
              基音の中央値は 156 Hz から 312 Hz (E♭4) へ、音域は B♭3〜G4 (女子学生の歌の音域)。
              伸ばした音は歌の調の音階 (C D E♭ F G A♭ B♭ と導音の B) に 0.8 で調律。旋律の動きはそのまま
    女子学生  フォルマント 1.19 倍 (若く、軽い響き)。息はほんの少し (0.12) — ドエロにしない。囁きの層なし、近さの低音なし
    月読様    倍音の声を 2 つ、ごく控えめに (ちょうど 2 倍 −12 dB、ちょうど 3 倍 −18 dB): 月の光の薄い輪。どの瞬間も 1 : 2 : 3。
              澄んだ響き (残響 2.2 秒・0.15、控えめ)
    はっきり  言葉の 2〜5 kHz +3 dB、圧縮は軽く (tanh ×1.3)
  使い方: python make_voice263.py <取り出した歌声.wav (extract_voice.py の出力)> <出力.wav> [層を別々に書き出すフォルダ]
"""
import sys
import make_voice255 as M

SEMIS = 12.0
SCALE = [0, 2, 3, 5, 7, 8, 10, 11]                     # ハ短調: C D E♭ F G A♭ B♭ と、導音の B (移調した後の高さで)
# (名前, 倍音, フォルマント, 息, 音量 dB, 左右 −1〜+1, ここから下を落とす Hz, ここから上を落とす Hz)
VOICES = [('harm1', 1.0, 1.19, 0.12, 0.0, 0.0, None, None), ('harm2', 2.0, 1.24, 0.10, -12.0, -0.35, None, 6000.0), ('harm3', 3.0, 1.28, 0.10, -18.0, 0.35, None, 5000.0)]

if __name__ == '__main__':
    M.main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None, semis=SEMIS, voices=VOICES, scale=SCALE, warm_db=0.0, comp=1.3, rev=0.15, seed=263, pres_db=3.0)
