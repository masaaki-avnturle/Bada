#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LII · Klang und Fuge (Klavier) (LI から、始めのシンセ・ビート・鼓動を消し、中から上がるシンセだけを弾く)
  楽譜 (4 声・Klang・フーガ・コラール・Amen) は XLVIII〜LI とまったく同じ。4 声は録音から切り出したピアノの実音 (LI と同じ)。
  消したもの: 始めのシンセ (Klang I の下から上へ分散する和音、Fuga I の主題の重ね)、ジャングルのビートと重低音、心臓の鼓動。
  残したもの: 曲の中ほど (Kyrie) から弾くピアノのようなシンセ (synth_piano) — Kyrie の 8 分の分散和音、Klang II の下から上へ分散する和音、
    Fuga II 後半の分散和音、Amen の分散する和音。
  使い方: python compose_tablet52.py <bank37.json> [score_tablet52.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet51 as M                       # LI: シンセの弾き方 (post) と、XLVIII の弦を鳴らさない設定を使う

K = M.K

def build():
    P = K.build()                                  # L の build (ビート・鼓動) は使わない
    # 区間の小節 (XLVIII): Introitus 0-4 · Klang I 4-6 · Fuga I 6-22 · Kyrie 22-30 · Klang II 30-32 · Fuga II 32-48 · Amen 48-51
    for bar in (30, 31, 48, 49): M.ROLLED.append((bar, 0.11))                  # Klang II と Amen の分散する和音 (Klang I は弾かない)
    M.ARP.append((22, 30, 0.07)); M.ARP.append((40, 48, 0.06))                 # Kyrie と Fuga II 後半の分散和音 (Fuga I の主題の重ねはしない)
    return P

META = {k: v for k, v in M.META.items() if k != 'heart_gain'}
META.update(
    title='Requiem BADA — LII · Klang und Fuge (Klavier)',
    subtitle='実音のピアノと、曲の中ほどから弾くピアノのようなシンセ — ビートと鼓動なし (♩=56)',
    legend=['TB', 'SY'], vname={'SY': 'シンセ (ピアノのように)'},
    footer=['Introitus 08:49 → Klang I → Fuga I (ピアノだけ) → Kyrie (シンセが入る) → Klang II → Fuga II → Amen (ヘ長調)',
            '4 声は録音から切り出したピアノの実音。シンセ (ピアノのように弾く) は曲の中ほどから。始めのシンセ・ビート・鼓動は消した。曲だけの演奏。'])

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet52.json'
    compose.main(out, seed=148, bpm=K.BPM, builder=build, meta=META, extras=CT.extras, post=M.post)
    CT.finish(out)
    K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n in d['notes']: n['dyn'] = round(n.get('dyn', 1.0) * 1.25, 4)   # 4 声のピアノの実音を前に (LI と同じ)
    for s in d['sections']:                        # 区間の説明: オルガン・ビオラ・弦・歌い手の記述を、ピアノとシンセに
        for a, b in (('主題が入るたびに、その声部の歌い手が歌う', '主題が 4 声に次々と入る'), ('5 人が和声で歌う', 'ピアノの 4 声が和声で'),
                     ('全員が 9 度', 'ピアノが 9 度'), ('5 人が「Amen」を長く歌い、', ''), ('最後はストレッタで歌い手が重なる', '最後はストレッタで主題が重なる'),
                     (' (ビオラはアルトの声部)', ''), (' (ビオラは内声)', ''), ('オルガン・ビオラ・弦が長調の和音で包む', 'ピアノとシンセが長調の和音で包む'),
                     ('大聖堂に響く 08:49 の録音 — 弦がそっと寄り添う', '08:49 のピアノの実音 (録音)')):
            s['sub'] = s['sub'].replace(a, b)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']))
