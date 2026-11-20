#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXIX · Sintesi ipnotica (tablet89・11/20 02:40 の鍵盤の録音・calma の声を、洗脳的に化学合成して)
  素材は 3 つ (楽器は何も加えない):
    声        届いた 20261108_145525_aureola_sensuale_calma.mp3 (11/08 14:55 の声 → 少し低めの女声、響きと音量を抑えた、安心するドエロの光輪様の声)。作り換えない
    鍵盤      届いた 20261120_024046.mp3 — 11/20 02:40 の鍵盤の録音。tablet276 と同じ音 (level273.py で強弱の幅を 4 割に、全体の残響)。高さも速さもそのまま
    tablet89  LXXXIX — Requiem e Fuga, recto e verso (ニ短調、♩=60)。LXXXIX も 9/23〜9/29 の録音を「化学合成」して作った曲
  化学合成 = 3 つを溶け合わせる: 鍵盤の録音は前半が黒い鍵盤 (変ロ短調 / 変ニ長調)、後半が白い鍵盤 (イ短調 / ハ長調)。tablet89 (ニ短調) を
    前半は 4 半音下げて (テープのように速さごと、0.794 倍速 = ゆっくり深く) 変ロ短調にし、後半は元の高さのまま重ねる。
    濁りの指数 (12 の移し方を全部測った): 前半は 4 半音下げて 0.23 (移さないと 0.46)、後半はそのまま 0.27 (これまでのテープどうしは 0.15〜0.27)。
    鍵盤が半音下がって白い鍵盤になる所で、tablet89 は元の高さ (ニ短調) に戻る — 2 つの調が入れ替わって、1 つになる
  洗脳的 = 主題の出だしが回る: tablet89 の主題 (09/24 08:53 の主題を 4 倍に伸ばしたもの) の出だし、元の 8〜16 秒 (2 小節) は、16 秒の後に 8 秒の頭へ
    戻っても響きがほとんど変わらない (継ぎ目の前後の響きの似かた 0.98)。これを 4 半音下げて (10.1 秒)、少しずつ大きく 3 回くり返し、4 回目からそのまま先へ
  形 (声が先に立ち、曲は 2 小節後から — いまの入りの間合い):
    I:   2 小節 (8 秒) から声、4 小節 (16 秒) から鍵盤の小さな音、6 小節 (24 秒) から tablet89 の主題の出だしが 3 回 (少しずつ大きく) →
    II:  4 回目 (54 秒) から tablet89 がそのまま先へ: Requiem I、Fuga I (変ロ短調、ゆっくり)。鍵盤は 3 分 7 秒から途切れずに流れ始める。声は 3 分 19 秒まで →
    III: 鍵盤だけ (4 分 6 秒から) — 前半の山を築いて、止まる (5 分 15 秒) →
    IV:  声 (2 回目) が先に入り、2 秒後から白い鍵盤、3 小節後から tablet89 の Requiem II (元の高さ、ニ短調; 初めの 2 小節は静か) →
    V:   Fuga II、ストレッタ — 鍵盤のいちばん大きい所。声は 8 分 26 秒まで →
    VI:  Amen (ニ長調)。tablet89 は 9 分 18 秒に閉じ、鍵盤の終わりが残る (9 分 27 秒)。142 小節
  声は synth.py の faithful の経路 (全体の残響を掛けずに前に)。静かな話し始めは tablet276 と同じに 3 つに分けて持ち上げる。鍵盤と tablet89 はこれまでの重ね方で後ろに
  和音の表示は録音から読んだもの (tablet89 は移した高さで)。♩=60 は目盛り (4 半音下げた tablet89 は ♩=48 前後、鍵盤は拍に縛られずに弾かれている)
  使い方: python compose_tablet279.py <wav のフォルダ (20261108_145525.wav = calma の声, 20261120_024046.wav = level273.py を通した鍵盤の録音,
          20261107_089000.wav = tablet89 の音)> <chords279.json (analyze_chords.py の出力)> [score_tablet279.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet279.json'
GV = float(os.environ.get('GV', '1.33'))                                              # 声の音量 (tablet276 と同じ)
GL1, GL2 = float(os.environ.get('GL1', '1.7')), float(os.environ.get('GL2', '1.25'))    # 静かな話し始めの持ち上げ (録音の 50.7 秒まで、82.25 秒まで; tablet276 と同じ)
GV2 = float(os.environ.get('GV2', '1.25'))                                            # 2 回目の声は、鍵盤と tablet89 の両方の上なので少し上げる
GK = float(os.environ.get('GK', '0.31'))                                              # 鍵盤の音量 (tablet276 と同じ)
G89A = float(os.environ.get('G89A', '0.24'))                                          # tablet89 (4 半音下げて) の音量 — 前半は鍵盤の小さな音を包む裏に
G89B = float(os.environ.get('G89B', '0.30'))                                          # tablet89 (元の高さ) の音量
LOOP_K = (0.30, 0.50, 0.72)                                                           # 主題の出だしの 3 回の音量 (G89A に対して)。4 回目で 1
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (録音だけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, RK, R89 = '20261108_145525', '20261120_024046', '20261107_089000'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
S89 = -4                                        # tablet89 を前半だけ 4 半音下げる (変ロ短調)
COLV, COLK, COL89A, COL89B = (255, 190, 160), (140, 200, 235), (150, 185, 245), (190, 160, 240)
V_OFF, V_ON, V_CUT, V_CUT2, V_LEN = 4.86, 5.36, 50.7, 82.25, 198.46                   # calma の声: 録音の 4.86 秒から (話し始めは 5.36 秒)。50.7 秒と 82.25 秒で 3 つに分けて置く
K_LEN, K0 = 556.3, 11.0                         # 鍵盤: 録音の f 秒は曲の f + 11 秒。最初の音 (録音の 5.0 秒) は 4 小節 (16 秒)
V1 = 8.0 - (V_ON - V_OFF)                       # 7.5: 声 (1 回目): 2 小節 (8 秒) から話し始める
P, OV = 8.0, 0.3                                # 主題の出だし: 元の 8 秒から 8 秒 (2 小節)。継ぎ目は 0.3 秒ずつ重ねて渡す
L = P / RATE(S89)                               # 10.08: 4 半音下げた一節の長さ
T1 = 24.0                                       # 1 回目の出だし: 6 小節 (鍵盤の 2 小節後)
T_CONT = T1 + 3 * L                             # 54.2: 4 回目の出だしから、そのまま先へ (元の 160 秒 = Fuga I の終わりまで)
A_END = 160.0                                   # 前半の tablet89 は Fuga I の終わりまで (曲の 4 分 6 秒)
TK = K0 + 304.4                                 # 315.4: 鍵盤が止まる所。声 (2 回目) はここで話し始める
V2 = TK - (V_ON - V_OFF)                        # 314.9
T2 = TK + 12.0                                  # 327.4: tablet89 (元の高さ) の Requiem II (元の 160 秒) の入り — 声の 3 小節後。1 秒ずつ動かして、白い鍵盤との濁りがいちばん小さい所 (0.28)
S2, S3, S4, S5, S6, TOTAL = 14, 62, 79, 106, 134, 142
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None, envk=1.0):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout, envk=envk)
def voice(beat, g, tag):                        # 声を 3 つに分けて置く: 静かな話し始め (持ち上げる)、その次 (少し持ち上げる)、その先
    return [play(RV, beat, g * GL1, 0, V_OFF, V_CUT - V_OFF, 0, COLV, tag, fin=0.3, fout=0.05),
            play(RV, beat + V_CUT - V_OFF, g * GL2, 0, V_CUT, V_CUT2 - V_CUT, 0, COLV, tag, fin=0.05, fout=0.05),
            play(RV, beat + V_CUT2 - V_OFF, g, 0, V_CUT2, V_LEN - V_CUT2, 0, COLV, tag, fin=0.05, fout=2.0)]
