#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CLXVIII · Sweet revenge nel 18:54 — senza arpeggio né batteria (tablet167 のアルペジオとドラムを消して作り換え)
  CLXVII と同じ (18:54 を 3 回リピート、tablet166 を裏に、循環コード、パッド・ベース・フック) で、エレピ風のアルペジオ (8 分音符) とドラムを消す
  実音: 11/06 18:54 の録音 (3 分 26 秒、とても静かなので rms −22 dB に揃えて) を **そのまま 3 回リピート** して表に、tablet166 (CLXVI) の実音を裏に (3 つの抜粋)
  雰囲気: Sweet Trio (BADA 528) と同じ、坂本龍一「Sweet Revenge」を思わせるダウンテンポの循環コード (ニ短調: Dm7 → Bbmaj7 → Gm7 → A7、旋律の引用はしない) — シンセ・パッド、ベース、柔らかいドラム、Sweet Trio の自作フック (アルペジオなし) (D5 C5 A4 / F4 G4 A4 / Bb4 A4 G4 / E4 F4 E4 C#4) をシンセ・リードと実音のピアノ (06:42 の 1 音のサンプラー) で
  形式: 序 (パッド、18:54 が始まる) → A (グルーヴ、フック 16 小節ごと) → B (2 回目のリピート、フック 8 小節ごと、弦) → C (3 回目、グルーヴが薄れ、パッドと 18:54 だけが残る)。♩=72
  使い方: python compose_tablet167.py <bank150.json> <wav のフォルダ (20261106_185402.wav = 音量を揃えたもの, 20261107_166000.wav = tablet166 の音声)> [score_tablet167.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet168.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
BANK = json.load(open(BANKP)); RECS = BANK['recordings']
R42, R1854, R166 = '20261106_064228', '20261106_185402', '20261107_166000'
PSRC = R42
BPM = 72
INTRO, A, B, C, TOTAL = 0, 8, 63, 125, 188
NAMES = {R1854: '11/06 18:54', R166: 'tablet166'}
FILE = {R1854: R1854 + '.wav', R166: R166 + '.wav'}
DUR = {R1854: 205.8, R166: 780.0}
LOOPBARS = 62                                                                                     # 205.8 秒 = 61.7 小節
PLAYS = [(R1854, 1, 0.62, 0, 0.0, None, True), (R1854, 1 + LOOPBARS, 0.62, 0, 0.0, None, True), (R1854, 1 + 2 * LOOPBARS, 0.6, 0, 0.0, None, True),   # 表: 18:54 を 3 回リピート
         (R166, 0, 0.3, 0, 0.0, 207.0, False), (R166, B, 0.3, 0, 365.0, 207.0, False), (R166, C, 0.28, 0, 600.0, 180.0, False)]                      # 裏: tablet166 の抜粋 (I、III の 06:42 + BWV 721、IV)
def play_len(rid, dur): return DUR[rid] if dur is None else dur
LOOP = ['Dm7', 'Bbmaj7', 'Gm7', 'A7']
HOOK = [(1.5, 74), (0.5, 72), (2, 69), (1.5, 65), (0.5, 67), (2, 69), (1.5, 70), (0.5, 69), (2, 67), (1.5, 64), (0.5, 65), (1, 64), (1, 61)]   # Sweet Trio のフック (自作、ニ短調)
RATE = lambda semis: 2 ** (semis / 12.0)
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))
def tones_of(h, lo, hi):
    c = chord(h); return sorted({min((x for x in range(lo, hi) if x % 12 == p), key=lambda x: abs(x - (lo + hi) / 2)) for p in (c['root'], c['third'], c['fifth'])})
def sec_of(b): return 'intro' if b < A else 'a' if b < B else 'b' if b < C else 'c'
DRUM_G = 0.22
def dr(beat, kind, g, pan=0.0, label=None): add('DR', beat, 0.25, 60, g * DRUM_G, label, kind=kind, pan=pan)

