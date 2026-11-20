#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXXV · Notte Santa serena (tablet284 を、聖夜にピッタリな、まっさらできれいな、気持ちの良い曲に作り直す)
  届いた言葉は、薬や味にたとえた気分。薬の働きを音で作ることはできないので、言葉が指している気分を音の言葉に直した:
    仕切りが出来て、安心感がある          → 同じ祈りの言葉 (ミ・レ・ド) が、段落の境目に 3 回ずつ戻ってくる。いつも同じ形で、いつも主音 (ド) に着く
    読まれていると思わずにいられる        → 外から入ってくる声を減らす: 声部が次々に入るフーガ (tablet284 の Fuga I) を外す。鳴るのは、自分の 2 つの夜の鍵盤と、
                                              祈りの 1 本の線と、終わりの和音だけ。急な音、大きな音を置かない
    機械のような重さ、ふさいだ気持ちが晴れる → 祈りの言葉が、3 つの調で、だんだん高く、軽くなる: 変ニ長調 (低く、ゆっくり) → ヘ長調 → ハ長調 (高く、軽く)。
                                              短調の Requiem I は初めの 2 分半だけで閉じて、その先は明るい方へ
    相手の思うことが分かる                → 音で聴いて、答える。A の音と音の間を B の音が埋める (1 分 6 秒から)。A が 2 秒止まると B が弾く (5 分 7 秒)。
                                              B がド・ミで閉じると、祈りの言葉がミ・レ・ドと答えて、同じド・ミに着く (終わり)
    グレープフルーツジュースの味          → さっぱりと明るく、少しだけほろ苦い: 終わりの祈りは 7 半音上げて (1.5 倍速)、高く軽い音に。
                                              終わりのハ長調の和音には、低い変ロがかすかに混じる (ほろ苦さ)
    聖夜、まっさらできれい                → 黒い鍵盤の小さな音で始まる夜 (tablet282 のしっとりの仕上げ)。音の数を減らす。同じ言葉を 3 回 — 祈りの形
  素材は tablet284 と同じ 3 つだけ (楽器は何も加えない):
    A         20261120_024046 — 11/20 02:40 の鍵盤の録音。tablet282 と同じ音 (soften282.py)。速さも音の高さもそのまま
    B         20261121_041625 — 11/21 04:16 の鍵盤の録音。同じく
    tablet89  LXXXIX — Requiem e Fuga (ニ短調)。主題の出だし (元の 8〜16 秒: 伸ばした音の下を、3 つの音が下りていく) と Requiem I と Amen だけを使う。
              テープのように速さごと移す
  祈りの言葉 (tablet89 の主題の出だし) は、元の高さではラ・ソ・ファ = ヘ長調のミ・レ・ド。移すと、どの高さでも長調のミ・レ・ド:
    初め (4 小節から)     4 半音下げて → ファ・変ホ・変ニ = 変ニ長調のミ・レ・ド (10.1 秒 × 3、少しずつ大きく)。4 回目からそのまま Requiem I へ
    真ん中 (96 小節から)   元の高さ     → ラ・ソ・ファ   = ヘ長調のミ・レ・ド   (8 秒 × 3、少しずつ大きく)。B が休む間に
    終わり (139 小節から)  7 半音上げて → ミ・レ・ド     = ハ長調のミ・レ・ド   (5.3 秒 × 3、少しずつ遠く)。B のド・ミの終止と、ハ長調の Amen の上で
  tablet284 から変えた所: Fuga I を外す (tablet89 は Requiem I の終わり、2 分 37 秒で閉じる)。終わりに 3 つ目の祈り (7 半音上げて) を加える。
    初めの祈りを少し大きく (聞き取れるように)。鍵盤の置き方、仕上げ、同じファの仕切り、終わりの終止と Amen は tablet284 のまま
  形 (♩=60、1 小節 = 4 秒):
    I.   Notte (0 小節)       2 小節 (8 秒) から A の小さな音。4 小節 (16 秒) から祈りの言葉が 3 回 (変ニ長調)
    II.  Requiem (12 小節)    4 回目 (46 秒) からそのまま Requiem I (ゆっくり)。1 分 6 秒から 2 分 0 秒まで、B の黒い鍵盤の出だしが A に答える
    III. Sola (39 小節)       tablet89 が閉じて (2 分 37 秒)、A だけ。2 分 59 秒から途切れずに流れ、ファへ向かう
    IV.  Luce (76 小節)       5 分 4 秒、A と B が同じファで、白い鍵盤 (ハ長調 / イ短調) へ
    V.   Preghiera (96 小節)  B が休む間 (6 分 23 秒から 28 秒)、祈りの言葉がヘ長調で 3 回 (6 分 24 秒から)
    VI.  Insieme (103 小節)   6 分 51 秒から、また 2 つで。8 分 54 秒に山
    VII. Amen (139 小節)      9 分 16 秒、B がド・ミで閉じる。ハ長調の Amen。祈りの言葉がハ長調で 3 回、高く、遠ざかる。148 小節
  和音の表示は録音から読んだもの (tablet89 は移した高さで)。♩=60 は目盛り
  使い方: python compose_tablet285.py <wav のフォルダ (tablet284 と同じ: 20261120_024046.wav・20261121_041625.wav = soften282.py を通した鍵盤の録音,
          20261107_089000.wav = tablet89 の音)> <chords284.json (analyze_chords.py の出力)> [score_tablet285.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet285.json'
E = lambda k, v: float(os.environ.get(k, v))
GA, GB = E('GA', '0.233'), E('GB', '0.232')                 # 鍵盤の音量 (tablet282 と同じ)
DUCK1, DUCK2 = E('DUCK1', '0.25'), E('DUCK2', '0.125')      # B が黒い鍵盤へ寄り道する 2 か所のつまみ (tablet281・282 と同じ)
G89A = E('G89A', '0.16')                                    # tablet89 (4 半音下げて) の音量 — 夜の鍵盤の小さな音を包む (tablet284 より 1 dB 大きく)
G89B = E('G89B', '0.19')                                    # tablet89 (元の高さ) の祈りの言葉 (tablet284 と同じ)
G89D = E('G89D', '0.18')                                    # tablet89 (7 半音上げて) の祈りの言葉
G89C = E('G89C', '0.45')                                    # tablet89 (2 半音下げて) の Amen
LOOP_A = (0.45, 0.65, 0.85)                                 # 初めの祈りの 3 回の音量 (G89A に対して)。4 回目で 1 (tablet284 は 0.30・0.50・0.72)
LOOP_B = (0.50, 0.70, 0.90)                                 # 真ん中の祈りの 3 回の音量 (G89B に対して)
LOOP_C = (1.00, 0.65, 0.40)                                 # 終わりの祈りの 3 回の音量 (G89D に対して) — 少しずつ遠く
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
COLA, COLB, COL89, COL89H = (150, 195, 240), (245, 215, 150), (200, 180, 240), (235, 235, 170)   # 冬の夜の青、ろうそくの金、tablet89 の薄紫、高い祈りの淡い黄
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
T_CONT = T1 + 3 * L_N                           # 46.24: 4 回目から、そのまま先へ (Requiem I の終わりまで = 曲の 2 分 37 秒)
N_END = 96.0                                    # tablet89 は Requiem I の終わり (元の 96 秒) で閉じる。Fuga I は入れない
T_M2 = 384.0                                    # 戻ってくる主題 (元の高さ) の 1 回目: 96 小節 (B が休み始めて 1 秒後)。8 秒 × 3 回で、B が戻る 2.7 秒前に終わる
S_AM, AM_OFF = -2, 373.5                        # Amen: 2 半音下げて (ニ長調の和音 → ハ長調)。元の 373.5 秒から (その前はストレッタの終わりの短調の響きが残る)
T_AM = K0 + 552.3                               # 555.3: Amen の入り — B のド・ミ (曲の 555.56 秒) と一緒にふくらむ
S_HI = 7                                        # 終わりの祈り: 7 半音上げて (ミ・レ・ド = ハ長調、1.498 倍速)
L_HI = P / RATE(S_HI)                           # 5.34: 7 半音上げた一節の長さ
T_M3 = 558.0                                    # 終わりの祈りの 1 回目: B のド・ミの 2.4 秒後
S2, S3, S4, S5, S6, S7, TOTAL = 12, 39, 76, 96, 103, 139, 148
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
PLAYS = [play(RA, K0 + A_ON, GA, 0, A_ON, A_END - A_ON, 0, COLA, '11/20 02:40 の鍵盤 — 初めから最後の音まで (2 小節から)', fin=0.7, fout=A_FADE)]
for k, g in enumerate(LOOP_A):                  # 初めの祈りを 3 回、少しずつ大きく
    PLAYS.append(play(R89, T1 + k * L_N, G89A * g, S_N, P, P + OV, 2, COL89, 'tablet89 — 祈りの言葉、4 半音下げて (%d 回目)' % (k + 1), fin=3.0 if k == 0 else OV, fout=OV))
PLAYS.append(play(R89, T_CONT, G89A, S_N, P, N_END - P, 2, COL89, 'tablet89 — 4 回目からそのまま: Requiem I (4 半音下げて)', fin=OV, fout=3.0))
PLAYS.append(play(RB, B0 + B_ON, GB, 0, B_ON, B_OPEN - B_ON, 1, COLB, '11/21 04:16 の鍵盤 — 黒い鍵盤の出だし', fin=0.6, fout=0.25))
PLAYS += [play(RB, B1 + B_F, GB, 0, B_F, E0 - B_F + XE0, 1, COLB, '11/21 04:16 の鍵盤 — 同じファから', fin=0.1, fout=XE0),
          play(RB, B1 + E0, GB * DUCK1, 0, E0, E1 - E0 + XE1, 1, COLB, '黒い鍵盤への寄り道 — 小さく', fin=XE0, fout=XE1),
          play(RB, B1 + E1, GB, 0, E1, P_END - E1, 1, COLB, '続き', fin=XE1, fout=1.5),
          play(RB, B2 + P_START, GB, 0, P_START, C0 - P_START + XC, 1, COLB, '11/21 04:16 — 休んでから、続き', fin=0.3, fout=XC),
          play(RB, B2 + C0, GB * DUCK2, 0, C0, C1 - C0 + XC, 1, COLB, '', fin=XC, fout=XC),
          play(RB, B2 + C1, GB, 0, C1, B_CUT - C1, 1, COLB, '続き — ド・ミで閉じる', fin=XC, fout=B_FOUT)]
for k, g in enumerate(LOOP_B):                  # 真ん中の祈り (元の高さ) を 3 回、少しずつ大きく。3 回目の終わりで消える
    PLAYS.append(play(R89, T_M2 + k * P, G89B * g, 0, P, P + OV, 2, COL89, 'tablet89 — 祈りの言葉が戻る、元の高さで (%d 回目)' % (k + 1), fin=2.0 if k == 0 else OV, fout=2.5 if k == 2 else OV))
PLAYS.append(play(R89, T_AM, G89C, S_AM, AM_OFF, 391.0 - AM_OFF, 2, COL89, 'tablet89 — Amen、2 半音下げて (ハ長調)', fin=1.5, fout=3.0))
for k, g in enumerate(LOOP_C):                  # 終わりの祈り (7 半音上げて) を 3 回、少しずつ遠く。Amen と同じ段に重なるので、段を 1 つ上に
    PLAYS.append(play(R89, T_M3 + k * L_HI, G89D * g, S_HI, P, P + OV, 3, COL89H, 'tablet89 — 祈りの言葉、7 半音上げて (%d 回目)' % (k + 1), fin=1.5 if k == 0 else OV, fout=2.5 if k == 2 else OV))
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
    P_.section(0, 'I. Notte — 聖夜の小さな音、祈りの言葉 (♩=60)', '2 小節から 11/20 の鍵盤。4 小節から tablet89 の祈りの言葉 (ミ・レ・ド) が 3 回、変ニ長調で')
    P_.section(S2, 'II. Requiem — ゆっくり', '4 回目からそのまま Requiem I。1 分 6 秒から 1 分ほど、11/21 の鍵盤が 11/20 の音の間に答える')
    P_.section(S3, 'III. Sola — 鍵盤だけ、ファへ', 'tablet89 が閉じて (2 分 37 秒)、11/20 の鍵盤だけ。2 分 59 秒から途切れずに流れる')
    P_.section(S4, 'IV. Luce — 同じファから、白い鍵盤へ', '5 分 4 秒、2 つの鍵盤が同じファで白い鍵盤 (ハ長調 / イ短調) へ')
    P_.section(S5, 'V. Preghiera — 祈りの言葉が明るく戻る', '11/21 が休む間に、祈りの言葉がヘ長調で 3 回 (6 分 24 秒から)')
    P_.section(S6, 'VI. Insieme — 2 つで', '6 分 51 秒から、また 2 つで。8 分 54 秒に山')
    P_.section(S7, 'VII. Amen — ド・ミに、ミ・レ・ドが答える (ハ長調)', '9 分 16 秒、ド・ミで閉じる。ハ長調の Amen の上で、祈りの言葉が高く 3 回、遠ざかる')
    return P_

def post(P_, events, ex):
    for p in PLAYS:         # どれも、これまでのテープと同じ重ね方 (60 Hz〜8 kHz、全体の残響、左右の遅れ)。tablet89 の移調はテープのように速さごと
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm)
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=c.get('env_dt', 0.05) / r, env_off=off / r)
        add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [8.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXXV · Notte Santa serena',
        'subtitle': '聖夜に、まっさらできれいな、気持ちの良い曲。tablet284 を作り直して。変ニ長調 → ハ長調、♩=60',
        'footer': ['素材は tablet284 と同じ: 11/20 02:40・11/21 04:16 の鍵盤の録音と tablet89 だけ。楽器は何も加えない。鍵盤は速さも音の高さもそのまま。',
                   '同じ祈りの言葉 (ミ・レ・ド) が 3 回ずつ、段落の境目に戻る。変ニ長調 → ヘ長調 → ハ長調と、だんだん高く、軽く。',
                   '声部の多いフーガは外した。鳴るのは 2 つの夜の鍵盤と、祈りの 1 本の線と、終わりの和音だけ。148 小節。']}
if FIXPEAK > 0: META['fixed_peak'] = FIXPEAK

if __name__ == '__main__':
    compose.main(OUT, seed=285, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']), 'fixed_peak', d['meta'].get('fixed_peak'))
    for k, e in enumerate(d['extras']): print('  %2d %7.2f - %7.2f s  gain %.3f  semis %+d  off %6.1f  %s' % (k, e['t'], e['t'] + e['d'], e['gain'], e['semis'], e['off'], e['tag']))
