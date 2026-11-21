#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXXVII · Il dolce consiglio (tablet285 と tablet286 を、tablet233 の優しい声で、諭すようにミックス)
  届いたもの: tablet286.mp4・tablet285.mp4 (こちらで作ったものと同じ) と 20261108_145525_aureola_sensuale_calma.mp3。
    tablet233 (CCXXXIII) の声は「安心するドエロの光輪様の声」(11/08 14:55 の声 → 少し低めの女声、響きと音量を抑えたもの) で、届いた calma の声がその声そのもの。
    だから声は作り換えず、届いたまま使う (音量のつまみだけ)
  言葉 (薬や煙草にたとえた気分) を音の言葉に直した。曲は薬ではない:
    優しい音声で、諭すように        → 声が先に立つ: 2 小節 (8 秒) から声、4 小節 (16 秒) から曲 (いつもの入り方)。声が話している間は、伴奏を 3 dB 下げる (声が休むと 1 dB 上げる)。
                                        声は 2 回。1 回目は夜の小さな音の上で、2 回目は白い鍵盤の上で (同じ言葉を、明るい所でもう一度)
    ホッと一安心、全身の力が抜ける  → tablet282 と同じやわらかい打鍵、小さな音量。同じ形を 3 回ずつ
    急に上がらず、急に落ちない      → 声のある所と無い所の大きさの差を小さく。声の間は伴奏が下がり、声が終わると戻る — つまみは 2〜3 秒かけて動かす
    一服するように (ひと息つく)     → 1 回目の声が終わる所で、祈りの言葉 (ミ・レ・ド) が 1 回だけ答える。その先の 2 分は、鍵盤だけ (ひと息)。終わりは、ミ・レ・ドが高く 3 回、遠ざかる
  ミックス: tablet285 と tablet286 は、同じ 2 つの鍵盤の録音を同じ置き方で使っている。そのまま重ねると鍵盤が 2 つ重なるので、鍵盤は 1 回だけ鳴らし、
    それぞれの曲だけにある段を重ねる:
    tablet286 から  3 回ずつのくり返し — 11/20 の出だし (初め)、11/21 の上っていく一節 (真ん中)、ハ長調の終止 (終わり)
    tablet285 から  tablet89 の段 — 祈りの言葉 (4 半音下げて 3 回) とそのまま続く Requiem I、終わりの Amen (2 半音下げて) と高い祈り (7 半音上げて 3 回)
    tablet285 の真ん中の祈り (元の高さで 3 回) は、そのままは入れない: 同じ所に tablet286 の上っていく一節があり、声も話しているので、重ねると言葉が聞き取りにくい。
    代わりに、1 回目の声が終わる所 (3 分 18 秒) へ移して、4 半音下げて 1 回だけ。鍵盤が自分で休む 2 秒を埋め、着く音 (変ニ) が鍵盤の変ニに重なる
    終わりの終止の 3 回は、tablet286 では少しずつ大きくしたが、ここでは同じ大きさに (優しく)。Amen は 3 回目のド・ミに合わせて開く (終止の 3 回は鍵盤だけで、濁らせない)。
    高い祈りは、その 2.7 秒後から (tablet285 と同じ間合い)
  置く位置は tablet286 の時間を 8 秒後ろへ (声が 2 小節、曲が 4 小節から)。A の録音の f 秒は曲の f + 33.206 秒
  形 (♩=60、1 小節 = 4 秒):
    I.   Voce (0 小節)         2 小節 (8 秒) から声。4 小節 (16 秒) から 11/20 の鍵盤の出だしが 3 回。46 秒から祈りの言葉が 3 回、そのまま Requiem I へ
    II.  Dialogo (23 小節)     1 分 36 秒から 2 分 31 秒まで、11/21 の鍵盤が答える。Requiem I は 3 分 7 秒に閉じる。声は 3 分 19 秒まで。声の終わりに、祈りの言葉がもう一度
    III. Respiro (52 小節)     ひと息: 3 分 28 秒から 11/20 の鍵盤だけ。3 分 29 秒から途切れずに流れ、ファへ向かう
    IV.  Luce (83 小節)        5 分 34 秒、同じファで白い鍵盤へ。5 分 38 秒から声をもう一度。6 分 53 秒から 11/21 が休み、上っていく一節が 3 回 (7 分 0 秒から)
    V.   Insieme (110 小節)    7 分 21 秒から、また 2 つで。声は 8 分 48 秒まで。9 分 25 秒に山
    VI.  Amen (146 小節)       9 分 46 秒、ド・ミで閉じる (3 回)。ハ長調の Amen。ミ・レ・ドが高く 3 回、遠ざかる。154 小節
  声は synth.py の faithful の経路 (帯域を削らず、全体の残響を掛けずに前に)。静かな話し始めは tablet276 と同じに 3 つに分けて持ち上げる。ほかは tablet282 と同じ重ね方
  使い方: python compose_tablet287.py <wav のフォルダ (20261108_145525.wav = calma の声, 20261120_024046.wav・20261121_041625.wav = soften282.py を通した鍵盤の録音,
          20261107_089000.wav = tablet89 の音)> <chords287.json (analyze_chords.py の出力)> [score_tablet287.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet287.json'
E = lambda k, v: float(os.environ.get(k, v))
GV = E('GV', '0.95')                                        # 声の音量 (段ごとに書き出して測って決めた; 優しく、言葉は聞き取れる大きさ)
GV2 = E('GV2', '1.15')                                      # 2 回目の声は、2 つの鍵盤の上なので少し上げる
GL1, GL2 = E('GL1', '1.7'), E('GL2', '1.25')                # 静かな話し始めの持ち上げ (録音の 50.7 秒まで、82.25 秒まで; tablet276 と同じ)
BED = E('BED', '0.71')                                      # 声が話している間の伴奏のつまみ (−3 dB)
SOLO = E('SOLO', '1.12')                                    # 声が休んでいる間の伴奏のつまみ (+1 dB) — 声のある所と無い所の大きさの差を小さく
GA, GB = E('GA', '0.233'), E('GB', '0.232')                 # 鍵盤の音量 (tablet282 と同じ)
DUCK1, DUCK2 = E('DUCK1', '0.25'), E('DUCK2', '0.125')      # B が黒い鍵盤へ寄り道する 2 か所のつまみ
G89A, G89C, G89D = E('G89A', '0.16'), E('G89C', '0.45'), E('G89D', '0.18')   # tablet89: 4 半音下げて / Amen / 7 半音上げて (tablet285 と同じ)
LOOP_A = (0.50, 0.70, 0.85)                                 # 11/20 の出だしの 3 回 (tablet286 と同じ)
LOOP_P = (0.45, 0.65, 0.85)                                 # 祈りの言葉 (4 半音下げて) の 3 回 (tablet285 と同じ)
LOOP_E = E('LOOP_E', '0.50')                                # 1 回目の声が終わる所で、祈りの言葉が 1 回だけ答える (4 半音下げて)
LOOP_B = (0.60, 0.80, 1.00)                                 # 上っていく一節の 3 回 (tablet286 と同じ)
LOOP_C = (1.00, 1.00, 1.00)                                 # 終止の 3 回 — 同じ大きさで (tablet286 は 1.0・1.2・1.4)
LOOP_H = (1.00, 0.65, 0.40)                                 # 高い祈りの 3 回 (tablet285 と同じ)
FIXPEAK = E('FIXPEAK', '0.88')                              # 仕上げの大きさ (synth.py の基準; 0 なら山に合わせる)。曲の山 (声の波形の山) は 0.78 — それより 1 dB 小さく仕上げる
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
# 声 (calma): 録音の 4.86 秒から (話し始めは 5.36 秒、話し終わりは 195.9 秒)。50.7 秒と 82.25 秒 (息継ぎの間) で 3 つに分けて置く
V_OFF, V_ON, V_CUT, V_CUT2, V_LEN = 4.86, 5.36, 50.7, 82.25, 198.46
# 鍵盤 (tablet286 と同じ置き方を、8 秒後ろへ)
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
LB0, L2, OVB = 58.45, 7.15, 0.1                 # 上っていく一節
T_R2 = K0 + 386.75 - (58.585 - LB0)             # 419.82
LC0, LC1, OVC = 286.60, 288.80, 0.12            # 終止
L3 = LC1 - LC0
B_CUT, B_FOUT = 288.90, 0.45
T_R3 = B2 + LC1                                 # 586.43
# 声の位置
V1 = 8.0 - (V_ON - V_OFF)                       # 7.5: 声 (1 回目): 2 小節 (8 秒) から話し始める
TK = K0 + 304.4                                 # 337.6: A が止まる所 (ファ、ド・ソの後)。声 (2 回目) はここで話し始める (tablet276 と同じ)
V2 = TK - (V_ON - V_OFF)                        # 337.1
V1_END, V2_END = V1 + V_LEN - V_OFF, V2 + V_LEN - V_OFF     # 201.1 / 530.7
# 伴奏のつまみを動かす所 (A の録音の秒): 1 回目の声が終わる所で戻し、2 回目の声の入りで下げ、終わりで戻す
AX1, XF1 = 162.3, 1.85                          # 162.3〜164.15 秒で戻す: 声の終わりの言葉の下の強い音 (161.69 秒) は小さいまま、その余韻から (声は 165.7 秒に終わる)
AX2, AX3, XFL = 303.6, 497.5, 3.0               # 303.6〜305.4 秒で下げる (A が止まっている間) / 497.5〜500.5 秒で戻す (2 回目の声は 495.0 秒に終わる)
# tablet89 (tablet285 と同じ置き方: A の時間で同じ所)
P, OV = 8.0, 0.3                                # 祈りの言葉: tablet89 の元の 8 秒から 8 秒
S_N = -4; L_N = P / RATE(S_N)                   # 4 半音下げて、10.08 秒
T1 = K0 + 13.0                                  # 46.206: 祈りの 1 回目 (A の最初の音の 8 秒後 — tablet285 と同じ間合い)
T_CONT = T1 + 3 * L_N                           # 76.44: 4 回目からそのまま Requiem I (元の 96 秒まで)
N_END = 96.0
T_E = K0 + 165.0                                # 198.2: 祈りの言葉がもう一度 — 1 回目の声が終わる所 (A の 165.7 秒) で。着く音 (変ニ) が、A が 170.39 秒に弾く変ニに重なる
S_AM, AM_OFF = -2, 373.5                        # Amen: 2 半音下げて (ハ長調)
T_AM = T_R3 + L3 + (552.3 - X1 - HOLD - LC0)    # 589.9: 3 回目のド・ミ (590.15 秒) に合わせて開く (tablet285 と同じ間合い: ド・ミの 0.25 秒前から)
S_HI = 7; L_HI = P / RATE(S_HI)                 # 高い祈り: 7 半音上げて、5.34 秒
T_M3 = T_AM + 2.7                               # 592.6: Amen の 2.7 秒後 (tablet285 と同じ間合い)
S2, S3, S4, S5, S6, TOTAL = 23, 52, 83, 110, 146, 154
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None, faithful=False):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout, faithful=faithful)
def voice(beat, g, tag):                        # 声を 3 つに分けて置く: 静かな話し始め (持ち上げる)、その次 (少し持ち上げる)、その先
    return [play(RV, beat, g * GL1, 0, V_OFF, V_CUT - V_OFF, 0, COLV, tag, fin=0.3, fout=0.05, faithful=True),
            play(RV, beat + V_CUT - V_OFF, g * GL2, 0, V_CUT, V_CUT2 - V_CUT, 0, COLV, 'calma の声 — 続き', fin=0.05, fout=0.05, faithful=True),
            play(RV, beat + V_CUT2 - V_OFF, g, 0, V_CUT2, V_LEN - V_CUT2, 0, COLV, 'calma の声 — 続き', fin=0.05, fout=2.0, faithful=True)]
