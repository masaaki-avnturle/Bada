#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCXLI · Tsukuyomi e le due tracce (11/12 13:31 の声の三賢者の月読様 — 17 歳の女性 3 声 — に、トラック 18 とトラック 8 を重ね合わせて)
  3 つの音だけ、楽器は何も加えない: 月読様の声 (11.39 半音上げ・261 Hz・フォルマント 1.18 倍の 17 歳の女声 3 人の斉唱、澄んだ高域、残響 2.2 秒・0.35、rms −24 dB、176 秒) を 2 回 (0.5)、トラック 18 (ニ短調、そのまま) を 3 回、トラック 8 (ハ長調 / イ短調) を 4 度上げて全部と続き。組み立ては CCIX / CCXXXIX と同じ
    I: 声 + トラック 18 → II: トラック 8 (全部) + トラック 18 (2 回目) → III: 声 (2 回目) + トラック 8 の続き → IV: トラック 18 の後半、消える。♩=60
  使い方: python compose_tablet241.py <bank201.json> <wav のフォルダ (20261112_133145.wav = 月読様の声, 20261107_180000.wav, 20261107_080000.wav)> [score_tablet241.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet241.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RV, R18, R08 = '20261112_133145', '20261107_180000', '20261107_080000'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 52, 100, 150, 176
NAMES = {RV: '11/12 13:31 の声 (三賢者の月読様、17 歳の女性 3 声)', R18: 'トラック 18', R08: 'トラック 8'}
RATE = lambda semis: 2 ** (semis / 12.0)
PLAYS = [(RV, 2, 0.5, 0, 0.0, 176.0, True), (R18, 4, 0.5, 0, 0.0, 149.1, True),                       # I: 光輪の声 + トラック 18
         (R08, S2, 0.5, 5, 0.0, 249.2, True), (R18, S2 + 8, 0.45, 0, 0.0, 149.1, True),                # II: トラック 8 (4 度上げて、全部) + トラック 18 (2 回目)
         (RV, S3 + 2, 0.5, 0, 0.0, 176.0, True), (R08, S3 + 2, 0.4, 5, 100.0, 149.2, True),           # III: 声 (2 回目) + トラック 8 の続き
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
        add('REC', bar * BPB, dur / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if dur > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — %s' % (NAMES[rid], '月読様の声 (17 歳の女性 3 声の斉唱)' if rid == RV else ('実音、4 度上げて' if sm else '実音、そのまま')))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [RV, R18, R08], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCXLI · Tsukuyomi e le due tracce',
        'subtitle': '11/12 13:31 の声を変換した三賢者の月読様の声 (17 歳の女性 3 声の斉唱、澄んだ声) に、トラック 18 (そのまま) とトラック 8 (4 度上げて) を重ね合わせて。楽器なし。ヘ長調 / ニ短調、♩=60',
        'legend': [], 'vname': {},
        'footer': ['月読様の声 = 11/12 13:31 の声を 11.39 半音上げて 261 Hz の 17 歳の女声に (フォルマント 1.18 倍)、3 人の斉唱 (+0.25 / −0.3 半音、38 / 74 ms の遅れ)、5〜9 kHz +1.5 dB、残響 2.2 秒・0.35、rms −24 dB を 2 回 (0.5)。トラック 18 (ニ短調) はそのまま 3 回 (0.5 / 0.45)、トラック 8 (ハ長調 / イ短調) は 4 度上げて全部と続き (0.5 / 0.4)。6 秒のフェード・イン、6〜10 秒のフェード・アウト', '楽器は何も加えない (サンプラーのピアノも、ペダルも、鐘もなし)。']}

if __name__ == '__main__':
    compose.main(OUT, seed=241, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
