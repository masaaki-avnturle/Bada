#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXXIV · Mantra della Notte Santa (2 つの鍵盤の録音と tablet89 をミックス — 聖夜に、洗脳的で気持ちよく、ホッとして、頭に仕切りができる曲に)
  届いた言葉は薬にたとえた気分 (CCLXXXIII と同じ言葉に、聖夜・洗脳的・気持ちよく・胸がホッとする、が加わった)。薬の働きを音で作ることはできないので、
  言葉が指している気分を音の言葉に直した:
    聖夜                                 → 黒い鍵盤の小さな音で始まる夜 (tablet282 のしっとりの仕上げ)。2 小節の無音、2 小節から鍵盤、4 小節から主題
    洗脳的で、気持ちよく                 → tablet89 の主題の出だし (2 小節: 伸ばしたラの下を、ラ・ソ・ファと下りていく 3 つの音) が、3 回ずつ回る。
                                            夜は 4 半音下げて (ファ・変ホ・変ニ、ゆっくり深く)、光の中では元の高さで (ラ・ソ・ファ)。同じ言葉が、明るく戻ってくる
    胸がホッとする (血圧が下がるように)  → 下りていく音型、ゆっくりした脈 (4 半音下げた tablet89 は ♩=48)、小さな音量、山を作らない
    ホッと一安心                         → やわらかい打鍵 (tablet282 の仕上げ)。終わりは、ハ長調のはっきりした終止の後に、ハ長調の Amen
    バタンキューにならない               → 段落ごとの大きさを揃える。急に上がらず、急に落ちない
    思考に仕切りができる                 → 仕切り = 段落。8 つの段落。回る主題が境目に立つ (初めと、白い鍵盤の真ん中)。大きな境目は同じ 1 つの音 (ファ)
    抗うつ (気分が上がる)                → 調が明るくなっていく: 変ロ短調 (夜) → ハ長調 (白い鍵盤)。主題は長 3 度上で戻る
  素材は 3 つだけ (楽器は何も加えない):
    A         20261120_024046 — 11/20 02:40 の鍵盤の録音。tablet282 と同じ音 (soften282.py)。速さも音の高さもそのまま
    B         20261121_041625 — 11/21 04:16 の鍵盤の録音。同じく
    tablet89  LXXXIX — Requiem e Fuga (ニ短調)。テープのように速さごと移す: 夜は 4 半音下げて変ロ短調に (CCLXXIX・CCLXXX と同じ)、主題が戻る所は元の高さ、
              Amen は 2 半音下げてハ長調に (元はニ長調の和音が消えていく所)
  ファ: 4 半音下げた主題の真ん中の音はファ。鍵盤の録音は 2 つとも、黒い鍵盤から白い鍵盤へ移る最初の音がファ。夜の間ずっと回っていたファが、仕切りの音になる
  形 (♩=60、1 小節 = 4 秒):
    I.    Notte (0 小節)       2 小節 (8 秒) から A の小さな音。4 小節 (16 秒) から主題の出だしが 3 回、少しずつ大きく (4 半音下げて)
    II.   Requiem (12 小節)    4 回目 (46 秒) からそのまま先へ: Requiem I (変ロ短調、ゆっくり)。1 分 6 秒から 2 分 0 秒まで、B の黒い鍵盤の出だし
    III.  Fuga (39 小節)       2 分 37 秒から Fuga I (声が順番に入る)。A は 2 分 59 秒から途切れずに流れ始める
    IV.   Sola (59 小節)       tablet89 が閉じて (3 分 58 秒)、A だけ。ファへ向かう
    V.    Luce (76 小節)       5 分 4 秒、A と B が同じファで、白い鍵盤 (ハ長調 / イ短調) へ
    VI.   Mantra (96 小節)     B が休む間 (6 分 23 秒から 28 秒)、主題の出だしが元の高さで 3 回戻る (6 分 24 秒から)
    VII.  Chiarezza (103 小節) 6 分 51 秒から、また 2 つで。8 分 54 秒に山
    VIII. Amen (139 小節)      A の最後の音 (ファ・ラ) の上で、B がシ・ファからド・ミへ閉じ (9 分 16 秒)、tablet89 の Amen がハ長調で重なって消える。146 小節
  置き方は CCLXXXI〜CCLXXXIII と同じ所: 同じファを重ねる (B の g 秒は A の g + 242.428 秒)、B の休みを 22 秒長く、B の寄り道の 2 か所を小さく、
    B の黒い鍵盤の出だしは A の 59 秒目から、B はハ長調の終止 (288.13 秒のド・ミ) の後、黒い鍵盤へ戻る手前 (288.90 秒) で止める
  和音の表示は録音から読んだもの (tablet89 は移した高さで)。♩=60 は目盛り
  使い方: python compose_tablet284.py <wav のフォルダ (20261120_024046.wav・20261121_041625.wav = soften282.py を通した鍵盤の録音 (tablet282 と同じもの),
          20261107_089000.wav = tablet89 の音)> <chords284.json (analyze_chords.py の出力)> [score_tablet284.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet284.json'
E = lambda k, v: float(os.environ.get(k, v))
GA, GB = E('GA', '0.233'), E('GB', '0.232')                 # 鍵盤の音量 (tablet282 と同じ)
DUCK1, DUCK2 = E('DUCK1', '0.25'), E('DUCK2', '0.125')      # B が黒い鍵盤へ寄り道する 2 か所のつまみ (tablet281・282 と同じ)
G89A = E('G89A', '0.14')                                    # tablet89 (4 半音下げて) の音量 — 夜の鍵盤の小さな音を包む裏に (鍵盤より 3〜4 dB 小さく)
G89B = E('G89B', '0.19')                                    # tablet89 (元の高さ) の主題の出だし
G89C = E('G89C', '0.45')                                    # tablet89 (2 半音下げて) の Amen
LOOP_A = (0.30, 0.50, 0.72)                                 # 夜の主題の出だしの 3 回の音量 (G89A に対して)。4 回目で 1 (CCLXXIX と同じ)
LOOP_B = (0.50, 0.70, 0.90)                                 # 戻ってくる主題の出だしの 3 回の音量 (G89B に対して)
FIXPEAK = E('FIXPEAK', '0.74')                              # 仕上げの大きさ (synth.py の基準)。曲の山は 0.390 なので、山に合わせるより 5.6 dB 小さい (平均 −20 dB)。0 なら山に合わせる
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RA, RB, R89 = '20261120_024046', '20261121_041625', '20261107_089000'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
COLA, COLB, COL89 = (150, 195, 240), (245, 215, 150), (200, 180, 240)   # 冬の夜の青、ろうそくの金、tablet89 の薄紫
A_ON, B_ON = 4.4, 3.0                           # 録音を始めた時の物音は入れない (最初の音は A 5.23 秒、B 3.71 秒)
K0 = 3.0                                        # A: 録音の f 秒は曲の f + 3.0 秒。最初の音は 2 小節 (8 秒)
A_END, A_FADE = 553.0, 1.4                      # A の終わり: 最後の音 (ファ・ラ、550.70 秒) の後、録音の終わりのかすかな物音 (553.05 秒から) の手前で消す
B0 = K0 + 59.0                                  # 62.0: B の黒い鍵盤の出だし: 録音の g 秒は曲の g + 62.0 秒 (A の音と音の間を埋める位置 — tablet282 と同じ)
B_OPEN, B_F = 58.40, 58.45                      # B の出だしはここまで / B が入り直す所 (58.585 秒が白い鍵盤の最初のファ)
X1 = 301.013 - 58.585                           # 242.428: B のファを A のファ (301.013 秒) に合わせる
HOLD = 22.0                                     # B の休み (137.5〜143.2 秒は無音) を長くする秒数
B1 = K0 + X1; B2 = B1 + HOLD                    # 245.428 / 267.428
P_END, P_START = 139.0, 142.9                   # B の休み
E0, E1, XE0, XE1 = 111.3, 121.0, 0.4, 0.25      # 寄り道 1
C0, C1, XC = 227.93, 232.90, 0.12               # 寄り道 2
B_CUT, B_FOUT = 288.90, 0.45                    # B の終わり: ド・ミ (288.13 秒) の後、黒い鍵盤へ戻る音 (288.94 秒) の手前
P, OV = 8.0, 0.3                                # 主題の出だし: tablet89 の元の 8 秒から 8 秒 (2 小節)。継ぎ目は 0.3 秒ずつ重ねて渡す
S_N = -4                                        # 夜: 4 半音下げて (変ロ短調、0.794 倍速)
L_N = P / RATE(S_N)                             # 10.08: 4 半音下げた一節の長さ
T1 = 16.0                                       # 夜の主題の 1 回目: 4 小節 (A の 2 小節後 — CCLXXIX と同じ間合い)
T_CONT = T1 + 3 * L_N                           # 46.24: 4 回目から、そのまま先へ (元の 160 秒 = Fuga I の終わりまで)
N_END = 160.0
T_M2 = 384.0                                    # 戻ってくる主題 (元の高さ) の 1 回目: 96 小節 (B が休み始めて 1 秒後)。8 秒 × 3 回で、B が戻る 2.7 秒前に終わる
S_AM, AM_OFF = -2, 373.5                        # Amen: 2 半音下げて (ニ長調の和音 → ハ長調)。元の 373.5 秒から (その前はストレッタの終わりの短調の響きが残る)
T_AM = K0 + 552.3                               # 555.3: Amen の入り — B のド・ミ (曲の 555.56 秒) と一緒にふくらむ
S2, S3, S4, S5, S6, S7, S8, TOTAL = 12, 39, 59, 76, 96, 103, 139, 146
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
PLAYS = [play(RA, K0 + A_ON, GA, 0, A_ON, A_END - A_ON, 0, COLA, '11/20 02:40 の鍵盤 — 初めから最後の音まで (2 小節から)', fin=0.7, fout=A_FADE)]
for k, g in enumerate(LOOP_A):                  # 夜の主題の出だしを 3 回、少しずつ大きく
    PLAYS.append(play(R89, T1 + k * L_N, G89A * g, S_N, P, P + OV, 2, COL89, 'tablet89 — 主題の出だし、4 半音下げて (%d 回目)' % (k + 1), fin=3.0 if k == 0 else OV, fout=OV))
PLAYS.append(play(R89, T_CONT, G89A, S_N, P, N_END - P, 2, COL89, 'tablet89 — 4 回目からそのまま: Requiem I・Fuga I (4 半音下げて)', fin=OV, fout=3.0))
PLAYS.append(play(RB, B0 + B_ON, GB, 0, B_ON, B_OPEN - B_ON, 1, COLB, '11/21 04:16 の鍵盤 — 黒い鍵盤の出だし', fin=0.6, fout=0.25))
PLAYS += [play(RB, B1 + B_F, GB, 0, B_F, E0 - B_F + XE0, 1, COLB, '11/21 04:16 の鍵盤 — 同じファから', fin=0.1, fout=XE0),
          play(RB, B1 + E0, GB * DUCK1, 0, E0, E1 - E0 + XE1, 1, COLB, '黒い鍵盤への寄り道 — 小さく', fin=XE0, fout=XE1),
          play(RB, B1 + E1, GB, 0, E1, P_END - E1, 1, COLB, '続き', fin=XE1, fout=1.5),
          play(RB, B2 + P_START, GB, 0, P_START, C0 - P_START + XC, 1, COLB, '11/21 04:16 — 休んでから、続き', fin=0.3, fout=XC),
          play(RB, B2 + C0, GB * DUCK2, 0, C0, C1 - C0 + XC, 1, COLB, '', fin=XC, fout=XC),
          play(RB, B2 + C1, GB, 0, C1, B_CUT - C1, 1, COLB, '続き — ド・ミで閉じる', fin=XC, fout=B_FOUT)]
for k, g in enumerate(LOOP_B):                  # 戻ってくる主題の出だし (元の高さ) を 3 回、少しずつ大きく。3 回目の終わりで消える
    PLAYS.append(play(R89, T_M2 + k * P, G89B * g, 0, P, P + OV, 2, COL89, 'tablet89 — 主題の出だしが戻る、元の高さで (%d 回目)' % (k + 1), fin=2.0 if k == 0 else OV, fout=2.5 if k == 2 else OV))
PLAYS.append(play(R89, T_AM, G89C, S_AM, AM_OFF, 391.0 - AM_OFF, 2, COL89, 'tablet89 — Amen、2 半音下げて (ハ長調)', fin=1.5, fout=3.0))
IA, I89N, I89M, I89AM = 0, 4, 12, 15            # PLAYS の番号: A、tablet89 (夜の続き)、戻ってくる主題 (1 回目)、Amen
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍): tablet89 が鳴っている間は tablet89、ほかは A
LEAD = [(IA, K0 + 5.0), (I89N, T_CONT), (IA, T_CONT + (N_END - P) / RATE(S_N)), (I89AM, T_AM + 1.5)]
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
    P_.section(0, 'I. Notte — 聖夜の小さな音、回る主題 (♩=60)', '2 小節から 11/20 の鍵盤。4 小節から tablet89 の主題の出だしが 3 回、少しずつ大きく')
    P_.section(S2, 'II. Requiem — ゆっくり深く', '4 回目からそのまま先へ (変ロ短調)。1 分 6 秒から 1 分ほど、11/21 の鍵盤が同じ黒い鍵盤で重なる')
    P_.section(S3, 'III. Fuga — 声が順番に入る', '2 分 37 秒から Fuga I。11/20 の鍵盤は 2 分 59 秒から途切れずに流れ始める')
    P_.section(S4, 'IV. Sola — 鍵盤だけ、ファへ', 'tablet89 が閉じて (3 分 58 秒)、11/20 の鍵盤だけ')
    P_.section(S5, 'V. Luce — 同じファから、白い鍵盤へ', '5 分 4 秒、2 つの鍵盤が同じファで白い鍵盤 (ハ長調 / イ短調) へ')
    P_.section(S6, 'VI. Mantra — 主題が明るく戻る', '11/21 が休む間に、主題の出だしが元の高さで 3 回 (6 分 24 秒から)')
    P_.section(S7, 'VII. Chiarezza — 2 つで', '6 分 51 秒から、また 2 つで。8 分 54 秒に山')
    P_.section(S8, 'VIII. Amen — ホッと一安心 (ハ長調)', '9 分 16 秒、ド・ミで閉じる。tablet89 の Amen がハ長調で重なって消える')
    return P_

