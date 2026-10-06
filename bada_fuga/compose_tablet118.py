#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXVIII · Dodici ninne nanne (12 の子守歌 — CXVII と同じ原理で、パターンの違う 12 曲)
  共通の原理 (CXVII): 眠りの 4 段階 (くつろぎ → 暖まり → 冷え → 眠り)、実音のピアノ (息の所だけ下げた録音) を表に、主題がだんだん伸びて低く沈み、
    テンポと鼓動 (13:04 の低い音) がゆっくり落ちて消える。13:19 の音の共鳴がその時の和音を保つ。弔鐘・祝鐘なし、声なし
  曲ごとに変えるもの (PLANS): 4 本の録音の組み合わせ ／ 主題 (大黒柱・3 分目・13:27・08:53・08:09・08:06) ／ 歌わせ方 (唱え・シャコンヌ・カノン・マントラ・下降・フーガ) ／
    重ねる層 (LXXXVI の Sweet・Flower、LXXXIX の伸ばした主題、late_bach_fuga_8x) ／ テンポの落ち方 ／ 終わり方 (長調の共鳴と B-A-D-A・主題だけ・録音が消える)
  No. 1 は CXVII を 3 分目の主題で作り直したもの、No. 2〜5 がパターンの違う 4 曲、No. 6〜12 が同じ原理の 7 曲
  使い方: python compose_tablet118.py <No. 1〜12> <bank112.json> <bank109.json> <score_tablet89.json> <score_tablet86.json> <wav のフォルダ> [score.json]
