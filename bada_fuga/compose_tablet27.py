#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XXVII · Contrapunctus turbato (XXVI の三重フーガを「乱れる」フーガに、9/23・9/24 の実音をミックス)
  XXVI (Contrapunctus XIV の形) をもとに:
    - フーガの入りを乱す (turbato): 主題が小節の頭ではなく拍の途中で、不揃いな間隔 (1.5 小節、3 拍、半小節、1 拍) で崩れ込むように入り、
      原形・反行形・拡大形 (2 倍)・縮小形 (半分) が同じ小節の中で同時に走る。B-A-D-A は 2 拍ごとの密なストレッタ。
    - 9/23・9/24 の実音の抜粋 (8 秒のクロスフェード) を各 Sectio の前にミックス: Introitus 11:23 → 08:53 (ホ短調)、
      Interludium I 9/23 08:06 → 11:18 (変ロ短調)、Interludium II 08:49 → 11:21 (ヘ短調)。フーガはその抜粋の調で歌う。
  以下は XXVI の説明:
  XXV から分散和音の波を消し、バッハ『フーガの技法』の Contrapunctus XIV (未完の三重フーガ) の形で作り換えたレクイエム。
  Contrapunctus XIV は 3 つの主題を順に提示して最後に重ねる: 第 1 主題 (荘重)、第 2 主題 (駆け足の 8 分音符)、第 3 主題 B-A-C-H、
  そして 239 小節目で楽譜が途切れる。ここでは:
    Sectio I  — 第 1 主題 = 9/24 08:53 の主題 (荘重、全音符と二分音符): 4 声の提示 → 反行形 → 低音の拡大形 (2 倍の長さ)
    Sectio II — 第 2 主題 = 9/23 08:06 の主題 (駆け足ではなく、ゆっくり): 4 声の提示 → 第 1 主題との二重フーガ
    Sectio III — 第 3 主題 = B-A-D-A (バッハの B-A-C-H の代わりに、このシリーズの印): 4 声の提示 → 3 つの主題を同時に重ねる三重フーガ
                 → 2 度目の重なりの途中、小節の 2 拍目で楽譜が途切れる (Contrapunctus XIV のように) → 鼓動だけが残って消える
  音はすべて 2026-09-23 / 09-24 の録音から切り出したピアノの 1 音 (実音、自然に減衰)。各 Sectio の頭に XXV の 12 音の塊がひとつ (弔鐘)。
  ニ短調 (『フーガの技法』と同じ調)、♩=56、鼓動は最後まで。
  使い方: python compose_tablet27.py <bank.json> [score_tablet27.json]
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
BPM = 56; BAR_S = 240.0 / BPM; XF = 2
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

def diminish(mat):
    return [(d / 2.0, m) for d, m in mat]

def rest_until(P, v, b0, bar, beat):
    """b0 小節から、bar 小節 beat 拍の入りまで休む"""
    P.rest_bars(v, b0, bar)
    if beat: P.rest_bars(v, bar, bar + 1, beats=range(int(beat)))

