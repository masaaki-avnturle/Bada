#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions IV · Mix (録音 11 本をミックスした、実録音の洗脳のレクイエムとフーガ)
  録音 11 本を順に並べるのではなく、同時に重ねてミックスする。全部の録音をテープのように速さごと移調してホ短調にそろえ、
  ♩=60 の止まらない鼓動の上で重ねる。鳴る音はすべて実録音 (4 声・オスティナート・持続音は録音の 1 音を移調するサンプラー、
  鼓動は録音の低い打鍵を 2 オクターヴ下げた音)。
    Introitus: 鼓動と持続音、最初の録音のループが立ち上がる
    Mix — 11 本の実音: 11 本の抜粋 (各 2 小節) を DJ のようにクロスフェードでつなぐ
    Kyrie — ループの重ね: 2 小節ごとに次の録音のループが入り、3 本が常に重なる。入るたびにその録音の主題を 1 声が歌う
    Fuga — 2 つずつ: 2 つの主題を同時に (上声と低音で)、それぞれ自分の録音の音で。下では 2 本のループが重なる
    Mantra — 全部のミックス: 1 小節ごとにループが 1 本ずつ増え、最後は 11 本全部が同時に回る。B-A-D-A ×6
    Lux aeterna: ピカルディ終止 → 最後の録音のループが消えていく
  使い方: python compose_tablet4.py <bank.json> [score_tablet4.json]
