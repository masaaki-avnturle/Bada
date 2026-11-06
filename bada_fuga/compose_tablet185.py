#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLXXXV · Tre registrazioni e il loro pianoforte (2026/11/06 18:54・トラック 8・トラック 18 を重ね合わせて、元の楽器を演奏させて — アルペジオや元の曲に無い楽器は付け加えない)
  テープ: 11/06 18:54 の実音 (rms −22 dB に揃えたもの) を途切れなく 3 回半 (0.5)、トラック 18 (ニ短調、そのまま) を 2 回、トラック 8 (ハ長調 / イ短調 → 4 度上げてヘ長調 / ニ短調に) を 2 回 (全部と続き)
  元の楽器 = 録音の中にある楽器 (ピアノ) だけ: トラック 8・18 の最上声の音から作った旋律 (各 8 小節) を実音のピアノ (06:42 の 1 音のサンプラー) で、トラック 18 が鳴っているときはトラック 18 の旋律、トラック 8 のときはトラック 8 の旋律、両方のときは 2 つを同時に。低いペダルの音 (2 小節ごと)。アルペジオ・パッド・ベース・ドラム・フックは付け加えない
  和音は表の録音 (トラック 18・8) の採譜から、鳴っていないところはニ短調の輪
  使い方: python compose_tablet185.py <bank150.json> <wav のフォルダ (20261106_185402.wav, 20261107_180000.wav, 20261107_080000.wav)> [score_tablet185.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet185.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R42, R18, R08, R1854 = '20261106_064228', '20261107_180000', '20261107_080000', '20261106_185402'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 40, 92, 132, 172
NAMES = {R18: 'トラック 18', R08: 'トラック 8', R1854: '11/06 18:54'}
FILE = {R18: R18 + '.wav', R08: R08 + '.wav', R1854: R1854 + '.wav'}
DUR = {R18: 149.1, R08: 249.2, R1854: 205.8}
PLAYS = [(R1854, k * 50, 0.5, 0, 0.0, 205.8 if k < 3 else 80.0, False) for k in range(4)] + [     # 18:54 を途切れなく
         (R18, 2, 0.55, 0, 0.0, None, True),                                                      # I: トラック 18 (37 小節)
         (R08, S2 + 1, 0.5, 5, 0.0, None, True),                                                  # II: トラック 8 を 4 度上げて (47 小節)
         (R18, S3 + 1, 0.55, 0, 0.0, None, True),                                                 # III: トラック 18 (2 回目)
         (R08, S4 + 1, 0.48, 5, 100.0, 149.2, True)]                                              # IV: トラック 8 の続き (100 秒から)
def play_len(rid, dur): return DUR[rid] if dur is None else dur
def sec_of(bar): return 1 if bar < S2 else 2 if bar < S3 else 3 if bar < S4 else 4
CANDS = ['F', 'Fmaj7', 'Dm', 'Dm7', 'Bb', 'Bbmaj7', 'C', 'C7', 'Gm', 'Gm7', 'Am', 'Am7', 'A7', 'F/A', 'Bb/D', 'C/E', 'Dm/F']
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
    P.section(S1, 'I. トラック 18 (ニ短調, ♩=60)', '18:54 の実音とトラック 18。元の楽器: トラック 18 の旋律を実音のピアノで (アルト → テノール)、低いペダル')
    put('A', 8, T18, 'トラック 18 の旋律 (実音のピアノ)'); put('T', 24, tr(T18, -12), None)
    P.section(S2, 'II. トラック 8 (4 度上げて)', '18:54 とトラック 8 の全部 (ヘ長調 / ニ短調に)。トラック 8 の旋律を実音のピアノで (ソプラノ → テノール → アルト)、トラック 18 の頭がバスで')
    put('S', S2 + 6, T8, 'トラック 8 の旋律 (実音のピアノ)'); put('T', S2 + 20, tr(T8, -12), None); put('B', S2 + 30, aug(tr(T18[:6], -24)), None); put('A', S2 + 36, T8, None)
    P.section(S3, 'III. トラック 18 (2 回目) — 2 つの旋律を同時に', '18:54 とトラック 18。トラック 18 の旋律 (ソプラノ) とトラック 8 の旋律 (テノール) を同時に、2 小節遅れで')
    put('S', S3 + 4, T18, '2 つの旋律を同時に'); put('T', S3 + 6, tr(T8, -12), None); put('A', S3 + 20, T18, None); put('B', S3 + 22, tr(T8, -24), None)
    P.section(S4, 'IV. トラック 8 の続き — 消える', '18:54 とトラック 8 の続き。旋律の頭を 2 倍に伸ばして、ペダルだけが残って消える')
    put('T', S4 + 4, aug(tr(T8[:6], -12)), '頭を 2 倍に'); put('B', S4 + 12, aug(tr(T18[:6], -24)), None); put('A', S4 + 20, aug(T8[:6]), None)
    harm_fit(P, 1, TOTAL - 3, E, CANDS)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if L > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — 実音%s' % (NAMES[rid], '、途切れなく 3 回半' if rid == R1854 else ('、4 度上げて' if sm else '、そのまま')))
    first = True
    for b in range(2, TOTAL - 6, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.6, r, 0.12 * P.dyn.get(b, 0.6) / 0.6, '低いペダルの音 (2 小節ごと)' if first else None); first = False

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R18, R08, R1854], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CLXXXV · Tre registrazioni e il loro pianoforte',
        'subtitle': '11/06 18:54・トラック 8・トラック 18 を重ね合わせて、元の楽器 (録音の中のピアノ) を演奏させて: トラック 8・18 の旋律を実音のピアノで、低いペダル。アルペジオや元の曲に無い楽器は付け加えない。ニ短調 / ヘ長調、♩=60',
        'legend': ['PF', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['18:54 は rms −22 dB に揃えて途切れなく 3 回半 (0.5)。トラック 18 (ニ短調) はそのまま 2 回 (0.55)、トラック 8 は 4 度上げてヘ長調 / ニ短調に (0.5)。和音は表の録音の採譜を優先しつつ旋律の音を含む和音を半小節ごとに',
                   '楽器 = トラック 8・18 の最上声の音から作った旋律 (各 8 小節) を 06:42 の実音のピアノの 1 音のサンプラーで、2 小節ごとの低いペダル。鐘なし、声なし、他の楽器なし。']}

if __name__ == '__main__':
    print('T8', ' '.join('%s:%g' % (name_of(m), d) for d, m in T8[:6]), '| T18', ' '.join('%s:%g' % (name_of(m), d) for d, m in T18[:6]))
    compose.main(OUT, seed=185, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
