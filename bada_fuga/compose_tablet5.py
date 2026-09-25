#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions V · Mix (実音) — ループを使わず、録音そのものを長く流してミックスしたレクイエムとフーガ
  録音 5 本 (09-22 17:57 / 17:59, 09-23 08:09, 09-24 08:49 / 08:53) を、1 小節ループではなく実音のまま (速さも音高も元のまま)
  40〜64 秒ずつ流し、録音どうしを長いクロスフェードでつなぐ。各録音から、その調にいちばん合う区間を選ぶ。
  実音の後半では 4 声 (録音の 1 音のサンプラー) が録音の和音を全音符で静かに支える (レクイエム)。
    Introitus — 録音 08:49 (ヘ短調) の実音
    Fuga I — 08:49 の主題 → ヘ長調の終止 → (ナポリの和音) → ホ短調へ
    Kyrie — ミックス: 17:59 → 08:53 → 08:09 (ホ短調) の実音を 8 秒のクロスフェードでつなぐ
    Fuga II — 3 つの主題の三重フーガ (ホ短調) → 属和音で止まる
    Lacrimosa — 録音 17:57 (ロ短調) の実音
    Finale — 5 つの主題のフーガ → 録音 08:09 の本当の終わり (ホ短調) の実音で閉じる
  使い方: python compose_tablet5.py <bank.json> [score_tablet5.json]
