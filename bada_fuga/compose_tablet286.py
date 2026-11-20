#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXXVI · Elevazione (2 つの鍵盤の録音だけで — 聖夜にピッタリな、まっさらできれいな、気持ちの高まる曲に)
  届いた言葉は、薬や味にたとえた気分 (CCLXXXV と同じ言葉に、胸に良い圧力、全身がホッと一安心、薬ではないものが洗脳的に高揚する、が加わった)。
  届いた言葉のとおり、曲は薬ではない。言葉が指している気分を音の言葉に直した:
    仕切りが出来て、安心感がある            → 同じ形を 3 回ずつ、段落の境目に置く (初め・真ん中・終わり)。いつも 3 回、いつも少しずつ大きく
    読まれていると思わずにいられる          → 鳴るのは、自分の 2 つの夜の鍵盤だけ。ほかの声は 1 つも入れない (tablet89 も使わない)。急な音、大きな音を置かない
    機械のような重さ、ふさいだ気持ちが晴れる → くり返すのは機械の音ではなく、自分で弾いた一節。3 つの一節は、黒い鍵盤の問いかけ → 白い鍵盤の上っていく線 →
                                              ハ長調の終止と、だんだん明るくなる
    相手の思うことが分かる                  → 音で聴いて、答える。A の音と音の間を B の音が埋める。A が 2 秒止まると B が弾く。A のファに、B の一節のファが重なる
    グレープフルーツジュースの味            → さっぱり: 2 つの鍵盤だけ。ほろ苦さ: B が白い鍵盤の途中で黒い鍵盤へ寄り道する 2 か所を、消さずに小さく残す
    聖夜、まっさらできれい                  → 黒い鍵盤の小さな音で始まる夜 (tablet282 のしっとりの仕上げ)
    胸に良い圧力                            → 小さすぎず大きすぎない音量 (CCLXXXV より 1 dB ほど大きく)。強い打鍵だけ抑えて、音の厚みを残す。低い音がゆっくり支える
    全身がホッと一安心                      → こわばりを作らない: 打鍵の頭はやわらかく、くり返しの継ぎ目は重ねて渡す。同じ形を 3 回くり返して、力を抜く
    洗脳的に高揚する                        → 3 回のくり返しは、どれも少しずつ大きく。真ん中の一節は上っていく線 (レ・ミ・ファ・ソ → ド)。
                                              終わりはハ長調の終止 (シ・ファ → ド・ミ) を 3 回言い切る
  素材は 2 つだけ (楽器は何も加えない。速さも音の高さも変えない):
    A   20261120_024046 — 11/20 02:40 の鍵盤の録音。tablet282 と同じ音 (soften282.py)
    B   20261121_041625 — 11/21 04:16 の鍵盤の録音。同じく
  3 回ずつくり返す一節 (どれも録音の中の、弾かれたままの一節):
    初め    A の出だし (録音の 5.10〜12.50 秒、7.4 秒): ファ・変ホ の和音、変ト、変ホ、変ニ。A はこの後 (12.63 秒) にもう一度同じ和音を弾くので、
            くり返しても元の流れのまま続く。3 回、少しずつ大きく。4 回目からそのまま A の録音が先へ進む (いつもの入り方)
    真ん中  B が白い鍵盤へ移る一節 (録音の 58.45〜65.60 秒、7.15 秒): ファ、ミ、レ、ミ、ファ、ソ・ド、ド — 下りてから上って、ドに着く。
            B が休む間に 3 回、少しずつ大きく。頭のファは、A がその時に弾くファ (録音の 386.75 秒) に重ねる (濁りの指数 0.31、白い鍵盤どうし)
    終わり  B の終止 (録音の 286.60〜288.80 秒、2.2 秒): シ・ファ、レ、レ、レ・ファ、ド・ミ。1 回目は元の流れのまま、続けて 2 回、少しずつ大きく。
            最後のド・ミは響きの尾で消える (B はこの 0.8 秒後に黒い鍵盤へ戻るので、その手前で止める)
  鍵盤の置き方は CCLXXXI〜CCLXXXV と同じ: 同じファを重ねる (B の g 秒は A の g + 242.428 秒)、B の休みを 22 秒長く、B が黒い鍵盤へ寄り道する 2 か所を小さく、
    B の黒い鍵盤の出だしは A の 59 秒目から、録音を始めた時の物音は入れない
  形 (♩=60、1 小節 = 4 秒):
    I.   Notte (0 小節)        2 小節 (8 秒) から A の出だしが 3 回、少しずつ大きく。4 回目 (30 秒) からそのまま先へ
    II.  Dialogo (21 小節)     1 分 28 秒から 2 分 23 秒まで、B の黒い鍵盤の出だしが A の音の間に答える
    III. Sola (50 小節)        A だけ。3 分 21 秒から途切れずに流れ、ファへ向かう
    IV.  Luce (81 小節)        5 分 26 秒、A と B が同じファで、白い鍵盤 (ハ長調 / イ短調) へ
    V.   Ritornello (102 小節) B が休む間 (6 分 45 秒から 28 秒)、B の上っていく一節が 3 回 (6 分 52 秒から)
    VI.  Insieme (108 小節)    7 分 13 秒から、また 2 つで。9 分 17 秒に山
    VII. Amen (144 小節)       9 分 38 秒、B がド・ミで閉じる。続けて 2 回、少しずつ大きく。149 小節
  和音の表示は A から、A が終わってからは B から読んだもの。♩=60 は目盛り (鍵盤は拍に縛られずに弾かれている)
  使い方: python compose_tablet286.py <wav のフォルダ (20261120_024046.wav・20261121_041625.wav = soften282.py を通した鍵盤の録音 — tablet282 と同じもの)>
          <chords286.json (analyze_chords.py の出力)> [score_tablet286.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet286.json'
E = lambda k, v: float(os.environ.get(k, v))
GA, GB = E('GA', '0.233'), E('GB', '0.232')                 # 鍵盤の音量 (tablet282 と同じ)
DUCK1, DUCK2 = E('DUCK1', '0.25'), E('DUCK2', '0.125')      # B が黒い鍵盤へ寄り道する 2 か所のつまみ (tablet281・282 と同じ)
LOOP_A = (0.50, 0.70, 0.85)                                 # 初めの 3 回の音量 (GA に対して)。4 回目で 1
LOOP_B = (0.60, 0.80, 1.00)                                 # 真ん中の 3 回の音量 (GB に対して)
LOOP_C = (1.00, 1.20, 1.40)                                 # 終わりの 3 回の音量 (GB に対して)。1 回目は元の流れ
FIXPEAK = E('FIXPEAK', '0.62')                              # 仕上げの大きさ (synth.py の基準)。曲の山は 0.390 なので、山に合わせるより 4 dB 小さい (平均 −19 dB)。0 なら山に合わせる
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RA, RB = '20261120_024046', '20261121_041625'
BPM = 60
COLA, COLB, COLR = (150, 195, 240), (245, 215, 150), (250, 235, 190)   # 冬の夜の青、ろうそくの金、くり返す一節の淡い金
# 初めのくり返し: A の出だし
LA0, L1, OVA = 5.10, 12.634 - 5.232, 0.3        # 録音の 5.10 秒から 7.402 秒 (ファ・変ホの和音は 5.232 秒と 12.634 秒)。継ぎ目は 0.3 秒重ねて渡す
T_R1 = 8.10                                     # 1 回目: 最初の音が 2 小節 (8.2 秒) に鳴る
K0 = T_R1 + 3 * L1 - LA0                        # 25.206: 4 回目から A がそのまま先へ — A の録音の f 秒は曲の f + 25.206 秒
A_END, A_FADE = 553.0, 1.4                      # A の終わり: 最後の音 (ファ・ラ、550.70 秒) の後、録音の終わりのかすかな物音の手前で消す
B_ON = 3.0                                      # B は録音の 3.0 秒から (録音を始めた時の物音は入れない)
B0 = K0 + 59.0                                  # 84.206: B の黒い鍵盤の出だし (A の音と音の間を埋める位置 — tablet282 と同じ)
B_OPEN, B_F = 58.40, 58.45                      # B の出だしはここまで / B が入り直す所 (58.585 秒が白い鍵盤の最初のファ)
X1 = 301.013 - 58.585                           # 242.428: B のファを A のファ (301.013 秒) に合わせる
HOLD = 22.0                                     # B の休み (137.5〜143.2 秒は無音) を長くする秒数
B1 = K0 + X1; B2 = B1 + HOLD                    # 267.634 / 289.634
P_END, P_START = 139.0, 142.9                   # B の休み
E0, E1, XE0, XE1 = 111.3, 121.0, 0.4, 0.25      # 寄り道 1
C0, C1, XC = 227.93, 232.90, 0.12               # 寄り道 2
# 真ん中のくり返し: B が白い鍵盤へ移る一節
LB0, L2, OVB = 58.45, 7.15, 0.1                 # 録音の 58.45 秒から 7.15 秒 (65.60 秒まで; 65.71 秒の次の音の手前)
T_R2 = K0 + 386.75 - (58.585 - LB0)             # 411.82: 頭のファ (58.585 秒) を、A のファ (386.75 秒) に重ねる
# 終わりのくり返し: B の終止
LC0, LC1, OVC = 286.60, 288.80, 0.12            # 録音の 286.60〜288.80 秒 (シ・ファは 286.76 秒、ド・ミは 288.12 秒)
L3 = LC1 - LC0                                  # 2.2
B_CUT, B_FOUT = 288.90, 0.45                    # B の終わり: 黒い鍵盤へ戻る音 (288.94 秒) の手前
T_R3 = B2 + LC1                                 # 578.43: 2 回目の頭
S2, S3, S4, S5, S6, S7, TOTAL = 21, 50, 81, 102, 108, 144, 149
def play(rid, beat, gain, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
PLAYS = []
for k, g in enumerate(LOOP_A):                  # A の出だしを 3 回、少しずつ大きく
    PLAYS.append(play(RA, T_R1 + k * L1, GA * g, LA0, L1 + OVA, 2, COLR, '11/20 の鍵盤 — 出だしの一節 (%d 回目)' % (k + 1), fin=0.1 if k == 0 else OVA, fout=OVA))
PLAYS.append(play(RA, T_R1 + 3 * L1, GA, LA0, A_END - LA0, 0, COLA, '11/20 02:40 の鍵盤 — 4 回目からそのまま、最後の音まで', fin=OVA, fout=A_FADE))
PLAYS.append(play(RB, B0 + B_ON, GB, B_ON, B_OPEN - B_ON, 1, COLB, '11/21 04:16 の鍵盤 — 黒い鍵盤の出だし', fin=0.6, fout=0.25))
PLAYS += [play(RB, B1 + B_F, GB, B_F, E0 - B_F + XE0, 1, COLB, '11/21 04:16 の鍵盤 — 同じファから', fin=0.1, fout=XE0),
          play(RB, B1 + E0, GB * DUCK1, E0, E1 - E0 + XE1, 1, COLB, '黒い鍵盤への寄り道 — 小さく', fin=XE0, fout=XE1),
          play(RB, B1 + E1, GB, E1, P_END - E1, 1, COLB, '続き', fin=XE1, fout=1.5)]
for k, g in enumerate(LOOP_B):                  # B の上っていく一節を 3 回、少しずつ大きく
    PLAYS.append(play(RB, T_R2 + k * L2, GB * g, LB0, L2 + OVB, 2, COLR, '11/21 の鍵盤 — 上っていく一節 (%d 回目)' % (k + 1), fin=OVB, fout=OVB))
PLAYS += [play(RB, B2 + P_START, GB, P_START, C0 - P_START + XC, 1, COLB, '11/21 04:16 — 休んでから、続き', fin=0.3, fout=XC),
          play(RB, B2 + C0, GB * DUCK2, C0, C1 - C0 + XC, 1, COLB, '', fin=XC, fout=XC),
          play(RB, B2 + C1, GB * LOOP_C[0], C1, LC1 - C1 + OVC, 1, COLB, '続き — ド・ミで閉じる', fin=XC, fout=OVC),
          play(RB, T_R3, GB * LOOP_C[1], LC0, L3 + OVC, 2, COLR, '11/21 の鍵盤 — 終止をもう一度 (2 回目)', fin=OVC, fout=OVC),
          play(RB, T_R3 + L3, GB * LOOP_C[2], LC0, B_CUT - LC0, 2, COLR, '終止 (3 回目)', fin=OVC, fout=B_FOUT)]
IA, IBEND = 3, len(PLAYS) - 3                   # PLAYS の番号: A (4 回目から)、B の終わりの切れ
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍): A、A が終わってからは B
LEAD = [(0, T_R1), (1, T_R1 + L1), (2, T_R1 + 2 * L1), (IA, T_R1 + 3 * L1), (IBEND, K0 + A_END)]
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
    P_ = Piece(TOTAL)
    for q in range(TOTAL * BPB): P_.harm[q] = harm_at(q)
    for k in range(TOTAL): P_.tempo[k] = BPM; P_.dyn[k] = 0.5
    for v in VOICES: P_.rest_bars(v, 0, TOTAL)
    P_.section(0, 'I. Notte — 聖夜の小さな音、3 回 (♩=60)', '2 小節から 11/20 の鍵盤の出だしが 3 回、少しずつ大きく。4 回目からそのまま先へ')
    P_.section(S2, 'II. Dialogo — もう 1 つの夜が答える', '1 分 28 秒から 1 分ほど、11/21 の鍵盤が、11/20 の音と音の間に答える')
    P_.section(S3, 'III. Sola — 鍵盤だけ、ファへ', '11/20 の鍵盤だけ。3 分 21 秒から途切れずに流れる')
    P_.section(S4, 'IV. Luce — 同じファから、白い鍵盤へ', '5 分 26 秒、2 つの鍵盤が同じファで白い鍵盤 (ハ長調 / イ短調) へ')
    P_.section(S5, 'V. Ritornello — 上っていく一節が 3 回', '11/21 が休む間に、白い鍵盤へ移った時の一節が戻る (6 分 52 秒から): レ・ミ・ファ・ソ → ド')
    P_.section(S6, 'VI. Insieme — 2 つで', '7 分 13 秒から、また 2 つで。9 分 17 秒に山')
    P_.section(S7, 'VII. Amen — ド・ミ、ド・ミ、ド・ミ', '9 分 38 秒、シ・ファからド・ミへ閉じる。続けて 2 回、少しずつ大きく')
    return P_

def post(P_, events, ex):
    for p in PLAYS:         # どれも tablet282 と同じ重ね方 (60 Hz〜8 kHz、全体の残響、左右の遅れ)。速さも音の高さも変えない (semis=0)
        rid, off, dur = p['rid'], p['off'], p['dur']; c = CH.get(rid, {})
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05), env_off=off)
        add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [8.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXXVI · Elevazione',
        'subtitle': '聖夜に、まっさらできれいな、気持ちの高まる曲。2 つの鍵盤の録音だけで。変ニ長調 → ハ長調、♩=60',
        'footer': ['素材は 11/20 02:40 と 11/21 04:16 の鍵盤の録音だけ。楽器は何も加えない。速さも音の高さも変えない (tablet282 の仕上げ)。',
                   '弾かれたままの一節を 3 回ずつ、少しずつ大きく: 初めは出だし、真ん中は上っていく線、終わりはハ長調の終止。',
                   '黒い鍵盤の夜 → 同じファ → 白い鍵盤 → ド・ミ、ド・ミ、ド・ミ。段落の大きさを揃え、山を作らない。149 小節。']}
if FIXPEAK > 0: META['fixed_peak'] = FIXPEAK

if __name__ == '__main__':
    compose.main(OUT, seed=286, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']), 'fixed_peak', d['meta'].get('fixed_peak'))
    for k, e in enumerate(d['extras']): print('  %2d %7.2f - %7.2f s  gain %.3f  off %6.2f  lane %d  %s' % (k, e['t'], e['t'] + e['d'], e['gain'], e['off'], e['lane'], e['tag']))
