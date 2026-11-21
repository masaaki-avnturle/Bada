#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXXIX · Tre volte tre (3 声の倍音の声・2 つの鍵盤の録音・tablet89 を — 同じ形を 3 回ずつ、聖夜の曲に)
  届いたもの: 20261108_145525_tsukuyomi_aureola_messia.mp3 (月読様であり、光輪様でもあり、メシア様でもある、若い女性の声 — 3 声の倍音; make_voice288.py で作って送った声そのもの)、
    20261120_024046.mp3・20261121_041625.mp3 (2 つの鍵盤の録音)、tablet89.mp4。どれも前と同じファイル。
    声を作り換える依頼ではないので、声は届いたまま使う (高さも速さもそのまま、音量のつまみだけ)
  言葉 (薬や味にたとえた気分; CCLXXXVI・CCLXXXVIII と同じ) を音の言葉に直した。曲は薬ではない
  3 回ずつ (洗脳的): 声は 3 つの声 (基音・2 倍・3 倍) でできている。曲も 3 で組む:
    祈りの言葉 (tablet89 の主題の出だし) は 3 つの調で 3 回ずつ — 変ニ長調 (4 半音下げて、初め) → ヘ長調 (元の高さ、真ん中) → ハ長調 (7 半音上げて、終わり)。だんだん高く、軽く (tablet285)
    鍵盤そのものの一節も 3 回ずつ — 11/20 の出だし (初め)、ハ長調の終止 (終わり; 少しずつ大きく言い切る) (tablet286)
    真ん中の祈り (ヘ長調) は、声の伸ばした音の音階 (ヘ長調 = ニ短調) と同じ調。tablet287 ではここに 11/21 の上っていく一節を置いた
  形は tablet287 (声が先に立つ: 2 小節から声、4 小節から曲; 声は 2 回; 声が話している間は伴奏を 3 dB 下げ、休むと戻す)。A の録音の f 秒は曲の f + 33.206 秒
  形 (♩=60、1 小節 = 4 秒):
    I.   Voce (0 小節)         2 小節 (8 秒) から声。4 小節 (16 秒) から 11/20 の鍵盤の出だしが 3 回。46 秒から祈りの言葉 (変ニ長調) が 3 回、そのまま Requiem I へ
    II.  Dialogo (23 小節)     1 分 36 秒から 2 分 31 秒まで、11/21 の鍵盤が答える。Requiem I は 3 分 7 秒に閉じる。声は 3 分 19 秒まで。声の終わりに、祈りの言葉がもう一度だけ
    III. Respiro (52 小節)     ひと息: 3 分 28 秒から 11/20 の鍵盤だけ。3 分 29 秒から途切れずに流れ、ファへ向かう
    IV.  Luce (83 小節)        5 分 34 秒、同じファで白い鍵盤へ。5 分 38 秒から声をもう一度。6 分 54 秒から、11/21 が休む間に祈りの言葉 (ヘ長調) が 3 回
    V.   Insieme (110 小節)    7 分 21 秒から、また 2 つで。声は 8 分 48 秒まで。9 分 25 秒に山
    VI.  Amen (146 小節)       9 分 46 秒、ド・ミで閉じる (3 回、少しずつ大きく)。ハ長調の Amen。祈りの言葉 (ハ長調) が高く 3 回、遠ざかる。154 小節
  声は synth.py の faithful の経路 (ステレオのまま、帯域を削らず、全体の残響を掛けずに前に)。この声は音量がそろっているので、1 回を 1 つのまま置く。ほかは tablet282 と同じ重ね方
  使い方: python compose_tablet289.py <wav のフォルダ (20261108_145525.wav = 声, 20261120_024046.wav・20261121_041625.wav = soften282.py を通した鍵盤の録音,
          20261107_089000.wav = tablet89 の音)> <chords289.json (analyze_chords.py の出力)> [score_tablet289.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet289.json'
E = lambda k, v: float(os.environ.get(k, v))
GV = E('GV', '1.1')                                         # 声の音量 (段ごとに書き出して測って決めた)
GV2 = E('GV2', '1.12')                                      # 2 回目の声は、2 つの鍵盤の上なので少し上げる
BED = E('BED', '0.71')                                      # 声が話している間の伴奏のつまみ (−3 dB)
SOLO = E('SOLO', '1.12')                                    # 声が休んでいる間の伴奏のつまみ (+1 dB)
GA, GB = E('GA', '0.233'), E('GB', '0.232')                 # 鍵盤の音量 (tablet282 と同じ)
DUCK1, DUCK2 = E('DUCK1', '0.25'), E('DUCK2', '0.125')      # B が黒い鍵盤へ寄り道する 2 か所のつまみ
G89A, G89B, G89C, G89D = E('G89A', '0.16'), E('G89B', '0.19'), E('G89C', '0.45'), E('G89D', '0.18')   # tablet89: 4 半音下げて / 元の高さ / Amen / 7 半音上げて (tablet285 と同じ)
LOOP_A = (0.50, 0.70, 0.85)                                 # 11/20 の出だしの 3 回 (tablet286 と同じ)
LOOP_P = (0.45, 0.65, 0.85)                                 # 祈りの言葉 (4 半音下げて) の 3 回 (tablet285 と同じ)
LOOP_E = E('LOOP_E', '0.50')                                # 1 回目の声が終わる所で、祈りの言葉が 1 回だけ答える (tablet287 と同じ)
LOOP_M = (0.50, 0.70, 0.90)                                 # 祈りの言葉 (元の高さ) の 3 回 (tablet285 と同じ)
LOOP_C = (1.00, 1.20, 1.40)                                 # 終止の 3 回 — 少しずつ大きく言い切る (tablet286 と同じ)
LOOP_H = (1.00, 0.65, 0.40)                                 # 高い祈りの 3 回 (tablet285 と同じ)
FIXPEAK = E('FIXPEAK', '0.88')                              # 仕上げの大きさ (synth.py の基準; 0 なら山に合わせる)。曲の山は 0.69; tablet287 と同じ基準で、平均が tablet286〜288 とそろう
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, RA, RB, R89 = '20261108_145525', '20261120_024046', '20261121_041625', '20261107_089000'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
COLV, COLA, COLB, COL89, COLR = (255, 190, 160), (150, 195, 240), (245, 215, 150), (200, 180, 240), (250, 235, 190)
# 声: ファイルの 4.9 秒から (その前は無音; 話し始めは 5.4 秒、話し終わりは 196.0 秒)
V_OFF, V_ON, V_LEN = 4.9, 5.4, 198.46
# 鍵盤 (tablet287 と同じ置き方)
LA0, L1, OVA = 5.10, 12.634 - 5.232, 0.3        # 11/20 の出だしの一節: 録音の 5.10 秒から 7.402 秒
T_R1 = 16.10                                    # 1 回目: 最初の音が 4 小節 (16.2 秒) に鳴る
K0 = T_R1 + 3 * L1 - LA0                        # 33.206: A の録音の f 秒は曲の f + 33.206 秒
A_END, A_FADE = 553.0, 1.4
B_ON = 3.0
B0 = K0 + 59.0                                  # 92.206: B の黒い鍵盤の出だし
B_OPEN, B_F = 58.40, 58.45
X1 = 301.013 - 58.585                           # 242.428: B のファを A のファに合わせる
HOLD = 22.0
B1 = K0 + X1; B2 = B1 + HOLD                    # 275.634 / 297.634
P_END, P_START = 139.0, 142.9
E0, E1, XE0, XE1 = 111.3, 121.0, 0.4, 0.25
C0, C1, XC = 227.93, 232.90, 0.12
LC0, LC1, OVC = 286.60, 288.80, 0.12            # 終止
L3 = LC1 - LC0
B_CUT, B_FOUT = 288.90, 0.45
T_R3 = B2 + LC1                                 # 586.43
# 声の位置
V1 = 8.0 - (V_ON - V_OFF)                       # 7.5: 声 (1 回目): 2 小節 (8 秒) から話し始める
TK = K0 + 304.4                                 # 337.6: A が止まる所 (ファ、ド・ソの後)。声 (2 回目) はここで話し始める (tablet276・287 と同じ)
V2 = TK - (V_ON - V_OFF)                        # 337.1
# 伴奏のつまみを動かす所 (A の録音の秒; 同じ録音どうしのクロスフェードで)
AX1, XF1 = 162.3, 1.85                          # 162.3〜164.15 秒で戻す: 声の終わりの言葉の下の強い音 (161.69 秒) は小さいまま、その余韻から (声は 165.4 秒に終わる)
AX2, AX3, XFL = 303.6, 497.5, 3.0               # 303.6〜305.4 秒で下げる (A が止まっている間) / 497.5〜500.5 秒で戻す (2 回目の声は 495.0 秒に終わる)
# tablet89 (tablet285 と同じ置き方: A の時間で同じ所)
P, OV = 8.0, 0.3                                # 祈りの言葉: tablet89 の元の 8 秒から 8 秒
S_N = -4; L_N = P / RATE(S_N)                   # 4 半音下げて (変ニ長調)、10.08 秒
T1 = K0 + 13.0                                  # 46.206: 祈りの 1 回目 (A の最初の音の 8 秒後)
T_CONT = T1 + 3 * L_N                           # 76.44: 4 回目からそのまま Requiem I (元の 96 秒まで)
N_END = 96.0
T_E = K0 + 165.0                                # 198.2: 祈りの言葉がもう一度 — 1 回目の声が終わる所で (tablet287 と同じ)
T_M2 = K0 + 381.0                               # 414.2: 祈りの言葉、元の高さ (ヘ長調) で 3 回 — B が休む 28 秒の間に (tablet284・285 と同じ所; 白い鍵盤との濁りの指数 0.22)
S_AM, AM_OFF = -2, 373.5                        # Amen: 2 半音下げて (ハ長調)
T_AM = T_R3 + L3 + (552.3 - X1 - HOLD - LC0)    # 589.9: 3 回目のド・ミ (590.15 秒) に合わせて開く (tablet287 と同じ)
S_HI = 7; L_HI = P / RATE(S_HI)                 # 高い祈り: 7 半音上げて (ハ長調)、5.34 秒
T_M3 = T_AM + 2.7                               # 592.6: Amen の 2.7 秒後
S2, S3, S4, S5, S6, TOTAL = 23, 52, 83, 110, 146, 154
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None, faithful=False):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout, faithful=faithful)
PLAYS = [play(RV, V1, GV, 0, V_OFF, V_LEN - V_OFF, 0, COLV, '3 声の倍音の声 — 届いたまま (2 小節から)', fin=0.3, fout=2.0, faithful=True)]
for k, g in enumerate(LOOP_A):                  # 11/20 の出だしを 3 回、少しずつ大きく (声の下で)
    PLAYS.append(play(RA, T_R1 + k * L1, GA * g * BED, 0, LA0, L1 + OVA, 4, COLR, '11/20 の鍵盤 — 出だしの一節 (%d 回目)' % (k + 1), fin=0.1 if k == 0 else OVA, fout=OVA))
