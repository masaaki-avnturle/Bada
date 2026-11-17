#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLX · La mia voce e le due tracce (取り出した歌声そのものに、トラック 18 とトラック 8 を重ねて)
  歌声: voice_only255.py — 2025/01/08 14:42 の録音から取り出した作曲者の歌声 (ハ短調、基音の中央値 156 Hz)。声は変えない
    (高さも速さも響きも、残響も足さない)。synth.py の faithful の経路で、そのまま前に置く
  調を合わせるのはテープの方: トラック 18 (ニ短調) は 2 半音下げてハ短調に (0.891 倍速)、トラック 8 (ハ長調 / イ短調) は 3 半音上げて
    変ホ長調 / ハ短調に (1.189 倍速)。テープどうしの高さの関係 (トラック 8 がトラック 18 の 5 半音上) はこれまでの曲と同じで、
    2 本とも同じだけ遅くなる (1.1225 倍の長さ) ので、テープどうしの重なり方 (濁りの指数) はこれまでと変わらない。
    歌った音だけで測った歌声との指数は、トラック 18 が −2 半音で 0.32 (移調なし 0.33、奇数の半音は 0.40〜0.41)
  形は CCLVI と同じ考え方: 洗脳的な入り (2 小節から歌声、4 小節からトラック 18 の出だしの一節 = ラメントの低音を 3 回、少しずつ大きく、
    4 回目でそのまま曲へ)、歌は 2 回。テープが長くなったぶん並べ方を詰める:
    I: 歌声 + トラック 18 の出だしが 3 回 → II: 歌声 + トラック 18 → III: 歌声 + トラック 8、歌が終わってトラック 8 がつなぐ →
    IV: 歌をもう一度 + トラック 8 の残り、トラック 18 (2 回目) → V: 歌声 + トラック 8 の続き (60 秒から) → VI: トラック 18 の後半、消える。164 小節
  重ねる位置は濁りの指数で: トラック 18 の 117 秒からトラック 8 (0.19)、トラック 8 の 150 秒後 (元の速さで) からトラック 18 の 2 回目 (0.21)、
    トラック 18 の 128 秒からトラック 8 の続き (0.17)、その 52 秒後 (元の速さで) からトラック 18 の後半 (0.25; 歌が終わった直後、
    トラック 8 がひと息つく所を埋める)。2 回目の歌の入りは、歌声と
    テープの指数がいちばん小さい所 (合わせて 0.30)
  楽器は何も加えない。和音の表示は録音から読んだもの (移調して)。♩=60
  使い方: python compose_tablet260.py <wav のフォルダ (20250108_144205.wav = 取り出した歌声, 20261107_180000.wav, 20261107_080000.wav)> <chords260.json (analyze_chords.py の出力)> [score_tablet260.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet260.json'
GV = float(os.environ.get('GV', '1.1'))                                               # 歌声の音量 (ステムを測って決めた)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (テープだけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, R18, R08 = '20250108_144205', '20261107_180000', '20261107_080000'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
S18, S8 = -2, 3                                 # テープの移調: トラック 18 は 2 半音下げ、トラック 8 は 3 半音上げ (歌のハ短調に)
COLV, COL18, COL8 = (250, 215, 150), (120, 190, 250), (110, 210, 190)
V_LEN, V_CUT, GV2 = 258.6, 168.0, 1.12         # 歌の後半 (録音の 168 秒から; 163〜175 秒は歌っていない) は静かに歌われているので、歌声を 1.12 倍に
V1 = 8.0                                        # 1 回目の歌: 2 小節から (tablet219 と同じ入りの間合い)
G_OFF, G_DUR, G_PER = 0.70, 14.8, 14.7 / RATE(S18)    # トラック 18 の出だしの一節: 元の 0.70 秒から 14.8 秒ぶん。くり返しの周期は元の 14.7 秒 = 遅くして 16.5 秒
G_T0, G_GAINS, G18 = 16.0, (0.10, 0.145, 0.205), 0.28 # 1 回目の入りの拍 (4 小節)、3 回の音量、本来の音量
TP = G_T0 + len(G_GAINS) * G_PER                # 65.5: 4 回目の出だし = そのまま曲へ
B8A = 196.0                                     # トラック 8 (1 回目): トラック 18 の 117 秒から
V2 = 304.0                                      # 2 回目の歌
B18_2 = 364.0                                   # トラック 18 の 2 回目: トラック 8 の 168 秒後 (元の速さで 150 秒後)
B8C = 508.0                                     # トラック 8 の続き (元の 60 秒から): トラック 18 (2 回目) の 128 秒から
B18H = 566.0                                    # トラック 18 の後半 (元の 60 秒から): 歌が終わった直後から
S2, S3, S4, S5, S6, TOTAL = 16, 57, 76, 127, 142, 164
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None, envk=1.0):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout, envk=envk)
def song(t0, n, fin):                            # 歌 1 回ぶん (前半と、少し大きくした後半)
    return [play(RV, t0, GV, 0, 0.0, V_CUT, 0, COLV, '2025/01/08 14:42 の歌 — 取り出した歌声そのもの (%d 回目)' % n, fin=fin, fout=0.5),
            play(RV, t0 + V_CUT, GV * GV2, 0, V_CUT, V_LEN - V_CUT, 0, COLV, '歌声 — 歌の後半 (%d 回目)' % n)]
