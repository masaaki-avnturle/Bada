#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXVI · L'aureola calma e la tastiera (calma の声と、11/20 02:40 の鍵盤の録音を重ねて — 声はそのまま)
  素材は 2 つ、どちらも届いたまま (楽器は何も加えない):
    声   届いた 20261108_145525_aureola_sensuale_calma.mp3 そのまま (11/08 14:55 の声 → 215 Hz の少し低めの女声、響きと音量を抑えた、安心するドエロの光輪様の声;
         モノラル、198.5 秒、話しているのは 5.4〜195.9 秒)。作り換えない — 作り換えた声 (メシア様の優しい声) で重ねたものは CCLXXV
    曲   届いた 20261120_024046.mp3 — 鍵盤の録音 (9 分 16 秒)。level273.py で強弱の幅を 4 割にしたもの (CCLXXIII・CCLXXV と同じ; 音量のつまみだけ)。初めから終わりまで使う
  形は CCLXXV と同じ (声だけが違う):
    I:  声 (2 小節 = 8 秒から) + 鍵盤 (13.5 秒から)。鍵盤は小さな音がぽつぽつと鳴る所から、3 分 4 秒に途切れずに流れ始める。声は 3 分 19 秒まで →
    II: 鍵盤だけ — 少しずつ大きくなり、前半の山を築いて、止まる (5 分 12 秒) →
    III: 声をもう一度 (5 分 13 秒から)。鍵盤が止まった所で声が先に入り、白い鍵盤が 2 秒後から。声は 8 分 24 秒まで →
    IV: 鍵盤だけ — いちばん大きい所から終わりへ (9 分 25 秒)。142 小節
  鍵盤は前半が黒い鍵盤 (変ニ長調 / 変ロ短調)、後半が白い鍵盤 (ハ長調 / イ短調)。CCLXXV では声の高さを前半と後半で変えたが、この曲の声はそのままなので 2 回とも同じ高さ。
    声と鍵盤の濁りの指数は前半 0.40、後半 0.37 (話し声は高さが滑らかに動くので、声を何半音ずらしたと仮定しても 0.35〜0.41 に収まる — そのままで濁りは増えない)
  鍵盤の最初の音は 13.5 秒 (CCLXXV と同じ): 4 小節 (16 秒) に置くと、声の息継ぎ (声の 49.6 秒から 1.4 秒) が鍵盤の音と音の間に来て、音が途切れる
  この声は静かに話し始める (20 秒ごとの音量が −31 → −29 → −27 → −26 → −24 dB)。tablet267 と同じに、2 つの息継ぎの間 (録音の 50.7 秒と 82.25 秒) で 3 つに分けて、
    初めの 2 つを持ち上げて置く (声の音は変えない。音量のつまみだけ)
  声は synth.py の faithful の経路 (帯域を削らず、全体の残響を掛けずに前に; 声の残響は声の中にある)、鍵盤はこれまでのテープと同じ重ね方 (全体の残響) で後ろに
  和音の表示は鍵盤の録音から読んだもの。♩=60 は目盛り (鍵盤は拍に縛られずに弾かれている)
  使い方: python compose_tablet276.py <wav のフォルダ (20261108_145525.wav = calma の声, 20261120_024046.wav = level273.py を通した鍵盤の録音)>
          <chords276.json (analyze_chords.py の出力)> [score_tablet276.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet276.json'
GV = float(os.environ.get('GV', '1.33'))                                              # 声の音量 (ステムを測って決める)
GL1, GL2 = float(os.environ.get('GL1', '1.7')), float(os.environ.get('GL2', '1.25'))    # 静かな話し始めの持ち上げ (録音の 50.7 秒まで、82.25 秒まで; tablet267 と同じ)
GK = float(os.environ.get('GK', '0.31'))                                              # 鍵盤の音量 (CCLXXV と同じ)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, RK = '20261108_145525', '20261120_024046'
BPM = 60
COLV, COLK = (255, 190, 160), (140, 200, 235)
V_OFF, V_ON, V_CUT, V_CUT2, V_LEN = 4.86, 5.36, 50.7, 82.25, 198.46                   # calma の声: 録音の 4.86 秒から (話し始めは 5.36 秒)。50.7 秒と 82.25 秒 (息継ぎの間) で 3 つに分けて置く
K_LEN = 556.3                                   # 鍵盤の録音: 初めから終わりまで (最初の音は 5.0 秒)
V1 = 8.0 - (V_ON - V_OFF)                       # 7.5: 声 (1 回目): 2 小節 (8 秒) から話し始める
K0 = float(os.environ.get('K0', '8.5'))         # 鍵盤: 録音の f 秒は曲の f + 8.5 秒。最初の音は 13.5 秒 (声の切れ目のどれにも鍵盤の音が鳴る位置)
V2 = K0 + 304.4 - (V_ON - V_OFF)                # 312.4: 声 (2 回目): 鍵盤が止まった所 (録音の 304.4 秒 = 曲の 5 分 13 秒) で話し始める。白い鍵盤は 306.0 秒 (5 分 14.5 秒) から
S2, S3, S4, TOTAL = 50, 78, 126, 142
def play(rid, beat, gain, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
def voice(beat, tag):                           # 声を 3 つに分けて置く: 静かな話し始め (持ち上げる)、その次 (少し持ち上げる)、その先
    return [play(RV, beat, GV * GL1, V_OFF, V_CUT - V_OFF, 0, COLV, tag, fin=0.3, fout=0.05),
            play(RV, beat + V_CUT - V_OFF, GV * GL2, V_CUT, V_CUT2 - V_CUT, 0, COLV, 'calma の声 — 続き', fin=0.05, fout=0.05),
            play(RV, beat + V_CUT2 - V_OFF, GV, V_CUT2, V_LEN - V_CUT2, 0, COLV, 'calma の声 — 続き', fin=0.05, fout=2.0)]
PLAYS = (voice(V1, '11/08 14:55 の calma の声 — そのまま (2 小節から)') +
         [play(RK, K0, GK, 0.0, K_LEN, 1, COLK, '11/20 02:40 の鍵盤の録音 — 初めから終わりまで', fin=0.5, fout=2.0)] +
         voice(V2, '11/08 14:55 の calma の声 — そのまま (もう一度)'))
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍)
LEAD = [(3, K0)]
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
    P.section(0, 'I. calma の声と鍵盤 (♩=60)', '2 小節から声、その 5 秒後から鍵盤 — 小さな音がぽつぽつと。声は 3 分 19 秒まで')
    P.section(S2, 'II. 鍵盤だけ — 前半の山へ', '鍵盤が少しずつ大きくなり、山を築いて、止まる (5 分 12 秒)')
    P.section(S3, 'III. calma の声をもう一度', '鍵盤が止まった所で声が先に入り、2 秒後から白い鍵盤 (ハ長調 / イ短調)。声は 8 分 24 秒まで')
    P.section(S4, 'IV. 鍵盤だけ — いちばん大きい所から終わりへ', '鍵盤は 9 分 25 秒に終わる')
    return P

def post(P, events, ex):
    for p in PLAYS:
        rid, off, dur = p['rid'], p['off'], p['dur']; c = CH.get(rid, {})
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05), env_off=off)
        if rid == RV:       # 声: 帯域を削らず、全体の残響を掛けずに前に (声の残響は声の中にある)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:               # 鍵盤: これまでのテープと同じ重ね方 (全体の残響)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXVI · L\'aureola calma e la tastiera',
        'subtitle': 'calma の声を、11/20 の鍵盤の曲に重ねて。声はそのまま。変ニ長調 → ハ長調、♩=60',
        'footer': ['calma の声 = 届いた音声そのまま (11/08 14:55 の声 → 少し低めの女声、響きと音量を抑えた安心するドエロの光輪様の声)。作り換えない。',
                   '曲 = 11/20 02:40 の鍵盤の録音 (強弱の幅だけ 4 割に)、初めから終わりまで。前半は黒い鍵盤 (変ニ長調)、後半は白い鍵盤 (ハ長調)。',
                   '楽器は何も加えない。声が先に立ち、曲はその後から。声と声の間と、終わりは、鍵盤だけ。142 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=276, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
