#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LIV · Klavier & Trommeln (ohne Synth) (LIII からシンセの演奏を消し、実音のピアノとドラムだけに)
  楽譜・実音のピアノの 4 声・太鼓の鳴り方をまねたドラムの重低音のジャングル「っど・っど・っど・どどど」は LIII (compose_tablet53.py) とまったく同じ。
  消したもの: ピアノのようなシンセ (Kyrie・Fuga II 後半の分散和音、Klang II・Amen の分散する和音)。
  使い方: python compose_tablet54.py <bank37.json> [score_tablet54.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet53 as T

K = T.K

def build():
    P = T.build()
    for lst in (T.M.ROLLED, T.M.ARP, T.M.DOUBLE): lst.clear()                   # シンセの演奏はすべて消す
    return P

META = dict(T.META,
    title='Requiem BADA — LIV · Klavier & Trommeln',
    subtitle='実音のピアノと、太鼓をまねたドラムの重低音のジャングル「っど・っど・っど・どどど」(シンセなし)',
    legend=['TB', 'AD'], vname={'AD': 'ドラム'},
    footer=['Introitus 08:49 → Klang I → Fuga I (5 小節目からドラム) → Kyrie → Klang II → Fuga II (ドラム) → Amen (ヘ長調)',
            '4 声は録音から切り出したピアノの実音、ドラムは膜の固有振動をまねたバスドラム・フロアタム・スネア。シンセは使わない。曲だけの演奏。'])

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet54.json'
    compose.main(out, seed=148, bpm=K.BPM, builder=build, meta=META, extras=CT.extras, post=T.post)
    CT.finish(out)
    K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n in d['notes']: n['dyn'] = round(n.get('dyn', 1.0) * 1.25, 4)   # 4 声のピアノの実音を前に (LI〜LIII と同じ)
    for s in d['sections']:
        for a, b in (('主題が入るたびに、その声部の歌い手が歌う', '主題が 4 声に次々と入る'), ('5 人が和声で歌う', 'ピアノの 4 声が和声で'),
                     ('全員が 9 度', 'ピアノが 9 度'), ('5 人が「Amen」を長く歌い、', ''), ('最後はストレッタで歌い手が重なる', '最後はストレッタで主題が重なる'),
                     (' (ビオラはアルトの声部)', ''), (' (ビオラは内声)', ''), ('オルガン・ビオラ・弦が長調の和音で包む', 'ピアノが長調の和音で包む'),
                     ('大聖堂に響く 08:49 の録音 — 弦がそっと寄り添う', '08:49 のピアノの実音 (録音)')):
            s['sub'] = s['sub'].replace(a, b)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']))
