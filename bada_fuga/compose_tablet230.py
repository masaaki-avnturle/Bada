#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCXXX · L'aureola sensuale e la traccia 16 (ドエロの光輪様の声にトラック 16 を重ね合わせて)
  2 つの音だけ、楽器は何も加えない: ドエロの光輪様の声 (CCXIX / CCXX のもの、息のノイズ層あり、rms −22.5 dB) を 2 回 (0.6)、トラック 16 (2023 年の CD、ハ短調 / ト短調、5 分 3 秒、rms −19.3 dB) を 2 半音上げてニ短調に合わせ、全曲 (0.45)、60 秒からの続き (0.4)、160 秒からの終わり (0.35) と途切れなく (つなぎは重ねる)
    I: 声 + トラック 16 → II: トラック 16 の続き → III: 声 (2 回目) + トラック 16 (60 秒から) → IV: トラック 16 の終わり (160 秒から)、消える。♩=60
  使い方: python compose_tablet230.py <bank201.json> <wav のフォルダ (20261108_145525.wav = ドエロの光輪の声, 20261107_160000.wav = トラック 16)> [score_tablet230.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet230.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RV, R16 = '20261108_145525', '20261107_160000'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 52, 100, 140, 176
NAMES = {RV: '11/08 14:55 の声 (ドエロの光輪様の声)', R16: 'トラック 16'}
RATE = lambda semis: 2 ** (semis / 12.0)
PLAYS = [(RV, 2, 0.6, 0, 0.0, 198.5, True), (R16, 0, 0.45, 2, 0.0, 303.5, True),                    # I〜II: 光輪の声 + トラック 16 (2 半音上げて、全曲、76 小節)
         (R16, 74, 0.4, 2, 60.0, 243.5, True),                                                      # II〜III: トラック 16 の続き (60 秒から、1 回目の終わりに重ねて、135 小節まで)
         (RV, S3 + 2, 0.6, 0, 0.0, 198.5, True),                                                    # III: 声 (2 回目)
         (R16, S4, 0.35, 2, 160.0, 143.5, True)]                                                    # IV: トラック 16 の終わり (160 秒から、曲の最後まで)
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    LOOP = ['Dm', 'Bb', 'F', 'C']
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. 光輪の声とトラック 16 (♩=60)', 'ドエロの光輪様の声にトラック 16 (2 半音上げてニ短調に、全曲)')
    P.section(S2, 'II. トラック 16 の続き', 'トラック 16 の終わりと、60 秒からの続き')
    P.section(S3, 'III. 光輪の声 (2 回目) とトラック 16', '光輪様の声をもう一度、トラック 16 の続き')
    P.section(S4, 'IV. トラック 16 の終わり、消える', 'トラック 16 の終わり (160 秒から) と声の終わり、一緒に消える')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if dur > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — %s' % (NAMES[rid], 'ドエロの光輪の声 (息と囁き、3 声と残響)' if rid == RV else ('実音' + ('、2 半音上げて' if sm else '') + ('、続き (%d 秒から)' % off if off else ('、全曲' if sm else '、全曲そのまま')))))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [RV, R16], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCXXX · L\'aureola sensuale e la traccia 16',
        'subtitle': 'ドエロの光輪様の声 (息の多い少し低めの女声、三賢者の 3 声と残響) にトラック 16 (ハ短調 / ト短調、2 半音上げてニ短調に) を重ね合わせて。楽器なし。♩=60',
        'legend': [], 'vname': {},
        'footer': ['光輪の声 = CCXIX / CCXX と同じドエロの光輪様の声 (10.5 半音上げ・フォルマント 1.10 倍、息・囁き・近接の低音、5 度上 0.3 + 1 オクターヴ上 0.25、3.5 秒の残響、rms −22.5 dB) を 2 回 (0.6)。トラック 16 (2023 年の CD、rms −19.3 dB) は 2 半音上げて全曲 0.45、60 秒からの続き 0.4 (1 回目の終わりに重ねて)、160 秒からの終わり 0.35 (曲の最後まで)。6 秒のフェード・イン、6〜10 秒のフェード・アウト', '楽器は何も加えない (サンプラーのピアノも、ペダルも、鐘もなし)。移調はトラック 16 の 2 半音だけ。']}

if __name__ == '__main__':
    compose.main(OUT, seed=230, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