def chain(P, b, rids, semis, bars=8):
    """実音の抜粋をクロスフェードでつなぐ (XXII と同じ)"""
    st = b
    for i, r in enumerate(rids):
        T5.passage(P, r, st, bars, semis, bars, fin=(1.5 if i == 0 else XF * BAR_S), fout=(XF * BAR_S if i < len(rids) - 1 else 3.0), bpm=BPM, gmul=0.65)
        CT.LAYOUT.append((st + (XF if i else 0), st + bars, semis, {v: r for v in VOICES}, {}))
        st += bars - XF
    end = st + XF
    for v in VOICES: P.rest_bars(v, b, end)
    T2.MANTRA.append((b, end, rids[0], ('PK',)))
    return end - b

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
    total = 14 + 18 + 14 + 16 + 14 + 24
    P = Piece(total)
    for k in range(total): P.tempo[k] = BPM; P.dyn[k] = 1.2
    b = 0
    # ---------------- Introitus — 実音 11:23 → 08:53 (ホ短調)
    P.section(b, 'Introitus — 〈%s → %s〉 (ホ短調)' % (hm(E1), hm(E2)), '9/24 の実音の抜粋を 8 秒のクロスフェードでつなぐ — ♩=56 の鼓動が最後まで止まらない')
    b += chain(P, b, [E1, E2], 2)
    # ---------------- Sectio I — 第 1 主題 (乱れる) ホ短調
    f = b; E = []
    P.section(b, 'Sectio I — Soggetto I turbato 〈%s〉 (ホ短調)' % hm(S1), '第 1 主題が拍の途中で不揃いに崩れ込む (A → 1.5 小節後に S → 3 拍後に T → 半小節後に B) → 原形・反行・縮小・拡大が同じ小節で同時に走る')
    cluster(f * BPB, 0.14, S1)
    for v, bar, beat in (('A', 0, 0), ('S', 1, 2), ('T', 2, 1), ('B', 2, 3)):
        entry(P, f + bar, v, s1, 0, L1, E, beat=beat); rest_until(P, v, f, f + bar, beat)
    T5.harm_from_entries(P, f, f + 6, E)
    P.set_harms(f + 6, [['Gm', 'Gm', 'C7', 'C7'], ['F', 'F', 'A7', 'A7']])                      # エピソード
    E = []                                                                                    # 乱流: 反行 (S) / 縮小 (A) / 原形 (T, 1 拍遅れ) / 拡大 (B)
    entry(P, f + 8, 'S', invert(s1), 0, L1 + ' (反行)', E); entry(P, f + 8, 'A', diminish(s1), 0, L1 + ' (縮小)', E, beat=2)
    entry(P, f + 8, 'T', s1, 0, L1, E, beat=1); entry(P, f + 8, 'B', augment(s1), 0, L1 + ' (拡大)', E)
    entry(P, f + 10, 'A', diminish(s1), 0, L1 + ' (縮小)', E, beat=1); entry(P, f + 11, 'S', s1, 0, L1, E, beat=3)
    T5.harm_from_entries(P, f, f + 14, E)
    P.set_harms(f + 14, [['Gm', 'Gm', 'A7', 'A7'], ['Dm', 'Dm', 'A7', 'A7'], ['Dm', 'Dm', 'Gm', 'Gm'], ['A7', 'A7', 'Dm', 'Dm']])
    P.hold.update({f + 16, f + 17})
    for k in range(8, 14): P.dyn[f + k] = 1.3
    T2.MANTRA.append((f, f + 18, S1, ('PK',))); CT.LAYOUT.append((f, f + 18, 2, VOICE_SRC, {})); b = f + 18
    # ---------------- Interludium I — 実音 9/23 08:06 → 9/24 11:18 (変ロ短調)
    P.section(b, 'Interludium I — 〈%s → %s〉 (変ロ短調)' % (hm(B1), hm(B2)), '9/23 と 9/24 の実音をミックス')
    b += chain(P, b, [B1, B2], -4)
    # ---------------- Sectio II — 第 2 主題 (乱れる) 変ロ短調
    f = b; E = []
    P.section(b, 'Sectio II — Soggetto II turbato 〈%s〉 (変ロ短調)' % hm(S2), '第 2 主題 (ゆっくり) が不揃いに入る → 第 1 主題と拍をずらして重なる二重フーガ (縮小形が上で乱す)')
    cluster(f * BPB, 0.12, S2)
    for v, bar, beat in (('T', 0, 0), ('A', 0, 3), ('B', 1, 2), ('S', 2, 2)):
        entry(P, f + bar, v, s2, 0, L2, E, beat=beat); rest_until(P, v, f, f + bar, beat)
    T5.harm_from_entries(P, f, f + 6, E)
    P.set_harms(f + 6, [['Gm', 'Gm', 'C7', 'C7'], ['F', 'F', 'A7', 'A7']])
    E = []
    entry(P, f + 8, 'S', s1, 0, L1, E, beat=1); entry(P, f + 8, 'T', s2, 0, L2, E)                # 二重: I (1 拍遅れ) + II
    entry(P, f + 9, 'A', diminish(s2), 0, L2 + ' (縮小)', E, beat=2)
    entry(P, f + 10, 'A', s2, 0, L2, E, beat=3); entry(P, f + 11, 'B', s1, 0, L1, E, beat=1)
    entry(P, f + 12, 'S', diminish(s1), 0, L1 + ' (縮小)', E, beat=2)
    T5.harm_from_entries(P, f + 8, f + 14, E)
    P.set_harms(f + 14, [['Gm', 'Gm', 'A7', 'A7'], ['Dm', 'Dm', 'A7', 'A7']]); P.hold.update({f + 14, f + 15})
    for k in range(8, 14): P.dyn[f + k] = 1.3
    T2.MANTRA.append((f, f + 16, S2, ('PK',))); CT.LAYOUT.append((f, f + 16, -4, VOICE_SRC, {})); b = f + 16
    # ---------------- Interludium II — 実音 08:49 → 11:21 (ヘ短調)
    P.section(b, 'Interludium II — 〈%s → %s〉 (ヘ短調)' % (hm(RF), hm(SY)), '9/24 の 08:49 と、シンセの重なった 11:21 の実音')
    b += chain(P, b, [RF, SY], 3)
    # ---------------- Sectio III — B-A-D-A → 三重フーガ (乱れる) → 途切れる ヘ短調
    f = b; E = []
    P.section(b, 'Sectio III — B-A-D-A · Fuga a tre soggetti turbata (ヘ短調)', 'B-A-D-A が 2 拍ごとに崩れ込む密なストレッタ → 3 つの主題が拍をずらして同時に重なる三重フーガ → 2 度目の重なりの途中で楽譜が途切れ、鼓動だけが残る')
    cluster(f * BPB, 0.14, RF)
    for k, v in enumerate('BTAS'):
        entry(P, f + (2 * k) // BPB, v, s3, 0, L3, E, beat=(2 * k) % BPB); rest_until(P, v, f, f + (2 * k) // BPB, (2 * k) % BPB)
    for k, v in enumerate('BTAS'):
        entry(P, f + 4 + (2 * k) // BPB, v, s3, 0, None, E, beat=(2 * k) % BPB)
    T5.harm_from_entries(P, f, f + 8, E)
    E = []                                                                                    # 三重 1 回目: I (S, 1 拍遅れ) + II (T) + B-A-D-A (A, 2 拍遅れ)
    entry(P, f + 8, 'S', s1, 0, L1, E, beat=1); entry(P, f + 8, 'T', s2, 0, L2, E); entry(P, f + 8, 'A', s3, 0, L3, E, beat=2)
    entry(P, f + 10, 'B', diminish(s1), 0, L1 + ' (縮小)', E, beat=2)
    T5.harm_from_entries(P, f + 8, f + 12, E)
    P.set_harms(f + 11, [['A7', 'A7', 'Dm', 'Dm']])
    E = []                                                                                    # 三重 2 回目: I (B, 拡大) + II (S, 3 拍遅れ) + B-A-D-A (T) + B-A-D-A (A, 縮小)
    entry(P, f + 12, 'B', augment(s1), 0, L1 + ' (拡大)', E); entry(P, f + 12, 'S', s2, 0, L2, E, beat=3); entry(P, f + 12, 'T', s3, 0, L3, E)
    entry(P, f + 13, 'A', diminish(s3), 0, L3 + ' (縮小)', E, beat=1); entry(P, f + 14, 'A', s3, 0, L3, E, beat=2)
    T5.harm_from_entries(P, f + 12, f + 16, E)
    CUT = (f + 15) * BPB + 1                                                                  # 楽譜が途切れる: 16 小節目の 2 拍目
    for v in VOICES: P.rest_bars(v, f + 16, f + 24)
    for k in range(f + 16, f + 24): P.harm[k * BPB:(k + 1) * BPB] = ['Dm'] * BPB
    TAIL = (f + 16, 8)
    for k in range(8, 16): P.dyn[f + k] = 1.3
    T2.MANTRA.append((f, f + 24, RF, ('PK',))); CT.LAYOUT.append((f, f + 24, 3, VOICE_SRC, {})); b = f + 24
    assert b == total, (b, total)
    return P

META = {
    'style': 'recsampler', 'bank': sys.argv[1], 'rec_order': ORDER, 'piano_decay': 1.5,
    'title': 'Requiem BADA — Tablet Sessions XXVII · Turbato',
    'subtitle': 'XXVI の三重フーガを乱れる入りで — 9/23・9/24 の実音の抜粋をミックス、途中で楽譜が途切れる。実録音のピアノ一色 (♩=56)',
    'legend': ['TB', 'PK'], 'vname': {'PK': '鼓動'},
    'footer': ['Introitus 11:23→08:53 → Sectio I (主題 I) → Interludium 08:06→11:18 → Sectio II (II + I) → Interludium 08:49→11:21 → Sectio III (B-A-D-A · 三重 → 途切れる)',
               '乱れ: 拍の途中の不揃いな入り、原形・反行・縮小・拡大の同時進行、2 拍ごとのストレッタ。Contrapunctus XIV にならい B-A-C-H の代わりに B-A-D-A。'],
}

if __name__ == '__main__':
    out = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet27.json'
    compose.main(out, seed=107, bpm=BPM, builder=build, meta=META, extras=CT.extras, post=post)
    CT.finish(out)
    d = json.load(open(out)); from collections import Counter
    print('extras:', Counter(e['v'] for e in d['extras']), 'notes', len(d['notes']))
