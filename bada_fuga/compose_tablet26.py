#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XXVI · Contrapunctus (Contrapunctus XIV のように — 分散和音なし、駆け足の主題なし)
  XXV から分散和音の波を消し、バッハ『フーガの技法』の Contrapunctus XIV (未完の三重フーガ) の形で作り換えたレクイエム。
  Contrapunctus XIV は 3 つの主題を順に提示して最後に重ねる: 第 1 主題 (荘重)、第 2 主題 (駆け足の 8 分音符)、第 3 主題 B-A-C-H、
  そして 239 小節目で楽譜が途切れる。ここでは:
    Sectio I  — 第 1 主題 = 9/24 08:53 の主題 (荘重、全音符と二分音符): 4 声の提示 → 反行形 → 低音の拡大形 (2 倍の長さ)
    Sectio II — 第 2 主題 = 9/23 08:06 の主題 (駆け足ではなく、ゆっくり): 4 声の提示 → 第 1 主題との二重フーガ
    Sectio III — 第 3 主題 = B-A-D-A (バッハの B-A-C-H の代わりに、このシリーズの印): 4 声の提示 → 3 つの主題を同時に重ねる三重フーガ
                 → 2 度目の重なりの途中、小節の 2 拍目で楽譜が途切れる (Contrapunctus XIV のように) → 鼓動だけが残って消える
  音はすべて 2026-09-23 / 09-24 の録音から切り出したピアノの 1 音 (実音、自然に減衰)。各 Sectio の頭に XXV の 12 音の塊がひとつ (弔鐘)。
  ニ短調 (『フーガの技法』と同じ調)、♩=56、鼓動は最後まで。
  使い方: python compose_tablet26.py <bank.json> [score_tablet26.json]
