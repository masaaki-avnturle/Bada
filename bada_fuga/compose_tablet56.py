#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LVI · Klavier & Taiko II (LV の太鼓を「っどー・っどー・っどー・っど・っど・っど・どど・っどー・っどー」に)
  楽譜・実音のピアノの 4 声・和太鼓をまねた太鼓 (大太鼓 46 Hz・長胴太鼓 72 Hz) は LV (compose_tablet55.py) と同じ。シンセ・キックなし。変えたのは太鼓の型:
  ♩=56 の拍の 3 小節 (12 拍) で一回り —
    「っどー・っどー・っどー」(0.5・2・3.5 拍目、大太鼓を長く響かせる) →「っど・っど・っど」(5・6・7 拍目、長胴太鼓を手で押さえて短く)
    →「どど」(7.5・8 拍目、長胴太鼓を短く) →「っどー・っどー」(9・10.5 拍目、大太鼓を長く)。
  太鼓が入る所と、Klang・Amen の大太鼓の一打は LV と同じ。
  使い方: python compose_tablet56.py <bank37.json> [score_tablet56.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet53 as T                       # LIII: XLVIII の楽譜と、弦・シンセを鳴らさない設定 (実音のピアノの 4 声)

K = T.K
add = CT.add
TAIKO, BIG = [], []
CYCLE = 12                                         # 3 小節 = 12 拍で一回り
HITS = ((0.5, 'odaiko', 1.0, None), (2.0, 'odaiko', 0.95, None), (3.5, 'odaiko', 1.0, None),               # っどー・っどー・っどー (長く)
        (5.0, 'nagado', 0.8, 0.35), (6.0, 'nagado', 0.8, 0.35), (7.0, 'nagado', 0.85, 0.35),              # っど・っど・っど (短く)
        (7.5, 'nagado', 0.8, 0.25), (8.0, 'nagado', 0.9, 0.25),                                           # どど (短く)
        (9.0, 'odaiko', 1.0, None), (10.5, 'odaiko', 1.0, None))                                          # っどー・っどー (長く)

def post(P, events, extras):
    for b0, b1, lvl in TAIKO:                      # 3 小節の型を区間の頭から繰り返す (区間の終わりで切る)
        for c0 in range(b0 * BPB, b1 * BPB, CYCLE):
            for t, kd, g, damp in HITS:
                if c0 + t < b1 * BPB:
                    kw = {'damp': damp} if damp else {}
                    add('AD', c0 + t, 1.0, 36, lvl * g, None, kind=kd, **kw)
    for bar, lvl in BIG: add('AD', bar * BPB, 1.5, 36, lvl, None, kind='odaiko')

def build():
    P = K.build()                                  # シンセ・ジャングルの build は使わない
    # 区間の小節 (XLVIII): Introitus 0-4 · Klang I 4-6 · Fuga I 6-22 · Kyrie 22-30 · Klang II 30-32 · Fuga II 32-48 · Amen 48-51
    TAIKO.append((10, 22, 0.14)); TAIKO.append((33, 48, 0.14))
    for bar in (4, 30, 49): BIG.append((bar, 0.2))
    return P

META = dict(T.META,
    title='Requiem BADA — LVI · Klavier & Taiko II',
    subtitle='実音のピアノ主体に、和太鼓の「っどー・っどー・っどー・っど・っど・っど・どど・っどー・っどー」(♩=56)',
    legend=['TB', 'AD'], vname={'AD': '和太鼓'},
    footer=['Introitus 08:49 → Klang I (大太鼓) → Fuga I (5 小節目から太鼓) → Kyrie → Klang II (大太鼓) → Fuga II (太鼓) → Amen (大太鼓、ヘ長調)',
            '4 声は録音から切り出したピアノの実音。太鼓は和太鼓 (大太鼓・長胴太鼓) の鳴り方をまねたもの。キックとシンセの音は使わない。曲だけの演奏。'])

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet56.json'
    compose.main(out, seed=148, bpm=K.BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n in d['notes']: n['dyn'] = round(n.get('dyn', 1.0) * 1.25, 4)   # 4 声のピアノの実音を前に (LI〜LIV と同じ)
    for s in d['sections']:
        for a, b in (('主題が入るたびに、その声部の歌い手が歌う', '主題が 4 声に次々と入る'), ('5 人が和声で歌う', 'ピアノの 4 声が和声で'),
                     ('全員が 9 度', 'ピアノが 9 度'), ('5 人が「Amen」を長く歌い、', ''), ('最後はストレッタで歌い手が重なる', '最後はストレッタで主題が重なる'),
                     (' (ビオラはアルトの声部)', ''), (' (ビオラは内声)', ''), ('オルガン・ビオラ・弦が長調の和音で包む', 'ピアノが長調の和音で包み、大太鼓が一打'),
                     ('大聖堂に響く 08:49 の録音 — 弦がそっと寄り添う', '08:49 のピアノの実音 (録音)')):
            s['sub'] = s['sub'].replace(a, b)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), Counter(e.get('kind') for e in d['extras'] if e['v'] == 'AD'))
