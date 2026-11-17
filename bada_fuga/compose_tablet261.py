#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXI · Sfasamento ipnotico a cinque (歌の録音・光輪様の声・tablet89・トラック 8・トラック 18 を重ねて —
  洗脳的で、音声と曲のズレで始まる曲調に)
  5 つの素材:
    歌声        2025/01/08 14:42 の録音から取り出した作曲者の歌声そのもの (voice_only255.py; ハ短調、声は変えない、残響も足さない)
    光輪様の声  届いた 20261112_144938_aureola_ventenne_dolce.mp3 そのまま (11/12 14:49 の声を変換した、優しさに満ちた二十歳の女性の光輪様 3 声)
    トラック 18  2 半音下げてハ短調に (0.891 倍速)
    トラック 8   3 半音上げて変ホ長調 / ハ短調に (1.189 倍速)
    tablet89    LXXXIX — Requiem e Fuga。2 半音下げてハ短調に (0.891 倍速、♩=53.5)。2 つ目の Requiem から終わりまで (元の 160 秒から)
  歌の調 (ハ短調) にテープを合わせる (CCLX と同じ)。テープどうしの高さの関係はこれまでの曲のまま
  音声と曲のズレで始まる: 初めの 2 小節は無音、2 小節 (8 秒) から光輪様の声、その 2 小節後 (16 秒) からトラック 18。
  洗脳的: トラック 18 は出だしの一節 (ラメントの低音、16.5 秒) を 3 回、少しずつ大きく繰り返してから、4 回目でそのまま曲へ。
    光輪様の声は曲の終わりにもう一度戻る (同じ言葉)
  形: I 声 + トラック 18 の出だしが 3 回 → II 声 + トラック 18 → III 歌声 + トラック 8 → IV 歌の終わり + tablet89 の Requiem →
      V 声 (2 回目) + tablet89 のフーガ、ストレッタ → VI Amen (ハ長調)、消える。159 小節
  重ねる位置は濁りの指数で: トラック 18 の 117 秒からトラック 8 (0.19)、トラック 8 の 180 秒後から tablet89 (0.17)。
    歌の入り (合わせて 0.34) と 2 回目の声の入り (0.36) は、声とテープの指数が小さい所
  声と歌声は synth.py の faithful の経路 (帯域を削らず、全体の残響を掛けずに前に)、テープはこれまでの重ね方 (モノラル、全体の残響) で後ろに
  楽器は何も加えない。和音の表示は録音から読んだもの (移調して)。♩=60
  使い方: python compose_tablet261.py <wav のフォルダ (20250108_144205.wav = 取り出した歌声, 20261112_144938.wav = 光輪様の声,
          20261107_180000.wav, 20261107_080000.wav, 20261107_089000.wav = tablet89 の音)> <chords261.json (analyze_chords.py の出力)> [score_tablet261.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet261.json'
GS = float(os.environ.get('GS', '1.1'))                                               # 歌声の音量 (ステムを測って決めた)
GP = float(os.environ.get('GP', '1.0'))                                               # 光輪様の声の音量
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (テープだけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RS, RP, R18, R08, R89 = '20250108_144205', '20261112_144938', '20261107_180000', '20261107_080000', '20261107_089000'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
S18, S8, S89 = -2, 3, -2                        # テープの移調 (歌のハ短調に)
COLP, COLS, COL18, COL8, COL89 = (250, 170, 205), (250, 215, 150), (120, 190, 250), (110, 210, 190), (190, 160, 240)
S_LEN, S_CUT, GS2 = 258.6, 168.0, 1.2           # 歌の後半 (録音の 168 秒から) は静かに歌われているので、歌声を 1.2 倍に
P_OFF, P_LEN = 6.0, 178.3                       # 光輪様の声: 録音の 6.0 秒から (話し始めは 6.5 秒)
P1 = 7.5                                        # 光輪様の声 (1 回目): 2 小節 (8 秒) から話し始める
G_OFF, G_DUR, G_PER = 0.70, 14.8, 14.7 / RATE(S18)    # トラック 18 の出だしの一節: 元の 0.70 秒から 14.8 秒ぶん、くり返しの周期は遅くして 16.5 秒
G_T0, G_GAINS, G18 = 16.0, (0.10, 0.145, 0.205), 0.28 # 1 回目の入りの拍 (4 小節 = 声の 2 小節後)、3 回の音量、本来の音量
TP = G_T0 + len(G_GAINS) * G_PER                # 65.5: 4 回目の出だし = そのまま曲へ
B8 = 196.0                                      # トラック 8: トラック 18 の 117 秒から
VS = 180.0                                      # 歌声: 光輪様の声が終わった所 (2 分 58 秒) から
B89 = B8 + 180.0                                # 376: tablet89 (元の 160 秒 = 2 つ目の Requiem から): トラック 8 の 180 秒後
P2 = 440.0                                      # 光輪様の声 (2 回目): 歌が終わった所 (7 分 17 秒) から
S2, S3, S4, S5, S6, TOTAL = 16, 45, 94, 110, 152, 159
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None, envk=1.0):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout, envk=envk)
PLAYS = [play(RP, P1, GP, 0, P_OFF, P_LEN - P_OFF, 0, COLP, '光輪様の声 — 優しさに満ちた二十歳の女性 (2 小節から)', fin=3.0)]
for k, g in enumerate(G_GAINS):
    PLAYS.append(play(R18, G_T0 + k * G_PER, g, S18, G_OFF, G_DUR, 2, COL18, 'トラック 18 の出だしの一節 — %d 回目%s' % (k + 1, ' (声の 2 小節後から)' if k == 0 else ' (少し大きく)'),
                      fin=5.0 if k == 0 else 0.05, fout=0.25, envk=g / G18))
