#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions VII · Piano & Synth (自分流のレクイエムとフーガのミックス)
  2026-09-24 の録音 5 本 (08:49 / 08:53 / 11:18 / 11:21 / 11:23) を実音のまま (ループせず、速さも音高も元のまま) つなぎ、
  その旋律で作ったレクイエムとフーガを混ぜる。11:21 はピアノとシンセサイザーを 1 曲にした録音 (音が減衰せず明るい) なので、
  フーガの旋律もピアノの音 (録音の 1 音のサンプラー) にシンセサイザーのリードを重ね、下でシンセのパッドが和音を支える。
    Introitus — Mix: 11:23 → 08:53 (ホ短調) の実音をクロスフェードで
    Fuga I — 11:23 と 08:53 の主題の二重フーガ (ピアノ + シンセのリード) → B7 → (F7) で変ロ短調へ
    Lacrimosa — 11:18 (変ロ短調) の実音
    Sanctus — Mix: 08:49 → 11:21 (ヘ短調、ピアノとシンセの曲) の実音をクロスフェードで
    Finale — 5 つの主題のフーガ (ヘ短調、ピアノ + シンセ)
    In paradisum — 11:21 の本当の終わりの実音
  使い方: python compose_tablet7.py <bank.json> [score_tablet7.json]
