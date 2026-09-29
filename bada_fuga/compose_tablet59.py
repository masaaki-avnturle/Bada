#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LIX · Klavier & Herzschlag-Rock (LVIII のドラムの音を、心臓の「ドクン」に置き換える)
  楽譜・実音のピアノの 4 声・ロックの 8 ビートのリズム (♩=112 で数えて、1・3 拍と 2・4 拍、フィル) は LVIII (compose_tablet58.py) とまったく同じ。
  音だけを心音 (synth.py の heart_tone、extras の HB) に置き換える:
    大太鼓 (1・3 拍) → 「ドッ」(I 音、lub)、スネア (2・4 拍) → 「クン」(II 音、dub) — 交互に鳴って「ドクン、ドクン」
    フィルのタム → 高い「クン」、フロアタム → 「ドッ」、Klang・Amen の一打 → 強い「ドクン」(ドッのあと 0.28 拍でクン)。
    ハイハットは心音にないので外す。心音の音高は和音の根音 (ドッ) と 5 度 (クン)。シンセなし、ピアノ主体。
  使い方: python compose_tablet59.py <bank37.json> [score_tablet59.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet58 as LVIII

K = LVIII.K

def post(P, events, extras):
    n0 = len(CT.extras)
    LVIII.post(P, events, extras)                  # LVIII のドラムのリズムを作ってから、音を心音に置き換える
    drums = CT.extras[n0:]; del CT.extras[n0:]
    for e in drums:
        kd, t, g = e.get('kind'), e['beat'], e['gain']
        root = chord(P.harm[min(P.N - 1, int(t))])['root']
        lub_m, dub_m = 33 + (root - 33) % 12, 33 + (root - 33) % 12 + 7
        if kd == 'hat': continue
        if kd == 'odaiko' and not e.get('damp'):   # Klang・Amen の一打: 強い「ドクン」
            CT.add('HB', t, 0.3, lub_m, g * 1.3, None, kind='lub'); CT.add('HB', t + 0.28, 0.2, dub_m, g * 1.0, None, kind='dub')
        elif kd == 'odaiko' or kd == 'floor':      # 大太鼓・フロアタム → ドッ
            CT.add('HB', t, 0.3, lub_m, g * (1.0 if kd == 'odaiko' else 0.8), None, kind='lub')
        elif kd == 'snare':                        # スネア → クン
            CT.add('HB', t, 0.2, dub_m, g * 0.9, None, kind='dub')
        elif kd == 'tom':                          # タム → 高いクン
            CT.add('HB', t, 0.2, dub_m + 5, g * 0.8, None, kind='dub')

META = dict(LVIII.META, heart_gain=2.2,
    title='Requiem BADA — LIX · Klavier & Herzschlag-Rock',
    subtitle='実音のピアノ主体に、ロックの 8 ビートのリズムを心臓の「ドクン」で (♩=56 / 112)',
    legend=['TB', 'HB'], vname={'HB': '心臓 (ドクン)'},
    footer=['Introitus 08:49 (終わりにフィル) → Klang I → Fuga I (8 ビート) → Kyrie (ハーフタイム) → Klang II → Fuga II (8 ビート) → Amen (ヘ長調)',
            '4 声は録音から切り出したピアノの実音。リズムはロックの 8 ビートのまま、音を心音 (ドッ = I 音、クン = II 音) に置き換えた。シンセなし。曲だけの演奏。'])

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet59.json'
    compose.main(out, seed=148, bpm=K.BPM, builder=LVIII.build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n in d['notes']: n['dyn'] = round(n.get('dyn', 1.0) * 1.25, 4)   # 4 声のピアノの実音を前に (LI〜LVIII と同じ)
    for s in d['sections']:
        for a, b in (('主題が入るたびに、その声部の歌い手が歌う', '主題が 4 声に次々と入る'), ('5 人が和声で歌う', 'ピアノの 4 声が和声で'),
                     ('全員が 9 度', 'ピアノが 9 度'), ('5 人が「Amen」を長く歌い、', ''), ('最後はストレッタで歌い手が重なる', '最後はストレッタで主題が重なる'),
                     (' (ビオラはアルトの声部)', ''), (' (ビオラは内声)', ''), ('オルガン・ビオラ・弦が長調の和音で包む', 'ピアノが長調の和音で包み、心臓が強くドクン'),
                     ('大聖堂に響く 08:49 の録音 — 弦がそっと寄り添う', '08:49 のピアノの実音 (録音)')):
            s['sub'] = s['sub'].replace(a, b)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), Counter(e.get('kind') for e in d['extras'] if e['v'] == 'HB'))
