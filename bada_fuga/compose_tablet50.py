#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions L · Klang und Fuge — Herzschlag & Jungle (曲だけの演奏: 鼓動の不整脈と、きれいなジャングルのビート)
  楽譜 (パイプオルガンの 4 声・ビオラ・弦・Klang・フーガ) は XLVIII (compose_tablet48.py) とまったく同じで、歌は入れず (曲だけの演奏)、ビートを重ねる。
  鼓動: 「ドックン、ドックン」— 心音 (heart_tone: lub = 「ドッ」、0.3 秒後に dub = 「クン」) が ♩=56 (安静時の心拍) で打ち、ときどき不整脈:
    早く来る脈 (期外収縮: 拍の途中で小さな「ドックン」→ 次の拍が抜けて、その次が強く打つ) と、抜ける脈。音高は和音の根音 (lub) と 5 度 (dub)。
  ジャングル: ♩=168 (♩=56 のちょうど 3 倍 = オルガンの 1 小節にジャングルの 3 小節) のブレイクビート — キック・スネア・小さなゴースト・スネア・
    暗いハイハットの 16 分、2 種類の型を交互に、区間の終わりはスネアの連打で盛り上げる。重低音 (サブベース) は和音の根音を長く。
    特定の曲のブレイク (録音) は使わず、ジャングルの型を自作のドラムの音で組む。明るい金属的な高音は使わない。
  入り方: Introitus の終わりから鼓動 → Klang I (鼓動が強く) → Fuga I は 5 小節目からジャングル → Kyrie は鼓動だけ (落ち着く)
    → Klang II (不整脈が続く) → Fuga II はジャングルが最後まで、終わりにスネアの連打 → Amen でジャングルが止まり、鼓動がゆっくり消える
  使い方: python compose_tablet50.py <bank37.json> [score_tablet50.json]
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet48 as K

add = CT.add
HEART, JUNGLE, SUB, SROLL = [], [], [], []
J = 1.0 / 12                                       # ジャングルの 16 分音符 = ♩=56 の 1/12 拍 (♩=168)
PAT = [((0, 1.0), (2, 0.55), (10, 0.95)), ((0, 1.0), (8, 0.5), (10, 0.9))]           # キック (16 分の位置, 強さ) — 型 A / 型 B
SNR = [((4, 1.0), (12, 1.0), (7, 0.28), (15, 0.3)), ((4, 1.0), (12, 1.0), (6, 0.25), (13, 0.3), (14, 0.35))]   # スネアとゴースト
# 不整脈 (2 小節 = 8 拍を 1 周期に、周期ごとに変える): 'n' ふつう / 'p' 早く来る脈 (拍の 0.55 で小さく、次の拍は抜ける) / 's' 抜ける / 'x' 強い代償の脈
RHYTHM = ['nnnnnnnn', 'nnnpsxnn', 'nnnnnnsn', 'nnpsxnnn', 'nnnnnnnn', 'npsxnnnn', 'nnnnsnnn', 'nnnnnpsx']

