#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXXVIII · Canto di luce (歌声・2 つの鍵盤の録音・tablet89 を — 聖夜の夜から、歌声の光へ)
  届いたもの: 20250108_144205_aureola_donna_sensuale.mp3 (大人の 20 代の光輪様の歌声 — CCLVI で作った声、4 分 19 秒)、
    20261120_024046.mp3・20261121_041625.mp3 (2 つの鍵盤の録音)、tablet89.mp4。どれも前に届いたものと同じファイル。
    依頼は「これらの曲を…作ってください」で、声を作り換える依頼ではないので、歌声は届いたまま使う (高さも速さもそのまま、音量のつまみだけ)
  言葉 (薬や味にたとえた気分; CCLXXXVI と同じ) を音の言葉に直した。曲は薬ではない
  歌声の高さと置き方 (濁りの指数を測って決めた):
    歌はト短調の高さで、伸ばした音はニ短調の音階 (ソ 25%・ド 20%・ラ 12%・レ 12%・変ロ 11%)。黒い鍵盤 (変ニ長調 / 変ロ短調) とは半音でぶつかる。
      白い鍵盤 (ハ長調 / イ短調) とは、変ロのほかは同じ音。だから歌声は夜 (黒い鍵盤) には入れず、2 つの鍵盤が同じファで白い鍵盤へ移ってから歌う
    歌の前半 (ファイルの 164 秒まで) は、白い鍵盤が始まってすぐ (A の 306.4 秒 = ファイルの 0 秒) に置く: 出だしの 8 秒の指数 0.31、句ごとに 0.33〜0.34
    歌の最後の句 (210.7 秒から; ラ・変ロ・嬰ハ・レ = ニ短調の動き) は、鍵盤の終わりの所 (シを中心に動く) と、どこに置いても 0.39〜0.43 でぶつかる。
      そこで、歌のひと息 (ファイルの 164〜174.5 秒) を 36.6 秒長くして (B の休みを 22 秒長くしたのと同じ考え方)、歌の後半を A の 343.0 秒 = ファイルの 0 秒に置く:
      句の終わりのレが鍵盤の属和音 (シ・ファ) に乗り、鍵盤がド・ミで閉じると、歌声がドで受けて、ド → 嬰ハ → レと上がる。
      そこから先の最後の句は、tablet89 の終わり (元の高さ = ニ短調のストレッタから Amen まで) が支える (指数 0.30)。
      歌は属音のラで終わり、tablet89 が属和音からニ長調の和音 (Amen) で受けて閉じる
  形 (♩=60、1 小節 = 4 秒; A の録音の f 秒は曲の f + 25.206 秒 — tablet286 と同じ):
    I.   Notte (0 小節)        2 小節 (8 秒) から 11/20 の鍵盤の出だしが 3 回、少しずつ大きく (tablet286)。38 秒から tablet89 の祈りの言葉 (4 半音下げて) が 3 回、
                               1 分 8 秒からそのまま Requiem I (tablet285)
    II.  Dialogo (21 小節)     1 分 28 秒から 2 分 23 秒まで、11/21 の鍵盤の黒い鍵盤の出だしが答える。Requiem I は 2 分 59 秒に閉じ、3 分 10 秒に祈りの言葉がもう一度だけ戻る (tablet287)
    III. Sola (50 小節)        11/20 の鍵盤だけ。3 分 21 秒から途切れずに流れ、ファへ向かう
    IV.  Luce (81 小節)        5 分 26 秒、同じファ。5 分 31 秒から白い鍵盤、5 分 32 秒から歌声。6 分 52 秒から、11/21 が休む間に上っていく一節が 3 回
    V.   Insieme (108 小節)    7 分 13 秒から、また 2 つの鍵盤で。歌は 8 分 16 秒にひと息 (鍵盤だけの 47 秒)。9 分 3 秒から歌の後半、9 分 17 秒に山
    VI.  Amen (144 小節)       9 分 38 秒、鍵盤がド・ミで閉じ、歌声がドで受ける。tablet89 (元の高さ) が歌の最後の句を支える。10 分 25 秒に歌い終えると、ニ長調の Amen。163 小節
  歌声が入ってからは、鍵盤を 0.71 倍 (−3 dB) に下げる (歌が前に立つように)。歌がひと息つく間は、鍵盤を元の大きさに戻す。
    歌は先へ行くほど静かに歌われているので、2 つの切れ目で分けて 1.1 倍・1.25 倍に (tablet255・256 は後半を 1.2 倍)
  声は synth.py の faithful の経路 (ステレオのまま、帯域を削らず、全体の残響を掛けずに前に)。鍵盤と tablet89 は tablet282 と同じ重ね方
  使い方: python compose_tablet288.py <wav のフォルダ (20250108_144205.wav = 歌声, 20261120_024046.wav・20261121_041625.wav = soften282.py を通した鍵盤の録音,
          20261107_089000.wav = tablet89 の音)> <chords288.json (analyze_chords.py の出力)> [score_tablet288.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet288.json'
E = lambda k, v: float(os.environ.get(k, v))
GV = E('GV', '1.0')                                         # 歌声の音量 (段ごとに書き出して測って決めた)
GV2, GV3 = E('GV2', '1.1'), E('GV3', '1.25')                # 歌は先へ行くほど静かに歌われている (20 秒ごとに −22〜−24 → −25 → −26 dB) ので、2 つの切れ目で分けて少しずつ持ち上げる
BEDV = E('BEDV', '0.71')                                    # 歌声が入ってからの鍵盤のつまみ (−3 dB; 歌が前に立つように)
GA, GB = E('GA', '0.233'), E('GB', '0.232')                 # 鍵盤の音量 (tablet282 と同じ)
DUCK1, DUCK2 = E('DUCK1', '0.25'), E('DUCK2', '0.125')      # B が黒い鍵盤へ寄り道する 2 か所のつまみ
G89A = E('G89A', '0.16')                                    # tablet89: 4 半音下げて (夜; tablet285 と同じ)
G89F, RISE = E('G89F', '0.13'), E('RISE', '2.85')           # tablet89: 元の高さ (歌の最後の句の下)。歌い終わる所から RISE 倍に (消えていく Amen の和音が聞こえるように)
LOOP_A = (0.50, 0.70, 0.85)                                 # 11/20 の出だしの 3 回 (tablet286 と同じ)
LOOP_P = (0.45, 0.65, 0.85)                                 # 祈りの言葉 (4 半音下げて) の 3 回 (tablet285 と同じ)
LOOP_E = E('LOOP_E', '0.50')                                # Requiem I が閉じた後に、祈りの言葉が 1 回だけ戻る (tablet287 と同じ所、同じ大きさ)
LOOP_B = (0.60, 0.80, 1.00)                                 # 上っていく一節の 3 回 (tablet286 と同じ)
FIXPEAK = E('FIXPEAK', '0.74')                              # 仕上げの大きさ (synth.py の基準; 0 なら山に合わせる)。夜の大きさが tablet285 (0.72) とほぼ同じになる
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, RA, RB, R89 = '20250108_144205', '20261120_024046', '20261121_041625', '20261107_089000'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
COLV, COLA, COLB, COL89, COLR = (255, 190, 160), (150, 195, 240), (245, 215, 150), (200, 180, 240), (250, 235, 190)
# 鍵盤 (tablet286 と同じ置き方)
LA0, L1, OVA = 5.10, 12.634 - 5.232, 0.3        # 11/20 の出だしの一節: 録音の 5.10 秒から 7.402 秒
T_R1 = 8.10                                     # 1 回目: 最初の音が 2 小節 (8.2 秒) に鳴る
K0 = T_R1 + 3 * L1 - LA0                        # 25.206: A の録音の f 秒は曲の f + 25.206 秒
A_END, A_FADE = 553.0, 1.4
B_ON = 3.0
B0 = K0 + 59.0                                  # 84.206: B の黒い鍵盤の出だし
B_OPEN, B_F = 58.40, 58.45
X1 = 301.013 - 58.585                           # 242.428: B のファを A のファに合わせる
HOLD = 22.0
B1 = K0 + X1; B2 = B1 + HOLD                    # 267.634 / 289.634; B の録音の g 秒 (休みの後) は A の g + 264.428 秒
P_END, P_START = 139.0, 142.9
E0, E1, XE0, XE1 = 111.3, 121.0, 0.4, 0.25
C0, C1, XC = 227.93, 232.90, 0.12
LB0, L2, OVB = 58.45, 7.15, 0.1                 # 上っていく一節
T_R2 = K0 + 386.75 - (58.585 - LB0)             # 411.82
B_CUT, B_FOUT = 288.90, 0.45                    # B はハ長調の終止 (ド・ミ) の後、黒い鍵盤へ戻る手前で止める
# 歌声 (ファイルの 0.6 秒から歌い出し、164.2 秒でひと息、174.5 秒から後半、256.5 秒に歌い終わる)。2 つの切れ目 (71 秒、170 秒) で 3 つに分けて置く
V_LEN, V_S1, V_S2 = 258.63, 71.0, 170.0
V_AT = 306.4                                    # 前半: ファイルの 0 秒を A の 306.4 秒に (白い鍵盤の最初の音は 306.19 秒)
V_AT2 = 343.0                                   # 後半: ファイルの 0 秒を A の 343.0 秒に (ひと息が 36.6 秒長くなる)。句の終わりのレ (208.1〜209.5 秒) が B の属和音 (A の 551.2〜552.5 秒) に乗る
T_V, T_V2 = K0 + V_AT, K0 + V_AT2               # 331.606 / 368.206
# 鍵盤のつまみを動かす所 (A の録音の秒; 同じ録音どうしのクロスフェードで)
AX2 = 303.6                                     # 303.6〜305.4 秒 (A が止まっている間) で、歌声の下の大きさへ
AX3, AX4, XFI = 471.0, 514.5, 2.0               # 歌のひと息: 471〜473 秒で元の大きさへ戻し、514.5〜516.5 秒でまた下げる (歌の後半は 517.5 秒から)
BX3, BX4 = AX3 - X1 - HOLD, AX4 - X1 - HOLD     # 同じ時刻を B の録音の秒で (206.57 / 250.07)
# tablet89
P, OV = 8.0, 0.3                                # 祈りの言葉: tablet89 の元の 8 秒から 8 秒
S_N = -4; L_N = P / RATE(S_N)                   # 4 半音下げて、10.08 秒
T1 = K0 + 13.0                                  # 38.206: 祈りの 1 回目 (A の最初の音の 8 秒後 — tablet285 と同じ間合い)
T_CONT = T1 + 3 * L_N                           # 68.44: 4 回目からそのまま Requiem I (元の 96 秒まで)
N_END = 96.0
T_E = K0 + 165.0                                # 190.2: 祈りの言葉がもう一度 — Requiem I が閉じて 11 秒後、A が自分で休む所 (166.5〜168.1 秒) を埋める。着く音 (変ニ) が、A が 170.39 秒に弾く変ニに重なる
F_O = 114.0                                     # 終わり: tablet89 の元の秒 = 歌のファイルの秒 + 114 (0.5 秒ずつ動かして、歌の最後の句との指数がいちばん小さい所の 1 つ: 0.30)
F_ON, F_UP, F_XF = 323.8, 369.5, 2.0            # 元の 323.8 秒 (ストレッタの初め) から。歌の最後の音 (ラ) の所 (元の 369.5〜371.5 秒) でつまみを上げる
T_F = T_V2 + F_ON - F_O                         # 578.0: 鍵盤のド・ミ (577.75 秒) のすぐ後から、3 秒かけて入る
S2, S3, S4, S5, S6, TOTAL = 21, 50, 81, 108, 144, 163
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None, faithful=False):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout, faithful=faithful)
PLAYS = []
for k, g in enumerate(LOOP_A):                  # 11/20 の出だしを 3 回、少しずつ大きく
    PLAYS.append(play(RA, T_R1 + k * L1, GA * g, 0, LA0, L1 + OVA, 4, COLR, '11/20 の鍵盤 — 出だしの一節 (%d 回目)' % (k + 1), fin=0.1 if k == 0 else OVA, fout=OVA))
