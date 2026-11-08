#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLXXXVIII · Le due mattine sul 185 (tablet185・tablet117・2026/11/06 18:54・06:42・06:39 を重ね合わせて、元の楽器を演奏させて — アルペジオや元の曲に無い楽器は付け加えない)
  テープ: tablet185 (CLXXXV — 18:54・トラック 8・18 とそのピアノ、11 分 36 秒) を全曲 (0.45) 土台に、tablet117 (CXVII) のヘ長調の段 (152〜320 秒) を繰り返して裏に (0.25)、11/06 18:54 の実音 (rms −22 dB に揃えたもの) を途切れなく 3 回半 (0.4)、06:42 (ヘ長調、そのまま) と 06:39 (全音下げてヘ長調に) を表に
  元の楽器 = 録音と tablet185 の中にあるものだけ: 06:42・06:39 の最上声の音から作った旋律 (各 8 小節) と tablet185 のトラック 8・18 の旋律 (各 8 小節、ヘ長調 / ニ短調) を実音のピアノ (06:42 の 1 音のサンプラー) で、低いペダルの音 (2 小節ごと)。アルペジオ・パッド・ベース・ドラム・フック・高い共鳴は付け加えない
  和音は表の録音 (06:42・06:39) の採譜から、鳴っていないところは tablet185 の楽譜の和音 (時間が一致する)
  使い方: python compose_tablet188.py <bank150.json> <wav のフォルダ (20261107_185000.wav, 20261003_117000.wav, 20261106_185402.wav, 20261106_063938_clean.wav, 20261106_064228_clean.wav)> <score_tablet185.json (和音)> [score_tablet188.json]
