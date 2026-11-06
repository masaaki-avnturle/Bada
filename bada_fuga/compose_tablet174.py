#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLXXIV · Le due tracce sul 173 (tablet173・トラック 18・トラック 8 で曲を)
  3 つの音声だけ、楽器は加えない: tablet173 (CLXXIII — tablet162 + 18:54 × 3) を全曲そのまま (0.45)、その上にトラック 18 (ニ短調、そのまま) とトラック 8 (4 度上げてヘ長調 / ニ短調に) を実音のまま段落ごとに重ねる
    I: トラック 18 → II: トラック 8 (全部) → III: トラック 18 (2 回目) → IV: トラック 8 の続き、消える。ヘ長調 / ニ短調、♩=60
  使い方: python compose_tablet174.py <bank150.json> <wav のフォルダ (20261107_173000.wav, 20261107_180000.wav, 20261107_080000.wav)> [score_tablet174.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet174.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
R173, R18, R08 = '20261107_173000', '20261107_180000', '20261107_080000'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 40, 104, 148, 184
NAMES = {R173: 'tablet173', R18: 'トラック 18', R08: 'トラック 8'}
RATE = lambda semis: 2 ** (semis / 12.0)
PLAYS = [(R173, 0, 0.45, 0, 0.0, 735.0, True),
         (R18, 2, 0.5, 0, 0.0, 149.1, True),                       # I: トラック 18 (37 小節)
         (R08, S2 + 1, 0.45, 5, 0.0, 249.2, True),                 # II: トラック 8 を 4 度上げて (187 秒 = 47 小節)
         (R18, S3 + 1, 0.5, 0, 0.0, 149.1, True),                  # III: トラック 18 (2 回目)
         (R08, S4 + 1, 0.42, 5, 100.0, 149.2, True)]               # IV: トラック 8 の続き (100 秒から、112 秒)
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    LOOP = ['Dm', 'Bb', 'F', 'C']
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. トラック 18 (♩=60)', 'tablet173 の始まり (06:42・トラック 18・18:54) の上にトラック 18 の実音 (ニ短調、そのまま)')
    P.section(S2, 'II. トラック 8 (4 度上げて)', 'tablet173 の 06:39 の段の上にトラック 8 の実音の全部 (ハ長調 / イ短調 → ヘ長調 / ニ短調)')
    P.section(S3, 'III. トラック 18 (2 回目)', 'tablet173 の頂点の段の上にトラック 18 をもう一度')
    P.section(S4, 'IV. トラック 8 の続き、消える', 'tablet173 の終わりの上にトラック 8 の続き (100 秒から)、少しずつ消える')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 4.0, fout=8.0, semis=sm, rid=rid + '.wav', tag='%s — 実音%s' % (NAMES[rid], '、4 度上げて' if sm else '、そのまま'))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R18, R08, R173], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CLXXIV · Le due tracce sul 173',
        'subtitle': 'tablet173・トラック 18・トラック 8 で: tablet173 (tablet162 + 18:54 × 3) を全曲そのまま、その上にトラック 18 (そのまま) とトラック 8 (4 度上げて) を実音のまま段落ごとに。楽器は加えない。ヘ長調 / ニ短調、♩=60',
        'legend': [], 'vname': {},
        'footer': ['tablet173 は 0.45 で全曲。トラック 18 (ニ短調) はそのまま 2 回 (0.5)、トラック 8 (ハ長調 / イ短調) は 4 度上げてヘ長調 / ニ短調に (0.45、終わりは続きを 0.42)。4 秒のフェード・イン、8 秒のフェード・アウト', '楽器を加えない、鐘なし、声なし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=174, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