def build():
    P = Piece(TOTAL)
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL):
        P.tempo[k] = BPM
        P.dyn[k] = 0.4 if k < A else 0.6 if k < B else 0.7 if k < C else max(0.12, 0.55 - 0.012 * (k - C))
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    def put(v, b, mat, label=None, tr=0):
        mat = [(d, m + tr) for d, m in mat]; t = b * BPB
        for d, m in mat: P.rest[v].difference_update(range(int(math.floor(t)), min(TOTAL * BPB, int(math.ceil(t + d - 1e-9))))); t += d
        P.place(v, b, mat, 0, label)
    P.section(INTRO, '序 — パッドと 18:54 (ニ短調, ♩=72)', 'シンセ・パッドの上で 11/06 18:54 の実音 (表) が始まる、tablet166 の実音が裏に。循環コード Dm7 → Bbmaj7 → Gm7 → A7')
    P.section(A, 'A — ベースとフック', 'ベースだけが下で (アルペジオもドラムもなし)。Sweet Trio のフックを 16 小節ごとにシンセ・リードと実音のピアノで')
    for k in range(3): put('S', A + 4 + 16 * k, HOOK, 'フック (Sweet Trio の自作)' if k == 0 else None)
    P.section(B, 'B — 18:54 の 2 回目、フックが近づく', '18:54 の 2 回目のリピート (表)、tablet166 の 06:42 + BWV 721 の段が裏に。フックを 8 小節ごと、弦のパッドが重なる、アルトに 1 オクターヴ下のフック')
    for k in range(7): put('S', B + 2 + 8 * k, HOOK, None); put('A', B + 6 + 8 * k, HOOK, None, -12)
    P.section(C, 'C — 18:54 の 3 回目、消えていく', '18:54 の 3 回目のリピート (表)、tablet166 の終わりが裏に。ベースが抜け、フックの頭だけが実音のピアノで、パッドと 18:54 だけが残る')
    for k in range(5): put('S', C + 4 + 10 * k, HOOK[:3], None)
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        L = play_len(rid, dur)
        add('REC', bar * BPB, L / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, FILE[rid]), off=off, fin=0.5 if bar > 0 else 0.02, fout=8.0, semis=sm, rid=rid + '.wav', tag='%s — 実音 (%s)' % (NAMES[rid], '表、リピート' if lead else '裏、抜粋'))
    # パッド (和音の 3 音、小節ごと)
    first = True
    for b in range(0, TOTAL - 3):
        if sec_of(b) == 'c' and b > C + 50: break
        g = 0.09 * P.dyn.get(b, 0.6) / 0.6
        for i, m in enumerate(tones_of(P.harm[b * BPB], 55, 69)): add('PD', b * BPB + 0.02 * i, BPB + 0.5, m, g * (1.0 if i == 0 else 0.8), 'シンセ・パッド' if (first and i == 0) else None)
        first = False
    # アルペジオ (エレピ風のプラック、8 分音符) と ベース と ドラム
    first_ar = first_sb = first_dr = True
    for b in range(A, TOTAL - 4):
        s = sec_of(b)
        if s == 'c' and b > C + 36: continue
        c = chord(P.harm[b * BPB]); r = 50 + c['root']; third = r + c['pcs'][1] - c['root'] + 12
        pat = [r, r + 7, third, r + 12, r + 7, third, r + 12, r + 7]
        if s == 'c' and b > C + 24: continue
        rb = 38 + c['root']
        if rb > 45: rb -= 12
        add('SB', b * BPB, 1.9, rb, 0.4, 'ベース' if first_sb else None); add('SB', b * BPB + 2, 1.4, rb, 0.34); add('SB', b * BPB + 3.5, 0.45, rb + 7, 0.24); first_sb = False
    # フックをシンセ・リードで (S の音符に重ねる) と、弦のパッド (B)
    def line(v, bar, mat, tr, g, label=None):
        t = bar * BPB; first_ = True
        for d, m in mat: add(v, t, d, m + tr, g, label if first_ else None); first_ = False; t += d
    for k in range(3): line('LD', A + 4 + 16 * k, HOOK, 0, 0.16, 'シンセ・リード (フック)' if k == 0 else None)
    for k in range(7): line('LD', B + 2 + 8 * k, HOOK, 0, 0.18)
    OG = 0.3
    for b in range(B + 4, C - 2):
        h = P.harm[b * BPB]
        for v, lo, hi in (('V2', 62, 76), ('VA', 55, 67), ('VC', 43, 55)):
            for i, m in enumerate(tones_of(h, lo, hi)[:3]): add(v, b * BPB + 0.03 * i, BPB + 0.3, m, 0.1 * OG * (1.0 if i == 0 else 0.8), '弦のパッド' if (b == B + 4 and v == 'V2' and i == 0) else None)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [R1854, R166], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4], 'band_gain': 0.9, 'orchestra': True,
        'title': 'Requiem BADA — CLXVIII · Sweet revenge nel 18:54 — senza arpeggio né batteria',
        'subtitle': 'tablet167 のアルペジオとドラムを消して作り換え: tablet166 の Sweet Revenge に、11/06 18:54 の実音をそのまま 3 回リピートして表に、tablet166 の実音を裏に: ダウンテンポの循環コード Dm7 → Bbmaj7 → Gm7 → A7 (旋律の引用はしない)、パッド・ベース・柔らかいドラム・Sweet Trio の自作フック (アルペジオなし)。序 → A → B (2 回目) → C (3 回目、消える)。ニ短調、♩=72',
        'legend': ['PD', 'LD', 'SB', 'PF', 'V2', 'VA', 'VC'], 'vname': {'PD': 'パッド', 'LD': 'リード', 'SB': 'ベース', 'PF': '実音のピアノ (06:42 の 1 音)', 'V2': 'Vn II', 'VA': 'Va', 'VC': 'Vc'}, 'src_name': {R42: '06:42 の音'},
        'footer': ['18:54 の録音は rms −22 dB に揃えて (tanh で軽く抑える) そのまま 3 回 (0.62)。tablet166 は 3 つの抜粋 (0〜207 秒、365〜572 秒、600〜780 秒) を 0.3 で裏に。和音は循環コードを固定 (催眠的な反復)',
                   '「Sweet Revenge」(坂本龍一) からは循環コードの型・音色・グルーヴだけを参照、旋律の引用はしない。フックは BADA 528 (Sweet Trio) の自作。4 声は 06:42 の実音のピアノの 1 音のサンプラー。鐘なし、声なし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=168, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    for n in d['notes']:
        n['src'] = PSRC
        d['extras'].append(dict(v='PF', beat=n['beat'], dbeats=n.get('dbeats', n['d']), t=n['t'], d=n['d'], m=n['m'], gain=round(0.42 * n.get('dyn', 1.0) * (1.3 if n['label'] else 1.0), 4), label=None, rid=PSRC, rel=0.5, layer='theme'))
    d['extras'].sort(key=lambda e: e['t'])
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    from collections import Counter
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'notes', len(d['notes']), 'extras', Counter(e.get('layer', e['v']) for e in d['extras']))