"""
import sys, os, json, math
BANKP, WDIR, HARMP = sys.argv[1], os.path.abspath(sys.argv[2]), sys.argv[3]; OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet188.json'
HARM151 = json.load(open(HARMP))['harm']
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R42, R39, R08, R18, R117, R185, R1854 = '20261106_064228', '20261106_063938', '20261107_080000', '20261107_180000', '20261003_117000', '20261107_185000', '20261106_185402'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 60, 108, 150, 176
NAMES = {R42: '11/06 06:42', R39: '11/06 06:39', R117: 'tablet117', R185: 'tablet185', R1854: '11/06 18:54'}
FILE = {R42: R42 + '_clean.wav', R39: R39 + '_clean.wav', R117: R117 + '.wav', R185: R185 + '.wav', R1854: R1854 + '.wav'}
DUR = {R42: 226.7, R39: 160.3, R117: 778.6, R185: 695.0, R1854: 205.8}
PLAYS = [(R185, 0, 0.45, 0, 0.0, 695.0, False)] + [(R117, 38 * k, 0.25, 0, 152.0, 168.0, False) for k in range(5)] + [(R1854, k * 50, 0.4, 0, 0.0, 205.8 if k < 3 else 96.0, False) for k in range(4)] + [   # tablet185 を全曲、tablet117 のヘ長調の段、18:54 を途切れなく
         (R42, 2, 0.55, 0, 0.0, None, True),                                                      # I: 06:42 全部
         (R39, S2 + 1, 0.55, -2, 0.0, None, True),                                                # II: 06:39 全音下げて
         (R42, S3 + 1, 0.5, 0, 60.0, 166.0, True),                                                # III: 06:42 の後半
         (R39, S4 + 1, 0.5, -2, 90.0, 70.0, True)]                                                # IV: 06:39 の終わり
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
T42 = tune_from(R42, 0, ends=((72, 77), (69, 65), (72, 77), (65, 65))); T39 = tune_from(R39, -2, ends=((72, 77), (69, 65), (72, 77), (65, 65)))
T8 = tune_from(R08, 5); T18 = tune_from(R18, 0)                                                   # tablet185 のトラック 8・18 の旋律 (ヘ長調 / ニ短調)
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
        if cur is None: cur = HARM151[q] if q < len(HARM151) else LOOP[(q // BPB) % 4]
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL):
        P.tempo[k] = BPM
        P.dyn[k] = 0.5 if k < S2 else 0.6 if k < S3 else 0.68 if k < S4 else max(0.1, 0.55 - 0.018 * (k - S4))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    E = []
    def put(v, b, mat, label=None):
        mat = clip(mat, (TOTAL - 3 - b) * BPB); t = b * BPB
        for d, m in mat: P.rest[v].difference_update(range(int(math.floor(t)), int(math.ceil(t + d - 1e-9)))); t += d
        P.place(v, b, mat, 0, label); E.append((b * BPB, mat))
    P.section(S1, 'I. 06:42 (ヘ長調, ♩=60)', 'tablet185 と 18:54、tablet117 のヘ長調の段の上に 06:42。元の楽器: 06:42 の旋律を実音のピアノで (アルト → テノール)、tablet185 のトラック 18 の旋律がバスで、低いペダル')
    put('A', 8, T42, '06:42 の旋律 (実音のピアノ)'); put('T', 24, tr(T42, -12), None); put('B', 40, tr(T18, -24), 'トラック 18 の旋律 (tablet185)')
    P.section(S2, 'II. 06:39 (全音下げて)', '06:39 (ヘ長調に)。06:39 の旋律 (ソプラノ → テノール)、tablet185 のトラック 8 の旋律がアルトで')
    put('S', S2 + 6, T39, '06:39 の旋律 (実音のピアノ)'); put('T', S2 + 20, tr(T39, -12), None); put('A', S2 + 30, T8, 'トラック 8 の旋律 (tablet185)'); put('B', S2 + 38, aug(tr(T42[:6], -24)), None)
    P.section(S3, 'III. 06:42 の後半 — 4 つの旋律', '06:42 の後半。06:42 (ソプラノ) と 06:39 (テノール) の旋律を同時に、次にトラック 18 (アルト) とトラック 8 (バス) を同時に')
    put('S', S3 + 4, T42, '4 つの旋律'); put('T', S3 + 6, tr(T39, -12), None); put('A', S3 + 20, T18, None); put('B', S3 + 22, tr(T8, -24), None); put('S', S3 + 32, T39, None)
    P.section(S4, 'IV. 06:39 の終わり — 消える', '06:39 の終わり。旋律の頭を 2 倍に伸ばして (06:42・トラック 18)、tablet117 とペダルだけが残って消える')
    put('T', S4 + 4, aug(tr(T42[:6], -12)), '頭を 2 倍に'); put('B', S4 + 12, aug(tr(T18[:6], -24)), None); put('A', S4 + 18, aug(T42[:6]), None)
    harm_fit(P, 1, TOTAL - 3, E, CANDS)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if L > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — 実音%s' % (NAMES[rid], '、途切れなく 3 回半' if rid == R1854 else ('、全曲そのまま (土台)' if rid == R185 else ('、ヘ長調の段を繰り返して裏に' if rid == R117 else ('、全音下げて' if sm else '、そのまま')))))
    first = True
    for b in range(2, TOTAL - 6, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.6, r, 0.12 * P.dyn.get(b, 0.6) / 0.6, '低いペダルの音 (2 小節ごと)' if first else None); first = False


META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R42, R39, R1854, R185, R117], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CLXXXVIII · Le due mattine sul 185',
        'subtitle': 'tablet185 を土台に、tablet117 (ヘ長調の段)・11/06 18:54・06:42・06:39 を重ね合わせて、元の楽器 (06:42・06:39 の旋律と tablet185 のトラック 8・18 の旋律を実音のピアノで、低いペダル) を演奏させて。アルペジオや元の曲に無い楽器は付け加えない。ヘ長調 / ニ短調、♩=60',
        'legend': ['PF', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音)', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['tablet185 (CLXXXV) は全曲そのまま 0.45 (土台)、tablet117 はヘ長調の段 (152〜320 秒) を 5 回 0.25、18:54 は rms −22 dB に揃えて途切れなく 3 回半 0.4。06:42 (ヘ長調) はそのまま、06:39 は全音下げてヘ長調に (0.55 / 0.5)。和音は表の録音の採譜を優先、表がないところは tablet185 の楽譜の和音',
                   '楽器 = 06:42・06:39・トラック 8・トラック 18 の最上声の音から作った旋律 (各 8 小節) を 06:42 の実音のピアノの 1 音のサンプラーで、2 小節ごとの低いペダル。鐘なし、声なし、他の楽器なし。']}

if __name__ == '__main__':
    print('T42', ' '.join('%s:%g' % (name_of(m), d) for d, m in T42[:6]), '| T39', ' '.join('%s:%g' % (name_of(m), d) for d, m in T39[:6]))
    compose.main(OUT, seed=188, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