PLAYS = voice(V1, GV, 'calma の声 (tablet233 の声) — 届いたまま (2 小節から)')
for k, g in enumerate(LOOP_A):                  # 11/20 の出だしを 3 回、少しずつ大きく (声の下で)
    PLAYS.append(play(RA, T_R1 + k * L1, GA * g * BED, 0, LA0, L1 + OVA, 4, COLR, '11/20 の鍵盤 — 出だしの一節 (%d 回目)' % (k + 1), fin=0.1 if k == 0 else OVA, fout=OVA))
IA = len(PLAYS)                                 # A (4 回目から): 声の間は下げて、声が終わると戻す (同じ録音どうしのクロスフェードでつまみを動かす)
PLAYS += [play(RA, K0 + LA0, GA * BED, 0, LA0, AX1 - LA0 + XF1, 1, COLA, '11/20 02:40 の鍵盤 — 4 回目からそのまま (声の下で、小さめに)', fin=OVA, fout=XF1),
          play(RA, K0 + AX1, GA * SOLO, 0, AX1, AX2 - AX1 + 1.8, 1, COLA, '11/20 の鍵盤 — ひと息 (声が休む間)', fin=XF1, fout=1.8),
          play(RA, K0 + AX2, GA * BED, 0, AX2, AX3 - AX2 + XFL, 1, COLA, '11/20 の鍵盤 — 白い鍵盤 (声の下で)', fin=1.8, fout=XFL),
          play(RA, K0 + AX3, GA * SOLO, 0, AX3, A_END - AX3, 1, COLA, '11/20 の鍵盤 — 山へ、最後の音まで', fin=XFL, fout=A_FADE)]