"""
import sys
import numpy as np
from compose import *
import compose
import compose_tablet as CT          # 主題・和声づけ・区間ごとの移調 (同じ bank.json を読む)
import compose_tablet3 as T3         # 音量合わせ、録音の日時表記

add, REC, MARK, hm = CT.add, CT.REC, T3.MARK, T3.hm
BPM = 60; BAR_S = 240.0 / BPM
KEYS = {'20260924_084937': (3, 'ヘ短調'), '20260922_175951': (2, 'ホ短調'), '20260924_085314': (2, 'ホ短調'),
        '20260923_080918': (2, 'ホ短調'), '20260922_175717': (-3, 'ロ短調')}
ORDER = ['20260924_084937', '20260922_175951', '20260924_085314', '20260923_080918', '20260922_175717']
VOICE_SRC = {'S': '20260923_080918', 'A': '20260922_175951', 'T': '20260924_085314', 'B': '20260924_084937'}
MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
XF = 2                               # クロスフェード (小節)

USED = {}                            # 録音 id → すでに流した区間 [(開始, 終了)] (同じ所を 2 度流さない)

def best_window(rid, semis, seconds, avoid_end=0.0):
    """録音の中から、その調 (短調) にいちばん合う seconds 秒を選ぶ (打鍵の頭から始め、主和音で始まると加点)"""
    segs = REC[rid]['segs']; tonic = (2 + semis) % 12; prof = np.roll(MINOR, tonic)
    best = None
    for s in segs:
        t0 = s['t'] - 0.03
        if t0 < 2 or t0 + seconds > REC[rid]['dur'] - 1 - avoid_end: continue
        if any(t0 < u1 and t0 + seconds > u0 for u0, u1 in USED.get(rid, [])): continue
        h = np.zeros(12)
        for x in segs:
            if t0 <= x['t'] < t0 + seconds:
                for m in x['m']: h[m % 12] += x['d']
        if h.sum() == 0: continue
        sc = np.corrcoef(prof, h)[0, 1] + (0.08 if CT.root_pc(s['ch']) == tonic else 0)
        if best is None or sc > best[0]: best = (sc, t0)
    t0 = best[1] if best else 3.0
    return t0, [x for x in segs if t0 <= x['t'] < t0 + seconds]

def passage(P, rid, bar, bars, semis, choir_from, fin=0.03, fout=6.0, t0=None, gain=None, bpm=None, pshift=0, gmul=1.0):
    """実音を bars 小節流す。採譜は表示用、和声は録音の和音 (小節でいちばん長く鳴る和音)。choir_from 小節目から 4 声が全音符で支える。
    pshift: 速さを変えない移調 (半音)。semis はその移調のあとの調 (ニ短調から)"""
    bpm = bpm or BPM; BAR_S = 240.0 / bpm
    if t0 is None: t0, inside = best_window(rid, semis - pshift, bars * BAR_S)
    else: inside = [x for x in REC[rid]['segs'] if t0 <= x['t'] < t0 + bars * BAR_S]
    USED.setdefault(rid, []).append((t0, t0 + bars * BAR_S))
    g = gain if gain is not None else 0.75 * gmul * T3.rec_gain(rid, t0, bars * BAR_S)     # サンプラーの 4 声と釣り合う大きさに
    add('REC', bar * BPB, bars * BPB + 1.0, 0, g, None, src=REC[rid]['file'], off=t0, rid=rid, fin=fin, fout=fout, **({'pshift': pshift} if pshift else {}))
    for s in inside:
        for m in s['m']: add('TB', bar * BPB + (s['t'] - t0) * bpm / 60.0, s['d'] * bpm / 60.0, m + pshift - semis, 0.0, None)
    for k in range(bars):
        a, z = t0 + k * BAR_S, t0 + (k + 1) * BAR_S; w = {}
        for s in inside:
            ov = min(z, s['t'] + s['d']) - max(a, s['t'])
            if ov > 0: w[s['ch']] = w.get(s['ch'], 0) + ov
        prev = None
        for s in REC[rid]['segs']:
            if s['t'] <= a: prev = s['ch']
        ch = max(w, key=w.get) if w else (prev or CT.transpose_h([['Dm']], semis - pshift)[0][0])
        lab = transpose_h([[ch]], pshift - semis)[0][0]
        for q in range(BPB): P.harm[(bar + k) * BPB + q] = lab
    for v in VOICES: P.rest_bars(v, bar, bar + choir_from)
    P.hold.update(range(bar + choir_from, bar + bars))
    for k in range(bars): P.dyn[bar + k] = 0.42
    return t0, g

SUBJ = {}

def expo(P, b, rid, lab_i):
    """4 声フーガの提示 (A → S 答唱 → B → T 答唱) — 8 小節"""
    subj, H_sub = SUBJ[rid][0], SUBJ[rid][1]; lab = '主題 %s (%s)' % (lab_i, hm(rid))
    P.set_harms(b, H_sub); P.place('A', b, subj, 0, lab)
    for v in 'STB': P.rest_bars(v, b, b + 2)
    P.set_harms(b + 2, transpose_h(H_sub, 7)); P.place('S', b + 2, subj, 7 + 12 if max(m for _, m in subj) + 7 < 72 else 7, lab + ' 答唱')
    for v in 'TB': P.rest_bars(v, b + 2, b + 4)
    P.set_harms(b + 4, H_sub); P.place('B', b + 4, subj, -24 if min(m for _, m in subj) - 24 >= 36 else -12, lab)
    P.rest_bars('T', b + 4, b + 6)
    P.set_harms(b + 6, transpose_h(H_sub, 7)); P.place('T', b + 6, subj, 7 - 12, lab + ' 答唱')

def harm_from_entries(P, b0, b1, entries):
    """その半小節で鳴る主題の音を最も多く含む和音"""
    for bar in range(b0, b1):
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

def build():
    for rid in ORDER:                                     # 主題: 主和音で始まる最初の 13 秒の最上声から
        semis = KEYS[rid][0]; t0, inside = CT.excerpt(rid, semis, 13.0)
        subj = CT.make_subject(inside, semis, 56); SUBJ[rid] = (subj, CT.harmonize(subj))
    total = 16 + 10 + 1 + (3 * 12 - 2 * XF) + 17 + 12 + 1 + 12 + 1 + 6
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 0.8
    ra, rb, rc, rd, re_ = ORDER
    # ---------------- Introitus: 08:49 の実音 (ヘ短調)
    P.section(0, 'Introitus — 録音 %s の実音' % hm(ra), 'ヘ短調 ／ 録音 %s をループせずそのまま 64 秒 — 後半は 4 声 (録音の音) が録音の和音を静かに支える' % ra)
    passage(P, ra, 0, 16, KEYS[ra][0], 6)
    CT.LAYOUT.append((0, 16, KEYS[ra][0], {v: ra for v in VOICES}, {}))
    # ---------------- Fuga I (ヘ短調) → ヘ長調の終止
    b = 16
    P.section(b, 'Fuga I — 主題 ① 〈録音 %s〉' % hm(ra), '実音の最上声から作った主題の 4 声フーガ → ヘ長調 (ピカルディ) で終わり、ナポリの和音としてホ短調へ')
    expo(P, b, ra, '①')
    P.set_harms(b + 8, [['Gm', 'Gm', 'A7', 'A7'], ['D']]); P.hold.add(b + 9)
    CT.LAYOUT.append((b, b + 10, KEYS[ra][0], {v: ra for v in VOICES}, {}))
    b += 10
    P.set_harms(b, [['Eb', 'Eb', 'A7', 'A7']]); P.hold.add(b)          # ホ短調で F (ナポリ) → B7
    CT.LAYOUT.append((b, b + 1, 2, VOICE_SRC, {}))
    b += 1
    # ---------------- Kyrie — ミックス: 17:59 → 08:53 → 08:09 をクロスフェードで (ホ短調)
    k0 = b
    P.section(b, 'Kyrie — ミックス (実音)', '録音 %s → %s → %s をループせず実音のまま、8 秒のクロスフェードで重ねてつなぐ (ホ短調)' % (hm(rb), hm(rc), hm(rd)))
    spans = [(rb, 12), (rc, 12), (rd, 12)]
    for i, (rid, bars) in enumerate(spans):
        st = b - (XF if i else 0)
        passage(P, rid, st, bars, 2, 4 if i == 0 else XF + 2, fin=(0.03 if i == 0 else XF * BAR_S), fout=XF * BAR_S)
        if i:                                              # 重なりの小節は、入ってくる録音の和声のまま 4 声は休む
            for v in VOICES: P.rest_bars(v, st, st + XF)
        CT.LAYOUT.append((st if i == 0 else st + XF, st + bars, 2, {v: rid for v in VOICES}, {}))
        b = st + bars
    # ---------------- Fuga II — 3 つの主題の三重フーガ (ホ短調) → 属和音で止まる
    f0 = b
    P.section(f0, 'Fuga II — 3 つの主題 〈%s · %s · %s〉' % (hm(rb), hm(rc), hm(rd)), '3 本の録音の主題の三重フーガ — 各主題は自分の録音の音で鳴る。最後は属和音で止まり、ロ短調の録音へ')
    octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}
    plan = [(0, 'A', rb, 0, '②'), (2, 'S', rc, 0, '③'), (4, 'T', rd, 0, '④'), (6, 'B', rb, 0, '②'), (8, 'S', rc, 7, '③'),
            (10, 'A', rd, 7, '④'), (12, 'T', rb, 0, '②'), (12, 'S', rc, 0, '③'), (14, 'B', rd, 0, '④')]
    entries, labmap = [], {}
    for bar, v, rid, tr0, mk in plan:
        subj = SUBJ[rid][0]; tr = octs[v] + tr0
        if v == 'B' and min(m for _, m in subj) + tr < 36: tr += 12
        if max(m for _, m in subj) + tr > {'S': 81, 'A': 74, 'T': 69, 'B': 62}[v]: tr -= 12
        lab = '主題 %s%s' % (mk, ' 答唱' if tr0 else ''); labmap[lab] = rid
        P.place(v, f0 + bar, subj, tr, lab); entries.append(((f0 + bar) * BPB, [(d, m + tr) for d, m in subj]))
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f0, f0 + z)
    harm_from_entries(P, f0, f0 + 16, entries)
    P.set_harms(f0 + 16, [['A7']]); P.hold.add(f0 + 16)
    CT.LAYOUT.append((f0, f0 + 17, 2, VOICE_SRC, labmap))
    b = f0 + 17
    # ---------------- Lacrimosa — 17:57 の実音 (ロ短調)
    P.section(b, 'Lacrimosa — 録音 %s の実音' % hm(re_), 'ロ短調 ／ 録音 %s をループせずそのまま 48 秒 — 後半は 4 声が録音の和音を支える' % re_)
    passage(P, re_, b, 12, KEYS[re_][0], 5)
    CT.LAYOUT.append((b, b + 12, KEYS[re_][0], {v: re_ for v in VOICES}, {}))
    b += 12
    P.set_harms(b, [['A7']]); P.hold.add(b)                             # ホ短調の B7
    CT.LAYOUT.append((b, b + 1, 2, VOICE_SRC, {}))
    b += 1
    # ---------------- Finale — 5 つの主題のフーガ → 08:09 の本当の終わりの実音
    f1 = b
    P.section(f1, 'Finale — Fuga a cinque soggetti', '5 本の録音の主題が 1 小節おきに入る — 各主題は自分の録音の音で (ホ短調)')
    for k in range(13): P.dyn[f1 + k] = 0.9
    order = [ra, rb, rc, rd, re_]; mks = '①②③④⑤'; vs = ['A', 'S', 'T', 'B', 'A', 'S', 'T', 'B', 'A', 'S']
    entries, labmap = [], {}
    for k in range(10):
        rid = order[k % 5]; v = vs[k]; w = k // 5; subj = SUBJ[rid][0]; tr = octs[v] + (7 if w else 0)
        if v == 'B' and min(m for _, m in subj) + tr < 36: tr += 12
        if max(m for _, m in subj) + tr > {'S': 81, 'A': 74, 'T': 69, 'B': 62}[v]: tr -= 12
        lab = '主題 %s%s' % (mks[k % 5], ' 答唱' if w else ''); labmap[lab] = rid
        P.place(v, f1 + k, subj, tr, lab); entries.append(((f1 + k) * BPB, [(d, m + tr) for d, m in subj]))
    harm_from_entries(P, f1, f1 + 11, entries)
    P.set_harms(f1 + 11, [['Gm', 'Gm', 'A7', 'A7']])
    CT.LAYOUT.append((f1, f1 + 12, 2, VOICE_SRC, labmap))
    b = f1 + 12
    P.set_harms(b, [['A7']]); P.hold.add(b)
    CT.LAYOUT.append((b, b + 1, 2, VOICE_SRC, {}))
    b += 1
    fin_t0 = REC[rd]['dur'] - 5 * BAR_S - 0.5
    P.section(b, 'In paradisum — 録音 %s の本当の終わり' % hm(rd), '録音 %s の最後の 20 秒を実音のまま — 録音自身のホ短調の終止で閉じる' % rd)
    passage(P, rd, b, 5, 2, 2, fin=1.0, fout=2.5, t0=fin_t0)
    for v in VOICES: P.rest_bars(v, b + 5, b + 6)
    P.set_harms(b + 5, [['Dm']])
    CT.LAYOUT.append((b, b + 6, 2, {v: rd for v in VOICES}, {}))
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1],
    'title': 'Requiem BADA — Tablet Sessions V · Mix',
    'subtitle': '実音・ループなし — 録音 5 本を実音のままクロスフェードでつなぎ、レクイエムとフーガに (音はすべて録音から)',
    'rec_order': ORDER,                                   # 凡例の ①〜⑤ を主題の番号と同じ順に
    'footer': ['Introitus 08:49 (ヘ短調) → Fuga I → Kyrie: 17:59 → 08:53 → 08:09 のミックス → Fuga II (三重) → Lacrimosa 17:57 (ロ短調) → Finale → In paradisum',
               '録音は速さも音高も元のまま。実音の後半は 4 声 (録音の 1 音のサンプラー) が録音の和音を全音符で支える。最後は 08:09 の本当の終わり。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet5.json'
    compose.main(out, seed=47, bpm=BPM, builder=build, meta=META, extras=CT.extras)
    CT.finish(out)
    for rid in ORDER: print(rid, 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in SUBJ[rid][0]))
