#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requiem BADA — Tablet Sessions CCLXXIV · L'aureola calma e la Messia (音声を女性のメシア様の優しい音声で、曲 — tablet267 — に重ねて)
  届いたもの: tablet267-2.mp4 (CCLXVII そのもの: calma の声・トラック 18・トラック 8) と 20250108_144205_aureola_donna_sensuale.mp3 (CCLV の歌声)。
  mp4 の音に歌を上から重ねるのではなく、tablet267 の素材から組み直す (CCLXVIII・CCLXIX と同じ考え方 — 話し声と歌声を重ねないため):
    歌声        make_voice273.py (14 半音上げ) — 2025/01/08 14:42 の歌を、女性のメシア様の優しい歌声に。ニ短調 (tablet267 のテープの調) なので、テープは移さない
    calma の声   届いていた 20261108_145525_aureola_sensuale_calma.mp3 そのまま (tablet267 と同じ; 3 つに分けて音量だけ整える)
    トラック 18  そのまま (ニ短調) — tablet267 と同じ
    トラック 8   4 度上げて (5 半音、1.335 倍速) — tablet267 と同じ
  形: 初めの 3 分 19 秒は tablet267 そのまま (トラック 18 が初めから、2 小節から calma の声、1 分 36 秒からトラック 8)。
    tablet267 では声と声の間が 1 分 53 秒しかない。歌は 4 分 16 秒あるので、テープを足して間を延ばす:
    I: トラック 18 + calma の声 → II: 声 + トラック 8 (声は 3 分 19 秒まで) → III: メシア様の歌声 (3 分 28 秒から) + トラック 8 の終わり + トラック 18 (2 回目) →
    IV: 歌の後半 + トラック 8 (2 回目、全部) → V: calma の声 (2 回目、7 分 50 秒から) + トラック 8 → VI: トラック 18 (3 回目) が声の終わりを受けて、消える。
    話し声と歌声は重ねない。170 小節
  重ねる位置 (濁りの指数; どれもこれまでの曲で使った関係):
    トラック 18 の 96.6 秒からトラック 8 (0.21)、トラック 8 の 164 秒後 (消えていく所) からトラック 18 の 2 回目 (0.24)、
    その 124 秒後からトラック 8 の 2 回目 (0.18)、その 148 秒後からトラック 18 の 3 回目 (0.20)。歌った音とテープの指数は 0.35
  静まる所を埋める:
    トラック 8 の短い休み (1 回目は 3 分 13〜17 秒、2 回目は 8 分 1〜5 秒) は、どちらも calma の声が覆う。
    トラック 8 (1 回目) は、声が終わった所 (3 分 20〜25 秒) で音量を 0.45 から 0.34 に下げる (歌の入りがトラック 8 の大きい所に重なるため; 同じ録音を 5 秒重ねて音量だけ移す)。
    歌の長い息継ぎ (6 分 14〜22 秒) にはトラック 18 (2 回目) の大きい所が来る。トラック 18 の静かな所 (元の 56・90・108 秒) は歌か声が覆う
  声と歌声は synth.py の faithful の経路 (帯域を削らず、全体の残響を掛けずに前に; 声の残響は声の中にある)、テープはこれまでの重ね方 (モノラル、全体の残響) で後ろに
  楽器は何も加えない。和音の表示は録音から読んだもの (トラック 8 は 5 半音上げて)。♩=60
  使い方: python compose_tablet274.py <wav のフォルダ (20250108_144205.wav = make_voice273.py の歌声 (14 半音), 20261108_145525.wav = calma の声,
          20261107_180000.wav, 20261107_080000.wav)> <chords274.json (analyze_chords.py の出力)> [score_tablet274.json]
