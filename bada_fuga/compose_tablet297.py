#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCXCVII · Ninna nanna delle due notti (2 つの夜の子守歌 — calma の声と 2 つの鍵盤の録音をミックス)
  届いたもの: tablet233_voce_sola.mp3 (calma の声そのもの; これまで届いた 20261108_145525_aureola_sensuale_calma.mp3 と 1 バイトも違わない)、
    20261120_024046.mp3・20261121_041625.mp3 (2 つの鍵盤の録音; 前と同じファイル)。依頼は CCXCVI と同じ言葉「睡眠導入剤の効く洗脳的に曲をミックスして」。
    曲は薬ではない。言葉が指している向き (眠りへ) を、CCXCVI と同じ音の言葉に直した。今回は声と 2 つの鍵盤だけで作る (トラック 18・トラック 8・tablet89 は届いていない)。
    声を作り換える依頼ではないので、声は届いたまま使う。楽器は何も加えない。鍵盤は速さも音の高さもそのまま
  眠りへ下りる 4 つの段 — 段ごとに音量が下がり、鍵盤は高い所の小さな音から低い所へ下りていき、調は半音下がる:
    I.   Veglia (目覚めている)  変ニ長調   声 (2 小節から)。4 小節から 11/20 の鍵盤の出だし (ファ・変ホの和音、変ト、変ホ、変ニ — 主音へ下りる一節) が 3 回、少しずつ大きく → そのまま先へ。
                               黒い鍵盤の小さな音が声の下で鳴り、11/21 の鍵盤の黒い鍵盤の出だしが音と音の間に答える。声が終わる所で、出だしの一節がもう 1 回
    II.  Notte (夜)            変ニ長調   声が終わって、11/20 の鍵盤だけ。途切れずに流れ、ファへ向かう
    III. Sogno (夢)            ハ長調     同じファから白い鍵盤へ (2 つの鍵盤)。ここから終わりまで、つまみを 45 秒ごとに少しずつ下げていく。
                               11/21 が休む間に、11/21 の一節 (ファ・ミ・レと下りて、ミ・ファ・ソ・ドへ戻る) が 3 回、少しずつ遠く
    IV.  Sonno (眠り)          ハ長調     ド・ミ・ソの終止が 3 回、間を広げながら、少しずつ遠く。3 回目の終止から、同じ一節 (ファ・ミ・レ…ド) がもう 3 回、間を広げながら遠ざかって、消える
  同じ形を 3 回ずつ、4 つ (洗脳的): 初めの 1 つは少しずつ大きく (耳を引き寄せる)、あとの 3 つは少しずつ遠く。終わりの 2 つは間を広げる (だんだん遅く — 鍵盤の速さは変えないので、間で)。
    声の初めと終わりを、同じ出だしの一節が囲む
  声は 1 回だけ (初めの 3 分; 眠りへ誘って、あとは鍵盤に任せる)。声は synth.py の faithful の経路 (帯域を削らず、全体の残響を掛けずに前に)。
    calma の声は静かに話し始めるので、初めの 82 秒だけ、つまみで持ち上げる (5 段; CCXCVI と同じ)。声の間、鍵盤は下げておき、声が終わる所で 5 秒かけて戻す
  鍵盤の置き方は CCLXXXI からと同じ (同じファを重ねる、B の休みを 22 秒長く、B の寄り道の 2 か所を小さく、B の黒い鍵盤の出だしは A の 59 秒目から; tablet282 のしっとりの仕上げ)
  仕上げは歪ませない (synth.py の linear_master)
  使い方: python compose_tablet297.py <wav のフォルダ (20261108_145525.wav = calma の声, 20261120_024046.wav・20261121_041625.wav = soften282.py を通した鍵盤の録音)>
          <chords297.json (analyze_chords.py の出力)> [score_tablet297.json]
