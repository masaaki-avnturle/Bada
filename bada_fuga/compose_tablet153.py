#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLIII · Sonnifero ipnotico (2026/11/06 の 2 曲・tablet152・tablet117 で、洗脳的な睡眠導入剤の曲を)
  4 つの音源 (すべて実音、そのまま; 11/06 は喘ぎの区間だけ下げて) を眠りの段階に沿って表と裏を入れ替えながら敷く:
    I.  くつろぎ   06:39 が表、tablet117 の始めが裏
    II. 暖まり     tablet152 (二重フーガの段落) が表、06:42 が裏
    III. 冷え      06:42 が表、tablet152 の終わりが裏
    IV. 眠り       tablet117 の眠りの段階が表、06:39 の終わりが遠くで — すべて消えていく
  洗脳的に: 06:42 の音から作った眠りの動機 (4 音 + 伸ばす、2 倍に伸ばして) を各段階の調で 8 小節ごと → 4 小節ごとに繰り返す、2 分音符の鼓動 (実音のピアノ、pp) が全曲、眠りでは 1 小節に 1 つになって消える。強弱は段階ごとに落ちる (0.45 → 0.1)
  音源: 4 声は 11/06 06:42 の実音のピアノの 1 音 (サンプラー)、低いペダルと高い共鳴は合成のピアノ。鐘なし、声なし、電子音なし
  使い方: python compose_tablet153.py <bank153.json> <wav のフォルダ> [score_tablet153.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet153.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R39, R42, R152, R117 = '20261106_063938', '20261106_064228', '20261107_152000', '20261003_117000'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 40, 102, 160, 198
NAMES = {R39: '11/06 06:39', R42: '11/06 06:42', R152: 'tablet152', R117: 'tablet117'}
FILE = {R39: R39 + '_clean.wav', R42: R42 + '_clean.wav', R152: R152 + '.wav', R117: R117 + '.wav'}
PLAYS = [(R39, 1, 0.55, 0, 0.0, None, True), (R117, 0, 0.22, 0, 0.0, 160.0, False),
         (R152, S2 + 1, 0.5, 0, 160.0, 240.0, True), (R42, S2 + 1, 0.22, 0, 0.0, 227.0, False),
         (R42, S3 + 1, 0.5, 0, 0.0, None, True), (R152, S3 + 1, 0.2, 0, 560.0, 120.0, False),
         (R117, S4 + 1, 0.48, 0, 564.0, 140.0, True), (R39, S4 + 4, 0.16, 0, 110.0, 50.0, False)]
def play_len(rid, dur): return RECS[rid]['dur'] if dur is None else dur
TR_SEC = {1: 2, 2: 0, 3: 0, 4: -7}                                                                 # 動機 (ヘ長調) を各段階の調に: ト / ヘ (tablet152 はハ〜ニ短) / ヘ / 変ロ
def sec_of(bar): return 1 if bar < S2 else 2 if bar < S3 else 3 if bar < S4 else 4
GMAJ = [5, 7, 9, 0, 2, 10]                                                                        # ヘ長調の五音 (ファ・ソ・ラ・ド・レ) + シ♭
def tune_from(rid, lo=62, hi=76, rhythm=(1, 1, 1, 1, 2, 2), ends=((72, 65), (69, 74), (72, 65), (65, 65)), n=4):
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
T42 = tune_from(R42)
LULL = [(2, m) for d, m in T42[:4]] + [(8, T42[4][1])]
def lull(sec, oct_=0): return [(d, m + TR_SEC[sec] + oct_) for d, m in LULL]
CANDS = {1: ['G', 'Gmaj7', 'D', 'D7', 'Em', 'Em7', 'C', 'Cmaj7', 'Am', 'Am7', 'Bm', 'Dm7', 'G/B', 'C/E'],
         2: ['C', 'Cmaj7', 'Am', 'Am7', 'F', 'Fmaj7', 'Dm', 'Dm7', 'G', 'G7', 'Em7', 'Bb', 'C/E', 'F/A', 'Dm/F', 'Gm7'],
         3: ['F', 'Fmaj7', 'C', 'Cmaj7', 'Dm', 'Dm7', 'Bb', 'Gm', 'Gm7', 'Am', 'E', 'C/E', 'F/A', 'Bb/D', 'Csus4'],
         4: ['Bb', 'Eb', 'F', 'F7', 'Gm', 'Cm', 'Dm', 'Bb/D', 'Eb/G', 'F/A', 'Cm7', 'Bbmaj7', 'Bbm', 'Ebm', 'Db']}
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
        if cur is None: cur = {1: 'G', 2: 'C', 3: 'F', 4: 'Bb'}[sec_of(q // BPB)]
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL):
        P.tempo[k] = BPM
        P.dyn[k] = 0.45 if k < S2 else 0.42 if k < S3 else 0.34 if k < S4 else max(0.1, 0.3 - 0.006 * (k - S4))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    E = []
    def put(v, b, mat, label=None):
        nb = int(math.ceil(sum(d for d, _ in mat) / BPB)); free(P, v, b, min(TOTAL, b + nb)); P.place(v, b, mat, 0, label); E.append((b * BPB, mat))
    P.section(S1, 'I. くつろぎ — 06:39 が表 (ト長調, ♩=60)', '11/06 06:39 の実音 (表)、tablet117 の始めが裏に小さく。2 分音符の鼓動 (実音のピアノ、pp) が始まり、眠りの動機 (06:42 の音から、2 倍に伸ばして) がアルトで 8 小節ごとに')
    for k in range(4): put('A', S1 + 8 + 8 * k, lull(1), '眠りの動機 (アルト、8 小節ごと)' if k == 0 else None)
    P.section(S2, 'II. 暖まり — tablet152 が表 (ハ長調〜ニ短調)', 'tablet152 (二重フーガの段落、160 秒から、表)、06:42 が裏に。動機がソプラノとテノールで 4 小節ごとに交互、高い共鳴が反響')
    for k in range(7): put('S', S2 + 4 + 8 * k, lull(2), '動機 (4 小節ごとに交互)' if k == 0 else None); put('T', S2 + 8 + 8 * k, lull(2, -12), None)
    P.section(S3, 'III. 冷え — 06:42 が表 (ヘ長調)', '06:42 の実音 (全部、表)、tablet152 の終わりが裏に。動機がヘ長調 (そのまま) でアルト pp とテノール (2 オクターヴ下) に交互、強弱は落ちる')
    for k in range(7): put('A', S3 + 4 + 8 * k, lull(3), '動機 (pp)' if k == 0 else None); put('T', S3 + 8 + 8 * k, lull(3, -24), None)
    P.section(S4, 'IV. 眠り — tablet117 の眠りの段階が表 (変ロ長調)', 'tablet117 の眠りの段階 (564 秒から、表)、06:39 の終わりが遠くで。動機の頭 (2 音) だけがアルトで 4 小節ごと、鼓動は 1 小節に 1 つになって消える')
    for k in range(8): put('A', S4 + 2 + 4 * k, lull(4)[:2], '動機の頭だけ' if k == 0 else None)
    for sec, (b0, b1) in {1: (S1, S2), 2: (S2, S3), 3: (S3, S4), 4: (S4, TOTAL)}.items(): harm_fit(P, b0 + 2, min(b1, TOTAL - 3), [e for e in E if b0 * BPB <= e[0] < b1 * BPB], CANDS[sec])
    for b in range(S1 + 4, TOTAL - 4):
        beats = (0, 2) if b < S4 + 10 else (0,)
        for k in beats:
            h = P.harm[b * BPB + k]; q = b * BPB + k
            P.rest['B'].discard(q); P.rest['B'].discard(q + 1); P.place('B', b, [(1.9, tones_of(h, 40, 52)[0])], 0, ('鼓動 (2 分音符の根音、pp)' if (b == S1 + 4 and k == 0) else None), beat=k)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.5 if bar > 1 else 0.02, fout=8.0, semis=sm, rid=rid + '.wav', tag='%s — 実音 (%s%s)' % (NAMES[rid], '表' if lead else '裏、小さく', '、抜粋' if dur else ''))
    first = True
    for b in range(S1 + 4, TOTAL - 4, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.5, r, 0.1 * P.dyn.get(b, 0.4) / 0.4, '低いペダルの音 (2 小節ごと、pp)' if first else None); first = False
    first = True
    for b0, sec in ((S2 + 4, 2), (S3 + 4, 3)):
        t = b0 * BPB + 2
        for d, m in lull(sec): add('H', t, d, m + 12, 0.06, '高い共鳴 (動機の反響、pp)' if first else None); first = False; t += d
    for k, b in enumerate(range(S4 + 2, TOTAL - 4, 4)): add('H', b * BPB + 1, 5.0, 82, 0.05 * max(0.2, 1 - 0.1 * k), None)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R39, R117, R152, R42], 'piano_decay': 2.6, 'reverb': [7.0, 3.0, 0.5],
        'title': 'Requiem BADA — CLIII · Sonnifero ipnotico',
        'subtitle': '11/06 06:39・06:42・tablet152・tablet117 で、洗脳的な睡眠導入剤の曲を: くつろぎ (06:39) → 暖まり (tablet152 の二重フーガ) → 冷え (06:42) → 眠り (tablet117 の眠りの段階)。06:42 の音から作った眠りの動機を各段階の調で繰り返し、2 分音符の鼓動が消えていく。♩=60',
        'legend': ['PF', 'H', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'H': 'Pf 高い共鳴', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['眠りの動機 = 06:42 の最上声の音 (ヘ長調の五音に寄せて) の第 1 句 (4 音 + 伸ばす、2 倍に) を各段階の調 (ト・ハ〜ニ短・ヘ・変ロ) に。和音は表の録音の採譜を優先しつつ動機の音を含む和音を半小節ごとに',
                   '4 つの音源は実音、そのまま。4 声は 06:42 の実音のピアノの 1 音のサンプラー。強弱は 0.45 → 0.1 へ。鐘なし、声なし、電子音なし。']}

if __name__ == '__main__':
    print('lull', ' '.join('%s:%g' % (name_of(m), d) for d, m in LULL))
    compose.main(OUT, seed=153, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.6, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