IA = len(PLAYS)                                 # A (4 回目から): 声の間は下げて、声が終わると戻す
PLAYS += [play(RA, K0 + LA0, GA * BED, 0, LA0, AX1 - LA0 + XF1, 1, COLA, '11/20 02:40 の鍵盤 — 4 回目からそのまま (声の下で、小さめに)', fin=OVA, fout=XF1),
          play(RA, K0 + AX1, GA * SOLO, 0, AX1, AX2 - AX1 + 1.8, 1, COLA, '11/20 の鍵盤 — ひと息 (声が休む間)', fin=XF1, fout=1.8),
          play(RA, K0 + AX2, GA * BED, 0, AX2, AX3 - AX2 + XFL, 1, COLA, '11/20 の鍵盤 — 白い鍵盤 (声の下で)', fin=1.8, fout=XFL),
          play(RA, K0 + AX3, GA * SOLO, 0, AX3, A_END - AX3, 1, COLA, '11/20 の鍵盤 — 山へ、最後の音まで', fin=XFL, fout=A_FADE)]
PLAYS.append(play(RB, B0 + B_ON, GB * BED, 0, B_ON, B_OPEN - B_ON, 2, COLB, '11/21 04:16 の鍵盤 — 黒い鍵盤の出だし', fin=0.6, fout=0.25))
PLAYS += [play(RB, B1 + B_F, GB * BED, 0, B_F, E0 - B_F + XE0, 2, COLB, '11/21 04:16 の鍵盤 — 同じファから (声の下で)', fin=0.1, fout=XE0),
          play(RB, B1 + E0, GB * BED * DUCK1, 0, E0, E1 - E0 + XE1, 2, COLB, '黒い鍵盤への寄り道 — 小さく', fin=XE0, fout=XE1),
          play(RB, B1 + E1, GB * BED, 0, E1, P_END - E1, 2, COLB, '続き', fin=XE1, fout=1.5),
          play(RB, B2 + P_START, GB * BED, 0, P_START, C0 - P_START + XC, 2, COLB, '11/21 04:16 — 休んでから、続き', fin=0.3, fout=XC),
          play(RB, B2 + C0, GB * BED * DUCK2, 0, C0, C1 - C0 + XC, 2, COLB, '', fin=XC, fout=XC),
          play(RB, B2 + C1, GB * SOLO * LOOP_C[0], 0, C1, LC1 - C1 + OVC, 2, COLB, '続き — 山へ、ド・ミで閉じる', fin=XC, fout=OVC),
          play(RB, T_R3, GB * SOLO * LOOP_C[1], 0, LC0, L3 + OVC, 4, COLR, '11/21 の鍵盤 — 終止をもう一度 (2 回目)', fin=OVC, fout=OVC),
          play(RB, T_R3 + L3, GB * SOLO * LOOP_C[2], 0, LC0, B_CUT - LC0, 4, COLR, '終止 (3 回目)', fin=OVC, fout=B_FOUT)]