"""
import sys, os, json, math
import numpy as np
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet297.json'
E = lambda k, v: float(os.environ.get(k, v))
GV = E('GV', '0.95')                                        # 声の音量 (CCXCVI と同じ)
VLIFT = [(0.0, 5.5), (30.0, 4.0), (42.0, 2.5), (60.0, 1.5), (72.0, 0.7), (82.0, 0.0)]   # 静かな話し始めの持ち上げ: (録音の秒, dB)、3 秒のクロスフェードで (CCXCVI と同じ)
GA, GB = E('GA', '0.233'), E('GB', '0.232')                 # 鍵盤の音量 (tablet282 と同じ)
BED = E('BED', '0.50')                                      # 声が話している間の鍵盤のつまみ
NIGHT = E('NIGHT', '0.90')                                  # 声が終わってからの鍵盤のつまみ (CCXCVI の夜と同じ)
LOOP_A = (0.50, 0.70, 0.85)                                 # 11/20 の出だしの 3 回 — 少しずつ大きく (tablet286・287 と同じ)
DUCK1, DUCK2 = E('DUCK1', '0.25'), E('DUCK2', '0.125')      # B が黒い鍵盤へ寄り道する 2 か所のつまみ
LOOP_B = (0.90, 0.68, 0.50)                                 # 11/21 の一節の 3 回 (夢の段) — 少しずつ遠く (tablet286・287 は少しずつ大きく)
LOOP_C = (1.00, 0.80, 0.64)                                 # 終止の 3 回 — 少しずつ遠く
GAP_C = (E('GAP_C1', '0.6'), E('GAP_C2', '1.2'))            # 終止の間 (秒): 1 回目と 2 回目の間、2 回目と 3 回目の間 — 広げていく
GM = E('GM', '1.06')                                        # 終わりの一節 (終止の 1 回目のつまみに掛ける; 一節は 1 つずつの音で、和音より小さく録れているので、つまみは終止より上)
LOOP_M = (1.00, 0.82, 0.68)                                 # 終わりの一節の 3 回 — 少しずつ遠く
GAP_M = (E('GAP_M1', '0.3'), E('GAP_M2', '0.6'))            # 終わりの一節の間 (秒) — 広げていく (広げすぎると、間が −45 dB を下回る)
F0, FSTEP, FGAP, FXS = E('F0', '-4.0'), E('FSTEP', '-1.0'), 45.0, 6.0   # 夢の段のつまみ: 同じファで F0 dB、そこから FGAP 秒ごとに FSTEP dB ずつ (FXS 秒かけて; CCXCVI は 1.5 dB ずつ — 今回は鍵盤だけなので浅く)
FIXPEAK = E('FIXPEAK', '1.0')                               # 仕上げの基準 (linear_master; 山 × 1.2515 ÷ FIXPEAK が 1 を超えないこと)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, RA, RB = '20261108_145525', '20261120_024046', '20261121_041625'
BPM = 60
COLV, COLA, COLB, COLR = (255, 214, 150), (150, 195, 240), (245, 215, 150), (250, 235, 190)
# 声 (calma): ファイルの 4.86 秒から (話し始めは 5.36 秒、話し終わりは 196.5 秒)
V_OFF, V_ON, V_LEN = 4.86, 5.36, 198.46
V1 = 8.0 - (V_ON - V_OFF)                       # 7.5: 2 小節 (8 秒) から話し始める
# I. 11/20 の鍵盤 (A) の出だしを 3 回 (tablet286・287 と同じ置き方)
LA0, L1, OVA = 5.10, 12.634 - 5.232, 0.3        # 出だしの一節: 録音の 5.10 秒から 7.402 秒 (A は同じ和音を 7.4 秒後にもう一度自分で弾いている)
T_R1 = 16.10                                    # 1 回目: 最初の和音が 4 小節 (16.2 秒) に鳴る
K0 = T_R1 + 3 * L1 - LA0                        # 33.206: A の録音の f 秒は曲の f + 33.206 秒
A_END, A_FADE = 553.0, 1.4
AX1, XF1 = 162.3, 5.0                           # 声が終わる所で、鍵盤のつまみを戻す: A の 162.3〜167.3 秒 (声は A の 165.9 秒に話し終わる; A の次の音は 168.08 秒)
T_E = E('T_E', '194.0')                         # 声が終わる所で、出だしの一節がもう一度 (1 回): A はここで 6 秒休む (161.7〜168.1 秒)。一節の変ホ・変ニ (曲の 199.6・200.5 秒) が、声の終わり (199.1 秒) のすぐ後を埋める。
GE, E_FIN, E_FOUT = E('GE', '0.60'), 1.5, 1.5   #   置く位置は 0.25 秒ずつ動かして、濁りの指数がいちばん小さい所 (0.18)。A の続き (ド 201.3 秒、変ニ 203.5 秒) へ、変ホ・変ニ・ド・変ニとつながる
B_ON = 3.0
B0 = K0 + 59.0                                  # 92.206: B の黒い鍵盤の出だし (A の音と音の間に答える)
B_OPEN, B_F = 58.40, 58.45
X1 = 301.013 - 58.585                           # 242.428: B のファを A のファに合わせる
HOLD = 22.0
B1 = K0 + X1; B2 = B1 + HOLD                    # 275.634 / 297.634
P_END, P_START = 139.0, 142.9
E0, E1, XE0, XE1 = 111.3, 121.0, 0.4, 0.25
C0, C1, XC = 227.93, 232.90, 0.12
HINGE = K0 + 301.013                            # 334.219: 同じファ
LB0, L2, OVB = 58.45, 7.15, 0.1                 # 11/21 の一節: ファ、ミ、レ、ミ、ファ、ソ・ド、ド (録音の 58.45 秒から 7.15 秒)
T_R2 = K0 + 386.75 - (58.585 - LB0)             # 419.82: 夢の段の 3 回 — 頭のファを、A がその時に弾くファ (A の 386.75 秒) に重ねる (tablet286 と同じ)
LC0, LC1, OVC = 286.60, 288.80, 0.12            # 終止: シ・ファ、レ、ド・ミ・ソ
L3 = LC1 - LC0
B_CUT, B_FOUT = 288.90, 0.45
T_R3 = B2 + LC1                                 # 586.43: 流れの中の 1 回目が終わる所
T_C2 = T_R3 + GAP_C[0]                          # 終止の 2 回目
T_C3 = T_C2 + L3 + GAP_C[1]                     # 終止の 3 回目
T_M = T_C3 + E('DM', '0.03')                    # 終わりの一節の 1 回目: 3 回目の終止と一緒に始まる — 一節のファ → ミが、終止のシ・ファ → ド・ミ・ソの中のファ → ミに重なる (打鍵をそろえる)。
M_FIN = E('M_FIN', '1.5')                       #   1 回目の頭のファは 1.5 秒かけて入れる (終止のファに任せる)。終止の後に置くと、一節のファが終止の余韻のミ・シとぶつかる (濁りの指数 0.48 → 一緒に始めると 0.37 以下)
T_M2 = T_M + L2 + GAP_M[0]; T_M3 = T_M2 + L2 + GAP_M[1]
M_FOUT = E('M_FOUT', '2.5')
FADE = [(HINGE - 3.0, F0)] + [(HINGE + k * FGAP, F0 + k * FSTEP) for k in range(1, 6)]   # 眠りへの下り: (曲の秒, dB)
def fade_db(t):
    d = 0.0
    for tt, db in FADE:
        if t >= tt: d = db
    return d
S2, S3, S4, TOTAL = 51, 83, 146, int(E('TOTAL', '156'))
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None, faithful=False):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout, faithful=faithful, env=None)
def stretch(rid, T0, a, b, base, lane, color, tag, marks=(), fin=0.1, fout=1.5, sched=True, faithful=False):
    """録音の a〜b 秒を、録音の 0 秒が曲の T0 秒に来るように置く。marks = [(録音の秒, そこからの倍率, 動かす時間)] (声の終わり、B の寄り道など)。
      sched: 眠りへの下り (FADE) も掛ける — ほかの印から 18 秒以上離れた所だけ、同じ録音どうしのクロスフェード (FXS 秒) で 1 段下げる"""
    pts = [(a, 1.0, fin)] + sorted(marks)
    if sched:
        for tt, db in FADE:
            o = tt - T0
            if a + 3 * FXS < o < b - 3 * FXS and all(abs(o - m[0]) > 3 * FXS for m in marks): pts.append((o, None, FXS))
    pts.sort(key=lambda q: q[0]); out = []; mult = 1.0
    for k, (o, m, xf) in enumerate(pts):
        if m is not None: mult = m
        nxt = pts[k + 1] if k + 1 < len(pts) else None; end = (nxt[0] + nxt[2]) if nxt else b
        g = base * mult * (10 ** (fade_db(T0 + o + FXS / 2) / 20.0) if sched else 1.0)
        out.append(play(rid, T0 + o, g, 0, o, end - o, lane, color, tag if k == 0 else '', fin=xf, fout=(nxt[2] if nxt else fout), faithful=faithful))
    c = CH[rid]; env = np.asarray(c['env']); t = np.arange(len(env)) * c.get('env_dt', 0.05); gg = np.full(len(env), out[0]['gain'])   # 画面の波形: 包絡に、つまみの動きを掛けておく (継ぎ目で途切れて見えないように)
    for k in range(1, len(out)):
        a0, a1 = out[k - 1]['gain'], out[k]['gain']; gg = np.where(t >= out[k]['off'], a0 + (a1 - a0) * np.clip((t - out[k]['off']) / max(out[k]['fin'], 1e-6), 0.0, 1.0), gg)
    envp = [round(float(v), 4) for v in env * gg / max(q['gain'] for q in out)]
    for q in out: q['env'] = envp
    return out

# 声: 届いたまま 1 回。静かな話し始めだけ、つまみで持ち上げる (同じ録音どうしの 3 秒のクロスフェード)
PLAYS = stretch(RV, V1 - V_OFF, V_OFF, V_LEN, GV * 10 ** (VLIFT[0][1] / 20.0), 0, COLV, 'calma の声 — 届いたまま (2 小節から)',
                marks=[(o, 10 ** ((db - VLIFT[0][1]) / 20.0), 3.0) for o, db in VLIFT[1:]], fin=0.3, fout=2.0, sched=False, faithful=True)
IL = len(PLAYS)
for k, g in enumerate(LOOP_A):                  # I. 11/20 の出だしを 3 回、少しずつ大きく (声の下で)
    PLAYS.append(play(RA, T_R1 + k * L1, GA * BED * g, 0, LA0, L1 + OVA, 3, COLR, '11/20 の鍵盤 — 出だしの一節 (%d 回目)' % (k + 1), fin=0.1 if k == 0 else OVA, fout=OVA))
IA = len(PLAYS)                                 # A (4 回目から): 声の間は下げて、声が終わる所で戻し、夢の段で少しずつ下がって、最後の音まで
PLAYS += stretch(RA, K0, LA0, A_END, GA * BED, 1, COLA, '11/20 02:40 の鍵盤 — 4 回目からそのまま (声の下で、小さく)', marks=[(AX1, NIGHT / BED, XF1)], fin=OVA, fout=A_FADE)
IB = len(PLAYS)
PLAYS.append(play(RA, T_E, GA * GE, 0, LA0, L1 + OVA, 3, COLR, '11/20 の鍵盤 — 出だしの一節がもう一度 (声が終わる所で、1 回)', fin=E_FIN, fout=E_FOUT))
PLAYS.append(play(RB, B0 + B_ON, GB * BED, 0, B_ON, B_OPEN - B_ON, 2, COLB, '11/21 04:16 の鍵盤 — 黒い鍵盤の出だしが答える (声の下で)', fin=0.6, fout=0.25))
PLAYS += stretch(RB, B1, B_F, P_END, GB * NIGHT, 2, COLB, '11/21 04:16 の鍵盤 — 同じファから白い鍵盤へ', marks=[(E0, DUCK1, XE0), (E1, 1.0, XE1)], fin=0.1, fout=1.5)
for k, g in enumerate(LOOP_B):                  # III. 11/21 の一節を 3 回、少しずつ遠く (11/21 が休む間に)
    PLAYS.append(play(RB, T_R2 + k * L2, GB * NIGHT * 10 ** (fade_db(T_R2) / 20.0) * g, 0, LB0, L2 + OVB, 3, COLR, '11/21 の鍵盤 — ファ・ミ・レの一節 (%d 回目)' % (k + 1), fin=OVB, fout=OVB if k < 2 else 0.6))
GAPPED = GAP_C[0] > 0.3                         # 終止の間を空ける時は、1 回目も最後の終止と同じ切り方で (次の黒い鍵盤の音 288.92 秒の手前で、0.45 秒かけて)
PLAYS += stretch(RB, B2, P_START, B_CUT if GAPPED else LC1 + OVC, GB * NIGHT, 2, COLB, '11/21 04:16 — 休んでから、続き', marks=[(C0, DUCK2, XC), (C1, 1.0, XC)], fin=0.3, fout=B_FOUT if GAPPED else OVC)
GC = GB * NIGHT * 10 ** (fade_db(T_R3) / 20.0)  # IV. 終止の 3 回 — 間を広げながら、少しずつ遠く (1 回目は上の続きの終わり)
IC = len(PLAYS)
PLAYS += [play(RB, T_C2, GC * LOOP_C[1], 0, LC0, B_CUT - LC0, 3, COLR, '11/21 の鍵盤 — 終止をもう一度 (2 回目、遠く)', fin=OVC, fout=B_FOUT),
          play(RB, T_C3, GC * LOOP_C[2], 0, LC0, B_CUT - LC0, 3, COLR, '終止 (3 回目、もっと遠く)', fin=OVC, fout=B_FOUT)]
IM = len(PLAYS)                                 # 終わりの一節を 3 回 — 間を広げながら遠ざかって、消える
for k, (t, g) in enumerate(zip((T_M, T_M2, T_M3), LOOP_M)):
    PLAYS.append(play(RB, t, GC * GM * g, 0, LB0, L2 + OVB, 2, COLB, '11/21 の鍵盤 — ファ・ミ・レの一節がもう一度 (%d 回目、遠ざかる)' % (k + 1), fin=M_FIN if k == 0 else OVB, fout=0.6 if k < 2 else M_FOUT))
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍): A の出だしの 3 回 → A → 終わりは B の終止と一節
LEAD = [(IL + k, T_R1 + k * L1) for k in range(3)] + [(i, PLAYS[i]['beat']) for i in range(IA, IB)] + [(IC, T_C2), (IC + 1, T_C3)] + [(IM + k, PLAYS[IM + k]['beat']) for k in range(3)]
# 終わりの和音の表示は、読み取りではなく弾かれた音から: 終止はシ・ファ・レ (ト) → ド・ミ・ソ (ハ)。3 回目の後は、一節の間もハ
OVR = [(t + d, n) for t in (T_R3 - L3, T_C2, T_C3) for d, n in ((0.15, 'G'), (1.50, 'C'))]
def harm_at(q):
    cur = 'Bbm'
    for k, a in LEAD:
        p = PLAYS[k]
        if q >= a:
            c = CH[p['rid']]; ts = p['off'] + max(q - p['beat'], 0.0)                         # 録音の中の秒
            cur = c['chords'][min(int(min(ts, p['off'] + p['dur'] - 0.01) / c['win']), len(c['chords']) - 1)]
    for t, name in OVR:
        if q >= t: cur = name
    return cur
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P_ = Piece(TOTAL)
    for q in range(TOTAL * BPB): P_.harm[q] = harm_at(q)
    for k in range(TOTAL): P_.tempo[k] = BPM; P_.dyn[k] = 0.5
    for v in VOICES: P_.rest_bars(v, 0, TOTAL)
    P_.section(0, 'I. Veglia — 声が先に、黒い鍵盤の小さな音 (♩=60)', '2 小節から声。4 小節から 11/20 の鍵盤の出だしが 3 回、そのまま先へ。1 分 35 秒から 11/21 の鍵盤が答える')
    P_.section(S2, 'II. Notte — 声が終わって、鍵盤だけ', '3 分 19 秒に声が終わる。11/20 の鍵盤が途切れずに流れ、ファへ向かう')
    P_.section(S3, 'III. Sogno — 同じファから白い鍵盤へ', '5 分 34 秒に同じファ、2 つの鍵盤。ここから少しずつ小さく。7 分 0 秒からファ・ミ・レの一節が 3 回')
    P_.section(S4, 'IV. Sonno — 遠ざかって、眠りへ', 'ド・ミ・ソで 3 回閉じる (間を広げて、遠く)。ファ・ミ・レの一節がもう 3 回、消えていく')
    return P_

def post(P_, events, ex):
    for p in PLAYS:
        rid, off, dur = p['rid'], p['off'], p['dur']; c = CH.get(rid, {})
        kw = dict(lane=p['lane'], color=list(p['color']), env=p['env'] or c.get('env'), env_dt=c.get('env_dt', 0.05), env_off=off, env_faded=bool(p['env']))
        add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, rid=rid + '.wav', tag=p['tag'],
            **(dict(faithful=True) if p['faithful'] else {}), **kw)   # 声: faithful (ステレオのまま、帯域を削らず、全体の残響を掛けずに前に)。鍵盤: tablet282 と同じ重ね方 (全体の残響)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [8.0, 2.0, 0.4], 'linear_master': True, 'fixed_peak': FIXPEAK,
        'title': 'Requiem BADA — CCXCVII · Ninna nanna delle due notti',
        'subtitle': 'calma の声と 2 つの鍵盤。眠りへ下りる子守歌。変ニ長調 → ハ長調、♩=60',
        'footer': ['段ごとに音量が下がり、鍵盤は高い所の小さな音から低い所へ、調は半音下がる (変ニ長調 → ハ長調)。声は初めの 3 分だけ (届いたまま)。',
                   '同じ形を 3 回ずつ: 11/20 の出だし (近づく)、11/21 のファ・ミ・レの一節、ド・ミ・ソの終止、終わりにもう一度の一節 (遠ざかる)。',
                   'つなぐ音は同じファ。鍵盤は速さも高さもそのまま。楽器は何も加えない。曲は薬ではない。%d 小節。' % TOTAL]}

if __name__ == '__main__':
    compose.main(OUT, seed=297, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'fixed_peak', d['meta'].get('fixed_peak'),
          '| K0 %.3f、同じファ %.1f、一節 (夢) %.1f、終止 %.1f・%.1f・%.1f、終わりの一節 %.1f・%.1f・%.1f〜%.1f' % (K0, HINGE, T_R2, T_R3 - L3, T_C2, T_C3, T_M, T_M2, T_M3, T_M3 + L2))
    for k, e in enumerate(d['extras']): print('  %2d %7.2f - %7.2f s  gain %.3f  off %6.2f  fin %.2f fout %.2f  lane %d  %s' % (k, e['t'], e['t'] + e['d'], e['gain'], e['off'], e['fin'] or 0, e['fout'] or 0, e['lane'], e['tag']))
