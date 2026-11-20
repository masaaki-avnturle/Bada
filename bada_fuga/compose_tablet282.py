#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXXII · Requiem della Notte Santa (CCLXXXI のミックスを、クリスマスの聖夜の、しっとりするレクイエムに仕上げる)
  素材は CCLXXXI と同じ 2 つの鍵盤の録音だけ (楽器は何も加えない)。どちらも速さも音の高さも変えない:
    A   20261120_024046 (9 分 16 秒) — 前半は黒い鍵盤 (変ニ長調 / 変ロ短調)、5 分 1 秒のファから白い鍵盤 (ハ長調 / イ短調)
    B   20261121_041625 (8 分 34 秒) — 黒 → 白 (58.6 秒のファから) → … 黒い鍵盤と白い鍵盤を何度も行き来する
  しっとり = 音量を抑えて、打鍵をやわらかく、響きを途切れさせず、静かに始まり静かに消える。変えたのは 4 つ:
    1) 音量のつまみ (soften282.py): ゆっくりしたつまみで強弱の幅を 2 割 5 分に (CCLXXXI は 4 割)、強く弾いた音だけを抑えて余韻を残す (2:1)。
       曲の中の大きさの流れ (どこを小さく、どこを大きく) も、このつまみに書き込んである — README の数字。
       雑音だけの帯域 (3 kHz から上) も落とす。録音を始めた時の物音 (A は 4.4 秒まで、B は 3.0 秒まで) は入れない — 初めの 2 小節は本当の無音
    2) 響き: 残響の尾を 5 秒で切らずに 8 秒まで伸ばす (減り方も量も同じ。ぽつぽつ鳴る音の余韻が、次の音まで途切れずに残る)
    3) 形: レクイエムの形に (フォーレのレクイエムのように、怒りの日は無く、In paradisum で閉じる)。
       B の黒い鍵盤の出だし (58 秒) を、A の流れる所の上 (CCLXXXI) から、初めの A のぽつぽつ鳴る所の上へ移す — 聖夜の静けさの中で、2 つの夜の小さな音が交わる。
       B は、白い鍵盤の最初の音 (ファ) で、A の同じファと同時に入り直す。終わりに、A の初めの小さな音がもう一度鳴って、消える
    4) 仕上げの大きさ: 曲全体を小さめに (平均 −20 dB)
  CCLXXXI から変えていない所: 同じファを重ねる置き方 (B の g 秒は A の g + 242.428 秒)、B の休みを 22 秒長くすること、B が黒い鍵盤へ寄り道する 2 か所を小さくすること
  形:
    I.   Introitus (0 小節)       A のぽつぽつ鳴る小さな音 (2 小節 = 8 秒から)。1 分 6 秒から 2 分 0 秒まで、B の黒い鍵盤の出だしが重なる
    II.  Kyrie (45 小節)          A が途切れずに流れ始める (2 分 59 秒)
    III. Sanctus (76 小節)        同じファ (5 分 4 秒) で B が入り、2 つとも白い鍵盤へ。B は 6 分 23 秒から 28 秒休む
    IV.  Agnus Dei (103 小節)     B が戻る (6 分 51 秒)。2 つで、やわらかな山へ (8 分 54 秒)。A が終わる (9 分 19 秒)
    V.   Lux aeterna (139 小節)   B だけ (9 分 16 秒から) — 黒い鍵盤と白い鍵盤を行き来しながら、だんだん小さく
    VI.  In paradisum (196 小節)  A の初めの小さな音がもう一度 (13 分 4 秒から)。そのまま消える。206 小節
  和音の表示は、A が鳴っている間は A から、A が終わってからは B から、終わりはまた A から読んだもの。♩=60 は目盛り (鍵盤は拍に縛られずに弾かれている)
  使い方: python compose_tablet282.py <wav のフォルダ (20261120_024046.wav と 20261121_041625.wav — どちらも soften282.py を通したもの)>
          <chords282.json (analyze_chords.py の出力)> [score_tablet282.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet282.json'
GA = float(os.environ.get('GA', '0.233'))                                             # A の音量: 0.31 (CCLXXXI と同じ) × 0.752 — 大きさの流れを書き込んだぶん録音全体の rms が 2.48 dB 下がり、synth.py がそれを揃え直すので、倍率で戻す
GB = float(os.environ.get('GB', '0.232'))                                             # B の音量: 0.35 (CCLXXXI と同じ) × 0.664 — 同じく 3.56 dB ぶん
GR = float(os.environ.get('GR', '0.8'))                                               # 終わりにもう一度鳴る A の小さな音の倍率
DUCK1 = float(os.environ.get('DUCK1', '0.25'))                                        # B が黒い鍵盤へ寄り道する所のつまみ: 9 秒の寄り道
DUCK2 = float(os.environ.get('DUCK2', '0.125'))                                       # 大きな和音 5 つ
FIXPEAK = float(os.environ.get('FIXPEAK', '0.70'))                                    # 仕上げの大きさ (synth.py の基準)。曲の山は 0.390 なので、山に合わせるより 5 dB 小さい (平均 −20.5 dB)。0 なら山に合わせる
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RA, RB = '20261120_024046', '20261121_041625'
BPM = 60
COLA, COLB = (150, 195, 240), (245, 215, 150)   # 冬の夜の青、ろうそくの金
A_LEN, B_LEN = 556.3, 513.88
A_ON, B_ON = 4.4, 3.0                           # A は録音の 4.4 秒から、B は 3.0 秒から (どちらも、録音を始めた時の物音とその余韻を入れない。最初の音は A 5.23 秒、B 3.71 秒)
K0 = 3.0                                        # A: 録音の f 秒は曲の f + 3.0 秒。最初の音は 2 小節 (8 秒)
Y0 = float(os.environ.get('Y0', '59.0'))        # B の黒い鍵盤の出だしを置く A の時間: A のぽつぽつ鳴る音の間を B の音が埋める位置 (静かな窓がいちばん少ない、濁りの指数 0.17)
B0 = K0 + Y0                                    # 62.0: B の出だし: 録音の g 秒は曲の g + 62.0 秒
B_OPEN = 58.40                                  # B の出だしはここまで (黒い鍵盤の最後の音が消えた所; 58.585 秒が白い鍵盤の最初のファ)
B_F = 58.45                                     # B が入り直す所 (ファの直前)
X1 = 301.013 - 58.585                           # 242.428: B のファ (58.585 秒) を A のファ (301.013 秒) に合わせる (CCLXXXI と同じ)
HOLD = 22.0                                     # B の休み (137.5〜143.2 秒は無音) を長くする秒数 (CCLXXXI と同じ)
B1 = K0 + X1                                    # 245.428: B の前半 (休みまで): 録音の g 秒は曲の g + 245.428 秒
B2 = B1 + HOLD                                  # 267.428: B の後半 (休みの後): 録音の g 秒は曲の g + 267.428 秒
P_END, P_START = 139.0, 142.9                   # B の休み
E0, E1, XE0, XE1 = 111.3, 121.0, 0.4, 0.25      # 寄り道 1: 黒い鍵盤の 9 秒 (111.93〜120.8 秒)
C0, C1, XC = 227.93, 232.90, 0.12               # 寄り道 2: 黒い鍵盤の和音 5 つ (228.08〜231.3 秒)
R0 = float(os.environ.get('R0', '779.0'))       # 終わりにもう一度鳴る A: 録音の f 秒は曲の f + 779.0 秒 (最初の音は 13 分 4 秒 — B の録音が終わって 3 秒後、余韻が消えきる前)
R_END, R_FADE = 41.0, 18.0                      # A の 41 秒まで (次の音まで 7 秒空く所の手前)。終わりの 18 秒で消える — 最後に聞こえるのは変ト (36.4 秒の音)
S2, S3, S4, S5, S6, TOTAL = 45, 76, 103, 139, 196, 206
def play(rid, beat, gain, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
PLAYS = [play(RA, K0 + A_ON, GA, A_ON, A_LEN - A_ON, 0, COLA, '11/20 02:40 の鍵盤 — 初めから終わりまで (2 小節から)', fin=0.7, fout=2.0),
         # B の黒い鍵盤の出だし — A のぽつぽつ鳴る所の上に
         play(RB, B0 + B_ON, GB, B_ON, B_OPEN - B_ON, 1, COLB, '11/21 04:16 の鍵盤 — 黒い鍵盤の出だし', fin=0.6, fout=0.25),
         # B が同じファで入り直す (休みまで)
         play(RB, B1 + B_F, GB, B_F, E0 - B_F + XE0, 1, COLB, '11/21 04:16 の鍵盤 — 同じファから', fin=0.1, fout=XE0),
         play(RB, B1 + E0, GB * DUCK1, E0, E1 - E0 + XE1, 1, COLB, '黒い鍵盤への寄り道 — 小さく', fin=XE0, fout=XE1),
         play(RB, B1 + E1, GB, E1, P_END - E1, 1, COLB, '続き', fin=XE1, fout=1.5),
         # B の後半 (休みを 22 秒長くしてから)
         play(RB, B2 + P_START, GB, P_START, C0 - P_START + XC, 1, COLB, '11/21 04:16 — 休んでから、続き', fin=0.3, fout=XC),
         play(RB, B2 + C0, GB * DUCK2, C0, C1 - C0 + XC, 1, COLB, '', fin=XC, fout=XC),
         play(RB, B2 + C1, GB, C1, B_LEN - C1, 1, COLB, '続き — 終わりまで、だんだん小さく', fin=XC, fout=2.0),
         # 終わり: A の初めの小さな音をもう一度
         play(RA, R0 + A_ON, GA * GR, A_ON, R_END - A_ON, 0, COLA, '11/20 02:40 の鍵盤 — 初めの小さな音をもう一度', fin=0.7, fout=R_FADE)]
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍): A が鳴っている間は A、A が終わってからは B、終わりはまた A
LEAD = [(0, K0), (7, K0 + A_LEN - 3.0), (8, R0 + 5.2)]
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
    P.section(0, 'I. Introitus — 聖夜、黒い鍵盤の小さな音 (♩=60)', '2 小節から 11/20 の鍵盤。1 分 6 秒から 1 分ほど、11/21 の鍵盤が同じ黒い鍵盤で重なる')
    P.section(S2, 'II. Kyrie — 流れ始める', '2 分 59 秒から、11/20 の鍵盤が途切れずに流れる')
    P.section(S3, 'III. Sanctus — 同じファから、白い鍵盤へ', '5 分 4 秒、2 つの鍵盤が同じファの音で白い鍵盤 (ハ長調 / イ短調) へ。11/21 は 6 分 23 秒から休む')
    P.section(S4, 'IV. Agnus Dei — 2 つで、やわらかな山へ', '6 分 51 秒から、また 2 つで。8 分 54 秒に山、9 分 19 秒に 11/20 が終わる')
    P.section(S5, 'V. Lux aeterna — 11/21 の鍵盤だけ、だんだん小さく', '9 分 16 秒から。黒い鍵盤と白い鍵盤を行き来しながら、少しずつ静かに')
    P.section(S6, 'VI. In paradisum — 初めの小さな音に戻って、消える', '13 分 4 秒から、11/20 の初めの小さな音がもう一度。そのまま消えていく')
    return P

def post(P, events, ex):
    for p in PLAYS:         # 重ね方はこれまでのテープと同じ (60 Hz〜8 kHz、全体の残響、左右の遅れ)。速さも音の高さも変えない (semis=0)
        rid, off, dur = p['rid'], p['off'], p['dur']; c = CH.get(rid, {})
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05), env_off=off)
        add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [8.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXXII · Requiem della Notte Santa',
        'subtitle': '聖夜のための、しっとりするレクイエム。11/20 と 11/21 の鍵盤の録音だけで。♩=60',
        'footer': ['CCLXXXI のミックスを、聖夜のレクイエムに。素材は 11/20 02:40 と 11/21 04:16 の鍵盤の録音だけ。速さも音の高さも変えない。',
                   '音量を抑え、強い打鍵をやわらかく、響きの尾を長く。黒い鍵盤の小さな音で始まり、同じファから白い鍵盤へ。',
                   '終わりは 11/21 がだんだん小さくなり、初めの小さな音に戻って消える。楽器は何も加えない。206 小節。']}
if FIXPEAK > 0: META['fixed_peak'] = FIXPEAK

if __name__ == '__main__':
    compose.main(OUT, seed=282, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']), 'fixed_peak', d['meta'].get('fixed_peak'))
    for e in d['extras']: print('  %7.2f - %7.2f s  gain %.3f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
