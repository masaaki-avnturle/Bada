#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions XCVII · Praeludium, Fuga e Requiem XVI — Natalitia (9/24 08:53 を 16 倍に — 規律的に、洗脳的に、フーガでありレクイエムであり、
  前奏曲と間奏曲をはさみ、終焉が生誕祭へ盛り上がる)
  骨組み (×16、規律・洗脳): 9/24 08:53 の録音 (3 分 22 秒、ロ短調) を 16 倍に — 採譜 (bank85) の音を 16 倍に伸ばし、2 拍ごと (低い音は 4 拍ごと) に息をするように打ち直す (♩=60、止まらない)。
    その下で、録音そのものを速さだけ 16 倍に引き伸ばした音 (位相ボコーダ、高さは変えない) が 54 分の霧のように流れる。和音は録音の採譜のまま 16 倍に
  形式 (848 小節 = 56 分 32 秒):
    Praeludium (0〜48)                     骨組みと霧だけ — 弔鐘ひとつから
    ×5 [ Fuga (32) → Interludium (32) → Requiem (64) ]  (48〜688)
      Fuga        08:53 の主題 (ミ・ファ#・シ・ミ・ミ) の 4 声フーガ (提示 → エピソード → 反行 → ストレッタ → 属音の保続 → 低音の拡大) — 回を重ねるごとに強く
      Interludium 録音を 4 倍に引き伸ばした音 (同じ所を 4 倍の速さで — メンスーラ・カノン) が骨組みの上を通る
      Requiem     採譜の和音のコラール (4 拍ごと) と、主題の 4 倍の拡大がテノールで 4 回。頭に弔鐘
    Finis (688〜760)                       終焉 — 骨組みが薄れ、霧だけが残り、低い シ の保続へ
    Natalitia (760〜840)                   生誕祭 — ロ長調へ。主題のストレッタが 4 声で 2 小節ごとに上へ上へ、1 拍ごとの鼓動、祝鐘、高い ミ・ファ#・シ・ミ・ミ のマントラ、ロ長調の和音で頂点
    Coda (840〜848)                        ロ長調の和音と鐘が残る
  音はすべて 08:53 の録音から切り出したピアノの 1 音 (bank85) と、録音そのものを引き伸ばした音、鐘。声なし。
  使い方: python compose_tablet97.py <bank85.json> <rec0853_x16.wav> <rec0853_x4.wav> [score_tablet97.json] → python render_long.py score_tablet97.json out97
"""
import sys, os, json, math
from compose import *
import compose

BANK = sys.argv[1]; X16, X4 = os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet97.json'
R = '20260924_085314'; REC = json.load(open(BANK))['recordings'][R]
T0 = 2.4                                                                       # 録音の頭の無音 (2.4 秒) は飛ばす
BPM, K = 60, 16
SUBJ = [(1, 64), (3, 66), (1.5, 71), (1.5, 76), (1, 76)]                       # ミ・ファ#・シ・ミ・ミ (8 拍、ロ短調)
CANDS_M = ['Bm', 'Em', 'F#', 'F#7', 'D', 'G', 'A', 'C#m7b5', 'Em/G', 'Bm/D']
CANDS_J = ['B', 'E', 'F#', 'F#7', 'G#m', 'C#m', 'D#m', 'B/D#', 'E/G#']
PRAE, FUGA, INTER, REQ, CYC = 48, 32, 32, 64, 5
FINIS0 = PRAE + CYC * (FUGA + INTER + REQ); NATAL0 = FINIS0 + 72; CODA0 = NATAL0 + 80; TOTAL = CODA0 + 8
NB_REC = int(math.ceil((REC['dur'] - T0) * K / 4.0))
octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}; TOP = {'S': 86, 'A': 76, 'T': 69, 'B': 62}
extras = []; SEC = {}                                                          # bar -> (kind, cycle)

def add(v, beat, dbeats, m, gain, label=None, **kw):
    extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def pf(beat, dbeats, m, gain, label=None, layer='bb', rel=0.6):
    add('PF', beat, dbeats, m, gain, label, rid=R, rel=rel, layer=layer)

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
    tr = fit(v, mat, octs[v] + tr0)
    P.place(v, bar, mat, tr, label, beat=beat); E.append((bar * BPB + beat, [(d, m + tr) for d, m in mat]))

def invert(mat): m0 = mat[0][1]; return [(d, 2 * m0 - m) for d, m in mat]
def augment(mat, k=2): return [(k * d, m) for d, m in mat]

def fuga(P, f, c):
    """08:53 の主題の 4 声フーガ 32 小節 (c 回目)"""
    lab = '主題 08:53'; E = []
    for k, v in enumerate('ASBT'):
        entry(P, f + 2 * k, v, SUBJ, 7 if k % 2 else 0, lab + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, f + 2 * k, f + 2 * k + 2)
    harm_from_entries(P, f, f + 8, E, CANDS_M)
    P.set_harms(f + 8, [['Em', 'Em', 'A7', 'A7'], ['D', 'D', 'F#7', 'F#7']])
    E = []; entry(P, f + 10, 'S', invert(SUBJ), 0, lab + ' (反行)', E); entry(P, f + 12, 'T', invert(SUBJ), 0, lab + ' (反行)', E)
    harm_from_entries(P, f + 10, f + 14, E, CANDS_M)
    P.set_harms(f + 14, [['G', 'G', 'C#m7b5', 'C#m7b5'], ['F#7', 'F#7', 'F#7', 'F#7']])
    E = []
    for k, v in enumerate('ASTB'): entry(P, f + 16 + k, v, SUBJ, 0, lab + ' ストレッタ', E)
    harm_from_entries(P, f + 16, f + 22, E, CANDS_M)
    E = []; entry(P, f + 22, 'S', SUBJ, 0, lab, E); entry(P, f + 24, 'A', SUBJ, 7, lab + ' 答唱', E)
    P.place('B', f + 22, [(4, 42)] * 4, 0, '属音の保続 (ファ#)')                   # ファ# の保続 4 小節
    P.set_harms(f + 22, [['F#7'] * 4] * 4)
    E = []; entry(P, f + 26, 'B', augment(SUBJ), 0, lab + ' (拡大 ×2)', E)
    harm_from_entries(P, f + 26, f + 30, E, CANDS_M)
    P.set_harms(f + 30, [['Bm'] * 4, ['Bm'] * 4]); P.hold.update({f + 30, f + 31})
    for k in range(FUGA): P.dyn[f + k] = 0.8 + 0.12 * c + (0.15 if 16 <= k < 26 else 0.0)

def natalitia(P, f):
    """生誕祭 (ロ長調): 主題のストレッタが 2 小節ごとに上へ、最後は拡大と和音"""
    lab = '主題 08:53 — 生誕祭 (ロ長調)'; E = []
    order = 'BTAS'
    for k in range(24):                                                            # 760〜808: 2 小節ごとに入る
        v = order[k % 4]; tr = 12 * min(2, k // 8) if v in 'SA' else 12 * min(1, k // 12)
        entry(P, f + 2 * k, v, SUBJ, tr, lab if k % 4 == 0 else None, E)
    harm_from_entries(P, f, f + 48, E, CANDS_J)
    E = []
    entry(P, f + 48, 'S', augment(SUBJ), 12, lab + ' (拡大 ×2、頂点)', E); entry(P, f + 48, 'B', augment(SUBJ), 0, None, E)
    entry(P, f + 50, 'A', SUBJ, 0, None, E); entry(P, f + 52, 'T', SUBJ, 0, None, E); entry(P, f + 54, 'A', SUBJ, 12, None, E)
    entry(P, f + 56, 'S', augment(SUBJ), 12, lab + ' (拡大 ×2)', E); entry(P, f + 56, 'T', augment(SUBJ), 0, None, E)
    entry(P, f + 60, 'A', SUBJ, 0, None, E); entry(P, f + 62, 'B', SUBJ, 0, None, E)
    harm_from_entries(P, f + 48, f + 64, E, CANDS_J)
    for b in range(f + 64, f + 72): P.set_harm(b, ['B', 'B', 'E', 'E'] if (b - f) % 4 == 0 else ['F#7', 'F#7', 'B', 'B'])
    entry(P, f + 64, 'S', SUBJ, 12, lab + ' (最後)', E); entry(P, f + 66, 'A', SUBJ, 12, None, E); entry(P, f + 68, 'T', SUBJ, 0, None, E); entry(P, f + 70, 'B', SUBJ, 0, None, E)
    for b in range(f + 72, TOTAL): P.set_harm(b, 'B'); P.hold.add(b)
    P.place('S', f + 72, [(4, 88), (4, 88)], 0, 'シ (頂点)'); P.place('B', f + 72, [(4, 35), (4, 35)], 0, None)
    for k in range(80): P.dyn[f + k] = 0.9 + 0.35 * min(1.0, k / 64.0)
    for k in range(CODA0, TOTAL): P.dyn[k] = 1.3 - 0.1 * (k - CODA0)

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.8
    # 骨組みの和音 (録音の採譜 ×16)
    cur = 'Bm'; segs = REC['segs']
    for q in range(TOTAL * BPB):
        tr = q / float(K) + T0
        for s in segs:
            if s['t'] <= tr: cur = s['ch']
        P.harm[q] = cur if q < NB_REC * BPB else 'Bm'
    b = 0
    P.section(0, 'Praeludium — 骨組みと霧', '08:53 の採譜を 16 倍に伸ばして 2 拍ごとに打ち直す (規律) — 下で録音そのものを 16 倍に引き伸ばした霧 — 弔鐘ひとつから')
    for v in VOICES: P.rest_bars(v, 0, PRAE)
    for k in range(PRAE): SEC[k] = ('prae', 0)
    b = PRAE
    for c in range(CYC):
        P.section(b, 'Fuga %s — 主題 08:53 の 4 声フーガ' % 'I II III IV V'.split()[c], '提示 (ミ・ファ#・シ・ミ・ミ) → エピソード → 反行 → ストレッタ → ファ# の保続 → 低音の拡大 — 骨組みは下で小さく、%d 回目は前より強く' % (c + 1))
        fuga(P, b, c)
        for k in range(FUGA): SEC[b + k] = ('fuga', c)
        b += FUGA
        P.section(b, 'Interludium %s — 4 倍の録音' % 'I II III IV V'.split()[c], '録音の同じ所を 4 倍の速さで引き伸ばした音が骨組み (16 倍) の上を通る — メンスーラ・カノン')
        for v in VOICES: P.rest_bars(v, b, b + INTER)
        for k in range(INTER): SEC[b + k] = ('inter', c)
        b += INTER
        P.section(b, 'Requiem %s — コラールと拡大' % 'I II III IV V'.split()[c], '弔鐘 → 採譜の和音のコラール (4 拍ごと) と、主題の 4 倍の拡大がテノールで 4 回 — 骨組みは息をするように')
        for v in VOICES: P.rest_bars(v, b, b + REQ)
        for k in range(REQ): SEC[b + k] = ('req', c)
        b += REQ
    assert b == FINIS0
    P.section(b, 'Finis — 終焉', '骨組みが薄れて、霧だけが残り、低い シ の保続へ — 録音の終わりが 16 倍にゆっくり近づく')
    for v in VOICES: P.rest_bars(v, b, NATAL0)
    for k in range(FINIS0, NATAL0): SEC[k] = ('finis', 0)
    P.section(NATAL0, 'Natalitia — 生誕祭 (ロ長調)', '終焉が生誕祭に: 主題のストレッタが 4 声で 2 小節ごとに上へ上へ、1 拍ごとの鼓動、祝鐘、高い ミ・ファ#・シ・ミ・ミ のマントラ、ロ長調の和音で頂点')
    natalitia(P, NATAL0)
    for k in range(NATAL0, TOTAL): SEC[k] = ('natal', 0)
    P.section(CODA0, 'Coda — 鐘', 'ロ長調の和音と祝鐘が残って消える')
    return P

def post(P, events, ex):
    MAJ = {2: 3, 7: 8, 9: 10}                                                     # ロ長調へ (レ→レ#、ソ→ソ#、ラ→ラ#)
    def gsec(bar):
        kind, c = SEC.get(bar, ('coda', 0))
        if kind == 'prae': return 0.55 + 0.45 * min(1.0, bar / 16.0)
        if kind == 'fuga': return 0.5
        if kind == 'inter': return 0.8
        if kind == 'req': return 1.0
        if kind == 'finis': return max(0.3, 1.0 - 0.7 * (bar - FINIS0) / 72.0)
        return 0.0
    # 骨組み: 採譜 ×16、2 拍ごと (低音は 4 拍ごと) に息をするように打ち直す
    for s in REC['segs']:
        b0, D = K * (s['t'] - T0), K * s['d']
        for m in s['m']:
            step = 4.0 if m < 48 else 2.0; n_ = max(1, int(round(D / step)))
            for i in range(n_):
                bt = b0 + i * step; bar = int(bt // BPB)
                if bar >= NATAL0: break
                amp = 1.0 if i == 0 else 0.6 + 0.25 * math.sin(math.pi * i / max(1, n_ - 1))
                g = 0.3 * gsec(bar) * amp
                if g > 0.005: pf(bt, step, m, g, None, 'bb')
    # 霧: 録音を 16 倍に引き伸ばした音 (区分ごとの大きさで)
    GR = {'prae': 0.5, 'fuga': 0.22, 'inter': 0.4, 'req': 0.5, 'finis': 0.5}
    b = 0
    while b < NATAL0:
        kind = SEC[b][0]; e = b
        while e < NATAL0 and SEC[e][0] == kind: e += 1
        if kind == 'finis':
            add('REC', b * BPB, (e - b) * BPB, 0, GR[kind], None, src=X16, off=b * 4.0 + K * T0, fin=0.5, fout=60.0, rid='rec0853_x16', tag='08:53 を 16 倍に引き伸ばした霧 — 終焉')
        else:
            add('REC', b * BPB, (e - b) * BPB, 0, GR[kind] * (1.0 if kind != 'prae' else 1.0), None, src=X16, off=b * 4.0 + K * T0, fin=(16.0 if b == 0 else 0.5), fout=0.5, rid='rec0853_x16',
                tag='08:53 を 16 倍に引き伸ばした霧')
        b = e
    # 間奏曲: 4 倍の録音 (同じ所を 4 倍の速さで)
    for bar, (kind, c) in sorted(SEC.items()):
        if kind == 'inter' and SEC.get(bar - 1, ('',))[0] != 'inter':
            add('REC', bar * BPB, INTER * BPB, 0, 0.45, None, src=X4, off=bar * 1.0 + 4 * T0, fin=3.0, fout=6.0, rid='rec0853_x4', tag='08:53 を 4 倍に引き伸ばして — 同じ所を 4 倍の速さで')
    # レクイエム: 弔鐘、コラール (4 拍ごと)、主題の 4 倍の拡大 (テノール)
    for bar, (kind, c) in sorted(SEC.items()):
        if kind != 'req': continue
        first = SEC.get(bar - 1, ('',))[0] != 'req'
        if first: add('X', bar * BPB, 6, 47, 0.7, '弔鐘')
        cc = chord(P.harm[bar * BPB]); root = 48 + cc['root']
        tones = sorted({root - 12, root} | {m for m in range(52, 72) if m % 12 in cc['pcs']})[:5]
        for m in tones: pf(bar * BPB, 4.0, m, 0.14 * (1.0 if m >= 52 else 1.3), None, 'chorale', rel=1.0)
        k = bar - [x for x in sorted(SEC) if SEC[x] == ('req', c)][0]
        if k % 16 == 0:
            t = bar * BPB; lab = '主題 08:53 ×4 (テノール)'
            for d, m in augment(SUBJ, 4):
                n_ = int(round(d / 2))
                for i in range(n_):
                    amp = 1.0 if i == 0 else 0.6 + 0.25 * math.sin(math.pi * i / max(1, n_ - 1))
                    pf(t + 2 * i, 2.0, m - 12, 0.3 * amp, lab if (i == 0 and lab) else None, 'x4'); lab = None
                t += d
    # 終焉: 低い シ の保続 (4 拍ごと)
    for bar in range(NATAL0 - 16, NATAL0): pf(bar * BPB, 4.0, 35, 0.22, '低い シ の保続' if bar == NATAL0 - 16 else None, 'ped', rel=1.2)
    # 生誕祭: 1 拍ごとの鼓動 (ロ長調の和音)、祝鐘、高いマントラ
    for bar in range(NATAL0, TOTAL):
        k = bar - NATAL0; g = 0.08 + 0.12 * min(1.0, k / 64.0)
        cc = chord(P.harm[bar * BPB]); root = 48 + cc['root']
        tones = [root - 12, root] + [m for m in range(55, 67) if m % 12 in cc['pcs']][:3]
        step = 1.0 if bar < CODA0 else 2.0
        for i in range(int(BPB / step)):
            amp = 1.0 if i == 0 else 0.75
            for m in tones: pf(bar * BPB + i * step, step, m, g * amp * (1.25 if m < 48 else 0.8), None, 'pulse', rel=0.5)
        if k % 4 == 0: add('X', bar * BPB, 6, 59 + 12 * ((k // 4) % 3), 0.3 + 0.3 * min(1.0, k / 64.0), '祝鐘' if k == 0 else None)
        if k % 2 == 0 and k >= 16:
            t = bar * BPB; lab = '高いマントラ ミ・ファ#・シ・ミ・ミ' if k == 16 else None
            for d, m in SUBJ: pf(t, d, m + 24, 0.12 + 0.1 * min(1.0, k / 64.0), lab, 'mantra', rel=0.8); t += d; lab = None
    for bar in range(CODA0, TOTAL): add('X', bar * BPB, 8, 71 if bar % 2 else 59, 0.5 - 0.05 * (bar - CODA0), None)
    # 生誕祭の 4 声はロ長調 (生成された音の短 3 度・短 6 度・短 7 度を上げる)
    for v in VOICES:
        events[v] = [(s, d, (m - m % 12 + MAJ[m % 12]) if (s >= NATAL0 * BPB and m % 12 in MAJ) else m, lab) for s, d, m, lab in events[v]]

META = {
    'style': 'recsampler', 'bank': BANK, 'rec_order': [R], 'piano_decay': 2.0, 'reverb': [5.5, 2.2, 0.44], 'fps': 15, 'fixed_peak': 1.0,
    'title': 'Requiem BADA — XCVII · Natalitia XVI',
    'subtitle': '9/24 08:53 を 16 倍に — 規律的に、洗脳的に。フーガでありレクイエムであり、前奏曲と間奏曲をはさみ、終焉が生誕祭 (ロ長調) へ (♩=60, 56 分 32 秒)',
    'legend': ['PF', 'X'], 'vname': {'PF': '骨組み ×16 / 層', 'X': '鐘'},
    'footer': ['Praeludium → ×5 [Fuga (主題 08:53 の 4 声フーガ) → Interludium (4 倍の録音) → Requiem (コラール、主題 ×4、弔鐘)] → Finis (終焉) → Natalitia (生誕祭、ロ長調) → Coda',
               '骨組み: 08:53 の採譜を 16 倍に伸ばして 2 拍ごとに打ち直す。霧: 録音そのものを 16 倍に引き伸ばした音。音はすべて 08:53 のピアノの 1 音と鐘。声なし。'],
}

if __name__ == '__main__':
    compose.main(OUT, seed=97, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT)); from collections import Counter
    print('bars', d['nbars'], 'duration %d:%02d:%02d' % (d['duration'] // 3600, d['duration'] % 3600 // 60, d['duration'] % 60), 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
