#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXCIII · I due pomeriggi sul 185 (tablet185 の原曲と 2026/11/08 13:10・13:16 だけで — この曲に無い楽器は使わない)
  3 つの音声だけ、楽器は何も加えない: tablet185 (CLXXXV — 18:54・トラック 8・18 とそのピアノ、ヘ長調 / ニ短調) を原曲の音声そのまま全曲 (0.5)、その上に 11/08 13:10 (ハ長調 / イ短調 → 4 度上げてヘ長調 / ニ短調に) と 13:16 (変イ長調 / ヘ短調 → 短 3 度下げてヘ長調 / ニ短調に) の実音を段落ごとに (0.55)
    I: 13:10 → II: 13:16 → III: 13:10 (2 回目) → IV: 13:16 の前半、消える。♩=60
  使い方: python compose_tablet193.py <bank150.json> <wav のフォルダ (20261107_185000.wav, 20261108_131016.wav, 20261108_131650.wav)> [score_tablet193.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet193.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
R185, R1310, R1316 = '20261107_185000', '20261108_131016', '20261108_131650'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 40, 100, 140, 176
NAMES = {R185: 'tablet185', R1310: '11/08 13:10', R1316: '11/08 13:16'}
RATE = lambda semis: 2 ** (semis / 12.0)
PLAYS = [(R185, 0, 0.5, 0, 0.0, 695.0, True),
         (R1310, 2, 0.55, 5, 0.0, 192.7, True),                    # I: 13:10 を 4 度上げて (144 秒 = 36 小節)
         (R1316, S2 + 1, 0.55, -3, 0.0, 187.4, True),              # II: 13:16 を短 3 度下げて (223 秒 = 56 小節)
         (R1310, S3 + 1, 0.55, 5, 0.0, 192.7, True),               # III: 13:10 (2 回目)
         (R1316, S4 + 1, 0.5, -3, 0.0, 118.0, True)]               # IV: 13:16 の前半、終わりまで
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    LOOP = ['Dm', 'Bb', 'F', 'C']
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. 13:10 (♩=60)', 'tablet185 の始まり (18:54 とトラック 18) の上に 11/08 13:10 の実音 (4 度上げてヘ長調 / ニ短調に)')
    P.section(S2, 'II. 13:16 (短 3 度下げて)', 'tablet185 のトラック 8 の段の上に 11/08 13:16 の実音の全部 (変イ長調 / ヘ短調 → ヘ長調 / ニ短調)')
    P.section(S3, 'III. 13:10 (2 回目)', 'tablet185 の 2 つの旋律の段の上に 13:10 をもう一度')
    P.section(S4, 'IV. 13:16 の前半、消える', 'tablet185 の終わりの上に 13:16 の前半、少しずつ消える')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 4.0, fout=8.0, semis=sm, rid=rid + '.wav', tag='%s — %s' % (NAMES[rid], {5: '実音、4 度上げて', -3: '実音、短 3 度下げて', 0: '原曲、全曲そのまま'}[sm]))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R1310, R1316, R185], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CXCIII · I due pomeriggi sul 185',
        'subtitle': 'tablet185 の原曲と 11/08 13:10・13:16 だけで、この曲に無い楽器は使わない: tablet185 を全曲そのまま、その上に 13:10 (4 度上げて) と 13:16 (短 3 度下げて) の実音を段落ごとに。ヘ長調 / ニ短調、♩=60',
        'legend': [], 'vname': {},
        'footer': ['tablet185 (CLXXXV) は原曲の音声そのまま 0.5 で全曲。13:10 (ハ長調 / イ短調、3 分 13 秒) は 4 度上げて 2 回 (0.55)、13:16 (変イ長調 / ヘ短調、3 分 7 秒) は短 3 度下げて全部と前半 (0.55 / 0.5)。4 秒のフェード・イン、8 秒のフェード・アウト', '楽器は何も加えない (サンプラーのピアノも、ペダルも、鐘も、声もなし)。']}

if __name__ == '__main__':
    compose.main(OUT, seed=193, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
