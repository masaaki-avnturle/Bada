#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXVIII · La tastiera sola (tablet276 のピアノの音だけに)
  tablet276 (CCLXXVI — calma の声 + 11/20 02:40 の鍵盤の録音) から声を外して、ピアノ (鍵盤の録音) だけにする。楽器は何も加えない
  ピアノの音は tablet276 と同じ:
    level273.py で強弱の幅を 4 割にした鍵盤の録音を、これまでのテープと同じ重ね方 (60 Hz〜8 kHz、全体の残響、左右の遅れ) で、初めから終わりまで
  変えたのは置く位置だけ: tablet276 では声が先に立つように、鍵盤の最初の音を 13.5 秒に置いていた。声が無いので、初めの 2 小節を無音にして、
    鍵盤の最初の音を 2 小節 (8 秒) に置く (録音の f 秒は曲の f + 3.0 秒)
  鍵盤の形 (録音から読んだもの):
    I:   黒い鍵盤 (変ニ長調 / 変ロ短調) — 小さな音が 5〜6 秒ごとにぽつぽつと
    II:  2 分 59 秒から途切れずに流れ、少しずつ大きくなり、前半の山を築いて、止まる (5 分 7 秒)
    III: 半音ひとつ下がって、白い鍵盤 (ハ長調 / イ短調) — 5 分 9 秒から
    IV:  いちばん大きい所 (7 分) から終わりへ (9 分 19 秒)。140 小節
  和音の表示は鍵盤の録音から読んだもの。♩=60 は目盛り (鍵盤は拍に縛られずに弾かれている)
  使い方: python compose_tablet278.py <wav のフォルダ (20261120_024046.wav = level273.py を通した鍵盤の録音 — tablet276 と同じもの)>
          <chords278.json (analyze_chords.py の出力)> [score_tablet278.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet278.json'
GK = float(os.environ.get('GK', '0.31'))                                              # 鍵盤の音量 (tablet276 と同じ; 曲は最後に山を揃えるので、ひとりの時は大きさに効かない)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RK = '20261120_024046'
BPM = 60
COLK = (140, 200, 235)
K_LEN = 556.3                                   # 鍵盤の録音: 初めから終わりまで (最初の音は 5.0 秒)
K0 = 3.0                                        # 鍵盤: 録音の f 秒は曲の f + 3.0 秒。最初の音は 2 小節 (8 秒)
S2, S3, S4, TOTAL = 45, 77, 105, 140            # 流れ始める (録音の 176 秒) / 白い鍵盤 (録音の 306 秒) / いちばん大きい所 (録音の 417 秒)
def play(rid, beat, gain, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
PLAYS = [play(RK, K0, GK, 0.0, K_LEN, 0, COLK, '11/20 02:40 の鍵盤の録音 — tablet276 と同じ音 (2 小節から)', fin=0.5, fout=2.0)]
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍)
LEAD = [(0, K0)]
def harm_at(q):
    cur = 'Bbm'
    for k, a in LEAD:
        p = PLAYS[k]
        if q >= a:
            c = CH[p['rid']]; ts = p['off'] + max(q - p['beat'], 0.0)                        # 録音の中の秒
            cur = c['chords'][min(int(min(ts, p['off'] + p['dur'] - 0.01) / c['win']), len(c['chords']) - 1)]
    return cur
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    for q in range(TOTAL * BPB): P.harm[q] = harm_at(q)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(0, 'I. 黒い鍵盤 — 小さな音がぽつぽつと (♩=60)', '2 小節から鍵盤。変ニ長調 / 変ロ短調、小さな音が 5〜6 秒ごとに')
    P.section(S2, 'II. 流れ始める — 前半の山へ', '2 分 59 秒から途切れずに流れ、少しずつ大きくなり、山を築いて、止まる (5 分 7 秒)')
    P.section(S3, 'III. 白い鍵盤 — ハ長調 / イ短調', '半音ひとつ下がって、5 分 9 秒から白い鍵盤だけで')
    P.section(S4, 'IV. いちばん大きい所から終わりへ', '鍵盤は 9 分 19 秒に終わる')
    return P

def post(P, events, ex):
    for p in PLAYS:         # 鍵盤: tablet276 と同じ重ね方 (これまでのテープと同じ: 全体の残響)
        rid, off, dur = p['rid'], p['off'], p['dur']; c = CH.get(rid, {})
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05), env_off=off)
        add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXVIII · La tastiera sola',
        'subtitle': 'tablet276 のピアノの音だけ (11/20 02:40 の鍵盤の録音)。変ニ長調 → ハ長調、♩=60',
        'footer': ['tablet276 から声を外して、ピアノ (11/20 02:40 の鍵盤の録音) だけに。音は tablet276 と同じ (強弱の幅を 4 割に、全体の残響)。',
                   '前半は黒い鍵盤 (変ニ長調 / 変ロ短調)、5 分 7 秒で止まって、後半は白い鍵盤 (ハ長調 / イ短調)。',
                   '楽器は何も加えない。初めの 2 小節は無音、2 小節から鍵盤。140 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=278, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
