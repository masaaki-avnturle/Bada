#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CVI · Canzone 9/23 tre in uno (CV の 3 つの層を同時に融合して、9/23 の 2 本の録音を表に — 融合した層も表に)
  表 1: 9/23 08:06 の録音 (3 分 3 秒、変ロ短調、実音、加工なし) を 2 小節目から ／ 表 2: 9/23 08:09 の録音 (3 分 37 秒、ホ短調、実音) を 50 小節目から
  同じ高さで (表として) CV = CIV の 3 つの層を、録音の実速に合わせて融合:
    ×16 の層 (骨組み) : 主題を 16 倍に伸ばして低く 2 拍ごとに息をするように — 前半 08:06 の主題 (ファ・ミ♭・ファ・ソ♭・ラ・シ♭・ド・シ♭)、後半 08:09 の主題 (ソ・ファ#・ソ・シ・ミ) と 08:06 の主題 (ホ短調に移して ×8)
    ×4 の層           : 主題 ×4 がテノールで 8 小節ごとに
    ×1 の層 (Fuga)    : 4 声のフガート → ストレッタ (前半)、4 声のフーガ (提示 → 反行) → Fusione (08:06 ×2 の低音 + 08:09 のストレッタ、後半) — 和音は録音のその時の和音に寄せて選ぶ (共鳴)
    Fiore の左手 (8 分音符の分散和音、前半) と Flower の 4 度の和音 (後半) も録音の和音で
  Amen (106〜110, ホ長調)。音源は bank85p (ピアノだけ)。110 小節 = 7 分 20 秒 + 残響
  使い方: python compose_tablet106.py <bank85p.json> <rec0806.wav> <rec0809.wav> [score_tablet106.json]
"""
import sys, os, json, math
from compose import *
import compose

BANK = sys.argv[1]; W1, W2 = os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]); OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet106.json'
B = json.load(open(BANK)); R1, R2 = '20260923_080607', '20260923_080918'; REC1, REC2 = B['recordings'][R1], B['recordings'][R2]
BPM = 60; T1, T2 = 8.0, 200.0                                                      # 録音の始まり (拍 = 秒): 2 小節目、50 小節目
SA = [(1, m) for m in (65, 63, 65, 66, 69, 70, 72, 70)]
SB = [(0.5, 67), (0.5, 66), (3, 67), (2, 71), (2, 76)]
SA_E = [(d, m + 6) for d, m in SA]
CANDS_BB = ['A#m', 'D#m', 'F', 'F7', 'C#', 'F#', 'G#', 'Cm7b5', 'D#m/F#', 'A#m/C#', 'A#m7', 'D#7', 'Fm', 'C#maj7', 'Cm7', 'D#sus4', 'A#7', 'C', 'Csus4', 'Fsus4', 'Cm']
CANDS_E = ['Em', 'Am', 'B', 'B7', 'G', 'C', 'D', 'F#m7b5', 'Am/C', 'Em/G', 'Cmaj7', 'Em7', 'Gmaj7', 'Esus4', 'A', 'Dsus4', 'A#m7', 'A#m', 'D#7']
P1, P2, AMEN, TOTAL = 0, 50, 106, 110
octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}; TOP = {'S': 86, 'A': 76, 'T': 69, 'B': 62}
extras = []; RH = []

def add(v, beat, dbeats, m, gain, label=None, **kw):
    extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
def pf(beat, dbeats, m, gain, label=None, layer='x16', rid=R1, rel=0.5): add('PF', beat, dbeats, m, gain, label, rid=rid, rel=rel, layer=layer)

def harm_fit(P, b0, b1, entries, cands):
    for bar in range(b0, b1):
        for h in range(2):
            a = bar * BPB + 2 * h; notes = []
            for e0, sb in entries:
                t = e0
                for d, m in sb:
                    ov = min(a + 2, t + d) - max(a, t)
                    if ov > 0: notes.append((ov * (2 if t <= a < t + d else 1), m))
                    t += d
            rc = set(chord(RH[a])['pcs'])
            def score(c):
                cc = set(chord(c)['pcs'])
                return sum(w * (1 if m % 12 in cc else -0.8) for w, m in notes) + 1.5 * len(cc & rc) / max(1, len(cc)) + (1.2 if c == RH[a] else 0)
            cs = max(cands, key=score)
            for q in range(2): P.harm[a + q] = cs

def fit(v, mat, tr):
    if v == 'B' and min(m for _, m in mat) + tr < 36: tr += 12
    if max(m for _, m in mat) + tr > TOP[v]: tr -= 12
    if min(m for _, m in mat) + tr < RANGE[v][0]: tr += 12
    return tr
def entry(P, bar, v, mat, tr0, label, E, beat=0):
    tr = fit(v, mat, octs[v] + tr0); P.place(v, bar, mat, tr, label or '', beat=beat); E.append((bar * BPB + beat, [(d, m + tr) for d, m in mat]))
def invert(mat): m0 = mat[0][1]; return [(d, 2 * m0 - m) for d, m in mat]
def augment(mat, k=2): return [(k * d, m) for d, m in mat]

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.95
    for q in range(TOTAL * BPB):                                                   # 和音は録音のその時の和音 (前半 08:06、後半 08:09)
        if q < P2 * BPB: rec, t0, cur = REC1, T1, 'A#m'
        else: rec, t0, cur = REC2, T2, 'Em'
        tr = q - t0
        for s in rec['segs']:
            if s['t'] <= tr: cur = s['ch']
        RH.append(cur); P.harm[q] = cur
    # ---- 前半 (変ロ短調): 08:06
    P.section(0, '表 1: 9/23 08:06 の録音 (実音) + ×16 の骨組み', '弔鐘 → 2 小節目から録音そのもの (加工なし)。同じ高さで 08:06 の主題 ×16 が低く息をする — Fiore の左手の分散和音')
    for v in VOICES: P.rest_bars(v, 0, 10)
    f = 10; lab = '主題 08:06'; E = []
    P.section(f, '×1 の層: 08:06 の主題のフガート (4 声)', '提示 (A → S → B → T) → ストレッタ — 和音は録音のその時の和音に寄せて (共鳴)')
    for k, v in enumerate('ASBT'):
        entry(P, f + 2 * k, v, SA, 7 if k % 2 else 0, lab + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, f + 2 * k, f + 2 * k + 2)
    harm_fit(P, f, f + 8, E, CANDS_BB)
    E = []; entry(P, f + 8, 'S', invert(SA), 0, lab + ' (反行)', E); entry(P, f + 10, 'T', invert(SA), 0, lab + ' (反行)', E); harm_fit(P, f + 8, f + 12, E, CANDS_BB)
    E = []
    for k, v in enumerate('ASTB'): entry(P, f + 12 + k, v, SA, 0, lab + ' ストレッタ', E)
    harm_fit(P, f + 12, f + 18, E, CANDS_BB)
    E = []; entry(P, f + 18, 'B', augment(SA), 0, lab + ' (拡大 ×2)', E); entry(P, f + 20, 'S', SA, 0, lab, E); harm_fit(P, f + 18, f + 22, E, CANDS_BB)
    for v in VOICES: P.rest_bars(v, f + 22, P2)
    # ---- 後半 (ホ短調): 08:09
    g = P2; lab2 = '主題 08:09'; E = []
    P.section(g, '表 2: 9/23 08:09 の録音 (実音) + ×16 の骨組み', '録音そのもの (加工なし)。同じ高さで 08:09 の主題 ×16 が低く息をする — Flower の 4 度の和音')
    for v in VOICES: P.rest_bars(v, g, g + 4)
    f = g + 4
    P.section(f, '×1 の層: 08:09 の主題の 4 声フーガ', '提示 (A → S → B → T) → 反行 → ストレッタ')
    for k, v in enumerate('ASBT'):
        entry(P, f + 2 * k, v, SB, 7 if k % 2 else 0, lab2 + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, f + 2 * k, f + 2 * k + 2)
    harm_fit(P, f, f + 8, E, CANDS_E)
    E = []; entry(P, f + 8, 'S', invert(SB), 0, lab2 + ' (反行)', E); entry(P, f + 10, 'T', invert(SB), 0, lab2 + ' (反行)', E); harm_fit(P, f + 8, f + 12, E, CANDS_E)
    E = []
    for k, v in enumerate('ASTB'): entry(P, f + 12 + k, v, SB, 0, lab2 + ' ストレッタ', E)
    harm_fit(P, f + 12, f + 16, E, CANDS_E)
    h = f + 16; E = []
    P.section(h, 'Fusione — 08:06 と 08:09 を同時に (ホ短調)', '08:06 の主題をホ短調に移して 2 倍に伸ばした低音の上で、08:09 の主題のストレッタ — 録音はまだ表で歌っている')
    for k in range(4): entry(P, h + 4 * k, 'B', augment(SA_E), 0, '主題 08:06 ×2 (ホ短調)' if k == 0 else None, E)
    for k in range(7):
        v = 'SAT'[k % 3]; entry(P, h + 2 * k, v, SB, 12 if (v == 'S' and k >= 3) else 0, lab2 + ' ストレッタ' if k == 0 else None, E)
    harm_fit(P, h, h + 16, E, CANDS_E)
    E = []; entry(P, h + 16, 'S', SB, 12, lab2, E); entry(P, h + 18, 'A', SA_E, 0, '主題 08:06 (ホ短調)', E); entry(P, h + 20, 'T', SB, 0, lab2, E); entry(P, h + 22, 'B', SA_E, 0, '主題 08:06 (ホ短調)', E)
    harm_fit(P, h + 16, AMEN, E, CANDS_E)
    for k in range(h, AMEN): P.dyn[k] = 1.0 + 0.2 * (k - h) / float(AMEN - h)
    P.section(AMEN, 'Amen (ホ長調)', '2 本の録音と 3 つの層が 1 つに — ホ長調の和音と鐘')
    for b in range(AMEN, TOTAL): P.set_harm(b, 'E'); P.hold.add(b); P.dyn[b] = 1.05 - 0.1 * (b - AMEN)
    P.place('S', AMEN, [(4, 88)] * 4, 0, 'ミ (頂点)'); P.place('B', AMEN, [(4, 40)] * 4, 0, '')
    return P

def post(P, events, ex):
    add('X', 0, 6, 46, 0.4, '弔鐘')
    add('REC', T1, REC1['dur'], 0, 0.8, None, src=W1, off=0.0, fin=0.02, fout=1.5, rid=R1 + '.wav', tag='9/23 08:06 — 表 (実音、加工なし)')
    add('REC', T2, REC2['dur'], 0, 0.8, None, src=W2, off=0.0, fin=0.02, fout=1.5, rid=R2 + '.wav', tag='9/23 08:09 — 表 (実音、加工なし)')
    def breathe(t, subj, k, lab, oct_, rid, g=0.2):
        first = True
        for d, m in augment(subj, k):
            n_ = max(1, int(round(d / 2)))
            for i in range(n_):
                amp = 1.0 if i == 0 else 0.6 + 0.25 * math.sin(math.pi * i / max(1, n_ - 1))
                pf(t + 2 * i, 2.0, m + oct_, g * amp, lab if (first and i == 0) else None, 'x16', rid=rid, rel=0.7)
                pf(t + 2 * i, 2.0, m + oct_ + 12, g * 0.45 * amp, None, 'x16', rid=rid, rel=0.7)
            first = False; t += d
    # ×16 の層
    breathe(2 * BPB, SA, 16, '主題 08:06 ×16 (骨組み、低く)', -24, R1)                       # 2〜34 小節
    breathe(34 * BPB, SA, 8, '主題 08:06 ×8', -24, R1)                                        # 34〜50
    breathe(P2 * BPB, SB, 16, '主題 08:09 ×16 (骨組み、低く)', -24, R2)                      # 50〜82
    breathe(82 * BPB, SA_E, 8, '主題 08:06 ×8 (ホ短調)', -24, R1)                             # 82〜98
    breathe(98 * BPB, SB, 4, '主題 08:09 ×4', -12, R2)                                        # 98〜106
    # ×4 の層: 主題 ×4 がテノールで 8 小節ごと
    for b0, subj, rid, lab in ((2, SA, R1, '主題 08:06 ×4'), (18, SA, R1, None), (34, SA, R1, None), (P2, SB, R2, '主題 08:09 ×4'), (66, SB, R2, None), (82, SB, R2, None), (90, SA_E, R1, '主題 08:06 ×4 (ホ短調)')):
        t = b0 * BPB; first = True
        for d, m in augment(subj, 4):
            pf(t, d + 0.2, m - 12, 0.14, lab if first else None, 'x4', rid=rid, rel=0.6); t += d; first = False
    # Fiore の左手 (前半) / Flower の 4 度の和音 (後半)
    for bar in range(2, P2):
        for half in (0, 2):
            c = chord(P.harm[bar * BPB + half]); pcs = sorted(c['pcs']); voi = sorted(52 + (p - 52) % 12 for p in pcs)[:4]
            pat = [voi[0], voi[1], voi[-1], voi[1]] if len(voi) >= 2 else voi * 4
            for i, m in enumerate(pat): pf(bar * BPB + half + 0.5 * i, 0.7, m, 0.11 * (1.0 if i % 2 == 0 else 0.8), '左手 — 分散和音 (Fiore)' if (bar == 2 and half == 0 and i == 0) else None, 'acc', rid=R1, rel=0.5)
    for bar in range(P2, AMEN):
        c = chord(P.harm[bar * BPB]); tones = sorted({55 + (p - 55) % 12 for p in c['pcs']})[:3]
        for k, m in enumerate(tones): pf(bar * BPB + 0.08 * k, 2.4, m + 12, 0.09, 'Flower の 4 度の和音' if (bar == P2 and k == 0) else None, 'flower', rid=R2, rel=0.6); pf(bar * BPB + 2.5 + 0.06 * k, 1.5, m + 12, 0.06, None, 'flower', rid=R2, rel=0.6)
    add('X', P2 * BPB, 6, 52, 0.35, '弔鐘')
    for k, bar in enumerate(range(AMEN, TOTAL)): add('X', bar * BPB, 8, 64 + 12 * (k % 2), 0.35 - 0.06 * k, '祝鐘' if k == 0 else None)

META = {'style': 'recsampler', 'bank': BANK, 'rec_order': [R1, R2], 'piano_decay': 2.0, 'reverb': [5.0, 2.0, 0.42],
        'title': 'Requiem BADA — CVI · Canzone 9/23 tre in uno', 'subtitle': '表: 9/23 08:06 → 08:09 の録音そのもの、同じ高さで CV (CIV の 3 つの層) を融合 — ×16 の骨組み・×4・×1 のフーガ、和音を録音にそろえて共鳴 (変ロ短調 → ホ短調 → ホ長調, ♩=60, 7 分 27 秒)',
        'legend': ['PF', 'X'], 'vname': {'PF': '×16・×4 の層 / 左手', 'X': '鐘'},
        'footer': ['表 1: 08:06 (2 小節目から 3 分 3 秒) + 主題 ×16・×4、フガート (×1)、Fiore の左手 → 表 2: 08:09 (50 小節目から 3 分 37 秒) + 主題 ×16・×4、フーガ (×1)、Fusione、Flower の和音 → Amen (ホ長調)',
                   '音源は bank85p (9/28 の歌の音を除いたピアノだけ)。録音は加工しない。声なし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=106, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT)); from collections import Counter
    print('bars', d['nbars'], 'duration', d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
