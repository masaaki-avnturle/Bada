#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLVII · Mantra a tre nel 06:39 (2026/11/06 06:39・トラック 18・トラック 8 で洗脳的な曲に合成)
  3 つの音源 (実音、そのまま; 06:39 は喘ぎの区間だけ下げて) を段落ごとに表と裏を入れ替えて敷き、トラック 8 の音から作った旋律の頭 (マントラ) を各段落の調で繰り返し、BWV 721 の打ち続ける和音 (8 分音符、実音のピアノ) が全曲の脈
    I.  06:39 が表 (ト長調〜ニ・ドリア)  脈が pp で始まり、マントラがアルトで 4 小節ごと
    II. トラック 18 が表 (ニ短調)   トラック 8 が裏、マントラが 2 小節ごとにアルトとテノールで、脈が強く
    III. トラック 8 が表 (ハ長調)   06:39 が裏、マントラ 3 声、全句を 2 倍に、脈は頂点
    IV. 06:39 の後半が表            トラック 18 の終わりが遠くで、脈が消え、頭だけ
  音源: 4 声は 06:42 の実音のピアノの 1 音 (サンプラー)、低いペダルと高い共鳴は合成のピアノ。鐘なし、声なし
  使い方: python compose_tablet157.py <bank150.json> <wav のフォルダ> [score_tablet156.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet157.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R39, R42, R18, R08 = '20261106_063938', '20261106_064228', '20261107_180000', '20261107_080000'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 42, 80, 142, 174
NAMES = {R39: '11/06 06:39', R18: 'トラック 18', R08: 'トラック 8'}
FILE = {R39: R39 + '_clean.wav', R18: R18 + '.wav', R08: R08 + '.wav'}
PLAYS = [(R39, 1, 0.6, 0, 0.0, None, True),
         (R18, S2 + 1, 0.55, 0, 0.0, None, True), (R08, S2 + 1, 0.28, 0, 0.0, 150.0, False),
         (R08, S3 + 1, 0.55, 0, 0.0, None, True), (R39, S3 + 1, 0.26, 0, 0.0, 160.0, False),
         (R39, S4 + 1, 0.5, 0, 40.0, 120.0, True), (R18, S4 + 6, 0.24, 0, 119.0, 30.0, False)]
def play_len(rid, dur): return RECS[rid]['dur'] if dur is None else dur
TR_SEC = {1: 7, 2: 5, 3: 0, 4: 7}                                                                 # マントラ (ハ長調の五音) を各段落の調に: ト / ヘ (ニ短調の平行調) / ハ / ト
def sec_of(bar): return 1 if bar < S2 else 2 if bar < S3 else 3 if bar < S4 else 4
GMAJ = [0, 2, 4, 7, 9, 5]
def tune_from(rid, lo=62, hi=76, rhythm=(1, 1, 1, 1, 2, 2), ends=((67, 72), (69, 64), (67, 72), (60, 60)), n=4):
    tops = []
    for sg in RECS[rid]['segs']:
        m = sg['m'][-1]
        if sg['d'] < 0.3: continue
        if tops and tops[-1] % 12 == m % 12: continue
        m = min((x for x in range(m - 2, m + 3) if x % 12 in GMAJ), key=lambda x: abs(x - m))
        while m < lo: m += 12
        while m > hi: m -= 12
        if tops and abs(m - tops[-1]) > 7: m = min((m + 12 * k for k in (-1, 0, 1)), key=lambda x: abs(x - tops[-1]))
        while m < lo: m += 12
        while m > hi: m -= 12
        tops.append(m)
    rh = list(rhythm) * n; out = [(d, tops[i % len(tops)]) for i, d in enumerate(rh)]
    for ph in range(n):
        i = ph * len(rhythm) + len(rhythm) - 1; out[i] = (2, min(ends[ph % len(ends)], key=lambda x: abs(x - out[i][1])))
    return out
T8 = tune_from(R08)
MANTRA = T8[:4] + [(4, T8[4][1])]
def mantra(sec, oct_=0): return [(d, m + TR_SEC[sec] + oct_) for d, m in MANTRA]
def aug(mat, k=2): return [(d * k, m) for d, m in mat]
CANDS = {1: ['G', 'Gmaj7', 'D', 'D7', 'Dm7', 'Em', 'Em7', 'C', 'Cmaj7', 'Am', 'Am7', 'Bm', 'Fmaj7', 'G/B', 'C/E'],
         2: ['Dm', 'F', 'C', 'Bb', 'Gm', 'Am', 'A', 'A7', 'Dm/F', 'Bb/D', 'C/E', 'Gm7', 'Fmaj7', 'Bbmaj7', 'Dm7', 'C7'],
         3: ['C', 'Cmaj7', 'Am', 'Am7', 'F', 'Fmaj7', 'Em', 'Em7', 'Dm', 'Dm7', 'G', 'G7', 'E7', 'A7', 'C/E', 'F/A'],
         4: ['G', 'Gmaj7', 'D', 'D7', 'Dm7', 'Em', 'Em7', 'C', 'Cmaj7', 'Am', 'Am7', 'Fmaj7', 'G/B', 'C/E']}
RATE = lambda semis: 2 ** (semis / 12.0)
extras = []; RH = []; RECQ = set()
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
            rc = set(chord(RH[a])['pcs']); rec = a in RECQ; prev = P.harm[a - 1] if a > 0 else None
            def score(c):
                cc = set(chord(c)['pcs'])
                return sum(w * (1 if m % 12 in cc else -0.8) for w, m in notes) + (1.5 if rec else 0.4) * len(cc & rc) / max(1, len(cc)) + ((1.2 if rec else 0.2) if c == RH[a] else 0) - (0.3 if (c == prev and notes) else 0)
            cs = max(cands, key=score)
            for q in range(2): P.harm[a + q] = cs
def tones_of(h, lo, hi):
    c = chord(h); return sorted({min((x for x in range(lo, hi) if x % 12 == p), key=lambda x: abs(x - (lo + hi) / 2)) for p in (c['root'], c['third'], c['fifth'])})
def free(P, v, b0, b1):
    for b in range(b0, b1): P.rest[v].difference_update(range(b * BPB, b * BPB + BPB))



def build():
    P = Piece(TOTAL)
    for q in range(TOTAL * BPB):
        cur = None
        for rid, bar, g, sm, off, dur, lead in PLAYS:
            if not lead: continue
            rec = RECS[rid]; t0 = bar * BPB; db = play_len(rid, dur) / RATE(sm) * BPM / 60.0
            if t0 <= q < t0 + db:
                frac = (q - t0) * 60.0 / BPM * RATE(sm) + off; cur = rec['segs'][0]['ch']
                for s in rec['segs']:
                    if s['t'] <= frac: cur = s['ch']
                cur = transpose_h([[cur]], sm)[0][0]; RECQ.add(q)
        if cur is None: cur = {1: 'G', 2: 'Dm', 3: 'C', 4: 'G'}[sec_of(q // BPB)]
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL):
        P.tempo[k] = BPM
        P.dyn[k] = 0.4 if k < 12 else 0.55 if k < S2 else 0.72 if k < S3 else 0.9 if k < S3 + 40 else 0.75 if k < S4 else max(0.08, 0.7 - 0.025 * (k - S4))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    E = []
    def put(v, b, mat, label=None):
        nb = int(math.ceil(sum(d for d, _ in mat) / BPB)); free(P, v, b, min(TOTAL, b + nb)); P.place(v, b, mat, 0, label); E.append((b * BPB, mat))
    P.section(S1, 'I. 06:39 が表 — 脈とマントラ (ト長調〜ニ・ドリア, ♩=60)', '11/06 06:39 の実音 (表)。BWV 721 の打ち続ける和音 (8 分音符、実音のピアノ) が pp で始まり、トラック 8 の音から作った旋律の頭 (マントラ) がアルトで 4 小節ごとに')
    for k in range(7): put('A', S1 + 10 + 4 * k, mantra(1), 'マントラ (トラック 8 の旋律の頭)' if k == 0 else None)
    P.section(S2, 'II. トラック 18 が表 — マントラが近づく (ニ短調)', 'トラック 18 (全部、表)、トラック 8 が裏に。マントラがアルトとテノールで 2 小節ごとに、脈が強く')
    for k in range(9): put('A', S2 + 2 + 4 * k, mantra(2), None); put('T', S2 + 4 + 4 * k, mantra(2, -12), None)
    P.section(S3, 'III. トラック 8 が表 — 頂点 (ハ長調〜イ短調)', 'トラック 8 (全部、表)、06:39 が裏に。マントラがソプラノ高く・アルト・テノール低くの 3 声で、全句を 2 倍に伸ばしてソプラノが、脈は頂点')
    for k in range(10): put('S', S3 + 2 + 4 * k, mantra(3, 12), 'マントラ 3 声 (頂点)' if k == 0 else None); put('A', S3 + 3 + 4 * k, mantra(3), None); put('T', S3 + 4 + 4 * k, mantra(3, -24), None)
    put('S', S3 + 42, aug(T8), '全句 (2 倍に伸ばして)')
    P.section(S4, 'IV. 06:39 の後半 — 消える (ト長調)', '06:39 の実音の後半 (40 秒から、表)、トラック 18 の終わりが遠くで。脈が少しずつ消え、マントラの頭 (2 音) だけがアルトで 2 小節ごとに、高い共鳴が反響')
    for k in range(14): put('A', S4 + 2 + 2 * k, mantra(4)[:2], '頭だけ' if k == 0 else None)
    for sec, (b0, b1) in {1: (S1, S2), 2: (S2, S3), 3: (S3, S4), 4: (S4, TOTAL)}.items(): harm_fit(P, b0 + 2, min(b1, TOTAL - 3), [e for e in E if b0 * BPB <= e[0] < b1 * BPB], CANDS[sec])
    for b in range(S1 + 6, TOTAL - 6):
        for k in range(BPB * 2):
            h = P.harm[b * BPB + k // 2]; q = b * BPB + k // 2
            P.rest['B'].discard(q); P.place('B', b, [(0.5, tones_of(h, 40, 52)[0])], 0, ('打ち続ける和音 (BWV 721 の脈)' if (b == S1 + 6 and k == 0) else None), beat=k * 0.5)
            tt = tones_of(h, 52, 64)
            if all((b * BPB + j) in P.rest['T'] for j in range(BPB)): P.place('T', b, [(0.5, tt[len(tt) // 2])], 0, None, beat=k * 0.5); P.rest['T'].discard(q)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.5 if bar > 1 else 0.02, fout=6.0, semis=sm, rid=rid + '.wav', tag='%s — 実音 (%s%s)' % (NAMES[rid], '表' if lead else '裏、小さく', '、抜粋' if dur else ''))
    first = True
    for b in range(S2, TOTAL - 6):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 3.6, r, 0.14 * P.dyn.get(b, 0.7) / 0.7, '低いペダルの音 (小節ごと)' if first else None); first = False
    first = True
    for b0, mat in ((S3 + 2, mantra(3, 12) * 5), (S3 + 42, aug(T8))):
        t = b0 * BPB + 2
        for d, m in mat: add('H', t, d, m + 12, 0.08 * P.dyn.get(int(t // BPB), 0.7) / 0.7, '高い共鳴 (反響、pp)' if first else None); first = False; t += d
    for k in range(14):
        b = S4 + 2 + 2 * k; add('H', b * BPB + 1, 3.0, 84, 0.07 * max(0.3, 1 - 0.07 * k), None); add('H', b * BPB + 2.5, 3.0, 79, 0.05 * max(0.3, 1 - 0.07 * k), None)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R39, R18, R08], 'piano_decay': 2.6, 'reverb': [6.0, 2.5, 0.45],
        'title': 'Requiem BADA — CLVII · Mantra a tre nel 06:39',
        'subtitle': '11/06 06:39・トラック 18・トラック 8 で洗脳的な曲に: 06:39 (脈とマントラ) → トラック 18 (マントラが近づく) → トラック 8 (頂点、3 声) → 06:39 の後半 (消える)。マントラ = トラック 8 の音から作った旋律の頭、脈 = BWV 721 の打ち続ける和音 (実音のピアノ)。♩=60',
        'legend': ['PF', 'H', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'H': 'Pf 高い共鳴', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['旋律 = トラック 8 の最上声の音 (ハ長調の五音に寄せて)。マントラはその第 1 句 (4 音 + 伸ばす) を各段落の調 (ト・ヘ・ハ・ト) に。和音は表の録音の採譜を優先しつつ旋律の音を含む和音を半小節ごとに',
                   '3 つの音源は実音、そのまま (段落ごとに表と裏を入れ替える)。4 声は 06:42 の実音のピアノの 1 音のサンプラー。鐘なし、声なし。']}

if __name__ == '__main__':
    print('mantra', ' '.join('%s:%g' % (name_of(m), d) for d, m in MANTRA))
    compose.main(OUT, seed=157, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
