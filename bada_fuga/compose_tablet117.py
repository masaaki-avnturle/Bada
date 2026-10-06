#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXVII · Ninna nanna 10/03 (眠りへの曲 — CXVI・CXI・requiem・LXXXVI・LXXXIX の材料で、実音のピアノを主体に、鐘なし)
  眠りの 4 段階 (♩=60 から後半で 44 へゆっくり落ちる。鼓動も一緒に遅くなる):
    I.   Rilassamento (くつろぎ)   0〜38   10/03 13:24 の実音 (変ロ短調) — LXXXVI の Sweet の旋律 (+6 で変ロ短調に、ピアノの 1 音) が小さく、大黒柱の主題を 2 倍に伸ばしてアルトが静かに唱える。鼓動 ♩=60
    II.  Calore (暖まり)          38〜80  9/24 11:18 の実音 (ヘ長調 — 暖かい) — 主題が和音に合う移調で (長調の響き)、共鳴は 3 度を重ねて暖かく
    III. Raffreddamento (冷え)    80〜136 9/24 08:49 の実音 (ヘ短調) — ♩=60 → 50。LXXXVI の Flower の旋律 (+1 でヘ短調の五音音階に)、主題は 4 倍に伸びて 1 オクターヴずつ下りていく。共鳴は 1 オクターヴ下、LXXXIX の I. Requiem の伸ばした主題 (−4) が遠くで
    IV.  Sonno (眠り)             136〜176 ♩=50 → 44。10/03 13:27 の実音を半分の大きさで、late_bach_fuga_8x (−4、×10) が遠くで。主題は 8 倍に、低く。鼓動は 2 拍に 1 つになり消え、最後は変ロ長調の共鳴と B-A-D-A だけが静かに消える
  私の周波数帯: 10/03・9/24 の録音の音域 (ソ 2〜ファ 6、重心 1〜1.5 kHz) の中に、ピアノの 1 音の層も置く (ソ 3〜ファ 5)。弔鐘・祝鐘は使わない。声なし
  使い方: python compose_tablet117.py <bank112.json> <bank109.json> <score_tablet89.json> <score_tablet86.json> <wav のフォルダ> [score_tablet117.json]
