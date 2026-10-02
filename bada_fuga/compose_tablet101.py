#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CI · Canzone tre in uno 08:53 (XCVII の 3 つの部を同時に融合して裏に、9/24 08:53 の録音そのものを表に)
  表: 9/24 08:53 の録音 (3 分 22 秒、ロ短調、ピアノの実音。加工なし — 引き伸ばしも速めもしない) を 2 小節目から、元の速さ・元の高さで
  裏 (XCVII の 3 つの部を 3 つの層に — XCVIII と同じ考え、ただし録音の実速に合わせる):
    第 1 部の層 (骨組み)  : 採譜の音を小さくピアノで重ねる (息をする打ち直し)
    第 2 部の層 (Fuga)    : 主題 ミ・ファ#・シ・ミ・ミ の 4 声フーガ (提示 → 反行 → ストレッタ → 保続 → 拡大)。和音は録音のその時の和音に寄せて選ぶ (共鳴)
    第 3 部の層 (Natalitia): 録音の終わりが近づく 40 小節目から 1 拍ごとの鼓動・祝鐘・高いマントラ、録音が終わる 53 小節目からロ長調の生誕祭 (ストレッタ、拡大、頂点) → Coda
  音源は bank85p (9/28 の歌の音を除いたピアノだけ)。声なし。62 小節 = 4 分 8 秒 + 残響
  使い方: python compose_tablet101.py <bank85p.json> <rec0853.wav (mp3 から)> [score_tablet101.json]