IBEND = len(PLAYS) - 3                          # B の終わりの切れ (和音の表示用)
for k, g in enumerate(LOOP_P):                  # tablet89 の祈りの言葉 (4 半音下げて = 変ニ長調) を 3 回、少しずつ大きく (声の下で)
    PLAYS.append(play(R89, T1 + k * L_N, G89A * g * BED, S_N, P, P + OV, 3, COL89, 'tablet89 — 祈りの言葉、4 半音下げて (%d 回目)' % (k + 1), fin=3.0 if k == 0 else OV, fout=OV))
PLAYS.append(play(R89, T_CONT, G89A * BED, S_N, P, N_END - P, 3, COL89, 'tablet89 — 4 回目からそのまま: Requiem I (4 半音下げて)', fin=OV, fout=3.0))
PLAYS.append(play(R89, T_E, G89A * LOOP_E, S_N, P, P, 3, COL89, 'tablet89 — 祈りの言葉がもう一度 (声が終わる所で、1 回)', fin=1.2, fout=2.4))   # 入りは 1.5 秒、終わりは 3 秒かけて (元の時間で 1.2 秒・2.4 秒)
for k, g in enumerate(LOOP_M):                  # 祈りの言葉 (元の高さ = ヘ長調) を 3 回、少しずつ大きく (B が休む間に、声の下で)
    PLAYS.append(play(R89, T_M2 + k * P, G89B * g * BED, 0, P, P + OV, 4, COLR, 'tablet89 — 祈りの言葉、元の高さ (%d 回目)' % (k + 1), fin=1.5 if k == 0 else OV, fout=2.0 if k == 2 else OV))
