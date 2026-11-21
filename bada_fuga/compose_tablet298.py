#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCXCVIII · Sogno lucido della Notte Santa (聖夜の明晰夢 — 上の曲 CCXCVII に、tablet89 のレクイエムとフーガを重ねて)
  届いたもの: 新しい音は無い。依頼の言葉は「上で作ってくれている曲を、この能力 (先読みと予知; 明晰夢でも; 仕切りと瞑想の状態) に応じる曲に合わせて。
    フーガにレクイエムを聖夜に洗脳して、優しさに満ちた曲を」。上の曲 = CCXCVII (calma の声と 2 つの鍵盤の録音)。フーガとレクイエム = tablet89 (LXXXIX — Requiem e Fuga; 今朝届いたもの)。
    曲は薬ではない。先読みや予知の力そのものを音で作ることもできない。言葉が指している形を、音の言葉に直した。声は届いたまま。楽器は何も加えない。鍵盤は速さも高さもそのまま
  言葉 → 音:
    先読み              フーガ (tablet89 のフーガ I): 主題が 1 声で鳴り、次の声が同じ主題で入る — 聞いた言葉が、次に来る。その主題の頭 (ラ・ソ・ファ) は、レクイエム I の中で先に小さく鳴っている
                        (tablet89 がそう書かれている)。その頭の一節を 3 回、少しずつ大きく → そのままレクイエム I → フーガ I (これまでの「祈りの言葉」は、フーガの主題の頭だった)
    予知                これから来る音が、先に小さく聞こえる: (1) フーガの主題の頭が 3 回 (フーガの 2 分 21 秒前から) (2) 白い鍵盤へ移るファが 1 回 (同じファの 4 小節前)
                        (3) 曲の終わりの終止 (シ・ファ、レ → ド・ミ・ソ) が 3 回、夢の段の途中で小さく (本当の終止の 2 分 47 秒前から)
    明晰夢でも          夢の段 (白い鍵盤) の中で、声がもう一度話す (眠りの曲 CCXCVII では、声は初めだけだった)。終わりの予告 (3) は、その夢の段の中で聞こえる
    仕切り              段落を 8 つ、小節の線にそろえる。境目には同じ印: 同じファ、3 回のくり返し
    瞑想の状態          ゆっくりした脈 (4 半音下げた tablet89 は ♩=48)、同じ言葉が回る、山を作らない、段落ごとの大きさをそろえる
    フーガにレクイエムを レクイエム I とフーガ I (4 半音下げて、変ロ短調) を黒い鍵盤の夜に。終わりは、同じ主題の頭が低く 3 回 (5 半音下げて = ハ長調のミ・レ・ド) と Amen — フーガの主題が祈りに戻る
    聖夜                黒い鍵盤の小さな音で始まる夜 (tablet282 のしっとりの仕上げ)
    洗脳                同じ形を 3 回ずつ: 11/20 の出だし、主題の頭 (夜)、終止の予告、終止、主題の頭 (終わり)
    優しさに満ちた      calma の声 (優しい声) が初めと夢の段に。声の間は伴奏を下げる。やわらかい打鍵。終止の 3 回は同じ大きさ。ハ長調の Amen で静かに閉じる
  形 (♩=60、1 小節 = 4 秒):
    I.    Notte           2 小節から声。4 小節から 11/20 の鍵盤の出だしが 3 回、そのまま先へ
    II.   Requiem         主題の頭が 3 回 (4 半音下げて)、そのままレクイエム I。11/21 の鍵盤が答える
    III.  Fuga            フーガ I。声が終わり、11/20 の鍵盤が流れ始める
    IV.   Sola            tablet89 が閉じて、11/20 の鍵盤だけ。ファが先に 1 回
    V.    Sogno lucido    同じファから白い鍵盤へ、2 つの鍵盤。声がもう一度
    VI.   Presagio        11/21 が休む間に、終わりの終止が 3 回、先に小さく
    VII.  Insieme         また 2 つで。声が終わり、山へ
    VIII. Amen            ド・ミ・ソで 3 回閉じる。Amen (ハ長調)。主題の頭が低く 3 回、遠ざかる
  置き方は CCLXXXVII (声・2 つの鍵盤・tablet89) と同じ時間。声の持ち上げと歪ませない仕上げは CCXCVI・CCXCVII と同じ
  使い方: python compose_tablet298.py <wav のフォルダ (20261108_145525.wav = calma の声, 20261120_024046.wav・20261121_041625.wav = soften282.py を通した鍵盤の録音,
          20261107_089000.wav = tablet89 の音)> <chords298.json (analyze_chords.py の出力)> [score_tablet298.json]