"""
import sys, os, json, math
NO = int(sys.argv[1]); OUT = sys.argv[7] if len(sys.argv) > 7 else 'score_tablet118_%02d.json' % NO
SCORE86 = sys.argv[5]; WDIR = os.path.abspath(sys.argv[6]); BANK109 = sys.argv[3]
sys.argv = [sys.argv[0], sys.argv[2], sys.argv[3], sys.argv[4], WDIR, OUT]
import compose_tablet112 as T
import compose_heart as H
from compose import *
import compose

S86 = json.load(open(SCORE86)); B109 = json.load(open(BANK109))
RECS = dict(B109['recordings']); RECS.update(T.RECS)
LOW = '20260925_130431'; PSRC = T.R24
KEY = {'20261003_132245': 10, '20261003_132431': 10, '20261003_132703': 10, '20260924_084937': 5, '20260924_085314': 11, '20260924_111846': 5,
       '20260924_112313': 11, '20260923_080918': 4, '20260923_080607': 10, '20260929_151249': 10, '20260929_151602': 10}       # 主音 (pc)
MAJOR = {'20260924_111846'}
NAME = {'20261003_132245': '10/03 13:22', '20261003_132431': '10/03 13:24', '20261003_132703': '10/03 13:27', '20260924_084937': '9/24 08:49', '20260924_085314': '9/24 08:53',
        '20260924_111846': '9/24 11:18', '20260924_112313': '9/24 11:23', '20260923_080918': '9/23 08:09', '20260923_080607': '9/23 08:06', '20260929_151249': '9/29 15:12', '20260929_151602': '9/29 15:16'}
THEMES = {'PT': ('大黒柱の主題', 10, [(1.5, 68), (1.5, 61), (1, 63), (1, 61), (1, 63), (0.5, 61), (0.5, 60), (1, 58)]),
          'T3': ('3 分目の主題', 2, [(2, 64), (1, 71), (1, 72), (2, 76), (1, 74), (1, 72)]),
          'S27': ('13:27 の主題', 10, [(0.5, 58), (0.5, 61), (0.5, 65), (0.5, 70), (1, 63), (0.5, 65), (0.5, 69), (1.5, 65), (0.5, 63), (2, 58)]),
          'S53': ('08:53 の主題', 11, [(1, 64), (3, 66), (1.5, 71), (1.5, 76), (1, 76)]),
          'S09': ('08:09 の主題', 4, [(0.5, 67), (0.5, 66), (3, 67), (2, 71), (2, 76)]),
          'S06': ('08:06 の主題', 10, [(1, 65), (1, 63), (1, 65), (1, 66), (1, 69), (1, 70), (1, 72), (1, 70)])}
R = {k: k for k in KEY}
PLANS = {  # (録音 4 本: くつろぎ・暖まり・冷え・眠り, 主題, 歌わせ方, LXXXVI の層, LXXXIX, 8x, 終わり, テンポ (始め, 終わり), 題)
    1: (['20261003_132245', '20260924_111846', '20260924_084937', '20261003_132703'], 'T3', 'chant', 'sweet+flower', True, True, 'major', (60, 42), 'Ninna nanna rifatta (3 分目の主題で)'),
    2: (['20261003_132431', '20260924_085314', '20260923_080607', '20261003_132245'], 'PT', 'chaconne', 'sweet', False, False, 'theme', (58, 44), 'Ciaccona'),
    3: (['20260923_080918', '20260924_111846', '20260929_151249', '20261003_132703'], 'S09', 'canon', 'flower', True, True, 'major', (60, 46), 'Canone'),
    4: (['20260924_112313', '20261003_132245', '20260924_084937', '20260929_151602'], 'S53', 'mantra', None, False, True, 'rec', (56, 40), 'Mantra'),
    5: (['20261003_132703', '20260924_111846', '20260923_080607', '20261003_132431'], 'PT', 'descent', 'sweet', True, False, 'major', (60, 44), 'Discesa'),
    6: (['20260929_151249', '20260929_151602', '20260924_084937', '20261003_132245'], 'S27', 'chant', 'flower', False, True, 'theme', (60, 44), 'Cantilena 9/29'),
    7: (['20260924_085314', '20260924_111846', '20260924_112313', '20261003_132703'], 'T3', 'chaconne', 'sweet+flower', True, False, 'major', (64, 46), 'Ciaccona 9/24'),
    8: (['20260923_080607', '20261003_132431', '20260924_084937', '20260929_151249'], 'S06', 'canon', None, True, True, 'rec', (58, 42), 'Canone 08:06'),
    9: (['20261003_132245', '20260924_085314', '20260929_151602', '20261003_132431'], 'PT', 'mantra', 'flower', False, False, 'theme', (60, 44), 'Mantra del tema'),
    10: (['20260924_111846', '20261003_132431', '20260923_080918', '20260924_084937'], 'S09', 'fugue', 'sweet', False, True, 'major', (60, 48), 'Fuga sommessa'),
    11: (['20261003_132431', '20260924_112313', '20260923_080607', '20261003_132703'], 'S27', 'descent', None, True, True, 'major', (56, 40), 'Discesa 13:27'),
    12: (['20260924_084937', '20260924_111846', '20261003_132245', '20260929_151602'], 'PT', 'chant', 'sweet+flower', True, True, 'major', (60, 44), 'Ninna nanna ultima')}
RECL, TH, TREAT, L86, L89, L8X, END, (TP0, TP1), TITLE = PLANS[NO]
TNAME, TKEY, THEME0 = THEMES[TH]
def shift(pc_from, pc_to): return ((pc_to - pc_from) + 6) % 12 - 6
def tr_theme(rid): s = shift(TKEY, KEY[rid]); return [(d, m + s) for d, m in THEME0]
# 段落: 録音の長さから (テンポは III から落ちる)
STAGE = []; b = 2
for i, rid in enumerate(RECL):
    STAGE.append(b); b += int(math.ceil(RECS[rid]['dur'] / 4.0)) + 2
I0, II0, III0, IV0 = STAGE; TOTAL = b + 8
def tempo_of(bar):
    if bar < III0: return float(TP0)
    mid = (TP0 + TP1) / 2.0
    if bar < IV0: return TP0 - (TP0 - mid) * (bar - III0) / float(IV0 - III0)
    return mid - (mid - TP1) * min(1.0, (bar - IV0) / float(max(1, TOTAL - IV0 - 8)))
def beats_for(beat0, secs):
    b = beat0; left = secs
    while left > 0 and b < TOTAL * BPB:
        sb = 60.0 / tempo_of(int(b // BPB))
        if left < sb: return b + left / sb - beat0
        left -= sb; b += 1
    return b - beat0
def best_tr(P, motif, bar, prev, lo, hi, bars=2):
    def score(tr):
        s, t = 0.0, bar * BPB
        for d, m in motif:
            pcs = chord(P.harm[min(int(t), TOTAL * BPB - 1)])['pcs']; w = d * (2.0 if abs(t - round(t)) < 1e-6 and int(t) % 2 == 0 else 1.0)
            s += w * (1.0 if (m + tr) % 12 in pcs else -1.0); t += d
        return s - 0.06 * abs(tr) - 0.04 * abs(tr - prev)
    cands = [tr for tr in range(-7, 8) if lo <= min(m for _, m in motif) + tr and max(m for _, m in motif) + tr <= hi]
    return max(cands, key=score) if cands else 0
def stage_tr(P, motif, b0, b1, lo, hi):
    """段落全体でいちばん合う移調 (マントラ: 同じ高さで繰り返す)"""
    best, bt = None, 0
    for tr in range(-7, 8):
        if not (lo <= min(m for _, m in motif) + tr and max(m for _, m in motif) + tr <= hi): continue
        s = 0.0
        for bar in range(b0, b1, 2):
            t = bar * BPB
            for d, m in motif:
                pcs = chord(P.harm[min(int(t), TOTAL * BPB - 1)])['pcs']; s += d * (1.0 if (m + tr) % 12 in pcs else -1.0); t += d
        if best is None or s > best: best, bt = s, tr
    return bt
def rest_others(P, b0, b1, keep):
    for v in VOICES:
        if v not in keep: P.rest_bars(v, b0, b1)

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = tempo_of(k); P.dyn[k] = 0.9
    for q in range(TOTAL * BPB):
        cur = None
        for i, rid in enumerate(RECL):
            rec = RECS[rid]; t0 = STAGE[i] * BPB; db = beats_for(t0, rec['dur'])
            if t0 <= q < t0 + db:
                frac = (q - t0) / db * rec['dur']; cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
        if cur is None:
            i = max([k for k in range(4) if q >= STAGE[k] * BPB] or [0]); rid = RECL[i]; N = 'C C# D D# E F F# G G# A A# B'.split()
            cur = N[KEY[rid]] + ('' if (rid in MAJOR or (q >= (TOTAL - 8) * BPB and END == 'major')) else 'm')
        T.RH.append(cur); P.harm[q] = cur
    names = ['I. Rilassamento — くつろぎ', 'II. Calore — 暖まり', 'III. Raffreddamento — 冷え', 'IV. Sonno — 眠り']
    for i, rid in enumerate(RECL):
        b0 = STAGE[i]; b1 = STAGE[i + 1] if i < 3 else TOTAL - 8
        th = tr_theme(rid); aug2, aug4, aug8, inv = T.augment(th), T.augment(th, 4), T.augment(th, 8), T.invert(th)
        P.section(b0 - (2 if i == 0 else 0), '%s (%s, ♩=%d)' % (names[i], NAME[rid], round(tempo_of(b0))), '%s の実音 — %s を %s' % (NAME[rid], TNAME, {'chant': '伸ばして唱える', 'chaconne': '和音に合う移調で置いていく (シャコンヌ)', 'canon': 'オクターヴ下のカノンで', 'mantra': '同じ高さで繰り返す (マントラ)', 'descent': '伸ばしながら下りていく', 'fugue': 'フーガで (小さく)'}[TREAT]))
        if i == 0: rest_others(P, 0, b0, '')
        if i == 3 or TREAT == 'descent' and i >= 2:                                                 # 眠り (と下降の III): 伸ばして低く
            k = 4 if (TREAT == 'descent' and i == 2) else 8; mat = T.augment(th, k); v = 'T' if (TREAT == 'descent' and i == 2) else 'B'
            for b in range(b0, b1, 8 * (k // 4)):
                if b + 2 * k <= b1: P.place(v, b, mat, -12 if v == 'T' else -24, '%s ×%d' % (TNAME, k) if b == b0 else None)
                else: P.rest_bars(v, b, b1)
            rest_others(P, b0, b1, v)
        elif TREAT in ('chant', 'fugue') or (TREAT == 'descent' and i == 0):
            for b in range(b0, b1, 4):
                if b + 4 > b1: rest_others(P, b, b1, ''); break
                tr = best_tr(P, aug2, b, 0, 57, 76, 4) if i != 0 else 0
                v = 'S' if (TREAT == 'descent') else 'A'; P.place(v, b, aug2, tr + (12 if v == 'S' else 0), '%s ×2' % TNAME if b == b0 else None)
                if i == 2: P.place('T', b, aug2, tr - 12, None)
                rest_others(P, b, b + 4, v + ('T' if i == 2 else ''))
            if TREAT == 'fugue' and i == 1:                                                         # 暖まりの段落で、小さな 4 声フーガ (提示 → ストレッタ)
                f = b0 + 4; E = []
                for v in VOICES: P.rest_bars(v, f, f + 14)
                octs = {'S': 12, 'A': 0, 'T': -12, 'B': -24}
                for k, v in enumerate('ASBT'):
                    mv = [(d, m + octs[v]) for d, m in th]; tr = best_tr(P, mv, f + 2 * k, 0, RANGE[v][0], RANGE[v][1]); P.place(v, f + 2 * k, mv, tr, '%s フーガ' % TNAME if k == 0 else None)
                for k, v in enumerate('ASTB'):
                    mv = [(d, m + octs[v]) for d, m in th]; tr = best_tr(P, mv, f + 8 + k, 0, RANGE[v][0], RANGE[v][1]); P.place(v, f + 8 + k, mv, tr, 'ストレッタ' if k == 0 else None)
        elif TREAT == 'chaconne':
            prev = 0
            for b in range(b0, b1, 2):
                if b + 2 > b1: rest_others(P, b, b1, ''); break
                tr = best_tr(P, th, b, prev, 57, 76); prev = tr; P.place('A', b, th, tr, '%s (シャコンヌ)' % TNAME if b == b0 else None)
                if i == 2 and (b - b0) % 4 == 0 and b + 4 <= b1: P.place('T', b, aug2, tr - 12, None)
                rest_others(P, b, b + 2, 'A' + ('T' if (i == 2 and (b - b0) % 4 == 0 and b + 4 <= b1) else ''))
        elif TREAT == 'canon':
            for b in range(b0, b1, 4):
                if b + 5 > b1: rest_others(P, b, b1, ''); break
                tr = best_tr(P, aug2, b, 0, 57, 76, 4); P.place('A', b, aug2, tr, '%s ×2 (カノン)' % TNAME if b == b0 else None); P.place('T', b + 1, aug2, tr - 12, None)
                rest_others(P, b, b + 4, 'AT'); P.rest_bars('T', b, b + 1)
            P.rest_bars('T', b1 - 1, b1) if b1 - 1 >= b0 else None
        elif TREAT == 'mantra':
            tr = stage_tr(P, aug2, b0, b1, 57, 76)
            for b in range(b0, b1, 4):
                if b + 4 > b1: rest_others(P, b, b1, ''); break
                P.place('A', b, aug2, tr, '%s ×2 (マントラ、移調 %+d)' % (TNAME, tr) if b == b0 else None); rest_others(P, b, b + 4, 'A')
        if i == 1 and TREAT != 'fugue' and TREAT != 'descent': pass
    for v in VOICES: P.rest_bars(v, TOTAL - 8, TOTAL)
    N = 'C C# D D# E F F# G G# A A# B'.split(); last = RECL[3]
    if END == 'major':
        for b in range(TOTAL - 8, TOTAL): P.set_harm(b, N[KEY[last]]); P.hold.add(b)
        P.place('A', TOTAL - 7, H.BADA, shift(10, KEY[last]), 'B-A-D-A'); P.rest_bars('A', TOTAL - 8, TOTAL - 7); P.rest_bars('A', TOTAL - 5, TOTAL)
        P.section(TOTAL - 8, '終わり — 長調の共鳴と B-A-D-A', '長調の共鳴が静かに続き、B-A-D-A がひとつ — 消える')
    elif END == 'theme':
        for b in range(TOTAL - 8, TOTAL): P.set_harm(b, N[KEY[last]] + 'm'); P.hold.add(b)
        P.place('B', TOTAL - 8, T.augment(tr_theme(last), 4), -24, '%s ×4 (ひとりで)' % TNAME); P.rest_bars('B', TOTAL - 8 + 2 * int(sum(d for d, _ in THEME0)) // 4 + 1, TOTAL) if False else None
        P.section(TOTAL - 8, '終わり — 主題だけ', '主題が低くひとりで歌い、共鳴の中に消える')
    else:
        for b in range(TOTAL - 8, TOTAL): P.set_harm(b, N[KEY[last]] + ('' if last in MAJOR else 'm')); P.hold.add(b)
        P.section(TOTAL - 8, '終わり — 共鳴だけ', '録音が消えたあと、共鳴だけが静かに残って消える')
    for k in range(TOTAL):
        P.dyn[k] = 0.9 if k < III0 else (0.9 - 0.3 * (k - III0) / float(IV0 - III0) if k < IV0 else 0.6 - 0.3 * min(1.0, (k - IV0) / float(TOTAL - IV0)))
    return P

def notes86(b0, b1, semis, bar_at, bar_end, gain, label):
    first = True
    for n in S86['notes']:
        if not (b0 * BPB <= n['beat'] < b1 * BPB) or n['v'] != 'S': continue
        beat = bar_at * BPB + (n['beat'] - b0 * BPB)
        if beat >= bar_end * BPB: continue
        T.add('PF', beat, n['dbeats'] + 0.1, n['m'] + semis, gain * (0.62 * n.get('dyn', 1.0) + 0.08), label if first else None, rid=n.get('src'), rel=0.6, layer='86'); first = False

def post(P, events, ex):
    gains = [0.85, 0.85, 0.7, 0.45]
    for i, rid in enumerate(RECL):
        rec = RECS[rid]; t0 = STAGE[i] * BPB
        T.add('REC', t0, beats_for(t0, rec['dur']), 0, gains[i], None, src=os.path.join(WDIR, rid + '_clean.wav'), off=0.0, fin=0.5 if i else 0.02, fout=6.0 if i == 3 else 2.0, rid=rid + '.wav', tag='%s — 実音 (%s)' % (NAME[rid], ['くつろぎ', '暖まり', '冷え', '眠り'][i]))
    if L8X:
        t0 = IV0 * BPB; T.add('REC', t0, beats_for(t0, 150.0), 0, 0.12, None, src=os.path.join(WDIR, 'late_bach_fuga_8x.wav'), off=1260.0, fin=8.0, fout=20.0, semis=shift(2, KEY[RECL[3]]), rid='late_bach_fuga_8x.wav', tag='late_bach_fuga_8x (遠くで)')
    if L86 and 'sweet' in L86:
        s6 = shift(4, KEY[RECL[0]]); notes86(4, 20, s6, I0 + 2, II0 - 2, 0.5, 'LXXXVI Sweet の旋律 (%+d)' % s6); notes86(4, 20, s6, I0 + 18, II0 - 2, 0.45, None)
    if L86 and 'flower' in L86:
        s6 = shift(4, KEY[RECL[2]]); notes86(20, 36, s6, III0 + 2, IV0 - 2, 0.45, 'LXXXVI Flower の旋律 (%+d)' % s6); notes86(20, 36, s6, III0 + 26, IV0 - 2, 0.35, None)
    if L89:
        s9 = shift(2, KEY[RECL[2]]); first = True
        for e in T.S89['extras']:
            if e['v'] != 'PF' or e['t'] >= 96: continue
            beat = III0 * BPB + e['beat'] * 0.5
            if beat >= (IV0 - 1) * BPB: continue
            T.add('PF', beat, e['dbeats'] * 0.5 + 0.2, e['m'] + s9, e['gain'] * 0.35, 'LXXXIX の伸ばした主題 (遠くで)' if first else None, rid=e.get('rid'), rel=0.6, layer='89'); first = False
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
        g = (0.14 if bar < III0 else 0.11 if bar < IV0 else 0.09) * (2.0 if last else 1.0)
        for i, m in enumerate(tones): T.add('PF', q + 0.05 * i, d, m, g * (1.0 if i == 0 else 0.7), '共鳴 (13:19 の音)' if first else None, rid='VOXRS', rel=1.5, layer='res'); first = False
        T.add('PF', q, d, tones[0] - 12, g * 0.6, None, rid='VOXRS', rel=1.5, layer='res')
        q = q1
    for bar in range(1, TOTAL - 8):
        c = chord(P.harm[bar * BPB]); root = 36 + c['root']
        step = 1 if bar < IV0 else 2; fade = 1.0 if bar < IV0 else max(0.0, 1.0 - (bar - IV0) / float(max(1, TOTAL - 8 - IV0)))
        for i in range(0, BPB, step):
            g = (0.24 if i == 0 else 0.15) * fade * (0.8 if bar >= III0 else 1.0)
            if g > 0.01: T.add('PF', bar * BPB + i, 0.6, root, g, '鼓動 (1 拍ごと)' if (bar == 1 and i == 0) else None, rid=LOW, rel=0.4, layer='pulse')

META = {'style': 'recsampler', 'bank': None, 'rec_order': RECL, 'piano_decay': 2.2, 'reverb': [6.0, 2.5, 0.45], 'src_name': {'VOXRS': '共鳴 (13:19 の音)'},
        'title': 'Requiem BADA — CXVIII · Dodici ninne nanne, No. %d · %s' % (NO, TITLE),
        'subtitle': '%s → %s (%s) → %s → %s ／ %s を%s ／ %s%s%s終わりは%s (♩=%d → %d)' % (
            NAME[RECL[0]], NAME[RECL[1]], '長調' if RECL[1] in MAJOR else '短調', NAME[RECL[2]], NAME[RECL[3]], TNAME,
            {'chant': '伸ばして唱える', 'chaconne': 'シャコンヌで', 'canon': 'カノンで', 'mantra': 'マントラで', 'descent': '下降で', 'fugue': '小さなフーガで'}[TREAT],
            ('LXXXVI の %s、' % L86) if L86 else '', 'LXXXIX、' if L89 else '', '8 倍のバッハ、' if L8X else '', {'major': '長調の共鳴と B-A-D-A', 'theme': '主題だけ', 'rec': '共鳴だけ'}[END], TP0, TP1),
        'legend': ['PF'], 'vname': {'PF': '共鳴 / 鼓動 / 旋律の層'},
        'footer': ['CXVII と同じ原理: くつろぎ → 暖まり → 冷え → 眠り。実音のピアノを表に、主題が伸びて低く沈み、テンポと鼓動がゆっくり落ちて消える。弔鐘・祝鐘なし、声なし',
                   '録音は息のような所だけ下げ、ほかは加工なし。共鳴は 13:19 の音、鼓動は 13:04 の低い音。ピアノの 1 音の層は録音の音域の中に。']}

if __name__ == '__main__':
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; T.make_bank(bank_out); META['bank'] = bank_out
    compose.main(OUT, seed=118 + NO, bpm=TP0, builder=build, meta=META, extras=T.extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC; endp = n['t'] >= d['bar_times'][TOTAL - 8]
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round((0.5 if endp else 0.45 * n.get('dyn', 0.9) / 0.9), 4), label=None, rid=PSRC, rel=0.6, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('No.', NO, TITLE, 'bars', d['nbars'], 'duration %.0f s' % d['duration'], 'stages', STAGE, 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