"""
import sys, os, json, math
OUT = sys.argv[6] if len(sys.argv) > 6 else 'score_tablet117.json'
SCORE86 = sys.argv[4]; WDIR = os.path.abspath(sys.argv[5]); BANK109 = sys.argv[2]
sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2], sys.argv[3], WDIR, OUT]
import compose_tablet112 as T
import compose_heart as H
from compose import *
import compose
THEME = [(1.5, 68), (1.5, 61), (1, 63), (1, 61), (1, 63), (0.5, 61), (0.5, 60), (1, 58)]              # 大黒柱の主題 (CXIII): ラ♭・レ♭・ミ♭・レ♭・ミ♭・レ♭・ド・シ♭

def best_tr(P, motif, bar, prev, lo, hi):
    """2 小節の和音に、強拍・長い音が和音の音になる移調 (±7) — 前の置き方に近いほうを少し優先、音域 lo〜hi (CXIII と同じ)"""
    def score(tr):
        s, t = 0.0, bar * BPB
        for d, m in motif:
            pcs = chord(P.harm[min(int(t), TOTAL * BPB - 1)])['pcs']; w = d * (2.0 if abs(t - round(t)) < 1e-6 and int(t) % 2 == 0 else 1.0)
            s += w * (1.0 if (m + tr) % 12 in pcs else -1.0); t += d
        return s - 0.06 * abs(tr) - 0.04 * abs(tr - prev)
    cands = [tr for tr in range(-7, 8) if lo <= min(m for _, m in motif) + tr and max(m for _, m in motif) + tr <= hi]
    return max(cands, key=score)

S86 = json.load(open(SCORE86)); B109 = json.load(open(BANK109))
RECS = dict(B109['recordings']); RECS.update(T.RECS)
R24, R27, R18, R49 = T.R24, T.R27, '20260924_111846', '20260924_084937'
LOW = '20260925_130431'
# 段落 (小節) とテンポ
I0, II0, III0, IV0, TOTAL = 0, 38, 80, 136, 176
def tempo_of(bar):
    if bar < III0: return 60.0
    if bar < IV0: return 60.0 - 10.0 * (bar - III0) / float(IV0 - III0)
    return 50.0 - 6.0 * min(1.0, (bar - IV0) / float(TOTAL - IV0 - 8))
BAR_S = [60.0 / tempo_of(b) * BPB for b in range(TOTAL)]
def beats_for(beat0, secs):
    """beat0 から secs 秒ぶんの拍数 (テンポが変わるので)"""
    b = beat0; left = secs
    while left > 0 and b < TOTAL * BPB:
        sb = 60.0 / tempo_of(int(b // BPB)); step = min(1.0, (int(b) + 1) - b) if b != int(b) else 1.0
        if left < sb * step: return b + left / sb - beat0
        left -= sb * step; b += step
    return b - beat0
PLAY = [(R24, I0 + 2, 0.85, '10/03 13:24 — 実音 (くつろぎ)'), (R18, II0 + 1, 0.85, '9/24 11:18 — 実音 (暖まり、ヘ長調)'),
        (R49, III0 + 1, 0.7, '9/24 08:49 — 実音 (冷え、ヘ短調)'), (R27, IV0 + 1, 0.45, '10/03 13:27 — 実音 (眠り、小さく)')]

def build():
    P = Piece(TOTAL)
    for k in range(TOTAL): P.tempo[k] = tempo_of(k); P.dyn[k] = 0.9
    for q in range(TOTAL * BPB):                                                                    # 和音は鳴っている録音の採譜から
        cur = None
        for rid, bar, g, _ in PLAY:
            rec = RECS[rid]; t0 = bar * BPB; db = beats_for(t0, rec['dur'])
            if t0 <= q < t0 + db:
                frac = (q - t0) / db * rec['dur']; cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
        if cur is None: cur = 'A#' if q >= (TOTAL - 8) * BPB else ('A#m' if q < II0 * BPB or q >= IV0 * BPB else ('F' if q < III0 * BPB else 'Fm'))
        T.RH.append(cur); P.harm[q] = cur
    aug, aug4, aug8 = T.augment(THEME), T.augment(THEME, 4), T.augment(THEME, 8)
    P.section(I0, 'I. Rilassamento — くつろぎ (変ロ短調, ♩=60)', '10/03 13:24 の実音 — 大黒柱の主題を 2 倍に伸ばしてアルトが静かに唱え、LXXXVI の Sweet の旋律が小さく。1 拍ごとの鼓動')
    for v in VOICES: P.rest_bars(v, 0, 2)
    for k in range(9):
        b = 2 + 4 * k; P.place('A', b, aug, 0, '大黒柱の主題 ×2' if k == 0 else None)
        for v in 'STB': P.rest_bars(v, b, b + 4)
    P.section(II0, 'II. Calore — 暖まり (ヘ長調, ♩=60)', '9/24 11:18 の実音 (ヘ長調) — 主題が和音に合う移調で静かに (長調の響き)、共鳴は 3 度を重ねて暖かく')
    prev = 0
    for k in range((III0 - II0) // 2):
        b = II0 + 2 * k; tr = best_tr(P, THEME, b, prev, 57, 76); prev = tr
        if k % 2 == 0: P.place('A', b, THEME, tr, '大黒柱の主題 (移調 %+d)' % tr if k == 0 else None)
        else: P.rest_bars('A', b, b + 2)
        for v in 'STB': P.rest_bars(v, b, b + 2)
    P.section(III0, 'III. Raffreddamento — 冷え (ヘ短調, ♩=60 → 50)', '9/24 08:49 の実音 (ヘ短調) — LXXXVI の Flower の旋律 (五音音階) が小さく、主題は 4 倍に伸びて 1 オクターヴずつ下りていく。鼓動がゆっくりになる')
    for k in range(3):
        b = III0 + 16 * k; v = 'ATB'[k]; P.place(v, b, aug4, (-12 if v == 'T' else -24 if v == 'B' else 0) + 0, '大黒柱の主題 ×4' if k == 0 else None)
        for w in VOICES:
            if w != v: P.rest_bars(w, b, b + 16)
    for v in VOICES: P.rest_bars(v, III0 + 48, IV0)
    P.section(IV0, 'IV. Sonno — 眠り (♩=50 → 44)', '10/03 13:27 の実音を半分の大きさで、late_bach_fuga_8x が遠くで — 主題は 8 倍に、低く。鼓動は 2 拍に 1 つになって消え、最後は変ロ長調の共鳴と B-A-D-A だけ')
    P.place('B', IV0, aug8, -24, '大黒柱の主題 ×8', beat=0)
    for v in 'SAT': P.rest_bars(v, IV0, IV0 + 32)
    P.rest_bars('B', IV0 + 32, TOTAL)
    for b in range(TOTAL - 8, TOTAL): P.set_harm(b, 'A#'); P.hold.add(b)
    P.place('A', TOTAL - 7, H.BADA, 0, 'B-A-D-A (変ロ長調で)')
    for v in 'STB': P.rest_bars(v, TOTAL - 8, TOTAL)
    P.rest_bars('A', TOTAL - 8, TOTAL - 7); P.rest_bars('A', TOTAL - 5, TOTAL)
    for k in range(TOTAL):
        P.dyn[k] = 0.9 if k < III0 else (0.9 - 0.3 * (k - III0) / float(IV0 - III0) if k < IV0 else 0.6 - 0.3 * min(1.0, (k - IV0) / float(TOTAL - IV0)))
    return P

def notes86(b0, b1, semis, bar_at, gain, label, rid_pref=None):
    """LXXXVI の旋律 (b0〜b1 小節) を semis 移して bar_at から、ピアノの 1 音で小さく"""
    first = True
    for n in S86['notes']:
        if not (b0 * BPB <= n['beat'] < b1 * BPB) or n['v'] != 'S': continue
        T.add('PF', bar_at * BPB + (n['beat'] - b0 * BPB), n['dbeats'] + 0.1, n['m'] + semis, gain * (0.62 * n.get('dyn', 1.0) + 0.08), label if first else None, rid=rid_pref or n.get('src'), rel=0.6, layer='86'); first = False

def post(P, events, ex):
    for rid, bar, g, tag in PLAY:                                                                   # 実音のピアノ
        rec = RECS[rid]; t0 = bar * BPB
        T.add('REC', t0, beats_for(t0, rec['dur']), 0, g, None, src=os.path.join(WDIR, rid + '_clean.wav'), off=0.0, fin=0.5 if bar > 2 else 0.02, fout=6.0 if rid == R27 else 2.0, rid=rid + '.wav', tag=tag)
    t0 = IV0 * BPB; T.add('REC', t0, beats_for(t0, 150.0), 0, 0.12, None, src=os.path.join(WDIR, 'late_bach_fuga_8x.wav'), off=1260.0, fin=8.0, fout=20.0, semis=-4, rid='late_bach_fuga_8x.wav', tag='late_bach_fuga_8x (−4、遠くで)')
    notes86(4, 20, 6, I0 + 4, 0.5, 'LXXXVI Sweet の旋律 (+6)'); notes86(4, 20, 6, I0 + 20, 0.45, None)                     # I: Sweet (Em → 変ロ短調)
    notes86(20, 36, 1, III0 + 2, 0.45, 'LXXXVI Flower の旋律 (+1、五音音階)'); notes86(20, 36, 1, III0 + 26, 0.35, None)   # III: Flower (→ ヘ短調の五音音階)
    first = True                                                                                    # III: LXXXIX の I. Requiem の伸ばした主題 (−4) が遠くで
    for e in T.S89['extras']:
        if e['v'] != 'PF' or e['t'] >= 96: continue
        T.add('PF', III0 * BPB + e['beat'] * 0.5, e['dbeats'] * 0.5 + 0.2, e['m'] - 4, e['gain'] * 0.35, 'LXXXIX の伸ばした主題 (遠くで)' if first else None, rid=e.get('rid'), rel=0.6, layer='89'); first = False
    q = 0; first = True                                                                             # 共鳴 (13:19 の音): II は 3 度を重ねて暖かく、III から 1 オクターヴ下
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
    for bar in range(1, TOTAL - 8):                                                                 # 鼓動: 13:04 の低い音、IV では 2 拍に 1 つ、消えていく
        c = chord(P.harm[bar * BPB]); root = 36 + c['root']
        step = 1 if bar < IV0 else 2; fade = 1.0 if bar < IV0 else max(0.0, 1.0 - (bar - IV0) / float(TOTAL - 8 - IV0))
        for i in range(0, BPB, step):
            g = (0.24 if i == 0 else 0.15) * fade * (0.8 if bar >= III0 else 1.0)
            if g > 0.01: T.add('PF', bar * BPB + i, 0.6, root, g, '鼓動 (1 拍ごと)' if (bar == 1 and i == 0) else None, rid=LOW, rel=0.4, layer='pulse')

META = {'style': 'recsampler', 'bank': None, 'rec_order': [R24, R18, R49, R27], 'piano_decay': 2.2, 'reverb': [6.0, 2.5, 0.45], 'src_name': {'VOXRS': '共鳴 (13:19 の音)'},
        'title': 'Requiem BADA — CXVII · Ninna nanna 10/03',
        'subtitle': '眠りへの曲 — くつろぎ (13:24) → 暖まり (11:18、ヘ長調) → 冷え (08:49、ヘ短調、♩=60 → 50) → 眠り (13:27、♩=50 → 44、変ロ長調の共鳴へ)。実音のピアノを主体に、大黒柱の主題が 2 倍 → 4 倍 → 8 倍に伸びて低く沈む。鐘なし (♩=60 → 44)',
        'legend': ['PF'], 'vname': {'PF': '共鳴 / 鼓動 / LXXXVI・LXXXIX の旋律'},
        'footer': ['I. Rilassamento: 13:24 + 主題 ×2 + LXXXVI Sweet → II. Calore: 11:18 (ヘ長調) + 主題 (長調の響き) → III. Raffreddamento: 08:49 (ヘ短調) + Flower + 主題 ×4 ↓ + LXXXIX → IV. Sonno: 13:27 (小さく) + late_bach_fuga_8x + 主題 ×8 → 変ロ長調の共鳴と B-A-D-A',
                   '私の周波数帯: 録音の音域 (ソ 2〜ファ 6) の中にピアノの 1 音の層を置く。鼓動 (13:04 の低い音) はテンポと一緒に遅くなり、眠りで消える。弔鐘・祝鐘なし。声なし。']}

if __name__ == '__main__':
    bank_out = os.path.splitext(OUT)[0] + '.bank.json'; T.make_bank(bank_out); META['bank'] = bank_out
    compose.main(OUT, seed=117, bpm=60, builder=build, meta=META, extras=T.extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:                                                                           # 主題の声部: 1 音のサンプラーの上限を超えて実音の下に立つよう、同じ音を PF でも重ねる
        n['src'] = R24; endp = n['t'] >= d['bar_times'][TOTAL - 8]
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round((0.5 if endp else 0.45 * n.get('dyn', 0.9) / 0.9), 4), label=None, rid=R24, rel=0.6, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] = d['meta']['subtitle'].replace('(♩=60 → 44)', '(♩=60 → 44, %d 分 %d 秒)' % (h, rem + 8)); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
    for e in d['extras']:
        if e['v'] == 'REC': print('  REC', e['tag'], 't %.0f d %.0f' % (e['t'], e['d']))