def post(P_, events, ex):
    for p in PLAYS:         # どれも、これまでのテープと同じ重ね方 (60 Hz〜8 kHz、全体の残響、左右の遅れ)。tablet89 の移調はテープのように速さごと
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm)
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05) / r, env_off=off / r)
        add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [8.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXXIV · Mantra della Notte Santa',
        'subtitle': '聖夜に、洗脳的で気持ちよく、ホッとする曲。2 つの鍵盤の録音と tablet89。変ロ短調 → ハ長調、♩=60',
        'footer': ['素材は 11/20 02:40・11/21 04:16 の鍵盤の録音と tablet89 だけ。楽器は何も加えない。鍵盤は速さも音の高さもそのまま (tablet282 の仕上げ)。',
                   '洗脳的 = tablet89 の主題の出だしが 3 回ずつ回る。夜は 4 半音下げてファから、光の中では元の高さでラから。下りていく 3 つの音。',
                   '黒い鍵盤の夜 → 同じファ → 白い鍵盤 → ハ長調の終止と Amen。段落の大きさを揃え、山を作らない。146 小節。']}
if FIXPEAK > 0: META['fixed_peak'] = FIXPEAK

if __name__ == '__main__':
    compose.main(OUT, seed=284, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']), 'fixed_peak', d['meta'].get('fixed_peak'))
    for k, e in enumerate(d['extras']): print('  %2d %7.2f - %7.2f s  gain %.3f  semis %+d  off %6.1f  %s' % (k, e['t'], e['t'] + e['d'], e['gain'], e['semis'], e['off'], e['tag']))