"""
import sys, os, json, math
WDIR, CHP = os.path.abspath(sys.argv[1]), sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else 'score_tablet274.json'
GS = float(os.environ.get('GS', '1.4'))                                               # 歌声の音量 (ステムを測って決める)
GS2 = float(os.environ.get('GS2', '1.15'))                                            # 歌の後半は静かに歌われているので、少し上げる
GV = float(os.environ.get('GV', '1.1'))                                               # calma の声の音量 (tablet267 と同じ)
GK1, GK2 = float(os.environ.get('GK1', '1.7')), float(os.environ.get('GK2', '1.25'))    # 静かな話し始めの持ち上げ (tablet267 と同じ)
G8A = float(os.environ.get('G8A', '0.45'))                                             # トラック 8 (1 回目): calma の声の下では tablet267 と同じ
G8S = float(os.environ.get('G8S', '0.34'))                                             # 声が終わったら (3 分 20〜25 秒)、歌の下になるので控えめに — 音量のつまみだけ
G18B = float(os.environ.get('G18B', '0.30')); G8B = float(os.environ.get('G8B', '0.27')); G18C = float(os.environ.get('G18C', '0.30'))   # トラック 18 (2 回目)、トラック 8 (2 回目)、トラック 18 (3 回目)
sys.argv = [sys.argv[0], '/dev/null']
from compose import *
import compose
CH = json.load(open(CHP))
BANKP = os.path.join(os.path.dirname(os.path.abspath(OUT)), 'bank_empty.json')         # サンプラーの音は使わない (テープだけ) ので、空の bank
json.dump({'recordings': {}, 'samples': []}, open(BANKP, 'w'))
RS, RV, R18, R08 = '20250108_144205', '20261108_145525', '20261107_180000', '20261107_080000'
BPM = 60
RATE = lambda semis: 2 ** (semis / 12.0)
COLV, COLS, COL18, COL8 = (255, 190, 160), (255, 226, 170), (120, 190, 250), (110, 210, 190)
V_OFF, V_CUT, V_CUT2, V_LEN = 4.86, 50.7, 82.25, 198.46                               # calma の声: 録音の 4.86 秒から (話し始めは 5.36 秒)。50.7 秒と 82.25 秒で 3 つに分けて置く (tablet267 と同じ)
S_LEN, S_ON, S_CUT = 258.6, 0.4, 168.0                                                # 歌: 歌い出しは 0.4 秒、歌い終わりは 256.4 秒。後半は 168 秒から (166.5〜174.4 秒は歌っていない)
V1 = 7.5                                                                              # calma の声 (1 回目): 2 小節 (8 秒) から話し始める。3 分 19 秒まで
B8 = 96.0                                                                             # トラック 8 (1 回目): トラック 18 の 96.6 秒から
VS = 208.0 - S_ON                                                                     # 207.6: 歌声: 声が終わった 9 秒後、52 小節 (3 分 28 秒) から歌い出す
X8, XF = 104.0, 5.0                                                                   # トラック 8 (1 回目) の音量を下げる所: 入りの 104 秒後 (曲の 3 分 20 秒) から 5 秒かけて
T2 = B8 + 164.0                                                                       # 260: トラック 18 の 2 回目: トラック 8 が消えていく所から
B8B = T2 + 124.0                                                                      # 384: トラック 8 の 2 回目 (全部): 歌の後半の頭 (382 秒) に重ねて入る
V2 = 470.0 - (5.36 - V_OFF)                                                           # 469.5: calma の声 (2 回目): 歌が終わった (7 分 44 秒) 6 秒後、7 分 50 秒から話し始める
T3 = B8B + 148.0                                                                      # 532: トラック 18 の 3 回目: 声の終わり (11 分 1 秒) の 3 秒後から、自分で消えていく
S2, S3, S4, S5, S6, TOTAL = 24, 52, 96, 117, 140, 170
def play(rid, beat, gain, semis, off, dur, lane, color, tag, fin=None, fout=None):
    return dict(rid=rid, beat=beat, gain=gain, semis=semis, off=off, dur=dur, lane=lane, color=color, tag=tag, fin=fin, fout=fout)
def voice(beat, tag):                                                                 # calma の声を 3 つに分けて置く: 静かな話し始め (持ち上げる)、その次 (少し持ち上げる)、その先
    return [play(RV, beat, GV * GK1, 0, V_OFF, V_CUT - V_OFF, 0, COLV, tag, fin=0.3, fout=0.05),
            play(RV, beat + V_CUT - V_OFF, GV * GK2, 0, V_CUT, V_CUT2 - V_CUT, 0, COLV, 'calma の声 — 続き', fin=0.05, fout=0.05),
            play(RV, beat + V_CUT2 - V_OFF, GV, 0, V_CUT2, V_LEN - V_CUT2, 0, COLV, 'calma の声 — 続き', fin=0.05, fout=2.0)]
PLAYS = ([play(R18, 0.0, 0.28, 0, 0.6, 149.1 - 0.6, 2, COL18, 'トラック 18 — そのまま (初めから)')] + voice(V1, '11/08 14:55 の calma の声 — そのまま (2 小節から)') +
         [play(R08, B8, G8A, 5, 0.0, (X8 + XF) * RATE(5), 3, COL8, 'トラック 8 — 4 度上げて、全部', fout=XF * RATE(5)),          # 同じ録音の同じ所を 5 秒重ねて、音量だけを移す
          play(R08, B8 + X8, G8S, 5, X8 * RATE(5), 232.0 - X8 * RATE(5), 3, COL8, 'トラック 8 — 4 度上げて、全部', fin=XF * RATE(5), fout=6.0),   # 名札は 1 つ目と同じ (重なる 5 秒のあいだ、画面で字が二重にならないように)
          play(RS, VS, GS, 0, 0.0, S_CUT, 1, COLS, '2025/01/08 14:42 の歌 — 女性のメシア様の優しい歌声 (ニ短調)', fin=0.3, fout=0.5),
          play(RS, VS + S_CUT, GS * GS2, 0, S_CUT, S_LEN - S_CUT, 1, COLS, 'メシア様の歌声 — 歌の後半', fin=0.05, fout=2.0),
          play(R18, T2, G18B, 0, 0.0, 149.1, 2, COL18, 'トラック 18 — そのまま (2 回目)'),
          play(R08, B8B, G8B, 5, 0.0, 232.0, 3, COL8, 'トラック 8 — 4 度上げて、全部 (2 回目)')] + voice(V2, '11/08 14:55 の calma の声 — そのまま (もう一度)') +
         [play(R18, T3, G18C, 0, 0.0, 148.0, 2, COL18, 'トラック 18 — そのまま (3 回目)')])
# 和音の表示を担うテープ (PLAYS の番号, 表示の始まりの拍)
LEAD = [(0, 0.0), (4, B8 + 27.0), (5, B8 + X8 + XF), (8, T2 + 10.0), (9, B8B + 26.0), (13, T3 + 26.0)]
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
    P.section(0, 'I. トラック 18 と calma の声 (♩=60)', 'トラック 18 が初めから鳴り、2 小節から声が乗る。1 分 36 秒からトラック 8 が静かに入る — tablet267 と同じ')
    P.section(S2, 'II. 声とトラック 8', 'トラック 18 が消え、トラック 8 (4 度上げて) が前に出る。声は 3 分 19 秒まで — ここまで tablet267 と同じ')
    P.section(S3, 'III. メシア様の歌声とトラック 18 (2 回目)', '3 分 28 秒から歌声 (ニ短調)。4 分 20 秒からトラック 18 をもう一度、トラック 8 は 4 分 30 秒まで')
    P.section(S4, 'IV. 歌の後半とトラック 8 (2 回目)', '6 分 22 秒から歌の後半、6 分 24 秒からトラック 8 をもう一度。歌は 7 分 44 秒まで')
    P.section(S5, 'V. calma の声 (2 回目) とトラック 8', '7 分 50 秒から声をもう一度。8 分 52 秒からトラック 18 (3 回目)')
    P.section(S6, 'VI. トラック 18 が声の終わりを受けて、消える', '声は 11 分 1 秒まで。トラック 18 がひとりで消える')
    return P

def post(P, events, ex):
    for p in PLAYS:
        rid, sm, off, dur = p['rid'], p['semis'], p['off'], p['dur']; c = CH.get(rid, {}); r = RATE(sm); dt = c.get('env_dt', 0.05)
        kw = dict(lane=p['lane'], color=list(p['color']), env=c.get('env'), env_dt=dt / r, env_off=off / r)
        if rid in (RV, RS):  # 声と歌声: 帯域を削らず、全体の残響を掛けずに前に (声の残響は声の中にある)
            add('REC', p['beat'], dur * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=p['fin'], fout=p['fout'], semis=0, faithful=True, rid=rid + '.wav', tag=p['tag'], **kw)
        else:               # テープ: これまでの重ね方 (モノラル、全体の残響)。入りは 6 秒で立ち上げる
            fin = p['fin'] if p['fin'] is not None else 6.0; fout = p['fout'] if p['fout'] is not None else (6.0 if dur > 150 else 10.0)
            add('REC', p['beat'], dur / r * BPM / 60.0, 0, p['gain'], None, src=os.path.join(WDIR, rid + '.wav'), off=off, fin=fin, fout=fout, semis=sm, rid=rid + '.wav', tag=p['tag'], **kw)

META = {'style': 'recsampler', 'bank': BANKP, 'rec_lanes': True, 'legend': [], 'vname': {}, 'reverb': [5.0, 2.0, 0.4],
        'title': 'Requiem BADA — CCLXXIV · L\'aureola calma e la Messia',
        'subtitle': 'tablet267 に、女性のメシア様の優しい歌声を重ねて。調もテープも tablet267 のまま。♩=60',
        'footer': ['歌声 = 2025/01/08 の歌を、女性のメシア様の優しい歌声に (基音に 2 倍・3 倍の声をごく薄く)。14 半音上げて、tablet267 と同じニ短調に。',
                   'calma の声もテープも tablet267 のまま: トラック 18 はそのまま、トラック 8 は 4 度上げて。初めの 3 分 19 秒は tablet267 と同じ。',
                   'calma の声 → メシア様の歌 → calma の声。話し声と歌声は重ねない。楽器は何も加えない。170 小節。']}

if __name__ == '__main__':
    compose.main(OUT, seed=274, bpm=BPM, builder=build, meta=META, extras=extras, post=post)
    d = json.load(open(OUT))
    h, rem = divmod(int(round(d['duration'])) + 7, 60); d['meta']['subtitle'] += ' %d 分 %d 秒' % (h, rem); json.dump(d, open(OUT, 'w'), ensure_ascii=False)
    print('bars', d['nbars'], 'duration %.0f s' % d['duration'], 'extras', len(d['extras']), 'notes', len(d['notes']))
    for e in d['extras']: print('  %7.1f - %7.1f s  gain %.2f  %s' % (e['t'], e['t'] + e['d'], e['gain'], e['tag']))