def post(P, events, extras):
    K.post(P, events, extras)
    cyc = 0
    for b0, b1, lvl in HEART:                      # 鼓動: lub (根音) → 0.28 拍 (0.3 秒) 後に dub (5 度)
        for bar in range(b0, b1, 2):
            pat = RHYTHM[cyc % len(RHYTHM)]; cyc += 1
            for k, c in enumerate(pat):
                t = bar * BPB + k
                if t >= b1 * BPB: break
                r = K.low_root(chord(P.harm[int(t)]), 33)
                if c == 's': continue
                if c == 'p':                       # 期外収縮: 拍の 0.55 で小さな脈 (この拍の本来の脈は来ない)
                    t = t + 0.55; g = 0.6
                else:
                    g = 1.25 if c == 'x' else 1.0
                add('HB', t, 0.3, r, lvl * g, None, kind='lub'); add('HB', t + 0.28, 0.2, r + 7, lvl * g * 0.7, None, kind='dub')
    for b0, b1, lvl in JUNGLE:                     # ジャングル: オルガンの 1 小節 = ジャングルの 3 小節 (16 分 × 16 × 3)
        for bar in range(b0, b1):
            for jb in range(3):
                base = bar * BPB + jb * 16 * J; kind = (bar * 3 + jb) % 2
                for st, g in PAT[kind]: add('DR', base + st * J, 0.25, 36, lvl * g, None, kind='kick')
                for st, g in SNR[kind]: add('DR', base + st * J, 0.2, 38, lvl * 0.8 * g, None, kind='snare', pan=0.05)
                for st in range(0, 16, 2): add('DR', base + st * J, 0.05, 42, lvl * (0.2 if st % 4 == 0 else 0.13), None, kind='hatd', pan=0.3)
    for bar, lvl in SROLL:                         # スネアの連打: 最後のジャングル 1 小節分を 16 分で、だんだん強く
        base = bar * BPB + 2 * 16 * J
        for st in range(16): add('DR', base + st * J, 0.12, 38, lvl * (0.3 + 0.045 * st), None, kind='snare', pan=0.05)
    for b0, b1, lvl in SUB:                        # 重低音: 半小節ごとに和音の根音 (E1〜D#2) を長く
        for bar in range(b0, b1):
            for half in (0, 2):
                t = bar * BPB + half
                add('E8', t, 1.95, K.low_root(chord(P.harm[t]), 28), lvl, None)

def build():
    P = K.build()
    # 区間の小節 (XLVIII): Introitus 0-4 · Klang I 4-6 · Fuga I 6-22 · Kyrie 22-30 · Klang II 30-32 · Fuga II 32-48 · Amen 48-51
    HEART.append((2, 4, 0.35)); HEART.append((4, 6, 0.5)); HEART.append((6, 22, 0.4)); HEART.append((22, 30, 0.38))
    HEART.append((30, 32, 0.5)); HEART.append((32, 48, 0.4)); HEART.append((48, 50, 0.3))
    JUNGLE.append((10, 22, 0.16)); SUB.append((10, 22, 0.105)); SROLL.append((21, 0.16))
    JUNGLE.append((33, 48, 0.16)); SUB.append((33, 48, 0.105)); SROLL.append((47, 0.17))
    return P

META = dict(K.META, organ_gain=0.9, heart_gain=0.5,
    title='Requiem BADA — L · Herzschlag & Jungle',
    subtitle='曲だけの演奏 — XLVIII に鼓動の不整脈 (ドックン) ときれいなジャングルのビート (♩=56 / 168)',
    legend=['TB', 'VA', 'HB', 'DR', 'E8', 'V1'], vname=dict(K.META['vname'], HB='鼓動', DR='ジャングル', E8='重低音'),
    footer=['Introitus → Klang I (鼓動) → Fuga I (ジャングルが入る) → Kyrie (鼓動だけ) → Klang II (不整脈) → Fuga II (ジャングル) → Amen (鼓動が消える)',
            '鼓動は ♩=56 の心音 (ドッ・クン) に、早く来る脈と抜ける脈。ジャングルは ♩=168 (3 倍) のブレイクビートを自作のドラムの音で。曲だけの演奏 (歌なし)。'])

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet50.json'
    compose.main(out, seed=148, bpm=K.BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    K.fix_voices(out)                              # XLVIII と同じ声部の修正 (楽譜を同じにする)
    d = json.load(open(out)); from collections import Counter
    for s in d['sections']:                        # 曲だけの演奏: 区間の説明から歌い手を外す
        for a, b in (('主題が入るたびに、その声部の歌い手が歌う', '主題が 4 声に次々と入る'), ('5 人が和声で歌う', 'オルガンの 4 声が和声で'),
                     ('全員が 9 度', 'オルガンが 9 度'), ('5 人が「Amen」を長く歌い、', ''), ('最後はストレッタで歌い手が重なる', '最後はストレッタで主題が重なる')):
            s['sub'] = s['sub'].replace(a, b)
    json.dump(d, open(out, 'w'), ensure_ascii=False)
    print('beat extras:', Counter(e['v'] for e in d['extras'] if e['v'] in ('HB', 'DR', 'E8')))