"""
import sys, json
from compose import *
import compose
import compose_heart as H
import compose_tablet as CT
import compose_tablet2 as T2
import compose_tablet3 as T3
import compose_tablet5 as T5
import compose_tablet7 as T7
import compose_tablet11 as T11

add, REC, hm = CT.add, CT.REC, T3.hm
BPM = 56
KEYS = {'20260923_080607': -4, '20260923_080918': 2, '20260924_084937': 3, '20260924_085314': 2, '20260924_111846': -4, '20260924_112131': 3, '20260924_112313': 2}
T7.KEYS.update(KEYS)
E1, E2, E3, B1, B2, RF, SY = '20260924_112313', '20260924_085314', '20260923_080918', '20260923_080607', '20260924_111846', '20260924_084937', '20260924_112131'
ORDER = [E1, E2, E3, B1, B2, RF, SY]
T7.MARK.update(dict(zip(ORDER, '①②③④⑤⑥⑦')))
VOICE_SRC = {'S': E1, 'A': E2, 'T': RF, 'B': B1}
S1, S2 = E2, B1                       # 第 1 主題 (08:53)、第 2 主題 (08:06)
CLUSTERS = []; CUT = None; TAIL = ()
octs, TOP = T7.octs, T7.TOP

def fit(v, mat, tr):
    if v == 'B' and min(m for _, m in mat) + tr < 36: tr += 12
    if max(m for _, m in mat) + tr > TOP[v]: tr -= 12
    return tr

def entry(P, bar, v, mat, tr0, label, entries, beat=0):
    tr = fit(v, mat, octs[v] + tr0)
    P.place(v, bar, mat, tr, label, beat=beat); entries.append((bar * BPB + beat, [(d, m + tr) for d, m in mat]))

def invert(mat):
    m0 = mat[0][1]; return [(d, 2 * m0 - m) for d, m in mat]

def augment(mat):
    return [(2 * d, m) for d, m in mat]

def cluster(beat, gain=0.14, rid=None):
    CLUSTERS.append((beat, gain, rid))

def post(P, events, extras):
    for beat, gain, rid in CLUSTERS:                                     # 12 音の塊 (弔鐘)
        root = chord(P.harm[int(beat)])['root']; base = 26 + (root - 2) % 12
        for j, x in enumerate((0, 1, 6, 7, 11, 13, 16, 18, 22, 25, 30, 31)):
            add('PF', beat + 0.006 * j, 3.0, base + x + (12 if j >= 8 else 0), gain * (1.0 if j < 3 else 0.8), None, rid=rid or VOICE_SRC['B'], rel=2.5)
    if CUT is not None:                                                  # 楽譜が途切れる: 2 拍目以降の音を切る
        for v in VOICES:
            events[v] = [(s, min(d, CUT - s), m, lab) for s, d, m, lab in events[v] if s < CUT]
    for b0, b1, rid, kinds in T2.MANTRA:
        for bar in range(b0, b1):
            g = 1.0 if bar < TAIL[0] else max(0.0, 1.0 - (bar - TAIL[0] + 1) / float(TAIL[1]))
            for k in range(BPB): add('PK', bar * BPB + k, 0.5, 26, (0.11 if k == 0 else 0.06) * g, None, rid=rid)

def build():
    global CUT, TAIL
    for r in ORDER:
        t0, inside = CT.excerpt(r, KEYS[r], 13.0)
        subj = CT.make_subject(inside, KEYS[r], 56); T5.SUBJ[r] = (subj, CT.harmonize(subj))
    s1, s2, s3 = T5.SUBJ[S1][0], T5.SUBJ[S2][0], list(H.BADA)
    L1, L2, L3 = '主題 ②', '主題 ④', 'B-A-D-A'
    total = 18 + 16 + 24
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 1.2
    b = 0
    # ---------------- Sectio I — 第 1 主題
    f = b; E = []
    P.section(b, 'Sectio I — Soggetto I 〈%s〉' % hm(S1), '第 1 主題の 4 声の提示 (オクターヴごとに) → エピソード → 反行形 → 低音の拡大形 (2 倍の長さ) — 分散和音はなく、対位法だけ')
    cluster(f * BPB, 0.14, S1)
    for k, v in enumerate('ASTB'): entry(P, f + 2 * k, v, s1, 0, L1, E)
    for v, z in {'S': 2, 'T': 4, 'B': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 8, E)
    P.set_harms(f + 8, [['Gm', 'Gm', 'C7', 'C7'], ['F', 'F', 'A7', 'A7']])                     # エピソード
    E = []
    entry(P, f + 10, 'S', invert(s1), 0, L1 + ' (反行)', E); entry(P, f + 12, 'T', invert(s1), 0, L1 + ' (反行)', E)
    T5.harm_from_entries(P, f + 10, f + 14, E)
    E = []; entry(P, f + 14, 'B', augment(s1), 0, L1 + ' (拡大)', E)
    T5.harm_from_entries(P, f + 14, f + 18, E)
    P.hold.update({f + 16, f + 17})
    T2.MANTRA.append((f, f + 18, S1, ('PK',))); CT.LAYOUT.append((f, f + 18, 0, VOICE_SRC, {})); b = f + 18
    # ---------------- Sectio II — 第 2 主題 (ゆっくり)
    f = b; E = []
    P.section(b, 'Sectio II — Soggetto II 〈%s〉' % hm(S2), '第 2 主題 (Contrapunctus XIV の駆け足の主題の代わりに、9/23 の主題をゆっくり) の 4 声の提示 → 第 1 主題と重なる二重フーガ')
    cluster(f * BPB, 0.12, S2)
    for k, v in enumerate('TABS'): entry(P, f + 2 * k, v, s2, 0, L2, E)
    for v, z in {'A': 2, 'B': 4, 'S': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 8, E)
    E = []
    entry(P, f + 8, 'S', s1, 0, L1, E); entry(P, f + 8, 'T', s2, 0, L2, E)                     # 二重: I + II
    entry(P, f + 11, 'A', s2, 0, L2, E); entry(P, f + 11, 'B', s1, 0, L1, E)
    T5.harm_from_entries(P, f + 8, f + 14, E)
    P.set_harms(f + 14, [['Gm', 'Gm', 'A7', 'A7'], ['Dm', 'Dm', 'A7', 'A7']]); P.hold.update({f + 14, f + 15})
    T2.MANTRA.append((f, f + 16, S2, ('PK',))); CT.LAYOUT.append((f, f + 16, 0, VOICE_SRC, {})); b = f + 16
    # ---------------- Sectio III — B-A-D-A → 三重フーガ → 途切れる
    f = b; E = []
    P.section(b, 'Sectio III — B-A-D-A · Fuga a tre soggetti', 'バッハの B-A-C-H の代わりに B-A-D-A を 4 声で提示 → 3 つの主題を同時に重ねる三重フーガ → 2 度目の重なりの途中で楽譜が途切れ、鼓動だけが残る')
    cluster(f * BPB, 0.14, RF)
    for k, (v, tr0) in enumerate((('B', 0), ('T', 0), ('A', 0), ('S', 0))): entry(P, f + 2 * k, v, s3, tr0, L3, E)
    for v, z in {'T': 2, 'A': 4, 'S': 6}.items(): P.rest_bars(v, f, f + z)
    T5.harm_from_entries(P, f, f + 8, E)
    E = []                                                                                    # 三重 1 回目: I (S) + II (T) + B-A-D-A (A)
    entry(P, f + 8, 'S', s1, 0, L1, E); entry(P, f + 8, 'T', s2, 0, L2, E); entry(P, f + 8, 'A', s3, 0, L3, E)
    T5.harm_from_entries(P, f + 8, f + 12, E)
    P.set_harms(f + 11, [['A7', 'A7', 'Dm', 'Dm']])
    E = []                                                                                    # 三重 2 回目: I (B, 拡大) + II (S) + B-A-D-A (T)
    entry(P, f + 12, 'B', augment(s1), 0, L1 + ' (拡大)', E); entry(P, f + 12, 'S', s2, 0, L2, E); entry(P, f + 12, 'T', s3, 0, L3, E)
    entry(P, f + 14, 'A', s3, 0, L3, E)
    T5.harm_from_entries(P, f + 12, f + 16, E)
    CUT = (f + 15) * BPB + 1                                                                  # 楽譜が途切れる: 16 小節目の 2 拍目
    for v in VOICES: P.rest_bars(v, f + 16, f + 24)
    for k in range(f + 16, f + 24): P.harm[k * BPB:(k + 1) * BPB] = ['Dm'] * BPB
    TAIL = (f + 16, 8)
    for k in range(6): P.dyn[f + 8 + k] = 1.3
    T2.MANTRA.append((f, f + 24, RF, ('PK',))); CT.LAYOUT.append((f, f + 24, 0, VOICE_SRC, {})); b = f + 24
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.5,
    'title': 'Requiem BADA — Tablet Sessions XXVI · Contrapunctus',
    'subtitle': 'Contrapunctus XIV のように — 3 つの主題 (08:53、08:06、B-A-D-A) の三重フーガが途中で途切れる。分散和音なし、駆け足の主題なし。実録音のピアノ一色 (♩=56, ニ短調)',
    'legend': ['TB', 'PK'], 'vname': {'PK': '鼓動 (ピアノの低い打鍵)'},
    'footer': ['Sectio I: 主題 I の提示 → 反行 → 拡大  |  Sectio II: 主題 II の提示 → I+II の二重フーガ  |  Sectio III: B-A-D-A の提示 → I+II+B-A-D-A の三重フーガ → 途切れる → 鼓動だけ',
               '『フーガの技法』の未完の Contrapunctus XIV にならい、B-A-C-H の代わりに B-A-D-A。音はすべて 9/23・9/24 の録音から切り出したピアノ。各 Sectio の頭に 12 音の塊 (弔鐘)。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet26.json'
    compose.main(out, seed=107, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