IA = len(PLAYS)                                 # A (4 回目から): 夜はそのまま、歌声の下では小さく、歌のひと息では元の大きさ
PLAYS += [play(RA, K0 + LA0, GA, 0, LA0, AX2 - LA0 + 1.8, 1, COLA, '11/20 02:40 の鍵盤 — 4 回目からそのまま', fin=OVA, fout=1.8),
          play(RA, K0 + AX2, GA * BEDV, 0, AX2, AX3 - AX2 + XFI, 1, COLA, '11/20 の鍵盤 — 白い鍵盤 (歌声の下で)', fin=1.8, fout=XFI),
          play(RA, K0 + AX3, GA, 0, AX3, AX4 - AX3 + XFI, 1, COLA, '11/20 の鍵盤 — 歌のひと息の間', fin=XFI, fout=XFI),
          play(RA, K0 + AX4, GA * BEDV, 0, AX4, A_END - AX4, 1, COLA, '11/20 の鍵盤 — 山へ、最後の音まで (歌声の下で)', fin=XFI, fout=A_FADE)]
PLAYS.append(play(RB, B0 + B_ON, GB, 0, B_ON, B_OPEN - B_ON, 2, COLB, '11/21 04:16 の鍵盤 — 黒い鍵盤の出だし', fin=0.6, fout=0.25))
PLAYS += [play(RB, B1 + B_F, GB * BEDV, 0, B_F, E0 - B_F + XE0, 2, COLB, '11/21 04:16 の鍵盤 — 同じファから (歌声の下で)', fin=0.1, fout=XE0),
          play(RB, B1 + E0, GB * BEDV * DUCK1, 0, E0, E1 - E0 + XE1, 2, COLB, '黒い鍵盤への寄り道 — 小さく', fin=XE0, fout=XE1),
          play(RB, B1 + E1, GB * BEDV, 0, E1, P_END - E1, 2, COLB, '続き', fin=XE1, fout=1.5)]
