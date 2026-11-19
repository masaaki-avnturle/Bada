#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXVII · L'aureola e la tastiera vera (CCLXXVI を実音で — calma の声と 11/20 02:40 の鍵盤の録音を、どちらも録音のまま重ねて)
  素材は 2 つ、どちらも録音のまま (楽器は何も加えない):
    声   届いた 20261108_145525_aureola_sensuale_calma.mp3 (11/08 14:55 の声 → 少し低めの女声、響きと音量を抑えた、安心するドエロの光輪様の声)
    曲   届いた 20261120_024046.mp3 — 鍵盤の録音 (9 分 16 秒)
  実音 = 録音を加工せずにそのまま流す (このプロジェクトでの使い方: 速さも音高も元のまま、楽器を足さない)。CCLXXVI から変えた所:
    鍵盤   強弱の幅を 4 割にしない (level273.py を通さない — 初めの小さな音は小さいまま、9 分 16 秒かけて 25 dB 大きくなる)。
           60 Hz 以下と 8 kHz 以上を削らない、全体の残響を足さない、左右の遅れを足さない (synth.py の faithful の経路)
    声     3 つに分けて音量を持ち上げない — 声の静かな話し始めは、鍵盤の小さな出だしとそのまま釣り合う
    変えたのは、録音ごとの音量のつまみ (1 つの録音の中では動かさない) と、置く位置だけ。2 回目の声は 1 回目より 3 dB 大きく置く —
    鍵盤の後半は前半より 14 dB ほど大きいので、同じ大きさだと 2 回目の声が鍵盤に埋もれ、1 回目は鍵盤が聞こえない
  形は CCLXXVI と同じ:
    I:  声 (2 小節 = 8 秒から) + 鍵盤 (14 秒から)。鍵盤は小さな音がぽつぽつと鳴る所から、3 分 5 秒に途切れずに流れ始める。声は 3 分 19 秒まで →
    II: 鍵盤だけ — 少しずつ大きくなり、前半の山を築いて、止まる (5 分 12 秒) →
    III: 声をもう一度 (5 分 13 秒から)。鍵盤が止まった所で声が先に入り、白い鍵盤が 2 秒後から。声は 8 分 24 秒まで →
    IV: 鍵盤だけ — いちばん大きい所から終わりへ (9 分 25 秒)。142 小節
  鍵盤の最初の音は 14.0 秒 (CCLXXVI は 13.5 秒): 録音のままだと、鍵盤の出だしは 5〜6 秒ごとに小さな音が 2 秒ほど鳴るだけで、その間はほとんど無音。
    声の長い息継ぎ (声の 49.6 秒から 1.4 秒) がその無音に重なると、1 秒ほど音が途切れる。鍵盤を 0.1 秒刻みで動かして、声の息継ぎのどこにも
    鍵盤の音が鳴る位置を選んだ
  和音の表示は鍵盤の録音から読んだもの。♩=60 は目盛り (鍵盤は拍に縛られずに弾かれている)
  使い方: python compose_tablet277.py <wav のフォルダ (20261108_145525.wav = calma の声, 20261120_024046.wav = 鍵盤の録音 — どちらも mp3 を wav にしただけのもの)>
          <chords277.json (analyze_chords.py の出力)> [score_tablet277.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet277.json'
GV1 = float(os.environ.get('GV1', '0.55'))                                            # 声 (1 回目) の音量 — 鍵盤の小さな前半の上
GV2 = float(os.environ.get('GV2', '0.80'))                                            # 声 (2 回目) の音量 — 鍵盤の大きな後半の上
GK = float(os.environ.get('GK', '0.55'))                                              # 鍵盤の音量 (曲を通して 1 つ)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, RK = '20261108_145525', '20261120_024046'
BPM = 60
COLV, COLK = (255, 190, 160), (140, 200, 235)
V_OFF, V_ON, V_LEN = 4.86, 5.36, 198.46         # calma の声: 録音の 4.86 秒から終わりまで (話し始めは 5.36 秒、話し終わりは 195.9 秒)
K_LEN = 556.3                                   # 鍵盤の録音: 初めから終わりまで (最初の音は 5.0 秒)
V1 = 8.0 - (V_ON - V_OFF)                       # 7.5: 声 (1 回目): 2 小節 (8 秒) から話し始める
K0 = float(os.environ.get('K0', '9.0'))         # 鍵盤: 録音の f 秒は曲の f + 9.0 秒。最初の音は 14.0 秒 (声の息継ぎのどこにも鍵盤の音が鳴る位置)
V2 = K0 + 304.4 - (V_ON - V_OFF)                # 312.9: 声 (2 回目): 鍵盤が止まった所 (録音の 304.4 秒 = 曲の 5 分 13 秒) で話し始める。白い鍵盤は 306.0 秒から
S2, S3, S4, TOTAL = 50, 78, 126, 142
def play(rid, beat, gain, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
PLAYS = [play(RV, V1, GV1, V_OFF, V_LEN - V_OFF, 0, COLV, '11/08 14:55 の calma の声 — 実音 (2 小節から)', fin=0.3, fout=2.0),
         play(RK, K0, GK, 0.0, K_LEN, 1, COLK, '11/20 02:40 の鍵盤の録音 — 実音、初めから終わりまで', fin=0.5, fout=0.3),
         play(RV, V2, GV2, V_OFF, V_LEN - V_OFF, 0, COLV, '11/08 14:55 の calma の声 — 実音 (もう一度)', fin=0.3, fout=2.0)]
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍)
LEAD = [(1, K0)]
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
    P.section(0, 'I. calma の声と鍵盤 — 実音 (♩=60)', '2 小節から声、その 6 秒後から鍵盤 — 録音のままの、小さな音がぽつぽつと。声は 3 分 19 秒まで')
    P.section(S2, 'II. 鍵盤だけ — 前半の山へ', '鍵盤が少しずつ大きくなり、山を築いて、止まる (5 分 13 秒)')
    P.section(S3, 'III. calma の声をもう一度', '鍵盤が止まった所で声が先に入り、2 秒後から白い鍵盤 (ハ長調 / イ短調)。声は 8 分 24 秒まで')
    P.section(S4, 'IV. 鍵盤だけ — いちばん大きい所から終わりへ', '鍵盤は 9 分 25 秒に終わる')
    return P

def post(P, events, ex):
    for p in PLAYS:         # どちらも録音のまま: 帯域を削らず、全体の残響も左右の遅れも足さない (synth.py の faithful の経路)
        rid, off, dur = p['rid'], p['off'], p['dur']; c = CH.get(rid, {})
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05), env_off=off)
        add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXVII · L\'aureola e la tastiera vera',
        'subtitle': 'calma の声と 11/20 の鍵盤の曲を、どちらも実音で重ねて。変ニ長調 → ハ長調、♩=60',
        'footer': ['声 = 届いた calma の声、曲 = 11/20 02:40 の鍵盤の録音。どちらも録音のまま (強弱も響きも帯域も変えない)。楽器は何も加えない。',
                   '鍵盤は小さな音で始まり、9 分かけて大きくなる。前半は黒い鍵盤 (変ニ長調)、後半は白い鍵盤 (ハ長調)。2 回目の声は鍵盤に合わせて少し大きく。',
                   '声が先に立ち、曲はその後から。声と声の間と、終わりは、鍵盤だけ。142 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=277, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
