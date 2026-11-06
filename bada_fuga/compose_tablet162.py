#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLXII · Sei voci senza metallo (tablet161・トラック 8・トラック 18・tablet117・2026/11/06 06:42・06:39 の金属の電子音を取り除いて、トラック 18 にトラック 8 を共鳴させて、全部を合成)
  6 つの音源はすべて実音のまま、高域を低域通過で落として (tablet117 は 1.8 kHz、tablet161 は 1.6 kHz、トラック 8 は 2.2 kHz、トラック 18 は 2.4 kHz、06:42・06:39 は 3 kHz より上を落とす) 金属的な電子音・高音の電子音を取り除く。鐘なし、高い共鳴なし、シンセなし
  共鳴: トラック 18 (ニ短調、表) が鳴るたびに、トラック 8 を 4 度上げて (ハ長調 / イ短調 → ヘ長調 / ニ短調) 同じ調で下に重ね、さらにトラック 8 の音から作った旋律の頭を低い実音のピアノで 2 小節遅れに反響させる
  調はヘ長調 / ニ短調に揃える: 06:42 はそのまま (ヘ長調)、06:39 は全音下げて (ト長調 → ヘ長調)、tablet117 はヘ長調の段 (160 秒から) と変ロ長調の終わりを、tablet161 はニ短調の頂点の段 (412 秒から)
  使い方: python compose_tablet162.py <bank150.json> <wav のフォルダ (高域を落とした 6 つの wav)> [score_tablet162.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet162.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R42, R39, R18, R08, R117, R161 = '20261106_064228', '20261106_063938', '20261107_180000', '20261107_080000', '20261003_117000', '20261107_161000'
PSRC = R42
BPM = 60
TOTAL = 180
NAMES = {R42: '11/06 06:42', R39: '11/06 06:39', R18: 'トラック 18', R08: 'トラック 8', R117: 'tablet117', R161: 'tablet161'}
FILE = {R42: R42 + '_clean.wav', R39: R39 + '_clean.wav', R18: R18 + '.wav', R08: R08 + '.wav', R117: R117 + '.wav', R161: R161 + '.wav'}
DUR = {R42: 226.7, R39: 160.3, R18: 149.1, R08: 249.2, R117: 778.6, R161: 711.0}
I, II, III, IV = 0, 44, 88, 136
# (録音, 小節, 音量, 半音, オフセット秒, 長さ秒, 表)  — 後ろの表が和音を決める
PLAYS = [(R117, 0, 0.18, 0, 160.0, 170.0, False),                                                  # I: tablet117 ヘ長調の段 (裏)
         (R42, 1, 0.5, 0, 0.0, None, True),                                                        # I: 06:42 (表)
         (R08, 4, 0.3, 5, 0.0, 150.0, False), (R18, 4, 0.62, 0, 0.0, None, True),                 # I: トラック 18 (表) + トラック 8 を 4 度上げて共鳴
         (R39, II, 0.45, -2, 0.0, None, True),                                                     # II: 06:39 を全音下げて (表)
         (R117, II, 0.16, 0, 330.0, 170.0, False),                                                 # II: tablet117 (裏)
         (R08, II + 3, 0.3, 5, 150.0, 99.0, False), (R18, II + 3, 0.62, 0, 0.0, None, True),       # II: トラック 18 + トラック 8 (続き)
         (R161, III, 0.4, 0, 412.0, 150.0, True),                                                  # III: tablet161 の頂点の段 (表)
         (R117, III, 0.16, 0, 200.0, 180.0, False),                                                # III: tablet117 (裏)
         (R08, III + 4, 0.3, 5, 0.0, 150.0, False), (R18, III + 4, 0.58, 0, 0.0, None, True),      # III: トラック 18 + トラック 8
         (R42, IV, 0.5, 0, 130.0, 96.0, True),                                                     # IV: 06:42 の終わり (表)
         (R117, IV, 0.18, 0, 600.0, 170.0, False),                                                 # IV: tablet117 の終わり (変ロ長調、裏)
         (R08, IV + 4, 0.26, 5, 100.0, 140.0, False), (R18, IV + 4, 0.5, 0, 0.0, None, True)]      # IV: トラック 18 + トラック 8、消えていく
def play_len(rid, dur): return DUR[rid] if dur is None else dur
LOOP = ['Dm', 'Bb', 'F', 'C']
SCALE = [5, 7, 9, 10, 0, 2, 4]
def tune_from(rid, sm, lo=62, hi=76, rhythm=(1, 1, 1, 1, 2, 2), ends=((69, 74), (65, 62), (69, 74), (62, 62)), n=4):
    tops = []
    for sg in RECS[rid]['segs']:
        m = sg['m'][-1] + sm
        if sg['d'] < 0.3: continue
        if tops and tops[-1] % 12 == m % 12: continue
        m = min((x for x in range(m - 2, m + 3) if x % 12 in SCALE), key=lambda x: abs(x - m))
        while m < lo: m += 12
        while m > hi: m -= 12
        if tops and abs(m - tops[-1]) > 7: m = min((m + 12 * k for k in (-1, 0, 1)), key=lambda x: abs(x - tops[-1]))
        while m < lo: m += 12
        while m > hi: m -= 12
        tops.append(m)
    rh = list(rhythm) * n; out = [(d, tops[i % len(tops)]) for i, d in enumerate(rh)]
    for ph in range(n):
        i = ph * len(rhythm) + len(rhythm) - 1; out[i] = (2, min(ends[ph % 4], key=lambda x: abs(x - out[i][1])))
    return out
T8 = tune_from(R08, 5); T18 = tune_from(R18, 0)
def tr(mat, o): return [(d, m + o) for d, m in mat]
def aug(mat, k=2): return [(d * k, m) for d, m in mat]
RATE = lambda semis: 2 ** (semis / 12.0)
extras = []; RH = []; RECQ = set()
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
def clip(mat, max_beats):
    out = []; t = 0.0
    for d, m in mat:
        if t >= max_beats: break
        out.append((min(d, max_beats - t), m)); t += d
    return out

def build():
    P = Piece(TOTAL)
    for q in range(TOTAL * BPB):
        cur = None
        for rid, bar, g, sm, off, dur, lead in PLAYS:
            if not lead or rid not in RECS: continue
            rec = RECS[rid]; t0 = bar * BPB; db = play_len(rid, dur) / RATE(sm) * BPM / 60.0
            if t0 <= q < t0 + db:
                frac = (q - t0) * 60.0 / BPM * RATE(sm) + off; cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
                cur = transpose_h([[cur]], sm)[0][0]; RECQ.add(q)
        if cur is None: b = q // BPB; cur = LOOP[b % 4]
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL):
        P.tempo[k] = BPM
        P.dyn[k] = 0.5 if k < II else 0.6 if k < III else 0.7 if k < IV else max(0.1, 0.6 - 0.014 * (k - IV))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    def put(v, b, mat, label=None):
        mat = clip(mat, (TOTAL - 3 - b) * BPB); t = b * BPB
        for d, m in mat: P.rest[v].difference_update(range(int(math.floor(t)), int(math.ceil(t + d - 1e-9)))); t += d
        P.place(v, b, mat, 0, label)
    P.section(I, 'I. 06:42 とトラック 18 (ヘ長調 / ニ短調, ♩=60)', '06:42 (表) にトラック 18 (表)、トラック 8 を 4 度上げて下に重ねて共鳴、tablet117 のヘ長調の段が裏に。トラック 8 の旋律の頭を低い実音のピアノで 2 小節遅れに反響。すべて高域を落として')
    P.section(II, 'II. 06:39 (全音下げて) とトラック 18', '06:39 を全音下げてヘ長調に (表)、トラック 18 (2 回目) + トラック 8 の続き、tablet117 が裏に')
    P.section(III, 'III. tablet161 の頂点とトラック 18', 'tablet161 (CLXI) のニ短調の頂点の段 (表)、トラック 18 (3 回目) + トラック 8、tablet117 が裏に。低いピアノの反響が 2 声に')
    P.section(IV, 'IV. 06:42 の終わり — 消える', '06:42 の終わり (表)、トラック 18 (4 回目) + トラック 8、tablet117 の終わり (変ロ長調) が裏に、少しずつ消える')
    for b0, nvoice in ((4, 1), (II + 3, 1), (III + 4, 2), (IV + 4, 1)):
        for k in range(4):
            b = b0 + 2 + 8 * k
            put('T', b, tr(T8[:6], -12), 'トラック 8 の旋律の頭 (低いピアノの反響)' if (b0 == 4 and k == 0) else None)
            if nvoice == 2: put('B', b + 2, tr(T8[:6], -24), None)
    put('B', II + 40, aug(tr(T18[:6], -24)), 'トラック 18 の旋律の頭 (2 倍に伸ばして)'); put('B', IV + 38, aug(tr(T18[:6], -24)), None)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.5 if bar > 0 else 0.02, fout=8.0, semis=sm, rid=rid + '.wav', tag='%s — %s%s' % (NAMES[rid], '表' if lead else '裏', {5: '、4 度上げて (共鳴)', -2: '、全音下げて', 0: ''}[sm]))
    first = True
    for b in range(2, TOTAL - 6, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.6, r, 0.12 * P.dyn.get(b, 0.6) / 0.6, '低いペダルの音 (2 小節ごと)' if first else None); first = False

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R18, R08, R42, R39, R161, R117], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CLXII · Sei voci senza metallo',
        'subtitle': 'tablet161・トラック 8・トラック 18・tablet117・11/06 06:42・06:39 の金属の電子音を取り除いて (すべて高域を落として)、トラック 18 にトラック 8 を 4 度上げて共鳴させ、全部を合成: 06:42 → 06:39 (全音下げて) → tablet161 の頂点 → 06:42 の終わり、トラック 18 は 4 回。ヘ長調 / ニ短調、♩=60',
        'legend': ['PF', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音、低く)', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['高域を落とす: tablet117 1.8 kHz、tablet161 1.6 kHz、トラック 8 2.2 kHz、トラック 18 2.4 kHz、06:42・06:39 3 kHz (低域通過、零位相)。鐘なし、高い共鳴なし、シンセなし',
                   '共鳴 = トラック 18 (ニ短調) の下にトラック 8 を 4 度上げて (ヘ長調 / ニ短調) 重ね、トラック 8 の旋律の頭を低い実音のピアノ (1〜2 オクターヴ下) で 2 小節遅れに。和音は表の録音 (トラック 18 が優先) の採譜から。声なし。']}

if __name__ == '__main__':
    print('T8', ' '.join('%s:%g' % (name_of(m), d) for d, m in T8[:6]), '| T18', ' '.join('%s:%g' % (name_of(m), d) for d, m in T18[:6]))
    compose.main(OUT, seed=162, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