for k, g in enumerate(LOOP_B):                  # 11/21 の上っていく一節を 3 回 (11/21 が休む間に、歌声の下で)
    PLAYS.append(play(RB, T_R2 + k * L2, GB * g * BEDV, 0, LB0, L2 + OVB, 4, COLR, '11/21 の鍵盤 — 上っていく一節 (%d 回目)' % (k + 1), fin=OVB, fout=OVB))
PLAYS += [play(RB, B2 + P_START, GB * BEDV, 0, P_START, BX3 - P_START + XFI, 2, COLB, '11/21 04:16 — 休んでから、続き', fin=0.3, fout=XFI),
          play(RB, B2 + BX3, GB, 0, BX3, C0 - BX3 + XC, 2, COLB, '11/21 の鍵盤 — 歌のひと息の間', fin=XFI, fout=XC),
          play(RB, B2 + C0, GB * DUCK2, 0, C0, C1 - C0 + XC, 2, COLB, '', fin=XC, fout=XC),
          play(RB, B2 + C1, GB, 0, C1, BX4 - C1 + XFI, 2, COLB, '続き', fin=XC, fout=XFI),
          play(RB, B2 + BX4, GB * BEDV, 0, BX4, B_CUT - BX4, 2, COLB, '山へ、ド・ミで閉じる (歌声の下で)', fin=XFI, fout=B_FOUT)]