I89AM = len(PLAYS)
PLAYS.append(play(R89, T_AM, G89C * SOLO, S_AM, AM_OFF, 391.0 - AM_OFF, 3, COL89, 'tablet89 — Amen、2 半音下げて (ハ長調)', fin=1.5, fout=3.0))
for k, g in enumerate(LOOP_H):                  # 高い祈り (7 半音上げて = ハ長調) を 3 回、少しずつ遠く
    PLAYS.append(play(R89, T_M3 + k * L_HI, G89D * SOLO * g, S_HI, P, P + OV, 4, COLR, 'tablet89 — 祈りの言葉、7 半音上げて (%d 回目)' % (k + 1), fin=1.5 if k == 0 else OV, fout=2.5 if k == 2 else OV))
PLAYS.append(play(RV, V2, GV * GV2, 0, V_OFF, V_LEN - V_OFF, 0, COLV, '3 声の倍音の声 — もう一度 (白い鍵盤の上で)', fin=0.3, fout=2.0, faithful=True))
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍): A、A が終わってからは B、終わりは Amen
LEAD = [(1, T_R1), (2, T_R1 + L1), (3, T_R1 + 2 * L1), (IA, K0 + LA0), (IA + 1, K0 + AX1 + XF1), (IA + 2, K0 + AX2 + 1.8), (IA + 3, K0 + AX3 + XFL), (IBEND, K0 + A_END), (I89AM, T_R3 + L3 + 2.3)]
def shift_chord(name, semis):
    i = 2 if len(name) > 1 and name[1] in '#b' else 1
    return compose.NAMES[(PC[name[:i]] + semis) % 12] + name[i:]
