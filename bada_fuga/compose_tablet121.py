#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXXI · Ninna nanna in fuga, R&B e jazz (バッハのフーガを 10/12 で作り換え、バックを CXVII の形で — R&B とジャズにクラシックの流れる、眠りへの曲)
  表: バッハ (平均律) のような 4 声のフーガ — 主題は 10/12 06:27 の最上声から (compose_tablet.make_subject)。ピアノの 1 音
  バック (CXVII の形): 眠りの 4 段階、テンポは 66 → 44 へゆっくり落ち、鼓動 (13:04 の低い音) も一緒に。13:19 の音の共鳴がその時の和音を保つ。実音のピアノを主体に:
    I.   Rilassamento くつろぎ   10/12 06:27 の実音 (変ロ短調)   フーガの提示 (A → S → B → T) → 対提示。ジャズの和音 (7th・9th、スウィング) とウォーキング・ベースが中音域で
    II.  Calore 暖まり           9/24 11:18 の実音 (ヘ長調)      主題がヘ長調の和音の上で (反行とストレッタ)、R&B の和音は 9th を重ねて暖かく。LXXXVI の Sweet
    III. Raffreddamento 冷え     9/24 08:49 の実音 (ヘ短調)      主題の拡大 (×2 → ×4) が下りていく、和音は 1 拍目だけ、LXXXVI の Flower、LXXXIX の伸ばした主題が遠くで。♩=66 → 52
    IV.  Sonno 眠り              10/12 06:30 の実音 (小さく)     late_bach_fuga_8x が遠くで、主題は 8 倍に低く、鼓動は 2 拍に 1 つになって消える。♩=52 → 44。最後は変ロ長調の共鳴と B-A-D-A
  和音は、主題の音を含み、録音のその時の和音に近いものを選ぶ (harm_fit、共鳴)。弔鐘・祝鐘なし、ドラムなし、声なし
  使い方: python compose_tablet121.py <bank1012.json> <bank112.json> <bank109.json> <score_tablet89.json> <score_tablet86.json> <wav のフォルダ> [score_tablet121.json]
