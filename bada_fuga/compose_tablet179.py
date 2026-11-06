#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLXXIX · Il 18:54 sul 157 — continuo (tablet157 と 2026/11/06 18:54 を、余計な楽器を付け加えずにミックス、2 つ目の配置)
  CLXXVIII と同じ 2 つの音声だけ (楽器なし) で、配置を変える: tablet157 (CLVII) を全曲 (0.5)、11/06 18:54 の実音 (rms −22 dB に揃えたもの) を **途切れなく続けて** (3 回半、切れ目は 6 秒のクロスフェード、0.5) 同じ大きさで重ねる。終わりは 2 つとも一緒に消える
  使い方: python compose_tablet179.py <bank150.json> <wav のフォルダ (20261107_157000.wav, 20261106_185402.wav)> [score_tablet179.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet179.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
R157, R1854 = '20261107_157000', '20261106_185402'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 50, 100, 150, 176
NAMES = {R157: 'tablet157', R1854: '11/06 18:54'}
PLAYS = [(R157, 0, 0.5, 0, 0.0, 703.0, True)] + [(R1854, k * 50, 0.5, 0, 0.0, 205.8 if k < 3 else 103.0, True) for k in range(4)]   # 18:54 を 50 小節 (200 秒) ごとに、切れ目は重ねてクロスフェード
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    LOOP = ['G', 'Dm7', 'C', 'G']
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. 18:54 の 1 回目 (♩=60)', 'tablet157 の 06:39 の段 (脈とマントラ) と 18:54 の実音を同じ大きさで')
    P.section(S2, 'II. 18:54 の 2 回目', 'tablet157 のトラック 18 の段と (切れ目はクロスフェード)')
    P.section(S3, 'III. 18:54 の 3 回目', 'tablet157 のトラック 8 の頂点と')
    P.section(S4, 'IV. 18:54 の 4 回目 (半分)', 'tablet157 の 06:39 の帰りと 18:54 の前半、2 つとも一緒に消える')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if dur > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — 実音%s' % (NAMES[rid], '、そのまま 3 回リピート' if rid == R1854 else '、全曲そのまま'))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R1854, R157], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CLXXIX · Il 18:54 sul 157 — continuo',
        'subtitle': 'tablet157 と 11/06 18:54 を、余計な楽器を付け加えずにミックス (2 つ目の配置): tablet157 を全曲、18:54 の実音を途切れなく続けて (3 回半、切れ目はクロスフェード) 同じ大きさで重ねる。ト長調 / ニ短調 / ハ長調、♩=60',
        'legend': [], 'vname': {},
        'footer': ['18:54 の録音は rms −22 dB に揃えて (tanh で軽く抑える) 途切れなく 3 回半 (0.5、切れ目は 6 秒のクロスフェード)。tablet157 は 0.5 で全曲', '楽器を加えない (tablet157 の中の実音のピアノはそのまま)、鐘なし、声なし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=179, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
