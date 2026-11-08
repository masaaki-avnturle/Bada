#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXCV · Il 13:40 e le due tracce sul 86 (2026/11/08 13:40・tablet86・トラック 18・トラック 8 を重ね合わせて、元の楽器を演奏させて — アルペジオや元の曲に無い楽器は付け加えない)
  調は tablet86 (LXXXVI、ト長調 / ホ短調、実音のピアノの 1 音のサンプラーだけで作った曲) に揃える: トラック 18 (ニ短調) は全音上げてホ短調に、トラック 8 (ハ長調 / イ短調) は 5 度上げてト長調 / ホ短調に、13:40 (ホ長調 / 嬰ハ短調、3 分 51 秒、静かなので rms −21 dB に揃えて) は短 3 度上げてト長調 / ホ短調に
  テープ: tablet86 を全曲 2 回 (0.45 / 0.4)、トラック 18 を 2 回、トラック 8 を全部と続き、13:40 を 1 回 (0.5)
  元の楽器 = 録音と tablet86 の中にある楽器 (ピアノ) だけ: tablet86・トラック 18・トラック 8・13:40 の最上声の音から作った旋律 (各 8 小節、ト長調 / ホ短調に寄せて) を実音のピアノ (06:42 の 1 音のサンプラー) で、低いペダルの音 (2 小節ごと)。アルペジオ・パッド・ベース・ドラム・フックは付け加えない
  和音は表の録音の採譜から (トラック 18・8・13:40 が優先、ないところは tablet86)
  使い方: python compose_tablet195.py <bank195.json (bank194 + 13:40 の採譜)> <wav のフォルダ> [score_tablet195.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet195.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R42, R86, R18, R08, R1340 = '20261106_064228', '20261107_086000', '20261107_180000', '20261107_080000', '20261108_134014'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 44, 86, 136, 176
NAMES = {R86: 'tablet86', R18: 'トラック 18', R08: 'トラック 8', R1340: '11/08 13:40'}
FILE = {R86: R86 + '.wav', R18: R18 + '.wav', R08: R08 + '.wav', R1340: R1340 + '.wav'}
DUR = {R86: 245.0, R18: 149.1, R08: 249.2, R1340: 231.1}
PLAYS = [(R86, 0, 0.45, 0, 0.0, None, True), (R86, 100, 0.4, 0, 0.0, None, True),                   # tablet86 を全曲 2 回 (ト長調、そのまま)
         (R18, 2, 0.5, 2, 0.0, None, True),                                                       # I: トラック 18 を全音上げてホ短調に (35 小節)
         (R08, S2, 0.5, 7, 0.0, None, True),                                                      # II: トラック 8 を 5 度上げて (42 小節)
         (R1340, S3, 0.5, 3, 0.0, None, True),                                                    # III: 13:40 を短 3 度上げて (49 小節)
         (R18, S4, 0.5, 2, 0.0, None, True), (R08, S4 + 20, 0.45, 7, 110.0, 139.0, True)]         # IV: トラック 18 (2 回目) とトラック 8 の続き
def play_len(rid, dur): return DUR[rid] if dur is None else dur
def sec_of(bar): return 1 if bar < S2 else 2 if bar < S3 else 3 if bar < S4 else 4
CANDS = ['G', 'Gmaj7', 'Em', 'Em7', 'C', 'Cmaj7', 'D', 'D7', 'Am', 'Am7', 'Bm', 'Bm7', 'B7', 'G/B', 'C/E', 'D/F#', 'Em/G']
LOOP = ['Em', 'C', 'G', 'D']
SCALE = [7, 9, 11, 0, 2, 4, 6]
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
ENDS_G = ((74, 79), (71, 67), (74, 79), (67, 67))
T86 = tune_from(R86, 0, ends=ENDS_G); T18 = tune_from(R18, 2, ends=ENDS_G); T8 = tune_from(R08, 7, ends=ENDS_G); T40 = tune_from(R1340, 3, ends=ENDS_G)   # 4 つの旋律 (ト長調 / ホ短調に寄せて)
def tr(mat, o): return [(d, m + o) for d, m in mat]
def aug(mat, k=2): return [(d * k, m) for d, m in mat]
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
            if not lead: continue
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
        P.dyn[k] = 0.5 if k < S2 else 0.6 if k < S3 else 0.7 if k < S4 else max(0.1, 0.6 - 0.016 * (k - S4))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    E = []
    def put(v, b, mat, label=None):
        mat = clip(mat, (TOTAL - 3 - b) * BPB); t = b * BPB
        for d, m in mat: P.rest[v].difference_update(range(int(math.floor(t)), int(math.ceil(t + d - 1e-9)))); t += d
        P.place(v, b, mat, 0, label); E.append((b * BPB, mat))
    P.section(S1, 'I. トラック 18 (ホ短調, ♩=60)', 'tablet86 (ト長調) の上にトラック 18 (全音上げて)。元の楽器: トラック 18 の旋律を実音のピアノで (アルト → テノール)、tablet86 の旋律がバスで、低いペダル')
    put('A', 6, T18, 'トラック 18 の旋律 (実音のピアノ)'); put('T', 20, tr(T18, -12), None); put('B', 32, tr(T86, -24), 'tablet86 の旋律')
    P.section(S2, 'II. トラック 8 (5 度上げて)', 'tablet86 の上にトラック 8 の全部 (ト長調 / ホ短調に)。トラック 8 の旋律 (ソプラノ → テノール)、tablet86 の旋律 (アルト)')
    put('S', S2 + 4, T8, 'トラック 8 の旋律 (実音のピアノ)'); put('T', S2 + 16, tr(T8, -12), None); put('A', S2 + 28, T86, None)
    P.section(S3, 'III. 13:40 (短 3 度上げて)', 'tablet86 (2 回目) の上に 11/08 13:40 の全部。13:40 の旋律 (ソプラノ → アルト)、トラック 18 とトラック 8 の旋律を同時に (テノールとバス)')
    put('S', S3 + 4, T40, '13:40 の旋律 (実音のピアノ)'); put('A', S3 + 18, T40, None); put('T', S3 + 30, tr(T18, -12), None); put('B', S3 + 32, tr(T8, -24), None)
    P.section(S4, 'IV. トラック 18 (2 回目) とトラック 8 の続き — 消える', 'tablet86 の終わりの上にトラック 18 をもう一度、トラック 8 の続き。4 つの旋律の頭を 2 倍に伸ばして、ペダルだけが残って消える')
    put('A', S4 + 4, aug(T18[:6]), '頭を 2 倍に'); put('T', S4 + 12, aug(tr(T86[:6], -12)), None); put('B', S4 + 20, aug(tr(T8[:6], -24)), None); put('S', S4 + 26, aug(T40[:6]), None)
    harm_fit(P, 1, TOTAL - 3, E, CANDS)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if L > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — 実音%s' % (NAMES[rid], {2: '、全音上げて', 7: '、5 度上げて', 3: '、短 3 度上げて', 0: '、全曲そのまま (ト長調)'}[sm] + ('、続き' if off else '')))
    first = True
    for b in range(2, TOTAL - 6, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.6, r, 0.12 * P.dyn.get(b, 0.6) / 0.6, '低いペダルの音 (2 小節ごと)' if first else None); first = False

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R18, R08, R1340, R86], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CXCV · Il 13:40 e le due tracce sul 86',
        'subtitle': '11/08 13:40・tablet86・トラック 18・トラック 8 を重ね合わせて、元の楽器 (4 つの旋律を実音のピアノで、低いペダル) を演奏させて。調は tablet86 のト長調 / ホ短調に揃える (トラック 18 は全音上げ、トラック 8 は 5 度上げ、13:40 は短 3 度上げ)。アルペジオや元の曲に無い楽器は付け加えない。♩=60',
        'legend': ['PF', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['tablet86 (LXXXVI、実音のピアノの 1 音だけで作った曲) は全曲そのまま 2 回 (0.45 / 0.4)。トラック 18 (ニ短調) は全音上げて 2 回、トラック 8 (ハ長調 / イ短調) は 5 度上げて全部と続き、13:40 (ホ長調 / 嬰ハ短調) は rms −21 dB に揃えて短 3 度上げて 1 回 (0.5)。和音は表の録音の採譜を優先しつつ旋律の音を含む和音を半小節ごとに',
                   '楽器 = tablet86・トラック 18・トラック 8・13:40 の最上声の音から作った旋律 (各 8 小節) を 06:42 の実音のピアノの 1 音のサンプラーで、2 小節ごとの低いペダル。鐘なし、声なし、他の楽器なし。']}

if __name__ == '__main__':
    print('T40', ' '.join('%s:%g' % (name_of(m), d) for d, m in T40[:6]), '| T86', ' '.join('%s:%g' % (name_of(m), d) for d, m in T86[:6]))
    compose.main(OUT, seed=195, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
