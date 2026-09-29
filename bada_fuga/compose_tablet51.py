#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LI · Herzschlag & Jungle — Klavier (L を実音のピアノだけに、ピアノのように弾くきれいなシンセを加えて)
  楽譜 (4 声・Klang・フーガ・コラール・Amen)、鼓動の不整脈、ジャングルのビートは L (compose_tablet50.py) とまったく同じ。変えたのは楽器だけ:
    - 4 声はパイプオルガンをやめ、録音から切り出したピアノの実音で弾く (Introitus の 08:49 の録音もピアノの実音)
    - シンセの弦・ビオラ・チェロ・コントラバスを外す — 冒頭で 08:49 の録音に重なってゆっくり膨らんでいた (音が上がって聞こえた) のはこの弦
    - ピアノのように弾くきれいなシンセ (synth.py の synth_piano: 打鍵で明るく、ピアノのように暗くなりながら減衰、4 kHz より上は出さない) を加える:
        Klang と Amen は下から上へ分散して弾く和音、Fuga I は主題の入りを 1 オクターヴ上で重ね、Kyrie と Fuga II の後半は 8 分の分散和音 (ピアノの左手のように)
  使い方: python compose_tablet51.py <bank37.json> [score_tablet51.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet50 as L

K = L.K
K.post = lambda P, events, extras: None           # XLVIII の弦・ビオラ・チェロ (シンセ) は鳴らさない
add = CT.add
ROLLED, DOUBLE, ARP = [], [], []

def post(P, events, extras):
    L.post(P, events, extras)                      # 鼓動とジャングル (L と同じ)
    for bar, lvl in ROLLED:                        # 分散して弾く和音: その小節の 4 声の音を下から上へ、0.09 拍ずつずらして
        ns = sorted({m for v in 'SATB' for s_, d, m, lab in events[v] if abs(s_ - bar * BPB) < 1e-6})
        for k, m in enumerate(ns): add('SY', bar * BPB + 0.09 * k, 3.8, m, lvl * (1.0 if k == 0 else 0.8), None, pan=-0.3 + 0.2 * k)
    for b0, b1, lvl in DOUBLE:                     # 主題の入り (置いた音 = ラベルのある音) を 1 オクターヴ上で重ねる
        for v in 'SATB':
            for s_, d, m, lab in events[v]:
                if b0 * BPB <= s_ < b1 * BPB and lab and lab.startswith('主題'):
                    while m + 12 > 84: m -= 12
                    add('SY', s_, d, m + 12, lvl, None, pan={'S': -0.3, 'A': 0.3, 'T': 0.1, 'B': -0.1}[v])
    for b0, b1, lvl in ARP:                        # 8 分の分散和音 (左手のように): 根音・5 度・オクターヴ・3 度
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half]); r = K.low_root(c, 43); th = (c['third'] - c['root']) % 12
                for k, m in enumerate((r, r + 7, r + 12, r + 12 + th)):
                    add('SY', bar * BPB + half + 0.5 * k, 1.4 - 0.25 * k, m, lvl * (1.0 if k == 0 else 0.75), None, pan=0.2)

def build():
    P = L.build()
    # 区間の小節 (XLVIII): Introitus 0-4 · Klang I 4-6 · Fuga I 6-22 · Kyrie 22-30 · Klang II 30-32 · Fuga II 32-48 · Amen 48-51
    for bar in (4, 5, 30, 31, 48, 49): ROLLED.append((bar, 0.11))
    DOUBLE.append((6, 22, 0.07))
    for lst in (L.JUNGLE, L.SUB):                  # ピアノの実音が主役なので、ジャングルと重低音を少し下げる
        lst[:] = [(b0, b1, lvl * 0.85) for b0, b1, lvl in lst]
    L.SROLL[:] = [(bar, lvl * 0.85) for bar, lvl in L.SROLL]
    ARP.append((22, 30, 0.07)); ARP.append((40, 48, 0.06))
    return P

META = {k: v for k, v in L.META.items() if k not in ('choir', 'organ_gain')}   # 4 声はピアノの実音 (オルガンをやめる)
META.update(reverb=[4.8, 1.7, 0.42], heart_gain=0.42,
    title='Requiem BADA — LI · Herzschlag & Jungle (Klavier)',
    subtitle='実音のピアノと、ピアノのように弾くきれいなシンセに、鼓動の不整脈とジャングル (♩=56 / 168)',
    legend=['TB', 'SY', 'HB', 'DR', 'E8'], vname=dict(L.META['vname'], SY='シンセ (ピアノのように)'),
    footer=['Introitus 08:49 → Klang I → Fuga I (ジャングル) → Kyrie (鼓動だけ) → Klang II (不整脈) → Fuga II (ジャングル) → Amen',
            '4 声は録音から切り出したピアノの実音、シンセはピアノのように弾く (分散和音・主題の重ね)。冒頭で膨らんでいたシンセの弦は外した。曲だけの演奏。'])

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet51.json'
    compose.main(out, seed=148, bpm=K.BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n in d['notes']: n['dyn'] = round(n.get('dyn', 1.0) * 1.25, 4)   # 4 声のピアノの実音を前に (オルガンより小さく聞こえるので)
    for s in d['sections']:                        # 区間の説明: オルガン・ビオラ・弦・歌い手の記述を、ピアノとシンセに
        for a, b in (('主題が入るたびに、その声部の歌い手が歌う', '主題が 4 声に次々と入る'), ('5 人が和声で歌う', 'ピアノの 4 声が和声で'),
                     ('全員が 9 度', 'ピアノが 9 度'), ('5 人が「Amen」を長く歌い、', ''), ('最後はストレッタで歌い手が重なる', '最後はストレッタで主題が重なる'),
                     (' (ビオラはアルトの声部)', ''), (' (ビオラは内声)', ''), ('オルガン・ビオラ・弦が長調の和音で包む', 'ピアノとシンセが長調の和音で包む'),
                     ('大聖堂に響く 08:49 の録音 — 弦がそっと寄り添う', '08:49 のピアノの実音 (録音)')):
            s['sub'] = s['sub'].replace(a, b)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']))
