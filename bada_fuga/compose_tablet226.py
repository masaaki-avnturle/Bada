#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCXXVI · L'aureola della giovane donna sul 89 (若かりし女性の光輪様の声に tablet89 を重ね合わせて)
  2 つの音だけ、楽器は何も加えない: 若かりし女性の光輪様の声 (CCXVI — 13 半音上げ・フォルマント 1.15 倍の若い女性の声 + 5 度上 + 1 オクターヴ上、3.5 秒の残響、rms −22.5 dB) を 2 回 (0.6)、tablet89 (LXXXIX — レクイエムとフーガ、ニ短調、6 分 31 秒) を全曲 (0.5) と後半 (90 秒から、0.45)。どちらも原音のまま
    I: 声 + tablet89 の始まり → II: tablet89 のフーガ → III: 声 (2 回目) + tablet89 の後半 → IV: tablet89 の終わり、消える。♩=60
  使い方: python compose_tablet226.py <bank201.json> <wav のフォルダ (20261108_145525.wav = 若かりし女性の光輪の声, 20261107_089000.wav = tablet89)> [score_tablet226.json]
"""
import sys, os, json, math
BANKP, WDIR = sys.argv[1], os.path.abspath(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet226.json'
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
RV, R89 = '20261108_145525', '20261107_089000'
BPM = 60
S1, S2, S3, S4, TOTAL = 0, 50, 100, 140, 176
NAMES = {RV: '11/08 14:55 の声 (若かりし女性の光輪様の声)', R89: 'tablet89'}
RATE = lambda semis: 2 ** (semis / 12.0)
PLAYS = [(RV, 2, 0.6, 0, 0.0, 198.5, True), (R89, 0, 0.5, 0, 0.0, 391.0, True),                     # I〜II: 光輪の声 + tablet89 全曲 (98 小節)
         (RV, S3 + 2, 0.6, 0, 0.0, 198.5, True), (R89, S3, 0.45, 0, 90.0, 300.0, True)]              # III〜IV: 声 (2 回目) + tablet89 の後半 (90 秒から、終わりまで)
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    LOOP = ['Dm', 'Bb', 'F', 'C']
    for q in range(TOTAL * BPB): P.harm[q] = LOOP[(q // BPB) % 4]
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(S1, 'I. 光輪の声と tablet89 の始まり (♩=60)', '若かりし女性の光輪様の声に tablet89 (レクイエム、ニ短調、そのまま)')
    P.section(S2, 'II. tablet89 のフーガ', 'tablet89 の続き (フーガ)')
    P.section(S3, 'III. 光輪の声 (2 回目) と tablet89 の後半', '光輪様の声をもう一度、tablet89 の後半 (90 秒から)')
    P.section(S4, 'IV. tablet89 の終わり、消える', 'tablet89 の終わりと声の終わり、一緒に消える')
    return P

def post(P, events, ex):
    for rid, bar, g, sm, off, dur, lead in PLAYS:
        add('REC', bar * BPB, dur / RATE(sm) * BPM / 60.0, 0, g, None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=0.02 if bar == 0 else 6.0, fout=6.0 if dur > 150 else 10.0, semis=sm, rid=rid + '.wav', tag='%s — %s' % (NAMES[rid], '若かりし女性の光輪の声 (3 声と残響)' if rid == RV else ('実音、後半 (90 秒から)' if off else '実音、全曲そのまま')))

META = {'style': 'recsampler', 'bank': BANKP, 'rec_order': [RV, R89], 'piano_decay': 2.6, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCXXVI · L\'aureola della giovane donna sul 89',
        'subtitle': '若かりし女性の光輪様の声 (CCXVI の三賢者の 3 声と残響) に tablet89 (レクイエムとフーガ、ニ短調) を原音のまま重ね合わせて。楽器なし。♩=60',
        'legend': [], 'vname': {},
        'footer': ['光輪の声 = CCXVI と同じ (13 半音上げ・フォルマント 1.15 倍の若い女性の声 + 5 度上 + 1 オクターヴ上、3.5 秒の残響、rms −22.5 dB) を 2 回 (0.6)。tablet89 (LXXXIX) は全曲そのまま 0.5、後半 (90 秒から) をもう一度 0.45。6 秒のフェード・イン、6〜10 秒のフェード・アウト', '楽器は何も加えない (サンプラーのピアノも、ペダルも、鐘もなし)。移調もなし。']}

if __name__ == '__main__':
    compose.main(OUT, seed=226, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(d['duration']), 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem + 8); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']))
