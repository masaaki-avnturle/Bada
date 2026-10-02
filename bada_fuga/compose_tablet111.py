#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXI · Canzone 9/24 quattro in uno senza sospiri (CI に 9/24 の録音を融合して — 息のような音を消して)
  表: 9/24 のピアノの録音 4 本をそのまま順に (dip_breath.py で息のような所だけ 1〜6 kHz を下げ、ほかは加工なし):
    08:49 (3 分 33 秒、ヘ短調) → 08:53 (3 分 22 秒、ロ短調; CI の表) → 11:18 (2 分 36 秒、ヘ長調) → 11:23 (1 分 31 秒、ロ短調)
    (11:21 は声・シンセの混じった録音で、ピアノの音と分けられないので使わない)
  裏 (CI の 3 つの層を、それぞれの録音の実速に合わせて):
    第 1 部の層 (骨組み) : 採譜の音を小さく重ねる (2 拍ごとの息をする打ち直し)
    第 2 部の層 (Fuga)   : 各録音の主題の 4 声フーガ — 08:53 は CI の主題 ミ・ファ#・シ・ミ・ミ、ほかは採譜の最上声から作った 8 拍の主題 (compose_tablet.make_subject)。
                           提示 → 反行 → ストレッタ → 拡大 (短い録音では提示 → ストレッタ)。和音は録音のその時の和音に寄せる (共鳴)
    第 3 部の層 (Natalitia): 各録音の終わりが近づくと 1 拍ごとの鼓動・祝鐘・高いマントラ。最後の録音が終わるとロ長調の生誕祭 (08:53 と 11:23 の主題のストレッタ) → Coda
  音源は bank109 (立ち上がりが遅くふくらむ 1 音を clean_bank.py で外した表)。声なし
  使い方: python compose_tablet111.py <bank109.json> <wav のフォルダ (<rid>_clean.wav)> [score_tablet111.json]
