#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLXIX · Due nastri (tablet168 と tablet152 を合成して作り換え)
  2 つの音声だけ (楽器なし): tablet168 (CLXVIII — 11/06 18:54 の実音 3 回 + tablet166) と tablet152 (CLII — トラック 8・18 の旋律の二重フーガ、06:39 の空気) を、段落ごとに表と裏を入れ替えて重ねる
    I: tablet168 が表 → II: tablet152 が表 → III: 同じ大きさで → IV: tablet152 が表、tablet168 が消える。ニ短調 / ニ・ドリア、♩=60
  使い方: python compose_tablet169.py <bank150.json> <wav のフォルダ (20261107_168000.wav, 20261107_152000.wav)> [score_tablet169.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet169.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
R168, R152 = '20261107_168000', '20261107_152000'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 40, 85, 125, 170
NAMES = {R168: 'tablet168', R152: 'tablet152'}
DUR = {R168: 633.0, R152: 694.0}
PLAYS = [(R168, 0, 0.55, 0, 0.0, 162.0, True), (R152, 0, 0.25, 0, 0.0, 162.0, False),              # I
         (R152, S2, 0.55, 0, 160.0, 182.0, True), (R168, S2, 0.25, 0, 160.0, 182.0, False),      # II
         (R168, S3, 0.42, 0, 340.0, 162.0, True), (R152, S3, 0.42, 0, 340.0, 162.0, True),       # III
         (R152, S4, 0.55, 0, 500.0, 190.0, True), (R168, S4, 0.25, 0, 500.0, 133.0, False)]      # IV
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    LOOP = ['Dm7', 'Fmaj7', 'Gmaj7', 'D7']
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. tablet168 が表 (♩=60)', '18:54 の実音と tablet166 (tablet168) が表、tablet152 のフーガが裏で小さく')
    P.section(S2, 'II. tablet152 が表', 'トラック 8・18 の旋律の二重フーガ (tablet152) が表、tablet168 が裏に')
    P.section(S3, 'III. 同じ大きさで', '2 つを同じ大きさで重ねる')
    P.section(S4, 'IV. tablet152 が表、消える', 'tablet152 の終わりが表、tablet168 が裏で消えていく')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 6.0, fout=8.0, semis=sm, rid=rid + '.wav', tag='%s — %s (%d 秒から)' % (NAMES[rid], '表' if lead else '裏、小さく', int(off)))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R168, R152], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CLXIX · Due nastri',
        'subtitle': 'tablet168 (11/06 18:54 の実音 3 回 + tablet166) と tablet152 (トラック 8・18 の二重フーガ、06:39 の空気) を合成: 段落ごとに表と裏を入れ替える (tablet168 → tablet152 → 同じ大きさ → tablet152)。楽器なし、2 つの音声だけ。♩=60',
        'legend': [], 'vname': {},
        'footer': ['tablet168 と tablet152 はそのまま (調はどちらもニ短調 / ニ・ドリア)。段落の境で 6 秒のフェード・イン、8 秒のフェード・アウト', '楽器なし、鐘なし、声なし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=169, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
