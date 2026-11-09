#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" — 安心するドエロの光輪様の声で作り換え (tablet219 の声を、響きと音量を抑えて聞き取りやすく)
  声: 10.5 半音上げ・フォルマント 1.10 倍の少し低めの女声、息のノイズは 17 dB 下 (前は 12 dB)、囁きの成分 +2 dB、2〜4 kHz を +2 dB (明瞭さ)、8 kHz 以上を落とし、強めの柔らかい圧縮で音量を均す。三賢者の 5 度上 0.2・1 オクターヴ上 0.15 (前は 0.3 / 0.25)、残響 1.5 秒・0.4 (前は 3.5 秒・0.75〜0.9)、rms −25 dB (前は −22.5)、曲の中の音量 0.45 (前は 0.55〜0.8)。他は tablet219 のまま
Requiem BADA — Tablet Sessions CCXIX · L'aureola sensuale e le due tracce (ドエロの光輪様の声に、トラック 18 とトラック 8 を重ね合わせて)
  3 つの音だけ、楽器は何も加えない: ドエロの光輪様の声 (14:55 の声を 10.5 半音上げ・フォルマント 1.10 倍の少し低めの女声に、息・囁きの成分・近接マイクの低音・柔らかい圧縮、5 度上 0.3 と 1 オクターヴ上 0.25、3.5 秒の残響) を 2 回 (0.55)、トラック 18 (ニ短調、そのまま) を 3 回、トラック 8 (ハ長調 / イ短調) を 4 度上げて全部と続き。組み立ては CCIX / CCXVIII と同じ
    I: 声 + トラック 18 → II: トラック 8 (全部) + トラック 18 (2 回目) → III: 声 (2 回目) + トラック 8 の続き → IV: トラック 18 の後半、消える。♩=60
  使い方: python compose_tablet219.py <bank201.json> <wav のフォルダ (20261108_145525.wav = ドエロの光輪の声, 20261107_180000.wav, 20261107_080000.wav)> [score_tablet219.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet233.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RV, R18, R08 = '20261108_145525', '20261107_180000', '20261107_080000'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 52, 100, 150, 176
NAMES = {RV: '11/08 14:55 の声 (安心するドエロの光輪様の声)', R18: 'トラック 18', R08: 'トラック 8'}
RATE = lambda semis: 2 ** (semis / 12.0)
PLAYS = [(RV, 2, 0.45, 0, 0.0, 198.5, True), (R18, 4, 0.5, 0, 0.0, 149.1, True),                       # I: 光輪の声 + トラック 18
         (R08, S2, 0.5, 5, 0.0, 249.2, True), (R18, S2 + 8, 0.45, 0, 0.0, 149.1, True),                # II: トラック 8 (4 度上げて、全部) + トラック 18 (2 回目)
         (RV, S3 + 2, 0.45, 0, 0.0, 198.5, True), (R08, S3 + 2, 0.4, 5, 100.0, 149.2, True),           # III: 声 (2 回目) + トラック 8 の続き
         (R18, S4 + 2, 0.45, 0, 60.0, 89.1, True)]                                                     # IV: トラック 18 の後半
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    LOOP = ['Dm', 'Bb', 'F', 'C']
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. 光輪の声とトラック 18 (♩=60)', '三賢者の光輪様の声にトラック 18 (ニ短調、そのまま)')
    P.section(S2, 'II. トラック 8 とトラック 18', 'トラック 8 (4 度上げて、全部) にトラック 18 をもう一度')
    P.section(S3, 'III. 光輪の声 (2 回目) とトラック 8 の続き', '光輪様の声をもう一度、トラック 8 の続き (100 秒から)')
    P.section(S4, 'IV. トラック 18 の後半、消える', 'トラック 18 の後半と声の終わり、一緒に消える')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if dur > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — %s' % (NAMES[rid], 'ドエロの光輪の声 (息と囁き、3 声と残響)' if rid == RV else ('実音、4 度上げて' if sm else '実音、そのまま')))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [RV, R18, R08], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCXXXIII · L\'aureola sensuale e le due tracce, voce calma',
        'subtitle': 'tablet219 の声を、響きと音量を抑えた聞き取りやすく安心するドエロの光輪様の声に (残響 1.5 秒・0.4、上声 0.2 / 0.15、息 −17 dB、rms −25 dB、0.45)。' + 'ドエロの光輪様の声 (息の多い少し低めの女声、三賢者の 3 声と残響) に、トラック 18 (そのまま) とトラック 8 (4 度上げて) を重ね合わせて。楽器なし。ヘ長調 / ニ短調、♩=60',
        'legend': [], 'vname': {},
        'footer': ['声 = 安心するドエロの光輪様の声 (10.5 半音上げ・フォルマント 1.10 倍、息 −17 dB、囁き +2 dB、2〜4 kHz +2 dB、8 kHz 以上を落とす、強めの柔らかい圧縮、5 度上 0.2 + 1 オクターヴ上 0.15、残響 1.5 秒・0.4、rms −25 dB) を 2 回 (0.45)。元: 光輪の声 = ドエロの光輪様の声 (10.5 半音上げ・フォルマント 1.10 倍の少し低めの女声に息・囁き・近接の低音、5 度上 0.3 + 1 オクターヴ上 0.25、3.5 秒の残響、rms −22.5 dB) を 2 回 (0.55)。トラック 18 (ニ短調) はそのまま 3 回 (0.5 / 0.45)、トラック 8 (ハ長調 / イ短調) は 4 度上げて全部と続き (0.5 / 0.4)。6 秒のフェード・イン、6〜10 秒のフェード・アウト', '楽器は何も加えない (サンプラーのピアノも、ペダルも、鐘もなし)。']}

if __name__ == '__main__':
    compose.main(OUT, seed=233, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