PLAYS.append(play(RB, B0 + B_ON, GB * BED, 0, B_ON, B_OPEN - B_ON, 2, COLB, '11/21 04:16 の鍵盤 — 黒い鍵盤の出だし', fin=0.6, fout=0.25))
PLAYS += [play(RB, B1 + B_F, GB * BED, 0, B_F, E0 - B_F + XE0, 2, COLB, '11/21 04:16 の鍵盤 — 同じファから (声の下で)', fin=0.1, fout=XE0),
          play(RB, B1 + E0, GB * BED * DUCK1, 0, E0, E1 - E0 + XE1, 2, COLB, '黒い鍵盤への寄り道 — 小さく', fin=XE0, fout=XE1),
          play(RB, B1 + E1, GB * BED, 0, E1, P_END - E1, 2, COLB, '続き', fin=XE1, fout=1.5)]
for k, g in enumerate(LOOP_B):                  # 11/21 の上っていく一節を 3 回 (11/21 が休む間に、声の下で)
    PLAYS.append(play(RB, T_R2 + k * L2, GB * g * BED, 0, LB0, L2 + OVB, 4, COLR, '11/21 の鍵盤 — 上っていく一節 (%d 回目)' % (k + 1), fin=OVB, fout=OVB))
PLAYS += [play(RB, B2 + P_START, GB * BED, 0, P_START, C0 - P_START + XC, 2, COLB, '11/21 04:16 — 休んでから、続き', fin=0.3, fout=XC),
          play(RB, B2 + C0, GB * BED * DUCK2, 0, C0, C1 - C0 + XC, 2, COLB, '', fin=XC, fout=XC),
          play(RB, B2 + C1, GB * SOLO * LOOP_C[0], 0, C1, LC1 - C1 + OVC, 2, COLB, '続き — 山へ、ド・ミで閉じる', fin=XC, fout=OVC),
          play(RB, T_R3, GB * SOLO * LOOP_C[1], 0, LC0, L3 + OVC, 4, COLR, '11/21 の鍵盤 — 終止をもう一度 (2 回目)', fin=OVC, fout=OVC),
          play(RB, T_R3 + L3, GB * SOLO * LOOP_C[2], 0, LC0, B_CUT - LC0, 4, COLR, '終止 (3 回目)', fin=OVC, fout=B_FOUT)]
