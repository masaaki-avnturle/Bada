#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXXXVI · Missa nel palazzetto (10/13・10/12・10/03 の 11 曲をベースに、雰囲気に合うように、キリスト教会のミサ曲 — Kyrie・Gloria・Credo・Sanctus・Benedictus・Agnus Dei — を主題に)
  11 の録音 (半音上げてロ短調に; 13:06 は全音上げてニ長調に) を段落ごとに敷き、その上にミサ通常文の形で、録音の音から作った聖歌風の主題を 4 声の実音のピアノと管弦楽で:
    Kyrie    (ロ短調, ♩=56)   10/13 06:41 → 10/12 06:27 → 10/13 06:42。06:41 の音から作った主題のフーガ (Kyrie I) → Christe (反行、2 声) → Kyrie II (ストレッタ)
    Gloria   (ニ長調)          10/03 13:27 → 13:24 → 13:22。13:27 の主題 (CXXVII の二重フーガの第 2 主題) のフガート、弦・フルート・トランペット → Et in terra pax (13:24 の音の唱え、静かに) → Amen (ストレッタ、ティンパニ)
    Credo    (ロ短調)          10/12 13:03 → 13:06 → 13:07。13:03 の音の唱え (ユニゾン) → Et incarnatus est (13:06 の讃美歌、ニ長調、コラール) → Et resurrexit (子守歌の大黒柱の主題のフガート、金管)
    Sanctus  (ニ長調)          10/12 06:30 → 10/03 13:19。06:42 の音から作った旋律のコラール → Benedictus (06:27 の音の旋律をソプラノ独唱、共鳴) → Hosanna (高い開いた 5 度、フルート)
    Agnus Dei (ロ短調 → ニ長調) 10/13 06:41 → 06:42。B-A-D-A の唱えに Kyrie の主題が重なる → Dona nobis pacem (Sanctus の旋律のコラール、ニ長調の和音、深い鐘)
  使い方: BANK1013=<bank1013.json> SCORE89=<score_tablet89.json> python compose_tablet136.py <bank1012b.json> <bank1012.json> <bank112.json> <bank109.json> <wav のフォルダ> [score_tablet136.json]
