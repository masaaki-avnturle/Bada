#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions VI · Lento ipnotico (実録音の、ゆったりとした洗脳のレクイエムとフーガ)
  録音 5 本 (2026-09-24 08:49 / 08:53 / 11:18 / 11:21 / 11:23) を、♩=50 のゆったりとした洗脳的なレクイエムとフーガにする。
  録音はループせず実音のまま流し (速さも音高も元のまま)、その下で録音の低い打鍵から作った鼓動が最後まで止まらない。
    各録音: 実音 8 小節 (後半は 4 声が録音の和音を全音符で支える) → その主題の 4 声フーガの提示 8 小節
      (下で実録音のオスティナートと持続音が回り続ける) → 次の録音の調の属和音 1 小節
    調の並び: 11:18 (変ロ短調) → 08:49 / 11:21 (ヘ短調) → 08:53 / 11:23 (ホ短調)
    Finale: 5 つの主題が 1 小節おきに入るフーガ (ホ短調) → 11:23 の実音 → ピカルディ終止
  4 声・オスティナート・持続音は録音の 1 音のサンプラー (build_sampler.py)。
  使い方: python compose_tablet6.py <bank.json> [score_tablet6.json]
"""
import sys
from compose import *
import compose
import compose_tablet as CT          # 主題・和声づけ・区間ごとの移調 (同じ bank.json を読む)
import compose_tablet2 as T2         # 実録音のオスティナート・持続音・鼓動 (post)
import compose_tablet3 as T3         # 録音の日時表記
import compose_tablet5 as T5         # 実音の区間 (passage)、フーガの提示、主題からの和声

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 50; BAR_S = 240.0 / BPM
KEYS = {'20260924_111846': (-4, '変ロ短調'), '20260924_084937': (3, 'ヘ短調'), '20260924_112131': (3, 'ヘ短調'),
        '20260924_085314': (2, 'ホ短調'), '20260924_112313': (2, 'ホ短調')}
ORDER = ['20260924_111846', '20260924_084937', '20260924_112131', '20260924_085314', '20260924_112313']
MARK = '①②③④⑤'
VOICE_SRC = {'S': '20260924_112313', 'A': '20260924_085314', 'T': '20260924_084937', 'B': '20260924_111846'}

def build():
    for rid in ORDER:                                     # 主題: 主和音で始まる最初の 13 秒の最上声から
        semis = KEYS[rid][0]; t0, inside = CT.excerpt(rid, semis, 13.0)
        subj = CT.make_subject(inside, semis, 56); T5.SUBJ[rid] = (subj, CT.harmonize(subj))
    total = 2 + 17 * len(ORDER) + 12 + 5 + 3
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 0.75
    first = ORDER[0]
    P.section(0, 'Introitus', '♩=50 の鼓動 (録音の低い打鍵) と持続音 — 鼓動は最後まで一度も止まらない')
    for v in VOICES: P.rest_bars(v, 0, 2)
    P.set_harms(0, [['Dm']] * 2)
    T2.MANTRA.append((0, 2, first, ('DN', 'PK')))
    CT.LAYOUT.append((0, 2, KEYS[first][0], {v: first for v in VOICES}, {}))
    b = 2
    for i, rid in enumerate(ORDER):
        semis, kname = KEYS[rid]
        # 実音 8 小節 (ループしない)
        P.section(b, '%s 録音 %s — 実音' % (MARK[i], hm(rid)), '%s ／ 録音 %s をループせずそのまま 38 秒 — 鼓動は止まらず、後半は 4 声が録音の和音を支える' % (kname, rid))
        T5.passage(P, rid, b, 8, semis, 4, fin=1.5, fout=3.0, bpm=BPM)
        T2.MANTRA.append((b, b + 8, rid, ('PK',)))
        CT.LAYOUT.append((b, b + 8, semis, {v: rid for v in VOICES}, {}))
        b += 8
        # 主題の 4 声フーガ (提示)
        P.section(b, '%s Fuga — 主題 %s 〈録音 %s〉' % (MARK[i], MARK[i], hm(rid)), '実音の最上声から作った主題の 4 声フーガ — 下で実録音のオスティナートと持続音が同じ形を回し続ける')
        for k in range(8): P.dyn[b + k] = 0.8
        T5.expo(P, b, rid, MARK[i])
        T2.MANTRA.append((b, b + 8, rid, ('DN', 'PK', 'OS')))
        CT.LAYOUT.append((b, b + 8, semis, {v: rid for v in VOICES}, {}))
        b += 8
        # 次の調の属和音
        nxt = ORDER[i + 1] if i + 1 < len(ORDER) else None
        P.set_harms(b, [['A7']]); P.hold.add(b)
        T2.MANTRA.append((b, b + 1, rid, ('PK',)))
        CT.LAYOUT.append((b, b + 1, KEYS[nxt][0] if nxt else 2, VOICE_SRC, {}))
        b += 1
    # ---------------- Finale: 5 つの主題が 1 小節おきに (ホ短調)
    f0 = b
    P.section(f0, 'Finale — Fuga a cinque soggetti', '5 本の録音の主題が 1 小節おきに入る — 各主題は自分の録音の音で。下でオスティナートと持続音 (ホ短調)')
    octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}; vs = ['A', 'S', 'T', 'B', 'A', 'S', 'T', 'B', 'A', 'S']
    entries, labmap = [], {}
    for k in range(10):
        rid = ORDER[k % 5]; v = vs[k]; w = k // 5; subj = T5.SUBJ[rid][0]; tr = octs[v] + (7 if w else 0)
        if v == 'B' and min(m for _, m in subj) + tr < 36: tr += 12
        if max(m for _, m in subj) + tr > {'S': 81, 'A': 74, 'T': 69, 'B': 62}[v]: tr -= 12
        lab = '主題 %s%s' % (MARK[k % 5], ' 答唱' if w else ''); labmap[lab] = rid
        P.place(v, f0 + k, subj, tr, lab); entries.append(((f0 + k) * BPB, [(d, m + tr) for d, m in subj]))
    for v, z in {'S': 1, 'T': 2, 'B': 3}.items(): P.rest_bars(v, f0, f0 + z)
    T5.harm_from_entries(P, f0, f0 + 11, entries)
    P.set_harms(f0 + 11, [['Gm', 'Gm', 'A7', 'A7']])
    for k in range(12): P.dyn[f0 + k] = 0.85
    T2.MANTRA.append((f0, f0 + 12, ORDER[-1], ('DN', 'PK', 'OS')))
    CT.LAYOUT.append((f0, f0 + 12, 2, VOICE_SRC, labmap))
    b = f0 + 12
    # ---------------- In paradisum: 11:23 の実音 → ピカルディ終止
    last = ORDER[-1]
    P.section(b, 'In paradisum — 録音 %s の実音' % hm(last), '録音 %s のホ短調の 24 秒を実音のまま → ピカルディ終止 (ホ長調) で、鼓動とともに消えていく' % last)
    T5.passage(P, last, b, 5, 2, 2, fin=1.5, fout=3.0, bpm=BPM)
    T2.MANTRA.append((b, b + 8, last, ('PK',)))
    CT.LAYOUT.append((b, b + 5, 2, {v: last for v in VOICES}, {}))
    b += 5
    P.set_harms(b, [['D']] * 3); P.hold.update(range(b, b + 3))
    P.place('S', b, mat(('F#5', 8)), 0, None); P.place('A', b, mat(('A4', 8)), 0, None); P.place('T', b, mat(('D4', 8)), 0, None); P.place('B', b, mat(('D3', 8)), 0, None)
    for v in VOICES: P.rest_bars(v, b + 2, b + 3)
    for k in range(3): P.dyn[b + k] = 0.6 - 0.1 * k
    CT.LAYOUT.append((b, b + 3, 2, VOICE_SRC, {}))
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER,
    'title': 'Requiem BADA — Tablet Sessions VI · Lento ipnotico',
    'subtitle': '録音 5 本 (09-24) の、ゆったりとした洗脳のレクイエムとフーガ — 実音はループせず、鼓動は止まらない',
    'footer': ['① 11:18 (変ロ短調) → ② 08:49 · ③ 11:21 (ヘ短調) → ④ 08:53 · ⑤ 11:23 (ホ短調) → Finale: 5 つの主題のフーガ → In paradisum (♩=50)',
               '各録音: 実音 8 小節 → その主題の 4 声フーガ。4 声・オスティナート・持続音は録音の 1 音のサンプラー、鼓動は録音の低い打鍵。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet6.json'
    compose.main(out, seed=53, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=T2.post)
    CT.finish(out)
    for rid in ORDER: print(rid, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in T5.SUBJ[rid][0]))
