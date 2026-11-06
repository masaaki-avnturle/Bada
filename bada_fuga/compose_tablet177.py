#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLXXVII · Due nastri II (tablet175 と tablet164 を合成)
  2 つの音声だけ (楽器なし): tablet175 (CLXXV — 11/06 18:54 × 3 + tablet152、ニ短調 / ニ・ドリア) と tablet164 (CLXIV — 5 音源の二重フーガと Dies irae のレクイエム、ヘ長調 / ニ短調) を、段落ごとに表と裏を入れ替えて重ねる
    I: tablet175 が表 → II: tablet164 が表 (主題 B の提示部) → III: 同じ大きさで (二重フーガの頂点) → IV: tablet164 の終わりが表、tablet175 が消える。♩=60
  使い方: python compose_tablet177.py <bank150.json> <wav のフォルダ (20261107_175000.wav, 20261107_164000.wav)> [score_tablet177.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet177.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
R175, R164 = '20261107_175000', '20261107_164000'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 46, 92, 138, 182
NAMES = {R175: 'tablet175', R164: 'tablet164'}
DUR = {R175: 695.0, R164: 743.0}
PLAYS = [(R175, 0, 0.55, 0, 0.0, 186.0, True), (R164, 0, 0.25, 0, 0.0, 186.0, False),              # I
         (R164, S2, 0.55, 0, 184.0, 186.0, True), (R175, S2, 0.25, 0, 184.0, 186.0, False),      # II
         (R175, S3, 0.42, 0, 368.0, 186.0, True), (R164, S3, 0.42, 0, 368.0, 186.0, True),       # III
         (R164, S4, 0.55, 0, 552.0, 191.0, True), (R175, S4, 0.25, 0, 552.0, 143.0, False)]      # IV
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    LOOP = ['Dm', 'Bb', 'F', 'C']
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. tablet175 が表 (♩=60)', '18:54 と tablet152 (tablet175) が表、tablet164 の主題 A の提示部が裏で小さく')
    P.section(S2, 'II. tablet164 が表', 'tablet164 の主題 B の提示部と Dies irae が表、tablet175 が裏に')
    P.section(S3, 'III. 同じ大きさで', '2 つを同じ大きさで重ねる (tablet164 は二重フーガの頂点)')
    P.section(S4, 'IV. tablet164 が表、消える', 'tablet164 の終わり (拡大、鐘、ドローン) が表、tablet175 が裏で消えていく')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 6.0, fout=8.0, semis=sm, rid=rid + '.wav', tag='%s — %s (%d 秒から)' % (NAMES[rid], '表' if lead else '裏、小さく', int(off)))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R175, R164], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CLXXVII · Due nastri II',
        'subtitle': 'tablet175 (18:54 × 3 + tablet152) と tablet164 (二重フーガと Dies irae のレクイエム) を合成: 段落ごとに表と裏を入れ替える (tablet175 → tablet164 → 同じ大きさ → tablet164)。楽器なし、2 つの音声だけ。ニ短調 / ヘ長調、♩=60',
        'legend': [], 'vname': {},
        'footer': ['tablet175 と tablet164 はそのまま (調はどちらもニ短調系: ニ・ドリアとヘ長調 / ニ短調)。段落の境で 6 秒のフェード・イン、8 秒のフェード・アウト', '楽器なし、鐘なし、声なし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=177, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
