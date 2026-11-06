#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLXXII · Il 18:54 sulla fuga (2026/11/06 18:54 と tablet152 を合成)
  テープ: 11/06 18:54 の実音 (3 分 26 秒、rms −22 dB に揃えたもの) を **そのまま 3 回リピート** して表に (0.55)、tablet152 (CLII — トラック 8・18 の旋律の二重フーガ、06:39 の空気) を全曲、裏に (0.38; 18:54 のない終わりでは表に)
  和音は tablet152 の楽譜に記録された拍ごとの和音の流れ (06:39 の採譜) をそのまま (tablet152 は全曲鳴っていて時間が一致する)
  楽器は CLXXI と同じ (Sweet Revenge 風、アルペジオなし): シンセ・パッド、ベース、柔らかいドラム、フック (Sweet Trio の自作をニ・ドリアに) をシンセ・リードと実音のピアノ (06:42 の 1 音のサンプラー) で、弦のパッド (III)
  使い方: python compose_tablet172.py <bank150.json> <wav のフォルダ (20261106_185402.wav, 20261107_152000.wav)> <score_tablet152.json (和音)> [score_tablet172.json]
"""
import sys, os, json, math
BANKP, WDIR, HARMP = sys.argv[1], os.path.abspath(sys.argv[2]), sys.argv[3]; OUT = sys.argv[4] if len(sys.argv) > 4 else 'score_tablet172.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
R42, R1854, R152 = '20261106_064228', '20261106_185402', '20261107_152000'
PSRC = R42
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 53, 105, 157, 170
NAMES = {R1854: '11/06 18:54', R152: 'tablet152'}
PLAYS = [(R152, 0, 0.38, 0, 0.0, 687.0, False),                                                   # tablet152 全曲 (裏)
         (R1854, 1, 0.55, 0, 0.0, 205.8, True), (R1854, S2 + 1, 0.55, 0, 0.0, 205.8, True), (R1854, S3 + 1, 0.52, 0, 0.0, 205.8, True)]   # 18:54 を 3 回
HARM152 = json.load(open(HARMP))['harm']                                                          # tablet152 の和音 (拍ごと、680 拍)
HOOK = [(1.5, 74), (0.5, 72), (2, 69), (1.5, 65), (0.5, 67), (2, 69), (1.5, 71), (0.5, 69), (2, 67), (1.5, 64), (0.5, 65), (1, 64), (1, 62)]   # Sweet Trio のフックをニ・ドリアに
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
def tones_of(h, lo, hi):
    c = chord(h); return sorted({min((x for x in range(lo, hi) if x % 12 == p), key=lambda x: abs(x - (lo + hi) / 2)) for p in (c['root'], c['third'], c['fifth'])})
def sec_of(b): return 1 if b < S2 else 2 if b < S3 else 3 if b < S4 else 4
DRUM_G = 0.22
def dr(beat, kind, g, pan=0.0, label=None): add('DR', beat, 0.25, 60, g * DRUM_G, label, kind=kind, pan=pan)

def build():
    P = Piece(TOTAL)
    for q in range(TOTAL * BPB): P.harm[q] = HARM152[q] if q < len(HARM152) else HARM152[-1]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.55 if k < S2 else 0.65 if k < S3 else 0.7 if k < S4 else max(0.12, 0.6 - 0.04 * (k - S4))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    def put(v, b, mat, label=None, tr=0):
        mat = [(d, m + tr) for d, m in mat]; t = b * BPB
        for d, m in mat: P.rest[v].difference_update(range(int(math.floor(t)), min(TOTAL * BPB, int(math.ceil(t + d - 1e-9))))); t += d
        P.place(v, b, mat, 0, label)
    P.section(S1, 'I. 18:54 の 1 回目 — パッドとベース (ニ・ドリア, ♩=60)', '18:54 の実音 (表) と tablet152 のフーガ (裏)。パッド、ベース、柔らかいドラムが始まり (アルペジオなし)、フックを 16 小節ごとに')
    for k in range(3): put('S', S1 + 6 + 16 * k, HOOK, 'フック (Sweet Trio の自作、ニ・ドリアに)' if k == 0 else None)
    P.section(S2, 'II. 18:54 の 2 回目 — フックが 8 小節ごと', '18:54 の 2 回目 (表)、tablet152 の中ほど (裏)。フックを 8 小節ごと、アルトに 1 オクターヴ下も')
    for k in range(6): put('S', S2 + 2 + 8 * k, HOOK, None); put('A', S2 + 6 + 8 * k, HOOK, None, -12)
    P.section(S3, 'III. 18:54 の 3 回目 — 弦のパッド', '18:54 の 3 回目 (表)、tablet152 の頂点 (裏)。弦のパッドが重なり、フックを 8 小節ごと')
    for k in range(6): put('S', S3 + 2 + 8 * k, HOOK, None)
    P.section(S4, 'IV. tablet152 の終わり — 消えていく', 'tablet152 の終わりだけが残る。ドラム → ベースの順に抜け、フックの頭だけが実音のピアノで、パッドが消える')
    put('S', S4 + 2, HOOK[:3], None); put('S', S4 + 7, HOOK[:3], None)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 6.0, fout=8.0, semis=sm, rid=rid + '.wav', tag='%s — %s (%d 秒から)' % (NAMES[rid], '表' if lead else '裏、小さく', int(off)))
    first = True
    for b in range(0, TOTAL - 3):
        if b > S4 + 10: break
        g = 0.09 * P.dyn.get(b, 0.6) / 0.6
        for i, m in enumerate(tones_of(P.harm[b * BPB], 55, 69)): add('PD', b * BPB + 0.02 * i, BPB + 0.5, m, g * (1.0 if i == 0 else 0.8), 'シンセ・パッド' if (first and i == 0) else None)
        first = False
    first_ar = first_sb = first_dr = True
    for b in range(2, TOTAL - 4):
        s = sec_of(b)
        if s == 4 and b > S4 + 8: continue
        c = chord(P.harm[b * BPB]); r = 50 + c['root']; third = r + c['pcs'][1] - c['root'] + 12
        pat = [r, r + 7, third, r + 12, r + 7, third, r + 12, r + 7]
        if s == 4 and b > S4 + 6: continue
        for k in (0, 2):
            c2 = chord(P.harm[b * BPB + k]); rb = 38 + c2['root']
            if rb > 45: rb -= 12
            add('SB', b * BPB + k, 1.9 if k == 0 else 1.4, rb, 0.4 if k == 0 else 0.34, 'ベース' if first_sb else None); first_sb = False
        add('SB', b * BPB + 3.5, 0.45, rb + 7, 0.24)
        if s == 4 and b > S4 + 3: continue
        g = 0.55 if s in (2, 3) else 0.45
        dr(b * BPB, 'kick', g, 0, 'ドラム (柔らかく)' if first_dr else None); dr(b * BPB + 2, 'kick', g * 0.8)
        dr(b * BPB + 1, 'snare', g * 0.55, 0.05); dr(b * BPB + 3, 'snare', g * 0.6, 0.05)
        for k in range(8): dr(b * BPB + k * 0.5, 'hatc', 0.3 * (1.0 if k % 2 == 0 else 0.6), 0.25)
        first_dr = False
    def line(v, bar, mat, tr, g, label=None):
        t = bar * BPB; first_ = True
        for d, m in mat: add(v, t, d, m + tr, g, label if first_ else None); first_ = False; t += d
    for k in range(3): line('LD', S1 + 6 + 16 * k, HOOK, 0, 0.16, 'シンセ・リード (フック)' if k == 0 else None)
    for k in range(6): line('LD', S2 + 2 + 8 * k, HOOK, 0, 0.18); line('LD', S3 + 2 + 8 * k, HOOK, 0, 0.18)
    OG = 0.3
    for b in range(S3 + 2, S4 - 2):
        h = P.harm[b * BPB]
        for v, lo, hi in (('V2', 62, 76), ('VA', 55, 67), ('VC', 43, 55)):
            for i, m in enumerate(tones_of(h, lo, hi)[:3]): add(v, b * BPB + 0.03 * i, BPB + 0.3, m, 0.1 * OG * (1.0 if i == 0 else 0.8), '弦のパッド' if (b == S3 + 2 and v == 'V2' and i == 0) else None)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R1854, R152], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4], 'band_gain': 0.9, 'orchestra': True,
        'title': 'Requiem BADA — CLXXII · Il 18:54 sulla fuga',
        'subtitle': '11/06 18:54 の実音をそのまま 3 回リピートして表に、tablet152 (トラック 8・18 の二重フーガ、06:39 の空気) を全曲裏に、Sweet Revenge 風のパッド・ベース・柔らかいドラム・フック (Sweet Trio の自作)・弦のパッド (アルペジオなし)。和音は tablet152 の楽譜の和音の流れ。ニ短調 / ニ・ドリア、♩=60',
        'legend': ['PD', 'LD', 'SB', 'DR', 'PF', 'V2', 'VA', 'VC'], 'vname': {'PD': 'パッド', 'LD': 'リード', 'SB': 'ベース', 'DR': 'ドラム', 'PF': '実音のピアノ (06:42 の 1 音)', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['18:54 の録音は rms −22 dB に揃えて (tanh で軽く抑える) そのまま 3 回 (0.55)。tablet152 は全曲 0.38 で裏に、終わりだけ残る。和音は tablet152 (CLII) の楽譜に記録された拍ごとの和音 — 時間がそのまま一致する',
                   '楽器は CLXXI と同じ (「Sweet Revenge」からは型・音色・グルーヴだけ、旋律の引用はしない、アルペジオなし)。フックは BADA 528 (Sweet Trio) の自作をニ・ドリアに。4 声は 06:42 の実音のピアノの 1 音のサンプラー。鐘なし、声なし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=172, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