"""
import sys, os, json, math
from compose import *
import compose

BANK = sys.argv[1]; RECWAV = os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet101.json'
R = '20260924_085314'; REC = json.load(open(BANK))['recordings'][R]
BPM = 60; T_REC = 8.0                                                           # 録音は 2 小節目から
SUBJ = [(1, 64), (3, 66), (1.5, 71), (1.5, 76), (1, 76)]
CANDS_M = ['Bm', 'Em', 'F#', 'F#7', 'D', 'G', 'A', 'C#m7b5', 'Em/G', 'Bm/D', 'Gmaj7', 'Bm7', 'Em7', 'Asus4', 'D7', 'C', 'Cmaj7', 'E', 'A#m', 'A#m7']
CANDS_J = ['B', 'E', 'F#', 'F#7', 'G#m', 'C#m', 'B/D#', 'E/G#']
FUGA0, NATAL0 = 6, 40
MAJ0 = int(math.ceil((T_REC + REC['dur']) / 4.0))                               # 録音が終わる小節 (53)
TOTAL = MAJ0 + 9
MAJ = {2: 3, 7: 8, 9: 10}
octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}; TOP = {'S': 86, 'A': 76, 'T': 69, 'B': 62}
extras = []; RH = []

def add(v, beat, dbeats, m, gain, label=None, **kw):
    extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
def pf(beat, dbeats, m, gain, label=None, layer='rec', rel=0.5): add('PF', beat, dbeats, m, gain, label, rid=R, rel=rel, layer=layer)

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
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.75 + 0.45 * max(0, k - NATAL0) / float(TOTAL - NATAL0)
    cur = 'Bm'
    for q in range(TOTAL * BPB):                                                   # 録音の和音 (実速)
        tr = q - T_REC
        for s in REC['segs']:
            if s['t'] <= tr: cur = s['ch']
        RH.append(cur); P.harm[q] = cur
    for b in range(MAJ0, TOTAL): P.set_harm(b, ['B', 'B', 'E', 'E'] if b % 2 == 0 else ['F#7', 'F#7', 'B', 'B'])
    for b in range(TOTAL - 2, TOTAL): P.set_harm(b, 'B'); P.hold.add(b)
    P.section(0, 'Canzone — 表: 9/24 08:53 の録音 (実音)', '弔鐘ひとつ → 2 小節目から録音そのもの (元の速さ・元の高さ、加工なし) — 裏に XCVII の 3 つの層が重なっていく')
    for v in VOICES: P.rest_bars(v, 0, FUGA0)
    f = FUGA0; lab = '主題 08:53'; E = []
    P.section(f, '裏: 第 2 部の層 (Fuga)', '主題の 4 声フーガが録音の下に: 提示 → 反行 → ストレッタ → ファ# の保続 → 拡大 — 和音は録音のその時の和音に寄せて (共鳴)')
    for k, v in enumerate('ASBT'):
        entry(P, f + 2 * k, v, SUBJ, 7 if k % 2 else 0, lab + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, f + 2 * k, f + 2 * k + 2)
    harm_fit(P, f, f + 8, E, CANDS_M)
    E = []; entry(P, f + 8, 'S', invert(SUBJ), 0, lab + ' (反行)', E); entry(P, f + 10, 'T', invert(SUBJ), 0, lab + ' (反行)', E)
    harm_fit(P, f + 8, f + 12, E, CANDS_M)
    E = []
    for k, v in enumerate('ASTB'): entry(P, f + 12 + k, v, SUBJ, 0, lab + ' ストレッタ', E)
    harm_fit(P, f + 12, f + 18, E, CANDS_M)
    E = []; entry(P, f + 18, 'S', SUBJ, 0, lab, E); entry(P, f + 20, 'A', SUBJ, 7, lab + ' 答唱', E)
    P.place('B', f + 18, [(4, 42)] * 4, 0, '属音の保続 (ファ#)'); harm_fit(P, f + 18, f + 22, E, ['F#7', 'F#', 'Bm', 'Bm/D', 'D', 'C#m7b5'])
    E = []; entry(P, f + 22, 'B', augment(SUBJ), 0, lab + ' (拡大 ×2)', E); harm_fit(P, f + 22, f + 26, E, CANDS_M)
    E = []; entry(P, f + 26, 'A', SUBJ, 0, lab, E); entry(P, f + 28, 'T', invert(SUBJ), 0, lab + ' (反行)', E)
    harm_fit(P, f + 26, f + 30, E, CANDS_M)
    for v in VOICES: P.rest_bars(v, f + 30, NATAL0)
    P.section(NATAL0, '裏: 第 3 部の層 (Natalitia が近づく)', '1 拍ごとの鼓動、祝鐘、高いマントラ — 録音はまだ表で歌っている')
    E = []
    for k, v in enumerate('SATB'): entry(P, NATAL0 + 2 * k, v, SUBJ, 12 if v in 'SA' else 0, lab + ' — 生誕祭へ' if k == 0 else None, E)
    harm_fit(P, NATAL0, NATAL0 + 8, E, CANDS_M)
    E = []
    for k, v in enumerate('ASTB'): entry(P, NATAL0 + 8 + k * 2, v, SUBJ, 12 if v in 'SA' else 0, None, E)
    harm_fit(P, NATAL0 + 8, MAJ0, E, CANDS_M)
    P.section(MAJ0, '生誕祭 — ロ長調 (録音が終わって)', '3 つの層ともロ長調へ — 主題のストレッタ、拡大、鼓動、祝鐘、ロ長調の和音で頂点')
    E = []
    for k, v in enumerate('BTAS'): entry(P, MAJ0 + k, v, SUBJ, 12 if v in 'SA' else 0, lab + ' (ロ長調)' if k == 0 else None, E)
    entry(P, MAJ0 + 4, 'S', augment(SUBJ), 12, lab + ' (拡大 ×2、頂点)', E); entry(P, MAJ0 + 5, 'A', SUBJ, 12, None, E)
    P.place('S', TOTAL - 2, [(4, 83), (4, 83)], 0, 'シ (頂点)'); P.place('B', TOTAL - 2, [(4, 35), (4, 35)], 0, '')
    return P

def post(P, events, ex):
    def majify(m): return (m - m % 12 + MAJ[m % 12]) if m % 12 in MAJ else m
    add('X', 0, 6, 47, 0.45, '弔鐘')
    add('REC', T_REC, REC['dur'], 0, 0.8, None, src=RECWAV, off=0.0, fin=0.02, fout=1.0, rid=R + '.wav', tag='9/24 08:53 — 表 (実音、加工なし)')
    first = True                                                                   # 第 1 部の層: 採譜を小さく重ねる (息をする打ち直し)
    for s in REC['segs']:
        b0 = T_REC + s['t']
        for m in s['m']:
            step = 2.0; n_ = max(1, int(round(s['d'] / step)))
            for i in range(n_):
                amp = 1.0 if i == 0 else 0.55
                pf(b0 + i * step, min(step, s['d'] - i * step) + 0.2, m, 0.11 * amp * (1.2 if m < 48 else 1.0), '採譜 (骨組み、小さく)' if first else None, 'bb', rel=0.5); first = False
    for bar in range(NATAL0, TOTAL):                                               # 第 3 部の層
        k = bar - NATAL0; g = 0.08 + 0.14 * min(1.0, k / 14.0)
        cc = chord(P.harm[bar * BPB]); root = 48 + cc['root']
        tones = [root - 12, root] + [m for m in range(55, 67) if m % 12 in cc['pcs']][:3]
        step = 1.0 if bar < TOTAL - 2 else 2.0
        for i in range(int(BPB / step)):
            for m in tones: pf(bar * BPB + i * step, step, m, g * (1.0 if i == 0 else 0.75) * (1.25 if m < 48 else 0.8), '鼓動 (1 拍ごと)' if (k == 0 and i == 0 and m == root) else None, 'pulse', rel=0.5)
        if k % 4 == 0: add('X', bar * BPB, 6, 59 + 12 * ((k // 4) % 2), 0.3 + 0.3 * min(1.0, k / 14.0), '祝鐘' if k == 0 else None)
        if k % 2 == 0 and bar < TOTAL - 2:
            t = bar * BPB; lab = '高いマントラ' if k == 0 else None
            for d, m in SUBJ: pf(t, d, (majify(m) if bar >= MAJ0 else m) + 24, 0.12 + 0.1 * min(1.0, k / 14.0), lab, 'mantra', rel=0.8); t += d; lab = None
    add('X', (TOTAL - 1) * BPB, 8, 71, 0.5, None); add('X', (TOTAL - 1) * BPB + 2, 8, 59, 0.4, None)
    for v in VOICES: events[v] = [(s, d, majify(m) if s >= MAJ0 * BPB else m, lab) for s, d, m, lab in events[v]]

META = {'style': 'recsampler', 'bank': BANK, 'rec_order': [R], 'piano_decay': 2.0, 'reverb': [5.0, 2.0, 0.42],
        'title': 'Requiem BADA — CI · Canzone tre in uno 08:53', 'subtitle': '表: 9/24 08:53 の録音そのもの ／ 裏: XCVII の 3 つの部を融合 (骨組み + フーガ + 生誕祭)、和音を録音にそろえて共鳴 (ロ短調 → ロ長調, ♩=60, 4 分 15 秒)',
        'legend': ['PF', 'X'], 'vname': {'PF': '裏の層', 'X': '鐘'},
        'footer': ['表: 録音 (実音、加工なし) が 2 小節目から 3 分 22 秒 ／ 裏: 第 1 部 = 採譜の骨組み (小さく)、第 2 部 = 主題の 4 声フーガ、第 3 部 = 鼓動・祝鐘・マントラ → 録音が終わるとロ長調の生誕祭',
                   '音源は bank85p (9/28 の歌の音を除いたピアノだけ)。録音は引き伸ばさない。声なし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=101, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT)); from collections import Counter
    print('bars', d['nbars'], 'duration', d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
