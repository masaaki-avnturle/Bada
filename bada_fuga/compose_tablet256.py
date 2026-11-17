#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLVI · Il canto della donna aureola (tablet255 を洗脳的な入りにして、歌を 2 回、女性の声を大人の 20 代に)
  歌声: make_voice256.py — 2025/01/08 14:42 の歌から取り出した歌声を 7 半音上げて、大人の 20 代の女性の歌声に (基音の中央値 B♭3、音域 F3〜D4、
    フォルマント 1.11 倍)。光輪 = 倍音の 2 声 (ちょうど 2 倍と 3 倍) と残響、ドエロ = 息の多い発声と囁きの層、近さ。ステレオ
  洗脳的な入り (CCLII〜CCLIV と同じ作り方、間合いは tablet219): 2 小節 (8 秒) から歌声、4 小節 (16 秒) からトラック 18 の出だしの一節
    (元の 0.70〜15.50 秒; 低音が D → C → B♭ → C → B♭ → A → G → A と下りて属音で止まるラメントの低音) を元と同じ周期 14.7 秒で 3 回、
    少しずつ大きく (0.12 → 0.17 → 0.24)、4 回目の出だしで本来の音量 (0.33) になり、そのまま曲の先へ
  歌は 2 回 (各 4 分 19 秒)。どちらも歌の前半をトラック 18、後半をトラック 8 (4 度上げて = 5 半音、1.335 倍速) に乗せる:
    I: 歌声 + トラック 18 の出だしが 3 回 → II: 歌声 + トラック 18 → III: 歌声 + トラック 8、歌が終わってトラック 8 がつなぐ →
    IV: 歌をもう一度 + トラック 18 (2 回目) → V: 歌声 + トラック 8 (2 回目) → VI: トラック 18 の後半、消える。164 小節
  重ねる位置は濁りの指数 (analyze_chords.py の節を参照) で: トラック 18 の 112 秒からトラック 8 (0.20)、トラック 8 の 148 秒後からトラック 18 の 2 回目 (0.20)、
    トラック 8 の 144 秒後からトラック 18 の後半 (0.27; 歌の最後の句に重ならないように、歌が終わってから入る)
  歌声は synth.py の faithful の経路 (ステレオのまま、帯域を削らず、全体の残響を掛けずに前に)、テープはこれまでの重ね方 (モノラル、全体の残響) で後ろに
  楽器は何も加えない。和音の表示は録音から読んだもの (トラック 8 は 5 半音上げて)。♩=60
  使い方: python compose_tablet256.py <wav のフォルダ (20250108_144205.wav = 大人の光輪様の歌声, 20261107_180000.wav, 20261107_080000.wav)> <chords256.json (analyze_chords.py の出力)> [score_tablet256.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet256.json'
GV = float(os.environ.get('GV', '1.15'))                                              # 歌声の音量 (ステムを測って決めた)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (テープだけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RV, R18, R08 = '20250108_144205', '20261107_180000', '20261107_080000'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
COLV, COL18, COL8 = (240, 150, 175), (120, 190, 250), (110, 210, 190)
V_LEN, V_CUT, GV2 = 258.6, 168.0, 1.2          # 歌の後半 (録音の 168 秒から; 163〜175 秒は歌っていない) は静かに歌われているので、歌声を 1.2 倍に
V1 = 8.0                                        # 1 回目の歌: 2 小節から (tablet219 と同じ入りの間合い)
G_OFF, G_DUR, G_PER = 0.70, 14.8, 14.7          # トラック 18 の出だしの一節: 元の 0.70 秒から 14.8 秒ぶん、くり返しの周期 14.7 秒
G_T0, G_GAINS, G18 = 16.0, (0.12, 0.17, 0.24), 0.33                                   # 1 回目の入りの拍 (4 小節)、3 回の音量、本来の音量
TP = G_T0 + len(G_GAINS) * G_PER                                                      # 60.1: 4 回目の出だし = そのまま曲へ
B8A = 172.0                                                                           # トラック 8 (1 回目): トラック 18 の 112.6 秒から
B18_2 = B8A + 148.0                                                                   # 320: トラック 18 の 2 回目 (トラック 8 の 148 秒後)
V2 = B18_2 - 8.0                                                                      # 312: 2 回目の歌 (トラック 18 の 8 秒前、1 回目と同じ間合い)
B8B = B18_2 + 112.0                                                                   # 432: トラック 8 (2 回目)
B18H = B8B + 144.0                                                                    # 576: トラック 18 の後半 (歌が終わってから)
S2, S3, S4, S5, S6, TOTAL = 15, 50, 78, 115, 144, 164
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None, envk=1.0):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout, envk=envk)
def song(t0, n, fin):                            # 歌 1 回ぶん (前半と、少し大きくした後半)
    return [play(RV, t0, GV, 0, 0.0, V_CUT, 0, COLV, '2025/01/08 14:42 の歌 — 大人の 20 代の光輪様の歌声 (%d 回目)' % n, fin=fin, fout=0.5),
            play(RV, t0 + V_CUT, GV * GV2, 0, V_CUT, V_LEN - V_CUT, 0, COLV, '光輪様の歌声 — 歌の後半 (%d 回目)' % n)]
