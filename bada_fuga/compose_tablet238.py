#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCXXXVIII · L'aureola sensuale calma, l'89 addolcito e la traccia 16 (tablet228 を、安心するドエロの光輪様の声と、響きを抑えた tablet89 で作り換え)
  声: 安心するドエロの光輪様の声 (CCXXXII〜 と同じ — 残響 1.5 秒・0.4、上声 0.2 / 0.15、息 −17 dB、2〜4 kHz +2 dB、rms −25 dB) を 2 回 (0.45)
  tablet89: 響きを抑えて柔らかく — 5 kHz 以上を落とし、1.5〜4 kHz の鋭さを少し抑え、0.4 秒の包絡で大きい所だけを抑える圧縮、rms −18.3 → −23 dB。全曲 (0.4) と後半 (90 秒から、0.35)
  トラック 16 (2 半音上げてニ短調) は全曲 (0.35) と後半 (150 秒から、0.3)。3 つの音だけ、楽器は何も加えない
  使い方: python compose_tablet238.py <bank201.json> <wav のフォルダ (20261108_145525.wav = 安心する光輪の声, 20261107_089000.wav = 響きを抑えた tablet89, 20261107_160000.wav = トラック 16)> [score_tablet238.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet238.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RV, R89, R16 = '20261108_145525', '20261107_089000', '20261107_160000'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 50, 100, 140, 176
NAMES = {RV: '11/08 14:55 の声 (安心するドエロの光輪様の声)', R89: 'tablet89 (響きを抑えて)', R16: 'トラック 16'}
RATE = lambda semis: 2 ** (semis / 12.0)
PLAYS = [(RV, 2, 0.45, 0, 0.0, 198.5, True), (R89, 0, 0.4, 0, 0.0, 391.0, True),                    # I〜II: 光輪の声 + tablet89 全曲 (98 小節)
         (R16, S2 + 2, 0.35, 2, 0.0, 303.5, True),                                                   # II〜III: トラック 16 (2 半音上げて、全曲)
         (RV, S3 + 2, 0.45, 0, 0.0, 198.5, True), (R89, S3, 0.35, 0, 90.0, 300.0, True),              # III〜IV: 声 (2 回目) + tablet89 の後半 (90 秒から、終わりまで)
         (R16, S4 + 2, 0.3, 2, 150.0, 150.0, True)]                                                # IV: トラック 16 の後半 (150 秒から)
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    LOOP = ['Dm', 'Bb', 'F', 'C']
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. 光輪の声と tablet89 の始まり (♩=60)', 'ドエロの光輪様の声に tablet89 (レクイエム、ニ短調、そのまま)')
    P.section(S2, 'II. tablet89 のフーガとトラック 16', 'tablet89 の続き (フーガ) にトラック 16 (2 半音上げて、全曲)')
    P.section(S3, 'III. 光輪の声 (2 回目) と tablet89 の後半', '光輪様の声をもう一度、tablet89 の後半 (90 秒から)、トラック 16 の続き')
    P.section(S4, 'IV. tablet89 の終わりとトラック 16 の後半、消える', 'tablet89 の終わりと声の終わり、トラック 16 の後半 (150 秒から)、一緒に消える')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if dur > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — %s' % (NAMES[rid], '安心するドエロの光輪の声 (響きを抑えて)' if rid == RV else ('実音' + ('、2 半音上げて' if sm else '') + ('、後半 (%d 秒から)' % off if off else ('、全曲' if sm else '、全曲そのまま')))))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [RV, R89, R16], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCXXXVIII · L\'aureola sensuale calma, l\'89 addolcito e la traccia 16',
        'subtitle': 'tablet228 を作り換え: 安心するドエロの光輪様の声 (響きと音量を抑えて聞き取りやすく) に、響きを抑えて柔らかくした tablet89 (レクイエムとフーガ、ニ短調) とトラック 16 (ハ短調 / ト短調、2 半音上げてニ短調に) を重ね合わせて。楽器なし。♩=60',
        'legend': [], 'vname': {},
        'footer': ['声 = 安心するドエロの光輪様の声 (残響 1.5 秒・0.4、5 度上 0.2 + 1 オクターヴ上 0.15、息 −17 dB、2〜4 kHz +2 dB、rms −25 dB) を 2 回 (0.45)。tablet89 は 5 kHz 以上を落とし、1.5〜4 kHz を少し抑え、大きい所だけを抑える圧縮で rms −23 dB にして、全曲 0.4、後半 (90 秒から) 0.35。トラック 16 (2 半音上げて) は全曲 0.35、後半 (150 秒から) 0.3。', '楽器は何も加えない (サンプラーのピアノも、ペダルも、鐘もなし)。移調はトラック 16 の 2 半音だけ。']}

if __name__ == '__main__':
    compose.main(OUT, seed=238, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
