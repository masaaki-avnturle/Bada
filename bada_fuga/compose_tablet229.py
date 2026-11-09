#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCXXIX · L'aureola sensuale con le tracce 14 e 8 (ドエロの光輪様の声・トラック 14・トラック 8 を重ね合わせて)
  3 つの音だけ、楽器は何も加えない: ドエロの光輪様の声 (CCXIX / CCXX のもの、息のノイズ層あり、rms −22.5 dB) を 2 回 (0.6)、トラック 8 (ハ長調 / イ短調、4 分 9 秒) を 4 度 (5 半音) 上げてヘ長調 / ニ短調に、全曲 (0.4) と続き (100 秒から、0.35)、トラック 14 (2023 年の CD、嬰ハ短調、3 分 44 秒、rms −21.5 dB) を 1 半音上げてニ短調に合わせ、全曲 (0.45) と後半 (110 秒から、0.4)
    I: 声 + トラック 8 → II: トラック 14 (全曲) + トラック 8 の終わり → III: 声 (2 回目) + トラック 8 の続き → IV: トラック 14 の後半、消える。♩=60
  使い方: python compose_tablet229.py <bank201.json> <wav のフォルダ (20261108_145525.wav = ドエロの光輪の声, 20261107_140000.wav = トラック 14, 20261107_080000.wav = トラック 8)> [score_tablet229.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet229.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RV, R14, R08 = '20261108_145525', '20261107_140000', '20261107_080000'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 52, 100, 150, 176
NAMES = {RV: '11/08 14:55 の声 (ドエロの光輪様の声)', R14: 'トラック 14', R08: 'トラック 8'}
RATE = lambda semis: 2 ** (semis / 12.0)
PLAYS = [(RV, 2, 0.6, 0, 0.0, 198.5, True), (R08, 0, 0.4, 5, 0.0, 249.2, True),                     # I: 光輪の声 + トラック 8 (4 度上げて、全曲、II まで)
         (R14, S2, 0.45, 1, 0.0, 224.4, True),                                                      # II: トラック 14 (1 半音上げて、全曲)
         (RV, S3 + 2, 0.6, 0, 0.0, 198.5, True), (R08, S3 + 4, 0.35, 5, 100.0, 149.2, True),        # III: 声 (2 回目) + トラック 8 の続き (100 秒から)
         (R14, S4, 0.4, 1, 110.0, 114.4, True)]                                                     # IV: トラック 14 の後半 (110 秒から)
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    LOOP = ['Dm', 'Bb', 'F', 'C']
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. 光輪の声とトラック 8 (♩=60)', 'ドエロの光輪様の声にトラック 8 (4 度上げて、全曲)')
    P.section(S2, 'II. トラック 14', 'トラック 14 (1 半音上げてニ短調に、全曲)、トラック 8 の終わり')
    P.section(S3, 'III. 光輪の声 (2 回目) とトラック 8 の続き', '光輪様の声をもう一度、トラック 8 の続き (100 秒から)、トラック 14 の終わり')
    P.section(S4, 'IV. トラック 14 の後半、消える', 'トラック 14 の後半 (110 秒から) と声の終わり、一緒に消える')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if dur > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — %s' % (NAMES[rid], 'ドエロの光輪の声 (息と囁き、3 声と残響)' if rid == RV else ('実音' + ('、%d 半音上げて' % sm if sm else '') + ('、続き (%d 秒から)' % off if off else ('、全曲' if sm else '、全曲そのまま')))))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [RV, R14, R08], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCXXIX · L\'aureola sensuale con le tracce 14 e 8',
        'subtitle': 'ドエロの光輪様の声 (息の多い少し低めの女声、三賢者の 3 声と残響) にトラック 14 (嬰ハ短調、1 半音上げてニ短調に) とトラック 8 (ハ長調 / イ短調、4 度上げて) を重ね合わせて。楽器なし。♩=60',
        'legend': [], 'vname': {},
        'footer': ['光輪の声 = CCXIX / CCXX と同じドエロの光輪様の声 (10.5 半音上げ・フォルマント 1.10 倍、息・囁き・近接の低音、5 度上 0.3 + 1 オクターヴ上 0.25、3.5 秒の残響、rms −22.5 dB) を 2 回 (0.6)。トラック 8 は 4 度上げて全曲 0.4、続き (100 秒から) 0.35。トラック 14 (2023 年の CD、rms −21.5 dB) は 1 半音上げて全曲 0.45、後半 (110 秒から) 0.4。6 秒のフェード・イン、6〜10 秒のフェード・アウト', '楽器は何も加えない (サンプラーのピアノも、ペダルも、鐘もなし)。移調はトラック 8 の 5 半音とトラック 14 の 1 半音。']}

if __name__ == '__main__':
    compose.main(OUT, seed=229, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