"""
import sys, os, json, math
from compose import *
import compose

BANK = sys.argv[1]; WDIR = os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet111.json'
sys.argv = [sys.argv[0], BANK]
import compose_tablet as CT                                                                        # 採譜から主題を作る (excerpt, make_subject)
B = json.load(open(BANK)); RECS = B['recordings']
BPM = 60
SUBJ_0853 = [(1, 64), (3, 66), (1.5, 71), (1.5, 76), (1, 76)]
MIN_E = ['Em', 'Am', 'B', 'B7', 'G', 'C', 'D', 'F#m7b5', 'Am/C', 'Em/G', 'Cmaj7', 'Em7', 'Gmaj7', 'Esus4', 'A', 'Dsus4']
MAJ_B = ['B', 'E', 'F#', 'F#7', 'G#m', 'C#m', 'B/D#', 'E/G#', 'Emaj7', 'F#sus4']
def tr_list(lst, semis): return [transpose_h([[c]], semis)[0][0] for c in lst]
# (録音 id, 表示名, 主音, 長調か, 主題 (None なら採譜から), 和音の候補)
PLAN = [('20260924_084937', '08:49', 5, False, None, tr_list(MIN_E, 1)),
        ('20260924_085314', '08:53', 11, False, SUBJ_0853, tr_list(MIN_E, 7)),
        ('20260924_111846', '11:18', 5, True, None, tr_list(MAJ_B, 6)),
        ('20260924_112313', '11:23', 11, False, None, tr_list(MIN_E, 7))]
MAJ = {2: 3, 7: 8, 9: 10}                                                                           # ロ短調 → ロ長調
octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}; TOP = {'S': 86, 'A': 76, 'T': 69, 'B': 62}
extras = []; RH = []; SEG = []                                                                      # SEG: (rid, name, 開始拍, 開始小節, 終わりの小節, 主題, 候補, 長調か)
b = 2
for rid, name, tonic, major, subj, cands in PLAN:
    if subj is None:
        semis = ((tonic - 2) + 6) % 12 - 6 if not major else ((tonic - 5) + 6) % 12 - 6               # 短調は主音、長調は平行短調 (ニ短調に対して)
        t0, inside = CT.excerpt(rid, semis, 13.0); subj = [(d, m + semis) for d, m in CT.make_subject(inside, semis, BPM)]
    t_start = b * 4.0; end_bar = int(math.ceil((t_start + RECS[rid]['dur']) / 4.0))
    SEG.append((rid, name, t_start, b, end_bar, subj, cands, major)); b = end_bar + 2
MAJ0 = SEG[-1][4] + 1; TOTAL = MAJ0 + 8

def add(v, beat, dbeats, m, gain, label=None, **kw):
    extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
def pf(beat, dbeats, m, gain, label=None, layer='bb', rid=None, rel=0.5): add('PF', beat, dbeats, m, gain, label, rid=rid, rel=rel, layer=layer)
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

def fuga(P, f, subj, lab, cands, full=True):
    E = []
    for k, v in enumerate('ASBT'):
        entry(P, f + 2 * k, v, subj, 7 if k % 2 else 0, lab + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, f + 2 * k, f + 2 * k + 2)
    harm_fit(P, f, f + 8, E, cands)
    if full:
        E = []; entry(P, f + 8, 'S', invert(subj), 0, lab + ' (反行)', E); entry(P, f + 10, 'T', invert(subj), 0, lab + ' (反行)', E); harm_fit(P, f + 8, f + 12, E, cands); f += 4
    E = []
    for k, v in enumerate('ASTB'): entry(P, f + 8 + k, v, subj, 0, lab + ' ストレッタ' if k == 0 else None, E)
    harm_fit(P, f + 8, f + 14, E, cands)
    if full:
        E = []; entry(P, f + 14, 'B', augment(subj), 0, lab + ' (拡大 ×2)', E); entry(P, f + 16, 'S', subj, 0, lab, E); harm_fit(P, f + 14, f + 18, E, cands); return f + 18
    return f + 14

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.95
    for q in range(TOTAL * BPB):                                                                    # 和音は録音のその時の和音
        seg = max((s for s in SEG if s[2] <= q), key=lambda s: s[2], default=SEG[0]); rec = RECS[seg[0]]; cur = rec['segs'][0]['ch']; tr = q - seg[2]
        for s in rec['segs']:
            if s['t'] <= tr: cur = s['ch']
        RH.append(cur); P.harm[q] = cur
    for v in VOICES: P.rest_bars(v, 0, SEG[0][3])
    for i, (rid, name, t0, b0, b1, subj, cands, major) in enumerate(SEG):
        keyname = {5: 'ヘ', 11: 'ロ'}[PLAN[i][2]] + ('長調' if major else '短調')
        P.section(b0, '表 %d: 9/24 %s の録音 (%s、息の所だけ下げて) + 骨組み' % (i + 1, name, keyname), '弔鐘 → 録音そのもの — 裏で採譜の骨組みが小さく息をする')
        for v in VOICES: P.rest_bars(v, b0, b0 + 4)
        full = (b1 - b0) >= 34
        P.section(b0 + 4, '裏: %s の主題のフーガ' % name, '主題 %s の 4 声フーガ: %s — 和音は録音のその時の和音に寄せて (共鳴)' % (' '.join(name_of(m) for _, m in subj), '提示 → 反行 → ストレッタ → 拡大' if full else '提示 → ストレッタ'))
        e = fuga(P, b0 + 4, subj, '主題 %s' % name, cands, full)
        nat = max(e, b1 - 14)
        for v in VOICES: P.rest_bars(v, e, b1 + 2 if i + 1 < len(SEG) else MAJ0)
        P.section(nat, '裏: 鼓動・祝鐘・マントラ (%s の終わりが近づく)' % name, '1 拍ごとの鼓動と高いマントラ' + ('' if i + 1 < len(SEG) else ' — 録音が終わるとロ長調へ'))
        SEG[i] = SEG[i] + (nat,)
    P.section(MAJ0, 'Natalitia (ロ長調) — 08:53 と 11:23 の主題のストレッタ', '2 つの主題がロ長調で重なり、頂点 → Coda')
    sA, sB = SEG[1][5], SEG[3][5]; E = []
    for k, v in enumerate('SATB'): entry(P, MAJ0 + k, v, sA if k % 2 == 0 else sB, 0, ('主題 08:53' if k == 0 else '主題 11:23') if k < 2 else None, E)
    entry(P, MAJ0 + 4, 'B', augment(sA), 0, '主題 08:53 (拡大 ×2)', E); entry(P, MAJ0 + 4, 'S', sA, 12, None, E); entry(P, MAJ0 + 5, 'A', sB, 0, None, E)
    harm_fit(P, MAJ0, TOTAL - 2, E, MAJ_B)
    for bb in range(TOTAL - 2, TOTAL): P.set_harm(bb, 'B'); P.hold.add(bb)
    P.place('S', TOTAL - 2, [(4, 83)] * 2, 0, 'シ (頂点)'); P.place('B', TOTAL - 2, [(4, 47)] * 2, 0, '')
    for k in range(MAJ0, TOTAL): P.dyn[k] = 1.05 + 0.15 * min(1.0, (k - MAJ0) / 4.0) - (0.25 if k >= TOTAL - 2 else 0)
    return P

def post(P, events, ex):
    for i, (rid, name, t0, b0, b1, subj, cands, major, nat) in enumerate(SEG):
        add('X', t0 - 8, 6, 47 if i % 2 else 52, 0.45 if i == 0 else 0.35, '弔鐘' if i == 0 else None)
        add('REC', t0, RECS[rid]['dur'], 0, 0.8, None, src=os.path.join(WDIR, rid + '_clean.wav'), off=0.0, fin=0.02, fout=1.0, rid=rid + '.wav', tag='9/24 %s — 表 (息の所だけ下げて)' % name)
        first = True
        for s in RECS[rid]['segs']:                                                                  # 第 1 部の層
            bb0 = t0 + s['t']
            for m in s['m']:
                step = 2.0; n_ = max(1, int(round(s['d'] / step)))
                for j in range(n_):
                    amp = 1.0 if j == 0 else 0.55
                    pf(bb0 + j * step, min(step, s['d'] - j * step) + 0.2, m, 0.11 * amp * (1.2 if m < 48 else 1.0), '採譜 (骨組み、小さく)' if (first and i == 0) else None, 'bb', rid=rid); first = False
        last = i + 1 == len(SEG); nat1 = TOTAL if last else b1                                         # 第 3 部の層
        for bar in range(nat, nat1):
            k = bar - nat; g = 0.08 + 0.14 * min(1.0, k / 14.0)
            cc = chord(P.harm[bar * BPB]); root = 48 + cc['root']
            tones = [root - 12, root] + [m for m in range(55, 67) if m % 12 in cc['pcs']][:3]
            step = 1.0 if bar < nat1 - 2 else 2.0
            for j in range(int(BPB / step)):
                for m in tones: pf(bar * BPB + j * step, step, m, g * (1.0 if j == 0 else 0.75) * (1.25 if m < 48 else 0.8), '鼓動 (1 拍ごと)' if (k == 0 and j == 0 and m == root and i == 0) else None, 'pulse', rid=rid)
            if k % 4 == 0: add('X', bar * BPB, 6, 64 + 12 * ((k // 4) % 2), 0.3 + 0.3 * min(1.0, k / 14.0), '祝鐘' if (k == 0 and i == 0) else None)
            if k % 2 == 0 and bar < nat1 - 2:
                t = bar * BPB; lab = '高いマントラ' if (k == 0 and i == 0) else None
                for d, m in subj: pf(t, d, (majify(m) if (last and bar >= MAJ0) else m) + 24, 0.12 + 0.1 * min(1.0, k / 14.0), lab, 'mantra', rid=rid, rel=0.8); t += d; lab = None
    add('X', (TOTAL - 1) * BPB, 8, 71, 0.5, None); add('X', (TOTAL - 1) * BPB + 2, 8, 59, 0.4, None)
    for v in VOICES: events[v] = [(s, d, majify(m) if s >= MAJ0 * BPB else m, lab) for s, d, m, lab in events[v]]

META = {'style': 'recsampler', 'bank': BANK, 'rec_order': [p[0] for p in PLAN], 'piano_decay': 2.0, 'reverb': [5.0, 2.0, 0.42],
        'title': 'Requiem BADA — CXI · Canzone 9/24 quattro in uno senza sospiri',
        'subtitle': 'CI に 9/24 の録音を融合して、息のような音を消して — 表: 08:49 → 08:53 → 11:18 → 11:23 の録音 (息の所だけ下げて) ／ 裏: 骨組み + 各録音の主題のフーガ + 生誕祭 (ヘ短調 → ロ短調 → ヘ長調 → ロ短調 → ロ長調, ♩=60)',
        'legend': ['PF', 'X'], 'vname': {'PF': '裏の層', 'X': '鐘'},
        'footer': ['表: 9/24 の 4 本の録音 (実音) を順に ／ 裏: 第 1 部 = 採譜の骨組み (小さく)、第 2 部 = 各録音の主題の 4 声フーガ、第 3 部 = 鼓動・祝鐘・マントラ → 最後の録音が終わるとロ長調の生誕祭',
                   '音源は bank109 (立ち上がりが速く減衰する 1 音だけ)。録音は息のような所だけ 1〜6 kHz を下げ、ほかは加工なし。11:21 (声・シンセの混じった録音) は使わない。声なし。']}

if __name__ == '__main__':
    for s in SEG: print(s[1], 'bars', s[3], '-', s[4], 'subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in s[5]))
    compose.main(OUT, seed=111, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT)); from collections import Counter
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] = d['meta']['subtitle'].replace('♩=60)', '♩=60, %d 分 %d 秒)' % (h, rem + 7)); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration', d['duration'], 'MAJ0', MAJ0, 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
