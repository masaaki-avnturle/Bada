#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLIII · Lamento ipnotico con attesa (CCLII を、もう少し音声が遅れて、曲が始まるように — tablet219 みたいに)
  入りの間合いは tablet219 (CCXIX) と同じ: 初めの 2 小節は何も鳴らず、2 小節 (8 秒) から声、4 小節 (16 秒) からトラック 18。どちらもゆっくり現れる
    (声は 3 秒、トラック 18 は 5 秒かけて)。CCLII は声が 0.5 秒から、トラック 18 の出だしが 4 秒からだった
  声: CCLI と同じ (make_voice251.py — 倍音の 3 声の、セクシーで可愛い女性の月読様)
  洗脳的な入り (CCLII と同じ作り方): トラック 18 の出だしの一節 (元の 0.70〜15.50 秒; 低音が D → C → B♭ → C → B♭ → A → G → A と下りて属音で止まるラメントの低音) を
    元と同じ周期 14.7 秒で 3 回、少しずつ大きく (0.13 → 0.18 → 0.25)、4 回目の出だしで本来の音量 (0.35) になり、そのまま曲の先へ。
    曲が始まったと分かるように、1 回目を CCLII (0.09) より大きくした。楽器も効果も足さない — トラック 18 の音を並べ直しただけ
  その後は CCLII と同じ重ね方を、入りのぶんずらして: トラック 18 の 96.6 秒からトラック 8 (4 度上げて = 5 半音、1.335 倍速) が静かに入り (濁りの指数 0.21)、
    トラック 8 の 44 秒後からトラック 18 の 2 回目 (0.26)、声の 2 回目とトラック 8 の続き、その 128 秒後からトラック 18 の後半 (0.20)。135 小節
  声は synth.py の faithful の経路 (ステレオのまま、帯域を削らず、全体の残響を掛けずに前に)、テープはこれまでの重ね方 (モノラル、全体の残響) で後ろに
  和音の表示は録音から読んだもの (トラック 8 は 5 半音上げて)。♩=60
  使い方: python compose_tablet253.py <wav のフォルダ (20261112_144938.wav = 倍音の 3 声の月読様の声, 20261107_180000.wav, 20261107_080000.wav)> <chords251.json (analyze_chords.py の出力)> [score_tablet253.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet253.json'
GV = float(os.environ.get('GV', '1.05'))                                              # 声の音量 (CCLI と同じ)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (テープだけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, R18, R08 = '20261112_144938', '20261107_180000', '20261107_080000'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
COLV, COL18, COL8 = (250, 170, 205), (120, 190, 250), (110, 210, 190)
# 洗脳的な入り: トラック 18 の出だしの一節
G_OFF, G_DUR, G_PER = 0.70, 14.8, 14.7        # 元の 0.70 秒から 14.8 秒ぶん (15.50 秒まで)、くり返しの周期 14.7 秒
V_T0, V_OFF, V_FIN = 7.5, 6.0, 3.0                                                    # 声: 録音の 6.0 秒から (話し始めは 6.56 秒) を 7.5 拍に置く → 2 小節 (8 秒) から声。3 秒かけて現れる
G_T0, G_GAINS, G18 = 16.0, (0.13, 0.18, 0.25), 0.35                                   # 1 回目の入りの拍 (4 小節)、3 回の音量、本来の音量
TP = G_T0 + len(G_GAINS) * G_PER                                                      # 60.1: 4 回目の出だし = そのまま曲へ
B8 = 156.0                                                                            # トラック 8 の入り (トラック 18 の 96.6 秒)
S2, S3, S4, S5, TOTAL = 15, 45, 80, 115, 135
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None, envk=1.0):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout, envk=envk)
PLAYS = [play(RV, V_T0, GV, 0, V_OFF, 178.3 - V_OFF, 0, COLV, '11/12 14:49 の声 — 倍音の 3 声の月読様 (2 小節から、ゆっくり現れる)', fin=V_FIN)]
for k, g in enumerate(G_GAINS):
    PLAYS.append(play(R18, G_T0 + k * G_PER, g, 0, G_OFF, G_DUR, 1, COL18, 'トラック 18 の出だしの一節 — %d 回目%s' % (k + 1, ' (4 小節から、ゆっくり現れる)' if k == 0 else ' (少し大きく)'),
                      fin=5.0 if k == 0 else 0.05, fout=0.25, envk=g / G18))
