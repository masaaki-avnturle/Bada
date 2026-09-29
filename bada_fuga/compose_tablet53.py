#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LIII · Klang und Fuge (Klavier & Trommeln) (LII に、実際の太鼓の鳴り方をまねたドラムの重低音のジャングルを)
  楽譜・実音のピアノの 4 声・中から入るピアノのようなシンセは LII (compose_tablet52.py) とまったく同じ。
  ドラム (synth.py の acoustic_drum: 張った膜の固有振動の和 = モード合成。808 やシンセのドラムの電子音は使わない):
    24 インチのバスドラム (52 Hz) とフロアタム (82 Hz) の胴鳴りが重低音、スネアは膜と響き線、ハイハットは小さく暗く。
  ジャングル (♩=168 = ♩=56 の 3 倍、オルガンの 1 小節にジャングルの 3 小節) の 1 小節:
    「っど・っど・っど・どどど」— 1〜3 拍目の裏にバスドラム、4 拍目は 16 分 3 つ (バスドラム・フロアタム・フロアタム)。
    その上にスネアの 2・4 拍 (ジャングルのバックビート) と小さなゴースト・スネア、8 分の小さなハイハット。区間の終わりはタムの連打。
  ドラムが入る所: Fuga I の 5 小節目から終わりまで、Fuga II の 2 小節目から終わりまで (Klang・Kyrie・Amen はドラムなし)
  使い方: python compose_tablet53.py <bank37.json> [score_tablet53.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet52 as LII

M, K = LII.M, LII.K
add = CT.add
J = 1.0 / 12                                       # ジャングルの 16 分音符 = ♩=56 の 1/12 拍
DRUMS, FILLS = [], []
KICK_STEPS = ((2, 'kick', 1.0), (6, 'kick', 1.0), (10, 'kick', 1.0),                       # っど・っど・っど
              (12, 'kick', 1.0), (13, 'floor', 0.9), (14, 'floor', 0.95))                  # どどど
SNARE_STEPS = ((4, 'snare', 1.0), (12, 'snare', 0.9), (7, 'ghost', 0.3), (9, 'ghost', 0.28), (15, 'ghost', 0.32))

def post(P, events, extras):
    M.post(P, events, extras)                      # ピアノのようなシンセ (LII と同じ)
    for b0, b1, lvl in DRUMS:
        for bar in range(b0, b1):
            for jb in range(3):
                base = bar * BPB + jb * 16 * J
                if (bar, jb) in FILLS: continue
                for st, kd, g in KICK_STEPS + SNARE_STEPS: add('AD', base + st * J, 0.3, 36, lvl * g * (0.8 if kd in ('snare', 'ghost') else 1.0), None, kind=kd)
                for st in range(0, 16, 2): add('AD', base + st * J, 0.05, 42, lvl * (0.16 if st % 4 == 0 else 0.1), None, kind='hat')
    for bar, jb in FILLS:                          # タムの連打: 前半はふつうの型、後半 (8〜15) はタム → フロアタム → バスドラムと下りながら強く
        base = bar * BPB + jb * 16 * J; lvl = next(l for b0, b1, l in DRUMS if b0 <= bar < b1)
        for st, kd, g in ((2, 'kick', 1.0), (4, 'snare', 0.8), (6, 'kick', 1.0), (7, 'ghost', 0.25)):
            add('AD', base + st * J, 0.3, 36, lvl * g, None, kind=kd)
        for k, kd in enumerate(('tom', 'tom', 'tom', 'floor', 'floor', 'floor', 'kick', 'kick')):
            add('AD', base + (8 + k) * J, 0.3, 36, lvl * (0.6 + 0.06 * k), None, kind=kd)

def build():
    P = LII.build()
    # 区間の小節 (XLVIII): Introitus 0-4 · Klang I 4-6 · Fuga I 6-22 · Kyrie 22-30 · Klang II 30-32 · Fuga II 32-48 · Amen 48-51
    DRUMS.append((10, 22, 0.15)); DRUMS.append((33, 48, 0.13))
    FILLS.extend([(21, 2), (47, 2)])               # 区間の最後のジャングル小節 (オルガンの小節, その中の 3 つ目)
    return P

META = dict(LII.META,
    title='Requiem BADA — LIII · Klavier & Trommeln',
    subtitle='実音のピアノに、太鼓の鳴り方をまねたドラムの重低音のジャングル「っど・っど・っど・どどど」(♩=56 / 168)',
    legend=['TB', 'SY', 'AD'], vname={'SY': 'シンセ (ピアノのように)', 'AD': 'ドラム'},
    footer=['Introitus 08:49 → Klang I → Fuga I (5 小節目からドラム) → Kyrie (シンセ) → Klang II → Fuga II (ドラム) → Amen (ヘ長調)',
            'ドラムは膜の固有振動をまねたバスドラム・フロアタム・スネア (808 やシンセのドラムは使わない)。4 声は録音から切り出したピアノの実音。曲だけの演奏。'])

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet53.json'
    compose.main(out, seed=148, bpm=K.BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n in d['notes']: n['dyn'] = round(n.get('dyn', 1.0) * 1.25, 4)   # 4 声のピアノの実音を前に (LI・LII と同じ)
    for s in d['sections']:
        for a, b in (('主題が入るたびに、その声部の歌い手が歌う', '主題が 4 声に次々と入る'), ('5 人が和声で歌う', 'ピアノの 4 声が和声で'),
                     ('全員が 9 度', 'ピアノが 9 度'), ('5 人が「Amen」を長く歌い、', ''), ('最後はストレッタで歌い手が重なる', '最後はストレッタで主題が重なる'),
                     (' (ビオラはアルトの声部)', ''), (' (ビオラは内声)', ''), ('オルガン・ビオラ・弦が長調の和音で包む', 'ピアノとシンセが長調の和音で包む'),
                     ('大聖堂に響く 08:49 の録音 — 弦がそっと寄り添う', '08:49 のピアノの実音 (録音)')):
            s['sub'] = s['sub'].replace(a, b)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']))
