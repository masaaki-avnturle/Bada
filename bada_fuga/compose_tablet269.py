#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXIX · La diciassettenne canta (recording の声を tablet266 と同じにして — 歌も 17 歳の 3 声の倍音の声で、調もテープも tablet266 のまま)
  CCLXVIII (tablet266 と、取り出した歌声を重ねたもの) の歌声を、tablet266 の声と同じ声に作り換える:
    歌声        make_voice269.py — 2025/01/08 14:42 の歌 (男声、ハ短調) を、倍音の 3 声の 17 歳のホッとする女性の歌声に。14 半音上げて
                ニ短調 (tablet266 のテープの調) にしたので、テープを移さなくてよくなった
    17 歳の声    make_voice266.py の声そのまま (tablet266 と同じ)
    トラック 18  そのまま (ニ短調) — tablet266 と同じ
    トラック 8   4 度上げて (5 半音、1.335 倍速、ニ短調 / ヘ長調) — tablet266 と同じ
  形: tablet266 の並びの、テープだけになる間の所に歌を置く (CCLXVIII と同じ考え方)。初めの 3 分は tablet266 そのまま
    (2 小節から声、4 小節からトラック 18 の出だしの一節を 3 回、4 回目でそのまま曲へ、2 分 36 秒からトラック 8)。歌は 4 分 19 秒あるので、
    トラック 18 の 2 回目をトラック 8 の 164 秒後に置いて (tablet266 は 44 秒後)、その先を 120 秒ずらす:
    I: 17 歳の声 + トラック 18 の出だしが 3 回 → II: 17 歳の声 + トラック 18 → III: 歌声 + トラック 8 → IV: 歌の続き + トラック 18 (2 回目) →
    V: 17 歳の声 (2 回目) + トラック 8 の続き → VI: トラック 18 の後半、消える。話し声と歌声は重ねない。165 小節
  重ねる位置 (濁りの指数): トラック 18 の 96.6 秒からトラック 8 (0.21)、トラック 8 の 164 秒後 (トラック 8 が消えていく所) からトラック 18 の 2 回目 (0.24)、
    その 132 秒後からトラック 8 の続き (0.15)、その 126 秒後 (トラック 8 の続きが消える所) からトラック 18 の後半 (0.20)。
    歌の入りは 3 分 9 秒: 歌った音で測ったテープとの指数は 0.34 (1 秒ずつ動かしても 0.31〜0.35)。トラック 8 の短い休み (曲の 4 分 13〜17 秒) を
    歌の句がちょうど覆う位置 (その間はほかのテープが鳴っていない)。
    トラック 18 の 2 回目を 5 分 20 秒に置くと、歌の前半と後半の間の息継ぎ (5 分 52 秒〜6 分 4 秒) にトラック 18 の最初の山が来る
    (5 分 4 秒に置くと、そこがトラック 18 のいちばん静かな所と重なって 3 秒ほど −36 dB まで静まった)
  声と歌声は synth.py の faithful の経路 (帯域を削らず、全体の残響を掛けずに前に; 声の残響は声の中にある)、テープはこれまでの重ね方 (モノラル、全体の残響) で後ろに
  楽器は何も加えない。和音の表示は録音から読んだもの (トラック 8 は 5 半音上げて)。♩=60
  使い方: python compose_tablet269.py <wav のフォルダ (20250108_144205.wav = make_voice269.py の歌声, 20261112_144938.wav = make_voice266.py の声,
          20261107_180000.wav, 20261107_080000.wav)> <chords269.json (analyze_chords.py の出力)> [score_tablet269.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet269.json'
GS = float(os.environ.get('GS', '1.4'))                                               # 歌声の音量 (ステムを測って決めた)
GP = float(os.environ.get('GP', '1.15'))                                              # 17 歳の声の音量 (tablet266 と同じ)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (テープだけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RS, RP, R18, R08 = '20250108_144205', '20261112_144938', '20261107_180000', '20261107_080000'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
S18, S8 = 0, 5                                  # テープの高さは tablet266 と同じ (トラック 18 はそのまま、トラック 8 は 4 度上げて)
COLP, COLS, COL18, COL8 = (255, 200, 205), (255, 170, 215), (120, 190, 250), (110, 210, 190)
S_LEN, S_CUT, GS2 = 258.6, 168.0, 1.15          # 歌の後半 (録音の 168 秒から; 163〜175 秒は歌っていない) は静かに歌われている (歌っている所の音量が 2.5 dB 小さい) ので、歌声を 1.15 倍に
P_OFF, P_LEN = 6.0, 178.3                       # 17 歳の声: 録音の 6.0 秒から (話し始めは 6.5 秒)
P1 = 7.5                                        # 17 歳の声 (1 回目): 2 小節 (8 秒) から話し始める
G_OFF, G_DUR, G_PER = 0.70, 14.8, 14.7                # トラック 18 の出だしの一節: 元の 0.70 秒から 14.8 秒ぶん、くり返しの周期 14.7 秒
G_T0, G_GAINS, G18 = 16.0, (0.13, 0.18, 0.25), 0.35   # 1 回目の入りの拍 (4 小節 = 声の 2 小節後)、3 回の音量、本来の音量 (tablet266 と同じ)
TP = G_T0 + len(G_GAINS) * G_PER                # 60.1: 4 回目の出だし = そのまま曲へ
B8 = 156.0                                      # トラック 8: トラック 18 の 96.6 秒から (tablet266 と同じ)
VS = 189.0                                      # 歌声: 17 歳の声が終わった所 (2 分 57 秒) の後、3 分 9 秒から (トラック 8 の短い休みを歌の句で覆う位置)
B18_2 = B8 + 164.0                              # 320: トラック 18 の 2 回目: トラック 8 の 164 秒後 (トラック 8 が消えていく所)
P2 = 453.0                                      # 17 歳の声 (2 回目): 歌が終わった所 (7 分 26 秒) の後、7 分 33.5 秒から話し始める (トラック 8 の続きの短い休みを声で覆う位置)
B8C = B18_2 + 132.0                             # 452: トラック 8 の続き (元の 60 秒から): トラック 18 (2 回目) の 132 秒から
B18H = B8C + 126.0                              # 578: トラック 18 の後半 (元の 60 秒から): トラック 8 の続きが消える所に重ねて入る
S2, S3, S4, S5, S6, TOTAL = 15, 47, 80, 113, 145, 165
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None, envk=1.0):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout, envk=envk)
PLAYS = [play(RP, P1, GP, 0, P_OFF, P_LEN - P_OFF, 0, COLP, '11/12 14:49 の声 — 倍音の 3 声の、17 歳のホッとする声 (2 小節から)', fin=1.0)]
for k, g in enumerate(G_GAINS):
    PLAYS.append(play(R18, G_T0 + k * G_PER, g, S18, G_OFF, G_DUR, 2, COL18, 'トラック 18 の出だしの一節 — %d 回目%s' % (k + 1, ' (声の 2 小節後から)' if k == 0 else ' (少し大きく)'),
                      fin=5.0 if k == 0 else 0.05, fout=0.25, envk=g / G18))
