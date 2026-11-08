#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCXXV · L'aureola sensuale sull'89 e l'86 con il pianoforte intero (tablet224 に、元からある楽器も省かずに、雑音も戻して)
  テープ: ドエロの光輪様の声 (息のノイズ層あり — 元の CCXIX / CCXX の声、rms −22.5 dB) を 2 回 (0.6)、tablet89 を全曲 (0.45) と後半 (0.4)、tablet86 を 2 半音下げて全曲 (0.4) と後半 (0.35)
  元の楽器 (実音のピアノ) を省かずに: tablet89・tablet86・声の採譜の旋律 (各 8 小節) を 06:42 の実音のピアノで全段落に途切れなく (CCXXIV では間が空いていた)、音量 0.42 → 0.55、低いペダル (2 小節ごと)。アルペジオ・パッド・ベース・ドラム・フック・鐘は付け加えない
  使い方: python compose_tablet225.py <bank201.json> <wav のフォルダ (20261108_145525.wav = ドエロの光輪の声 (雑音あり), 20261107_089000.wav, 20261107_086000.wav)> [score_tablet225.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet225.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R42, R89, RV, R86 = '20261106_064228', '20261107_089000', '20261108_145525', '20261107_086000'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 50, 100, 140, 176
NAMES = {R89: 'tablet89', RV: '11/08 14:55 の声 (ドエロの光輪様の声、雑音あり)', R86: 'tablet86'}
FILE = {R89: R89 + '.wav', RV: RV + '.wav', R86: R86 + '.wav'}
DUR = {R89: 391.0, RV: 198.5, R86: 245.0}
PLAYS = [(RV, 2, 0.6, 0, 0.0, None, True), (RV, S3 + 2, 0.6, 0, 0.0, None, True),                 # 光輪の声を I と III に
         (R89, 0, 0.45, 0, 0.0, None, True),                                                       # I〜II: tablet89 全曲 (98 小節)
         (R89, S3, 0.4, 0, 90.0, 300.0, True),
         (R86, S2 + 2, 0.4, -2, 0.0, None, False), (R86, S4, 0.35, -2, 120.0, 125.0, False)]        # tablet86 (2 半音下げて) を II〜III に全曲、IV に後半 (裏)                                                   # III〜IV: tablet89 の後半 (90 秒から、終わりまで)
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
T89 = tune_from(R89, 0); T89b = tune_from(R89, 0, lo=55, hi=69, ends=((62, 69), (57, 62), (62, 69), (62, 62))); TV = tune_from(RV, 0, ends=((72, 77), (69, 65), (72, 77), (65, 65))); T86 = tune_from(R86, -2)   # tablet89 の旋律 (ニ短調 / ヘ長調) と低い形
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
    P.section(S1, 'I. tablet89 の始まり (ニ短調, ♩=60)', 'ドエロの光輪様の声 (雑音なし) と tablet89 (レクイエム)。元の楽器: tablet89 の旋律 (アルト) と声の旋律 (テノール → ソプラノ) を実音のピアノで、低いペダル')
    put('A', 2, T89, 'tablet89 の旋律 (実音のピアノ)'); put('T', 10, tr(TV, -12), '声の旋律'); put('B', 18, tr(T86, -24), 'tablet86 の旋律'); put('S', 26, TV, None); put('A', 34, T86, None); put('T', 42, tr(T89, -12), None); put('B', 42, tr(T89b, -12), None)
    P.section(S2, 'II. tablet89 のフーガ', 'tablet89 の続き (フーガ) と tablet86。旋律を 2 声で (ソプラノとテノール、2 小節遅れ)、低い形をバスで、声と tablet86 の旋律も続けて')
    put('S', S2 + 2, T89, '2 声で'); put('T', S2 + 4, tr(T89, -12), None); put('B', S2 + 10, tr(T89b, -12), None); put('A', S2 + 18, TV, None); put('S', S2 + 26, T86, None); put('T', S2 + 34, tr(T86, -12), None); put('A', S2 + 42, T89, None); put('B', S2 + 42, tr(TV, -24), None)
    P.section(S3, 'III. tablet89 の後半 (2 回目)', '光輪の声をもう一度、tablet89 の後半 (90 秒から)、tablet86 の続き。3 つの録音の旋律を途切れなく')
    put('A', S3 + 2, TV, None); put('B', S3 + 4, tr(T89b, -12), None); put('S', S3 + 10, T89, None); put('T', S3 + 18, tr(T86, -12), None); put('A', S3 + 26, T86, None); put('S', S3 + 28, TV, None); put('B', S3 + 34, tr(T89, -24), None)
    P.section(S4, 'IV. tablet89 の終わり — 消える', 'tablet89 の終わりと声の終わり、tablet86 の後半。旋律を続け、最後は頭を 2 倍に伸ばして、ペダルだけが残って消える')
    put('T', S4 + 2, tr(TV, -12), None); put('A', S4 + 2, T89, None); put('S', S4 + 10, T86, None); put('B', S4 + 10, tr(T89b, -12), None); put('A', S4 + 18, aug(T89[:6]), '頭を 2 倍に'); put('T', S4 + 24, aug(tr(T86[:6], -12)), None)
    harm_fit(P, 1, TOTAL - 3, E, CANDS)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if L > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — 実音%s' % (NAMES[rid], '、ドエロの光輪の声 (息の雑音あり)' if rid == RV else (('、2 半音下げて' if sm else '') + ('、全曲' + ('' if sm else 'そのまま') if dur is None else '、後半 (%d 秒から)' % off))))
    first = True
    for b in range(2, TOTAL - 6, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.6, r, 0.12 * P.dyn.get(b, 0.6) / 0.6, '低いペダルの音 (2 小節ごと)' if first else None); first = False

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [RV, R89, R86], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCXXV · L\'aureola sensuale sull\'89 e l\'86 con il pianoforte intero',
        'subtitle': 'tablet224 に、元からある楽器 (3 つの録音の旋律を実音のピアノで全段落に途切れなく、低いペダル) も省かずに、声は息の雑音のある元のドエロの光輪様の声に戻して。アルペジオや元の曲に無い楽器は付け加えない。ニ短調 / ヘ長調、♩=60',
        'legend': ['PF', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['光輪の声 = CCXIX / CCXX と同じ (息のノイズ層あり、rms −22.5 dB) を 2 回 (0.6)。tablet89 (LXXXIX) は全曲そのまま 0.45、後半 (90 秒から) をもう一度 0.4。tablet86 (LXXXVI) は 2 半音下げて全曲 0.4 (II〜III)、後半 (120 秒から) 0.35 (IV)。和音は表の録音の採譜 (音声から build_sampler で) を優先しつつ旋律の音を含む和音を半小節ごとに',
                   '楽器 = tablet89・tablet86・声の最上声の音から作った旋律 (各 8 小節) を 06:42 の実音のピアノの 1 音のサンプラーで、2 小節ごとの低いペダル。鐘なし、合成の声なし、他の楽器なし。']}

if __name__ == '__main__':
    print('T89', ' '.join('%s:%g' % (name_of(m), d) for d, m in T89[:12]))
    compose.main(OUT, seed=225, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.55 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