PLAYS += [play(R18, TP, G18, S18, G_OFF, 149.1 - G_OFF, 2, COL18, 'トラック 18 — 2 半音下げて、4 回目の出だしからそのまま曲へ', fin=0.05),
          play(RS, VS, GS, 0, 0.0, S_CUT, 1, COLS, '2025/01/08 14:42 の歌 — 取り出した歌声そのもの', fin=1.5, fout=0.5),
          play(RS, VS + S_CUT, GS * GS2, 0, S_CUT, S_LEN - S_CUT, 1, COLS, '歌声 — 歌の後半'),
          play(R08, B8, 0.30, S8, 0.0, 232.0, 3, COL8, 'トラック 8 — 3 半音上げて、全部'),
          play(R89, B89, 0.28, S89, 160.0, 231.0, 4, COL89, 'tablet89 — 2 半音下げて、2 つ目の Requiem から終わりまで'),
          play(RP, P2, GP, 0, P_OFF, P_LEN - P_OFF, 0, COLP, '光輪様の声 — もう一度', fin=1.5)]
# 和音の表示を担うテープ (PLAYS の番号, 表示の始まりの拍)
LEAD = [(1, G_T0), (2, G_T0 + G_PER), (3, G_T0 + 2 * G_PER), (4, TP), (7, B8 + 34.0), (8, B89 + 14.0)]
def shift_chord(name, semis):
    i = 2 if len(name) > 1 and name[1] in '#b' else 1
    return {'G#': 'Ab', 'C#': 'Db'}.get(compose.NAMES[(PC[name[:i]] + semis) % 12], compose.NAMES[(PC[name[:i]] + semis) % 12]) + name[i:]   # ハ短調の綴りで (A♭・D♭)
def harm_at(q):
    cur = 'Cm'
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
    P.section(0, 'I. 音声と曲のズレ — 光輪様の声、2 小節後にトラック 18 (♩=60)', '2 小節から声、4 小節からトラック 18 の出だしの一節 (低音が C から G へ下りる) が 3 回、少しずつ大きく')
    P.section(S2, 'II. 光輪様の声とトラック 18', '4 回目の出だしから、トラック 18 はそのまま先へ。声は 2 分 58 秒で終わる')
    P.section(S3, 'III. 歌声とトラック 8', '3 分から歌声。トラック 18 が消え、トラック 8 (3 半音上げて) が前に出る')
    P.section(S4, 'IV. 歌の終わりと tablet89 の Requiem', '6 分 16 秒から tablet89 (2 半音下げて)。歌は 7 分 17 秒で終わる')
    P.section(S5, 'V. 光輪様の声 (2 回目) と tablet89', '声がもう一度。tablet89 はフーガ、ストレッタへ')
    P.section(S6, 'VI. Amen、消える', '声が終わり、tablet89 の Amen (ハ長調) で閉じる')
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
        'title': 'Requiem BADA — CCLXI · Sfasamento ipnotico a cinque',
        'subtitle': '歌声・光輪様の声・tablet89・トラック 8・18 を重ねて。音声と曲のズレで始まる、洗脳的な曲。♩=60',
        'footer': ['入りのズレ: 2 小節 (8 秒) から光輪様の声、その 2 小節後からトラック 18 の出だしの一節 (ラメントの低音) を 3 回、少しずつ大きく、4 回目でそのまま曲へ。',
                   '歌声 (2025/01/08 の録音から取り出した声そのもの、ハ短調) に合わせて、テープをハ短調に: トラック 18 と tablet89 は 2 半音下げ、トラック 8 は 3 半音上げ。',
                   '光輪様の声 → 歌声 → 光輪様の声。歌はトラック 8 に、終わりの声は tablet89 のフーガとストレッタに乗り、Amen で閉じる。楽器は何も加えない。159 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=261, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