PLAYS = song(V1, 1, 3.0)
for k, g in enumerate(G_GAINS):
    PLAYS.append(play(R18, G_T0 + k * G_PER, g, 0, G_OFF, G_DUR, 1, COL18, 'トラック 18 の出だしの一節 — %d 回目%s' % (k + 1, ' (4 小節から、ゆっくり現れる)' if k == 0 else ' (少し大きく)'),
                      fin=5.0 if k == 0 else 0.05, fout=0.25, envk=g / G18))
PLAYS += [play(R18, TP, G18, 0, G_OFF, 149.1 - G_OFF, 1, COL18, 'トラック 18 — 4 回目の出だしから、そのまま曲へ', fin=0.05),
          play(R08, B8A, 0.32, 5, 0.0, 232.0, 2, COL8, 'トラック 8 — 4 度上げて、全部')]
PLAYS += song(V2, 2, 1.5)
PLAYS += [play(R18, B18_2, G18, 0, 0.0, 149.1, 1, COL18, 'トラック 18 — そのまま (2 回目)'),
          play(R08, B8B, 0.32, 5, 0.0, 232.0, 2, COL8, 'トラック 8 — 4 度上げて、全部 (2 回目)'),
          play(R18, B18H, 0.24, 0, 60.0, 80.0, 1, COL18, 'トラック 18 — 後半 (60 秒から)')]
# 和音の表示を担うテープ (PLAYS の番号, 表示の始まりの拍)
LEAD = [(2, G_T0), (3, G_T0 + G_PER), (4, G_T0 + 2 * G_PER), (5, TP), (6, B8A + 27.0), (9, B18_2 + 24.0), (10, B8B + 27.0), (11, B18H + 40.0)]
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
    P.section(0, 'I. 光輪様の歌声が入り、トラック 18 が洗脳的に始まる (♩=60)', '2 小節から歌声、4 小節からトラック 18 の出だしの一節 (低音が D から A へ下りる) が 3 回、少しずつ大きく')
    P.section(S2, 'II. 歌声とトラック 18', '4 回目の出だしから、トラック 18 はそのまま先へ。2 分 52 秒からトラック 8 が静かに入る')
    P.section(S3, 'III. 歌声とトラック 8', '歌の後半がトラック 8 (4 度上げて) に乗る。歌は 4 分 25 秒で終わり、トラック 8 がつなぐ')
    P.section(S4, 'IV. 歌をもう一度 — 歌声とトラック 18', '5 分 12 秒から 2 回目の歌、5 分 20 秒からトラック 18 (2 回目)')
    P.section(S5, 'V. 歌声とトラック 8 (2 回目)', 'トラック 18 が消え、トラック 8 が前に出る。歌の後半は 8 分 7 秒から')
    P.section(S6, 'VI. トラック 18 の後半、消える', '歌が終わり (9 分 29 秒)、トラック 18 の後半が受けて、消える')
    return P

def post(P, events, ex):
    for p in PLAYS:
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm)
        env = c.get('env')
        if env and p['envk'] != 1.0: env = [round(v * p['envk'], 4) for v in env]       # くり返しの段は、音量に合わせて波形も小さく描く
        kw = dict(lane=p['lane'], color=list(p['color']), env=env, env_dt=c.get('env_dt', 0.05) / r, env_off=off / r)
        if rid == RV:       # 歌声: 帯域を削らず、ステレオのまま、全体の残響を掛けずに前に (光輪の響きは声の中にある)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'] if p['fin'] is not None else 0.05, fout=p['fout'] if p['fout'] is not None else 2.0, semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:               # テープ: これまでの重ね方 (モノラル、全体の残響)。入りは 6 秒で立ち上げる (くり返しと 4 回目の出だしは、無音の所からそのまま)
            fin = p['fin'] if p['fin'] is not None else 6.0; fout = p['fout'] if p['fout'] is not None else (6.0 if dur > 150 else 10.0)
            add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=fin, fout=fout, semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLVI · Il canto della donna aureola',
        'subtitle': '大人の 20 代の女性の光輪様の歌声で、歌を 2 回。トラック 18 は洗脳的に始まる。ニ短調、♩=60',
        'footer': ['歌声 = 2025/01/08 14:42 の歌から取り出した歌声を 7 半音上げて、大人の 20 代の女性に (基音の中央値 B♭3、フォルマント 1.11 倍)。息と囁き、倍音の 2 声と残響。',
                   '入り: 2 小節から歌声、4 小節からトラック 18 の出だしの一節 (ラメントの低音、14.7 秒) を 3 回、少しずつ大きく、4 回目でそのまま曲に入る。',
                   '歌は 2 回。どちらも前半をトラック 18、後半をトラック 8 (4 度上げて) に乗せ、最後をトラック 18 の後半が受ける。楽器は何も加えない。164 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=256, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
