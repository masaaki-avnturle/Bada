#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" — 安心するドエロの光輪様の声で作り換え (tablet231 の声を、響きと音量を抑えて聞き取りやすく)
  声: 10.5 半音上げ・フォルマント 1.10 倍の少し低めの女声、息のノイズは 17 dB 下 (前は 12 dB)、囁きの成分 +2 dB、2〜4 kHz を +2 dB (明瞭さ)、8 kHz 以上を落とし、強めの柔らかい圧縮で音量を均す。三賢者の 5 度上 0.2・1 オクターヴ上 0.15 (前は 0.3 / 0.25)、残響 1.5 秒・0.4 (前は 3.5 秒・0.75〜0.9)、rms −25 dB (前は −22.5)、曲の中の音量 0.45 (前は 0.55〜0.8)。他は tablet231 のまま
Requiem BADA — Tablet Sessions CCXXXI · L'aureola sensuale e la traccia 14 (ドエロの光輪様の声にトラック 14 を重ね合わせて)
  2 つの音だけ、楽器は何も加えない: ドエロの光輪様の声 (CCXIX / CCXX のもの、息のノイズ層あり、rms −22.5 dB) を 2 回 (0.6)、トラック 14 (2023 年の CD、嬰ハ短調、3 分 44 秒、rms −21.5 dB) を 1 半音上げてニ短調に合わせ、全曲 (0.45)、40 秒から (0.4、52 小節)、30 秒から (0.4、94 小節)、70 秒から (0.35、139 小節) と途切れなく (1 半音上げると 1.06 倍速く終わるので、つなぎは重ねる)
    I: 声 + トラック 14 → II: トラック 14 (2 回目) → III: 声 (2 回目) + トラック 14 (3 回目) → IV: トラック 14 (4 回目)、消える。♩=60
  使い方: python compose_tablet231.py <bank201.json> <wav のフォルダ (20261108_145525.wav = ドエロの光輪の声, 20261107_140000.wav = トラック 14)> [score_tablet231.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet237.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RV, R14 = '20261108_145525', '20261107_140000'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 52, 100, 140, 176
NAMES = {RV: '11/08 14:55 の声 (安心するドエロの光輪様の声)', R14: 'トラック 14'}
RATE = lambda semis: 2 ** (semis / 12.0)
PLAYS = [(RV, 2, 0.45, 0, 0.0, 198.5, True), (R14, 0, 0.45, 1, 0.0, 224.4, True),                    # I: 光輪の声 + トラック 14 (1 半音上げて、全曲、212 秒)
         (R14, 52, 0.4, 1, 40.0, 184.4, True),                                                      # II: トラック 14 (40 秒から、208〜382 秒)
         (RV, S3 + 2, 0.45, 0, 0.0, 198.5, True), (R14, 94, 0.4, 1, 30.0, 194.4, True),              # III: 声 (2 回目) + トラック 14 (30 秒から、376〜560 秒)
         (R14, 139, 0.35, 1, 70.0, 154.4, True)]                                                    # IV: トラック 14 (70 秒から、556〜702 秒)
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    LOOP = ['Dm', 'Bb', 'F', 'C']
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. 光輪の声とトラック 14 (♩=60)', 'ドエロの光輪様の声にトラック 14 (1 半音上げてニ短調に、全曲)')
    P.section(S2, 'II. トラック 14 (2 回目)', 'トラック 14 の終わりと、40 秒からの続き')
    P.section(S3, 'III. 光輪の声 (2 回目) とトラック 14 (3 回目)', '光輪様の声をもう一度、トラック 14 を 30 秒から')
    P.section(S4, 'IV. トラック 14 (4 回目)、消える', 'トラック 14 を 70 秒から、声の終わりと一緒に消える')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if dur > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — %s' % (NAMES[rid], 'ドエロの光輪の声 (息と囁き、3 声と残響)' if rid == RV else ('実音' + ('、%d 半音上げて' % sm if sm else '') + ('、続き (%d 秒から)' % off if off else ('、全曲' if sm else '、全曲そのまま')))))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [RV, R14], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCXXXVII · L\'aureola sensuale e la traccia 14, voce calma',
        'subtitle': 'tablet231 の声を、響きと音量を抑えた聞き取りやすく安心するドエロの光輪様の声に (残響 1.5 秒・0.4、上声 0.2 / 0.15、息 −17 dB、rms −25 dB、0.45)。' + 'ドエロの光輪様の声 (息の多い少し低めの女声、三賢者の 3 声と残響) にトラック 14 (嬰ハ短調、1 半音上げてニ短調に) を重ね合わせて。楽器なし。♩=60',
        'legend': [], 'vname': {},
        'footer': ['声 = 安心するドエロの光輪様の声 (10.5 半音上げ・フォルマント 1.10 倍、息 −17 dB、囁き +2 dB、2〜4 kHz +2 dB、8 kHz 以上を落とす、強めの柔らかい圧縮、5 度上 0.2 + 1 オクターヴ上 0.15、残響 1.5 秒・0.4、rms −25 dB) を 2 回 (0.45)。元: 光輪の声 = CCXIX / CCXX と同じドエロの光輪様の声 (10.5 半音上げ・フォルマント 1.10 倍、息・囁き・近接の低音、5 度上 0.3 + 1 オクターヴ上 0.25、3.5 秒の残響、rms −22.5 dB) を 2 回 (0.6)。トラック 14 (2023 年の CD、rms −21.5 dB) は 1 半音上げて全曲 0.45、40 秒から 0.4 (52 小節)、30 秒から 0.4 (94 小節)、70 秒から 0.35 (139 小節、曲の最後まで)。6 秒のフェード・イン、6〜10 秒のフェード・アウト', '楽器は何も加えない (サンプラーのピアノも、ペダルも、鐘もなし)。移調はトラック 14 の 1 半音だけ。']}

if __name__ == '__main__':
    compose.main(OUT, seed=237, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