PLAYS += [play(R18, TP, G18, S18, G_OFF, 149.1 - G_OFF, 2, COL18, 'トラック 18 — 4 回目の出だしから、そのまま曲へ', fin=0.05),
          play(RS, VS, GS, 0, 0.0, S_CUT, 1, COLS, '2025/01/08 14:42 の歌 — 倍音の 3 声の、17 歳の歌声', fin=1.5, fout=0.5),
          play(RS, VS + S_CUT, GS * GS2, 0, S_CUT, S_LEN - S_CUT, 1, COLS, '歌声 — 歌の後半'),
          play(R08, B8, 0.38, S8, 0.0, 232.0, 3, COL8, 'トラック 8 — 4 度上げて、全部'),          # 歌の下なので、tablet266 (0.45) より控えめに
          play(R18, B18_2, 0.30, S18, 0.0, 149.1, 2, COL18, 'トラック 18 — そのまま (2 回目)'),     # 歌の下なので、tablet266 (0.40) より控えめに
          play(RP, P2, GP, 0, P_OFF, P_LEN - P_OFF, 0, COLP, '17 歳の声 — もう一度', fin=1.0),
          play(R08, B8C, 0.32, S8, 60.0, 172.0, 3, COL8, 'トラック 8 — 4 度上げて、続き (60 秒から)'),
          play(R18, B18H, 0.36, S18, 60.0, 80.0, 2, COL18, 'トラック 18 — 後半 (60 秒から)')]