PLAYS = song(V1, 1, 3.0)
for k, g in enumerate(G_GAINS):
    PLAYS.append(play(R18, G_T0 + k * G_PER, g, S18, G_OFF, G_DUR, 1, COL18, 'トラック 18 の出だしの一節 — %d 回目%s' % (k + 1, ' (ゆっくり現れる)' if k == 0 else ' (少し大きく)'),
                      fin=5.0 if k == 0 else 0.05, fout=0.25, envk=g / G18))
PLAYS += [play(R18, TP, G18, S18, G_OFF, 149.1 - G_OFF, 1, COL18, 'トラック 18 — 2 半音下げて、4 回目の出だしからそのまま曲へ', fin=0.05),
          play(R08, B8A, 0.30, S8, 0.0, 232.0, 2, COL8, 'トラック 8 — 3 半音上げて、全部')]
PLAYS += song(V2, 2, 1.5)
PLAYS += [play(R18, B18_2, G18, S18, 0.0, 149.1, 1, COL18, 'トラック 18 — 2 半音下げて (2 回目)'),
          play(R08, B8C, 0.30, S8, 60.0, 172.0, 2, COL8, 'トラック 8 — 3 半音上げて、続き (60 秒から)'),
          play(R18, B18H, 0.24, S18, 60.0, 80.0, 1, COL18, 'トラック 18 — 後半 (60 秒から)')]
# 和音の表示を担うテープ (PLAYS の番号, 表示の始まりの拍)
LEAD = [(2, G_T0), (3, G_T0 + G_PER), (4, G_T0 + 2 * G_PER), (5, TP), (6, B8A + 34.0), (9, B18_2 + 26.0), (10, B8C + 12.0), (11, B18H + 78.0)]
def shift_chord(name, semis):
    i = 2 if len(name) > 1 and name[1] in '#b' else 1
    return compose.NAMES[(PC[name[:i]] + semis) % 12] + name[i:]
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
    P.section(0, 'I. 歌声が入り、トラック 18 が洗脳的に始まる (♩=60)', '2 小節から歌声、4 小節からトラック 18 の出だしの一節 (低音が C から G へ下りる) が 3 回、少しずつ大きく')
    P.section(S2, 'II. 歌声とトラック 18', '4 回目の出だしから、トラック 18 はそのまま先へ。3 分 16 秒からトラック 8 が静かに入る')
    P.section(S3, 'III. 歌声とトラック 8', '歌の後半がトラック 8 に乗る。歌は 4 分 25 秒で終わり、トラック 8 がつなぐ')
    P.section(S4, 'IV. 歌をもう一度 — 歌声とトラック 8、トラック 18', '5 分 4 秒から 2 回目の歌。6 分 4 秒からトラック 18 (2 回目)')
    P.section(S5, 'V. 歌声とトラック 8 の続き', 'トラック 18 が消え、トラック 8 の続きが前に出る。歌は 9 分 21 秒で終わる')
    P.section(S6, 'VI. トラック 18 の後半、消える', '歌が終わってから、トラック 18 の後半が受けて、消える')
    return P

def post(P, events, ex):
    for p in PLAYS:
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm)
        env = c.get('env')
        if env and p['envk'] != 1.0: env = [round(v * p['envk'], 4) for v in env]       # くり返しの段は、音量に合わせて波形も小さく描く
        kw = dict(lane=p['lane'], color=list(p['color']), env=env, env_dt=c.get('env_dt', 0.05) / r, env_off=off / r)
        if rid == RV:       # 歌声: 何も変えずにそのまま前に (帯域も削らず、残響も足さない)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'] if p['fin'] is not None else 0.05, fout=p['fout'] if p['fout'] is not None else 2.0, semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:               # テープ: これまでの重ね方 (モノラル、全体の残響)。移調はテープのように速さごと。入りは 6 秒で立ち上げる
            fin = p['fin'] if p['fin'] is not None else 6.0; fout = p['fout'] if p['fout'] is not None else (6.0 if dur > 150 else 10.0)
            add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=fin, fout=fout, semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLX · La mia voce e le due tracce',
        'subtitle': '取り出した歌声そのもの (声は変えない) に、トラック 18 と 8 をハ短調に合わせて重ねて。歌は 2 回。♩=60',
        'footer': ['歌声 = 2025/01/08 14:42 の録音から取り出した歌声そのもの (ハ短調)。高さも速さも響きも変えず、残響も足さない。',
                   'テープを歌の調に合わせる: トラック 18 は 2 半音下げ (ニ短調 → ハ短調、0.89 倍速)、トラック 8 は 3 半音上げ (変ホ長調 / ハ短調、1.19 倍速)。',
                   '入りは 2 小節から歌声、4 小節からトラック 18 の出だしの一節 (ラメントの低音) を 3 回、少しずつ大きく。歌は 2 回。楽器は何も加えない。164 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=260, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