IBEND = len(PLAYS) - 3                          # B の終わりの切れ (和音の表示用)
for k, g in enumerate(LOOP_P):                  # tablet89 の祈りの言葉 (4 半音下げて) を 3 回、少しずつ大きく (声の下で)
    PLAYS.append(play(R89, T1 + k * L_N, G89A * g * BED, S_N, P, P + OV, 3, COL89, 'tablet89 — 祈りの言葉、4 半音下げて (%d 回目)' % (k + 1), fin=3.0 if k == 0 else OV, fout=OV))
PLAYS.append(play(R89, T_CONT, G89A * BED, S_N, P, N_END - P, 3, COL89, 'tablet89 — 4 回目からそのまま: Requiem I (4 半音下げて)', fin=OV, fout=3.0))
PLAYS.append(play(R89, T_E, G89A * LOOP_E, S_N, P, P, 3, COL89, 'tablet89 — 祈りの言葉がもう一度 (声が終わる所で、1 回)', fin=1.2, fout=2.4))   # 入りは 1.5 秒、終わりは 3 秒かけて (元の時間で 1.2 秒・2.4 秒)
I89AM = len(PLAYS)
PLAYS.append(play(R89, T_AM, G89C * SOLO, S_AM, AM_OFF, 391.0 - AM_OFF, 3, COL89, 'tablet89 — Amen、2 半音下げて (ハ長調)', fin=1.5, fout=3.0))
for k, g in enumerate(LOOP_H):                  # 高い祈り (7 半音上げて) を 3 回、少しずつ遠く
    PLAYS.append(play(R89, T_M3 + k * L_HI, G89D * SOLO * g, S_HI, P, P + OV, 4, COLR, 'tablet89 — 祈りの言葉、7 半音上げて (%d 回目)' % (k + 1), fin=1.5 if k == 0 else OV, fout=2.5 if k == 2 else OV))
