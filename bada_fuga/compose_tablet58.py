#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions LVIII · Klavier & Rock-Drums (実音のピアノ主体に、ドラマーが叩くふつうのロックの 8 ビート — 重低音は大太鼓)
  楽譜と実音のピアノの 4 声は LV〜LVII とまったく同じ。シンセ (ピアノに似たシンセも) なし。旋律に合わせて打っていた太鼓 (っど) はやめた。
  ドラム (synth.py の acoustic_drum: 膜の固有振動の和): ジャングルのような軽いビートではなく、ドラマーがふつうに叩くロックの 8 ビート —
    ♩=56 の倍 (♩=112) で数えて、バスドラムの役は大太鼓 (46 Hz、深い「ドン」、ロックらしく 0.45 秒で響きを止める) が 1・3 拍 (と 3 拍目の裏の押し)、
    スネアが 2・4 拍、ハイハットは 8 分で小さく暗く。4 小節ごとにタム → フロアタムと下りるフィル。金属的なクラッシュは使わない。
  ドラムが入る所: Introitus の終わりにフィルで入り → Klang I は大太鼓とフロアタムの一打 → Fuga I は 3 小節目から 8 ビート → Kyrie はハーフタイム (スネアは 3 拍目だけ)
    → Klang II は一打 → Fuga II は 2 小節目から 8 ビート → Amen は大太鼓の一打で終わる
  使い方: python compose_tablet58.py <bank37.json> [score_tablet58.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet53 as T                       # LIII: XLVIII の楽譜と、弦・シンセを鳴らさない設定 (実音のピアノの 4 声)
import compose_tablet55 as LV

K = T.K
add = CT.add
ROCK, HITS, FILL = [], [], []                      # ROCK: (b0, b1, 大きさ, 'full' / 'half')

def bass(t, g): add('AD', t, 0.5, 36, g, None, kind='odaiko', damp=0.45)
def post(P, events, extras):
    for b0, b1, lvl, mode in ROCK:
        for bar in range(b0, b1):
            if (bar, 'fill') in FILL: continue
            B = bar * BPB
            for h in range(2):                     # ♩=112 の 1 小節 = ♩=56 の 2 拍
                o = B + 2 * h
                if mode == 'full':
                    bass(o, lvl); bass(o + 1.0, lvl * 0.9)
                    if h == 1: bass(o + 1.25, lvl * 0.7)                                 # 3 拍目の裏の押し (2 小節に 1 回)
                    for t in (0.5, 1.5): add('AD', o + t, 0.3, 38, lvl * 0.8, None, kind='snare')
                else:                              # ハーフタイム: 大太鼓は 1 拍目、スネアは 3 拍目だけ
                    bass(o, lvl)
                    add('AD', o + 1.0, 0.3, 38, lvl * 0.75, None, kind='snare')
                for k in range(4): add('AD', o + 0.5 * k, 0.05, 42, lvl * (0.16 if k % 2 == 0 else 0.1), None, kind='hat')
            if (bar - b0) % 4 == 3 and bar + 1 < b1:                                    # 4 小節ごとのフィル (最後の 2 拍を 16 分でタム → フロアタム)
                for k, kd in enumerate(('tom', 'tom', 'tom', 'tom', 'floor', 'floor', 'floor', 'floor')):
                    add('AD', B + 2 + 0.25 * k, 0.3, 36, lvl * (0.55 + 0.05 * k), None, kind=kd)
    for bar, kd in FILL:                           # 区間の終わりの長いフィル (1 小節まるごと、8 分 → 16 分でだんだん細かく)
        B = bar * BPB; lvl = next(l for b0, b1, l, m in ROCK if b0 <= bar < b1)
        seq = [(0, 'snare'), (0.5, 'snare'), (1, 'tom'), (1.5, 'tom')] + [(2 + 0.25 * k, ('tom', 'tom', 'floor', 'floor', 'floor', 'floor', 'floor', 'floor')[k]) for k in range(8)]
        for t, kd2 in seq: add('AD', B + t, 0.3, 36, lvl * (0.6 + 0.3 * t / 4), None, kind=kd2)
        bass(B, lvl)
    for bar, lvl in HITS:                          # 大太鼓とフロアタムの一打 (Klang・Amen)
        add('AD', bar * BPB, 1.5, 36, lvl, None, kind='odaiko'); add('AD', bar * BPB, 1.0, 36, lvl * 0.6, None, kind='floor')

def build():
    P = K.build()
    # 区間の小節 (XLVIII): Introitus 0-4 · Klang I 4-6 · Fuga I 6-22 · Kyrie 22-30 · Klang II 30-32 · Fuga II 32-48 · Amen 48-51
    ROCK.extend([(3, 4, 0.11, 'full'), (8, 22, 0.11, 'full'), (22, 30, 0.085, 'half'), (33, 48, 0.11, 'full')])
    FILL.extend([(3, 'fill'), (21, 'fill'), (29, 'fill'), (47, 'fill')])
    HITS.extend([(4, 0.16), (30, 0.16), (49, 0.15)])
    return P

META = dict(LV.META,
    title='Requiem BADA — LVIII · Klavier & Rock-Drums',
    subtitle='実音のピアノ主体に、ドラマーが叩くロックの 8 ビート — 重低音は大太鼓 (♩=56 / 112)',
    legend=['TB', 'AD'], vname={'AD': 'ドラム'},
    footer=['Introitus 08:49 (終わりにフィル) → Klang I → Fuga I (8 ビート) → Kyrie (ハーフタイム) → Klang II → Fuga II (8 ビート) → Amen (大太鼓、ヘ長調)',
            '4 声は録音から切り出したピアノの実音。ドラムは大太鼓・スネア・ハイハット・タムの鳴り方をまねたもの (シンセなし)。曲だけの演奏。'])

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet58.json'
    compose.main(out, seed=148, bpm=K.BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    K.fix_voices(out)
    d = json.load(open(out)); from collections import Counter
    for n in d['notes']: n['dyn'] = round(n.get('dyn', 1.0) * 1.25, 4)   # 4 声のピアノの実音を前に (LI〜LVII と同じ)
    for s in d['sections']:
        for a, b in (('主題が入るたびに、その声部の歌い手が歌う', '主題が 4 声に次々と入る'), ('5 人が和声で歌う', 'ピアノの 4 声が和声で'),
                     ('全員が 9 度', 'ピアノが 9 度'), ('5 人が「Amen」を長く歌い、', ''), ('最後はストレッタで歌い手が重なる', '最後はストレッタで主題が重なる'),
                     (' (ビオラはアルトの声部)', ''), (' (ビオラは内声)', ''), ('オルガン・ビオラ・弦が長調の和音で包む', 'ピアノが長調の和音で包み、大太鼓が一打'),
                     ('大聖堂に響く 08:49 の録音 — 弦がそっと寄り添う', '08:49 のピアノの実音 (録音)')):
            s['sub'] = s['sub'].replace(a, b)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('extras:', Counter(e['v'] for e in d['extras']), Counter(e.get('kind') for e in d['extras'] if e['v'] == 'AD'))
