#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CX · Canzone 9/23 e 9/24 tre in uno senza sospiri (C から息のような音を消して — 9/23 08:09 と 9/24 08:53 の録音 (息の所を下げて) を表に融合)
  表 1: 9/23 08:09 の録音 (3 分 37 秒、ホ短調) を 2 小節目から ／ 表 2: 9/24 08:53 の録音 (3 分 22 秒、ロ短調) を 58 小節目から — どちらも dip_breath.py で息のような所だけ 1〜6 kHz を下げ、ほかは加工なし
  裏 (C / CI / CII の 3 つの層を、それぞれの録音の実速に合わせて):
    第 1 部の層 (骨組み) : 採譜の音を小さく重ねる (2 拍ごとの息をする打ち直し)
    第 2 部の層 (Fuga)   : 08:09 の主題 ソ・ファ#・ソ・シ・ミ (ホ短調)、08:53 の主題 ミ・ファ#・シ・ミ・ミ (ロ短調) の 4 声フーガ (提示 → 反行 → ストレッタ → 拡大)。和音は録音のその時の和音に寄せる (共鳴)
    第 3 部の層 (Natalitia): 録音の終わりが近づくと 1 拍ごとの鼓動・祝鐘・高いマントラ。08:53 が終わる 110 小節目からロ長調の生誕祭 (2 つの主題のストレッタ) → Coda
  音源は bank109 (立ち上がりが遅くふくらむ 1 音を clean_bank.py で外した表)。声なし。119 小節 = 7 分 56 秒 + 残響
  使い方: python compose_tablet110.py <bank109.json> <rec0809_clean.wav> <rec0853_clean.wav> [score_tablet110.json]