"""
import sys, os, json, math
BANK1012, BANK112, BANK109, SCORE89, SCORE86, WDIR = sys.argv[1:7]; WDIR = os.path.abspath(WDIR); OUT = sys.argv[7] if len(sys.argv) > 7 else 'score_tablet121.json'
sys.argv = [sys.argv[0], BANK1012]
import compose_tablet as CT
import compose_heart as H
from compose import *
import compose
from clean_bank import measure

B1012, B112, B109 = json.load(open(BANK1012)), json.load(open(BANK112)), json.load(open(BANK109)); S89, S86 = json.load(open(SCORE89)), json.load(open(SCORE86))
RECS = dict(B109['recordings']); RECS.update(B112['recordings']); RECS.update(B1012['recordings'])
R27, R30, R18, R49 = '20261012_062753', '20261012_063057', '20260924_111846', '20260924_084937'
LOW = '20260925_130431'; PSRC = R27; RS = '20261003_131932'
KEY = {R27: 10, R30: 10, R18: 5, R49: 5}; MAJOR = {R18}; NAME = {R27: '10/12 06:27', R30: '10/12 06:30', R18: '9/24 11:18', R49: '9/24 08:49'}
RECL = [R27, R18, R49, R30]; TP0, TP1 = 66, 44
def shift(a, b): return ((b - a) + 6) % 12 - 6
TR = -4; _t, _in = CT.excerpt(R27, TR, 13.0); SUBJ = [(d, m + TR) for d, m in CT.make_subject(_in, TR, 60)]       # 主題 (変ロ短調)
MIN_E = ['Em', 'Am', 'B', 'B7', 'G', 'C', 'D', 'F#m7b5', 'Am/C', 'Em/G', 'Cmaj7', 'Em7', 'Gmaj7', 'Esus4', 'A', 'Dsus4']
MAJ_B = ['B', 'E', 'F#', 'F#7', 'G#m', 'C#m', 'B/D#', 'E/G#', 'Emaj7', 'F#sus4']
def tr_list(lst, s): return [transpose_h([[c]], s)[0][0] for c in lst]
CANDS = {R27: tr_list(MIN_E, 6), R30: tr_list(MIN_E, 6), R18: tr_list(MAJ_B, 6), R49: tr_list(MIN_E, 1)}
STAGE = []; b = 2
for rid in RECL: STAGE.append(b); b += int(math.ceil(RECS[rid]['dur'] / (240.0 / (TP0 if len(STAGE) < 3 else 52)))) + 2
I0, II0, III0, IV0 = STAGE; TOTAL = b + 8
def tempo_of(bar):
    if bar < III0: return float(TP0)
    if bar < IV0: return TP0 - (TP0 - 52) * (bar - III0) / float(IV0 - III0)
    return 52 - (52 - TP1) * min(1.0, (bar - IV0) / float(max(1, TOTAL - IV0 - 8)))
def beats_for(beat0, secs):
    b = beat0; left = secs
    while left > 0 and b < TOTAL * BPB:
        sb = 60.0 / tempo_of(int(b // BPB))
        if left < sb: return b + left / sb - beat0
        left -= sb; b += 1
    return b - beat0
octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}; TOP = {'S': 86, 'A': 76, 'T': 69, 'B': 62}
extras = []; RH = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
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
def rest_others(P, b0, b1, keep):
    for v in VOICES:
        if v not in keep: P.rest_bars(v, b0, b1)

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = tempo_of(k); P.dyn[k] = 1.0
    for q in range(TOTAL * BPB):
        cur = None
        for i, rid in enumerate(RECL):
            rec = RECS[rid]; t0 = STAGE[i] * BPB; db = beats_for(t0, rec['dur'])
            if t0 <= q < t0 + db:
                frac = (q - t0) / db * rec['dur']; cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
        if cur is None:
            i = max([k for k in range(4) if q >= STAGE[k] * BPB] or [0]); N = 'C C# D D# E F F# G G# A A# B'.split()
            cur = N[KEY[RECL[i]]] + ('' if (RECL[i] in MAJOR or q >= (TOTAL - 8) * BPB) else 'm')
        RH.append(cur); P.harm[q] = cur
    sub = {rid: [(d, m + shift(10, KEY[rid])) for d, m in SUBJ] for rid in RECL}
    rest_others(P, 0, I0 + 2, '')
    # ---- I. くつろぎ: 提示 → 対提示 (ジャズの和音とウォーキング・ベース)
    b0, b1 = I0, II0; s = sub[R27]
    P.section(0, 'I. Rilassamento — くつろぎ (10/12 06:27, ♩=66)', '06:27 の実音 — 主題 %s (06:27 の最上声から) の 4 声の提示 → 対提示。ジャズの 7th・9th の和音 (スウィング) とウォーキング・ベースが中音域で、鼓動 ♩=66' % ' '.join(name_of(m) for _, m in SUBJ))
    E = []
    for k, v in enumerate('ASBT'):
        entry(P, b0 + 2 + 4 * k, v, s, 7 if k % 2 else 0, '主題' + (' 答唱' if k % 2 else ''), E)
        for w in 'ASBT'[k + 1:]: P.rest_bars(w, b0 + 2 + 4 * k, b0 + 6 + 4 * k)
    harm_fit(P, b0, b0 + 18, E, CANDS[R27]); f = b0 + 18; E = []
    for k, v in enumerate('TBSA'):
        if f + 4 * k + 4 > b1 - 2: break
        entry(P, f + 4 * k, v, s, 7 if k % 2 else 0, '主題 (対提示)' if k == 0 else None, E)
        for w in VOICES:
            if w != v: P.rest_bars(w, f + 4 * k, f + 4 * k + 4)
    harm_fit(P, f, b1, E, CANDS[R27]); rest_others(P, f + 16, b1, '')
    # ---- II. 暖まり: ヘ長調の上で反行とストレッタ
    b0, b1 = II0, III0; s = sub[R18]
    P.section(b0, 'II. Calore — 暖まり (9/24 11:18, ヘ長調, ♩=66)', '11:18 の実音 (ヘ長調) — 主題と反行が長調の和音の上で、ストレッタ。R&B の和音は 9th を重ねて暖かく、LXXXVI の Sweet が小さく')
    E = []; k = 0
    for b in range(b0 + 2, b1 - 4, 6):
        v = 'SATB'[k % 4]; mat = s if k % 2 == 0 else invert(s); entry(P, b, v, mat, 0, ('主題 (長調の上で)' if k == 0 else '主題 (反行)' if k == 1 else None), E)
        if k >= 2: entry(P, b + 1, 'TSAB'[k % 4], s, 0, 'ストレッタ' if k == 2 else None, E)
        for w in VOICES:
            if w != v and not (k >= 2 and w == 'TSAB'[k % 4]): P.rest_bars(w, b, b + 6)
        k += 1
    harm_fit(P, b0, b1, E, CANDS[R18]); rest_others(P, b0, b0 + 2, ''); rest_others(P, b, b1, '')
    # ---- III. 冷え: 拡大が下りていく
    b0, b1 = III0, IV0; s = sub[R49]
    P.section(b0, 'III. Raffreddamento — 冷え (9/24 08:49, ヘ短調, ♩=66 → 52)', '08:49 の実音 (ヘ短調) — 主題の拡大 (×2 → ×4) がアルト → テノール → バスと下りていく。和音は 1 拍目だけ、LXXXVI の Flower、LXXXIX の伸ばした主題が遠くで。鼓動がゆっくりに')
    E = []; a2, a4 = augment(s), augment(s, 4)
    entry(P, b0 + 2, 'A', a2, 0, '主題 (拡大 ×2)', E); entry(P, b0 + 10, 'T', a2, 0, None, E); entry(P, b0 + 18, 'B', a4, 0, '主題 (拡大 ×4)', E); entry(P, b0 + 34, 'T', a4, 0, None, E)
    rest_others(P, b0, b0 + 2, ''); rest_others(P, b0 + 2, b0 + 10, 'A'); rest_others(P, b0 + 10, b0 + 18, 'T'); rest_others(P, b0 + 18, b0 + 34, 'B'); rest_others(P, b0 + 34, b0 + 50, 'T'); rest_others(P, b0 + 50, b1, '')
    harm_fit(P, b0, b1, E, CANDS[R49])
    # ---- IV. 眠り: 8 倍に低く
    b0, b1 = IV0, TOTAL - 8; s = sub[R30]
    P.section(b0, 'IV. Sonno — 眠り (10/12 06:30, ♩=52 → 44)', '06:30 の実音を小さく、late_bach_fuga_8x が遠くで — 主題は 8 倍に低く、鼓動は 2 拍に 1 つになって消える。最後は変ロ長調の共鳴と B-A-D-A')
    E = []; entry(P, b0, 'B', augment(s, 8), 0, '主題 (拡大 ×8)', E); rest_others(P, b0, b1, 'B'); P.rest_bars('B', b0 + 2 * int(sum(d for d, _ in s)) // 1 + 1, b1) if False else None
    harm_fit(P, b0, b1, E, CANDS[R30])
    for b in range(TOTAL - 8, TOTAL): P.set_harm(b, 'A#'); P.hold.add(b)
    for v in VOICES: P.rest_bars(v, TOTAL - 8, TOTAL)
    P.place('A', TOTAL - 7, H.BADA, 0, 'B-A-D-A'); P.rest_bars('A', TOTAL - 8, TOTAL - 7); P.rest_bars('A', TOTAL - 5, TOTAL)
    P.section(TOTAL - 8, '終わり — 変ロ長調の共鳴と B-A-D-A', '長調の共鳴が静かに続き、B-A-D-A がひとつ — 消える')
    for k in range(TOTAL): P.dyn[k] = 1.0 if k < III0 else (1.0 - 0.3 * (k - III0) / float(IV0 - III0) if k < IV0 else 0.7 - 0.3 * min(1.0, (k - IV0) / float(TOTAL - IV0)))
    return P

def notes86(b0, b1, semis, bar_at, bar_end, gain, label):
    first = True
    for n in S86['notes']:
        if not (b0 * BPB <= n['beat'] < b1 * BPB) or n['v'] != 'S': continue
        beat = bar_at * BPB + (n['beat'] - b0 * BPB)
        if beat >= bar_end * BPB: continue
        add('PF', beat, n['dbeats'] + 0.1, n['m'] + semis, gain * (0.62 * n.get('dyn', 1.0) + 0.08), label if first else None, rid=n.get('src'), rel=0.6, layer='86'); first = False

def post(P, events, ex):
    gains = [0.85, 0.85, 0.7, 0.45]
    for i, rid in enumerate(RECL):
        rec = RECS[rid]; t0 = STAGE[i] * BPB
        add('REC', t0, beats_for(t0, rec['dur']), 0, gains[i], None, src=os.path.join(WDIR, rid + '_clean.wav'), off=0.0, fin=0.5 if i else 0.02, fout=6.0 if i == 3 else 2.0, rid=rid + '.wav', tag='%s — 実音 (%s)' % (NAME[rid], ['くつろぎ', '暖まり', '冷え', '眠り'][i]))
    t0 = IV0 * BPB; add('REC', t0, beats_for(t0, 150.0), 0, 0.12, None, src=os.path.join(WDIR, 'late_bach_fuga_8x.wav'), off=1260.0, fin=8.0, fout=20.0, semis=-4, rid='late_bach_fuga_8x.wav', tag='late_bach_fuga_8x (遠くで)')
    notes86(4, 20, shift(4, KEY[R18]), II0 + 2, III0 - 2, 0.4, 'LXXXVI Sweet の旋律'); notes86(20, 36, shift(4, KEY[R49]), III0 + 2, IV0 - 2, 0.4, 'LXXXVI Flower の旋律')
    first = True
    for e in S89['extras']:
        if e['v'] != 'PF' or e['t'] >= 96: continue
        beat = III0 * BPB + e['beat'] * 0.5
        if beat >= (IV0 - 1) * BPB: continue
        add('PF', beat, e['dbeats'] * 0.5 + 0.2, e['m'] + shift(2, KEY[R49]), e['gain'] * 0.35, 'LXXXIX の伸ばした主題 (遠くで)' if first else None, rid=e.get('rid'), rel=0.6, layer='89'); first = False
    # ---- ジャズ / R&B の和音 (中音域) とベース
    for bar in range(2, TOTAL - 8):
        b0 = bar * BPB; c = chord(P.harm[b0]); c2 = chord(P.harm[b0 + 2]); stage = max(k for k in range(4) if bar >= STAGE[k]) if bar >= STAGE[0] else 0
        warm = stage == 1; cool = stage == 2; sleep = stage == 3
        fade = 1.0 if not sleep else max(0.0, 1.0 - (bar - IV0) / float(max(1, TOTAL - 8 - IV0)))
        def voicing(cc, warm):
            pcs = [cc['third'], (cc['root'] + 10) % 12, (cc['root'] + 2) % 12, cc['fifth']] + ([(cc['root'] + 9) % 12] if warm else [])   # 3rd・7th・9th・5th (+13th)
            return sorted({min((x for x in range(58, 78) if x % 12 == p), key=lambda x: abs(x - 67)) for p in pcs})[:5]
        cg = (0.3 if stage == 0 else 0.3 if warm else 0.24 if cool else 0.2 * fade)
        hits = ((0, 1.6, 1.0, c), (1.67, 0.9, 0.7, c), (3.0, 0.9, 0.8, c2), (3.67, 0.8, 0.55, c2)) if stage <= 1 else (((0, 2.4, 1.0, c), (2.67, 1.2, 0.6, c2)) if cool else ((0, 3.5, 1.0, c),))
        for beat, dur, gm, cc in hits:
            for i, m in enumerate(voicing(cc, warm)): add('PF', b0 + beat + 0.03 * i, dur, m, cg * gm * (0.9 if i else 1.0), ('ジャズの和音 (7th・9th、スウィング)' if bar == 2 else 'R&B の和音 (9th・13th を重ねて暖かく)' if bar == II0 else None) if (beat == 0 and i == 0) else None, rid=PSRC, rel=0.4, layer='comp')
        root, third, fifth = 36 + c['root'], 36 + c['third'], 36 + c['fifth']; nroot = 36 + c2['root'] if bar % 2 == 0 else 36 + chord(P.harm[min(TOTAL * BPB - 1, b0 + 4)])['root']
        bg = 0.4 if stage <= 1 else 0.34 if cool else 0.3 * fade
        if stage <= 1:                                                                             # ウォーキング・ベース: 根音 → 3 度 → 5 度 → 次の根音への半音
            appr = nroot - 1 if nroot - 1 != fifth else nroot + 1
            for i, m in enumerate((root, third, fifth, appr)): add('PF', b0 + i, 1.05, m, bg * (1.0 if i == 0 else 0.8), 'ウォーキング・ベース' if (bar == 2 and i == 0) else None, rid=LOW, rel=0.3, layer='bass')
        elif cool: add('PF', b0, 2.2, root, bg, None, rid=LOW, rel=0.4, layer='bass'); add('PF', b0 + 2, 2.2, 36 + c2['root'], bg * 0.8, None, rid=LOW, rel=0.4, layer='bass')
        elif bg > 0.02: add('PF', b0, 4.2, root, bg, None, rid=LOW, rel=0.5, layer='bass')
    # ---- 共鳴 (13:19 の音) と鼓動 (CXVII と同じ)
    q = 0; first = True
    while q < TOTAL * BPB:
        h = P.harm[q]; q1 = q
        while q1 < TOTAL * BPB and P.harm[q1] == h: q1 += 1
        d = max(1.0, (q1 - q) + 0.6); c = chord(h); bar = q // BPB
        warm = II0 <= bar < III0; low = bar >= III0; last = bar >= TOTAL - 8
        pcs = [c['root'], c['fifth']] + ([c['third'], c['third']] if warm else [c['third']])
        tones = [min((x for x in range(52, 76) if x % 12 == p), key=lambda x: abs(x - (64 if warm else 60))) for p in pcs]
        if warm: tones[-1] += 12
        if low: tones = [m - 12 for m in tones]
        g = (0.12 if bar < III0 else 0.1 if bar < IV0 else 0.09) * (2.0 if last else 1.0)
        for i, m in enumerate(tones): add('PF', q + 0.05 * i, d, m, g * (1.0 if i == 0 else 0.7), '共鳴 (13:19 の音)' if first else None, rid='VOXRS', rel=1.5, layer='res'); first = False
        add('PF', q, d, tones[0] - 12, g * 0.6, None, rid='VOXRS', rel=1.5, layer='res')
        q = q1
    for bar in range(1, TOTAL - 8):
        c = chord(P.harm[bar * BPB]); root = 36 + c['root']
        step = 1 if bar < IV0 else 2; fade = 1.0 if bar < IV0 else max(0.0, 1.0 - (bar - IV0) / float(max(1, TOTAL - 8 - IV0)))
        for i in range(0, BPB, step):
            g = (0.32 if i == 0 else 0.19) * fade * (0.8 if bar >= III0 else 1.0)
            if g > 0.01: add('PF', bar * BPB + i, 0.6, root, g, '鼓動 (1 拍ごと)' if (bar == 1 and i == 0) else None, rid=LOW, rel=0.4, layer='pulse')

META = {'style': 'recsampler', 'bank': None, 'rec_order': RECL, 'piano_decay': 2.0, 'reverb': [5.0, 2.0, 0.4], 'src_name': {'VOXRS': '共鳴 (13:19 の音)'},
        'title': 'Requiem BADA — CXXI · Ninna nanna in fuga, R&B e jazz',
        'subtitle': 'バッハのフーガを 10/12 で作り換え (主題は 06:27 の最上声から)、バックを CXVII の形で — くつろぎ (06:27) → 暖まり (11:18、ヘ長調) → 冷え (08:49) → 眠り (06:30)。ジャズの和音とウォーキング・ベース、R&B の 9th が中音域で、クラシックのフーガが流れる。実音のピアノを主体に、鐘なし (♩=66 → 44)',
        'legend': ['PF'], 'vname': {'PF': '和音 / ベース / 共鳴 / 鼓動'},
        'footer': ['I. 提示 → 対提示 (ジャズ) → II. 長調の上で反行とストレッタ (R&B) → III. 拡大が下りていく (冷え) → IV. 8 倍に低く (眠り) → 変ロ長調の共鳴と B-A-D-A',
                   '和音は主題の音を含み、録音のその時の和音に近いものを選ぶ (共鳴)。鼓動 (13:04 の低い音) はテンポと一緒に遅くなり、眠りで消える。弔鐘・祝鐘なし、ドラムなし、声なし。']}

def make_bank(path):
    out = []
    for s in B1012['samples']:
        atk, dec = measure(s['file'])
        if atk <= 0.12 and dec <= -0.1: out.append(s)
    out += [dict(s, rid='VOXRS') for s in B112['samples'] if s['rid'] == RS] + B109['samples']
    json.dump(dict(recordings={}, samples=out), open(path, 'w'), ensure_ascii=False)

if __name__ == '__main__':
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; make_bank(bank_out); META['bank'] = bank_out
    print('subject', ' '.join('%s:%g' % (name_of(m), d) for d, m in SUBJ), 'stages', STAGE, 'total', TOTAL)
    compose.main(OUT, seed=121, bpm=TP0, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC; endp = n['t'] >= d['bar_times'][TOTAL - 8]
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round((0.5 if endp else 0.45 * n.get('dyn', 1.0)), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
