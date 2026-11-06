#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLXI · Traccia 18 in primo piano (トラック 18 を全面に押し出して、tablet160 とトラック 8 をベースに、高音の金属音を取り除いて)
  表 = トラック 18 (実音) を 4 回: tablet160 の調に合わせて、ヘ長調の段落ではそのまま (ニ短調)、ト長調の段落では全音上げて (ホ短調)。間は低い実音のピアノでトラック 18 の旋律をつなぐ
  ベース (裏) = tablet160 (CLX、全曲) とトラック 8 (全曲、2 回) — どちらも高域を落として (tablet160 は 1.6 kHz、トラック 8 は 2 kHz の低域通過、トラック 18 は 3.2 kHz)、鐘・サンプラーの金属的な高音を取り除く
  鐘なし、高い共鳴なし。低いペダルの音と、トラック 18 の旋律の低いピアノ (06:42 の実音のピアノの 1 音のサンプラー、1〜2 オクターヴ下) だけ
  使い方: python compose_tablet161.py <bank150.json> <wav のフォルダ (20261107_180000.wav, 20261107_080000.wav, 20261107_160000.wav = 高域を落としたもの)> [score_tablet161.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet161.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R42, R18, R08, R160 = '20261106_064228', '20261107_180000', '20261107_080000', '20261107_160000'
PSRC = R42
BPM = 60
TOTAL = 176
NAMES = {R18: 'トラック 18', R08: 'トラック 8', R160: 'tablet160 (CLX)'}
FILE = {R18: R18 + '.wav', R08: R08 + '.wav', R160: R160 + '.wav'}
DUR160 = 687.0
# (録音, 小節, 音量, 半音, オフセット秒, 長さ秒, 表)
PLAYS = [(R160, 0, 0.34, 0, 0.0, DUR160, False),                                                   # ベース: tablet160 全曲 (高域を落として)
         (R08, 40, 0.22, 0, 0.0, None, False), (R08, 110, 0.22, 0, 0.0, None, False),             # ベース: トラック 8 を 2 回
         (R18, 1, 0.7, 0, 0.0, None, True),                                                       # 表 1: ニ短調 (tablet160 I ヘ長調)
         (R18, 60, 0.7, 2, 0.0, None, True),                                                      # 表 2: ホ短調 (tablet160 II ト長調)
         (R18, 103, 0.72, 0, 0.0, None, True),                                                    # 表 3: ニ短調 (tablet160 III ヘ長調)
         (R18, 150, 0.66, 2, 0.0, 90.0, True)]                                                    # 表 4: ホ短調 (tablet160 IV ト長調)、終わりまで
def play_len(rid, dur): return RECS[rid]['dur'] if dur is None else dur
KEYSEC = [(0, 'F'), (60, 'G'), (102, 'F'), (150, 'G')]
def key_of(bar): return [k for b, k in KEYSEC if b <= bar][-1]
LOOP = {'F': ['Dm', 'Bb', 'F', 'C'], 'G': ['Em', 'C', 'G', 'D']}
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
extras = []; RH = []; RECQ = set()
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
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
        if cur is None: b = q // BPB; cur = LOOP[key_of(b)][b % 4]
        RH.append(cur); P.harm[q] = cur
    for k in range(TOTAL):
        P.tempo[k] = BPM
        P.dyn[k] = 0.5 if k < 60 else 0.6 if k < 102 else 0.7 if k < 150 else max(0.1, 0.6 - 0.02 * (k - 150))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    def put(v, b, mat, label=None):
        mat = clip(mat, (TOTAL - 3 - b) * BPB); t = b * BPB
        for d, m in mat: P.rest[v].difference_update(range(int(math.floor(t)), int(math.ceil(t + d - 1e-9)))); t += d
        P.place(v, b, mat, 0, label)
    P.section(0, 'I. トラック 18 — ニ短調 (♩=60)', 'トラック 18 の実音 (表、そのまま)。裏に tablet160 (CLX) の高域を落としたもの。鐘も高い共鳴もない')
    P.section(39, '間 — 低いピアノの旋律', 'トラック 18 の音から作った旋律を低い実音のピアノ (1〜2 オクターヴ下) で。トラック 8 (高域を落として) が裏に入る')
    put('T', 40, tr(T18['F'], -12), 'トラック 18 の旋律 (低いピアノ)'); put('B', 48, tr(T18['F'], -24), None)
    P.section(60, 'II. トラック 18 — 全音上げてホ短調', 'tablet160 のト長調の段落に合わせて、トラック 18 を全音上げて (表)。裏にトラック 8')
    P.section(98, '間 — 低いピアノ', '旋律の頭を低いピアノで')
    put('T', 98, tr(T18['G'][:6], -12), None); put('B', 100, tr(T18['G'][:6], -24), None)
    P.section(103, 'III. トラック 18 — ニ短調 (頂点)', 'トラック 18 (表、少し大きく)。裏に tablet160 の頂点とトラック 8 (2 回目)')
    P.section(141, '間 — 低いピアノの旋律 (2 倍に伸ばして)', '旋律の頭を 2 倍に伸ばして低いピアノで')
    put('B', 141, aug(tr(T18['F'][:6], -24)), '2 倍に伸ばして'); put('T', 145, tr(T18['F'][:6], -12), None)
    P.section(150, 'IV. トラック 18 — ホ短調、消える', 'トラック 18 を全音上げて (表)、裏が少しずつ消え、終わりまで')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.5 if bar > 0 else 0.02, fout=8.0, semis=sm, rid=rid + '.wav', tag='%s — %s%s' % (NAMES[rid], '実音 (表' if lead else '裏、高域を落として (', '、全音上げて)' if sm else ')'))
    first = True
    for b in range(2, TOTAL - 6, 2):
        r = 24 + chord(P.harm[b * BPB])['root']
        if r < 26: r += 12
        add('L', b * BPB, 7.6, r, 0.12 * P.dyn.get(b, 0.6) / 0.6, '低いペダルの音 (2 小節ごと)' if first else None); first = False

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R18, R160, R08], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CLXI · Traccia 18 in primo piano',
        'subtitle': 'トラック 18 を全面に押し出して (実音、4 回: ニ短調 → ホ短調 → ニ短調 → ホ短調、tablet160 の調に合わせて)、tablet160 (CLX) とトラック 8 をベースに (高域を落として)、高音の金属音を取り除いて: 鐘なし、高い共鳴なし。間は低い実音のピアノでトラック 18 の旋律。♩=60',
        'legend': ['PF', 'L'], 'vname': {'PF': '実音のピアノ (06:42 の 1 音、低く)', 'L': 'Pf ペダル'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['表 = トラック 18 (実音、3.2 kHz より上を落として)。裏 = tablet160 全曲 (1.6 kHz より上を落として 0.34) とトラック 8 (2 kHz より上を落として 0.22、2 回)。和音は表のトラック 18 の採譜から',
                   '間の低いピアノ = トラック 18 の最上声の音から作った旋律 (1〜2 オクターヴ下、06:42 の実音のピアノの 1 音のサンプラー)。鐘なし、高い共鳴なし、声なし。']}

if __name__ == '__main__':
    print('tune', ' '.join('%s:%g' % (name_of(m), d) for d, m in T18['F'][:12]))
    compose.main(OUT, seed=161, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