"""
import sys, os, json, math
from compose import *
import compose

BANK = sys.argv[1]; W1, W2 = os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]); OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet110.json'
B = json.load(open(BANK)); R1, R2 = '20260923_080918', '20260924_085314'; REC1, REC2 = B['recordings'][R1], B['recordings'][R2]
BPM = 60; T1 = 8.0; P2 = 2 + int(math.ceil((T1 + REC1['dur']) / 4.0)); T2 = P2 * 4.0                 # 表 2 は 08:09 が終わった次の次の小節から
MAJ0 = int(math.ceil((T2 + REC2['dur']) / 4.0)) + 1; TOTAL = MAJ0 + 8
SA = [(0.5, 67), (0.5, 66), (3, 67), (2, 71), (2, 76)]                                              # ソ・ファ#・ソ・シ・ミ (08:09)
SB = [(1, 64), (3, 66), (1.5, 71), (1.5, 76), (1, 76)]                                              # ミ・ファ#・シ・ミ・ミ (08:53)
CANDS_E = ['Em', 'Am', 'B', 'B7', 'G', 'C', 'D', 'F#m7b5', 'Am/C', 'Em/G', 'Cmaj7', 'Em7', 'Gmaj7', 'Esus4', 'A', 'Dsus4']
CANDS_B = ['Bm', 'Em', 'F#', 'F#7', 'D', 'G', 'A', 'C#m7b5', 'Em/G', 'Bm/D', 'Gmaj7', 'Bm7', 'Em7', 'Asus4', 'D7', 'C', 'Cmaj7']
CANDS_BJ = ['B', 'E', 'F#', 'F#7', 'G#m', 'C#m', 'B/D#', 'E/G#']
MAJ = {2: 3, 7: 8, 9: 10}                                                                           # ロ短調 → ロ長調
NAT1, NAT2 = P2 - 14, MAJ0 - 10
octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}; TOP = {'S': 86, 'A': 76, 'T': 69, 'B': 62}
extras = []; RH = []

def add(v, beat, dbeats, m, gain, label=None, **kw):
    extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
def pf(beat, dbeats, m, gain, label=None, layer='bb', rid=R1, rel=0.5): add('PF', beat, dbeats, m, gain, label, rid=rid, rel=rel, layer=layer)
def majify(m): return (m - m % 12 + MAJ[m % 12]) if m % 12 in MAJ else m

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

def fuga(P, f, subj, lab, cands, order='ASBT'):
    """提示 (8) → 反行 (4) → ストレッタ (6) → 拡大 + 主題 (4) = 22 小節"""
    E = []
    for k, v in enumerate(order):
        entry(P, f + 2 * k, v, subj, 7 if k % 2 else 0, lab + (' 答唱' if k % 2 else ''), E)
        for w in order[k + 1:]: P.rest_bars(w, f + 2 * k, f + 2 * k + 2)
    harm_fit(P, f, f + 8, E, cands)
    E = []; entry(P, f + 8, 'S', invert(subj), 0, lab + ' (反行)', E); entry(P, f + 10, 'T', invert(subj), 0, lab + ' (反行)', E); harm_fit(P, f + 8, f + 12, E, cands)
    E = []
    for k, v in enumerate('ASTB'): entry(P, f + 12 + k, v, subj, 0, lab + ' ストレッタ' if k == 0 else None, E)
    harm_fit(P, f + 12, f + 18, E, cands)
    E = []; entry(P, f + 18, 'B', augment(subj), 0, lab + ' (拡大 ×2)', E); entry(P, f + 20, 'S', subj, 0, lab, E); harm_fit(P, f + 18, f + 22, E, cands)
    return f + 22

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.95
    for q in range(TOTAL * BPB):                                                                    # 和音は録音のその時の和音
        if q < P2 * BPB: rec, t0, cur = REC1, T1, 'Em'
        else: rec, t0, cur = REC2, T2, 'Bm'
        tr = q - t0
        for s in rec['segs']:
            if s['t'] <= tr: cur = s['ch']
        RH.append(cur); P.harm[q] = cur
    P.section(0, '表 1: 9/23 08:09 の録音 (息の所だけ下げて) + 骨組み', '弔鐘 → 2 小節目から録音 — 裏で採譜の骨組みが小さく息をする')
    for v in VOICES: P.rest_bars(v, 0, 6)
    P.section(6, '裏: 08:09 の主題のフーガ (ホ短調)', '主題 ソ・ファ#・ソ・シ・ミ の 4 声フーガ: 提示 → 反行 → ストレッタ → 拡大 — 和音は録音のその時の和音に寄せて (共鳴)')
    e1 = fuga(P, 6, SA, '主題 08:09', CANDS_E)
    for v in VOICES: P.rest_bars(v, e1, P2)
    P.section(NAT1, '裏: 鼓動・祝鐘・マントラ (録音の終わりが近づく)', '1 拍ごとの鼓動と高いマントラが入り、08:09 の録音が終わる')
    P.section(P2, '表 2: 9/24 08:53 の録音 (息の所だけ下げて) + 骨組み', '弔鐘 → ロ短調の録音 — 裏で採譜の骨組みが小さく息をする')
    for v in VOICES: P.rest_bars(v, P2, P2 + 4)
    P.section(P2 + 4, '裏: 08:53 の主題のフーガ (ロ短調)', '主題 ミ・ファ#・シ・ミ・ミ の 4 声フーガ: 提示 → 反行 → ストレッタ → 拡大 — 和音は録音のその時の和音に寄せて')
    e2 = fuga(P, P2 + 4, SB, '主題 08:53', CANDS_B)
    for v in VOICES: P.rest_bars(v, e2, MAJ0)
    P.section(NAT2, '裏: 鼓動・祝鐘・マントラ (録音の終わりが近づく)', '1 拍ごとの鼓動と高いマントラ — 08:53 の録音が終わるとロ長調へ')
    P.section(MAJ0, 'Natalitia (ロ長調) — 2 つの主題のストレッタ', '08:53 の主題と 08:09 の主題 (ロ短調に移して) がロ長調で重なり、頂点 → Coda')
    E = []; SA_B = [(d, m + 7) for d, m in SA]
    for k, v in enumerate('SATB'): entry(P, MAJ0 + k, v, SB if k % 2 == 0 else SA_B, 0, ('主題 08:53' if k == 0 else '主題 08:09 (ロ短調に)') if k < 2 else None, E)
    entry(P, MAJ0 + 4, 'B', augment(SB), 0, '主題 08:53 (拡大 ×2)', E); entry(P, MAJ0 + 4, 'S', SB, 12, None, E); entry(P, MAJ0 + 5, 'A', SA_B, 0, None, E)
    harm_fit(P, MAJ0, TOTAL - 2, E, CANDS_BJ)
    for b in range(TOTAL - 2, TOTAL): P.set_harm(b, 'B'); P.hold.add(b)
    P.place('S', TOTAL - 2, [(4, 83)] * 2, 0, 'シ (頂点)'); P.place('B', TOTAL - 2, [(4, 47)] * 2, 0, '')
    for k in range(MAJ0, TOTAL): P.dyn[k] = 1.05 + 0.15 * min(1.0, (k - MAJ0) / 4.0) - (0.25 if k >= TOTAL - 2 else 0)
    return P

def post(P, events, ex):
    add('X', 0, 6, 52, 0.45, '弔鐘')
    add('REC', T1, REC1['dur'], 0, 0.8, None, src=W1, off=0.0, fin=0.02, fout=1.0, rid=R1 + '.wav', tag='9/23 08:09 — 表 (息の所だけ下げて)')
    add('REC', T2, REC2['dur'], 0, 0.8, None, src=W2, off=0.0, fin=0.02, fout=1.0, rid=R2 + '.wav', tag='9/24 08:53 — 表 (息の所だけ下げて)')
    add('X', T2, 6, 47, 0.4, '弔鐘')
    for rec, t0, rid in ((REC1, T1, R1), (REC2, T2, R2)):                                           # 第 1 部の層: 採譜を小さく重ねる
        first = True
        for s in rec['segs']:
            b0 = t0 + s['t']
            for m in s['m']:
                step = 2.0; n_ = max(1, int(round(s['d'] / step)))
                for i in range(n_):
                    amp = 1.0 if i == 0 else 0.55
                    pf(b0 + i * step, min(step, s['d'] - i * step) + 0.2, m, 0.11 * amp * (1.2 if m < 48 else 1.0), '採譜 (骨組み、小さく)' if first else None, 'bb', rid=rid); first = False
    for nat0, nat1, subj, rid, maj in ((NAT1, P2, SA, R1, False), (NAT2, TOTAL, SB, R2, True)):     # 第 3 部の層
        for bar in range(nat0, nat1):
            k = bar - nat0; g = 0.08 + 0.14 * min(1.0, k / 14.0)
            cc = chord(P.harm[bar * BPB]); root = 48 + cc['root']
            tones = [root - 12, root] + [m for m in range(55, 67) if m % 12 in cc['pcs']][:3]
            step = 1.0 if bar < nat1 - 2 else 2.0
            for i in range(int(BPB / step)):
                for m in tones: pf(bar * BPB + i * step, step, m, g * (1.0 if i == 0 else 0.75) * (1.25 if m < 48 else 0.8), '鼓動 (1 拍ごと)' if (k == 0 and i == 0 and m == root) else None, 'pulse', rid=rid)
            if k % 4 == 0: add('X', bar * BPB, 6, 64 + 12 * ((k // 4) % 2), 0.3 + 0.3 * min(1.0, k / 14.0), '祝鐘' if k == 0 else None)
            if k % 2 == 0 and bar < nat1 - 2:
                t = bar * BPB; lab = '高いマントラ' if k == 0 else None
                for d, m in subj: pf(t, d, (majify(m) if (maj and bar >= MAJ0) else m) + 24, 0.12 + 0.1 * min(1.0, k / 14.0), lab, 'mantra', rid=rid, rel=0.8); t += d; lab = None
    add('X', (TOTAL - 1) * BPB, 8, 71, 0.5, None); add('X', (TOTAL - 1) * BPB + 2, 8, 59, 0.4, None)
    for v in VOICES: events[v] = [(s, d, majify(m) if s >= MAJ0 * BPB else m, lab) for s, d, m, lab in events[v]]

META = {'style': 'recsampler', 'bank': BANK, 'rec_order': [R1, R2], 'piano_decay': 2.0, 'reverb': [5.0, 2.0, 0.42],
        'title': 'Requiem BADA — CX · Canzone 9/23 e 9/24 tre in uno senza sospiri',
        'subtitle': 'C から息のような音を消して — 表: 9/23 08:09 → 9/24 08:53 の録音 (息の所だけ下げて) ／ 裏: 骨組み + 2 つの主題のフーガ + 生誕祭、ふくらむ音を外したピアノの 1 音で (ホ短調 → ロ短調 → ロ長調, ♩=60, 8 分 3 秒)',
        'legend': ['PF', 'X'], 'vname': {'PF': '裏の層', 'X': '鐘'},
        'footer': ['表 1: 08:09 (2 小節目から 3 分 37 秒) + 骨組み・フーガ (ホ短調)・鼓動 → 表 2: 08:53 (%d 小節目から 3 分 22 秒) + 骨組み・フーガ (ロ短調)・鼓動 → Natalitia (ロ長調、2 つの主題のストレッタ) → Coda' % (P2 + 1),
                   '音源は bank109 (立ち上がりが速く減衰する 1 音だけ)。録音は息のような所 (1〜4 kHz が平らなノイズになる 0.5 秒) だけ 1〜6 kHz を下げ、ほかは加工なし。声なし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=110, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT)); from collections import Counter
    print('bars', d['nbars'], 'duration', d['duration'], 'P2', P2, 'MAJ0', MAJ0, 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
