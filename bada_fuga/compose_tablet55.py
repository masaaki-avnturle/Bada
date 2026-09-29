#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LV · Klavier & Taiko (実音のピアノ主体に、和太鼓に近い重低音のゆっくりしたドラム)
  楽譜と実音のピアノの 4 声は LIV まで (XLVIII〜) とまったく同じ。シンセの音はなし。
  キック・スネア・ハイハット (ジャングル) をやめ、和太鼓をまねた太鼓 (synth.py の acoustic_drum: 張った膜の固有振動の和、太い木の撥の柔らかい当たり、胴の響き):
    大太鼓 (46 Hz、1.3 秒響く「ドン」) と長胴太鼓 (72 Hz、連打)。
  ゆっくり (♩=56 の拍) の 3 小節で一回り:
    「っど・っど・っど・っど」(拍の裏に大太鼓) →「どどど」(長胴太鼓の 8 分 3 つ) →「っど・っど・っど・っど」→「どどどど」(長胴太鼓の 8 分 4 つ)
  太鼓が入る所: Fuga I の 5 小節目から終わりまで、Fuga II の 2 小節目から終わりまで。Klang I・Klang II の頭と、Amen の長調の和音で大太鼓の大きな一打。
  使い方: python compose_tablet55.py <bank37.json> [score_tablet55.json]
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
HITS = ((0.5, 'odaiko', 1.0), (1.5, 'odaiko', 0.9), (2.5, 'odaiko', 0.95), (3.5, 'odaiko', 0.9),        # っど・っど・っど・っど
        (4.0, 'nagado', 0.8), (4.5, 'nagado', 0.85), (5.0, 'nagado', 1.0),                               # どどど
        (6.5, 'odaiko', 1.0), (7.5, 'odaiko', 0.9), (8.5, 'odaiko', 0.95), (9.5, 'odaiko', 0.9),        # っど・っど・っど・っど
        (10.0, 'nagado', 0.75), (10.5, 'nagado', 0.8), (11.0, 'nagado', 0.9), (11.5, 'nagado', 1.0))    # どどどど

def post(P, events, extras):
    for b0, b1, lvl in TAIKO:                      # 3 小節の型を区間の頭から繰り返す (区間の終わりで切る)
        for c0 in range(b0 * BPB, b1 * BPB, CYCLE):
            for t, kd, g in HITS:
                if c0 + t < b1 * BPB: add('AD', c0 + t, 1.0, 36, lvl * g, None, kind=kd)
    for bar, lvl in BIG: add('AD', bar * BPB, 1.5, 36, lvl, None, kind='odaiko')

def build():
    P = K.build()                                  # シンセ・ジャングルの build は使わない
    # 区間の小節 (XLVIII): Introitus 0-4 · Klang I 4-6 · Fuga I 6-22 · Kyrie 22-30 · Klang II 30-32 · Fuga II 32-48 · Amen 48-51
    TAIKO.append((10, 22, 0.14)); TAIKO.append((33, 48, 0.14))
    for bar in (4, 30, 49): BIG.append((bar, 0.2))
    return P

META = dict(T.META,
    title='Requiem BADA — LV · Klavier & Taiko',
    subtitle='実音のピアノ主体に、和太鼓に近い重低音のゆっくりした太鼓「っど・っど・っど・っど・どどど」(♩=56)',
    legend=['TB', 'AD'], vname={'AD': '和太鼓'},
    footer=['Introitus 08:49 → Klang I (大太鼓) → Fuga I (5 小節目から太鼓) → Kyrie → Klang II (大太鼓) → Fuga II (太鼓) → Amen (大太鼓、ヘ長調)',
            '4 声は録音から切り出したピアノの実音。太鼓は和太鼓 (大太鼓・長胴太鼓) の鳴り方をまねたもの。キックとシンセの音は使わない。曲だけの演奏。'])

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet55.json'
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
