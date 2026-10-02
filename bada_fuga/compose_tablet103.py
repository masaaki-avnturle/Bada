#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CIII · Canzone 08:53 sopra Contrapunctus (XCVI の 3 つの層を同時に融合して裏 (バック) に、9/24 08:53 の録音そのものを表に)
  表: 9/24 08:53 の録音 (3 分 22 秒、ロ短調、ピアノの実音、加工なし) を 2 小節目から、元の速さ・元の高さで
  裏 (XCVI = piano_solo_8x の主題による Contrapunctus XIV を ×16・×4・×1 で — をロ短調 (−3) に移して、録音の実速に合わせた 3 つの層に):
    ×16 の層 (骨組み) : 第 1 主題 (ソ・ド#・ソ・ファ#・シ・ファ#・ミ・レ・シ) を 4 倍に伸ばして低く、2 拍ごとに息をするように打ち直す — 8 小節ごとに 6 回
    ×4 の層           : 第 2 主題 (駆け足) ×4 と B-A-C-H ×4 (ロ短調では ソ・ファ#・ラ・ソ#) が交互に、内声で小さく
    ×1 の層 (Fuga)    : 4 声のフーガ — 第 1 主題の提示 → 第 2 主題の提示 → 第 1 主題の反行 → B-A-C-H の提示 → ストレッタ → 二重 → ファ# の保続 → 低音の拡大。和音は録音のその時の和音に寄せて選ぶ (共鳴)
  録音が終わる 53 小節目から三重フーガ (3 つの主題を同時に) → 58 小節目の 2 拍目で楽譜が途切れる (Contrapunctus XIV のように) → 沈黙
  音源は bank85p (9/28 の歌の音を除いたピアノだけ)、鐘。声なし。60 小節 = 4 分 + 残響
  使い方: python compose_tablet103.py <bank85p.json> <rec0853.wav> [score_tablet103.json]
"""
import sys, os, json, math
from compose import *
import compose

BANK = sys.argv[1]; RECWAV = os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet103.json'
R = '20260924_085314'; REC = json.load(open(BANK))['recordings'][R]
BPM = 60; T_REC = 8.0; TR = -3                                                    # ニ短調 → ロ短調
S1 = [(d, m + TR) for d, m in [(1.5, 70), (0.5, 64), (1, 70), (1, 69), (1, 62), (1, 69), (0.5, 67), (0.5, 65), (1, 62)]]
S2 = [(0.5, m + TR) for m in (72, 67, 62, 65, 64, 62, 64, 60, 62, 64, 70, 69, 67, 65, 64, 61)]
S3 = [(2, m + TR) for m in (70, 69, 72, 71)]                                      # B-A-C-H → ソ・ファ#・ラ・ソ#
L1, L2, L3 = '主題 I (piano_solo_8x)', '主題 II (駆け足)', 'B-A-C-H'
CANDS = ['Bm', 'Em', 'F#', 'F#7', 'D', 'G', 'A', 'C#m7b5', 'Em/G', 'Bm/D', 'Gmaj7', 'Bm7', 'Em7', 'Asus4', 'D7', 'C', 'Cmaj7', 'E', 'E7', 'C#7', 'A#m', 'A#m7']
MAJ0 = int(math.ceil((T_REC + REC['dur']) / 4.0))                                 # 録音が終わる小節 (53)
TOTAL = MAJ0 + 7; CUT = (MAJ0 + 5) * 4 + 1                                        # 58 小節目の 2 拍目で途切れる
octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}; TOP = {'S': 86, 'A': 76, 'T': 69, 'B': 62}
extras = []; RH = []

def add(v, beat, dbeats, m, gain, label=None, **kw):
    extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
def pf(beat, dbeats, m, gain, label=None, layer='x16', rel=0.5): add('PF', beat, dbeats, m, gain, label, rid=R, rel=rel, layer=layer)

def harm_fit(P, b0, b1, entries, cands, use_rec=True):
    for bar in range(b0, b1):
        for h in range(2):
            a = bar * BPB + 2 * h; notes = []
            for e0, sb in entries:
                t = e0
                for d, m in sb:
                    ov = min(a + 2, t + d) - max(a, t)
                    if ov > 0: notes.append((ov * (2 if t <= a < t + d else 1), m))
                    t += d
            rc = set(chord(RH[a])['pcs']) if use_rec else set()
            def score(c):
                cc = set(chord(c)['pcs'])
                return sum(w * (1 if m % 12 in cc else -0.8) for w, m in notes) + (1.5 * len(cc & rc) / max(1, len(cc)) + (1.2 if c == RH[a] else 0) if use_rec else 0)
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

def expo(P, f, subj, lab, order, E):
    for k, v in enumerate(order):
        entry(P, f + 2 * k, v, subj, 7 if k % 2 else 0, lab + (' 答唱' if k % 2 else ''), E)
        for w in order[k + 1:]: P.rest_bars(w, f + 2 * k, f + 2 * k + 2)

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.7 + 0.4 * max(0, k - 40) / 18.0
    cur = 'Bm'
    for q in range(TOTAL * BPB):
        tr = q - T_REC
        for s in REC['segs']:
            if s['t'] <= tr: cur = s['ch']
        RH.append(cur); P.harm[q] = cur
    P.section(0, 'Canzone — 表: 9/24 08:53 の録音 (実音)', '弔鐘ひとつ → 2 小節目から録音そのもの (加工なし) — 裏に XCVI の 3 つの層 (×16・×4・×1、ロ短調に移して) が重なっていく')
    for v in VOICES: P.rest_bars(v, 0, 4)
    f = 4; E = []
    P.section(f, '裏: ×1 の層 — Contrapunctus (第 1 主題の提示)', '第 1 主題 (ソ・ド#・ソ・ファ#・シ・ファ#・ミ・レ・シ) の 4 声の提示 — 和音は録音のその時の和音に寄せて (共鳴)')
    expo(P, f, S1, L1, 'ASBT', E); harm_fit(P, f, f + 8, E, CANDS)
    P.set_harms(f + 8, [[RH[(f + 8) * 4]] * 4, [RH[(f + 9) * 4]] * 4])
    E = []; P.section(f + 10, '裏: 第 2 主題の提示', '駆け足の第 2 主題が 4 声で (T → A → B → S)'); expo(P, f + 10, S2, L2, 'TABS', E); harm_fit(P, f + 10, f + 18, E, CANDS)
    E = []; entry(P, f + 18, 'S', invert(S1), 0, L1 + ' (反行)', E); entry(P, f + 20, 'T', invert(S1), 0, L1 + ' (反行)', E); harm_fit(P, f + 18, f + 22, E, CANDS)
    E = []; P.section(f + 22, '裏: B-A-C-H の提示', 'ロ短調の B-A-C-H (ソ・ファ#・ラ・ソ#) が 4 声で (B → T → A → S)'); expo(P, f + 22, S3, L3, 'BTAS', E); harm_fit(P, f + 22, f + 30, E, CANDS)
    E = []; P.section(f + 30, '裏: ストレッタ → 二重 → 保続 → 拡大', '第 1 主題のストレッタ → 第 1 + 第 2 主題の二重 → ファ# の保続 → 低音の拡大 — 録音はまだ表で歌っている')
    for k, v in enumerate('ASTB'): entry(P, f + 30 + k, v, S1, 0, L1 + ' ストレッタ', E)
    harm_fit(P, f + 30, f + 34, E, CANDS)
    E = []; entry(P, f + 34, 'S', S1, 0, L1, E); entry(P, f + 34, 'T', S2, 0, L2, E); entry(P, f + 36, 'A', S2, 0, L2, E); entry(P, f + 36, 'B', S1, 0, L1, E)
    harm_fit(P, f + 34, f + 38, E, CANDS)
    E = []; entry(P, f + 38, 'S', S1, 0, L1, E); entry(P, f + 40, 'A', S3, 0, L3, E); P.place('B', f + 38, [(4, 42)] * 4, 0, '属音の保続 (ファ#)')
    harm_fit(P, f + 38, f + 42, E, ['F#7', 'F#', 'Bm', 'Bm/D', 'D', 'C#m7b5'])
    E = []; entry(P, f + 42, 'B', augment(S1), 0, L1 + ' (拡大 ×2)', E); harm_fit(P, f + 42, f + 46, E, CANDS)
    for v in VOICES: P.rest_bars(v, f + 46, MAJ0)
    P.section(MAJ0, 'Fuga a tre soggetti — 録音が終わって', '3 つの主題を同時に重ねる三重フーガ → 2 度目の重なりの途中、%d 小節目の 2 拍目で楽譜が途切れる (Contrapunctus XIV のように) → 沈黙' % (MAJ0 + 6))
    E = []; entry(P, MAJ0, 'S', S1, 0, L1, E); entry(P, MAJ0, 'T', S2, 0, L2, E); entry(P, MAJ0, 'A', S3, 0, L3, E)
    entry(P, MAJ0 + 2, 'B', augment(S1), 0, L1 + ' (拡大)', E); entry(P, MAJ0 + 2, 'S', S2, 0, L2, E); entry(P, MAJ0 + 2, 'T', S3, 0, L3, E); entry(P, MAJ0 + 4, 'A', S1, 0, L1, E)
    harm_fit(P, MAJ0, TOTAL, E, CANDS, use_rec=False)
    for k in range(MAJ0, TOTAL): P.dyn[k] = 1.15
    for v in VOICES: P.rest_bars(v, MAJ0 + 6, TOTAL)
    return P

def post(P, events, ex):
    add('X', 0, 6, 47, 0.45, '弔鐘')
    add('REC', T_REC, REC['dur'], 0, 0.8, None, src=RECWAV, off=0.0, fin=0.02, fout=1.0, rid=R + '.wav', tag='9/24 08:53 — 表 (実音、加工なし)')
    # ×16 の層: 第 1 主題 ×4 を低く、2 拍ごとに息をするように (8 小節ごと)
    for n_ in range(6):
        t = (2 + 8 * n_) * BPB; lab = L1 + ' ×4 (骨組み、低く)' if n_ == 0 else None
        for d, m in augment(S1, 4):
            k = max(1, int(round(d / 2)))
            for i in range(k):
                amp = 1.0 if i == 0 else 0.6 + 0.25 * math.sin(math.pi * i / max(1, k - 1))
                for o, gg in ((-24, 1.0), (-12, 0.5)): pf(t + 2 * i, 2.0, m + o, 0.13 * gg * amp, lab if (lab and o == -24 and i == 0) else None, 'x16', rel=0.6)
                lab = None
            t += d
    # ×4 の層: 第 2 主題 ×4 と B-A-C-H ×4 が交互に、内声で小さく
    for j, (b0, subj, lab) in enumerate(((6, S2, L2 + ' ×4'), (14, S3, L3 + ' ×4'), (22, S2, L2 + ' ×4'), (30, S3, L3 + ' ×4'), (38, S2, L2 + ' ×4'), (46, S3, L3 + ' ×4'))):
        t = b0 * BPB; first = True
        for d, m in augment(subj, 4):
            pf(t, d + 0.2, m - 12, 0.1, lab if first else None, 'x4', rel=0.6); t += d; first = False
    if CUT is not None:                                                            # 途切れる
        for v in VOICES: events[v] = [(s, min(d, CUT - s), m, lab) for s, d, m, lab in events[v] if s < CUT]
        ex[:] = [e for e in ex if e['beat'] < CUT]
        for e in ex: e['dbeats'] = min(e['dbeats'], CUT - e['beat'])

META = {'style': 'recsampler', 'bank': BANK, 'rec_order': [R], 'piano_decay': 2.0, 'reverb': [5.0, 2.0, 0.42], 'pause_bar': MAJ0 + 5,
        'title': 'Requiem BADA — CIII · Canzone 08:53 sopra Contrapunctus', 'subtitle': '表: 9/24 08:53 の録音そのもの ／ 裏: XCVI (piano_solo_8x の Contrapunctus XIV) の 3 つの層をロ短調に移して融合 (♩=60, 4 分 7 秒)',
        'legend': ['PF', 'X'], 'vname': {'PF': '×16・×4 の層', 'X': '鐘'},
        'footer': ['表: 録音 (実音、加工なし) が 2 小節目から 3 分 22 秒 ／ 裏: ×16 = 主題 I ×4 の骨組み、×4 = 主題 II と B-A-C-H の ×4、×1 = 4 声のフーガ (提示・反行・ストレッタ・二重・保続・拡大) → 録音が終わると三重フーガ → 途切れる',
                   '音源は bank85p (9/28 の歌の音を除いたピアノだけ)。録音は加工しない。声なし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=103, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT)); from collections import Counter
    print('bars', d['nbars'], 'duration', d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