PLAYS += voice(V2, GV * GV2, 'calma の声 — もう一度 (白い鍵盤の上で)')
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍): A、A が終わってからは B、終わりは Amen
LEAD = [(3, T_R1), (4, T_R1 + L1), (5, T_R1 + 2 * L1), (IA, K0 + LA0), (IA + 1, K0 + AX1 + XF1), (IA + 2, K0 + AX2 + 1.8), (IA + 3, K0 + AX3 + XFL), (IBEND, K0 + A_END), (I89AM, T_R3 + L3 + 2.3)]
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
    P_.section(0, 'I. Voce — 優しい声が、先に (♩=60)', '2 小節から calma の声。4 小節から 11/20 の鍵盤の出だしが 3 回。46 秒から祈りの言葉が 3 回、そのまま Requiem I へ')
    P_.section(S2, 'II. Dialogo — もう 1 つの夜が答える', '1 分 36 秒から 1 分ほど、11/21 の鍵盤が答える。声は 3 分 19 秒まで。声の終わりに、祈りの言葉がもう一度')
    P_.section(S3, 'III. Respiro — ひと息', '声が休み、11/20 の鍵盤だけ。3 分 29 秒から途切れずに流れ、ファへ向かう')
    P_.section(S4, 'IV. Luce — 同じファから白い鍵盤へ、声をもう一度', '5 分 34 秒に同じファ。5 分 38 秒から声。7 分 0 秒から、上っていく一節が 3 回')
    P_.section(S5, 'V. Insieme — 2 つで', '7 分 21 秒から、また 2 つで。声は 8 分 48 秒まで。9 分 25 秒に山')
    P_.section(S6, 'VI. Amen — ド・ミ、そして遠ざかる', '9 分 46 秒、ド・ミで閉じる (3 回)。ハ長調の Amen。ミ・レ・ドが高く 3 回、遠ざかる')
    return P_

def post(P_, events, ex):
    for p in PLAYS:
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm)
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05) / r, env_off=off / r)
        if p['faithful']:   # 声: 帯域を削らず、全体の残響を掛けずに前に (声の残響は声の中にある)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:               # 鍵盤と tablet89: tablet282 と同じ重ね方 (全体の残響)。tablet89 の移調はテープのように速さごと
            add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [8.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXXVII · Il dolce consiglio',
        'subtitle': 'tablet285 と tablet286 を、tablet233 の優しい声で、諭すように。変ニ長調 → ハ長調、♩=60',
        'footer': ['声は届いた calma の声そのまま (tablet233 の声)。2 小節から声、4 小節から曲。声が話している間は、伴奏を小さく。',
                   '鍵盤は 1 回だけ鳴らし、tablet286 の 3 回ずつのくり返しと、tablet285 の祈りの言葉・Requiem I・Amen を重ねた。',
                   '声は 2 回。間の 2 分は鍵盤だけのひと息。終わりはド・ミで閉じ、ミ・レ・ドが遠ざかる。楽器は何も加えない。154 小節。']}
if FIXPEAK > 0: META['fixed_peak'] = FIXPEAK

if __name__ == '__main__':
    compose.main(OUT, seed=287, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']), 'fixed_peak', d['meta'].get('fixed_peak'))
    for k, e in enumerate(d['extras']): print('  %2d %7.2f - %7.2f s  gain %.3f  semis %+d  off %6.2f  lane %d  %s' % (k, e['t'], e['t'] + e['d'], e['gain'], e['semis'], e['off'], e['lane'], e['tag']))
