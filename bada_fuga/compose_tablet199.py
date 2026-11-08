#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CXCIX · Quattro suoni originali (トラック 18・トラック 8・2026/11/08 13:51・11/06 18:54 の原音を重ねて — アルペジオや原曲に無い音は使わない)
  4 つの原音だけ、楽器は何も加えない (サンプラーのピアノも、ペダルも、鐘もなし): 13:51 の声は変換せず原音のまま (rms −22 dB に揃えるだけ)、18:54 の実音 (rms −22 dB) を途切れなく 3 回半、トラック 18 (ニ短調) はそのまま 2 回、トラック 8 (ハ長調 / イ短調) だけ 4 度上げてヘ長調 / ニ短調に (全部と続き)
    I: 声 + トラック 8 (裏) → II: トラック 18 → III: 声 (2 回目) + トラック 8 の続き (裏) → IV: トラック 18 の後半、消える。♩=60
  使い方: python compose_tablet199.py <bank150.json> <wav のフォルダ (20261108_135116.wav = 原音, 20261106_185402.wav, 20261107_180000.wav, 20261107_080000.wav)> [score_tablet199.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet199.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RV, R1854, R18, R08 = '20261108_135116', '20261106_185402', '20261107_180000', '20261107_080000'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 60, 100, 158, 176
NAMES = {RV: '11/08 13:51 (原音)', R1854: '11/06 18:54', R18: 'トラック 18', R08: 'トラック 8'}
RATE = lambda semis: 2 ** (semis / 12.0)
PLAYS = [(R1854, k * 50, 0.45, 0, 0.0, 205.8 if k < 3 else 96.0, True) for k in range(4)] + [       # 18:54 を途切れなく
         (R08, 2, 0.35, 5, 0.0, 200.0, True), (RV, 2, 0.55, 0, 0.0, 234.2, True),                  # I: 声 (原音)、トラック 8 (4 度上げて) が裏
         (R18, S2 + 1, 0.5, 0, 0.0, 149.1, True),                                                 # II: トラック 18
         (RV, S3 + 2, 0.55, 0, 0.0, 234.2, True), (R08, S3 + 2, 0.4, 5, 100.0, 149.2, True),       # III: 声 (2 回目)、トラック 8 の続きが裏
         (R18, S4 + 2, 0.45, 0, 60.0, 89.1, True)]                                                 # IV: トラック 18 の後半
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    LOOP = ['Dm', 'Bb', 'F', 'C']
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. 声 (♩=60)', '18:54 の上に 13:51 の声 (原音)、トラック 8 (4 度上げて) が裏に')
    P.section(S2, 'II. トラック 18', '18:54 の上にトラック 18 (ニ短調、そのまま)')
    P.section(S3, 'III. 声 (2 回目)', '18:54 の上に声をもう一度、トラック 8 の続きが裏に')
    P.section(S4, 'IV. トラック 18 の後半、消える', '18:54 の終わりとトラック 18 の後半、一緒に消える')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if dur > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — 原音%s' % (NAMES[rid], '、途切れなく 3 回半' if rid == R1854 else ('、4 度上げて、裏に' if sm else '、そのまま')))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [RV, R18, R08, R1854], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CXCIX · Quattro suoni originali',
        'subtitle': 'トラック 18・トラック 8・11/08 13:51・11/06 18:54 の原音を重ねて、アルペジオや原曲に無い音は使わない: 声は変換せず原音のまま、18:54 は途切れなく、トラック 18 はそのまま、トラック 8 だけ 4 度上げて。楽器なし。ニ短調 / ヘ長調、♩=60',
        'legend': [], 'vname': {},
        'footer': ['13:51 の声は原音のまま rms −22 dB に揃えて 2 回 (0.55)。18:54 は rms −22 dB で途切れなく 3 回半 (0.45)。トラック 18 (ニ短調) はそのまま全部と後半 (0.5 / 0.45)、トラック 8 (ハ長調 / イ短調) は 4 度上げて裏に 2 回 (0.35 / 0.4)。6 秒のフェード・イン、6〜10 秒のフェード・アウト', '楽器は何も加えない (サンプラーのピアノも、ペダルも、鐘もなし)。']}

if __name__ == '__main__':
    compose.main(OUT, seed=199, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
