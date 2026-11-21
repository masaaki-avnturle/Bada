#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCXCVI · Tre gradini verso il sonno (眠りへの 3 段 — calma の声・トラック 18・トラック 8・2 つの鍵盤の録音・tablet89 をミックス)
  届いたもの: 20261108_145525_aureola_sensuale_calma.mp3 (calma の声)、18 トラック 18.wma、08 トラック 8.wma、20261120_024046.mp3・20261121_041625.mp3 (2 つの鍵盤の録音)、
    tablet89.mp4。どれも前と同じファイル。依頼は「睡眠導入剤の効く洗脳的に曲をミックスして」。曲は薬ではない。言葉が指している向き (眠りへ) を、音の言葉に直した。
    声を作り換える依頼ではないので、声は届いたまま使う。楽器は何も加えない
  眠りへ下りる 3 つの段 — 段ごとに、調が半音ずつ下がり、祈りの言葉がゆっくりになり、音量が下がる:
    I.   Veglia (目覚めている)  ニ短調     声 (2 小節から) とトラック 18 (4 小節から; 出だしのラメントの低音を 3 回、少しずつ大きく → そのまま曲へ; tablet265 の入り方)。
                               声の終わりに、祈りの言葉 (tablet89 の主題の出だし、元の高さ = ヘ長調のミ・レ・ド; 8 秒) が 3 回、少しずつ遠く。ファに着く
    II.  Notte (夜)            変ニ長調   同じファから、11/20 の鍵盤の黒い鍵盤の夜。祈りの言葉 (4 半音下げて = 変ニ長調; 10.1 秒) が 3 回、そのまま Requiem I。
                               11/21 の鍵盤が答える。Requiem I が閉じると、11/20 の鍵盤だけ
    III. Sogno (夢)            ハ長調     同じファから白い鍵盤へ (2 つの鍵盤)。4 小節後にトラック 8 (元の高さ = ハ長調 / イ短調)。ここから終わりまで、つまみを少しずつ下げていく
    IV.  Sonno (眠り)                     ド・ミの終止が 3 回、少しずつ遠く。祈りの言葉 (5 半音下げて = ハ長調のミ・レ・ド; 10.7 秒) が 3 回、少しずつ遠く。Amen (2 半音下げて) が下で消える
  つなぐ音はファ (これまでと同じ): ヘ長調のド → 変ニ長調のミ → ハ長調のファ。祈りの言葉の伸ばした音は ラ → ファ → ミ と下がる
  声は 1 回だけ (初めの 3 分; 眠りへ誘って、あとは曲に任せる)。声は synth.py の faithful の経路 (ステレオのまま、帯域を削らず、全体の残響を掛けずに前に)。
    calma の声は静かに話し始めるので、初めの 82 秒だけ、つまみで持ち上げる (5 段; tablet276・287 は 2 段)
  鍵盤の録音は速さも高さもそのまま (tablet282 のしっとりの仕上げ)。トラック 18・トラック 8 も元の高さのまま。tablet89 だけ、テープのように速さごと移す
  仕上げは歪ませない (synth.py の linear_master)
  使い方: python compose_tablet296.py <wav のフォルダ (20261108_145525.wav = calma の声, 20261107_180000.wav = トラック 18, 20261107_080000.wav = トラック 8,
          20261120_024046.wav・20261121_041625.wav = soften282.py を通した鍵盤の録音, 20261107_089000.wav = tablet89 の音)> <chords296.json (analyze_chords.py の出力)> [score_tablet296.json]