"""
import sys, os, json, math
import numpy as np
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet298.json'
E = lambda k, v: float(os.environ.get(k, v))
GV, GV2 = E('GV', '0.95'), E('GV2', '1.00')                 # 声の音量 (1 回目 / 2 回目も同じ倍率; CCLXXXVII は 2 回目を 1.15 倍にしたが、今回は伴奏の方を下げる)
VLIFT = [(0.0, 5.5), (30.0, 4.0), (42.0, 2.5), (60.0, 1.5), (72.0, 0.7), (82.0, 0.0)]   # 静かな話し始めの持ち上げ: (録音の秒, dB)、3 秒のクロスフェードで (CCXCVI・CCXCVII と同じ)
BED, BED2, SOLO = E('BED', '0.63'), E('BED2', '0.50'), E('SOLO', '1.12')   # 伴奏のつまみ: 声が話している間 (1 回目 / 2 回目は鍵盤が 2 つなので、もっと下げる) / 声が休んでいる間
GA, GB = E('GA', '0.233'), E('GB', '0.232')                 # 鍵盤の音量 (tablet282 と同じ)
DUCK1, DUCK2 = E('DUCK1', '0.25'), E('DUCK2', '0.125')      # B が黒い鍵盤へ寄り道する 2 か所のつまみ
G89A, G89C, G89L = E('G89A', '0.16'), E('G89C', '0.40'), E('G89L', '0.21')   # tablet89: 4 半音下げて (レクイエム I・フーガ I) / Amen / 5 半音下げて (終わりの主題の頭)
LOOP_A = (0.50, 0.70, 0.85)                                 # 11/20 の出だしの 3 回 — 少しずつ大きく
LOOP_P = (0.45, 0.65, 0.85)                                 # 主題の頭 (4 半音下げて) の 3 回 — 少しずつ大きく、そのままレクイエム I へ
GPF = E('GPF', '0.80')                                      # 先に聞こえるファ (B のつまみに掛ける)
LOOP_Q = (E('Q1', '0.50'), E('Q2', '0.64'), E('Q3', '0.80'))   # 終止の予告の 3 回 — 少しずつはっきり (B のつまみに掛ける)
LOOP_C = (1.00, 1.00, 1.00)                                 # 終わりの終止の 3 回 — 同じ大きさで (優しく; CCLXXXVII と同じ)
LOOP_L = (1.00, 0.78, 0.62)                                 # 終わりの主題の頭 (5 半音下げて) の 3 回 — 少しずつ遠く
FIXPEAK = E('FIXPEAK', '1.00')                              # 仕上げの基準 (linear_master; 山 × 1.2515 ÷ FIXPEAK が 1 を超えないこと)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, RA, RB, R89 = '20261108_145525', '20261120_024046', '20261121_041625', '20261107_089000'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
COLV, COLA, COLB, COL89, COLR = (255, 214, 150), (150, 195, 240), (245, 215, 150), (200, 180, 240), (250, 235, 190)
# 声 (calma): ファイルの 4.86 秒から (話し始めは 5.36 秒、話し終わりは 196.5 秒)
V_OFF, V_ON, V_LEN = 4.86, 5.36, 198.46
# 鍵盤 (CCLXXXVII・CCXCVII と同じ置き方)
LA0, L1, OVA = 5.10, 12.634 - 5.232, 0.3        # 11/20 の出だしの一節: 録音の 5.10 秒から 7.402 秒
T_R1 = 16.10                                    # 1 回目: 最初の和音が 4 小節 (16.2 秒) に鳴る
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
HINGE = K0 + 301.013                            # 334.219: 同じファ
LC0, LC1, OVC = 286.60, 288.80, 0.12            # 終止: シ・ファ、レ、ド・ミ・ソ
L3 = LC1 - LC0
B_CUT, B_FOUT = 288.90, 0.45
T_R3 = B2 + LC1                                 # 586.43: 流れの中の 1 回目が終わる所。続けて 2 回
# 声の位置 (CCLXXXVII と同じ)
V1 = 8.0 - (V_ON - V_OFF)                       # 7.5: 1 回目は 2 小節 (8 秒) から話し始める
TK = K0 + 304.4                                 # 337.6: A が止まる所 (ファ、ド・ソの後)。2 回目はここで話し始める
V2 = TK - (V_ON - V_OFF)
# 伴奏のつまみを動かす所 (A の録音の秒): 1 回目の声が終わる所で戻し、2 回目の声の入りで下げ、終わりで戻す
AX1, XF1 = 162.3, 5.0                           # 162.3〜167.3 秒で戻す (声は A の 165.9 秒に話し終わる)
AX2, XF2 = 303.6, 1.8                           # 303.6〜305.4 秒で下げる (A が止まっている間)
AX3, XF3 = 497.5, 6.0                           # 497.5〜503.5 秒で戻す (2 回目の声は A の 495.5 秒に話し終わる; 急に大きくならないように 6 秒かけて)
BX3 = C1 + 0.5                                  # B も同じ 6 秒で戻す: 寄り道の和音 (小さくしてある) の後、いったん声の下の大きさで戻ってから
# tablet89 (ニ短調): テープのように速さごと移す
P, OV = 8.0, 0.3                                # 主題の頭 (これまでの「祈りの言葉」): 元の 8 秒から 8 秒 — 伸ばしたラの下を、ラ・ソ・ファ (フーガ I の主題の頭)
S_N = -4; R4 = RATE(S_N); L_N = P / R4          # 夜: 4 半音下げて (変ロ短調、0.794 倍速)、一節は 10.08 秒
T1 = K0 + 13.0                                  # 46.206: 主題の頭の 1 回目 (A の最初の音の 8 秒後)
T_CONT = T1 + 3 * L_N                           # 76.44: 4 回目からそのままレクイエム I (元の 96 秒まで) → フーガ I (元の 160 秒まで)
N_FUGA, N_END = 96.0, 160.0
T_FUGA = T_CONT + (N_FUGA - P) / R4             # 187.3: フーガ I の入り
T_NEND = T_CONT + (N_END - P) / R4              # 267.9: フーガ I の終わり
O1 = P + (K0 + AX1 - T_CONT) * R4; XO1 = XF1 * R4   # tablet89 のつまみも、A と同じ所 (曲の 195.5〜200.5 秒) で戻す — 元の秒に直して
S_AM, AM_OFF = -2, 373.5                        # Amen: 2 半音下げて (ハ長調)
T_AM = T_R3 + L3 + (552.3 - X1 - HOLD - LC0)    # 589.9: 3 回目のド・ミ・ソに合わせて開く (CCLXXXVII・CCXCVI と同じ)
S_LO = -5; L_LO = P / RATE(S_LO)                # 終わりの主題の頭: 5 半音下げて (ハ長調のミ・レ・ド)、10.68 秒
T_LO = T_AM + 2.7                               # Amen の 2.7 秒後から (CCXCVI と同じ)
# 予知: 先に小さく聞こえるもの
T_PF = E('T_PF', '318.25')                      # ファ (B の録音の 58.45 秒から 1.25 秒 — ファのオクターヴだけ): 同じファ (334.2 秒) の 4 小節前。316〜322 秒は濁りの指数 0.02〜0.08 (同じファの直前 330 秒から後は 0.44 以上)
PF_LEN, PF_FOUT = 1.25, 0.5
T_Q = (E('T_Q1', '417.0'), E('T_Q2', '425.25'), E('T_Q3', '433.5'))  # 終止の予告の 3 回 (11/21 が休む 414.6〜440.5 秒の間に; 8.25 秒おき — 同じ間合いで 3 回置ける中で、濁りの指数の平均がいちばん小さい: 0.29・0.35・0.35)
S2, S3, S4, S5, S6, S7, S8, TOTAL = 11, 46, 67, 83, 104, 110, 146, int(E('TOTAL', '160'))
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None, faithful=False):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout, faithful=faithful, env=None)
def stretch(rid, T0, a, b, base, lane, color, tag, marks=(), fin=0.1, fout=1.5, faithful=False):
    """録音の a〜b 秒を、録音の 0 秒が曲の T0 秒に来るように置く (速さはそのまま)。marks = [(録音の秒, そこからの倍率, 動かす時間)]: つまみは、同じ録音どうしのクロスフェードで動かす"""
    pts = [(a, 1.0, fin)] + sorted(marks); out = []
    for k, (o, m, xf) in enumerate(pts):
        nxt = pts[k + 1] if k + 1 < len(pts) else None; end = (nxt[0] + nxt[2]) if nxt else b
        out.append(play(rid, T0 + o, base * m, 0, o, end - o, lane, color, tag if k == 0 else '', fin=xf, fout=(nxt[2] if nxt else fout), faithful=faithful))
    c = CH[rid]; env = np.asarray(c['env']); t = np.arange(len(env)) * c.get('env_dt', 0.05); gg = np.full(len(env), out[0]['gain'])   # 画面の波形: 包絡に、つまみの動きを掛けておく (継ぎ目で途切れて見えないように)
    for k in range(1, len(out)):
        a0, a1 = out[k - 1]['gain'], out[k]['gain']; gg = np.where(t >= out[k]['off'], a0 + (a1 - a0) * np.clip((t - out[k]['off']) / max(out[k]['fin'], 1e-6), 0.0, 1.0), gg)
    envp = [round(float(v), 4) for v in env * gg / max(q['gain'] for q in out)]
    for q in out: q['env'] = envp
    return out
def voice(T, g, tag):                           # 声: 届いたまま。静かな話し始めだけ、つまみで持ち上げる (5 段、3 秒のクロスフェード)
    return stretch(RV, T - V_OFF, V_OFF, V_LEN, g * 10 ** (VLIFT[0][1] / 20.0), 0, COLV, tag, marks=[(o, 10 ** ((db - VLIFT[0][1]) / 20.0), 3.0) for o, db in VLIFT[1:]], fin=0.3, fout=2.0, faithful=True)

PLAYS = voice(V1, GV, 'calma の声 — 届いたまま (2 小節から)')
IL = len(PLAYS)
for k, g in enumerate(LOOP_A):                  # I. 11/20 の出だしを 3 回、少しずつ大きく (声の下で)
    PLAYS.append(play(RA, T_R1 + k * L1, GA * BED * g, 0, LA0, L1 + OVA, 4, COLR, '11/20 の鍵盤 — 出だしの一節 (%d 回目)' % (k + 1), fin=0.1 if k == 0 else OVA, fout=OVA))
IA = len(PLAYS)                                 # A (4 回目から): 声の間は下げて、声が休む間は戻す
PLAYS += stretch(RA, K0, LA0, A_END, GA * BED, 1, COLA, '11/20 02:40 の鍵盤 — 4 回目からそのまま (声の下で、小さめに)',
                 marks=[(AX1, SOLO / BED, XF1), (AX2, BED2 / BED, XF2), (AX3, SOLO / BED, XF3)], fin=OVA, fout=A_FADE)
IB = len(PLAYS)
PLAYS.append(play(RB, B0 + B_ON, GB * BED, 0, B_ON, B_OPEN - B_ON, 2, COLB, '11/21 04:16 の鍵盤 — 黒い鍵盤の出だしが答える', fin=0.6, fout=0.25))
PLAYS.append(play(RB, T_PF, GB * SOLO * GPF, 0, B_F, PF_LEN, 4, COLR, '11/21 の鍵盤 — ファが先に 1 回 (予告)', fin=0.05, fout=PF_FOUT))
PLAYS += stretch(RB, B1, B_F, P_END, GB * BED2, 2, COLB, '11/21 04:16 の鍵盤 — 同じファから白い鍵盤へ (声の下で)', marks=[(E0, DUCK1, XE0), (E1, 1.0, XE1)], fin=0.1, fout=1.5)
for k, (t, g) in enumerate(zip(T_Q, LOOP_Q)):   # VI. 終わりの終止が、先に 3 回、小さく (11/21 が休む間に、声の下で)
    PLAYS.append(play(RB, t, GB * BED2 * g, 0, LC0, B_CUT - LC0, 4, COLR, '11/21 の鍵盤 — 終わりの終止が先に聞こえる (予告、%d 回目)' % (k + 1), fin=OVC, fout=B_FOUT))
PLAYS += stretch(RB, B2, P_START, LC1 + OVC, GB * BED2, 2, COLB, '11/21 04:16 — 休んでから、続き', marks=[(C0, DUCK2, XC), (C1, 1.0, XC), (BX3, SOLO * LOOP_C[0] / BED2, XF3)], fin=0.3, fout=OVC)
IC = len(PLAYS)                                 # VIII. 終止をもう 2 回 (同じ大きさで)
PLAYS += [play(RB, T_R3, GB * SOLO * LOOP_C[1], 0, LC0, L3 + OVC, 4, COLR, '11/21 の鍵盤 — 終止をもう一度 (2 回目)', fin=OVC, fout=OVC),
          play(RB, T_R3 + L3, GB * SOLO * LOOP_C[2], 0, LC0, B_CUT - LC0, 4, COLR, '終止 (3 回目)', fin=OVC, fout=B_FOUT)]
I89 = len(PLAYS)
for k, g in enumerate(LOOP_P):                  # II. 主題の頭 (4 半音下げて) を 3 回、少しずつ大きく (声の下で)
    PLAYS.append(play(R89, T1 + k * L_N, G89A * BED * g, S_N, P, P + OV, 3, COL89, 'tablet89 — フーガの主題の頭、4 半音下げて (%d 回目)' % (k + 1), fin=3.0 if k == 0 else OV, fout=OV))
PLAYS += [play(R89, T_CONT, G89A * BED, S_N, P, O1 + XO1 - P, 3, COL89, 'tablet89 — 4 回目からそのまま: レクイエム I (4 半音下げて)', fin=OV, fout=XO1),
          play(R89, T_CONT + (O1 - P) / R4, G89A * SOLO, S_N, O1, N_END - O1, 3, COL89, 'tablet89 — フーガ I (声が終わって、前へ)', fin=XO1, fout=3.0)]
IAM = len(PLAYS)                                # VIII. Amen と、終わりの主題の頭
PLAYS.append(play(R89, T_AM, G89C * SOLO, S_AM, AM_OFF, 391.0 - AM_OFF, 3, COL89, 'tablet89 — Amen、2 半音下げて (ハ長調)', fin=1.5, fout=3.0))
for k, g in enumerate(LOOP_L):
    PLAYS.append(play(R89, T_LO + k * L_LO, G89L * SOLO * g, S_LO, P, P + OV, 4, COLR, 'tablet89 — 主題の頭、5 半音下げて (%d 回目、遠ざかる)' % (k + 1), fin=1.5 if k == 0 else OV, fout=3.0 if k == 2 else OV))
PLAYS += voice(V2, GV * GV2, 'calma の声 — もう一度 (夢の段で)')
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍): A の出だしの 3 回 → A。終わりは弾かれた音から (ト → ハ)
LEAD = [(IL + k, T_R1 + k * L1) for k in range(3)] + [(i, PLAYS[i]['beat']) for i in range(IA, IB)]
OVR = [(t + d, n) for t in (T_R3 - L3, T_R3, T_R3 + L3) for d, n in ((0.15, 'G'), (1.50, 'C'))]
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
    P_.section(0, 'I. Notte — 声が先に、黒い鍵盤の小さな音 (♩=60)', '2 小節から声。4 小節から 11/20 の鍵盤の出だしが 3 回、そのまま先へ')
    P_.section(S2, 'II. Requiem — フーガの主題の頭が 3 回、先に', '46 秒から主題の頭が 3 回、そのままレクイエム I。1 分 35 秒から 11/21 の鍵盤が答える')
    P_.section(S3, 'III. Fuga — 先に聞いた主題が、声を重ねて', '3 分 7 秒からフーガ I。声は 3 分 19 秒まで。11/20 の鍵盤が流れ始める')
    P_.section(S4, 'IV. Sola — 鍵盤だけ、ファへ', 'フーガが閉じて、11/20 の鍵盤だけ。5 分 18 秒に、ファが先に 1 回')
    P_.section(S5, 'V. Sogno lucido — 同じファから白い鍵盤へ、声がもう一度', '5 分 34 秒に同じファ。5 分 38 秒から声をもう一度')
    P_.section(S6, 'VI. Presagio — 終わりの終止が、先に 3 回', '11/21 が休む間に、終わりの終止が小さく 3 回')
    P_.section(S7, 'VII. Insieme — また 2 つで', '声は 8 分 49 秒まで。9 分 25 秒に山')
    P_.section(S8, 'VIII. Amen — 先に聞いた終止で閉じる', 'ド・ミ・ソで 3 回閉じる。Amen。主題の頭が低く 3 回、遠ざかる')
    return P_

def post(P_, events, ex):
    for p in PLAYS:
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm)
        kw = dict(lane=p['lane'], color=list(p['color']), env=p['env'] or c.get('env'), env_dt=c.get('env_dt', 0.05) / r, env_off=off / r, env_faded=bool(p['env']))
        add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=sm, rid=rid + '.wav', tag=p['tag'],
            **(dict(faithful=True) if p['faithful'] else {}), **kw)   # 声: faithful (帯域を削らず、全体の残響を掛けずに前に)。鍵盤・tablet89: tablet282 と同じ重ね方。tablet89 の移調はテープのように速さごと

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [8.0, 2.0, 0.4], 'linear_master': True, 'fixed_peak': FIXPEAK,
        'title': 'Requiem BADA — CCXCVIII · Sogno lucido della Notte Santa',
        'subtitle': 'calma の声・2 つの鍵盤・tablet89。聖夜のフーガとレクイエム。変ロ短調 → ハ長調、♩=60',
        'footer': ['これから来る音が、先に小さく聞こえる: フーガの主題の頭 (3 回)、白い鍵盤へ移るファ (1 回)、曲の終わりの終止 (3 回)。',
                   '声は 2 回 (夜と、夢の段)。同じ形を 3 回ずつ。段落は 8 つ、境目は同じファ。鍵盤は速さも高さもそのまま。楽器は何も加えない。',
                   'tablet89 はテープのように移す (夜は 4 半音下げて、終わりは 5 半音・2 半音下げてハ長調)。曲は薬ではない。%d 小節。' % TOTAL]}

if __name__ == '__main__':
    compose.main(OUT, seed=298, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'fixed_peak', d['meta'].get('fixed_peak'),
          '| K0 %.3f、主題の頭 %.1f、レクイエム I %.1f、フーガ I %.1f〜%.1f、ファの予告 %.1f、同じファ %.1f、声 2 回目 %.1f、終止の予告 %s、終止 %.1f、Amen %.1f、主題の頭 (終わり) %.1f〜%.1f' % (
              K0, T1, T_CONT, T_FUGA, T_NEND, T_PF, HINGE, V2 + V_ON - V_OFF, '・'.join('%.1f' % t for t in T_Q), T_R3 - L3, T_AM, T_LO, T_LO + 3 * L_LO))
    for k, e in enumerate(d['extras']): print('  %2d %7.2f - %7.2f s  gain %.3f  semis %+d  off %6.2f  fin %.2f fout %.2f  lane %d  %s' % (k, e['t'], e['t'] + e['d'], e['gain'], e['semis'], e['off'], e['fin'] or 0, e['fout'] or 0, e['lane'], e['tag']))
