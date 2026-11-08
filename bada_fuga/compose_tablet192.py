#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXCII · Il 18:54 sul 89 — solo l'originale (tablet89 の原曲と 2026/11/06 18:54 だけで — この曲に無い楽器は使わない)
  2 つの音声だけ、楽器は何も加えない (06:42 の実音のピアノのサンプラーも tablet89 には無い楽器なので使わない): tablet89 (LXXXIX、ニ短調、6 分 31 秒) を全曲そのまま (0.5) と後半 (90 秒から、0.45)、11/06 18:54 の実音 (rms −22 dB に揃えたもの) を途切れなく 3 回半 (0.5、切れ目はクロスフェード)
  使い方: python compose_tablet192.py <bank150.json> <wav のフォルダ (20261107_089000.wav, 20261106_185402.wav)> [score_tablet192.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet192.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
R89, R1854 = '20261107_089000', '20261106_185402'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 50, 100, 150, 176
NAMES = {R89: 'tablet89', R1854: '11/06 18:54'}
PLAYS = [(R89, 0, 0.5, 0, 0.0, 391.0, True), (R89, 100, 0.45, 0, 90.0, 300.0, True)] + [(R1854, k * 50, 0.5, 0, 0.0, 205.8 if k < 3 else 103.0, True) for k in range(4)]   # 18:54 を 50 小節 (200 秒) ごとに、切れ目は重ねてクロスフェード
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    LOOP = ['Dm', 'Bb', 'F', 'C']
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. 18:54 の 1 回目 (♩=60)', 'tablet89 の始まり (レクイエム) と 18:54 の実音を同じ大きさで')
    P.section(S2, 'II. 18:54 の 2 回目', 'tablet89 の続き (フーガ) と (切れ目はクロスフェード)')
    P.section(S3, 'III. 18:54 の 3 回目', 'tablet89 の後半 (90 秒から、2 回目) と')
    P.section(S4, 'IV. 18:54 の 4 回目 (半分)', 'tablet89 の終わりと 18:54 の前半、2 つとも一緒に消える')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if dur > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — 原曲%s' % (NAMES[rid], '、途切れなく 3 回半' if rid == R1854 else ('、全曲そのまま' if off == 0 else '、後半 (90 秒から)')))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R89, R1854], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CXCII · Il 18:54 sul 89 — solo l\'originale',
        'subtitle': 'tablet89 の原曲と 11/06 18:54 だけで、この曲に無い楽器は使わない: tablet89 を全曲と後半、18:54 の実音を途切れなく 3 回半、同じ大きさで重ねる。ニ短調、♩=60',
        'legend': [], 'vname': {},
        'footer': ['tablet89 (LXXXIX) は原曲の音声そのまま 0.5、後半 (90 秒から) をもう一度 0.45。18:54 は rms −22 dB に揃えて途切れなく 3 回半 (0.5、切れ目は 6 秒のクロスフェード)', '楽器は何も加えない (サンプラーのピアノも、ペダルも、鐘も、声もなし)。']}

if __name__ == '__main__':
    compose.main(OUT, seed=192, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