PLAYS = voice(V1, GV, '11/08 14:55 の calma の声 (2 小節から)')
PLAYS.append(play(RK, K0, GK, 0, 0.0, K_LEN, 1, COLK, '11/20 02:40 の鍵盤の録音 — tablet276 と同じ音 (4 小節から)', fin=0.5, fout=2.0))
for k, g in enumerate(LOOP_K):                  # 主題の出だしを 3 回、少しずつ大きく
    PLAYS.append(play(R89, T1 + k * L, G89A * g, S89, P, P + OV, 2, COL89A, 'tablet89 — 主題の出だし、4 半音下げて (%d 回目)' % (k + 1),
                      fin=3.0 if k == 0 else OV, fout=OV, envk=g))
PLAYS.append(play(R89, T_CONT, G89A, S89, P, A_END - P, 2, COL89A, 'tablet89 — 4 回目からそのまま: Requiem I・Fuga I (4 半音下げて)', fin=OV, fout=3.0))
PLAYS.append(play(R89, T2, G89B, 0, 160.0, 391.0 - 160.0, 3, COL89B, 'tablet89 — Requiem II から終わりまで (元の高さ)', fin=1.0, fout=6.0))
PLAYS += voice(V2, GV * GV2, 'calma の声 (もう一度)')
IK, IA, IB = 3, 7, 8                            # PLAYS の番号: 鍵盤、tablet89 (4 半音下げて、続き)、tablet89 (元の高さ)
# 和音の表示を担う録音 (PLAYS の番号, 表示の始まりの拍): tablet89 が鳴っている間は tablet89、ほかは鍵盤
LEAD = [(IK, K0 + 5.0), (IA, T_CONT), (IK, T_CONT + (A_END - P) / RATE(S89)), (IB, T2 + 8.0), (IK, T2 + 231.0)]   # 鍵盤 → tablet89 (下げて) → 鍵盤だけ → tablet89 → 鍵盤の終わり
def shift_chord(name, semis):
    i = 2 if len(name) > 1 and name[1] in '#b' else 1
    return compose.NAMES[(PC[name[:i]] + semis) % 12] + name[i:]
