#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLIV · Purificazione nel sonno (tablet152 と tablet117 の 2 曲で、洗脳的に、睡眠導入剤の心が清らかになる曲を)
  2 つの音源 (実音、そのまま) を眠りの段階に沿って表と裏を入れ替えながら敷く:
    I.  くつろぎ   tablet117 の始め (変ロ短調) が表、tablet152 の始め (06:39 の空気) が裏
    II. 清め       tablet152 の二重フーガの段落 (ハ長調〜ニ短調) が表、tablet117 の暖まり (ヘ長調) が裏
    III. 冷え      tablet117 の冷え (ヘ短調) が表、tablet152 のストレッタが裏
    IV. 眠り       tablet117 の眠り (変ロ長調) が表、tablet152 の終わり (06:39) が遠くで — 消えていく
  心が清らかに: 高い開いた 5 度の共鳴 (合成のピアノ、pp) が各段落の調で 4 小節ごとに澄んで鳴り、全音符の根音の鼓動 (実音のピアノ、1 小節に 1 つ) が静かに続く。tablet152 の音から作った清めの動機 (上って伸ばす 5 音、2 倍に) をアルト → ソプラノが 8 小節ごと → 4 小節ごとに繰り返す (洗脳)。強弱は 0.42 → 0.1
  音源: 4 声は 11/06 06:42 の実音のピアノの 1 音 (サンプラー)。鐘なし、声なし、電子音なし
  使い方: python compose_tablet154.py <bank153.json> <wav のフォルダ> [score_tablet154.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet154.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R152, R117, R42 = '20261107_152000', '20261003_117000', '20261106_064228'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 40, 100, 150, 190
NAMES = {R152: 'tablet152', R117: 'tablet117'}
FILE = {R152: R152 + '.wav', R117: R117 + '.wav'}
PLAYS = [(R117, 1, 0.55, 0, 0.0, 158.0, True), (R152, 1, 0.22, 0, 0.0, 158.0, False),
         (R152, S2 + 1, 0.5, 0, 160.0, 236.0, True), (R117, S2 + 1, 0.22, 0, 160.0, 236.0, False),
         (R117, S3 + 1, 0.5, 0, 320.0, 196.0, True), (R152, S3 + 1, 0.2, 0, 408.0, 150.0, False),
         (R117, S4 + 1, 0.48, 0, 564.0, 150.0, True), (R152, S4 + 4, 0.16, 0, 560.0, 120.0, False)]
def play_len(rid, dur): return RECS[rid]['dur'] if dur is None else dur
TR_SEC = {1: 1, 2: 0, 3: 8, 4: -2}                                                                 # 動機 (ハ長調の五音) を各段落の調に: 変ニ / ハ / 変イ / 変ロ
FIFTH = {1: 73, 2: 72, 3: 68, 4: 70}                                                               # 高い開いた 5 度の根 (レ♭5 / ド5 / ラ♭4 / シ♭4) + 12
def sec_of(bar): return 1 if bar < S2 else 2 if bar < S3 else 3 if bar < S4 else 4
GMAJ = [0, 2, 4, 7, 9]
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
T152 = tune_from(R152)
_asc = sorted({m for _, m in T152[:6]})[:4]                                                        # 清めの動機: 第 1 句の音を低い方から上って、最後を伸ばす
PURE = [(2, m) for m in _asc] + [(8, _asc[-1] + 12 if _asc[-1] + 12 <= 79 else _asc[-1])]
def pure(sec, oct_=0): return [(d, m + TR_SEC[sec] + oct_) for d, m in PURE]
CANDS = {1: ['Db', 'Gb', 'Ab', 'Bbm', 'Ebm', 'Fm', 'Db/F', 'Gb/Bb', 'Ab/C', 'Bbm/Db', 'Dbmaj7', 'Ebm7'],
         2: ['C', 'Cmaj7', 'Am', 'Am7', 'F', 'Fmaj7', 'Dm', 'Dm7', 'G', 'Em7', 'C/E', 'F/A', 'Dm/F', 'G/B'],
         3: ['Ab', 'Db', 'Eb', 'Fm', 'Bbm', 'Cm', 'Ab/C', 'Db/F', 'Eb/G', 'Fm/Ab', 'Abmaj7', 'Bbm7'],
         4: ['Bb', 'Eb', 'F', 'Gm', 'Cm', 'Dm', 'Bb/D', 'Eb/G', 'F/A', 'Cm7', 'Bbmaj7', 'Gm7']}
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
        if cur is None: cur = {1: 'Db', 2: 'C', 3: 'Ab', 4: 'Bb'}[sec_of(q // BPB)]
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL):
        P.tempo[k] = BPM
        P.dyn[k] = 0.42 if k < S2 else 0.4 if k < S3 else 0.33 if k < S4 else max(0.1, 0.3 - 0.006 * (k - S4))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    E = []
    def put(v, b, mat, label=None):
        nb = int(math.ceil(sum(d for d, _ in mat) / BPB)); free(P, v, b, min(TOTAL, b + nb)); P.place(v, b, mat, 0, label); E.append((b * BPB, mat))
    P.section(S1, 'I. くつろぎ — tablet117 の始めが表 (変ロ短調 / 変ニ長調, ♩=60)', 'tablet117 の始め (表)、tablet152 の始め (06:39 の空気) が裏に小さく。全音符の鼓動 (実音のピアノ、pp) が始まり、高い開いた 5 度の共鳴が澄んで鳴り、清めの動機 (上って伸ばす) がアルトで 8 小節ごとに')
    for k in range(4): put('A', S1 + 8 + 8 * k, pure(1), '清めの動機 (アルト、8 小節ごと)' if k == 0 else None)
    P.section(S2, 'II. 清め — tablet152 の二重フーガが表 (ハ長調〜ニ短調)', 'tablet152 の二重フーガの段落 (表)、tablet117 の暖まり (ヘ長調) が裏に。動機がソプラノとアルトで 4 小節ごとに交互、高い 5 度の共鳴が澄む')
    for k in range(7): put('S', S2 + 4 + 8 * k, pure(2), '動機 (4 小節ごとに交互)' if k == 0 else None); put('A', S2 + 8 + 8 * k, pure(2, -12), None)
    P.section(S3, 'III. 冷え — tablet117 の冷えが表 (ヘ短調 / 変イ長調)', 'tablet117 の冷え (表)、tablet152 のストレッタが裏に。動機が変イ長調でアルト pp とテノール (低く) に交互、強弱は落ちる')
    for k in range(6): put('A', S3 + 4 + 8 * k, pure(3), '動機 (pp)' if k == 0 else None); put('T', S3 + 8 + 8 * k, pure(3, -24), None)
    P.section(S4, 'IV. 眠り — tablet117 の眠りが表 (変ロ長調)', 'tablet117 の眠りの段階 (表)、tablet152 の終わりが遠くで。動機の頭 (2 音) だけがアルトで 4 小節ごと、高い 5 度の共鳴だけが残って消える')
    for k in range(8): put('A', S4 + 2 + 4 * k, pure(4)[:2], '動機の頭だけ' if k == 0 else None)
    for sec, (b0, b1) in {1: (S1, S2), 2: (S2, S3), 3: (S3, S4), 4: (S4, TOTAL)}.items(): harm_fit(P, b0 + 2, min(b1, TOTAL - 3), [e for e in E if b0 * BPB <= e[0] < b1 * BPB], CANDS[sec])
    for b in range(S1 + 4, TOTAL - 4):                                                              # 鼓動: 全音符の根音 (バス、1 小節に 1 つ)
        h = P.harm[b * BPB]
        for j in range(BPB): P.rest['B'].discard(b * BPB + j)
        P.place('B', b, [(3.8, tones_of(h, 40, 52)[0])], 0, '鼓動 (全音符の根音、pp)' if b == S1 + 4 else None)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.5 if bar > 1 else 0.02, fout=8.0, semis=sm, rid=rid + '.wav', tag='%s — 実音 (%s、抜粋)' % (NAMES[rid], '表' if lead else '裏、小さく'))
    first = True
    for b in range(S1 + 2, TOTAL - 4, 4):                                                          # 高い開いた 5 度の共鳴 (清らかに)
        sec = sec_of(b); r = FIFTH[sec] + 12; g = 0.07 * P.dyn.get(b, 0.4) / 0.4
        add('H', b * BPB, 15.5, r, g, '高い開いた 5 度の共鳴 (pp、清らかに)' if first else None); add('H', b * BPB + 0.05, 15.5, r + 7, g * 0.8); first = False
    first = True
    for b in range(S1 + 4, TOTAL - 4, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.5, r, 0.09 * P.dyn.get(b, 0.4) / 0.4, '低いペダルの音 (2 小節ごと、pp)' if first else None); first = False

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R117, R152], 'piano_decay': 2.6, 'reverb': [8.0, 3.5, 0.55],
        'title': 'Requiem BADA — CLIV · Purificazione nel sonno',
        'subtitle': 'tablet152 と tablet117 の 2 曲で、洗脳的に、睡眠導入剤の心が清らかになる曲を: くつろぎ (tablet117 の始め) → 清め (tablet152 の二重フーガ) → 冷え (tablet117 の冷え) → 眠り (tablet117 の眠り)。高い開いた 5 度の共鳴が澄み、全音符の鼓動と清めの動機 (上って伸ばす) が繰り返して消える。♩=60',
        'legend': ['PF', 'H', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'H': 'Pf 高い 5 度の共鳴', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['清めの動機 = tablet152 の旋律の第 1 句の音を低い方から上って最後を伸ばす (5 音、2 倍に) を各段階の調 (変ニ・ハ・変イ・変ロ) に。和音は表の録音の採譜を優先しつつ動機の音を含む和音を半小節ごとに',
                   '2 つの音源は実音、そのまま (抜粋、表と裏)。4 声は 06:42 の実音のピアノの 1 音のサンプラー。強弱は 0.42 → 0.1 へ。鐘なし、声なし、電子音なし。']}

if __name__ == '__main__':
    print('pure', ' '.join('%s:%g' % (name_of(m), d) for d, m in PURE))
    compose.main(OUT, seed=154, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.6, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