# 和音の表示を担うテープ (PLAYS の番号, 表示の始まりの拍)
LEAD = [(1, G_T0), (2, G_T0 + G_PER), (3, G_T0 + 2 * G_PER), (4, TP), (7, B8 + 27.0), (8, B8 + 174.0), (10, B8C + 12.0), (11, B18H)]
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
    P.section(0, 'I. 音声と曲のズレ — 17 歳の声、2 小節後にトラック 18 (♩=60)', '2 小節から声、4 小節からトラック 18 の出だしの一節 (低音が D から A へ下りる) が 3 回、少しずつ大きく')
    P.section(S2, 'II. 17 歳の声とトラック 18', '4 回目の出だしから、トラック 18 はそのまま先へ。2 分 36 秒からトラック 8。声は 2 分 57 秒で終わる')
    P.section(S3, 'III. 17 歳の歌声とトラック 8', '3 分 9 秒から歌声 (同じ 17 歳の声で)。トラック 18 が消え、トラック 8 (4 度上げて) が前に出る')
    P.section(S4, 'IV. 歌の続きとトラック 18 (2 回目)', '5 分 20 秒からトラック 18 をもう一度。トラック 8 は 5 分 30 秒まで。歌は 7 分 26 秒で終わる')
    P.section(S5, 'V. 17 歳の声 (2 回目) とトラック 8 の続き', '7 分 34 秒から声がもう一度、トラック 8 の続き (60 秒から) に乗って')
    P.section(S6, 'VI. トラック 18 の後半、消える', 'トラック 18 の後半が声の終わり (10 分 23 秒) を受けて、消える')
    return P

def post(P, events, ex):
    for p in PLAYS:
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm)
        env = c.get('env')
        if env and p['envk'] != 1.0: env = [round(v * p['envk'], 4) for v in env]       # くり返しの段は、音量に合わせて波形も小さく描く
        kw = dict(lane=p['lane'], color=list(p['color']), env=env, env_dt=c.get('env_dt', 0.05) / r, env_off=off / r)
        if rid in (RS, RP):  # 声と歌声: 何も変えずにそのまま前に (帯域も削らず、全体の残響も掛けない)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'] if p['fin'] is not None else 0.05, fout=p['fout'] if p['fout'] is not None else 2.0, semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:               # テープ: これまでの重ね方 (モノラル、全体の残響)。移調はテープのように速さごと。入りは 6 秒で立ち上げる
            fin = p['fin'] if p['fin'] is not None else 6.0; fout = p['fout'] if p['fout'] is not None else (6.0 if dur > 150 else 10.0)
            add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=fin, fout=fout, semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXIX · La diciassettenne canta',
        'subtitle': '歌の録音の声を、tablet266 と同じ 17 歳の声に。調もテープも tablet266 のまま。♩=60',
        'footer': ['歌声 = 2025/01/08 の歌を、tablet266 の声と同じ作りの 17 歳の女性の歌声に (基音・2 倍・3 倍の 3 声)。14 半音上げて、tablet266 と同じニ短調に。',
                   '話し声もテープも tablet266 のまま: 17 歳の声、トラック 18 はそのまま、トラック 8 は 4 度上げて。初めの 3 分は tablet266 と同じ。',
                   '17 歳の声 → 同じ声の歌 → 17 歳の声。話し声と歌声は重ねない。楽器は何も加えない。165 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=269, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