def harm_at(q):
    cur = 'Bbm'
    for k, a in LEAD:
        p = PLAYS[k]
        if q >= a:
            c = CH[p['rid']]; ts = p['off'] + max(q - p['beat'], 0.0) * RATE(p['semis'])   # 録音の中の秒
            cur = shift_chord(c['chords'][min(int(min(ts, p['off'] + p['dur'] - 0.01) / c['win']), len(c['chords']) - 1)], p['semis'])
    return cur
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P_ = Piece(TOTAL)
    for q in range(TOTAL * BPB): P_.harm[q] = harm_at(q)
    for k in range(TOTAL): P_.tempo[k] = BPM; P_.dyn[k] = 0.5
    for v in VOICES: P_.rest_bars(v, 0, TOTAL)
    P_.section(0, 'I. 洗脳的な入り — 声、鍵盤、主題が回る (♩=60)', '2 小節から声、4 小節から鍵盤、6 小節から tablet89 の主題の出だし (4 半音下げて) が 3 回、少しずつ大きく')
    P_.section(S2, 'II. Requiem I・Fuga I (変ロ短調) と黒い鍵盤', '4 回目からそのまま先へ。鍵盤は 3 分 7 秒から流れ始める。声は 3 分 19 秒まで')
    P_.section(S3, 'III. 鍵盤だけ — 前半の山', '鍵盤が大きくなり、山を築いて、止まる (5 分 15 秒)')
    P_.section(S4, 'IV. 声 (2 回目) と Requiem II (ニ短調) と白い鍵盤', '声が先に入り、2 秒後から白い鍵盤、3 小節後から tablet89 の Requiem II (元の高さ)')
    P_.section(S5, 'V. Fuga II、ストレッタ — 鍵盤のいちばん大きい所', '声は 8 分 26 秒まで')
    P_.section(S6, 'VI. Amen (ニ長調)、鍵盤の終わり', 'tablet89 は 9 分 18 秒に閉じ、鍵盤の終わりが残る (9 分 27 秒)')
    return P_

def post(P_, events, ex):
    for p in PLAYS:
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm)
        env = c.get('env')
        if env and p['envk'] != 1.0: env = [round(v * p['envk'], 4) for v in env]           # くり返しの回は、音量に合わせて波形も小さく描く
        kw = dict(lane=p['lane'], color=list(p['color']), env=env, env_dt=c.get('env_dt', 0.05) / r, env_off=off / r)
        if rid == RV:       # 声: 帯域を削らず、全体の残響を掛けずに前に (声の残響は声の中にある)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:               # 鍵盤と tablet89: これまでの重ね方 (全体の残響)。移調はテープのように速さごと
            add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXIX · Sintesi ipnotica',
        'subtitle': 'tablet89・11/20 の鍵盤・calma の声を、洗脳的に化学合成して。変ロ短調 → ニ短調、♩=60',
        'footer': ['声 = 届いた calma の声。鍵盤 = 11/20 02:40 の録音 (tablet276 と同じ音)。tablet89 は前半だけ 4 半音下げて、鍵盤の調 (変ロ短調) に溶かす。',
                   '鍵盤が白い鍵盤に変わる所で、tablet89 は元の高さ (ニ短調) に戻る。主題の出だしが 3 回回って、4 回目から曲へ。',
                   '楽器は何も加えない。声が先に立ち、曲は 2 小節後から。142 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=279, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.3f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