PLAYS += [play(R18, TP, G18, 0, G_OFF, 149.1 - G_OFF, 1, COL18, 'トラック 18 — 4 回目の出だしから、そのまま曲へ', fin=0.05),
          play(R08, B8, 0.45, 5, 0.0, 232.0, 2, COL8, 'トラック 8 — 4 度上げて、全部'),
          play(R18, B8 + 44.0, 0.4, 0, 0.0, 149.1, 1, COL18, 'トラック 18 — そのまま (2 回目)'),
          play(RV, B8 + 164.0, GV, 0, 0.0, 178.3, 0, COLV, '11/12 14:49 の声 — 倍音の 3 声の月読様 (もう一度)'),
          play(R08, B8 + 176.0, 0.32, 5, 60.0, 172.0, 2, COL8, 'トラック 8 — 4 度上げて、続き (60 秒から)'),
          play(R18, B8 + 304.0, 0.36, 0, 60.0, 80.0, 1, COL18, 'トラック 18 — 後半 (60 秒から)')]
# 和音の表示を担うテープ (PLAYS の番号, 表示の始まりの拍)
LEAD = [(1, G_T0), (2, G_T0 + G_PER), (3, G_T0 + 2 * G_PER), (4, TP), (5, B8 + 27.0), (8, B8 + 176.0), (9, B8 + 304.0)]
def shift_chord(name, semis):
    i = 2 if len(name) > 1 and name[1] in '#b' else 1
    return compose.NAMES[(PC[name[:i]] + semis) % 12] + name[i:]
def harm_at(q):
    cur = 'Dm'
    for k, a in LEAD:
        p = PLAYS[k]
        if q >= a:
            c = CH[p['rid']]; ts = p['off'] + max(q - p['beat'], 0.0) * RATE(p['semis'])   # 録音の中の秒
            cur = shift_chord(c['chords'][min(int(min(ts, p['off'] + p['dur'] - 0.01) / c['win']), len(c['chords']) - 1)], p['semis'])
    return cur
extras = []
def add(v, beat, dbeats, m, gain, label=None, **kw): extras.append(dict(v=v, beat=round(beat, 4), dbeats=round(dbeats, 4), m=int(m), gain=round(gain, 4), label=label, **kw))

def build():
    P = Piece(TOTAL)
    for q in range(TOTAL * BPB): P.harm[q] = harm_at(q)
    for k in range(TOTAL): P.tempo[k] = BPM; P.dyn[k] = 0.5
    for v in VOICES: P.rest_bars(v, 0, TOTAL)
    P.section(0, 'I. 声が少し遅れて入り、トラック 18 が洗脳的に始まる (♩=60)', '2 小節から月読様の声、4 小節からトラック 18 の出だしの一節 (低音が D から A へ下りる) が 3 回、少しずつ大きく')
    P.section(S2, 'II. トラック 18 が曲に入る', '4 回目の出だしから、トラック 18 はそのまま先へ。2 分 36 秒からトラック 8 が静かに入る')
    P.section(S3, 'III. トラック 8 とトラック 18', '声が終わる所でトラック 8 (4 度上げて) が前に出る。3 分 20 秒からトラック 18 をもう一度')
    P.section(S4, 'IV. 月読様の声 (2 回目) とトラック 8 の続き', '月読様の声をもう一度、トラック 8 の続き (60 秒から)')
    P.section(S5, 'V. トラック 18 の後半、消える', 'トラック 18 の後半が声の終わりを受けて、消える')
    return P

def post(P, events, ex):
    for p in PLAYS:
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm); dt = c.get('env_dt', 0.05)
        env = c.get('env')
        if env and p['envk'] != 1.0: env = [round(v * p['envk'], 4) for v in env]       # くり返しの段は、音量に合わせて波形も小さく描く
        kw = dict(lane=p['lane'], color=list(p['color']), env=env, env_dt=dt / r, env_off=off / r)
        if rid == RV:       # 声: 帯域を削らず、ステレオのまま、全体の残響を掛けずに前に (声の残響は声の中にある)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'] if p['fin'] is not None else 0.05, fout=2.0, semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:               # テープ: これまでの重ね方 (モノラル、全体の残響)。入りは 6 秒で立ち上げる (くり返しと 4 回目の出だしは、無音の所からそのまま)
            fin = p['fin'] if p['fin'] is not None else 6.0; fout = p['fout'] if p['fout'] is not None else (6.0 if dur > 150 else 10.0)
            add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=fin, fout=fout, semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLIII · Lamento ipnotico con attesa',
        'subtitle': '声は少し遅れて 2 小節から、トラック 18 は 4 小節から洗脳的に始まる (tablet219 と同じ入りの間合い)。♩=60',
        'footer': ['入りの間合いは tablet219 と同じ: 2 小節 (8 秒) から月読様の声 (CCLI と同じ倍音の 3 声)、4 小節 (16 秒) からトラック 18。どちらもゆっくり現れる。',
                   'トラック 18 は出だしの一節 (低音が D → C → B♭ → A と下りるラメントの形、14.7 秒) を 3 回、少しずつ大きく繰り返し、4 回目でそのまま曲に入る。',
                   '楽器は何も加えない。トラック 18 はそのまま、トラック 8 は 4 度上げて。声が入ってからは音は途切れない (135 小節)。']}

if __name__ == '__main__':
    compose.main(OUT, seed=253, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
