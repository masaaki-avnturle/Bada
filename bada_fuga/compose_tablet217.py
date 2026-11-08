#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCXVII · L'aureola della giovane donna, la fuga e il tablet89 (若かりし女性の光輪様の声・fuga・tablet89 を、無い楽器を加えずに重ね合わせて)
  3 つの音だけ、楽器は何も加えない (サンプラーも無し): 若かりし女性の光輪様の声 (CCXVI — 13 半音上げ・フォルマント 1.15 倍の若い女性の声 + 5 度上 + 1 オクターヴ上、3.5 秒の残響) を 2 回 (0.6)、fuga (オルガンのフーガ、ニ短調、329 秒) を全部 1 回と終わりの 90 秒をもう一度 (0.32 / 0.3)、tablet89 (ヘ長調 / ニ短調、391 秒) を全部 1 回と後半をもう一度 (0.35 / 0.3)。どれも原音のまま (移調なし)
    I: 声 + tablet89 → II: fuga (全部) + tablet89 の続き → III: 声 (2 回目) + fuga の終わり + tablet89 の後半 → IV: fuga の終わりをもう一度、消える。♩=60
  使い方: python compose_tablet217.py <bank201.json> <wav のフォルダ (20261108_145525.wav = 若かりし女性の光輪の声, fuga.wav, 20261107_089000.wav = tablet89)> [score_tablet217.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet217.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RV, RF, R89 = '20261108_145525', 'fuga', '20261107_089000'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 52, 100, 152, 178
NAMES = {RV: '11/08 14:55 の声 (若かりし女性の光輪様の声)', RF: 'fuga', R89: 'tablet89'}
RATE = lambda semis: 2 ** (semis / 12.0)
PLAYS = [(RV, 2, 0.6, 0, 0.0, 198.5, True), (R89, 0, 0.35, 0, 0.0, 391.0, True),                     # I: 光輪の声 + tablet89 (全部、II まで)
         (RF, S2, 0.32, 0, 0.0, 329.0, True),                                                          # II: fuga (全部、III まで)
         (RV, S3, 0.6, 0, 0.0, 198.5, True), (R89, S3 + 4, 0.3, 0, 200.0, 191.0, True),               # III: 声 (2 回目) + tablet89 の後半
         (RF, S4, 0.3, 0, 239.0, 90.0, True)]                                                         # IV: fuga の終わりをもう一度
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    LOOP = ['Dm', 'Bb', 'F', 'C']
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. 光輪の声と tablet89 (♩=60)', '若かりし女性の光輪様の声に tablet89 (ヘ長調 / ニ短調、そのまま)')
    P.section(S2, 'II. fuga と tablet89 の続き', 'fuga (ニ短調、全部) に tablet89 の続き')
    P.section(S3, 'III. 光輪の声 (2 回目)、fuga の終わり、tablet89 の後半', '光輪様の声をもう一度、fuga の終わりと tablet89 の後半 (200 秒から)')
    P.section(S4, 'IV. fuga の終わりをもう一度、消える', 'fuga の終わり (239 秒から) をもう一度、消える')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if dur > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — %s' % (NAMES[rid], '若かりし女性の光輪の声 (3 声と残響)' if rid == RV else '原音、そのまま'))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [RV, RF, R89], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCXVII · L\'aureola della giovane donna, la fuga e il tablet89',
        'subtitle': '若かりし女性の光輪様の声 (CCXVI の三賢者の 3 声と残響) に、fuga (ニ短調) と tablet89 (ヘ長調 / ニ短調) を原音のまま重ね合わせて。楽器なし。♩=60',
        'legend': [], 'vname': {},
        'footer': ['光輪の声 = CCXVI と同じ (13 半音上げ・フォルマント 1.15 倍の若い女性の声 + 5 度上 + 1 オクターヴ上、3.5 秒の残響、rms −22.5 dB) を 2 回 (0.6)。fuga (329 秒) は全部 1 回 (0.32) と終わりの 90 秒をもう一度 (0.3)、tablet89 (391 秒) は全部 1 回 (0.35) と 200 秒からの後半をもう一度 (0.3)。6 秒のフェード・イン、6〜10 秒のフェード・アウト', '楽器は何も加えない (サンプラーのピアノも、ペダルも、鐘もなし)。移調もなし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=217, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