"""
import sys
from compose import *
import compose
import compose_tablet as CT
import compose_tablet3 as T3
import compose_tablet5 as T5

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 60; BAR_S = 240.0 / BPM; XF = 2
KEYS = {'20260924_084937': 3, '20260924_085314': 2, '20260924_111846': -4, '20260924_112131': 3, '20260924_112313': 2}
R_A, R_B, R_L, R_C, R_SY = '20260924_112313', '20260924_085314', '20260924_111846', '20260924_084937', '20260924_112131'
ORDER = [R_A, R_B, R_L, R_C, R_SY]
MARK = dict(zip(ORDER, '①②③④⑤'))
VOICE_SRC = {'S': R_A, 'A': R_B, 'T': R_C, 'B': R_L}
PADS = []                            # (開始小節, 終了小節, 大きさ) — シンセのパッド
octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}; TOP = {'S': 81, 'A': 74, 'T': 69, 'B': 62}

def post(P, events, extras):
    for b0, b1, g in PADS:
        for bar in range(b0, b1):
            for half in (0, 2):
                c = chord(P.harm[bar * BPB + half] or 'Dm')
                for pc, tg in ((c['root'], 50), (c['third'], 57), (c['fifth'], 60)):
                    add('PD', bar * BPB + half, 2.1, min((x for x in range(36, 84) if x % 12 == pc), key=lambda x: abs(x - tg)), g, None)

def entry(P, bar, v, rid, tr0, entries, labmap, synth=True):
    """主題の入り: 4 声の 1 声 (ピアノの音) + 上の声ならシンセのリードが 1 オクターヴ上で重なる"""
    subj = T5.SUBJ[rid][0]; tr = octs[v] + tr0
    if v == 'B' and min(m for _, m in subj) + tr < 36: tr += 12
    if max(m for _, m in subj) + tr > TOP[v]: tr -= 12
    lab = '主題 %s%s' % (MARK[rid], ' 答唱' if tr0 else ''); labmap[lab] = rid
    P.place(v, bar, subj, tr, lab); entries.append((bar * BPB, [(d, m + tr) for d, m in subj]))
    if synth and v in 'SA':
        t = bar * BPB
        for d, m in subj: add('LD', t, d * 0.95, m + tr + 12, 0.13, None); t += d

def mix(P, b, r1, r2, bars=10):
    """2 本の実音をクロスフェードでつなぐ (4 声は後半だけ全音符で静かに)。占める小節数を返す"""
    T5.passage(P, r1, b, bars, KEYS[r1], 5, fin=1.5, fout=XF * BAR_S, bpm=BPM)
    CT.LAYOUT.append((b, b + bars, KEYS[r1], {v: r1 for v in VOICES}, {}))
    st = b + bars - XF
    T5.passage(P, r2, st, bars, KEYS[r2], XF + 4, fin=XF * BAR_S, fout=3.0, bpm=BPM)
    for v in VOICES: P.rest_bars(v, st, st + XF)
    CT.LAYOUT.append((st + XF, st + bars, KEYS[r2], {v: r2 for v in VOICES}, {}))
    return 2 * bars - XF

def build():
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0)
        subj = CT.make_subject(inside, KEYS[r], 56); T5.SUBJ[r] = (subj, CT.harmonize(subj))
    total = 18 + 10 + 1 + 10 + 1 + 18 + 11 + 1 + 5 + 1
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 0.75
    b = 0
    # ---------------- Introitus — Mix (ホ短調)
    P.section(b, 'Introitus — Mix 〈%s → %s〉' % (hm(R_A), hm(R_B)), 'ホ短調 ／ 2 本の録音をループせず実音のまま、8 秒のクロスフェードでつなぐ — 後半は 4 声が録音の和音を静かに支える')
    b += mix(P, b, R_A, R_B)
    # ---------------- Fuga I (ホ短調): 二重フーガ + シンセ
    f0 = b; entries, labmap = [], {}
    P.section(b, 'Fuga I — 主題 ①② 〈%s · %s〉' % (hm(R_A), hm(R_B)), '2 本の録音の主題の二重フーガ — ピアノの音にシンセサイザーのリードが重なり、シンセのパッドが和音を支える')
    for bar, v, r, tr0 in ((0, 'A', R_A, 0), (2, 'S', R_B, 0), (4, 'T', R_A, 7), (6, 'B', R_B, 0), (8, 'S', R_A, 0), (8, 'T', R_B, 0)):
        entry(P, f0 + bar, v, r, tr0, entries, labmap)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f0, f0 + z)
    T5.harm_from_entries(P, f0, f0 + 10, entries)
    for k in range(10): P.dyn[f0 + k] = 0.8
    PADS.append((f0, f0 + 10, 0.07)); CT.LAYOUT.append((f0, f0 + 10, 2, VOICE_SRC, labmap))
    b = f0 + 10
    P.set_harms(b, [['A7']]); P.hold.add(b)                               # 変ロ短調の F7 (ホ短調の B7 からの裏)
    CT.LAYOUT.append((b, b + 1, KEYS[R_L], VOICE_SRC, {})); b += 1
    # ---------------- Lacrimosa (変ロ短調)
    P.section(b, 'Lacrimosa — 録音 %s の実音' % hm(R_L), '変ロ短調 ／ ループせずそのまま 40 秒 — 後半は 4 声が録音の和音を支える')
    T5.passage(P, R_L, b, 10, KEYS[R_L], 5, fin=1.5, fout=3.0, bpm=BPM)
    CT.LAYOUT.append((b, b + 10, KEYS[R_L], {v: R_L for v in VOICES}, {})); b += 10
    P.set_harms(b, [['A7']]); P.hold.add(b)                               # ヘ短調の C7
    CT.LAYOUT.append((b, b + 1, KEYS[R_C], VOICE_SRC, {})); b += 1
    # ---------------- Sanctus — Mix (ヘ短調、ピアノとシンセの曲)
    s0 = b
    P.section(b, 'Sanctus — Mix 〈%s → %s (ピアノとシンセ)〉' % (hm(R_C), hm(R_SY)), 'ヘ短調 ／ 08:49 から、ピアノとシンセサイザーを 1 曲にした 11:21 へ実音のままつなぐ — シンセのパッドがそっと寄り添う')
    b += mix(P, b, R_C, R_SY)
    PADS.append((s0 + 12, b, 0.05))
    # ---------------- Finale (ヘ短調): 5 つの主題 + シンセ
    f1 = b; entries, labmap = [], {}; vs = ['A', 'S', 'T', 'B', 'A', 'S', 'T', 'B', 'A', 'S']
    P.section(b, 'Finale — Fuga a cinque soggetti', '5 本の録音の主題が 2 小節ごとに次々と — 上の声にはシンセのリードが重なる (ヘ短調)')
    for k in range(5): entry(P, f1 + 2 * k, ['A', 'S', 'T', 'B', 'S'][k], ORDER[k], 0, entries, labmap)   # 2 小節ごとに 1 つずつ
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f1, f1 + z)
    T5.harm_from_entries(P, f1, f1 + 10, entries); P.set_harms(f1 + 10, [['Gm', 'Gm', 'A7', 'A7']])
    for k in range(11): P.dyn[f1 + k] = 0.85
    PADS.append((f1, f1 + 11, 0.07)); CT.LAYOUT.append((f1, f1 + 11, 3, VOICE_SRC, labmap))
    b = f1 + 11
    P.set_harms(b, [['Dm']]); P.hold.add(b); CT.LAYOUT.append((b, b + 1, 3, VOICE_SRC, {})); b += 1
    # ---------------- In paradisum: 11:21 の本当の終わり
    P.section(b, 'In paradisum — %s の本当の終わり' % hm(R_SY), 'ピアノとシンセサイザーの録音 11:21 の最後の 20 秒を実音のまま — 録音自身の終わりで閉じる')
    T5.passage(P, R_SY, b, 5, KEYS[R_SY], 2, fin=1.0, fout=2.5, t0=REC[R_SY]['dur'] - 5 * BAR_S - 0.5, bpm=BPM)
    CT.LAYOUT.append((b, b + 6, KEYS[R_SY], {v: R_SY for v in VOICES}, {}))
    for v in VOICES: P.rest_bars(v, b + 5, b + 6)
    P.set_harms(b + 5, [['Dm']]); b += 6
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER,
    'title': 'Requiem BADA — Tablet Sessions VII · Piano & Synth',
    'subtitle': '自分流のレクイエムとフーガのミックス — 録音 5 本 (09-24) を実音のまま、ピアノの旋律にシンセサイザーを重ねて',
    'legend': ['TB', 'LD', 'PD'],
    'footer': ['Introitus: 11:23 → 08:53 (ホ短調) → Fuga I (二重) → Lacrimosa 11:18 (変ロ短調) → Sanctus: 08:49 → 11:21 (ピアノとシンセ) → Finale (5 つの主題) → In paradisum (11:21 の終わり)',
               '録音は速さも音高も元のまま。4 声は録音の 1 音 (ピアノ)、その旋律にシンセのリード、下にシンセのパッド。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet7.json'
    compose.main(out, seed=71, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    for r in ORDER: print(r, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in T5.SUBJ[r][0]))