IBEND = len(PLAYS) - 1                          # B の終わりの切れ (和音の表示用)
for k, g in enumerate(LOOP_P):                  # tablet89 の祈りの言葉 (4 半音下げて) を 3 回、少しずつ大きく
    PLAYS.append(play(R89, T1 + k * L_N, G89A * g, S_N, P, P + OV, 3, COL89, 'tablet89 — 祈りの言葉、4 半音下げて (%d 回目)' % (k + 1), fin=3.0 if k == 0 else OV, fout=OV))
PLAYS.append(play(R89, T_CONT, G89A, S_N, P, N_END - P, 3, COL89, 'tablet89 — 4 回目からそのまま: Requiem I (4 半音下げて)', fin=OV, fout=3.0))
PLAYS.append(play(R89, T_E, G89A * LOOP_E, S_N, P, P, 3, COL89, 'tablet89 — 祈りの言葉がもう一度 (1 回)', fin=1.2, fout=2.4))   # 入りは 1.5 秒、終わりは 3 秒かけて (元の時間で 1.2 秒・2.4 秒)
I89F = len(PLAYS)                               # 終わり: 元の高さ (ニ短調) のストレッタから Amen (ニ長調) まで。歌の最後の句を支え、歌い終わると前に出て閉じる
PLAYS += [play(R89, T_F, G89F, 0, F_ON, F_UP - F_ON + F_XF, 3, COL89, 'tablet89 — 元の高さ (ニ短調): 歌の最後の句を支える', fin=3.0, fout=F_XF),
          play(R89, T_F + F_UP - F_ON, G89F * RISE, 0, F_UP, 391.0 - F_UP, 3, COL89, 'tablet89 — Amen (ニ長調) で閉じる', fin=F_XF, fout=3.0)]
