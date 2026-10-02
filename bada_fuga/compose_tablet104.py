#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CIV · Fiore e Fuga 9/23 (9/23 の 2 本 — 08:06・08:09 — を主題曲に、LXXXVI (Fiore dolce) と LXXXIX (Requiem e Fuga) の作りで融合)
  声を消す: 9/23 の録音の実音は使わず、採譜 (bank85) とピアノだけの音源 (bank85p、9/28 の歌の音を除いたもの) で
  主題: 08:06 (変ロ短調) ← 採譜の最上声から ファ・ミ♭・ファ・ソ♭・ラ・シ♭・ド・シ♭ (8 拍) ／ 08:09 (ホ短調) ← ソ・ファ#・ソ・シ・ミ (8 拍)
  形式 (76 小節 = 5 分 4 秒 + 残響、♩=60):
    I.  Fiore dolce 08:06 (0〜24, 変ロ短調)   LXXXVI の歌う形: 08:06 の採譜の旋律 (最上声) を実速で、左手は根音と 8 分音符で揺れる分散和音 (Sweet Revenge の手つき)、和音は採譜のまま
    II. Requiem 08:06 (24〜40)                LXXXIX の形: 主題を 4 倍に伸ばして 2 拍ごとに息をするように打ち直し (2 回)、和音のコラール — 弔鐘
    III. Fuga 08:09 (40〜56, ホ短調)           主題の 4 声フーガ: 提示 → 反行 → ストレッタ
    IV. Fusione (56〜72, ホ短調)              融合: 08:06 の主題をホ短調に移して (シ・ラ・シ・ド・レ#・ミ・ファ#・ミ) 2 倍に伸ばした低音、その上で 08:09 の主題のストレッタ (4 声)、Flower の 4 度の和音
    V.  Amen (72〜76, ホ長調)                 ホ長調の和音と鐘
  使い方: python compose_tablet104.py <bank85p.json> [score_tablet104.json]
"""
import sys, json, math
from compose import *
import compose

BANK = sys.argv[1]; OUT = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet104.json'
B = json.load(open(BANK)); R1, R2 = '20260923_080607', '20260923_080918'; REC1 = B['recordings'][R1]
BPM = 60
SA = [(1, m) for m in (65, 63, 65, 66, 69, 70, 72, 70)]                           # 08:06: ファ・ミ♭・ファ・ソ♭・ラ・シ♭・ド・シ♭
SB = [(0.5, 67), (0.5, 66), (3, 67), (2, 71), (2, 76)]                            # 08:09: ソ・ファ#・ソ・シ・ミ
SA_E = [(d, m + 6) for d, m in SA]                                                 # 08:06 をホ短調に (+6): シ・ラ・シ・ド・レ#・ミ・ファ#・ミ
CANDS_BB = ['A#m', 'D#m', 'F', 'F7', 'C#', 'F#', 'G#', 'Cm7b5', 'D#m/F#', 'A#m/C#', 'A#m7', 'D#7', 'Fm', 'C#maj7', 'Cm7', 'D#sus4', 'A#7', 'C', 'Csus4']
CANDS_E = ['Em', 'Am', 'B', 'B7', 'G', 'C', 'D', 'F#m7b5', 'Am/C', 'Em/G', 'Cmaj7', 'Em7', 'Gmaj7', 'Esus4', 'A']
T_I0 = 3.5; I0, II0, III0, IV0, V0, TOTAL = 0, 24, 40, 56, 72, 76
octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}; TOP = {'S': 86, 'A': 76, 'T': 69, 'B': 62}
extras = []

def add(v, beat, dbeats, m, gain, label=None, **kw):
    extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
def pf(beat, dbeats, m, gain, label=None, layer='pf', rid=R1, rel=0.5): add('PF', beat, dbeats, m, gain, label, rid=rid, rel=rel, layer=layer)

def harm_from_entries(P, b0, b1, entries, cands):
    for bar in range(b0, b1):
        for h in range(2):
            a = bar * BPB + 2 * h; notes = []
            for e0, sb in entries:
                t = e0
                for d, m in sb:
                    ov = min(a + 2, t + d) - max(a, t)
                    if ov > 0: notes.append((ov * (2 if t <= a < t + d else 1), m))
                    t += d
            cs = max(cands, key=lambda c: sum(w * (1 if m % 12 in chord(c)['pcs'] else -0.8) for w, m in notes)) if notes else cands[0]
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
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.8
    # I. 和音は 08:06 の採譜のまま (実速、3.5 秒から)
    cur = 'A#m'
    for q in range(II0 * BPB):
        tr = q + T_I0
        for s in REC1['segs']:
            if s['t'] <= tr: cur = s['ch']
        P.harm[q] = cur
    for v in VOICES: P.rest_bars(v, 0, III0)
    P.section(0, 'I. Fiore dolce 08:06 (変ロ短調)', 'LXXXVI の歌う形 — 08:06 の採譜の旋律を実速で、左手は根音と 8 分音符で揺れる分散和音。実音は使わず (声を消して)、ピアノの 1 音だけ')
    # II. Requiem 08:06: 主題 ×4 ×2 回、和音は主題から
    P.section(II0, 'II. Requiem 08:06 — 主題 ×4', 'LXXXIX の形 — 弔鐘 → 主題 ファ・ミ♭・ファ・ソ♭・ラ・シ♭・ド・シ♭ を 4 倍に伸ばして 2 拍ごとに息をするように (2 回)、和音のコラール')
    E = [(II0 * BPB, augment(SA, 4)), ((II0 + 8) * BPB, [(d, m - 12) for d, m in augment(SA, 4)])]
    harm_from_entries(P, II0, III0, E, CANDS_BB)
    # III. Fuga 08:09 (ホ短調)
    f = III0; lab = '主題 08:09'; E = []
    P.section(f, 'III. Fuga 08:09 (ホ短調)', '主題 ソ・ファ#・ソ・シ・ミ の 4 声フーガ: 提示 (A → S → B → T) → 反行 → ストレッタ')
    for k, v in enumerate('ASBT'):
        entry(P, f + 2 * k, v, SB, 7 if k % 2 else 0, lab + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, f + 2 * k, f + 2 * k + 2)
    harm_from_entries(P, f, f + 8, E, CANDS_E)
    E = []; entry(P, f + 8, 'S', invert(SB), 0, lab + ' (反行)', E); entry(P, f + 10, 'T', invert(SB), 0, lab + ' (反行)', E); harm_from_entries(P, f + 8, f + 12, E, CANDS_E)
    E = []
    for k, v in enumerate('ASTB'): entry(P, f + 12 + k, v, SB, 0, lab + ' ストレッタ', E)
    harm_from_entries(P, f + 12, f + 16, E, CANDS_E)
    for k in range(16): P.dyn[f + k] = 0.85 + 0.2 * k / 16.0
    # IV. Fusione: 08:06 ×2 (ホ短調) が低音、08:09 のストレッタが上で
    g = IV0; E = []
    P.section(g, 'IV. Fusione — 08:06 と 08:09 を同時に (ホ短調)', '08:06 の主題をホ短調に移して 2 倍に伸ばした低音 (シ・ラ・シ・ド・レ#・ミ・ファ#・ミ) の上で、08:09 の主題のストレッタ — Flower の 4 度の和音が揺れる')
    for k in range(4): entry(P, g + 4 * k, 'B', augment(SA_E), 0, '主題 08:06 ×2 (ホ短調)' if k == 0 else None, E)
    for k in range(7):
        v = 'SAT'[k % 3]; entry(P, g + 2 * k, v, SB, 12 if (v == 'S' and k >= 3) else 0, '主題 08:09 ストレッタ' if k == 0 else None, E)
    harm_from_entries(P, g, V0, E, CANDS_E)
    for k in range(16): P.dyn[g + k] = 1.0 + 0.25 * k / 16.0
    # V. Amen
    P.section(V0, 'V. Amen (ホ長調)', 'ホ長調の和音と鐘 — 2 本の録音が 1 つに')
    for b in range(V0, TOTAL): P.set_harm(b, 'E'); P.hold.add(b)
    P.place('S', V0, [(4, 88), (4, 88), (4, 88), (4, 88)], 0, 'ミ (頂点)'); P.place('B', V0, [(4, 40)] * 4, 0, '')
    for k in range(V0, TOTAL): P.dyn[k] = 1.0 - 0.1 * (k - V0)
    return P

def post(P, events, ex):
    # I. 旋律 (採譜の最上声) + 左手 (根音 + 8 分音符の分散和音)
    first = True
    for s in REC1['segs']:
        b = s['t'] - T_I0
        if b < 0 or b >= II0 * BPB: continue
        pf(b, max(0.5, s['d']), s['m'][-1], 0.34, '08:06 の旋律 (採譜、実速)' if first else None, 'mel', rid=R1, rel=0.6); first = False
    for bar in range(0, II0):
        for half in (0, 2):
            c = chord(P.harm[bar * BPB + half]); pcs = sorted(c['pcs']); root = c['root']
            r = 40 + (root - 40) % 12
            pf(bar * BPB + half, 2.0, r, 0.2, '左手 — 根音と分散和音 (Sweet Revenge の手つき)' if (bar == 0 and half == 0) else None, 'acc', rid=R1, rel=0.7)
            voi = sorted(52 + (p - 52) % 12 for p in pcs)[:4]
            pat = [voi[0], voi[1], voi[-1], voi[1]] if len(voi) >= 2 else voi * 4
            for i, m in enumerate(pat): pf(bar * BPB + half + 0.5 * i, 0.7, m, 0.13 * (1.0 if i % 2 == 0 else 0.8), None, 'acc', rid=R1, rel=0.5)
    # II. 弔鐘、主題 ×4 (息をする打ち直し)、コラール
    add('X', II0 * BPB, 6, 46, 0.4, '弔鐘')
    for n_ in range(2):
        t = (II0 + 8 * n_) * BPB; lab = '主題 08:06 ×4' if n_ == 0 else '主題 08:06 ×4 (オクターヴ下)'
        for d, m in augment(SA, 4):
            k = int(round(d / 2))
            for i in range(k):
                amp = 1.0 if i == 0 else 0.6 + 0.25 * math.sin(math.pi * i / max(1, k - 1))
                pf(t + 2 * i, 2.0, m - 12 * n_, 0.4 * amp, lab if (lab and i == 0) else None, 'x4', rid=R1, rel=0.8); lab = None
            t += d
    for bar in range(II0, III0):
        c = chord(P.harm[bar * BPB]); root = 48 + c['root']
        for m in sorted({root - 12, root} | {m for m in range(52, 70) if m % 12 in c['pcs']})[:4]: pf(bar * BPB, 4.0, m, 0.12, None, 'chorale', rid=R1, rel=1.0)
    # IV. Flower の 4 度の和音 (2 拍ごと)
    for bar in range(IV0, V0):
        c = chord(P.harm[bar * BPB]); tones = sorted({55 + (p - 55) % 12 for p in c['pcs']})[:3]
        for k, m in enumerate(tones): pf(bar * BPB + 0.08 * k, 2.4, m + 12, 0.1, 'Flower の 4 度の和音' if (bar == IV0 and k == 0) else None, 'flower', rid=R2, rel=0.6); pf(bar * BPB + 2.5 + 0.06 * k, 1.5, m + 12, 0.07, None, 'flower', rid=R2, rel=0.6)
    # V. 鐘
    for k, bar in enumerate(range(V0, TOTAL)): add('X', bar * BPB, 8, 64 + 12 * (k % 2), 0.35 - 0.06 * k, '祝鐘' if k == 0 else None)

META = {'style': 'recsampler', 'bank': BANK, 'rec_order': [R1, R2], 'piano_decay': 2.0, 'reverb': [5.0, 2.0, 0.42],
        'title': 'Requiem BADA — CIV · Fiore e Fuga 9/23', 'subtitle': '9/23 の 08:06・08:09 を主題曲に — LXXXVI (Fiore dolce) と LXXXIX (Requiem e Fuga) の作りで融合。実音は使わず、ピアノの 1 音だけ (変ロ短調 → ホ短調 → ホ長調, ♩=60, 5 分 11 秒)',
        'legend': ['PF', 'X'], 'vname': {'PF': '旋律・左手・層', 'X': '鐘'},
        'footer': ['I. Fiore dolce 08:06 (旋律 + 分散和音) → II. Requiem 08:06 (主題 ×4、コラール、弔鐘) → III. Fuga 08:09 (4 声) → IV. Fusione (08:06 ×2 の低音 + 08:09 のストレッタ + Flower の和音) → V. Amen (ホ長調)',
                   '音源は bank85p (9/28 の歌の音を除いたピアノだけ)。9/23 の録音の実音は使わない (声を消す)。声なし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=104, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT)); from collections import Counter
    print('bars', d['nbars'], 'duration', d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
