#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLXXXI · Il 18:54 sul 161 con il pianoforte basso (tablet180 に、元の楽器を演奏させて作り換え — アルペジオや元の曲に無い楽器は付け加えない)
  テープは CLXXX のまま: tablet161 (CLXI) を全曲 (0.5)、11/06 18:54 の実音を途切れなく 3 回半 (0.5)
  元の楽器 = tablet161 (CLXI) に元からある 2 つだけ: トラック 18 の最上声の音から作った旋律を低い実音のピアノ (06:42 の 1 音のサンプラー、1〜2 オクターヴ下) で、低いペダルの音 (2 小節ごと)。アルペジオ・パッド・ベース・ドラム・フックは付け加えない
  和音は tablet161 の楽譜に記録された拍ごとの和音の流れ (トラック 18 の採譜) をそのまま (時間が一致する)
  使い方: python compose_tablet181.py <bank150.json> <wav のフォルダ (20261107_161000.wav, 20261106_185402.wav)> <score_tablet161.json (和音)> [score_tablet181.json]
"""
import sys, os, json, math
BANKP, WDIR, HARMP = sys.argv[1], os.path.abspath(sys.argv[2]), sys.argv[3]; OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet181.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R42, R18, R161, R1854 = '20261106_064228', '20261107_180000', '20261107_161000', '20261106_185402'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 50, 100, 150, 178
NAMES = {R161: 'tablet161', R1854: '11/06 18:54'}
PLAYS = [(R161, 0, 0.5, 0, 0.0, 711.0, True)] + [(R1854, k * 50, 0.5, 0, 0.0, 205.8 if k < 3 else 110.0, True) for k in range(4)]
HARM = json.load(open(HARMP))['harm']
KEYSEC = [(0, 'F'), (60, 'G'), (102, 'F'), (150, 'G')]
def key_of(bar): return [k for b, k in KEYSEC if b <= bar][-1]
SCALE = {'F': [5, 7, 9, 10, 0, 2, 4], 'G': [7, 9, 11, 0, 2, 4, 6]}
ENDS = {'F': ((69, 74), (65, 62), (69, 74), (62, 62)), 'G': ((71, 76), (67, 64), (71, 76), (64, 64))}
def tune_from(rid, key, lo=62, hi=76, rhythm=(1, 1, 1, 1, 2, 2), n=4):
    sm = {'F': 0, 'G': 2}[key]; sc = SCALE[key]; tops = []
    for sg in RECS[rid]['segs']:
        m = sg['m'][-1] + sm
        if sg['d'] < 0.3: continue
        if tops and tops[-1] % 12 == m % 12: continue
        m = min((x for x in range(m - 2, m + 3) if x % 12 in sc), key=lambda x: abs(x - m))
        while m < lo: m += 12
        while m > hi: m -= 12
        if tops and abs(m - tops[-1]) > 7: m = min((m + 12 * k for k in (-1, 0, 1)), key=lambda x: abs(x - tops[-1]))
        while m < lo: m += 12
        while m > hi: m -= 12
        tops.append(m)
    rh = list(rhythm) * n; out = [(d, tops[i % len(tops)]) for i, d in enumerate(rh)]
    for ph in range(n):
        i = ph * len(rhythm) + len(rhythm) - 1; out[i] = (2, min(ENDS[key][ph % 4], key=lambda x: abs(x - out[i][1])))
    return out
T18 = {k: tune_from(R18, k) for k in ('F', 'G')}
def tr(mat, o): return [(d, m + o) for d, m in mat]
def aug(mat, k=2): return [(d * k, m) for d, m in mat]
RATE = lambda semis: 2 ** (semis / 12.0)
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
def clip(mat, max_beats):
    out = []; t = 0.0
    for d, m in mat:
        if t >= max_beats: break
        out.append((min(d, max_beats - t), m)); t += d
    return out

def build():
    P = Piece(TOTAL)
    for q in range(TOTAL * BPB): P.harm[q] = HARM[q] if q < len(HARM) else HARM[-1]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5 if k < S2 else 0.6 if k < S3 else 0.7 if k < S4 else max(0.1, 0.6 - 0.02 * (k - S4))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    def put(v, b, mat, label=None):
        mat = clip(mat, (TOTAL - 3 - b) * BPB); t = b * BPB
        for d, m in mat: P.rest[v].difference_update(range(int(math.floor(t)), int(math.ceil(t + d - 1e-9)))); t += d
        P.place(v, b, mat, 0, label)
    P.section(S1, 'I. 18:54 の 1 回目 — 低いピアノ (ニ短調, ♩=60)', 'tablet161 のトラック 18 と 18:54 の実音。元の楽器: トラック 18 の旋律を低い実音のピアノで (テノール → バス)、低いペダルが 2 小節ごと')
    put('T', 8, tr(T18['F'], -12), 'トラック 18 の旋律 (低いピアノ)'); put('B', 24, tr(T18['F'], -24), None); put('T', 40, tr(T18['F'], -12), None)
    P.section(S2, 'II. 18:54 の 2 回目 — ホ短調', 'tablet161 のトラック 18 (ホ短調) の段。旋律をホ短調で、頭を 2 倍に伸ばしてバスに')
    put('T', S2 + 6, tr(T18['G'], -12), None); put('B', S2 + 20, aug(tr(T18['G'][:6], -24)), '頭を 2 倍に (バス)'); put('T', S2 + 34, tr(T18['G'], -12), None)
    P.section(S3, 'III. 18:54 の 3 回目 — 頂点', 'tablet161 のトラック 18 (ニ短調、頂点)。旋律を 2 声で (テノールとバス、2 小節遅れ)')
    put('T', S3 + 4, tr(T18['F'], -12), '2 声で'); put('B', S3 + 6, tr(T18['F'], -24), None); put('T', S3 + 24, tr(T18['F'], -12), None); put('B', S3 + 26, tr(T18['F'], -24), None); put('B', S3 + 42, aug(tr(T18['F'][:6], -24)), None)
    P.section(S4, 'IV. 18:54 の 4 回目 (半分) — 消える', 'tablet161 の終わり (ホ短調)。旋律の頭を 2 倍に伸ばして、ペダルだけが残って一緒に消える')
    put('T', S4 + 4, aug(tr(T18['G'][:6], -12)), None); put('B', S4 + 12, aug(tr(T18['G'][:6], -24)), None)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if dur > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — 実音%s' % (NAMES[rid], '、途切れなく 3 回半' if rid == R1854 else '、全曲そのまま'))
    first = True
    for b in range(2, TOTAL - 6, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.6, r, 0.12 * P.dyn.get(b, 0.6) / 0.6, '低いペダルの音 (2 小節ごと)' if first else None); first = False

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R1854, R161], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CLXXXI · Il 18:54 sul 161 con il pianoforte basso',
        'subtitle': 'tablet180 (18:54 + tablet161) に元の楽器を演奏させて: tablet161 に元からある低い実音のピアノ (トラック 18 の旋律、1〜2 オクターヴ下) と低いペダルだけ。アルペジオや元の曲に無い楽器は付け加えない。和音は tablet161 の楽譜の流れ。ニ短調 / ホ短調、♩=60',
        'legend': ['PF', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音、低く)', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['テープは CLXXX のまま (tablet161 を全曲 0.5、18:54 を途切れなく 3 回半 0.5)。和音は tablet161 (CLXI) の楽譜に記録された拍ごとの和音 — 時間がそのまま一致する',
                   '楽器 = トラック 18 の最上声の音から作った旋律 (各段の調に寄せて 8 小節) を低い実音のピアノ (06:42 の 1 音のサンプラー) で、2 小節ごとの低いペダル。鐘なし、声なし、他の楽器なし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=181, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