"""
import sys, os, json, math
OUT = sys.argv[6] if len(sys.argv) > 6 else 'score_tablet136.json'
sys.argv = sys.argv[:6] + ['/dev/null']
import compose_tablet127 as T
from compose import *
import compose
import compose_heart as H
RECS, R41, R42, R03, R06, R07, R24, RS, WDIR, RATE, PSRC, GMAJ = T.RECS, T.R41, T.R42, T.R03, T.R06, T.R07, T.R24, T.RS, T.WDIR, T.RATE, T.PSRC, T.GMAJ
R27A, R30, R27, R22 = '20261012_062753', '20261012_063057', '20261003_132703', '20261003_132245'
extras, RH, add, entry, harm_fit, rest_others, invert, augment, aphrase, phrase = T.extras, T.RH, T.add, T.entry, T.harm_fit, T.rest_others, T.invert, T.augment, T.aphrase, T.phrase
SUBJ27, PILLAR = T.SUBJ27, T.PILLAR
CANDS_BM = ['Bm', 'D', 'G', 'F#m', 'A', 'Em', 'F#', 'F#7', 'Bm/D', 'G/B', 'D/F#', 'Em/G', 'Bsus4', 'C#m7b5']
CANDS_D = ['D', 'G', 'A', 'A7', 'Bm', 'Em', 'F#m', 'D/F#', 'G/B', 'A/C#', 'Em7', 'Asus4', 'Bm/D', 'D/A', 'G/D']
BPM = 56
KYRIE, GLORIA, CREDO, SANCTUS, AGNUS, TOTAL = 0, 48, 96, 150, 190, 232
NAMES = {R41: '10/13 06:41', R42: '10/13 06:42', R27A: '10/12 06:27', R30: '10/12 06:30', R03: '10/12 13:03', R06: '10/12 13:06', R07: '10/12 13:07', R27: '10/03 13:27', R24: '10/03 13:24', R22: '10/03 13:22', RS: '10/03 13:19'}
# (録音, 小節, 大きさ, テープの移調, 抜粋の始まり (秒), 抜粋の長さ (秒; None = 全部))
PLAYS = [(R41, 1, 0.45, 1, 0.0, None), (R27A, 17, 0.4, 1, 0.0, 60.0), (R42, 32, 0.4, 1, 0.0, None),
         (R27, GLORIA + 1, 0.45, 1, 0.0, 60.0), (R24, GLORIA + 18, 0.4, 1, 0.0, 55.0), (R22, GLORIA + 32, 0.45, 1, 0.0, 55.0),
         (R03, CREDO + 1, 0.4, 1, 0.0, 60.0), (R06, CREDO + 16, 0.4, 2, 0.0, 55.0), (R07, CREDO + 30, 0.45, 1, 0.0, 60.0),
         (R30, SANCTUS + 1, 0.4, 1, 0.0, None), (RS, SANCTUS + 18, 0.4, 1, 0.0, 60.0),
         (R41, AGNUS + 1, 0.4, 1, 0.0, None), (R42, AGNUS + 18, 0.4, 1, 0.0, None)]
def play_len(rid, dur): return (RECS[rid]['dur'] if dur is None else dur)
def tune_from(rid, lo=62, hi=79, rhythm=(1, 1, 1, 1, 2, 2), ends=((74, 78), (76, 71), (74, 78), (74, 74)), n=4):
    """録音の最上声の音 (+1 でロ短調/ニ長調に、五音音階に寄せる) を讃美歌のリズムに — n 句、各句の終わりは長い音"""
    tops = []
    for sg in RECS[rid]['segs']:
        m = sg['m'][-1] + 1
        if sg['d'] < 0.4: continue
        if tops and tops[-1] % 12 == m % 12: continue
        m = min((x for x in range(m - 2, m + 3) if x % 12 in GMAJ), key=lambda x: abs(x - m))
        while m < lo: m += 12
        while m > hi: m -= 12
        if tops and abs(m - tops[-1]) > 7: m = min((m + 12 * k for k in (-1, 0, 1)), key=lambda x: abs(x - tops[-1]))
        while m < lo: m += 12
        while m > hi: m -= 12
        tops.append(m)
    rh = list(rhythm) * n; out = [(d, tops[i % len(tops)]) for i, d in enumerate(rh)]
    for ph in range(n):
        i = ph * len(rhythm) + len(rhythm) - 1; out[i] = (2, min(ends[ph % len(ends)], key=lambda x: abs(x - out[i][1])))
    return out
KYRIE_T = aphrase(0)                                                                               # 06:41 の音から (14 拍)
TERRA_T = tune_from(R24, lo=59, hi=74, rhythm=(2, 1, 1, 2, 2), ends=((71, 66), (74, 71), (71, 66), (71, 71)))     # Et in terra pax (13:24 の音、ロ短調の五音)
CREDO_T = tune_from(R03, lo=59, hi=74, rhythm=(1, 1, 1, 1, 1, 1, 2), ends=((71, 66), (74, 71), (71, 66), (71, 71)))   # Credo の唱え (13:03 の音)
SANCTUS_T = tune_from(R42)                                                                         # 06:42 の音から (ニ長調)
BENED_T = tune_from(R27A, lo=66, hi=81, rhythm=(2, 1, 1, 2, 1, 1, 4), ends=((78, 81), (74, 76), (78, 81), (74, 74)))    # Benedictus (06:27 の音)
def ph(mat, k, n): return mat[n * k: n * k + n]
BADA = [(d, m + 1) for d, m in H.BADA]
SAN_RH = ['D', 'G', 'D', 'A', 'Bm', 'G', 'D', 'A', 'D', 'G', 'A', 'D', 'G', 'A', 'D', 'D']
OG = 0.34
def oadd(v, beat, dbeats, m, gain, label=None): add(v, beat, dbeats, m, gain * OG, label)

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.95
    for q in range(TOTAL * BPB):
        cur = None
        for rid, bar, g, sm, off, dur in PLAYS:
            rec = RECS[rid]; t0 = bar * BPB; db = play_len(rid, dur) / RATE(sm) * BPM / 60.0
            if t0 <= q < t0 + db:
                frac = (q - t0) * 60.0 / BPM * RATE(sm) + off; cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
                cur = transpose_h([[cur]], sm)[0][0]
        if cur is None: cur = 'D' if (GLORIA <= q // BPB < CREDO or SANCTUS <= q // BPB < AGNUS or q // BPB >= AGNUS + 18) else 'Bm'
        if SANCTUS + 2 <= q // BPB < SANCTUS + 18: cur = SAN_RH[q // BPB - SANCTUS - 2]
        if AGNUS + 19 <= q // BPB < AGNUS + 35: cur = SAN_RH[q // BPB - AGNUS - 19]
        RH.append(cur); P.harm[q] = cur
    # Kyrie
    P.section(KYRIE, 'Kyrie — フーガ (ロ短調, ♩=56)', '10/13 06:41 の実音の上で、06:41 の音から作った主題のフーガ (アルト → ソプラノ 答唱 → バス → テノール 答唱) → Christe (10/12 06:27 の実音、反行の 2 声と保続) → Kyrie II (06:42 の実音、ストレッタ)。高い開いた 5 度の弦、深い鐘')
    f = KYRIE + 3; E = []; rest_others(P, KYRIE, f, '')
    for k, v in enumerate('ASBT'):
        entry(P, f + 4 * k, v, KYRIE_T, 7 if k % 2 else 0, 'Kyrie — 主題' + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, f + 4 * k, f + 4 * (k + 1))
    harm_fit(P, KYRIE, f + 16, E, CANDS_BM); rest_others(P, f + 16, f + 18, ''); f += 18; E = []
    for k in range(3):
        entry(P, f + 4 * k, 'SAS'[k], invert(KYRIE_T), 0 if k < 2 else 7, 'Christe (反行)' if k == 0 else None, E)
        for w in VOICES:
            if w != 'SAS'[k]: P.rest_bars(w, f + 4 * k, f + 4 * k + 4)
        P.place('TB'[k % 2], f + 4 * k, [(4, 47 - 12 * (k % 2))] * 4, 0, None)
    harm_fit(P, f, f + 12, E, CANDS_BM); rest_others(P, f + 12, f + 13, ''); f += 13; E = []
    for k, v in enumerate('ASTB'): entry(P, f + k, v, KYRIE_T, 0, 'Kyrie II — ストレッタ' if k == 0 else None, E)
    for k, v in enumerate('SATB'): entry(P, f + 6 + k, v, KYRIE_T, 7 if k % 2 else 0, None, E)
    harm_fit(P, f, GLORIA, E, CANDS_BM); P.hold.update(range(f + 11, GLORIA)); rest_others(P, GLORIA - 2, GLORIA, '')
    # Gloria
    P.section(GLORIA, 'Gloria — フガート (ニ長調)', '10/03 13:27 の実音の上で、13:27 の主題 (CXXVII の二重フーガの第 2 主題) のフガート (ソプラノ → アルト → テノール → バス)、弦・フルート・トランペット → Et in terra pax (13:24 の実音、13:24 の音の唱えを静かにユニゾンで) → Amen (13:22 の実音、ストレッタ、ティンパニ)')
    f = GLORIA + 2; E = []; rest_others(P, GLORIA, f, '')
    for k, v in enumerate('SATB'):
        entry(P, f + 3 * k, v, SUBJ27, 7 if k % 2 else 0, 'Gloria — 主題 (13:27)' + (' 答唱' if k % 2 else ''), E)
        for w in 'SATB'[k + 1:]: P.rest_bars(w, f + 3 * k, f + 3 * (k + 1))
    harm_fit(P, GLORIA, f + 14, E, CANDS_D); rest_others(P, f + 14, GLORIA + 19, ''); f = GLORIA + 19; E = []
    for k in range(3):
        for v in VOICES: entry(P, f + 4 * k, v, ph(TERRA_T, k, 5), (0 if v == 'S' else -12 if v == 'A' else -24 if v == 'T' else -36), ('Et in terra pax (ユニゾン) 第 %d 句' % (k + 1)) if v == 'S' else None, E)
        for v in VOICES: P.rest_bars(v, f + 4 * k + 2, f + 4 * k + 4)
    harm_fit(P, f, f + 12, E, CANDS_D); rest_others(P, f + 12, GLORIA + 33, ''); f = GLORIA + 33; E = []
    for k, v in enumerate('BTAS'): entry(P, f + k, v, SUBJ27, 0, 'Amen — ストレッタ' if k == 0 else None, E)
    for k, v in enumerate('SATB'): entry(P, f + 5 + k, v, SUBJ27, 7 if k % 2 else 0, None, E)
    harm_fit(P, f, CREDO, E, CANDS_D); P.hold.update(range(f + 10, CREDO)); rest_others(P, CREDO - 2, CREDO, '')
    # Credo
    P.section(CREDO, 'Credo — 唱え (ロ短調)', '10/12 13:03 の実音の上で、13:03 の音の唱えを 4 声のユニゾンで (Credo in unum Deum) → Et incarnatus est (13:06 の実音を全音上げてニ長調に、13:06 の讃美歌のコラール) → Et resurrexit (13:07 の実音、子守歌の大黒柱の主題のフガート、金管、ティンパニ)')
    f = CREDO + 2; E = []; rest_others(P, CREDO, f, '')
    for k in range(4):
        for v in VOICES: entry(P, f + 3 * k, v, ph(CREDO_T, k, 7), (0 if v == 'S' else -12 if v == 'A' else -24 if v == 'T' else -36), ('Credo (ユニゾン) 第 %d 句' % (k + 1)) if v == 'S' else None, E)
        for v in VOICES: P.rest_bars(v, f + 3 * k + 2, f + 3 * k + 3)
    harm_fit(P, f, f + 12, E, CANDS_BM); rest_others(P, f + 12, CREDO + 17, ''); f = CREDO + 17; E = []
    for k in range(4): entry(P, f + 2 * k + (1 if k >= 2 else 0), 'S', phrase(k), 0, 'Et incarnatus est (13:06 の讃美歌、コラール)' if k == 0 else None, E)
    P.hold.update(range(f, f + 10)); harm_fit(P, f, f + 10, E, CANDS_D); rest_others(P, f + 10, CREDO + 31, ''); f = CREDO + 31; E = []
    for k, v in enumerate('BTAS'):
        entry(P, f + 2 * k, v, PILLAR, 7 if k % 2 else 0, 'Et resurrexit — 大黒柱の主題' + (' 答唱' if k % 2 else ''), E)
        for w in 'BTAS'[k + 1:]: P.rest_bars(w, f + 2 * k, f + 2 * (k + 1))
    for k, v in enumerate('SATB'): entry(P, f + 10 + 2 * k, v, invert(PILLAR), 0, '反行' if k == 0 else None, E)
    harm_fit(P, f, SANCTUS, E, CANDS_BM); P.hold.update(range(f + 17, SANCTUS)); rest_others(P, SANCTUS - 2, SANCTUS, '')
    # Sanctus
    P.section(SANCTUS, 'Sanctus — コラール (ニ長調)', '10/12 06:30 の実音の上で、06:42 の音から作った旋律を 4 声のコラールに (Sanctus, Sanctus, Sanctus) → Benedictus (10/03 13:19 の実音、06:27 の音の旋律をソプラノが独唱、共鳴) → Hosanna (高い開いた 5 度、フルート)')
    E = []; rest_others(P, SANCTUS, SANCTUS + 2, '')
    for k in range(4):
        b = SANCTUS + 2 + 4 * k
        entry(P, b, 'S', ph(SANCTUS_T, k, 6), 0, 'Sanctus 第 %d 句' % (k + 1), E)
        if k < 3:
            for v in 'ATB': P.rest_bars(v, b + 2, b + 4)
    P.hold.update(range(SANCTUS + 2, SANCTUS + 18)); harm_fit(P, SANCTUS + 2, SANCTUS + 18, E, CANDS_D); rest_others(P, SANCTUS + 18, SANCTUS + 20, ''); f = SANCTUS + 20; E = []
    for k in range(4): entry(P, f + 3 * k, 'S', ph(BENED_T, k, 7), 0, 'Benedictus (ソプラノ独唱、06:27 の音)' if k == 0 else None, E)
    for v in 'ATB': P.rest_bars(v, f, f + 12)
    harm_fit(P, f, f + 12, E, CANDS_D); f += 12
    for q in range(f * BPB, AGNUS * BPB): P.harm[q] = 'D'
    for v in 'ATB': P.rest_bars(v, f, AGNUS)
    P.place('S', f, [(4, 81)] * 4, 0, 'Hosanna (高いラ)'); P.rest_bars('S', f + 4, AGNUS)
    # Agnus Dei
    P.section(AGNUS, 'Agnus Dei — B-A-D-A (ロ短調 → ニ長調)', '10/13 06:41 の実音の上で、B-A-D-A の唱え (アルト) に Kyrie の主題がソプラノに重なる、バスの保続 (シ)、深い鐘 → Dona nobis pacem (06:42 の実音、Sanctus の旋律のコラール、ニ長調の和音、深い鐘)')
    rest_others(P, AGNUS, AGNUS + 2, ''); E = []
    for k in range(4):
        bb = AGNUS + 2 + 4 * k
        P.place('A', bb, BADA, 0, 'B-A-D-A' if k == 0 else None); E.append((bb * BPB, [(d, m) for d, m in BADA]))
        if k % 2 == 1: entry(P, bb, 'S', KYRIE_T, 0, 'Kyrie の主題' if k == 1 else None, E)
        else: P.rest_bars('S', bb, bb + 4)
        P.rest_bars('T', bb, bb + 4); P.place('B', bb, [(4, 47)] * 4, 0, 'バスの保続' if k == 0 else None)
    P.hold.update(range(AGNUS + 2, AGNUS + 18)); harm_fit(P, AGNUS + 2, AGNUS + 18, E, CANDS_BM); rest_others(P, AGNUS + 18, AGNUS + 19, ''); f = AGNUS + 19; E = []
    for k in range(4):
        b = f + 4 * k
        entry(P, b, 'S', ph(SANCTUS_T, k, 6), 0, 'Dona nobis pacem (Sanctus の旋律、コラール)' if k == 0 else None, E)
        if k < 3:
            for v in 'ATB': P.rest_bars(v, b + 2, b + 4)
    P.hold.update(range(f, TOTAL)); harm_fit(P, f, f + 16, E, CANDS_D); f += 16
    for b in range(f, TOTAL): P.set_harm(b, 'D')
    P.place('S', f, [(4, 78)] * 5, 0, 'pacem — ニ長調 (レ・ラ・ファ#)'); P.place('A', f, [(4, 74)] * 5, 0, ''); P.place('T', f, [(4, 69)] * 5, 0, ''); P.place('B', f, [(4, 50)] * 5, 0, '')
    for v in VOICES: P.rest_bars(v, f + 5, TOTAL)
    return P

def line(v, bar, mat, tr, g, label=None, beat=0):
    t = bar * BPB + beat; first = True
    for d, m in mat:
        oadd(v, t, d, m + tr, g, label if first else None); first = False; t += d
def chord_pad(P, b0, b1, parts, g, label=None):
    q = b0 * BPB; first = True
    while q < b1 * BPB:
        h = P.harm[q]; q1 = q
        while q1 < b1 * BPB and P.harm[q1] == h: q1 += 1
        c = chord(h)
        for v, lo, hi in parts:
            tones = sorted({min((x for x in range(lo, hi) if x % 12 == p), key=lambda x: abs(x - (lo + hi) / 2)) for p in (c['root'], c['third'], c['fifth'])})
            for i, m in enumerate(tones[:3] if v != 'CB' else [min(tones)]): oadd(v, q + 0.03 * i, (q1 - q) + 0.3, m if v != 'CB' else m - 12, g * (1.0 if i == 0 else 0.8), label if (first and i == 0) else None); first = False
        q = q1
def fifths(b0, b1, g, label, m1=90, m2=83):
    for b in range(b0, b1, 4):
        oadd('V1', b * BPB, 4 * BPB + 0.5, m1, g, label if b == b0 else None); oadd('V2', b * BPB + 0.05, 4 * BPB + 0.5, m2, g * 0.85)
        oadd('CB', b * BPB, 4 * BPB + 0.5, 35 if m1 == 90 else 38, g * 1.5, None)
def strings_follow(b0, mat, g, label, step=2, order=(('V1', 12), ('V2', 0), ('VA', -12), ('VC', -24))):
    for k, (v, tr) in enumerate(order): line(v, b0 + step * k, mat, tr + (7 if k % 2 else 0), g, label if k == 0 else None)

def post(P, events, ex):
    for rid, bar, g, sm, off, dur in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '_clean.wav'), off=off, fin=0.5 if bar > 1 else 0.02, fout=5.0, semis=sm, rid=rid + '.wav', tag='%s — 実音 (%s)' % (NAMES[rid], '全音上げてニ長調に' if sm == 2 else '半音上げてロ短調に'))
    # Kyrie
    fifths(KYRIE + 1, KYRIE + 17, 0.14, '高い開いた 5 度 (Vn, pp)')
    strings_follow(KYRIE + 37, KYRIE_T, 0.22, '弦 — Kyrie の主題')
    chord_pad(P, KYRIE + 19, KYRIE + 31, [('VA', 50, 64), ('CB', 43, 55)], 0.1)
    # Gloria
    strings_follow(GLORIA + 2, SUBJ27, 0.26, '弦 — Gloria の主題 (Vn I → Vn II → Va → Vc)', step=3)
    line('FL', GLORIA + 14, SUBJ27, 12, 0.16, 'フルート'); line('TR', GLORIA + 14, SUBJ27, 0, 0.24, 'トランペット — 主題')
    chord_pad(P, GLORIA + 2, GLORIA + 16, [('VA', 50, 64), ('VC', 43, 55), ('CB', 43, 55)], 0.14)
    for b in range(GLORIA + 19, GLORIA + 31, 4): oadd('VA', b * BPB, 4 * BPB + 0.5, 62, 0.12, 'Va (静かに)' if b == GLORIA + 19 else None); oadd('VC', b * BPB, 4 * BPB + 0.5, 50, 0.12)
    strings_follow(GLORIA + 34, SUBJ27, 0.26, '弦 — Amen のストレッタ', step=1)
    line('TR', GLORIA + 40, SUBJ27, 12, 0.26, 'トランペット'); line('TB', GLORIA + 40, augment(SUBJ27), -12, 0.28, 'トロンボーン — 拡大')
    for k, b in enumerate(range(GLORIA + 36, CREDO - 2, 2)): oadd('TP', b * BPB, 2.0, 38 if k % 2 == 0 else 45, 0.3 + 0.03 * k, 'ティンパニ' if k == 0 else None)
    chord_pad(P, GLORIA + 33, CREDO - 2, [('VA', 50, 64), ('VC', 43, 55), ('CB', 43, 55)], 0.16)
    # Credo
    for b in range(CREDO + 2, CREDO + 14, 4): oadd('CB', b * BPB, 4 * BPB + 0.5, 35, 0.2, 'コントラバスの保続 (シ)' if b == CREDO + 2 else None); oadd('VC', b * BPB, 4 * BPB + 0.5, 47, 0.14)
    chord_pad(P, CREDO + 17, CREDO + 27, [('V2', 62, 76), ('VA', 55, 67), ('VC', 43, 55)], 0.14, 'Vn II・Va・Vc の和音 (Et incarnatus est)')
    strings_follow(CREDO + 33, PILLAR, 0.24, '弦 — 大黒柱の主題', step=2, order=(('VC', -24), ('VA', -12), ('V2', 0), ('V1', 12)))
    line('HN', CREDO + 41, augment(PILLAR), -12, 0.26, 'ホルン — 拡大'); line('TB', CREDO + 41, augment(PILLAR), -24, 0.26, 'トロンボーン')
    for k, b in enumerate(range(CREDO + 37, SANCTUS - 2, 3)): oadd('TP', b * BPB, 2.0, 35 if k % 2 == 0 else 42, 0.26 + 0.03 * k, 'ティンパニ' if k == 0 else None)
    chord_pad(P, CREDO + 35, SANCTUS - 2, [('VA', 50, 64), ('CB', 43, 55)], 0.14)
    # Sanctus
    chord_pad(P, SANCTUS + 2, SANCTUS + 18, [('V2', 62, 76), ('VA', 55, 67), ('VC', 43, 55)], 0.16, 'Vn II・Va・Vc の和音')
    t = (SANCTUS + 20) * BPB; first = True
    for d, m in BENED_T: oadd('FL', t, d, m + 12, 0.1, 'フルート (Benedictus、1 オクターヴ上)' if first else None); first = False; t += d
    chord_pad(P, SANCTUS + 20, SANCTUS + 32, [('VA', 55, 67), ('VC', 43, 55)], 0.1)
    for b in range(SANCTUS + 32, AGNUS - 2, 4):
        oadd('V1', b * BPB, 4 * BPB + 0.5, 93, 0.16, 'Hosanna — 高い開いた 5 度 (Vn, Fl)' if b == SANCTUS + 32 else None); oadd('V2', b * BPB + 0.05, 4 * BPB + 0.5, 86, 0.14); oadd('FL', b * BPB + 0.1, 4 * BPB + 0.5, 98, 0.1); oadd('CB', b * BPB, 4 * BPB + 0.5, 38, 0.2)
    # Agnus Dei
    chord_pad(P, AGNUS + 2, AGNUS + 18, [('VA', 50, 64), ('VC', 43, 55)], 0.14, 'Va・Vc の和音')
    for b in range(AGNUS + 2, AGNUS + 16, 4): oadd('CB', b * BPB, 4 * BPB + 0.5, 35, 0.2, None)
    add('X', AGNUS * BPB, 12, 35, 0.3, '深い鐘')
    t = (AGNUS + 19) * BPB; first = True
    for d, m in SANCTUS_T: oadd('V1', t, d, m, 0.26, 'Vn I — Dona nobis pacem' if first else None); oadd('FL', t, d, m + 12, 0.12, None); first = False; t += d
    chord_pad(P, AGNUS + 19, AGNUS + 35, [('V2', 62, 76), ('VA', 55, 67), ('VC', 43, 55), ('CB', 43, 55)], 0.16, 'Vn II・Va・Vc・Cb の和音')
    chord_pad(P, AGNUS + 35, AGNUS + 40, [('V1', 74, 86), ('V2', 62, 76), ('VA', 55, 67), ('VC', 43, 55), ('CB', 43, 55)], 0.18, 'ニ長調の和音 (弦)')
    oadd('HN', (AGNUS + 35) * BPB, 5 * BPB, 62, 0.2, 'ホルン'); oadd('FL', (AGNUS + 35) * BPB, 5 * BPB, 90, 0.12, None)
    # 共鳴 (13:19 の音): 高い開いた 5 度を Kyrie の始めと Benedictus に小さく
    first = True
    for b in list(range(KYRIE + 2, KYRIE + 14, 4)) + list(range(SANCTUS + 20, SANCTUS + 32, 4)):
        for i, m in enumerate((83, 90)): add('PF', b * BPB + 0.05 * i, 4 * BPB, m, 0.5 * (1.0 if i == 0 else 0.7), '高い開いた 5 度 (共鳴)' if first else None, rid='VOXRS', rel=1.5, layer='res'); first = False
    add('X', 0, 10, 35, 0.3, '深い鐘 (ひとつ)'); add('X', (TOTAL - 2) * BPB, 14, 35, 0.4, None)

META = dict(T.META, orchestra=True, rec_order=[R41, R27A, R42, R27, R24, R22, R03, R06, R07, R30, RS], reverb=[8.0, 3.0, 0.5],
            title='Requiem BADA — CXXXVI · Missa nel palazzetto',
            subtitle='10/13・10/12・10/03 の 11 曲 (半音上げてロ短調に) をベースに、キリスト教会のミサ曲を主題に: Kyrie (06:41・06:27・06:42、フーガ) → Gloria (13:27・13:24・13:22、フガートと Et in terra pax) → Credo (13:03・13:06・13:07、唱え・Et incarnatus est・Et resurrexit) → Sanctus (06:30・13:19、コラール・Benedictus・Hosanna) → Agnus Dei (06:41・06:42、B-A-D-A・Dona nobis pacem)。♩=56',
            legend=['PF', 'X', 'V1', 'V2', 'VA', 'VC', 'CB', 'FL', 'HN', 'TR', 'TB', 'TP'], vname={'PF': '共鳴 (13:19 の音)', 'X': '鐘', 'V1': 'Vn I', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc', 'CB': 'Cb', 'FL': 'Fl', 'HN': 'Hn', 'TR': 'Tp', 'TB': 'Tb', 'TP': 'Timp'},
            footer=['主題はすべて録音の音から: Kyrie = 06:41 (CXXV の Inno の第 1 句)、Gloria = 13:27 (CXXVII の第 2 主題)、Et in terra pax = 13:24、Credo = 13:03、Et incarnatus est = 13:06 の讃美歌、Et resurrexit = 子守歌の大黒柱、Sanctus = 06:42、Benedictus = 06:27。B-A-D-A',
                    '4 声は実音のピアノ (9/24 08:53 の音)。管弦楽は synth の合成。長い録音は始めの 55〜60 秒。鐘は始め・Agnus Dei・終わりに深いもの。声なし。'])

if __name__ == '__main__':
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; T.make_bank(bank_out); META['bank'] = bank_out
    print('credo', ' '.join('%s:%g' % (name_of(m), d) for d, m in CREDO_T[:7]), '| bened', ' '.join('%s:%g' % (name_of(m), d) for d, m in BENED_T[:7]))
    compose.main(OUT, seed=136, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