PLAYS += [play(RV, T_V, GV, 0, 0.0, V_S1, 0, COLV, '光輪様の歌声 — 届いたまま (白い鍵盤から)', fin=0.05, fout=0.3, faithful=True),
          play(RV, T_V + V_S1, GV * GV2, 0, V_S1, V_S2 - V_S1, 0, COLV, '歌声 — 続き', fin=0.3, fout=0.5, faithful=True),
          play(RV, T_V2 + V_S2, GV * GV3, 0, V_S2, V_LEN - V_S2, 0, COLV, '歌声 — 後半 (ひと息の後)', fin=0.5, fout=1.0, faithful=True)]
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍): A、A が終わってからは B、終わりは tablet89
LEAD = [(0, T_R1), (1, T_R1 + L1), (2, T_R1 + 2 * L1), (IA, K0 + LA0), (IA + 1, K0 + AX2 + 1.8), (IA + 2, K0 + AX3 + XFI), (IA + 3, K0 + AX4 + XFI), (IBEND, K0 + A_END), (I89F, T_F + 3.0), (I89F + 1, T_F + F_UP - F_ON + F_XF)]
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
    P_.section(0, 'I. Notte — 聖夜の小さな音 (♩=60)', '2 小節から 11/20 の鍵盤の出だしが 3 回。38 秒から祈りの言葉が 3 回、そのまま Requiem I へ')
    P_.section(S2, 'II. Dialogo — もう 1 つの夜が答える', '1 分 28 秒から 1 分ほど、11/21 の鍵盤が答える。Requiem I は 2 分 59 秒に閉じ、祈りの言葉がもう一度')
    P_.section(S3, 'III. Sola — ファへ向かう', '11/20 の鍵盤だけ。3 分 21 秒から途切れずに流れる')
    P_.section(S4, 'IV. Luce — 同じファから、歌声', '5 分 26 秒に同じファ。5 分 31 秒から白い鍵盤、5 分 32 秒から歌声。6 分 52 秒から、上っていく一節が 3 回')
    P_.section(S5, 'V. Insieme — 歌と 2 つの鍵盤', '7 分 13 秒から、また 2 つで。歌は 8 分 16 秒にひと息 (鍵盤だけ)。9 分 3 秒から歌の後半、9 分 17 秒に山')
    P_.section(S6, 'VI. Amen — 歌の最後の句、ニ長調へ', '9 分 38 秒、鍵盤がド・ミで閉じ、歌声がドで受ける。tablet89 (元の高さ) が歌を支え、ニ長調の Amen で閉じる')
    return P_

def post(P_, events, ex):
    for p in PLAYS:
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm)
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05) / r, env_off=off / r)
        if p['faithful']:   # 歌声: ステレオのまま、帯域を削らず、全体の残響を掛けずに前に (声の残響は声の中にある)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:               # 鍵盤と tablet89: tablet282 と同じ重ね方 (全体の残響)。tablet89 の移調はテープのように速さごと
            add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [8.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXXVIII · Canto di luce',
        'subtitle': '歌声・2 つの鍵盤・tablet89。夜は鍵盤と祈り、白い鍵盤から歌声。変ニ長調 → ハ長調 → ニ長調、♩=60',
        'footer': ['歌声は届いた音声そのまま (大人の 20 代の光輪様の歌声)。歌の高さは白い鍵盤に合うので、夜には入れず、白い鍵盤から歌う。',
                   '夜は 11/20・11/21 の鍵盤と、tablet89 の祈りの言葉・Requiem I (4 半音下げて)。出だしと祈りは 3 回ずつ、少しずつ大きく。',
                   '鍵盤がド・ミで閉じると、歌の最後の句を tablet89 (元の高さ) が支え、ニ長調の Amen で閉じる。楽器は何も加えない。163 小節。']}
if FIXPEAK > 0: META['fixed_peak'] = FIXPEAK

if __name__ == '__main__':
    compose.main(OUT, seed=288, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']), 'fixed_peak', d['meta'].get('fixed_peak'))
    for k, e in enumerate(d['extras']): print('  %2d %7.2f - %7.2f s  gain %.3f  semis %+d  off %6.2f  lane %d  %s' % (k, e['t'], e['t'] + e['d'], e['gain'], e['semis'], e['off'], e['lane'], e['tag']))
