#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions C · Tre in uno (08:09) (XCIX の 3 つの部を同時に — 上手に共鳴させて、3 分以内に)
  XCIX (56 分、3 部) を 3 つの層に凝縮して同時に鳴らす (42 小節 = 2 分 48 秒 + 残響):
    第 1 部の層 (Praeludium・骨組み) : 08:09 の採譜を実速に戻して 160 秒に (録音の 215 秒 × 0.744) ピアノで
    第 2 部の層 (Fuga)               : 主題 ソ・ファ#・ソ・シ・ミ の 4 声フーガ (提示 → 反行 → ストレッタ → 保続 → 拡大)。和音は録音の進行に寄せて選ぶ (共鳴)
    第 3 部の層 (Natalitia)          : 30 小節目から 1 拍ごとの鼓動、祝鐘、高いマントラ — 36 小節目からホ長調 (3 つの層とも長調へ)、ホ長調の和音と鐘で閉じる
  共鳴: 3 つの層の和音は録音の採譜の進行を土台にそろえ、フーガの和音は「主題の音を含み、かつ録音の和音に近いもの」を選ぶ。音はすべて 08:09 のピアノの 1 音と鐘。声なし
  使い方: python compose_tablet100.py <bank85.json> [score_tablet100.json]
"""
import sys, os, json, math
from compose import *
import compose

BANK = sys.argv[1]; FAST = ''; OUT = sys.argv[2] if len(sys.argv) > 2 else 'score_tablet100.json'
R = '20260923_080918'; REC = json.load(open(BANK))['recordings'][R]
FOG = 0.0                                                                      # 霧 (録音を速めた音) は使わない (声のように聞こえるので)
BPM = 60; T0 = 1.7; SC = 160.0 / (REC['dur'] - T0)                              # 録音の時間 → 拍 (×0.8)
SUBJ = [(0.5, 67), (0.5, 66), (3, 67), (2, 71), (2, 76)]                       # ソ・ファ#・ソ・シ・ミ
CANDS_M = ['Em', 'Am', 'B', 'B7', 'G', 'C', 'D', 'F#m7b5', 'Am/C', 'Em/G', 'Cmaj7', 'Em7', 'Gmaj7', 'Esus4', 'A', 'Dsus4', 'A#m7', 'A#m', 'D#7']
CANDS_J = ['E', 'A', 'B', 'B7', 'C#m', 'F#m', 'E/G#', 'A/C#']
FUGA0, NATAL0, MAJ0, TOTAL = 4, 30, 36, 42
MAJ = {7: 8, 0: 1, 2: 3}                                                       # ホ長調へ
octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}; TOP = {'S': 86, 'A': 76, 'T': 69, 'B': 62}
extras = []; RH = []                                                            # 録音の和音 (拍ごと)

def add(v, beat, dbeats, m, gain, label=None, **kw):
    extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
def pf(beat, dbeats, m, gain, label=None, layer='rec', rel=0.5): add('PF', beat, dbeats, m, gain, label, rid=R, rel=rel, layer=layer)

def harm_fit(P, b0, b1, entries, cands):
    """主題の音を最も多く含み、かつ録音の和音 (RH) に近い和音"""
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
                return sum(w * (1 if m % 12 in cc else -0.8) for w, m in notes) + 1.2 * len(cc & rc) / max(1, len(cc)) + (1.0 if c == RH[a] else 0)
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
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.9 + 0.4 * max(0, k - NATAL0) / 12.0
    cur = 'Em'
    for q in range(TOTAL * BPB):                                                   # 録音の和音を ×0.8 で
        tr = q / SC + T0
        for s in REC['segs']:
            if s['t'] <= tr: cur = s['ch']
        RH.append(cur); P.harm[q] = cur
    for b in range(MAJ0, TOTAL): P.set_harm(b, ['E', 'E', 'A', 'A'] if b % 2 == 0 else ['B7', 'B7', 'E', 'E'])
    for b in range(TOTAL - 2, TOTAL): P.set_harm(b, 'E'); P.hold.add(b)
    P.section(0, 'Tre in uno — 第 1 部の層 (骨組み、実速)', '08:09 の採譜を実速に (×0.744 で 160 秒) ピアノの 1 音で — 弔鐘ひとつから')
    for v in VOICES: P.rest_bars(v, 0, FUGA0)
    f = FUGA0; lab = '主題 08:09'; E = []
    P.section(f, '+ 第 2 部の層 (Fuga)', '主題の 4 声フーガ: 提示 → 反行 → ストレッタ → シ の保続 → 拡大 — 和音は録音の進行に寄せて (共鳴)')
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
    P.place('B', f + 18, [(4, 47)] * 4, 0, '属音の保続 (シ)'); harm_fit(P, f + 18, f + 22, E, ['B7', 'B', 'Em', 'Em/G', 'G', 'F#m7b5'])
    E = []; entry(P, f + 22, 'B', augment(SUBJ), 0, lab + ' (拡大 ×2)', E); harm_fit(P, f + 22, f + 26, E, CANDS_M)
    P.section(NATAL0, '+ 第 3 部の層 (Natalitia)', '1 拍ごとの鼓動、祝鐘、高いマントラ ソ・ファ#・ソ・シ・ミ — 3 つの層が重なる')
    E = []
    for k, v in enumerate('SATB'): entry(P, NATAL0 + 2 * k, v, SUBJ, 12 if v in 'SA' else 0, lab + ' — 生誕祭' if k == 0 else None, E)
    harm_fit(P, NATAL0, NATAL0 + 6, E, CANDS_M)
    P.section(MAJ0, 'ホ長調 — 3 つの層が共鳴して閉じる', '3 つの層ともホ長調へ — 主題のストレッタ、鼓動、祝鐘、ホ長調の和音で')
    E = []
    for k, v in enumerate('BTAS'): entry(P, MAJ0 + k, v, SUBJ, 12 if v in 'SA' else 0, lab + ' (ホ長調)' if k == 0 else None, E)
    P.place('S', TOTAL - 2, [(4, 88), (4, 88)], 0, 'ミ (頂点)'); P.place('B', TOTAL - 2, [(4, 40), (4, 40)], 0, '')
    return P

def post(P, events, ex):
    def majify(m): return (m - m % 12 + MAJ[m % 12]) if m % 12 in MAJ else m
    add('X', 0, 6, 52, 0.4, '弔鐘')
    # 第 1 部の層: 採譜を実速 (×0.8) で、終わりはロ長調に寄せる。霧 = 録音を速めた音
    first = True
    for s in REC['segs']:
        b0 = (s['t'] - T0) * SC
        if b0 < 0 or b0 >= TOTAL * BPB - 1: continue
        for m in s['m']:
            mm = majify(m) if b0 >= MAJ0 * BPB else m
            pf(b0, max(0.5, s['d'] * SC), mm, 0.30 * (1.2 if m < 48 else 1.0), '08:09 の採譜 (実速 ×0.744)' if first else None, 'rec'); first = False
    if FOG > 0: add('REC', 0, TOTAL * BPB, 0, FOG, None, src=FAST, off=0.0, fin=2.0, fout=8.0, rid='rec0853_fast', tag='08:53 の録音を ×0.8 の時間に (高さは変えず) — 霧')
    # 第 3 部の層: 鼓動 (1 拍ごと)、祝鐘、高いマントラ
    for bar in range(NATAL0, TOTAL):
        k = bar - NATAL0; g = 0.1 + 0.12 * min(1.0, k / 8.0)
        cc = chord(P.harm[bar * BPB]); root = 48 + cc['root']
        tones = [root - 12, root] + [m for m in range(55, 67) if m % 12 in cc['pcs']][:3]
        step = 1.0 if bar < TOTAL - 2 else 2.0
        for i in range(int(BPB / step)):
            for m in tones: pf(bar * BPB + i * step, step, m, g * (1.0 if i == 0 else 0.75) * (1.25 if m < 48 else 0.8), '鼓動 (1 拍ごと)' if (k == 0 and i == 0 and m == root) else None, 'pulse', rel=0.5)
        if k % 4 == 0: add('X', bar * BPB, 6, 64 + 12 * ((k // 4) % 2), 0.35 + 0.3 * min(1.0, k / 8.0), '祝鐘' if k == 0 else None)
        if k % 2 == 0 and bar < TOTAL - 2:
            t = bar * BPB; lab = '高いマントラ' if k == 0 else None
            for d, m in SUBJ: pf(t, d, (majify(m) if bar >= MAJ0 else m) + 24, 0.14 + 0.08 * min(1.0, k / 8.0), lab, 'mantra', rel=0.8); t += d; lab = None
    add('X', (TOTAL - 1) * BPB, 8, 76, 0.5, None); add('X', (TOTAL - 1) * BPB + 2, 8, 64, 0.4, None)
    for v in VOICES: events[v] = [(s, d, majify(m) if s >= MAJ0 * BPB else m, lab) for s, d, m, lab in events[v]]

META = {'style': 'recsampler', 'bank': BANK, 'rec_order': [R], 'piano_decay': 2.0, 'reverb': [5.0, 2.0, 0.42],
        'title': 'Requiem BADA — C · Tre in uno (08:09)', 'subtitle': 'XCIX の 3 つの部を同時に — 採譜 (実速) + フーガ + 生誕祭、和音を録音にそろえて共鳴 (ホ短調 → ホ長調, ♩=60, 2 分 55 秒)',
        'legend': ['PF', 'X'], 'vname': {'PF': '第 1・3 部の層', 'X': '鐘'},
        'footer': ['第 1 部の層: 08:09 の採譜 (実速) ／ 第 2 部の層: 主題の 4 声フーガ ／ 第 3 部の層: 鼓動・祝鐘・マントラ → 36 小節目からホ長調',
                   '3 つの層の和音は録音の進行にそろえる。音はすべて 08:09 のピアノの 1 音と鐘。声なし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=100, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT)); from collections import Counter
    print('bars', d['nbars'], 'duration', d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