def harm_at(q):
    cur = 'Bbm'
    for k, a in LEAD:
        p = PLAYS[k]
        if q >= a:
            c = CH[p['rid']]; ts = p['off'] + max(q - p['beat'], 0.0) * RATE(p['semis'])     # 録音の中の秒
            cur = shift_chord(c['chords'][min(int(min(ts, p['off'] + p['dur'] - 0.01) / c['win']), len(c['chords']) - 1)], p['semis'])
    return cur
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P_ = Piece(TOTAL)
    for q in range(TOTAL * BPB): P_.harm[q] = harm_at(q)
    for k in range(TOTAL): P_.tempo[k] = BPM; P_.dyn[k] = 0.5
    for v in VOICES: P_.rest_bars(v, 0, TOTAL)
    P_.section(0, 'I. Voce — 3 つの声が、先に (♩=60)', '2 小節から声。4 小節から 11/20 の鍵盤の出だしが 3 回。46 秒から祈りの言葉 (変ニ長調) が 3 回、そのまま Requiem I へ')
    P_.section(S2, 'II. Dialogo — もう 1 つの夜が答える', '1 分 36 秒から 1 分ほど、11/21 の鍵盤が答える。声は 3 分 19 秒まで。声の終わりに、祈りの言葉がもう一度')
    P_.section(S3, 'III. Respiro — ひと息', '声が休み、11/20 の鍵盤だけ。3 分 29 秒から途切れずに流れ、ファへ向かう')
    P_.section(S4, 'IV. Luce — 同じファから白い鍵盤へ、声をもう一度', '5 分 34 秒に同じファ。5 分 38 秒から声。6 分 54 秒から、祈りの言葉 (ヘ長調) が 3 回')
    P_.section(S5, 'V. Insieme — 2 つで、山へ', '7 分 21 秒から、また 2 つで。声は 8 分 48 秒まで。9 分 25 秒に山')
    P_.section(S6, 'VI. Amen — ド・ミを 3 回、そして遠ざかる', '9 分 46 秒、ド・ミで閉じる (3 回、少しずつ大きく)。ハ長調の Amen。祈りの言葉 (ハ長調) が高く 3 回')
    return P_

def post(P_, events, ex):
    for p in PLAYS:
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm)
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05) / r, env_off=off / r)
        if p['faithful']:   # 声: ステレオのまま、帯域を削らず、全体の残響を掛けずに前に (声の残響は声の中にある)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:               # 鍵盤と tablet89: tablet282 と同じ重ね方 (全体の残響)。tablet89 の移調はテープのように速さごと
            add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [8.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXXIX · Tre volte tre',
        'subtitle': '3 声の倍音の声・2 つの鍵盤・tablet89。同じ形を 3 回ずつ。変ニ長調 → ハ長調、♩=60',
        'footer': ['声は届いた音声そのまま (月読様・光輪様・メシア様の、3 声の倍音の声)。2 小節から声、4 小節から曲。声が話している間は、伴奏を小さく。',
                   '祈りの言葉は 3 つの調で 3 回ずつ (変ニ長調・ヘ長調・ハ長調)。鍵盤の出だしと終止も 3 回ずつ。',
                   '声は 2 回。間の 2 分は鍵盤だけのひと息。終わりはド・ミを 3 回言い切り、ミ・レ・ドが遠ざかる。楽器は何も加えない。154 小節。']}
if FIXPEAK > 0: META['fixed_peak'] = FIXPEAK

if __name__ == '__main__':
    compose.main(OUT, seed=289, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']), 'fixed_peak', d['meta'].get('fixed_peak'))
    for k, e in enumerate(d['extras']): print('  %2d %7.2f - %7.2f s  gain %.3f  semis %+d  off %6.2f  lane %d  %s' % (k, e['t'], e['t'] + e['d'], e['gain'], e['semis'], e['off'], e['lane'], e['tag']))