"""
import sys, math
from compose import *
import compose
import compose_heart as H
import compose_tablet as CT          # 抜粋・主題・和声づけ・移調 (同じ bank.json を読む)
import compose_tablet2 as T2         # テープ・ループ、実録音のオスティナート・持続音・鼓動 (post)
import compose_tablet3 as T3         # 抜粋の音量合わせ、録音の日時表記

add, REC, MARK, hm = CT.add, CT.REC, T3.MARK, T3.hm
BPM = 60
SEMIS = 2                            # ホ短調 (ニ短調から)
# 録音 id → 録音の調への移調 (ニ短調から)。これまでの曲の調、新しい録音は音高の分布から推定した短調
KEYS = {'20260920_154001': 3, '20260920_154118': 3, '20260922_090933': 2, '20260922_174527': -3, '20260922_175145': -4,
        '20260922_175429': -4, '20260922_175951': 2, '20260923_080607': -4, '20260923_080918': 2, '20260924_084937': 3,
        '20260924_085314': 2}
RIDS = sorted(r for r in REC if r in KEYS)
VOICE_SRC = {'S': '20260923_080918', 'A': '20260922_175951', 'T': '20260922_090933', 'B': '20260923_080607'}

def shift(rid):
    """テープの移調: 録音の調 → ホ短調 (-7〜+4 半音。下げるほうが多い = ゆっくり低く)"""
    return ((SEMIS - KEYS[rid] + 7) % 12) - 7

SUBJ, GAIN = [], {}

def build():
    bar_s = 240.0 / BPM; E = 2
    plan = []
    for rid in RIDS:
        ratio = 2 ** (shift(rid) / 12.0)
        t0, inside = CT.excerpt(rid, KEYS[rid], E * bar_s * ratio)
        T2.FRAG[rid] = t0; GAIN[rid] = T3.rec_gain(rid, t0, E * bar_s * ratio)
        subj = CT.make_subject(inside, KEYS[rid], BPM)
        SUBJ.append((rid, subj, CT.harmonize(subj)))
        plan.append((rid, ratio, t0, inside))
    N = len(plan)
    total = 4 + E * N + 2 * N + 12 + 12 + 4
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 0.75
    # ---------------- Introitus
    P.section(0, 'Introitus', '♩=60 の鼓動 (録音の低い打鍵) と持続音 — 最初の録音のループが立ち上がる。鼓動は最後まで止まらない')
    for v in VOICES: P.rest_bars(v, 0, 4)
    P.set_harms(0, [['Dm']] * 4)
    T2.MANTRA.append((0, 4, RIDS[0], ('DN', 'PK')))
    T2.loop(RIDS[0], 2, 2, BPM, 0.5 * GAIN[RIDS[0]], semis=shift(RIDS[0]), fade=[0.5, 0.9])
    CT.LAYOUT.append((0, 4, SEMIS, VOICE_SRC, {}))
    # ---------------- Mix — 11 本の実音をクロスフェードで (4 声は休む)
    b = 4; x0 = b
    P.section(b, 'Mix — 11 本の実音', '11 本の録音の抜粋 (各 2 小節) をクロスフェードでつなぐ — 全部テープのように速さごと移調してホ短調に')
    for v in VOICES: P.rest_bars(v, b, b + E * N)
    for i, (rid, ratio, t0, inside) in enumerate(plan):
        sh = shift(rid)
        add('REC', b * BPB, E * BPB + 2, 0, GAIN[rid], None, src=REC[rid]['file'], off=t0, rid=rid, semis=sh)
        for s in inside:
            for m in s['m']: add('TB', b * BPB + (s['t'] - t0) / ratio * BPM / 60.0, s['d'] / ratio * BPM / 60.0, m + sh - SEMIS, 0.0, None)
        for k in range(E * BPB):
            tt = t0 + k * 60.0 / BPM * ratio; cur = None
            for s in inside:
                if s['t'] <= tt + 0.05: cur = s
            if cur: P.harm[b * BPB + k] = transpose_h([[cur['ch']]], sh - SEMIS)[0][0]
        b += E
    T2.MANTRA.append((x0, b, RIDS[-1], ('PK',)))
    CT.LAYOUT.append((x0, b, SEMIS, VOICE_SRC, {}))
    # ---------------- Kyrie — ループの重ね: 2 小節ごとに次の録音が入り、その主題を 1 声が歌う
    k0 = b; cyc = ['A', 'S', 'T', 'B']; octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}
    P.section(k0, 'Kyrie — ループの重ね', '2 小節ごとに次の録音のループが入り、3 本が常に重なる。入るたびにその録音の主題を 1 声が、その録音の音で歌う')
    for i, (rid, ratio, t0, inside) in enumerate(plan):
        bb = k0 + 2 * i; subj = SUBJ[i][1]; v = cyc[i % 4]; tr = octs[v]
        if v == 'B' and min(m for _, m in subj) + tr < 36: tr += 12
        if max(m for _, m in subj) + tr > {'S': 81, 'A': 74, 'T': 69, 'B': 62}[v]: tr -= 12
        P.set_harms(bb, SUBJ[i][2]); P.place(v, bb, subj, tr, '主題 %s (%s)' % (MARK[i], hm(rid)))
        if i % 4 == 0: add('X', bb * BPB, 8, n('D3'), 0.25)
        nb = min(6, k0 + 2 * N - bb)
        T2.loop(rid, bb, nb, BPM, 0.5 * GAIN[rid], semis=shift(rid), fade=[0.5, 0.8, 1.0, 1.0, 0.8, 0.5][:nb])
        CT.LAYOUT.append((bb, bb + 2, SEMIS, {x: rid for x in VOICES}, {}))
    b = k0 + 2 * N
    T2.MANTRA.append((k0, b, RIDS[-1], ('DN', 'PK', 'OS')))
    # ---------------- Fuga — 2 つずつ: 2 つの主題を同時に
    f0 = b
    P.section(f0, 'Fuga — 2 つずつ', '2 つの主題を同時に、上声と低音で — それぞれ自分の録音の音で。下では 2 本のループが重なる')
    for k in range(12): P.dyn[f0 + k] = 0.85
    entries = []
    for p in range(6):
        i, j = (2 * p) % N, (2 * p + 1) % N; bb = f0 + 2 * p
        vi, vj = ('S', 'B') if p % 2 == 0 else ('A', 'T')
        labs = {}
        for idx, v in ((i, vi), (j, vj)):
            rid, subj, _ = SUBJ[idx]; tr = octs[v] + (7 if p % 3 == 2 else 0)
            if v == 'B' and min(m for _, m in subj) + tr < 36: tr += 12
            if max(m for _, m in subj) + tr > {'S': 81, 'A': 74, 'T': 69, 'B': 62}[v]: tr -= 12
            lab = '主題 %s%s' % (MARK[idx], ' 答唱' if p % 3 == 2 else '')
            P.place(v, bb, subj, tr, lab); labs[lab] = rid
            entries.append((bb * BPB, [(d, m + tr) for d, m in subj]))
            T2.loop(rid, bb, 2, BPM, 0.42 * GAIN[rid], semis=shift(rid), fade=[0.9, 0.7])
        rest = sorted(set(VOICES) - {vi, vj})
        CT.LAYOUT.append((bb, bb + 2, SEMIS, {vi: SUBJ[i][0], rest[0]: SUBJ[i][0], vj: SUBJ[j][0], rest[1]: SUBJ[j][0]}, labs))
    for bar in range(f0, f0 + 12):                        # 和声: その半小節で鳴る 2 つの主題の音を最も多く含む和音
        for h in range(2):
            a = bar * BPB + 2 * h; notes = []
            for e0, sb in entries:
                t = e0
                for d, m in sb:
                    ov = min(a + 2, t + d) - max(a, t)
                    if ov > 0: notes.append((ov * (2 if t <= a < t + d else 1), m))
                    t += d
            cs = max(CT.CANDS, key=lambda c: sum(w * (1 if m % 12 in chord(c)['pcs'] else -0.8) for w, m in notes)) if notes else 'Dm'
            for q in range(2): P.harm[a + q] = cs
    T2.MANTRA.append((f0, f0 + 12, RIDS[-1], ('DN', 'PK', 'OS')))
    # ---------------- Mantra — 全部のミックス: ループが 1 小節ごとに 1 本ずつ増え、最後は 11 本全部
    m0 = f0 + 12
    P.section(m0, 'Mantra — 全部のミックス', '1 小節ごとに録音のループが 1 本ずつ増え、最後は 11 本全部が同時に回る — B-A-D-A を 6 回唱える')
    for k in range(6):
        bb = m0 + 2 * k; P.set_harms(bb, H.MANTRA_PROG); P.place('A', bb, H.BADA, 0, 'B-A-D-A' if k == 0 else None)
        for q in range(2): P.place('B', bb + q, H.DRONE_BAR, 0, None)
        if k % 2 == 0: add('X', bb * BPB, 8, n('D3'), 0.25)
    for k in range(12):
        act = RIDS[:min(N, k + 1)]
        for rid in act:
            add('REC', (m0 + k) * BPB, BPB + 1.0, 0, 0.55 * GAIN[rid] / math.sqrt(len(act)), None, src=REC[rid]['file'], off=T2.FRAG[rid], rid=rid, loop=True, semis=shift(rid))
    T2.MANTRA.append((m0, m0 + 12, RIDS[-1], ('DN', 'PK')))
    # ---------------- Lux aeterna
    e0 = m0 + 12; last = RIDS[-1]
    P.section(e0, 'Lux aeterna', 'D 長調 (ホ長調) のピカルディ終止 → 最後の録音 %s のループが、鼓動とともに消えていく' % hm(last))
    P.set_harms(e0, [['D']] * 4); P.hold.update(range(m0, e0 + 4))
    P.place('S', e0, mat(('F#5', 8)), 0, None); P.place('A', e0, mat(('A4', 8)), 0, None); P.place('T', e0, mat(('D4', 8)), 0, None); P.place('B', e0, mat(('D3', 8)), 0, None)
    for v in VOICES: P.rest_bars(v, e0 + 2, e0 + 4)
    for k in range(16): P.dyn[m0 + k] = max(0.35, 0.8 - 0.03 * k)
    T2.loop(last, e0 + 1, 3, BPM, 0.6 * GAIN[last], semis=shift(last), fade=[1.0, 0.7, 0.45])
    T2.MANTRA.append((e0, e0 + 3, last, ('PK',)))
    CT.LAYOUT.append((m0, e0 + 4, SEMIS, VOICE_SRC, {}))
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1],
    'title': 'Requiem BADA — Tablet Sessions IV · Mix',
    'subtitle': '録音 11 本を重ねてミックスした、止まらない鼓動の上の洗脳のレクイエムとフーガ (ホ短調, 音はすべて録音から)',
    'footer': ['Introitus → Mix: 11 本の実音 → Kyrie: ループの重ね + 11 の主題 → Fuga: 2 つずつ → Mantra: 11 本全部のミックス + B-A-D-A ×6 → Lux aeterna',
               '録音はテープのように速さごと移調してホ短調に。4 声・オスティナート・持続音は録音の 1 音のサンプラー、鼓動は録音の低い打鍵 (♩=60 で最後まで)。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet4.json'
    compose.main(out, seed=43, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=T2.post)
    CT.finish(out)
    for rid, subj, hh in SUBJ: print(rid, 'shift %+d' % shift(rid), 'gain %.2f' % GAIN[rid], 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in subj))
