#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLXXVIII · Il 18:54 sul 157 (tablet157 と 2026/11/06 18:54 をミックス)
  2 つの音声だけ、楽器は加えない: tablet157 (CLVII — 06:39・トラック 18・トラック 8 のマントラ、11 分 43 秒、中の実音のピアノはそのまま) を全曲 (0.5)、11/06 18:54 の実音 (3 分 26 秒、rms −22 dB に揃えたもの) を 3 回リピートして重ねる (0.55)
    I: 18:54 の 1 回目 (06:39 の段) → II: 2 回目 (トラック 18 の段) → III: 3 回目 (トラック 8 の頂点) → IV: tablet157 の終わりだけ (06:39 の帰り)。ト長調 / ニ短調 / ハ長調、♩=60
  使い方: python compose_tablet178.py <bank150.json> <wav のフォルダ (20261107_157000.wav, 20261106_185402.wav)> [score_tablet178.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet178.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
R157, R1854 = '20261107_157000', '20261106_185402'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 54, 108, 162, 176
NAMES = {R157: 'tablet157', R1854: '11/06 18:54'}
PLAYS = [(R157, 0, 0.5, 0, 0.0, 703.0, True),
         (R1854, 2, 0.55, 0, 0.0, 205.8, True), (R1854, S2 + 2, 0.55, 0, 0.0, 205.8, True), (R1854, S3 + 2, 0.52, 0, 0.0, 205.8, True)]
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    LOOP = ['G', 'Dm7', 'C', 'G']
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. 18:54 の 1 回目 (♩=60)', 'tablet157 の 06:39 の段 (脈とマントラ) の上に、18:54 の実音')
    P.section(S2, 'II. 18:54 の 2 回目', 'tablet157 のトラック 18 の段の上に')
    P.section(S3, 'III. 18:54 の 3 回目', 'tablet157 のトラック 8 の頂点の上に')
    P.section(S4, 'IV. tablet157 の終わり', '06:39 の帰りだけが残って消える')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 4.0, fout=8.0, semis=sm, rid=rid + '.wav', tag='%s — 実音%s' % (NAMES[rid], '、そのまま 3 回リピート' if rid == R1854 else '、全曲そのまま'))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R1854, R157], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CLXXVIII · Il 18:54 sul 157',
        'subtitle': 'tablet157 と 11/06 18:54 をミックス: tablet157 (06:39・トラック 18・トラック 8 のマントラ、中の実音のピアノはそのまま) を全曲、18:54 の実音を 3 回リピートして重ねる。楽器を加えない。ト長調 / ニ短調 / ハ長調、♩=60',
        'legend': [], 'vname': {},
        'footer': ['18:54 の録音は rms −22 dB に揃えて (tanh で軽く抑える) そのまま 3 回 (0.55、4 秒のフェード・イン、8 秒のフェード・アウト)。tablet157 は 0.5 で全曲', '楽器を加えない (tablet157 の中の実音のピアノはそのまま)、鐘なし、声なし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=178, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