"""
import sys, os, json, math
import numpy as np
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet296.json'
E = lambda k, v: float(os.environ.get(k, v))
GV = E('GV', '0.95')                                        # 声の音量 (tablet287 と同じ倍率; 仕上げの基準が違うので、少し小さく出る)
VLIFT = [(0.0, 5.5), (30.0, 4.0), (42.0, 2.5), (60.0, 1.5), (72.0, 0.7), (82.0, 0.0)]   # 静かな話し始めの持ち上げ: (録音の秒, dB)。calma の声は初めの 30 秒が 6 dB 小さく、80 秒までに少しずつ大きくなる。
                                                            #   tablet276・287 は 2 か所で切って持ち上げた (×1.7・×1.25); 今回は 5 段に分けて、3 秒のクロスフェードで滑らかに (40〜50 秒が大きく出ないように)
G18 = E('G18', '0.12')                                      # トラック 18 (声の下で)
LOOP_18 = (0.36, 0.54, 0.75)                                # トラック 18 の出だしの 3 回 — 少しずつ大きく (tablet265 と同じ比)
GA, GB = E('GA', '0.233'), E('GB', '0.232')                 # 鍵盤の音量 (tablet282 と同じ)
NIGHT, NIGHT_B = E('NIGHT', '0.90'), E('NIGHT_B', '0.71')   # 夜の段のつまみ: 11/20 の鍵盤 / 11/21 の鍵盤の答え
DUCK1, DUCK2 = E('DUCK1', '0.25'), E('DUCK2', '0.125')      # B が黒い鍵盤へ寄り道する 2 か所のつまみ
G08 = E('G08', '0.30')                                      # トラック 8 (夢の段)
G89F, G89A, G89L, G89C = E('G89F', '0.13'), E('G89A', '0.16'), E('G89L', '0.28'), E('G89C', '0.30')   # tablet89: 元の高さ / 4 半音下げて / 5 半音下げて / Amen
LOOP_F = (1.00, 0.75, 0.55)                                 # 祈りの言葉 (元の高さ) の 3 回 — 少しずつ遠く
LOOP_P = (0.45, 0.65, 0.85)                                 # 祈りの言葉 (4 半音下げて) の 3 回 — 少しずつ大きく、そのまま Requiem I へ (tablet285 と同じ)
LOOP_E = E('LOOP_E', '0.50')                                # 11/20 の鍵盤が自分で休む 2 秒を、祈りの言葉が 1 回埋める (tablet287 と同じ)
LOOP_C = (1.00, 0.75, 0.55)                                 # 終止の 3 回 — 少しずつ遠く (tablet286〜290 は少しずつ大きく)
LOOP_L = (1.00, 0.78, 0.62)                                 # 祈りの言葉 (5 半音下げて) の 3 回 — 少しずつ遠く
F0, FSTEP, FGAP, FXS = E('F0', '-4.0'), E('FSTEP', '-1.5'), 45.0, 6.0   # 夢の段のつまみ: 同じファで F0 dB、そこから FGAP 秒ごとに FSTEP dB ずつ (FXS 秒かけて)
FIXPEAK = E('FIXPEAK', '1.0')                               # 仕上げの基準 (linear_master; 山 × 1.2515 ÷ FIXPEAK が 1 を超えないこと)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, R18, R08, RA, RB, R89 = '20261108_145525', '20261107_180000', '20261107_080000', '20261120_024046', '20261121_041625', '20261107_089000'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
COLV, COL18, COL8, COLA, COLB, COL89, COLR = (255, 214, 150), (120, 190, 250), (110, 210, 190), (150, 195, 240), (245, 215, 150), (200, 180, 240), (250, 235, 190)
# 声 (calma): ファイルの 4.86 秒から (話し始めは 5.36 秒、話し終わりは 196.5 秒)
V_OFF, V_ON, V_LEN = 4.86, 5.36, 198.46
V1 = 8.0 - (V_ON - V_OFF)                       # 7.5: 2 小節 (8 秒) から話し始める
# I. トラック 18 (tablet265 と同じ入り方)
G_OFF, G_DUR, G_PER, T18_LEN = 0.70, 14.8, 14.7, 149.07    # 出だしの一節: 録音の 0.70 秒から 14.8 秒ぶん、くり返しの周期 14.7 秒
G_T0 = 16.0                                     # 1 回目: 4 小節から
TP = G_T0 + 3 * G_PER                           # 60.1: 4 回目の出だし = そのまま曲へ (録音の 142.5 秒 = 曲の 201.9 秒に鳴り終わる)
P, OV = 8.0, 0.3                                # 祈りの言葉: tablet89 の元の 8 秒から 8 秒
T_F = E('T_F', '188.0')                         # 祈りの言葉、元の高さ (ヘ長調) で 3 回 — 声の終わりからトラック 18 の終わりへ。3 回目はファに着いて、夜へ渡す
# II. 夜 (tablet285〜290 と同じ置き方)
LA0 = 5.10
K0 = 212.0 - 5.232                              # 206.768: 11/20 の鍵盤の最初の和音 (ファ・変ホ、録音の 5.232 秒) が 53 小節 (212 秒) に鳴る — A の録音の f 秒は曲の f + 206.768 秒
A_END, A_FADE = 553.0, 1.4
B_ON = 3.0
B0 = K0 + 59.0                                  # B の黒い鍵盤の出だし
B_OPEN, B_F = 58.40, 58.45
X1 = 301.013 - 58.585                           # 242.428: B のファを A のファに合わせる
HOLD = 22.0
B1 = K0 + X1; B2 = B1 + HOLD
P_END, P_START = 139.0, 142.9
E0, E1, XE0, XE1 = 111.3, 121.0, 0.4, 0.25
C0, C1, XC = 227.93, 232.90, 0.12
LC0, LC1, OVC = 286.60, 288.80, 0.12            # 終止
L3 = LC1 - LC0
B_CUT, B_FOUT = 288.90, 0.45
T_R3 = B2 + LC1                                 # 760.0
S_N = -4; L_N = P / RATE(S_N)                   # 4 半音下げて (変ニ長調)、10.08 秒
T1 = K0 + 13.0                                  # 219.8: 祈りの 1 回目 (A の最初の音の 8 秒後)
T_CONT = T1 + 3 * L_N                           # 250.0: 4 回目からそのまま Requiem I (元の 96 秒まで)
N_END = 96.0
T_E = K0 + 165.0                                # 371.8: A が自分で休む 2 秒を、祈りの言葉が 1 回埋める
# III. 夢
HINGE = K0 + 301.013                            # 507.8: 同じファ
T8 = HINGE + 16.0 - 0.70                        # トラック 8 の最初の音が、同じファの 4 小節後に鳴る (鍵盤との濁りの指数 0.29; どこに置いても 0.29〜0.32)
T8_END = 240.0                                  # トラック 8 は録音の 239 秒に鳴り終わる
FADE = [(HINGE - 3.0, F0)] + [(HINGE + k * FGAP, F0 + k * FSTEP) for k in range(1, 6)]   # 眠りへの下り: (曲の秒, dB)
def fade_db(t):
    d = 0.0
    for tt, db in FADE:
        if t >= tt: d = db
    return d
# IV. 眠り
S_AM, AM_OFF = -2, 373.5                        # Amen: 2 半音下げて (ハ長調)
T_AM = T_R3 + L3 + (552.3 - X1 - HOLD - LC0)    # 3 回目のド・ミに合わせて開く (tablet287・289 と同じ)
S_LO = -5; L_LO = P / RATE(S_LO)                # 低い祈り: 5 半音下げて (ハ長調のミ・レ・ド)、10.68 秒
T_LO = T_AM + 2.7                               # Amen の 2.7 秒後から (tablet285・289 の高い祈りと同じ所; 今回は低く、ゆっくり)
S2, S3, S4, TOTAL = 53, 127, 190, 202
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None, faithful=False):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout, faithful=faithful, env=None)
def stretch(rid, T0, a, b, base, lane, color, tag, marks=(), fin=0.1, fout=1.5, sched=True, faithful=False):
    """録音の a〜b 秒を、録音の 0 秒が曲の T0 秒に来るように置く。marks = [(録音の秒, そこからの倍率, 動かす時間)] (B の寄り道など)。
      sched: 眠りへの下り (FADE) も掛ける — 段の境目やほかの印から 18 秒以上離れた所だけ、同じ録音どうしのクロスフェード (FXS 秒) で 1 段下げる"""
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
I18 = len(PLAYS)
for k, g in enumerate(LOOP_18):                 # I. トラック 18 の出だしを 3 回、少しずつ大きく (声の下で)
    PLAYS.append(play(R18, G_T0 + k * G_PER, G18 * g, 0, G_OFF, G_DUR, 1, COL18, 'トラック 18 — 出だしの一節 (%d 回目)' % (k + 1), fin=5.0 if k == 0 else 0.05, fout=0.25))
PLAYS.append(play(R18, TP, G18, 0, G_OFF, T18_LEN - G_OFF, 1, COL18, 'トラック 18 — 4 回目からそのまま曲へ (声の下で)', fin=0.05, fout=0.05))
for k, g in enumerate(LOOP_F):                  # 祈りの言葉 (元の高さ = ヘ長調) が 3 回、少しずつ遠く
    PLAYS.append(play(R89, T_F + k * P, G89F * g, 0, P, P + OV, 3, COLR, 'tablet89 — 祈りの言葉、元の高さ (%d 回目)' % (k + 1), fin=1.5 if k == 0 else OV, fout=2.0 if k == 2 else OV))
IA = len(PLAYS)                                 # II・III. 11/20 の鍵盤: 夜から、夢の段で少しずつ下がって、最後の音まで
PLAYS += stretch(RA, K0, LA0, A_END, GA * NIGHT, 2, COLA, '11/20 02:40 の鍵盤 — 黒い鍵盤の夜 (同じファから)', fin=0.1, fout=A_FADE)
IB = len(PLAYS)
PLAYS.append(play(RB, B0 + B_ON, GB * NIGHT_B, 0, B_ON, B_OPEN - B_ON, 3, COLB, '11/21 04:16 の鍵盤 — 黒い鍵盤の出だしが答える', fin=0.6, fout=0.25))
PLAYS += stretch(RB, B1, B_F, P_END, GB * NIGHT, 3, COLB, '11/21 04:16 の鍵盤 — 同じファから白い鍵盤へ', marks=[(E0, DUCK1, XE0), (E1, 1.0, XE1)], fin=0.1, fout=1.5)
PLAYS += stretch(RB, B2, P_START, LC1 + OVC, GB * NIGHT, 3, COLB, '11/21 04:16 — 休んでから、続き', marks=[(C0, DUCK2, XC), (C1, 1.0, XC)], fin=0.3, fout=OVC)
GC = GB * NIGHT * 10 ** (fade_db(T_R3) / 20.0)  # 終止の 3 回 — 少しずつ遠く (1 回目は上の続きの終わり)
PLAYS += [play(RB, T_R3, GC * LOOP_C[1], 0, LC0, L3 + OVC, 3, COLR, '11/21 の鍵盤 — 終止をもう一度 (2 回目、遠く)', fin=OVC, fout=OVC),
          play(RB, T_R3 + L3, GC * LOOP_C[2], 0, LC0, B_CUT - LC0, 3, COLR, '終止 (3 回目、もっと遠く)', fin=OVC, fout=B_FOUT)]
I89 = len(PLAYS)
for k, g in enumerate(LOOP_P):                  # 祈りの言葉 (4 半音下げて = 変ニ長調) を 3 回、そのまま Requiem I へ
    PLAYS.append(play(R89, T1 + k * L_N, G89A * g, S_N, P, P + OV, 4, COL89, 'tablet89 — 祈りの言葉、4 半音下げて (%d 回目)' % (k + 1), fin=3.0 if k == 0 else OV, fout=OV))
PLAYS.append(play(R89, T_CONT, G89A, S_N, P, N_END - P, 4, COL89, 'tablet89 — 4 回目からそのまま: Requiem I (4 半音下げて)', fin=OV, fout=3.0))
PLAYS.append(play(R89, T_E, G89A * LOOP_E, S_N, P, P, 4, COL89, 'tablet89 — 祈りの言葉がもう一度 (鍵盤が休む所で、1 回)', fin=1.2, fout=2.4))
I08 = len(PLAYS)                                # III. トラック 8: 元の高さのまま、少しずつ下がって、自分の終わりまで
PLAYS += stretch(R08, T8, 0.0, T8_END, G08, 1, COL8, 'トラック 8 — 元の高さのまま (白い鍵盤の上で)', fin=0.03, fout=0.05)
IAM = len(PLAYS)                                # IV. Amen と低い祈り
PLAYS.append(play(R89, T_AM, G89C * 10 ** (fade_db(T_AM) / 20.0), S_AM, AM_OFF, 391.0 - AM_OFF, 4, COL89, 'tablet89 — Amen、2 半音下げて (ハ長調)', fin=1.5, fout=3.0))
for k, g in enumerate(LOOP_L):
    PLAYS.append(play(R89, T_LO + k * L_LO, G89L * g * 10 ** (fade_db(T_LO) / 20.0), S_LO, P, P + OV, 1, COLR, 'tablet89 — 祈りの言葉、5 半音下げて (%d 回目)' % (k + 1), fin=1.5 if k == 0 else OV, fout=3.0 if k == 2 else OV))
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍): トラック 18 → 11/20 の鍵盤 → 終わりは 11/21 の終止と低い祈り
LEAD = [(I18 + k, G_T0 + k * G_PER) for k in range(3)] + [(I18 + 3, TP)] + [(i, PLAYS[i]['beat']) for i in range(IA, IB)] + [(IAM + 1, T_LO + 1.5)]
def shift_chord(name, semis):
    i = 2 if len(name) > 1 and name[1] in '#b' else 1
    return compose.NAMES[(PC[name[:i]] + semis) % 12] + name[i:]
def harm_at(q):
    cur = 'Dm'
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
    P_.section(0, 'I. Veglia — 声が先に、トラック 18 がそっと (♩=60)', '2 小節から声。4 小節からトラック 18 の出だしが 3 回、そのまま曲へ。3 分 8 秒から祈りの言葉 (ヘ長調) が 3 回、遠ざかる')
    P_.section(S2, 'II. Notte — 同じファから、黒い鍵盤の夜', '3 分 32 秒、11/20 の鍵盤。祈りの言葉 (変ニ長調) が 3 回、そのまま Requiem I。11/21 の鍵盤が答える')
    P_.section(S3, 'III. Sogno — 同じファから白い鍵盤へ、トラック 8', '8 分 28 秒に同じファ。4 小節後にトラック 8。ここから少しずつ小さく')
    P_.section(S4, 'IV. Sonno — 遠ざかって、眠りへ', 'ド・ミで 3 回閉じる (少しずつ遠く)。祈りの言葉 (ハ長調) が低く、ゆっくり、3 回')
    return P_

def post(P_, events, ex):
    for p in PLAYS:
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm)
        kw = dict(lane=p['lane'], color=list(p['color']), env=p['env'] or c.get('env'), env_dt=c.get('env_dt', 0.05) / r, env_off=off / r, env_faded=bool(p['env']))
        if p['faithful']:   # 声: ステレオのまま、帯域を削らず、全体の残響を掛けずに前に (声の残響は声の中にある)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:               # 鍵盤・トラック・tablet89: tablet282 と同じ重ね方 (全体の残響)。tablet89 の移調はテープのように速さごと
            add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [8.0, 2.0, 0.4], 'linear_master': True, 'fixed_peak': FIXPEAK,
        'title': 'Requiem BADA — CCXCVI · Tre gradini verso il sonno',
        'subtitle': 'calma の声・トラック 18 と 8・2 つの鍵盤・tablet89。眠りへの 3 段。ニ短調 → 変ニ長調 → ハ長調、♩=60',
        'footer': ['段ごとに、調が半音ずつ下がり (ニ短調 → 変ニ長調 → ハ長調)、祈りの言葉がゆっくりになり (8 秒 → 10.1 秒 → 10.7 秒)、音量が下がる。',
                   '声は初めの 3 分だけ (届いたまま)。つなぐ音は同じファ。鍵盤とトラックは速さも高さもそのまま。楽器は何も加えない。',
                   '同じ形を 3 回ずつ: トラック 18 の出だし、祈りの言葉 (3 つの調で)、終止。曲は薬ではない。%d 小節。' % TOTAL]}

if __name__ == '__main__':
    compose.main(OUT, seed=296, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'fixed_peak', d['meta'].get('fixed_peak'), '| K0 %.3f、同じファ %.1f、トラック 8 %.1f、終止 %.1f、Amen %.1f、低い祈り %.1f〜%.1f' % (K0, HINGE, T8, T_R3, T_AM, T_LO, T_LO + 3 * L_LO))
    for k, e in enumerate(d['extras']): print('  %2d %7.2f - %7.2f s  gain %.3f  semis %+d  off %6.2f  fin %.2f fout %.2f  lane %d  %s' % (k, e['t'], e['t'] + e['d'], e['gain'], e['semis'], e['off'], e['fin'] or 0, e['fout'] or 0, e['lane'], e['tag']))
