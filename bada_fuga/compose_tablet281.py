#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXXI · Due notti, una tastiera (11/20 02:40 と 11/21 04:16 の鍵盤の録音をミックス)
  素材は 2 つの鍵盤の録音だけ (楽器は何も加えない)。どちらも速さも音の高さも変えない:
    A   届いた 20261120_024046.mp3 (9 分 16 秒) — 前半は黒い鍵盤 (変ニ長調 / 変ロ短調)、5 分 1 秒のファから白い鍵盤 (ハ長調 / イ短調)
    B   届いた 20261121_041625.mp3 (8 分 34 秒) — 黒 (0〜58 秒) → 白 (58.6 秒のファから) → 黒 (1 分 52 秒から 9 秒だけ) → 白 (2 分 1 秒から) →
        黒 (4 分 49 秒から) → 白 (5 分 43 秒から) → 黒 (7 分 30 秒から) → 白 (8 分 19 秒から終わりまで)
    どちらも level273.py で強弱の幅を 4 割にしたもの (tablet276 のピアノの音と同じ; 音量のつまみだけ)。重ね方もこれまでのテープと同じ (60 Hz〜8 kHz、全体の残響、左右の遅れ)
  黒い鍵盤の音と白い鍵盤の音は半音ずれているので、重ねると濁る (濁りの指数: 黒に黒 0.18〜0.24、白に白 0.29〜0.32、黒に白 0.47〜0.55)。
  そこで、2 つの録音の「黒い鍵盤から白い鍵盤へ移る所」を合わせて置く:
    どちらも、白い鍵盤の最初の音は同じファ (A は 301.013 秒のファ、B は 58.585 秒のファ)。この 2 つのファが同時に鳴るように B を置く (B の g 秒は A の g + 242.428 秒)。
    B の黒い鍵盤の出だし (58 秒) は A の黒い鍵盤の終わりの上に、B の白い鍵盤は A の白い鍵盤の上に来る
  B の白い鍵盤 (230 秒) は A の白い鍵盤 (252 秒) より 22 秒短い。そのままだと、A の終わりの山 (A の 8 分 51 秒から) の上で B が先に黒い鍵盤へ戻って濁る (指数 0.41〜0.66)。
    B は自分の 2 分 17 秒から 5.7 秒、休んでいる (無音)。この休みを 22 秒長くして (B を止めて待たせるだけ; 音は切らない)、
    B が黒い鍵盤へ戻る音 (288.94 秒の変ホ) を、A の最後の音 (550.70 秒) の 2.7 秒後に置く。すると B の小さな繋ぎ (B の 4 分 20 秒〜4 分 28 秒) が A の山の前の静かな所に、
    B の大きな所が A の山に重なり、A が終わる所で B が黒い鍵盤へ移る (重なっている所の指数は 0.326 → 0.313、終わりの山は 0.25〜0.42)
  B が白い鍵盤の間に黒い鍵盤へ寄り道する 2 か所 (B の 1 分 52 秒〜2 分 1 秒の 9 秒と、3 分 48 秒〜3 分 52 秒の大きな和音 5 つ) は、A の白い鍵盤とぶつかるので、
    そこだけ B のつまみを下げる (9 秒の方は 12 dB、和音の方は 18 dB; 同じ録音どうしのクロスフェードでつまみを動かす; 音は切らない)。どちらも A より 12〜13 dB 小さく鳴る
  形:
    I:    A だけ — 黒い鍵盤、小さな音がぽつぽつと (2 小節 = 8 秒から)
    II:   A が途切れずに流れ始める (2 分 59 秒)
    III:  B が入る (4 分 5 秒、最初の音は 4 分 9 秒) — 黒い鍵盤に黒い鍵盤
    IV:   同じファ (5 分 4 秒) から、2 つとも白い鍵盤へ。B は 6 分 23 秒から 28 秒休む
    V:    B が戻る (6 分 51 秒)。一緒に A の終わりの山へ (8 分 54 秒)
    VI:   A が終わり (9 分 19 秒)、B だけ — 黒い鍵盤 (9 分 16 秒から)
    VII:  B だけ — 白い鍵盤 (10 分 11 秒から)
    VIII: B だけ — もう一度黒い鍵盤 (11 分 57 秒)、白い鍵盤 (12 分 46 秒) で終わる (13 分 1 秒)。196 小節
  和音の表示は、A が鳴っている間は A から、A が終わってからは B から読んだもの。♩=60 は目盛り (鍵盤は拍に縛られずに弾かれている)
  使い方: python compose_tablet281.py <wav のフォルダ (20261120_024046.wav と 20261121_041625.wav — どちらも level273.py を通したもの)>
          <chords281.json (analyze_chords.py の出力)> [score_tablet281.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet281.json'
GA = float(os.environ.get('GA', '0.31'))                                              # A の音量 (tablet276・278 と同じ)
GB = float(os.environ.get('GB', '0.35'))                                              # B の音量 (ステムを測って決めた: 白い鍵盤で重なる所で A と同じ大きさ)
DUCK1 = float(os.environ.get('DUCK1', '0.25'))                                        # B が黒い鍵盤へ寄り道する所のつまみ: 9 秒の寄り道 (−12 dB)
DUCK2 = float(os.environ.get('DUCK2', '0.125'))                                       # 大きな和音 5 つ (−18 dB; そのままだと A より 6 dB 大きい)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RA, RB = '20261120_024046', '20261121_041625'
BPM = 60
COLA, COLB = (140, 200, 235), (240, 200, 140)
A_LEN, B_LEN = 556.3, 513.88
K0 = 3.0                                        # A: 録音の f 秒は曲の f + 3.0 秒。最初の音は 2 小節 (8 秒)
X1 = 301.013 - 58.585                           # 242.428: B の白い鍵盤の最初の音 (58.585 秒のファ) を、A の白い鍵盤の最初の音 (301.013 秒のファ) に合わせる
HOLD = float(os.environ.get('HOLD', '22.0'))    # B の休み (137.5〜143.2 秒は無音) を長くする秒数
B1 = K0 + X1                                    # 245.428: B の前半 (休みまで): 録音の g 秒は曲の g + 245.428 秒
B2 = B1 + HOLD                                  # 267.428: B の後半 (休みの後): 録音の g 秒は曲の g + 267.428 秒
P_END, P_START = 139.0, 142.9                   # B の休み: 前半は 139.0 秒まで (137.5 秒から無音)、後半は 142.9 秒から (143.22 秒に小さな音、146.07 秒から弾き始める)
E0, E1, XE0, XE1 = 111.3, 121.0, 0.4, 0.25      # 寄り道 1: 黒い鍵盤の 9 秒 (111.93〜120.8 秒)。つまみは無音の所 (111.3 秒) で下げ、白い鍵盤の音 (121.26 秒) の直前で戻す
C0, C1, XC = 227.93, 232.90, 0.12               # 寄り道 2: 黒い鍵盤の和音 5 つ (228.08〜231.3 秒)。次の白い鍵盤の音 (232.98 秒) で戻す
S2, S3, S4, S5, S6, S7, S8, TOTAL = 45, 61, 76, 103, 139, 153, 179, 196
def play(rid, beat, gain, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
PLAYS = [play(RA, K0, GA, 0.0, A_LEN, 0, COLA, '11/20 02:40 の鍵盤の録音 — 初めから終わりまで (2 小節から)', fin=0.5, fout=2.0),
         # B の前半 (休みまで)
         play(RB, B1, GB, 0.0, E0 + XE0, 1, COLB, '11/21 04:16 の鍵盤の録音 — 初めから', fin=0.5, fout=XE0),
         play(RB, B1 + E0, GB * DUCK1, E0, E1 - E0 + XE1, 1, COLB, '黒い鍵盤への寄り道 — 小さく', fin=XE0, fout=XE1),
         play(RB, B1 + E1, GB, E1, P_END - E1, 1, COLB, '続き', fin=XE1, fout=1.5),
         # B の後半 (休みを 22 秒長くしてから)
         play(RB, B2 + P_START, GB, P_START, C0 - P_START + XC, 1, COLB, '11/21 04:16 — 休んでから、続き', fin=0.3, fout=XC),
         play(RB, B2 + C0, GB * DUCK2, C0, C1 - C0 + XC, 1, COLB, '', fin=XC, fout=XC),
         play(RB, B2 + C1, GB, C1, B_LEN - C1, 1, COLB, '続き — 終わりまで', fin=XC, fout=2.0)]
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍): A が鳴っている間は A、A が終わってからは B
LEAD = [(0, K0), (6, K0 + A_LEN - 3.0)]
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
    P.section(0, 'I. 11/20 の鍵盤 — 黒い鍵盤、小さな音がぽつぽつと (♩=60)', '2 小節から。変ニ長調 / 変ロ短調、小さな音が 5〜6 秒ごとに')
    P.section(S2, 'II. 流れ始める', '2 分 59 秒から途切れずに流れ、少しずつ大きくなる')
    P.section(S3, 'III. 11/21 の鍵盤が入る — 黒い鍵盤に黒い鍵盤', '4 分 9 秒から、もう 1 つの夜の鍵盤が同じ黒い鍵盤で重なる')
    P.section(S4, 'IV. 同じファから、2 つとも白い鍵盤へ', '5 分 4 秒、2 つの録音が同じファの音で白い鍵盤 (ハ長調 / イ短調) へ移る。11/21 は 6 分 23 秒から休む')
    P.section(S5, 'V. 11/21 の鍵盤が戻る — 一緒に山へ', '6 分 51 秒から、また 2 つで。8 分 54 秒に 11/20 の終わりの山')
    P.section(S6, 'VI. 11/21 の鍵盤だけ — 黒い鍵盤へ', '11/20 が終わる所 (9 分 16 秒) で、11/21 が黒い鍵盤へ移る')
    P.section(S7, 'VII. 11/21 の鍵盤だけ — 白い鍵盤', '10 分 11 秒から白い鍵盤。途中にごく小さな音の所がある')
    P.section(S8, 'VIII. もう一度黒い鍵盤、白い鍵盤で終わる', '11 分 57 秒から黒い鍵盤、12 分 46 秒から白い鍵盤。13 分 1 秒に終わる')
    return P

def post(P, events, ex):
    for p in PLAYS:         # どちらも tablet276 のピアノの音と同じ重ね方 (これまでのテープと同じ: 全体の残響)。速さも音の高さも変えない (semis=0)
        rid, off, dur = p['rid'], p['off'], p['dur']; c = CH.get(rid, {})
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05), env_off=off)
        add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXXI · Due notti, una tastiera',
        'subtitle': '11/20 02:40 と 11/21 04:16 の鍵盤の録音をミックス。黒い鍵盤 → 白い鍵盤、♩=60',
        'footer': ['11/20 02:40 と 11/21 04:16 の鍵盤の録音だけ。どちらも速さも音の高さも変えない。楽器は何も加えない。',
                   '2 つとも黒い鍵盤から白い鍵盤へ移る。その移り目の同じファの音を重ねて置いた。白い鍵盤の間は一緒に鳴る。',
                   '11/20 が終わると、11/21 がひとりで黒い鍵盤へ戻り、白い鍵盤で終わる。196 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=281, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.2f - %7.2f s  gain %.3f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
