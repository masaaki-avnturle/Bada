#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XLIX · Klang und Fuge .exe (XLVIII に、FrostBorne「stargod.exe」を参考にしたビートを取り入れる)
  楽譜 (5 人の歌い手・ビオラ・パイプオルガン・Klang・ドイツ語のフーガ) は XLVIII (compose_tablet48.py) とまったく同じで、その上にビートを重ねる。
  参考にした曲の音やリズムは写さず、「.exe」系の暗いトラップ (フォンク寄り) の特徴だけを取り入れる:
    808 のベース (長く伸びる重低音、和音の根音をなぞり、次の根音へすべる)、重いキック、2・4 拍目の手拍子 (クラップ)、
    細かく刻む暗いハイハット (小節の終わりで 3 連符に転がる)。明るいカウベルや金属的な高音は使わない (ハイハットも丸める)。
  ♩=56 の 1 拍を倍の速さで数えるハーフタイムのトラップ (手拍子は ♩=56 の 2・4 拍目)。
  ビートの入り方: Introitus なし → Klang I は 808 の一撃 → Fuga I は 3 小節目から (前半は疎ら、後半は細かく転がる) → Kyrie は疎ら
    → Klang II でいったん引く (808 の一撃) → Fuga II は細かく転がり、最後の 2 小節はキックが倍に → Amen で止まり、最後に 808 の長い一撃
  使い方: python compose_tablet49.py <bank37.json> [score_tablet49.json]  (歌は add_vocals.py tablet48 score_tablet49.json ... voice.npz)
"""
import sys, json
from compose import *
import compose
import compose_tablet as CT
import compose_tablet48 as K

add = CT.add
BEAT, E808, BOOM, ROLL = [], [], [], []

def post(P, events, extras):
    K.post(P, events, extras)
    for b0, b1, lvl in E808:                       # 808: 半小節ごとに和音の根音 (E1〜D#2)、次の根音が違えば終わりですべる
        for bar in range(b0, b1):
            for half in (0, 2):
                t = bar * BPB + half
                r = K.low_root(chord(P.harm[t]), 28)
                nt = min(P.N - 1, t + 2); rn = K.low_root(chord(P.harm[nt]), 28)
                add('E8', t, 1.9, r, lvl, None, slide=rn if rn != r and nt < b1 * BPB else None)
    for bar, lvl, m in BOOM:                       # 808 の一撃 (長く)
        add('E8', bar * BPB, 7.5, m, lvl, None)
        add('DR', bar * BPB, 0.4, 36, lvl * 0.9, None, kind='kick')
    for b0, b1, lvl, mode in BEAT:
        for bar in range(b0, b1):
            kicks = (0, 1.75, 2.5) if mode == 'half' else ((0, 0.75, 1.75, 2.5, 3.25) if mode == 'full' else (0, 0.5, 1.5, 1.75, 2.5, 3, 3.25, 3.75))
            for t in kicks: add('DR', bar * BPB + t, 0.3, 36, lvl * (1.0 if t in (0, 2.5) else 0.8), None, kind='kick')
            for t in (1, 3): add('DR', bar * BPB + t, 0.3, 38, lvl * 0.75, None, kind='clap', pan=0.05)
            step = 0.5 if mode == 'half' else 0.25
            for k in range(int(4 / step)):
                t = k * step
                if mode != 'half' and bar % 2 == 1 and t >= 3: continue            # 2 小節ごとの最後の拍は 3 連符の転がり (下で)
                add('DR', bar * BPB + t, 0.06, 42, lvl * (0.22 if k % 2 == 0 else 0.15), None, kind='hatd', pan=0.3)
            if mode != 'half' and bar % 2 == 1:
                for k in range(6): add('DR', bar * BPB + 3 + k / 6, 0.05, 42, lvl * (0.1 + 0.03 * k), None, kind='hatd', pan=0.3)
    for bar, lvl in ROLL:                          # フィル: 最後の拍を 32 分で転がるハイハットと手拍子
        for k in range(8): add('DR', bar * BPB + 3 + k / 8, 0.04, 42, lvl * (0.1 + 0.04 * k), None, kind='hatd', pan=0.3)
        for t in (3.5, 3.75): add('DR', bar * BPB + t, 0.2, 38, lvl * 0.6, None, kind='clap')

def build():
    P = K.build()
    # 区間の小節 (XLVIII): Introitus 0-4 · Klang I 4-6 · Fuga I 6-22 · Kyrie 22-30 · Klang II 30-32 · Fuga II 32-48 · Amen 48-51
    BOOM.append((4, 0.1, 28 + (2 - 28) % 12))                                    # Klang I: 808 の一撃 (根音 D = 枠の主音、ホ短調へ移調される)
    BEAT.append((8, 14, 0.096, 'half')); E808.append((8, 14, 0.08))
    BEAT.append((14, 22, 0.104, 'full')); E808.append((14, 22, 0.088)); ROLL.append((21, 0.104))
    BEAT.append((22, 30, 0.08, 'half')); E808.append((22, 30, 0.072)); ROLL.append((29, 0.08))
    BOOM.append((30, 0.1, 28 + (2 - 28) % 12))                                   # Klang II: いったん引いて 808 の一撃
    BEAT.append((33, 46, 0.104, 'full')); E808.append((33, 48, 0.088)); ROLL.append((45, 0.104))
    BEAT.append((46, 48, 0.112, 'double')); ROLL.append((47, 0.112))
    BOOM.append((49, 0.1, 28 + (2 - 28) % 12))                                   # Amen の長調の和音で 808 の長い一撃
    return P

META = dict(K.META,
    title='Requiem BADA — XLIX · Klang und Fuge .exe',
    subtitle='XLVIII に「.exe」系の暗いトラップのビート (808・キック・手拍子・暗いハイハット) を — FrostBorne「stargod.exe」を参考に (♩=56)',
    legend=['TB', 'VA', 'E8', 'DR', 'V1'], vname=dict(K.META['vname'], DR='ビート', E8='808'),
    footer=['Introitus → Klang I (808) → Fuga I (ビートが入る) → Kyrie → Klang II (808) → Fuga II (細かく転がる) → Amen (808 の長い一撃)',
            'ビートは FrostBorne「stargod.exe」を参考にした「.exe」系の暗いトラップの特徴だけで、音やリズムは写していない。歌い手・歌詞は XLVIII と同じ。'])

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet49.json'
    compose.main(out, seed=148, bpm=K.BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    K.fix_voices(out)                              # XLVIII と同じ声部の修正 (楽譜を同じにする)
    print('beat extras:', sum(1 for e in json.load(open(out))['extras'] if e['v'] in ('DR', 'E8')))
